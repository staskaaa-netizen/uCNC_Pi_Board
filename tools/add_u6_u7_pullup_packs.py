"""Add the four U6/U7 4 x 10 k pull-up arrays to the staged PCB."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
NETLIST = ROOT / "hardware" / "motherboard.net.xml"
REFERENCES = ("RN45", "RN46", "RN47", "RN48")
PARK_X_MM = 190.0
PARK_Y_MM = 10.0
PARK_PITCH_MM = 10.0


def board_net(board, name: str):
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def netlist_parts():
    root = ET.parse(NETLIST).getroot()
    nets: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        for node in net.findall("./node"):
            nets[(node.get("ref", ""), node.get("pin", ""))] = net.get("name", "")
    return {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
        if component.get("ref") in REFERENCES
    }, nets


def set_fields(footprint, component) -> None:
    fields = {
        field.get("name", ""): field.get("value", "")
        for field in component.findall("./fields/field")
    }
    for name in ("MPN", "Manufacturer", "Footprint", "Datasheet", "Description"):
        if name in fields:
            footprint.SetField(name, fields[name])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    parts, nets = netlist_parts()
    missing = sorted(set(REFERENCES) - set(parts))
    if missing:
        raise RuntimeError(f"Pull-up arrays missing from netlist: {missing}")

    board = pcbnew.LoadBoard(str(BOARD))
    added = []
    updated = []
    for index, reference in enumerate(REFERENCES):
        component = parts[reference]
        footprint_id = (component.findtext("footprint") or "").strip()
        footprint = board.FindFootprintByReference(reference)
        if footprint is None:
            footprint = load_footprint(footprint_id)
            footprint.SetReference(reference)
            footprint.SetValue((component.findtext("value") or "").strip())
            footprint.SetPosition(
                pcbnew.VECTOR2I_MM(PARK_X_MM + index * PARK_PITCH_MM, PARK_Y_MM)
            )
            footprint.SetOrientationDegrees(0)
            footprint.SetLayer(pcbnew.F_Cu)
            board.Add(footprint)
            added.append(reference)
        else:
            updated.append(reference)

        set_fields(footprint, component)
        for pad in footprint.Pads():
            net_name = nets.get((reference, pad.GetNumber()))
            if net_name:
                pad.SetNet(board_net(board, net_name))

    board.BuildConnectivity()
    if args.apply:
        pcbnew.SaveBoard(str(BOARD), board)
        print(f"Saved {BOARD}")
    print(
        {
            "added": added,
            "updated": updated,
            "parked_at_mm": {
                reference: (
                    PARK_X_MM + index * PARK_PITCH_MM,
                    PARK_Y_MM,
                )
                for index, reference in enumerate(REFERENCES)
            },
            "apply": args.apply,
        }
    )


if __name__ == "__main__":
    main()
