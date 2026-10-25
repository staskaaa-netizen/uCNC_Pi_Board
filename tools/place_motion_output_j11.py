"""Place the J11 motion-output support components near U25."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    placement = (
        ("RN10", 88.64, 18.5, 270.0, False),
        ("RN11", 82.0, 18.5, 270.0, False),
        ("C54", 79.0, 25.0, 90.0, True),
    )
    for reference, x, y, rotation, back in placement:
        footprint = footprints[reference]
        put_on_side(footprint, back=back)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(
            f"{reference:4} -> ({x:.2f}, {y:.2f}) "
            f"rot={rotation:.1f} {'B' if back else 'F'}.Cu"
        )

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
