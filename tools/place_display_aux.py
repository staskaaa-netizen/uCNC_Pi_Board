"""Place LCD LVDS resistor networks and the AUX open-drain MOSFET."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap, put_on_side


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

PLACEMENTS = {
    "RN27": (135.5, 40.0, 90.0),
    "RN26": (143.0, 40.0, 90.0),
    "Q5": (144.0, 14.0, 0.0),
    "R112": (149.0, 14.0, 90.0),
    "R113": (139.0, 14.0, 90.0),
}


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def spans_sides(footprint) -> bool:
    return any(
        pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
        for pad in footprint.Pads()
    )


def add_box(footprint, box, occupied) -> None:
    layers = (
        (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
        if spans_sides(footprint)
        else (int(footprint.GetLayer()),)
    )
    for layer in layers:
        occupied[layer].append(box)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    missing = sorted(set(PLACEMENTS) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )
    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        if reference in PLACEMENTS:
            continue
        x, y = point_mm(footprint.GetPosition())
        if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
            continue
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        add_box(footprint, box, occupied)

    for reference, (x, y, rotation) in PLACEMENTS.items():
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetOrientationDegrees(rotation)
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        if not bbox_inside(box, 0.55):
            raise RuntimeError(f"{reference} falls outside the board")
        if any(overlap(box, other) for other in occupied[int(pcbnew.F_Cu)]):
            conflicts = []
            for other_reference, other in footprints.items():
                if other_reference == reference:
                    continue
                other_position = point_mm(other.GetPosition())
                if other_reference not in PLACEMENTS and not (
                    bounds[0] <= other_position[0] <= bounds[2]
                    and bounds[1] <= other_position[1] <= bounds[3]
                ):
                    continue
                other_box = candidate_boxes(
                    other, other_position[0], other_position[1], clearance=0.05
                )
                if overlap(box, other_box):
                    conflicts.append(other_reference)
            raise RuntimeError(f"{reference} overlaps: {', '.join(conflicts)}")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        add_box(footprint, box, occupied)
        print(f"{reference}: ({x:.3f}, {y:.3f}) rotation={rotation:.1f} F.Cu")

    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
