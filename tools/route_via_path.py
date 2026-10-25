"""Route one pad-to-pad net using F.Cu, B.Cu and a controlled via transition."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def point(value: str):
    return pcbnew.VECTOR2I_MM(*[float(item) for item in value.split(",")])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--net", required=True)
    parser.add_argument("--from-pad", required=True)
    parser.add_argument("--to-pad", required=True)
    parser.add_argument("--via-a", required=True)
    parser.add_argument("--via-b", required=True)
    parser.add_argument("--back-waypoints", default="")
    parser.add_argument("--width-mm", type=float, default=0.25)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--append", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    existing = [
        item
        for item in board.GetTracks()
        if item.GetNetname() == args.net
    ]
    if existing and args.replace:
        for item in existing:
            board.Remove(item)
    elif existing and not args.append:
        raise SystemExit(f"{args.net}: net already has routed copper")

    def pad(selector: str):
        reference, pin = selector.rsplit(".", 1)
        footprint = next(
            (item for item in board.GetFootprints() if item.GetReference() == reference),
            None,
        )
        if footprint is None:
            raise SystemExit(f"Footprint not found: {reference}")
        item = footprint.FindPadByNumber(pin)
        if item is None or item.GetNetname() != args.net:
            raise SystemExit(f"{selector} is not on net {args.net}")
        return item

    start_pad = pad(args.from_pad)
    end_pad = pad(args.to_pad)
    vias = [point(args.via_a), point(args.via_b)]
    back_points = [vias[0]]
    if args.back_waypoints:
        back_points.extend(point(item) for item in args.back_waypoints.split(";"))
    back_points.append(vias[1])

    retained = []

    def add_track(start, end, layer):
        start_copy = pcbnew.VECTOR2I(start.x, start.y)
        end_copy = pcbnew.VECTOR2I(end.x, end.y)
        retained.extend((start_copy, end_copy))
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(start_copy)
        track.SetEnd(end_copy)
        track.SetWidth(pcbnew.FromMM(args.width_mm))
        track.SetLayer(layer)
        track.SetNet(start_pad.GetNet())
        board.Add(track)

    add_track(start_pad.GetPosition(), vias[0], pcbnew.F_Cu)
    for start, end in zip(back_points, back_points[1:]):
        add_track(start, end, pcbnew.B_Cu)
    add_track(vias[1], end_pad.GetPosition(), pcbnew.F_Cu)

    retained_vias = []
    for via_point in vias:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(via_point.x, via_point.y))
        via.SetDrill(pcbnew.FromMM(0.4))
        via.SetWidth(pcbnew.FromMM(0.8))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(start_pad.GetNet())
        retained_vias.append(via)
        board.Add(via)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(
        f"{args.net}: routed {args.from_pad} -> {args.to_pad} with two vias "
        f"on F.Cu/B.Cu, width {args.width_mm:.3f} mm"
    )


if __name__ == "__main__":
    main()
