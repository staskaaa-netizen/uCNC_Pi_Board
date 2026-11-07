"""Remove selected footprints and copper branches left dangling by them."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def point_key(point) -> tuple[int, int]:
    return point.x, point.y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    footprints = [
        footprint
        for footprint in board.GetFootprints()
        if footprint.GetReference() in set(args.ref)
    ]
    found = {footprint.GetReference() for footprint in footprints}
    missing = sorted(set(args.ref) - found)
    if missing:
        raise RuntimeError(f"Missing footprints: {missing}")

    former_pad_points = {
        point_key(pad.GetPosition())
        for footprint in footprints
        for pad in footprint.Pads()
    }
    for footprint in footprints:
        board.Remove(footprint)

    tracks = [
        item
        for item in board.GetTracks()
        if type(item).__name__ == "PCB_TRACK"
    ]
    endpoints = defaultdict(int)
    for track in tracks:
        endpoints[point_key(track.GetStart())] += 1
        endpoints[point_key(track.GetEnd())] += 1

    dangling = [
        track
        for track in tracks
        if (
            point_key(track.GetStart()) in former_pad_points
            and endpoints[point_key(track.GetStart())] == 1
        )
        or (
            point_key(track.GetEnd()) in former_pad_points
            and endpoints[point_key(track.GetEnd())] == 1
        )
        or (
            point_key(track.GetStart()) in former_pad_points
            and point_key(track.GetEnd()) in former_pad_points
        )
    ]

    print(
        {
            "footprints": sorted(found),
            "dangling_tracks": [
                (
                    track.GetNetname(),
                    pcbnew.ToMM(track.GetStart().x),
                    pcbnew.ToMM(track.GetStart().y),
                    pcbnew.ToMM(track.GetEnd().x),
                    pcbnew.ToMM(track.GetEnd().y),
                )
                for track in dangling
            ],
            "apply": args.apply,
        }
    )
    if not args.apply:
        return

    for track in dangling:
        board.Remove(track)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
