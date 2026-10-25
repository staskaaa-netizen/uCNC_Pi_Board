"""Branch one pad onto an existing same-net via through a new via."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def vector(value: str):
    return pcbnew.VECTOR2I_MM(*[float(item) for item in value.split(",")])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--net", required=True)
    parser.add_argument("--pad", required=True)
    parser.add_argument("--new-via", required=True)
    parser.add_argument("--target-via", required=True)
    parser.add_argument("--width-mm", type=float, default=0.25)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    reference, pin = args.pad.rsplit(".", 1)
    footprint = next(
        (item for item in board.GetFootprints() if item.GetReference() == reference),
        None,
    )
    if footprint is None:
        raise SystemExit(f"Footprint not found: {reference}")
    pad = footprint.FindPadByNumber(pin)
    if pad is None or pad.GetNetname() != args.net:
        raise SystemExit(f"{args.pad} is not on net {args.net}")

    new_position = vector(args.new_via)
    target_position = vector(args.target_via)
    existing = [
        item
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == args.net
        and abs(item.GetPosition().x - target_position.x) <= pcbnew.FromMM(0.001)
        and abs(item.GetPosition().y - target_position.y) <= pcbnew.FromMM(0.001)
    ]
    if not existing:
        raise SystemExit(f"No existing {args.net} via at {args.target_via}")

    pad_position = pad.GetPosition()
    start = pcbnew.VECTOR2I(pad_position.x, pad_position.y)
    retained = [start, new_position, target_position]
    for begin, end, layer in (
        (start, new_position, pcbnew.F_Cu),
        (new_position, target_position, pcbnew.B_Cu),
    ):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(begin)
        track.SetEnd(end)
        track.SetWidth(pcbnew.FromMM(args.width_mm))
        track.SetLayer(layer)
        track.SetNet(pad.GetNet())
        board.Add(track)

    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(new_position.x, new_position.y))
    via.SetDrill(pcbnew.FromMM(0.4))
    via.SetWidth(pcbnew.FromMM(0.8))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(pad.GetNet())
    board.Add(via)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"{args.pad}: branched through {args.new_via} to existing via {args.target_via}")


if __name__ == "__main__":
    main()
