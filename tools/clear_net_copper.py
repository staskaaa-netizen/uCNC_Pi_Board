"""Remove all tracks and vias from one net, leaving pads untouched."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--net", required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    copper = [item for item in board.GetTracks() if item.GetNetname() == args.net]
    for item in copper:
        board.Remove(item)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"{args.net}: removed {len(copper)} track/via item(s)")


if __name__ == "__main__":
    main()
