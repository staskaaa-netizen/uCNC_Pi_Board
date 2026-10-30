"""Update selected footprint values and packages without moving them."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


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

    root = ET.parse(args.netlist).getroot()
    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}

    updates = []
    replacements = []
    for reference in args.ref:
        component = components.get(reference)
        footprint = footprints.get(reference)
        if component is None or footprint is None:
            continue
        value = (component.findtext("value") or "").strip()
        target_id = (component.findtext("footprint") or "").strip()
        target_name = target_id.rsplit(":", 1)[-1]
        actual_name = str(footprint.GetFPID().GetLibItemName())
        if footprint.GetValue() != value:
            updates.append((reference, footprint.GetValue(), value))
        if actual_name != target_name:
            new = load_footprint(target_id)
            old_pads = sorted(pad.GetNumber() for pad in footprint.Pads())
            new_pads = sorted(pad.GetNumber() for pad in new.Pads())
            if old_pads != new_pads:
                raise SystemExit(
                    f"{reference} replacement pad mismatch: {old_pads} != {new_pads}"
                )
            replacements.append((reference, actual_name, target_name))

    for message in updates:
        print(f"value {message[0]}: {message[1]} -> {message[2]}")
    for message in replacements:
        print(f"footprint {message[0]}: {message[1]} -> {message[2]}")
    print(
        f"value_updates={len(updates)} footprint_replacements={len(replacements)} "
        f"apply={args.apply}"
    )
    if not args.apply:
        return

    for reference in args.ref:
        component = components.get(reference)
        footprint = footprints.get(reference)
        if component is None or footprint is None:
            continue
        target_id = (component.findtext("footprint") or "").strip()
        target_name = target_id.rsplit(":", 1)[-1]
        actual_name = str(footprint.GetFPID().GetLibItemName())
        value = (component.findtext("value") or "").strip()
        if actual_name == target_name:
            footprint.SetValue(value)
            continue

        replacement = load_footprint(target_id)
        replacement.SetReference(reference)
        replacement.SetValue(value)
        replacement.SetPosition(footprint.GetPosition())
        replacement.SetOrientation(footprint.GetOrientation())
        replacement.SetLayer(footprint.GetLayer())
        replacement.SetLocked(footprint.IsLocked())
        replacement.SetDNP(footprint.IsDNP())
        for pad in replacement.Pads():
            old_pad = footprint.FindPadByNumber(pad.GetNumber())
            if old_pad is not None and old_pad.GetNetCode():
                pad.SetNet(old_pad.GetNet())
        board.Remove(footprint)
        board.Add(replacement)

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")


if __name__ == "__main__":
    main()
