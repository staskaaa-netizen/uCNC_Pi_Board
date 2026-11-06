"""Put LED references on silkscreen and find nearby clear label positions."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
LED_FOOTPRINT = "LED_0805_2012Metric"
TEXT_SIZE_MM = 0.8
TEXT_THICKNESS_MM = 0.12
CLEARANCE_MM = 0.18


def bbox(item) -> tuple[float, float, float, float]:
    box = item.GetBoundingBox()
    return (
        pcbnew.ToMM(box.GetLeft()),
        pcbnew.ToMM(box.GetTop()),
        pcbnew.ToMM(box.GetRight()),
        pcbnew.ToMM(box.GetBottom()),
    )


def overlaps(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
    clearance: float = CLEARANCE_MM,
) -> bool:
    return not (
        first[2] + clearance <= second[0]
        or second[2] + clearance <= first[0]
        or first[3] + clearance <= second[1]
        or second[3] + clearance <= first[1]
    )


def inside(
    box: tuple[float, float, float, float],
    bounds: tuple[float, float, float, float],
) -> bool:
    margin = 0.5
    return (
        box[0] >= bounds[0] + margin
        and box[1] >= bounds[1] + margin
        and box[2] <= bounds[2] - margin
        and box[3] <= bounds[3] - margin
    )


def candidate_positions(center: tuple[float, float]):
    for radius in (2.2, 2.8, 3.4, 4.0, 4.8, 5.8, 7.0, 8.5, 10.0, 12.0, 15.0):
        for angle in range(0, 360, 45):
            radians = math.radians(angle)
            yield (
                center[0] + radius * math.cos(radians),
                center[1] + radius * math.sin(radians),
                0.0 if angle in {0, 90, 180, 270} else 0.0,
                radius,
            )


def place_led_references(board) -> dict:
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )

    leds = [
        footprint
        for footprint in board.GetFootprints()
        if str(footprint.GetFPID().GetLibItemName()) == LED_FOOTPRINT
    ]
    moving_refs = {footprint.GetReference() for footprint in leds}
    obstacles = []
    for footprint in board.GetFootprints():
        obstacles.extend(bbox(pad) for pad in footprint.Pads())
        obstacles.extend(
            bbox(item)
            for item in footprint.GraphicalItems()
            if item.GetLayer() in {pcbnew.F_SilkS, pcbnew.B_SilkS}
        )
        for field in (footprint.Reference(), footprint.Value()):
            if (
                field.IsVisible()
                and field.GetLayer() in {pcbnew.F_SilkS, pcbnew.B_SilkS}
                and footprint.GetReference() not in moving_refs
            ):
                obstacles.append(bbox(field))
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            obstacles.append(bbox(item))
    for item in board.GetDrawings():
        if item.GetLayer() in {
            pcbnew.F_SilkS,
            pcbnew.B_SilkS,
        }:
            obstacles.append(bbox(item))

    placed = []
    failures = []
    for footprint in sorted(leds, key=lambda item: item.GetReference()):
        field = footprint.Reference()
        layer = pcbnew.B_SilkS if footprint.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
        field.SetLayer(layer)
        field.SetVisible(True)
        field.SetMirrored(layer == pcbnew.B_SilkS)
        field.SetTextSize(pcbnew.VECTOR2I_MM(TEXT_SIZE_MM, TEXT_SIZE_MM))
        field.SetTextThickness(pcbnew.FromMM(TEXT_THICKNESS_MM))
        field.ClearBoundingBoxCache()
        center = (
            pcbnew.ToMM(footprint.GetPosition().x),
            pcbnew.ToMM(footprint.GetPosition().y),
        )
        chosen = None
        for x, y, angle, distance in candidate_positions(center):
            field.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            field.SetTextAngleDegrees(angle)
            field.ClearBoundingBoxCache()
            box = bbox(field)
            if not inside(box, bounds):
                continue
            if any(overlaps(box, obstacle) for obstacle in obstacles):
                continue
            if any(overlaps(box, other) for other in placed):
                continue
            chosen = ((x, y, angle), box, distance)
            break
        if chosen is None:
            field.SetLayer(layer)
            field.ClearBoundingBoxCache()
            box = bbox(field)
            placed.append(box)
            failures.append(footprint.GetReference())
            continue
        (x, y, angle), box, _distance = chosen
        field.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        field.SetTextAngleDegrees(angle)
        field.ClearBoundingBoxCache()
        placed.append(box)

    return {
        "led_references": len(leds),
        "placed_with_clearance": len(leds) - len(failures),
        "fallback_positions": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    report = place_led_references(board)
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")
    print(report)


if __name__ == "__main__":
    main()
