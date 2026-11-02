"""Restore standard single-row connectors and add direct servo feedback."""

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
    "J34", "J35", "J37", "J38", "J39",
    "J31", "J44", "J51",
    "JP2", "JP3", "JP4",
    "U45", "U46",
    "RN23", "RN25",
    *(f"R{index}" for index in range(174, 182)),
    *(f"D{index}" for index in range(73, 81)),
    *(f"D{index}" for index in range(89, 97)),
    "U40", "F4", "D56", "C103", "C105",
    "Q8", "R129", "R130",
    "U36", "U39", "RN6", "RN7",
    *(f"R{index}" for index in range(166, 174)),
    *(f"D{index}" for index in range(65, 73)),
    *(f"D{index}" for index in range(81, 89)),
    "R50", "R51", "R52", "R53",
    "C57",
    "R131",
)
REPLACED_REFERENCES = (
    "J7", "J8",
    "J10", "J11", "J28", "J29", "J30",
    "J12", "J32",
    "J13", "J14", "J15",
    "J40", "J36", "J2", "J18", "J46", "J47",
)
ADDED_REFERENCES = {
    "U9": (87.802, 80.618, 270.0),
    "C25": (93.527, 80.838, 90.0),
    "J45": (30.000, 6.750, 180.0),
    "J41": (370.000, 140.000, 0.0),
    "J42": (395.000, 140.000, 0.0),
    "J43": (420.000, 140.000, 0.0),
    "J48": (445.000, 140.000, 0.0),
    "J49": (470.000, 140.000, 0.0),
    "J50": (495.000, 140.000, 0.0),
    "U3": (182.000, 165.000, 0.0),
    "L2": (194.000, 165.000, 0.0),
    "D3": (170.000, 165.000, 0.0),
    "C107": (206.000, 165.000, 0.0),
    "C108": (218.000, 165.000, 0.0),
    "C109": (230.000, 165.000, 0.0),
    "C110": (242.000, 165.000, 0.0),
    "C111": (254.000, 165.000, 0.0),
    "C112": (266.000, 165.000, 0.0),
    "C113": (278.000, 165.000, 0.0),
    "C114": (290.000, 165.000, 0.0),
    "R126": (302.000, 165.000, 0.0),
    "R127": (314.000, 165.000, 0.0),
    "R128": (326.000, 165.000, 0.0),
    "RN44": (142.240, 27.200, 0.0),
    "R182": (220.000, 12.000, 270.0),
    "R183": (228.000, 12.000, 90.0),
    "C118": (236.000, 12.000, 90.0),
    "C115": (112.946, -38.136, 0.0),
    "C116": (112.946, -23.136, 0.0),
    **{
        f"R{index}": (45.0 + (index - 166) % 4 * 8.0, 100.0, 0.0)
        for index in range(166, 174)
    },
    **{
        f"D{index}": (45.0 + (index - 65) % 4 * 8.0, 106.0, 0.0)
        for index in range(65, 73)
    },
    **{
        f"D{index}": (45.0 + (index - 81) % 4 * 8.0, 112.0, 0.0)
        for index in range(81, 89)
    },
}
RELINKED_REFERENCES = ("U6", "U7", "J33")


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
    parser.add_argument("--remove-only", action="store_true")
    parser.add_argument("--replace-one")
    parser.add_argument("--add-one")
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
    print(f"replace={list(REPLACED_REFERENCES)}")
    print(f"initial_tracks={len(list(board.GetTracks()))} apply={args.apply}")
    if not args.apply:
        return

    if args.replace_one:
        reference = args.replace_one
        if reference not in REPLACED_REFERENCES:
            raise SystemExit(f"{reference} is not a dual-row replacement")
        component = components.get(reference)
        old = footprints.get(reference)
        if component is None or old is None:
            raise SystemExit(f"Missing {reference} from board or netlist")
        replacement = load_footprint(
            (component.findtext("footprint") or "").strip()
        )
        replacement.SetReference(reference)
        replacement.SetValue((component.findtext("value") or "").strip())
        replacement.SetPosition(old.GetPosition())
        replacement.SetOrientation(old.GetOrientation())
        replacement.SetLayer(old.GetLayer())
        replacement.SetLocked(old.IsLocked())
        set_pad_nets(
            board,
            replacement,
            {
                pin: net_name
                for (ref, pin), net_name in expected_nets.items()
                if ref == reference
            },
        )
        board.Remove(old)
        board.Add(replacement)
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"replaced {reference}; saved {args.board}")
        return

    if args.add_one:
        reference = args.add_one
        if reference not in ADDED_REFERENCES:
            raise SystemExit(f"{reference} is not a scheduled addition")
        if reference in footprints:
            print(f"{reference} already exists")
            return
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from the netlist")
        x, y, rotation = ADDED_REFERENCES[reference]
        footprint = load_footprint(
            (component.findtext("footprint") or "").strip()
        )
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
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"added {reference}; saved {args.board}")
        return

    for reference in present_removed:
        board.Remove(footprints[reference])

    if args.remove_only:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")
        print(f"final_tracks={len(list(board.GetTracks()))}")
        return

    # Load all replacement footprints before mutating the board. KiCad 10's
    # Python plugin loader can invalidate its plugin object after footprint
    # removal in the same process.
    replacements = {}
    for reference in REPLACED_REFERENCES:
        component = components.get(reference)
        if component is None:
            raise SystemExit(f"Missing {reference} from the netlist")
        old = footprints.get(reference)
        if old is None:
            raise SystemExit(f"Missing footprint {reference}")
        target = (component.findtext("footprint") or "").strip()
        replacement = load_footprint(target)
        replacement.SetReference(reference)
        replacement.SetValue((component.findtext("value") or "").strip())
        replacement.SetPosition(old.GetPosition())
        replacement.SetOrientation(old.GetOrientation())
        replacement.SetLayer(old.GetLayer())
        replacement.SetLocked(old.IsLocked())
        replacements[reference] = replacement

    for reference, replacement in replacements.items():
        old = footprints.get(reference)
        set_pad_nets(
            board,
            replacement,
            {
                pin: net_name
                for (ref, pin), net_name in expected_nets.items()
                if ref == reference
            },
        )
        board.Remove(old)
        board.Add(replacement)
        footprints[reference] = replacement

    for reference in RELINKED_REFERENCES:
        footprint = footprints[reference]
        set_pad_nets(
            board,
            footprint,
            {
                pin: net_name
                for (ref, pin), net_name in expected_nets.items()
                if ref == reference
            },
        )
        footprint.SetValue(
            (components[reference].findtext("value") or "").strip()
        )

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"saved {args.board}")
    print(f"final_tracks={len(list(board.GetTracks()))}")


if __name__ == "__main__":
    main()
