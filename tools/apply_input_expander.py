"""Apply the 20-pin input-expander circuit without changing PCB copper."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"
REMOVED_REFERENCES = (
    "J9", "J16", "J17", "J27",
    "RN20", "RN21", "RN22", "RN24",
)
UPDATED_REFERENCES = ("J37", "U6", "U7", "RN6", "RN7", "RN23", "RN25")
NEW_PLACEMENTS = {
    "J37": (20.955, 51.275, 90.0),
    "RN23": (37.500, 60.000, 180.0),
    "RN25": (37.500, 55.000, 180.0),
}


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
    expected_pad_nets = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        for node in net.findall("node"):
            if node.get("ref") in UPDATED_REFERENCES:
                expected_pad_nets[(node.get("ref"), node.get("pin"))] = name

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    actions = []

    for reference in REMOVED_REFERENCES:
        if reference in footprints:
            actions.append(("remove", reference))
    for reference in UPDATED_REFERENCES:
        if reference not in footprints:
            actions.append(("add", reference))

    for action, reference in actions:
        print(f"{action} {reference}")
    print(f"actions={len(actions)} apply={args.apply}")
    if not args.apply:
        return

    for reference in REMOVED_REFERENCES:
        footprint = footprints.get(reference)
        if footprint is not None:
            board.Remove(footprint)

    for reference in UPDATED_REFERENCES:
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from netlist")
        footprint = board.FindFootprintByReference(reference)
        target_footprint = (component.findtext("footprint") or "").strip()
        value = (component.findtext("value") or "").strip()
        if footprint is None:
            footprint = load_footprint(target_footprint)
            footprint.SetReference(reference)
            footprint.SetValue(value)
            x, y, rotation = NEW_PLACEMENTS[reference]
            footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            footprint.SetOrientationDegrees(rotation)
            board.Add(footprint)
        else:
            footprint.SetValue(value)

        for pad in footprint.Pads():
            net_name = expected_pad_nets.get((reference, pad.GetNumber()), "")
            net = board.FindNet(net_name) if net_name else None
            if net_name and net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
