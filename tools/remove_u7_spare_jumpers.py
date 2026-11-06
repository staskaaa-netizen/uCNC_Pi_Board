"""Remove retired JP6/JP7 and their routing branches."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REFERENCES = ("JP6", "JP7")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    footprints = [
        footprint
        for footprint in board.GetFootprints()
        if footprint.GetReference() in REFERENCES
    ]
    pad_endpoints = {
        ((pad.GetPosition().x, pad.GetPosition().y), pad.GetNetCode())
        for footprint in footprints
        for pad in footprint.Pads()
    }
    branches = []
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_TRACK):
            continue
        start = item.GetStart()
        end = item.GetEnd()
        if (
            ((start.x, start.y), item.GetNetCode()) in pad_endpoints
            or ((end.x, end.y), item.GetNetCode()) in pad_endpoints
        ):
            branches.append(item)

    print(
        {
            "footprints": [footprint.GetReference() for footprint in footprints],
            "branch_tracks": len(branches),
            "apply": args.apply,
        }
    )
    if not args.apply:
        return

    for item in branches:
        board.Remove(item)
    for footprint in footprints:
        board.Remove(footprint)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
