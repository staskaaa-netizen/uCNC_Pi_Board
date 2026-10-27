"""Add the second open-collector connector and two MOSFET sinks."""

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
    "J32": {
        "position": (81.0, 6.75),
        "rotation": 180.0,
        "back": False,
    },
    "J33": {
        "position": (173.5, 145.0),
        "rotation": 180.0,
        "back": False,
    },
    "J34": {
        "position": (8.0, 43.25),
        "rotation": -90.0,
        "back": False,
    },
    "J35": {
        "position": (8.0, 105.75),
        "rotation": -90.0,
        "back": False,
    },
    "Q6": {
        "position": (50.0, 36.5),
        "rotation": 0.0,
        "back": True,
    },
    "Q7": {
        "position": (55.5, 36.5),
        "rotation": 0.0,
        "back": True,
    },
    "R114": {
        "position": (48.5, 39.5),
        "rotation": 0.0,
        "back": True,
    },
    "R115": {
        "position": (50.0, 42.0),
        "rotation": 0.0,
        "back": True,
    },
    "R116": {
        "position": (54.0, 39.5),
        "rotation": 0.0,
        "back": True,
    },
    "R117": {
        "position": (55.5, 42.0),
        "rotation": 0.0,
        "back": True,
    },
    "RN30": {
        "position": (50.5, 24.0),
        "rotation": 0.0,
        "back": False,
    },
    "RN31": {
        "position": (31.0, 25.0),
        "rotation": 0.0,
        "back": False,
    },
    **{
        f"D{57 + index}": {
            "position": (41.536 - index * 3.5, 14.143),
            "rotation": 90.0,
            "back": False,
        }
        for index in range(8)
    },
    **{
        f"R{118 + index}": {
            "position": (41.536 - index * 3.5, 19.142),
            "rotation": 90.0,
            "back": False,
        }
        for index in range(8)
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--netlist", type=Path, default=NETLIST)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    net_nodes: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        if name.startswith("unconnected-"):
            continue
        for node in net.findall("node"):
            net_nodes[(node.get("ref", ""), node.get("pin", ""))] = name

    components = {
        component.get("ref", ""): component
        for component in root.findall("./components/comp")
    }
    board = pcbnew.LoadBoard(str(args.board))
    existing = {footprint.GetReference() for footprint in board.GetFootprints()}

    additions = []
    for reference, placement in PLACEMENTS.items():
        if reference in existing:
            print(f"keep {reference}: already present")
            continue
        component = components[reference]
        footprint_id = (component.findtext("footprint") or "").strip()
        footprint = load_footprint(footprint_id)
        footprint.SetReference(reference)
        footprint.SetValue((component.findtext("value") or "").strip())
        footprint.SetPosition(pcbnew.VECTOR2I_MM(*placement["position"]))
        footprint.SetOrientationDegrees(placement["rotation"])
        footprint.SetLayer(
            pcbnew.B_Cu if placement["back"] else pcbnew.F_Cu
        )

        for pad in footprint.Pads():
            net_name = net_nodes.get((reference, pad.GetNumber()))
            if not net_name:
                continue
            net = board.FindNet(net_name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)
        additions.append((reference, footprint_id))

    for reference, footprint_id in additions:
        print(f"add {reference}: {footprint_id}")
    print(f"additions={len(additions)} apply={args.apply}")
    if not args.apply:
        return

    for reference, _ in additions:
        component = components[reference]
        footprint_id = (component.findtext("footprint") or "").strip()
        placement = PLACEMENTS[reference]
        footprint = load_footprint(footprint_id)
        footprint.SetReference(reference)
        footprint.SetValue((component.findtext("value") or "").strip())
        footprint.SetPosition(pcbnew.VECTOR2I_MM(*placement["position"]))
        footprint.SetOrientationDegrees(placement["rotation"])
        if placement["back"]:
            board.Add(footprint)
            footprint.Flip(
                footprint.GetPosition(),
                pcbnew.FLIP_DIRECTION_LEFT_RIGHT,
            )
            footprint.SetOrientationDegrees(placement["rotation"])
            footprint.SetPosition(pcbnew.VECTOR2I_MM(*placement["position"]))
        else:
            footprint.SetLayer(pcbnew.F_Cu)
            board.Add(footprint)
        for pad in footprint.Pads():
            net_name = net_nodes.get((reference, pad.GetNumber()))
            if net_name:
                pad.SetNet(board.FindNet(net_name))
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
