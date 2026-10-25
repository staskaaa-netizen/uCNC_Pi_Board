"""Move a footprint reference field on the current PCB."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=ROOT / "hardware" / "motherboard.kicad_pcb")
    parser.add_argument("--ref", required=True)
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--hide", action="store_true")
    parser.add_argument("--layer", choices=("front", "back"))
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprint = next(
        (item for item in board.GetFootprints() if item.GetReference() == args.ref),
        None,
    )
    if footprint is None:
        raise SystemExit(f"Footprint not found: {args.ref}")
    footprint.Reference().SetPosition(pcbnew.VECTOR2I_MM(args.x, args.y))
    if args.layer == "back":
        footprint.Reference().SetLayer(pcbnew.B_SilkS)
        footprint.Reference().SetMirrored(True)
    elif args.layer == "front":
        footprint.Reference().SetLayer(pcbnew.F_SilkS)
        footprint.Reference().SetMirrored(False)
    if args.hide:
        footprint.Reference().SetVisible(False)
    pcbnew.SaveBoard(str(args.board), board)
    print(
        f"{args.ref} reference -> ({args.x:.2f}, {args.y:.2f})"
        f"{' hidden' if args.hide else ''}"
    )


if __name__ == "__main__":
    main()
