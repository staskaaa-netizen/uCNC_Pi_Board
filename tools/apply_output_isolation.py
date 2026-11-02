"""Apply buffered motion and opto-isolated general outputs without routing."""

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
    "J6", "J19", "J26",
    "R17", "R75", "R108", "R109",
    "D11", "D12", "D54", "D55",
    "R44", "R45", "R46", "R47", "R48", "R49",
    "U41", "C106",
    *(f"U{index}" for index in range(47, 61)),
    *(f"U{index}" for index in range(66, 78)),
    "Q5", "Q6", "Q7",
    "R113", "R114", "R115", "R116", "R117",
    "C55", "C56", "C117",
    "U44", "U65",
    *(f"R{index}" for index in range(132, 149)),
    *(f"R{index}" for index in range(149, 165)),
    "RN14", "RN15",
    *(f"RN{index}" for index in range(16, 23)),
    "RN24",
)
UPDATED_REFERENCES = (
    tuple(f"U{index}" for index in range(6, 14))
    + tuple(f"U{index}" for index in range(18, 22))
    + ("U26", "U27", "U28", "U35", "U36", "U39", "U45", "U46")
    + ("R16", "R17", "R108")
    + tuple(f"R{index}" for index in range(18, 34))
    + ("D9", "D10", "D11", "D12", "D54", "D55")
    + tuple(f"D{index}" for index in range(13, 45))
    + tuple(f"U{index}" for index in range(42, 44))
    + tuple(f"U{index}" for index in range(61, 65))
    + ("RN6", "RN7", "RN8", "RN9", "RN10", "RN11", "RN12", "RN13")
    + ("RN23", "RN25", "RN30", "RN31", "RN32", "RN33", "RN34", "RN35", "RN36")
    + ("RN37", "RN38", "RN39", "RN40")
    + ("RN26", "RN27", "RN42", "RN43", "J31", "J32", "J33", "J36", "J37")
)
NEW_REFERENCES = (
    tuple(f"U{index}" for index in range(18, 22))
    + ("U36", "U39", "U42", "U43", "U45", "U46")
    + tuple(f"U{index}" for index in range(61, 65))
    + ("RN10", "RN11", "RN12", "RN13")
    + ("RN23", "RN25", "RN35", "RN37", "RN38", "RN39", "RN40")
    + ("RN42", "RN43")
    + ("R74", "R75", "R109")
    + tuple(f"R{index}" for index in range(34, 42))
    + tuple(f"R{index}" for index in range(118, 126))
    + tuple(f"R{index}" for index in range(166, 182))
    + tuple(f"D{index}" for index in range(65, 97))
    + ("C57", "C115", "C116")
)


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
    selected = set(UPDATED_REFERENCES) | set(NEW_REFERENCES)
    expected_nets = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        for node in net.findall("node"):
            if node.get("ref") in selected:
                expected_nets[(node.get("ref"), node.get("pin"))] = name

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    actions = [("remove", ref) for ref in REMOVED_REFERENCES if ref in footprints]
    actions.extend(
        ("add", ref) for ref in NEW_REFERENCES if ref not in footprints
    )
    for action, reference in actions:
        print(f"{action} {reference}")
    print(f"actions={len(actions)} apply={args.apply}")
    if not args.apply:
        return

    for reference in REMOVED_REFERENCES:
        footprint = footprints.get(reference)
        if footprint is not None:
            board.Remove(footprint)
    print(f"board_footprints_after_remove={len(board.GetFootprints())}")

    for index, reference in enumerate(NEW_REFERENCES):
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from netlist")
        footprint = footprints.get(reference)
        target = (component.findtext("footprint") or "").strip()
        value = (component.findtext("value") or "").strip()
        if footprint is None:
            footprint = load_footprint(target)
            footprint.SetReference(reference)
            footprint.SetValue(value)
            x = 620.0 + (index // 20) * 24.0
            y = 20.0 + (index % 20) * 15.0
            footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            board.Add(footprint)
            footprints[reference] = footprint
        for pad in footprint.Pads():
            net_name = expected_nets.get((reference, pad.GetNumber()), "")
            net = board.FindNet(net_name) if net_name else None
            if net_name and net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)
    print(f"board_footprints_after_add={len(board.GetFootprints())}")

    for reference in UPDATED_REFERENCES:
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from netlist")
        footprint = footprints.get(reference)
        if footprint is None:
            raise SystemExit(f"Missing footprint {reference}")
        target = (component.findtext("footprint") or "").strip()
        value = (component.findtext("value") or "").strip()
        target_name = target.rsplit(":", 1)[-1]
        actual_name = str(footprint.GetFPID().GetLibItemName())
        assembly = next(
            (
                prop.get("value", "")
                for prop in component.findall("property")
                if prop.get("name") == "Assembly"
            ),
            "FIT",
        )
        if actual_name != target_name:
            replacement = load_footprint(target)
            replacement.SetReference(reference)
            replacement.SetValue(value)
            replacement.SetPosition(footprint.GetPosition())
            replacement.SetOrientation(footprint.GetOrientation())
            replacement.SetLayer(footprint.GetLayer())
            replacement.SetLocked(footprint.IsLocked())
            replacement.SetDNP(assembly == "DNP")
            for pad in replacement.Pads():
                net_name = expected_nets.get((reference, pad.GetNumber()), "")
                net = board.FindNet(net_name) if net_name else None
                if net_name and net is None:
                    net = pcbnew.NETINFO_ITEM(board, net_name)
                    board.Add(net)
                pad.SetNet(net)
            board.Remove(footprint)
            board.Add(replacement)
            continue
        else:
            footprint.SetValue(value)
            footprint.SetDNP(assembly == "DNP")
        for pad in footprint.Pads():
            net_name = expected_nets.get((reference, pad.GetNumber()), "")
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
