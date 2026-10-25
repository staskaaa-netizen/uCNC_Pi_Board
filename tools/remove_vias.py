"""Remove PCB vias by UUID, leaving tracks and footprints untouched."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--uuid", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    wanted = set(args.uuid)
    board = pcbnew.LoadBoard(str(args.board))
    matched = []
    rejected = []
    for track in list(board.GetTracks()):
        if not isinstance(track, pcbnew.PCB_VIA):
            continue
        identifier = str(track.m_Uuid.AsString())
        if identifier not in wanted:
            continue
        if track.GetNetname() != "GND":
            rejected.append((identifier, track.GetNetname()))
            continue
        matched.append(track)

    found = {str(track.m_Uuid.AsString()) for track in matched}
    found.update(identifier for identifier, _ in rejected)
    missing = sorted(wanted - found)
    for identifier, net in rejected:
        print(f"rejected {identifier}: net={net}")
    for identifier in missing:
        print(f"missing {identifier}")
    print(f"matched_gnd_vias={len(matched)} apply={args.apply}")
    if not args.apply:
        return
    for track in matched:
        board.Remove(track)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
