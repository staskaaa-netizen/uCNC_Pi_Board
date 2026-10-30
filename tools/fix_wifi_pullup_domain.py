"""Move ESP pull-ups onto +3V3_WIFI without moving footprints.

The four 10 k pull-ups beside J20 previously connected to the motherboard
+3V3 net. They now belong to the ESP's dedicated +3V3_WIFI domain. This script
removes only the obsolete front-side +3V3 fanout and replaces it with a short
power rail between J20 pin 2 and R55-R58 pin 1.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

PULLUP_REFERENCES = ("R55", "R56", "R57", "R58")
OBSOLETE_UUIDS = {
    # +3V3 front-side fanout that terminated on the four pull-up pads.
    "27163aa1-b151-46df-af79-3e21144bbd8f",
    "3b5ed18a-9d01-458a-8959-6761e249c4f0",
    "5a9249d6-f10e-467f-9c39-4642f1d51091",
    "bb00514d-e3c0-41fc-884e-121c329ec753",
    "eeaffcf4-4446-4e54-a9ac-193ad5408dc1",
    # Layer-changing vias used only by the removed front-side fanout.
    "276213f0-0372-4229-a271-11d2235af214",
    "56132e5a-0d8b-4f2c-ac34-387ff5cf4c72",
}
NEW_POLYLINE_MM = (
    (169.545, 40.64),   # J20 pin 2
    (168.4, 39.495),
    (168.4, 38.0),
    (161.3875, 38.0),
    (160.4625, 39.37),  # R58 pin 1
    (160.4625, 50.8),   # R56 pin 1, through every pull-up pad
)
WIDTH_MM = 0.8


def point_mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def same_point(
    lhs: pcbnew.VECTOR2I,
    rhs: pcbnew.VECTOR2I,
    tolerance_mm: float = 0.01,
) -> bool:
    lx, ly = point_mm(lhs)
    rx, ry = point_mm(rhs)
    return abs(lx - rx) <= tolerance_mm and abs(ly - ry) <= tolerance_mm


def add_track(
    board: pcbnew.BOARD,
    net: pcbnew.NETINFO_ITEM,
    start_mm: tuple[float, float],
    end_mm: tuple[float, float],
) -> None:
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(pcbnew.VECTOR2I_MM(*start_mm))
    track.SetEnd(pcbnew.VECTOR2I_MM(*end_mm))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(net)
    track.SetWidth(pcbnew.FromMM(WIDTH_MM))
    board.Add(track)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--route",
        action="store_true",
        help="Also install the temporary +3V3_WIFI fanout for DRC checking.",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    wifi_net = board.FindNet("+3V3_WIFI")
    if wifi_net is None:
        raise SystemExit("Board has no +3V3_WIFI net")

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(set(PULLUP_REFERENCES) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing pull-up footprints: {', '.join(missing)}")

    pad_net_changes = []
    for reference in PULLUP_REFERENCES:
        pad = footprints[reference].FindPadByNumber("1")
        if pad.GetNetname() != "+3V3_WIFI":
            pad_net_changes.append((reference, pad.GetNetname(), "+3V3_WIFI"))
            if args.apply:
                pad.SetNet(wifi_net)

    obsolete = [
        track
        for track in board.GetTracks()
        if track.m_Uuid.AsString() in OBSOLETE_UUIDS
    ]
    if args.apply:
        for track in obsolete:
            board.Remove(track)

    segments = list(zip(NEW_POLYLINE_MM, NEW_POLYLINE_MM[1:]))
    temporary_segments = []
    missing_segments = []
    for start_mm, end_mm in segments:
        start = pcbnew.VECTOR2I_MM(*start_mm)
        end = pcbnew.VECTOR2I_MM(*end_mm)
        matches = [
            track
            for track in board.GetTracks()
            if track.GetClass() == "PCB_TRACK"
            and track.GetNetname() == "+3V3_WIFI"
            and track.GetLayer() == pcbnew.F_Cu
            and (
                (
                    same_point(track.GetStart(), start)
                    and same_point(track.GetEnd(), end)
                )
                or (
                    same_point(track.GetStart(), end)
                    and same_point(track.GetEnd(), start)
                )
            )
        ]
        temporary_segments.extend(matches)
        if not matches:
            missing_segments.append((start_mm, end_mm))

    if args.apply and not args.route:
        for track in temporary_segments:
            board.Remove(track)

    if args.apply and args.route:
        for start_mm, end_mm in missing_segments:
            add_track(board, wifi_net, start_mm, end_mm)

    print(f"pad_net_changes={pad_net_changes}")
    print(f"removed_obsolete={len(obsolete)}")
    print(f"temporary_segments={len(temporary_segments)} route={args.route}")
    print(f"missing_wifi_segments={len(missing_segments)}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
