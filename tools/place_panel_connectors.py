"""Place the paired PLC input and per-axis motion connectors."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap, put_on_side


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

PLACEMENTS = {
    # Two 16-pin PLC connectors, alternating input and isolated common.
    "J7": (8.0, 23.0, 270.0),
    "J8": (8.0, 83.0, 270.0),
    "J17": (30.0, 31.0, 270.0),
    "J18": (154.0, 48.0, 270.0),
    # General I/O followed by five motor-axis connectors and AUX/GND.
    "J12": (51.0, 5.5, 180.0),
    "J10": (68.0, 5.5, 180.0),
    "J11": (85.5, 5.5, 180.0),
    "J28": (103.0, 5.5, 180.0),
    "J29": (120.5, 5.5, 180.0),
    "J30": (137.5, 5.5, 180.0),
    "J31": (147.5, 5.5, 180.0),
    "J24": (137.0, 142.0, 0.0),
    "J25": (161.5, 142.5, 0.0),
}


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


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
    occupied = []
    for reference, footprint in footprints.items():
        if reference in PLACEMENTS:
            continue
        x, y = point_mm(footprint.GetPosition())
        if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
            continue
        occupied.append(candidate_boxes(footprint, x, y, clearance=0.0))

    for reference, (x, y, rotation) in PLACEMENTS.items():
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetOrientationDegrees(rotation)
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        if not bbox_inside(box, 0.55):
            raise RuntimeError(f"{reference} falls outside the board")
        if any(overlap(box, other) for other in occupied):
            raise RuntimeError(f"{reference} overlaps an existing footprint")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        occupied.append(box)
        print(f"{reference}: ({x:.3f}, {y:.3f}) rotation={rotation:.1f} F.Cu")

    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
