"""Place the first isolated PLC input channel beside J7."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# ref: (x_mm, y_mm, rotation_degrees)
INPUT_0 = {
    "R18": (63.5, 134.5, 90.0),
    "D13": (63.5, 123.0, -90.0),
    "D14": (63.5, 128.5, 90.0),
    "U18": (68.0, 113.0, 90.0),
    "R76": (63.5, 101.5, 90.0),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for reference, (x, y, rotation) in INPUT_0.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        put_on_side(footprint, back=False)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(f"{reference}: ({x:.2f}, {y:.2f}) rotation={rotation:.1f}")
    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
