"""Place the four-channel PWM-to-0-10 V output block near J25."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# ref: (x_mm, y_mm, rotation_degrees, back_side)
PLACEMENT = {
    "J25": (134.50, 142.00, 0.0, False),
    "U37": (164.00, 107.50, 180.0, False),
    "U38": (144.00, 128.00, 0.0, False),
    "R92": (141.00, 98.50, 180.0, False),
    "R93": (142.50, 108.00, 180.0, False),
    "R94": (153.50, 108.50, 180.0, False),
    "R95": (153.00, 98.50, 180.0, False),
    "R96": (136.50, 99.00, 180.0, False),
    "R97": (137.00, 116.00, -90.0, False),
    "R98": (148.50, 108.50, 180.0, False),
    "R99": (148.00, 98.50, 180.0, False),
    "R100": (138.00, 135.00, -90.0, False),
    "R101": (142.00, 135.00, -90.0, False),
    "R102": (145.00, 135.00, -90.0, False),
    "R103": (148.50, 135.00, -90.0, False),
    "R104": (136.50, 127.00, 180.0, False),
    "R105": (135.00, 132.50, 90.0, False),
    "R106": (151.50, 133.20, 90.0, False),
    "R107": (151.50, 127.50, 0.0, False),
    "C92": (137.00, 94.50, 180.0, False),
    "C93": (136.50, 124.50, 180.0, False),
    "C94": (137.00, 104.00, 180.0, False),
    "C95": (136.50, 129.30, 180.0, False),
    "C96": (148.50, 105.00, 180.0, False),
    "C97": (153.00, 130.00, 0.0, False),
    "C98": (148.00, 95.50, 180.0, False),
    "C99": (151.50, 125.00, 0.0, False),
    "C100": (161.00, 101.50, 180.0, False),
    "C101": (170.452382, 105.50, 180.0, False),
    "C102": (149.00, 117.00, 0.0, False),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for reference, (x, y, rotation, back) in PLACEMENT.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        put_on_side(footprint, back=back)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(
            f"{reference:5s} -> ({x:.2f}, {y:.2f}) "
            f"rot={rotation:.1f} {'B' if back else 'F'}.Cu"
        )

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
