"""Place U10-U13 in physical left-to-right daisy-chain order."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REFERENCES = ("U10", "U11", "U12", "U13")


def transform(footprint):
    return (
        footprint.GetPosition(),
        footprint.GetOrientation(),
        footprint.GetLayer(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    missing = [reference for reference in REFERENCES if reference not in footprints]
    if missing:
        raise SystemExit(f"Missing output registers: {', '.join(missing)}")

    current = {
        reference: transform(footprints[reference])
        for reference in REFERENCES
    }
    slots = sorted(
        current.values(),
        key=lambda item: (item[0].x, item[0].y),
    )
    targets = dict(zip(REFERENCES, slots))

    for reference in REFERENCES:
        old_position, old_orientation, old_layer = current[reference]
        new_position, _, _ = targets[reference]
        print(
            f"{reference}: "
            f"({pcbnew.ToMM(old_position.x):.3f}, {pcbnew.ToMM(old_position.y):.3f}) -> "
            f"({pcbnew.ToMM(new_position.x):.3f}, {pcbnew.ToMM(new_position.y):.3f})"
        )
    print(f"placements={len(REFERENCES)} apply={args.apply}")
    if not args.apply:
        return

    for reference in REFERENCES:
        footprint = footprints[reference]
        position, orientation, layer = targets[reference]
        footprint.SetPosition(position)
        footprint.SetOrientation(orientation)
        footprint.SetLayer(layer)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
