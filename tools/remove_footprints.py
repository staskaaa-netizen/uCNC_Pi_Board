"""Remove footprints by reference and save the board."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--ref", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    wanted = set(args.ref)
    board = pcbnew.LoadBoard(str(args.board))
    matches = [
        footprint
        for footprint in board.GetFootprints()
        if footprint.GetReference() in wanted
    ]
    found = {footprint.GetReference() for footprint in matches}
    print(f"matched={','.join(sorted(found))}")
    print(f"missing={','.join(sorted(wanted - found))}")
    if not args.apply:
        return
    for footprint in matches:
        board.Remove(footprint)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
