"""Replace discrete shift-control resistors R10-R13 with one 4x10k array."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"
REMOVED_REFERENCES = ("R10", "R11", "R12", "R13")
ARRAY_REFERENCE = "RN41"
ARRAY_POSITION = (95.6945, 67.183)
ARRAY_ROTATION = 0.0


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
            if item.get("ref") == ARRAY_REFERENCE
        ),
        None,
    )
    if component is None:
        raise SystemExit(f"{ARRAY_REFERENCE} is missing from the netlist")
    expected_nets = {}
    for net in root.findall("./nets/net"):
        for node in net.findall("node"):
            if node.get("ref") == ARRAY_REFERENCE:
                expected_nets[node.get("pin", "")] = net.get("name", "")

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    present = [ref for ref in REMOVED_REFERENCES if ref in footprints]
    if ARRAY_REFERENCE in footprints:
        raise SystemExit(f"{ARRAY_REFERENCE} already exists")
    print(f"remove={present}")
    print(f"add={ARRAY_REFERENCE} at {ARRAY_POSITION} rotation={ARRAY_ROTATION}")
    print(f"initial_tracks={len(list(board.GetTracks()))} apply={args.apply}")
    if not args.apply:
        return

    for reference in present:
        board.Remove(footprints[reference])

    footprint_id = (component.findtext("footprint") or "").strip()
    footprint = load_footprint(footprint_id)
    footprint.SetReference(ARRAY_REFERENCE)
    footprint.SetValue((component.findtext("value") or "").strip())
    footprint.SetPosition(pcbnew.VECTOR2I_MM(*ARRAY_POSITION))
    footprint.SetOrientationDegrees(ARRAY_ROTATION)
    for pad in footprint.Pads():
        net_name = expected_nets.get(pad.GetNumber(), "")
        net = board.FindNet(net_name) if net_name else None
        if net_name and net is None:
            net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(net)
        pad.SetNet(net)
    board.Add(footprint)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")
    print(f"final_tracks={len(list(board.GetTracks()))}")


if __name__ == "__main__":
    main()
