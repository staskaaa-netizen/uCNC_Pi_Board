"""Replace Q1 with the 40 V IRF7240PBF SO-8 input MOSFET."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
FOOTPRINT_DIR = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0"
    r"\share\kicad\footprints\Package_SO.pretty"
)
FOOTPRINT_NAME = "SOIC-8_3.9x4.9mm_P1.27mm"
NET_BY_PAD = {
    "1": "VIN_PROT",
    "2": "VIN_PROT",
    "3": "VIN_PROT",
    "4": "Q1_GATE",
    "5": "VIN_FUSED",
    "6": "VIN_FUSED",
    "7": "VIN_FUSED",
    "8": "VIN_FUSED",
}


def ensure_power_pad_bridges(board, footprint) -> int:
    """Bond adjacent same-net SO-8 source and drain pads with short copper."""
    pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
    added = 0
    for first, second in (("1", "2"), ("2", "3"), ("5", "6"), ("6", "7"), ("7", "8")):
        start = pads[first].GetPosition()
        end = pads[second].GetPosition()
        net = pads[first].GetNet()
        exists = any(
            track.GetClass() == "PCB_TRACK"
            and track.GetLayer() == pcbnew.F_Cu
            and track.GetNetCode() == net.GetNetCode()
            and {
                (track.GetStart().x, track.GetStart().y),
                (track.GetEnd().x, track.GetEnd().y),
            }
            == {(start.x, start.y), (end.x, end.y)}
            for track in board.GetTracks()
        )
        if exists:
            continue
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(start)
        track.SetEnd(end)
        track.SetWidth(pcbnew.FromMM(0.8))
        track.SetLayer(pcbnew.F_Cu)
        track.SetNet(net)
        board.Add(track)
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    old = next(
        (item for item in board.GetFootprints() if item.GetReference() == "Q1"),
        None,
    )
    if old is None:
        raise SystemExit("Q1 not found")
    print(
        "Q1:",
        old.GetValue(),
        old.GetFPID().GetLibItemName(),
        pcbnew.ToMM(old.GetPosition().x),
        pcbnew.ToMM(old.GetPosition().y),
        old.GetOrientationDegrees(),
    )
    if not args.apply:
        return

    replacement = old
    if old.GetFPID().GetLibItemName() != FOOTPRINT_NAME:
        position = old.GetPosition()
        orientation = old.GetOrientationDegrees()
        layer = old.GetLayer()
        locked = old.IsLocked()
        path = old.GetPath()
        board.Remove(old)

        replacement = pcbnew.FootprintLoad(str(FOOTPRINT_DIR), FOOTPRINT_NAME)
        if replacement is None:
            raise SystemExit(f"Footprint not found: {FOOTPRINT_NAME}")
        replacement.SetReference("Q1")
        replacement.SetPosition(position)
        replacement.SetOrientationDegrees(orientation)
        replacement.SetLayer(layer)
        replacement.SetLocked(locked)
        replacement.SetPath(path)
        board.Add(replacement)
    replacement.SetValue("IRF7240PBF")
    replacement.Reference().SetLayer(
        pcbnew.B_Fab
        if replacement.GetLayer() == pcbnew.B_Cu
        else pcbnew.F_Fab
    )
    replacement.Value().SetLayer(
        pcbnew.B_Fab
        if replacement.GetLayer() == pcbnew.B_Cu
        else pcbnew.F_Fab
    )
    for pad in replacement.Pads():
        net_name = NET_BY_PAD.get(pad.GetNumber())
        if net_name is None:
            raise SystemExit(f"Unexpected Q1 pad {pad.GetNumber()}")
        pad.SetNet(board.FindNet(net_name))
    bridges = ensure_power_pad_bridges(board, replacement)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(
        f"Q1 is IRF7240PBF in {FOOTPRINT_NAME}; "
        f"added {bridges} power-pad bridge tracks"
    )


if __name__ == "__main__":
    main()
