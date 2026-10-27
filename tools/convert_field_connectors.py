"""Replace non-standard field connector footprints while preserving layout."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
NETLIST = ROOT / "hardware" / "motherboard.net.xml"

PLACEMENTS = {
    "J7": ((8.0, 12.0), -90.0),
    "J8": ((8.0, 74.5), -90.0),
    "J12": ((86.132, 6.558), 180.0),
    "J24": ((118.75, 145.0), 0.0),
    "J25": ((149.75, 145.0), 0.0),
    "J1": ((177.368, 144.942), 0.0),
}
REPLACE = {"J7", "J8", "J12", "J24"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--netlist", type=Path, default=NETLIST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    expected_footprints = {
        component.get("ref", ""): (component.findtext("footprint") or "").strip()
        for component in root.findall("./components/comp")
    }
    net_nodes = {
        (node.get("ref", ""), node.get("pin", "")): net.get("name", "")
        for net in root.findall("./nets/net")
        if not net.get("name", "").startswith("unconnected-")
        for node in net.findall("node")
    }

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    changes = []
    for reference in REPLACE:
        old = footprints[reference]
        target = expected_footprints[reference]
        current = (
            f"{old.GetFPID().GetLibNickname()}:{old.GetFPID().GetLibItemName()}"
        )
        if current != target:
            changes.append((reference, current, target))
    for reference, (position, rotation) in PLACEMENTS.items():
        old = footprints[reference]
        current_position = old.GetPosition()
        if (
            abs(pcbnew.ToMM(current_position.x) - position[0]) > 1e-6
            or abs(pcbnew.ToMM(current_position.y) - position[1]) > 1e-6
            or abs(old.GetOrientationDegrees() - rotation) > 1e-6
        ):
            changes.append(
                (
                    reference,
                    (
                        round(pcbnew.ToMM(current_position.x), 3),
                        round(pcbnew.ToMM(current_position.y), 3),
                        old.GetOrientationDegrees(),
                    ),
                    (*position, rotation),
                )
            )

    for reference, before, after in changes:
        print(f"{reference}: {before} -> {after}")
    print(f"changes={len(changes)} apply={args.apply}")
    if not args.apply:
        return

    for reference in REPLACE:
        old = footprints[reference]
        target = expected_footprints[reference]
        current = (
            f"{old.GetFPID().GetLibNickname()}:{old.GetFPID().GetLibItemName()}"
        )
        if current == target:
            continue
        new = load_footprint(target)
        position, rotation = PLACEMENTS[reference]
        new.SetReference(reference)
        new.SetValue(old.GetValue())
        new.SetDNP(old.IsDNP())
        new.SetLayer(old.GetLayer())
        new.SetPosition(pcbnew.VECTOR2I_MM(*position))
        new.SetOrientationDegrees(rotation)
        for pad in new.Pads():
            net_name = net_nodes.get((reference, pad.GetNumber()))
            if net_name:
                net = board.FindNet(net_name)
                if net is None:
                    net = pcbnew.NETINFO_ITEM(board, net_name)
                    board.Add(net)
                pad.SetNet(net)
        board.Remove(old)
        board.Add(new)

    for reference, (position, rotation) in PLACEMENTS.items():
        footprint = next(
            fp for fp in board.GetFootprints() if fp.GetReference() == reference
        )
        footprint.SetPosition(pcbnew.VECTOR2I_MM(*position))
        footprint.SetOrientationDegrees(rotation)

    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
