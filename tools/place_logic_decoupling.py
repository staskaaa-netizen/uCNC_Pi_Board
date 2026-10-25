"""Place one local 100 nF capacitor at each 74HC165/74HC595 VCC pin."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap, put_on_side


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# The +3V3 pad is the left pad at 0 degrees. Each body starts 0.5 mm to the
# right of its SOIC courtyard, preserving a bottom-plane ground via position.
PLACEMENTS = {
    "C22": ("U6", (60.000, 57.480, 0.0)),
    "C23": ("U7", (78.000, 57.480, 0.0)),
    "C24": ("U8", (94.500, 56.980, 0.0)),
    "C25": ("U9", (110.500, 56.980, 0.0)),
    "C26": ("U10", (110.500, 42.980, 0.0)),
    "C27": ("U11", (94.500, 42.980, 0.0)),
    "C28": ("U12", (77.500, 42.980, 0.0)),
    "C29": ("U13", (59.500, 42.980, 0.0)),
}


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def pad_distance(footprint, footprint_net: str, other, other_net: str) -> float:
    footprint_points = [
        point_mm(pad.GetPosition())
        for pad in footprint.Pads()
        if pad.GetNetname() == footprint_net
    ]
    other_points = [
        point_mm(pad.GetPosition())
        for pad in other.Pads()
        if pad.GetNetname() == other_net
    ]
    return min(math.dist(a, b) for a in footprint_points for b in other_points)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    missing = sorted(
        reference
        for reference in (*PLACEMENTS.keys(), *(ic for ic, _ in PLACEMENTS.values()))
        if reference not in footprints
    )
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )

    occupied = []
    for reference, footprint in footprints.items():
        if reference in PLACEMENTS:
            continue
        position = point_mm(footprint.GetPosition())
        if not (
            bounds[0] <= position[0] <= bounds[2]
            and bounds[1] <= position[1] <= bounds[3]
        ):
            continue
        occupied.append(
            candidate_boxes(footprint, position[0], position[1], clearance=0.0)
        )

    result = {}
    loop_total = 0.0
    for reference, (ic_reference, (x, y, rotation)) in PLACEMENTS.items():
        capacitor = footprints[reference]
        put_on_side(capacitor, back=False)
        capacitor.SetOrientationDegrees(rotation)
        box = candidate_boxes(capacitor, x, y, clearance=0.05)
        if not bbox_inside(box, 0.55):
            raise RuntimeError(f"{reference} falls outside the board")
        if any(overlap(box, other) for other in occupied):
            raise RuntimeError(f"{reference} overlaps an existing footprint")
        capacitor.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        box = candidate_boxes(capacitor, x, y, clearance=0.05)
        occupied.append(box)

        ic = footprints[ic_reference]
        supply_loop = pad_distance(capacitor, "+3V3", ic, "+3V3")
        ground_loop = pad_distance(capacitor, "GND", ic, "GND")
        loop = supply_loop + ground_loop
        loop_total += loop
        result[reference] = {
            "ic": ic_reference,
            "x": x,
            "y": y,
            "rotation": rotation,
            "supply_mm": round(supply_loop, 3),
            "ground_mm": round(ground_loop, 3),
            "loop_mm": round(loop, 3),
        }
        print(
            f"{reference} -> {ic_reference}: ({x:.2f}, {y:.2f}) "
            f"loop={loop:.2f} mm"
        )

    report = {
        "board": str(args.board),
        "total_loop_mm": round(loop_total, 3),
        "placements": result,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
