"""Remove the retired 595/541 motion buffers without modifying copper routing."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
RETIRED_REFERENCES = ("U24", "U25", "C53", "C54")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    present = [ref for ref in RETIRED_REFERENCES if ref in footprints]
    for reference in present:
        print(f"retire {reference}")
    print(f"footprint_removals={len(present)} apply={args.apply}")
    if not args.apply:
        return

    for reference in present:
        board.Remove(footprints[reference])
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
