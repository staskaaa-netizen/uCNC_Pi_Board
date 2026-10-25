"""Move explicit references to a collision-free off-board staging grid."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--refs", required=True)
    parser.add_argument("--start-x", type=float, default=620.0)
    parser.add_argument("--start-y", type=float, default=20.0)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    references = [item for item in args.refs.split(",") if item]
    for index, reference in enumerate(references):
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        x = args.start_x + (index // 20) * 24
        y = args.start_y + (index % 20) * 15
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        print(f"{reference}: parked at ({x:.1f}, {y:.1f})")
    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
