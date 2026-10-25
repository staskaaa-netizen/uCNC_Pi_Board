"""Synchronize PCB footprint libraries with the authoritative KiCad netlist.

Positions, rotations, layers, values, DNP state and pad nets are preserved.
This is intended for controlled footprint substitutions on a manually staged
board.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
NETLIST = ROOT / "hardware" / "motherboard.net.xml"
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--netlist", type=Path, default=NETLIST)
    parser.add_argument("--ref", action="append")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    expected = {
        component.get("ref", ""): (component.findtext("footprint") or "").strip()
        for component in root.findall("./components/comp")
        if (component.findtext("footprint") or "").strip()
    }
    board = pcbnew.LoadBoard(str(args.board))
    selected = set(args.ref) if args.ref else None
    old_footprints = list(board.GetFootprints())
    changes = []
    skipped = []
    for old in old_footprints:
        reference = old.GetReference()
        target = expected.get(reference)
        if not target:
            continue
        if selected is not None:
            if reference not in selected:
                continue
        elif not target.startswith("Connector_Phoenix_MC:"):
            continue
        old_id = (
            f"{old.GetFPID().GetLibNickname()}:{old.GetFPID().GetLibItemName()}"
        )
        if old_id == target:
            continue
        new = load_footprint(target)
        if [
            pad.GetNumber() for pad in new.Pads()
        ] != [
            pad.GetNumber() for pad in old.Pads()
        ]:
            skipped.append((reference, target))
            continue
        changes.append((old, new, target))

    for old, _, target in sorted(changes, key=lambda item: item[0].GetReference()):
        reference = old.GetReference()
        print(f"{reference:6s} -> {target}")
    for reference, target in skipped:
        print(f"{reference:6s} skipped pad mismatch -> {target}")
    print(f"footprint_changes={len(changes)} apply={args.apply}")
    if not args.apply:
        return

    for old, new, _ in changes:
        position = old.GetPosition()
        orientation = old.GetOrientation()
        new.SetReference(old.GetReference())
        new.SetValue(old.GetValue())
        new.SetDNP(old.IsDNP())
        new.SetPosition(position)
        new.SetOrientation(orientation)
        new.SetLayer(old.GetLayer())
        for pad in new.Pads():
            old_pad = old.FindPadByNumber(pad.GetNumber())
            if old_pad is not None and old_pad.GetNetCode():
                pad.SetNet(old_pad.GetNet())
        board.Remove(old)
        board.Add(new)

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
