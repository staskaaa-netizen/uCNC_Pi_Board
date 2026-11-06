"""Remove retired C2/C4/C7/C112 and any resulting dangling branch tracks."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
REFERENCES = ("C2", "C4", "C7", "C112")

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
    former_pads = {
        (
            (pad.GetPosition().x, pad.GetPosition().y),
            pad.GetNetCode(),
        )
        for footprint in footprints
        for pad in footprint.Pads()
    }

    endpoints: dict[tuple[tuple[int, int], int], list] = defaultdict(list)
    for item in board.GetTracks():
        if type(item).__name__ != "PCB_TRACK":
            continue
        start = item.GetStart()
        end = item.GetEnd()
        endpoints[((start.x, start.y), item.GetNetCode())].append(item)
        endpoints[((end.x, end.y), item.GetNetCode())].append(item)

    dangling = []
    for pad_key in former_pads:
        pad_tracks = endpoints.get(pad_key, [])
        if len(pad_tracks) == 1 and pad_tracks[0] not in dangling:
            dangling.append(pad_tracks[0])

    print(
        {
            "footprints": [footprint.GetReference() for footprint in footprints],
            "dangling_branch_tracks": [
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
    for footprint in footprints:
        board.Remove(footprint)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
