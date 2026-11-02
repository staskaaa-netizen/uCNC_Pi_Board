"""Apply E-stop, microSD, resistor-network and passive-LVDS simplifications."""

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
    "J6", "J26",
    "R17", "R75", "R108", "R109",
    "D11", "D12", "D54", "D55",
    "J19",
    "R44", "R45", "R46", "R47", "R48", "R49",
    "U41", "C106",
)
ADDED_REFERENCES = {
    "RN42": (144.780, 20.000, 90.0),
    "RN43": (144.780, 36.500, 90.0),
}
REPLACED_REFERENCES = ("U35",)
FITTED_REFERENCES = ("J36", "RN26", "RN27")


def set_pad_nets(board, footprint, expected_nets) -> None:
    for pad in footprint.Pads():
        net_name = expected_nets.get(pad.GetNumber(), "")
        net = board.FindNet(net_name) if net_name else None
        if net_name and net is None:
            net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(net)
        pad.SetNet(net)


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
    expected_nets = {}
    for net in root.findall("./nets/net"):
        net_name = net.get("name", "")
        for node in net.findall("node"):
            expected_nets[(node.get("ref", ""), node.get("pin", ""))] = net_name

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    present_removed = [
        reference for reference in REMOVED_REFERENCES if reference in footprints
    ]
    print(f"remove={present_removed}")
    print(f"add={list(ADDED_REFERENCES)}")
    print(f"replace={list(REPLACED_REFERENCES)}")
    print(f"fit={list(FITTED_REFERENCES)}")
    print(f"initial_tracks={len(list(board.GetTracks()))} apply={args.apply}")
    if not args.apply:
        return

    for reference in present_removed:
        board.Remove(footprints[reference])

    for reference, (x, y, rotation) in ADDED_REFERENCES.items():
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from the netlist")
        footprint = load_footprint((component.findtext("footprint") or "").strip())
        footprint.SetReference(reference)
        footprint.SetValue((component.findtext("value") or "").strip())
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        set_pad_nets(
            board,
            footprint,
            {
                pin: net_name
                for (ref, pin), net_name in expected_nets.items()
                if ref == reference
            },
        )
        board.Add(footprint)
        footprints[reference] = footprint

    for reference in REPLACED_REFERENCES:
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from the netlist")
        old = footprints.get(reference)
        target = (component.findtext("footprint") or "").strip()
        replacement = load_footprint(target)
        replacement.SetReference(reference)
        replacement.SetValue((component.findtext("value") or "").strip())
        if old is not None:
            replacement.SetPosition(old.GetPosition())
            replacement.SetOrientation(old.GetOrientation())
            replacement.SetLayer(old.GetLayer())
            replacement.SetLocked(old.IsLocked())
        else:
            replacement.SetPosition(pcbnew.VECTOR2I_MM(229.810, 100.258))
            replacement.SetOrientationDegrees(180.0)
        set_pad_nets(
            board,
            replacement,
            {
                pin: net_name
                for (ref, pin), net_name in expected_nets.items()
                if ref == reference
            },
        )
        if old is not None:
            board.Remove(old)
        board.Add(replacement)
        footprints[reference] = replacement

    for reference in FITTED_REFERENCES:
        footprints[reference].SetDNP(False)
        footprints[reference].SetValue(
            (components[reference].findtext("value") or "").strip()
        )

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")
    print(f"final_tracks={len(list(board.GetTracks()))}")


if __name__ == "__main__":
    main()
