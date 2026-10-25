"""Audit in-board component alignment to a common placement grid."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--grid", type=float, default=0.5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    edge_box = board.GetBoardEdgesBoundingBox()
    left = pcbnew.ToMM(edge_box.GetLeft())
    top = pcbnew.ToMM(edge_box.GetTop())
    right = pcbnew.ToMM(edge_box.GetRight())
    bottom = pcbnew.ToMM(edge_box.GetBottom())
    errors = []
    checked = 0
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if reference.startswith("H"):
            continue
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        if not (left <= x <= right and top <= y <= bottom):
            continue
        checked += 1
        x_error = abs(x / args.grid - round(x / args.grid)) * args.grid
        y_error = abs(y / args.grid - round(y / args.grid)) * args.grid
        rotation_error = footprint.GetOrientationDegrees() % 90.0
        rotation_error = min(rotation_error, 90.0 - rotation_error)
        if x_error > 0.001 or y_error > 0.001 or rotation_error > 0.001:
            errors.append(
                {
                    "reference": reference,
                    "position": [round(x, 4), round(y, 4)],
                    "rotation": footprint.GetOrientationDegrees(),
                    "x_error_mm": round(x_error, 4),
                    "y_error_mm": round(y_error, 4),
                    "rotation_error_deg": round(rotation_error, 4),
                }
            )

    result = {
        "grid_mm": args.grid,
        "checked": checked,
        "off_grid": errors,
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
