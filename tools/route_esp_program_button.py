"""Reconnect SW2 to the existing ESP GPIO0 net after the Wi-Fi-area rework."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

TRACKS = (
    (pcbnew.F_Cu, (172.075, 33.0), (178.575, 33.0)),
    (pcbnew.B_Cu, (172.075, 33.0), (172.965, 41.135)),
)
WIDTH_MM = 0.2


def same_point(
    lhs: pcbnew.VECTOR2I,
    rhs: pcbnew.VECTOR2I,
    tolerance_mm: float = 0.01,
) -> bool:
    return (
        abs(pcbnew.ToMM(lhs.x - rhs.x)) <= tolerance_mm
        and abs(pcbnew.ToMM(lhs.y - rhs.y)) <= tolerance_mm
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    net = board.FindNet("WIFI_GPIO0")
    if net is None:
        raise SystemExit("WIFI_GPIO0 net is missing")

    added = []
    for layer, start_mm, end_mm in TRACKS:
        start = pcbnew.VECTOR2I_MM(*start_mm)
        end = pcbnew.VECTOR2I_MM(*end_mm)
        exists = any(
            item.GetClass() == "PCB_TRACK"
            and item.GetNetname() == "WIFI_GPIO0"
            and item.GetLayer() == layer
            and (
                (same_point(item.GetStart(), start) and same_point(item.GetEnd(), end))
                or (same_point(item.GetStart(), end) and same_point(item.GetEnd(), start))
            )
            for item in board.GetTracks()
        )
        if exists:
            continue
        added.append((layer, start_mm, end_mm))
        if args.apply:
            track = pcbnew.PCB_TRACK(board)
            track.SetStart(start)
            track.SetEnd(end)
            track.SetLayer(layer)
            track.SetWidth(pcbnew.FromMM(WIDTH_MM))
            track.SetNet(net)
            board.Add(track)

    print(f"added_tracks={added}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
