"""Connect one pad to a new through-via on the same net."""

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
    parser.add_argument("--pad", required=True)
    parser.add_argument("--via-at", required=True)
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

    via_position = pcbnew.VECTOR2I_MM(
        *[float(item) for item in args.via_at.split(",")]
    )
    pad_position = pad.GetPosition()
    start = pcbnew.VECTOR2I(pad_position.x, pad_position.y)
    retained = [start, via_position]

    track = pcbnew.PCB_TRACK(board)
    track.SetStart(start)
    track.SetEnd(via_position)
    track.SetWidth(pcbnew.FromMM(args.width_mm))
    track.SetLayer(pcbnew.F_Cu)
    track.SetNet(pad.GetNet())
    board.Add(track)

    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(via_position.x, via_position.y))
    via.SetDrill(pcbnew.FromMM(0.4))
    via.SetWidth(pcbnew.FromMM(0.8))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetNet(pad.GetNet())
    board.Add(via)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"{args.pad}: connected to {args.net} via at {args.via_at}")


if __name__ == "__main__":
    main()
