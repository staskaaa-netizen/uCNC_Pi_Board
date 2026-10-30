"""Restore the fitted quad/DIP optocouplers while keeping RN32-RN36."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"

PLACEMENTS = {
    "U18": (46.5, 104.5, 0.0),
    "U19": (46.5, 119.5, 0.0),
    "U20": (46.5, 76.0, 0.0),
    "U21": (46.5, 90.5, 0.0),
    "U35": (89.468, 128.442, 90.0),
    "U36": (99.567, 128.5, 90.0),
    "U39": (109.725, 128.605, 90.0),
}
REMOVE_ONLY = {f"U{index}" for index in range(42, 54)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    node_nets = {
        (node.get("ref", ""), node.get("pin", "")): net.get("name", "")
        for net in root.findall("./nets/net")
        for node in net.findall("node")
        if not net.get("name", "").startswith("unconnected-")
    }
    missing = sorted(set(PLACEMENTS) - components.keys())
    if missing:
        raise SystemExit(f"Netlist is missing restored components: {missing}")

    board = pcbnew.LoadBoard(str(args.board))
    original_track_uuids = {
        item.m_Uuid.AsString() for item in board.GetTracks()
    }
    old = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    removed = []
    for reference in sorted(set(PLACEMENTS) | REMOVE_ONLY):
        footprint = old.get(reference)
        if footprint is not None:
            board.Remove(footprint)
            removed.append(reference)

    added = []
    for reference in sorted(PLACEMENTS):
        component = components[reference]
        footprint_name = (component.findtext("footprint") or "").strip()
        footprint = load_footprint(footprint_name)
        footprint.SetReference(reference)
        x, y, rotation = PLACEMENTS[reference]
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        footprint.SetLayer(pcbnew.F_Cu)
        footprint.SetLocked(False)
        footprint.SetDNP(False)
        footprint.SetValue((component.findtext("value") or "").strip())
        for pad in footprint.Pads():
            net_name = node_nets.get((reference, pad.GetNumber()))
            if not net_name:
                pad.SetNet(None)
                continue
            net = board.FindNet(net_name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)
        board.Add(footprint)
        added.append(reference)

    final_track_uuids = {
        item.m_Uuid.AsString() for item in board.GetTracks()
    }
    if final_track_uuids != original_track_uuids:
        raise SystemExit("Copper routing changed; refusing to save")

    print(f"removed={removed}")
    print(f"restored={added}")
    print(f"tracks_unchanged={len(final_track_uuids)}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
