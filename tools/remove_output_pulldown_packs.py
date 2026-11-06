"""Remove the four unused optocoupler-side output pull-down networks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REFERENCES = ("RN12", "RN13", "RN30", "RN31")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    footprints = []
    pad_endpoints = set()
    for reference in REFERENCES:
        footprint = board.FindFootprintByReference(reference)
        if footprint is not None:
            footprints.append(footprint)
            for pad in footprint.Pads():
                position = pad.GetPosition()
                pad_endpoints.add(
                    ((position.x, position.y), pad.GetNetCode())
                )

    stubs = []
    for item in board.GetTracks():
        if not isinstance(item, pcbnew.PCB_TRACK):
            continue
        start = item.GetStart()
        end = item.GetEnd()
        if (
            ((start.x, start.y), item.GetNetCode()) in pad_endpoints
            or ((end.x, end.y), item.GetNetCode()) in pad_endpoints
        ):
            stubs.append(item)

    print(
        {
            "footprints": [footprint.GetReference() for footprint in footprints],
            "connected_stub_tracks": len(stubs),
            "apply": args.apply,
        }
    )
    if not args.apply:
        return

    for item in stubs:
        board.Remove(item)
    for footprint in footprints:
        board.Remove(footprint)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
