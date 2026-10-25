"""Apply the compact LMR36510 5 V buck topology placement."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]

# ref: (x_mm, y_mm, rotation_degrees)
POWER_LOOP = {
    "U1": (54.0, 30.86, 0),
    "L1": (63.0, 30.86, 0),
    "C4": (47.8, 32.5, 0),
    "C5": (45.0, 38.0, 0),
    "C6": (69.0, 31.0, 0),
    "C7": (69.0, 27.0, 0),
    "C11": (69.0, 35.0, 0),
    "C8": (69.0, 43.0, 0),
    "C86": (58.0, 36.0, 90),
    "C91": (58.0, 40.0, 90),
    "R70": (63.0, 40.0, 0),
    "R71": (63.0, 43.5, 0),
    "R72": (63.0, 47.0, 0),
    "R73": (60.0, 25.0, 0),
    "Q2": (128.0, 10.5, 90),
    "Q3": (123.0, 7.5, 0),
    "R6": (130.2, 15.2, 90),
    "D6": (122.0, 14.0, 0),
    "R7": (110.5, 18.0, 0),
    "C18": (124.5, 17.5, 0),
    "JP1": (117.0, 17.0, 0),
    "U2": (198.120, 94.000, 0),
    "C90": (195.580, 87.015, 0),
    "C13": (191.135, 89.555, 90),
    "C10": (191.135, 99.080, 90),
    "C76": (191.135, 94.000, 90),
    "U34": (121.0, 7.0, 0),
    "C88": (114.0, 3.0, 90),
    "C89": (114.0, 8.0, 90),
    "C69": (128.0, 3.0, 90),
    "C70": (128.0, 8.0, 90),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--board",
        type=Path,
        default=ROOT / "hardware" / "motherboard.kicad_pcb",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for reference, (x, y, rotation) in POWER_LOOP.items():
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        print(f"{reference}: ({x:.2f}, {y:.2f}) rotation={rotation:.0f}")
    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
