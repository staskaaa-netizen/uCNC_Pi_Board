"""Remove board text objects whose complete text matches a supplied value."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--text", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    wanted = set(args.text)
    board = pcbnew.LoadBoard(str(args.board))
    matches = [
        item
        for item in board.GetDrawings()
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetText() in wanted
    ]
    print(f"matched_text_items={len(matches)} apply={args.apply}")
    if not args.apply:
        return
    for item in matches:
        board.Remove(item)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
