"""Route one explicitly approved point-to-point connection at a time."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--net", required=True)
    parser.add_argument("--width-mm", type=float, default=0.25)
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Allow a multi-pad net and connect its pads using a minimum spanning tree",
    )
    parser.add_argument(
        "--waypoints",
        help="Semicolon-separated x,y waypoints for a two-pad route",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Remove existing tracks on the net before routing",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Add a leg to an already routed net",
    )
    parser.add_argument("--from-pad", help="Footprint.pin selector for one explicit leg")
    parser.add_argument("--to-pad", help="Footprint.pin selector for one explicit leg")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    existing = [
        track
        for track in board.GetTracks()
        if not isinstance(track, pcbnew.PCB_VIA)
        and track.GetNetname() == args.net
    ]
    if existing and args.replace:
        for track in existing:
            board.Remove(track)
    elif existing and not args.append:
        print(f"{args.net}: already has {len(existing)} routed segment(s)")
        return

    all_pads = [
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetname() == args.net
    ]
    if bool(args.from_pad) != bool(args.to_pad):
        raise SystemExit("--from-pad and --to-pad must be used together")
    if args.from_pad:
        def selected(selector: str):
            reference, pin = selector.rsplit(".", 1)
            footprint = next(
                (
                    item
                    for item in board.GetFootprints()
                    if item.GetReference() == reference
                ),
                None,
            )
            if footprint is None:
                raise SystemExit(f"Footprint not found: {reference}")
            pad = footprint.FindPadByNumber(pin)
            if pad is None or pad.GetNetname() != args.net:
                raise SystemExit(f"{selector} is not on net {args.net}")
            return pad

        pads = [selected(args.from_pad), selected(args.to_pad)]
    else:
        pads = all_pads
    if len(pads) != 2 and not args.tree:
        raise SystemExit(
            f"{args.net}: expected exactly two pads for incremental point-to-point routing, "
            f"found {len(pads)}"
        )

    if args.waypoints and len(pads) != 2:
        raise SystemExit("--waypoints requires exactly two pads")
    points = [
        pcbnew.VECTOR2I(pad.GetPosition().x, pad.GetPosition().y)
        for pad in pads
    ]
    if args.waypoints:
        waypoints = [
            pcbnew.VECTOR2I_MM(*[float(value) for value in item.split(",")])
            for item in args.waypoints.split(";")
        ]
        points = [points[0], *waypoints, points[1]]
        edges = [(index, index + 1) for index in range(len(points) - 1)]
    else:
        remaining = set(range(1, len(points)))
        connected = {0}
        edges = []
        while remaining:
            best = None
            for a in connected:
                for b in remaining:
                    distance = math.hypot(
                        pcbnew.ToMM(points[a].x) - pcbnew.ToMM(points[b].x),
                        pcbnew.ToMM(points[a].y) - pcbnew.ToMM(points[b].y),
                    )
                    if best is None or distance < best[0]:
                        best = (distance, a, b)
            _, a, b = best
            edges.append((a, b))
            connected.add(b)
            remaining.remove(b)

    retained_points = []
    for a, b in edges:
        start = pcbnew.VECTOR2I(points[a].x, points[a].y)
        end = pcbnew.VECTOR2I(points[b].x, points[b].y)
        retained_points.extend((start, end))
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(start)
        track.SetEnd(end)
        track.SetWidth(pcbnew.FromMM(args.width_mm))
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(pads[0].GetNet())
        board.Add(track)
        if args.verbose:
            saved_start = track.GetStart()
            saved_end = track.GetEnd()
            print(
                "segment: "
                f"({pcbnew.ToMM(saved_start.x):.2f},{pcbnew.ToMM(saved_start.y):.2f}) -> "
                f"({pcbnew.ToMM(saved_end.x):.2f},{pcbnew.ToMM(saved_end.y):.2f})"
            )
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(
        f"{args.net}: routed {len(edges)} segment(s) on F.Cu, "
        f"width {args.width_mm:.3f} mm"
    )


if __name__ == "__main__":
    main()
