"""Swap TLP291-4 reference designators without moving footprints."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
SWAPS = (("U61", "U62"), ("U63", "U64"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for left, right in SWAPS:
        print(f"{left} <-> {right}")
    if not args.apply:
        return

    for left, right in SWAPS:
        left_fp = footprints[left]
        right_fp = footprints[right]
        left_fp.SetReference("__TEMP__")
        right_fp.SetReference(left)
        left_fp.SetReference(right)
        footprints[right] = left_fp
        footprints[left] = right_fp

    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
