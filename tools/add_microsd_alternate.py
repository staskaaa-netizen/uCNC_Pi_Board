"""Add the optional microSD alternate connector without touching copper."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"
PLACEMENT_MM = (208.0, 68.58, 90.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    component = next(
        (
            item
            for item in root.findall("./components/comp")
            if item.get("ref") == "J36"
        ),
        None,
    )
    if component is None:
        raise SystemExit("Netlist does not contain J36")
    node_nets = {
        node.get("pin", ""): net.get("name", "")
        for net in root.findall("./nets/net")
        for node in net.findall("node")
        if node.get("ref") == "J36"
        and not net.get("name", "").startswith("unconnected-")
    }

    board = pcbnew.LoadBoard(str(args.board))
    track_uuids = {item.m_Uuid.AsString() for item in board.GetTracks()}
    footprint = next(
        (
            item
            for item in board.GetFootprints()
            if item.GetReference() == "J36"
        ),
        None,
    )
    added = footprint is None
    if footprint is None:
        footprint_id = (component.findtext("footprint") or "").strip()
        footprint = load_footprint(footprint_id)
        footprint.SetReference("J36")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(*PLACEMENT_MM[:2]))
        footprint.SetOrientationDegrees(PLACEMENT_MM[2])
        footprint.SetLayer(pcbnew.F_Cu)
        footprint.SetLocked(False)
        board.Add(footprint)

    footprint.SetValue((component.findtext("value") or "").strip())
    footprint.SetDNP(True)
    for pad in footprint.Pads():
        net_name = node_nets.get(pad.GetNumber(), "")
        net = board.FindNet(net_name) if net_name else None
        if net_name and net is None:
            net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(net)
        pad.SetNet(net)

    if {item.m_Uuid.AsString() for item in board.GetTracks()} != track_uuids:
        raise SystemExit("Copper routing changed; refusing to save")
    print(
        f"J36 added={added} position={PLACEMENT_MM} "
        f"footprint={footprint.GetFPID().GetLibItemName()} DNP={footprint.IsDNP()}"
    )
    print(f"tracks_unchanged={len(track_uuids)}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
