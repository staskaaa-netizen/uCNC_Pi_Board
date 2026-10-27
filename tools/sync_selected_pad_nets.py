"""Apply netlist pad assignments to selected footprints while preserving layout."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--ref", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    selected = set(args.ref)
    root = ET.parse(args.netlist).getroot()
    expected = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        if name.startswith("unconnected-"):
            continue
        for node in net.findall("node"):
            reference = node.get("ref", "")
            if reference in selected:
                expected[(reference, node.get("pin", ""))] = name

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(selected - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")

    changes = []
    for reference in sorted(selected):
        for pad in footprints[reference].Pads():
            key = (reference, pad.GetNumber())
            new_name = expected.get(key, "")
            old_name = pad.GetNetname()
            if old_name != new_name:
                changes.append((reference, pad.GetNumber(), old_name, new_name))

    for reference, pin, old_name, new_name in changes:
        print(f"{reference}.{pin}: {old_name} -> {new_name}")
    print(f"pad_net_changes={len(changes)} apply={args.apply}")
    if not args.apply:
        return

    for reference, pin, _, new_name in changes:
        pad = footprints[reference].FindPadByNumber(pin)
        if not new_name:
            pad.SetNet(None)
            continue
        net = board.FindNet(new_name)
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, new_name)
            board.Add(net)
        pad.SetNet(net)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
