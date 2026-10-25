"""Route an explicit polyline with stable scalar KiCad coordinates."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--net", required=True)
    parser.add_argument("--points", required=True)
    parser.add_argument("--layer", choices=("front", "back"), default="front")
    parser.add_argument("--width-mm", type=float, default=0.25)
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    if args.clear:
        for item in [
            track for track in board.GetTracks() if track.GetNetname() == args.net
        ]:
            board.Remove(item)

    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    coordinates = []
    selected_net = None
    for token in args.points.split(";"):
        token = token.strip()
        if "." in token and "," not in token:
            reference, pin = token.rsplit(".", 1)
            footprint = footprints.get(reference)
            if footprint is None:
                raise SystemExit(f"Footprint not found: {reference}")
            pad = footprint.FindPadByNumber(pin)
            if pad is None or pad.GetNetname() != args.net:
                raise SystemExit(f"{token} is not on net {args.net}")
            position = pad.GetPosition()
            coordinates.append((position.x, position.y))
            selected_net = selected_net or pad.GetNet()
        else:
            x, y = [float(value) for value in token.split(",")]
            coordinates.append((pcbnew.FromMM(x), pcbnew.FromMM(y)))

    layer = pcbnew.F_Cu if args.layer == "front" else pcbnew.B_Cu
    if selected_net is None:
        raise SystemExit("At least one point must be a pad selector")

    for (start_x, start_y), (end_x, end_y) in zip(coordinates, coordinates[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStartX(start_x)
        track.SetStartY(start_y)
        track.SetEndX(end_x)
        track.SetEndY(end_y)
        track.SetWidth(pcbnew.FromMM(args.width_mm))
        track.SetLayer(layer)
        track.SetNet(selected_net)
        board.Add(track)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"{args.net}: routed {len(coordinates) - 1} explicit segment(s)")


if __name__ == "__main__":
    main()
