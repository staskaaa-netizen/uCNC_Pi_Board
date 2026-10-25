"""Set the position and rotation of named footprints on the current PCB."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=ROOT / "hardware" / "motherboard.kicad_pcb")
    parser.add_argument("--ref", required=True)
    parser.add_argument("--x", type=float, required=True)
    parser.add_argument("--y", type=float, required=True)
    parser.add_argument("--rotation", type=float, required=True)
    parser.add_argument("--side", choices=("front", "back"))
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprint = next(
        (item for item in board.GetFootprints() if item.GetReference() == args.ref),
        None,
    )
    if footprint is None:
        raise SystemExit(f"Footprint not found: {args.ref}")
    if args.side:
        put_on_side(footprint, back=args.side == "back")
    footprint.SetPosition(pcbnew.VECTOR2I_MM(args.x, args.y))
    footprint.SetOrientationDegrees(args.rotation)
    pcbnew.SaveBoard(str(args.board), board)
    print(
        f"{args.ref}: ({args.x:.2f}, {args.y:.2f}) "
        f"rotation={args.rotation:.1f}"
    )


if __name__ == "__main__":
    main()
