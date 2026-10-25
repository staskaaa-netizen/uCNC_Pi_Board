"""Add the isolated dry-contact supply and field-mode selectors to the PCB."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint, put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"

PLACEMENTS = {
    "U40": (39.0, 130.5, 270.0, "front"),
    "F4": (44.5, 130.5, 270.0, "front"),
    "C103": (37.0, 134.0, 180.0, "front"),
    "C105": (27.5, 134.0, 0.0, "front"),
    "D56": (17.5, 132.5, 90.0, "front"),
    "RN22": (24.0, 54.0, 90.0, "front"),
    "RN24": (36.5, 53.5, 90.0, "front"),
    "JP2": (15.0, 69.5, 0.0, "back"),
    "JP3": (15.0, 90.0, 0.0, "back"),
    "JP4": (15.0, 110.0, 0.0, "back"),
}


NET_SYNC_REFS = {
    *(f"D{number}" for number in range(14, 45, 2)),
    "D10",
    "D12",
    "D55",
    "U18",
    "U19",
    "U20",
    "U21",
    "U35",
    "U36",
    "U39",
    *PLACEMENTS,
}

SILK_NOTES = {
    "J7 1-2=24V  2-3=CONTACT": (34.0, 70.0),
    "J8 1-2=24V  2-3=CONTACT": (34.0, 90.0),
    "SAFETY 1-2=24V  2-3=CONTACT": (40.0, 110.0),
}

LEGACY_SILK_REPLACEMENTS = {
    "BANK0  24V: JP2   ISO5V: JP3+JP4": "J7 1-2=24V  2-3=CONTACT",
    "BANK1  24V: JP5   ISO5V: JP6+JP7": "J8 1-2=24V  2-3=CONTACT",
    "SAFETY 24V: JP8   ISO5V: JP9+JP10": "SAFETY 1-2=24V  2-3=CONTACT",
    "J7 BANK 24V: JP2  ISO5V: JP3+JP4": "J7 1-2=24V  2-3=CONTACT",
    "J8 BANK 24V: JP5  ISO5V: JP6+JP7": "J8 1-2=24V  2-3=CONTACT",
    "SAFETY 24V: JP8  ISO5V: JP9+JP10": "SAFETY 1-2=24V  2-3=CONTACT",
}


def add_silk_notes(board) -> int:
    existing = set()
    for item in board.GetDrawings():
        if not isinstance(item, pcbnew.PCB_TEXT):
            continue
        if item.GetText() in LEGACY_SILK_REPLACEMENTS:
            item.SetText(LEGACY_SILK_REPLACEMENTS[item.GetText()])
        if item.GetText() in SILK_NOTES:
            item.SetMirrored(True)
            x, y = SILK_NOTES[item.GetText()]
            item.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            existing.add(item.GetText())
    added = 0
    for text, (x, y) in SILK_NOTES.items():
        if text in existing:
            continue
        item = pcbnew.PCB_TEXT(board)
        item.SetText(text)
        item.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        item.SetLayer(pcbnew.B_SilkS)
        item.SetTextSize(pcbnew.VECTOR2I_MM(0.8, 0.8))
        item.SetTextThickness(pcbnew.FromMM(0.12))
        item.SetMirrored(True)
        board.Add(item)
        added += 1
    return added


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--netlist", type=Path, default=DEFAULT_NETLIST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    print("Reading field-supply netlist...")
    root = ET.parse(args.netlist).getroot()
    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    expected_nets = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        if name.startswith("unconnected-"):
            continue
        for node in net.findall("node"):
            key = (node.get("ref", ""), node.get("pin", ""))
            if key[0] in NET_SYNC_REFS:
                expected_nets[key] = name

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    print(f"Board footprints before update: {len(footprints)}")
    obsolete = sorted({"C104", "C106"} & footprints.keys())
    if obsolete:
        raise SystemExit(
            "Remove obsolete footprints first: " + ", ".join(obsolete)
        )
    added = []
    for reference, (x, y, rotation, side) in PLACEMENTS.items():
        component = components.get(reference)
        if component is None:
            raise RuntimeError(f"{reference} missing from netlist")
        footprint = footprints.get(reference)
        if footprint is None:
            print(f"Loading {reference}...", flush=True)
            footprint_id = (component.findtext("footprint") or "").strip()
            footprint = load_footprint(footprint_id)
            footprint.SetReference(reference)
            footprint.SetValue((component.findtext("value") or "").strip())
            board.Add(footprint)
            footprints[reference] = footprint
            added.append(reference)
        else:
            footprint.SetValue((component.findtext("value") or "").strip())
        if reference in {"C103", "C105", "D56"}:
            footprint.Reference().SetVisible(False)
        elif reference == "F4":
            footprint.Reference().SetVisible(False)
        elif reference == "U40":
            footprint.Reference().SetPosition(pcbnew.VECTOR2I_MM(39.0, 122.5))
            footprint.Reference().SetLayer(pcbnew.B_SilkS)
            footprint.Reference().SetMirrored(True)
        put_on_side(footprint, back=side == "back")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)

    print(f"Missing footprints added in memory: {len(added)}")
    changes = []
    for reference in sorted(NET_SYNC_REFS):
        footprint = footprints[reference]
        for pad in footprint.Pads():
            new_name = expected_nets.get((reference, pad.GetNumber()))
            if new_name is None:
                continue
            old_name = pad.GetNetname()
            if old_name == new_name:
                continue
            net = board.FindNet(new_name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, new_name)
                board.Add(net)
            pad.SetNet(net)
            changes.append((reference, pad.GetNumber(), old_name, new_name))

    print(f"added={','.join(added)}")
    print(f"pad_net_changes={len(changes)}")
    print(f"silk_notes_added={add_silk_notes(board)}")
    for reference, pin, old_name, new_name in changes:
        print(f"{reference}.{pin}: {old_name} -> {new_name}")
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
