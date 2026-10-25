"""Place the J12 general-output indicator and state-definition parts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
J12_PIN_X = (50.75, 47.25, 43.75, 40.25, 36.75, 33.25, 29.75, 26.25)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}

    for channel, x in enumerate(J12_PIN_X):
        for reference, y in (
            (f"R{34 + channel}", 18.0),
            (f"D{45 + channel}", 13.0),
        ):
            footprint = footprints[reference]
            put_on_side(footprint, back=False)
            footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            footprint.SetOrientationDegrees(90.0)
            print(f"{reference:4} -> ({x:.2f}, {y:.2f}) rot=90.0 F.Cu")

    for reference, x, y, rotation in (
        ("C55", 77.0, 23.5, 90.0),
        ("C56", 59.0, 23.5, 90.0),
        ("RN12", 60.5, 34.0, 90.0),
        ("RN13", 79.5, 34.0, 90.0),
    ):
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(f"{reference:4} -> ({x:.2f}, {y:.2f}) rot={rotation:.1f} F.Cu")

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
