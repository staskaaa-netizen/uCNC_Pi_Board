"""Place the encoder buffer/divider and connector-local support parts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# ref: (x_mm, y_mm, rotation_degrees)
PLACEMENT = {
    "U28": (68.000, 124.184, 90.0),
    "R110": (85.500, 133.300, 0.0),
    "R111": (90.000, 133.300, 0.0),
    "D53": (98.000, 132.000, 180.0),
    "F2": (38.000, 132.000, 0.0),
    "C57": (64.000, 116.000, 0.0),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for reference, (x, y, rotation) in PLACEMENT.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        put_on_side(footprint, back=False)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(f"{reference:4} -> ({x:.3f}, {y:.3f}) rot={rotation:.1f} F.Cu")

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
