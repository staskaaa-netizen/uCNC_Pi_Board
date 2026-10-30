"""Replace the retired input MOSFET with parked backlight-buck footprints.

The new parts are deliberately placed outside the board outline. Existing
placement and routed copper are otherwise preserved.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"

NEW_REFERENCES = {
    "D2", "D3", "U3", "L2", "C107", "C108", "C109", "C110", "C111",
    "C112", "C113", "C114", "R126", "R127", "R131", "J2", "Q8", "R129", "R130",
}
REMOVE_REFERENCES = {"Q1", "R1", "C1", "C115", "R128", "J3"}
TIDY_TRACK_UUIDS = {
    # Branches that ended on the removed Q1/R1/D2 network.
    "5af0e949-dfdb-4c27-8e93-8e1d98672e4f",
    "ebf71b84-f25d-4798-9fbe-23544599e4ec",
    "d6ee5a98-3c33-41d7-8fd4-a631d6e8cb56",
}
PARKED_PLACEMENTS = {
    "D2": (207.0, 92.0, 90.0),
    "D3": (207.0, 99.0, 90.0),
    "C107": (207.0, 106.0, 0.0),
    "C108": (207.0, 111.0, 0.0),
    "U3": (215.0, 115.0, 0.0),
    "C113": (215.0, 104.0, 0.0),
    "C114": (215.0, 109.0, 0.0),
    "L2": (224.0, 115.0, 0.0),
    "C109": (235.0, 106.0, 0.0),
    "C110": (235.0, 111.0, 0.0),
    "C111": (235.0, 116.0, 0.0),
    "C112": (235.0, 121.0, 0.0),
    "R126": (244.0, 106.0, 0.0),
    "R127": (244.0, 111.0, 0.0),
    "R131": (249.0, 121.0, 90.0),
    "J2": (255.0, 92.0, 0.0),
    "Q8": (255.0, 124.0, 0.0),
    "R129": (246.0, 132.0, 90.0),
    "R130": (252.0, 132.0, 90.0),
}


def point_inside(box: pcbnew.BOX2I, point: pcbnew.VECTOR2I) -> bool:
    return box.Contains(point)


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
    node_nets = {
        (node.get("ref", ""), node.get("pin", "")): net.get("name", "")
        for net in root.findall("./nets/net")
        for node in net.findall("node")
        if not net.get("name", "").startswith("unconnected-")
    }

    board = pcbnew.LoadBoard(str(args.board))
    old = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    missing = sorted(NEW_REFERENCES - set(components))
    if missing:
        raise SystemExit(f"Netlist is missing new components: {missing}")

    remove_references = set(REMOVE_REFERENCES)
    preserved = {}
    for reference in NEW_REFERENCES:
        footprint = old.get(reference)
        if footprint is None:
            continue
        expected_id = (components[reference].findtext("footprint") or "").strip()
        expected_name = expected_id.rsplit(":", 1)[-1]
        actual_name = str(footprint.GetFPID().GetLibItemName())
        if actual_name == expected_name:
            preserved[reference] = footprint
        else:
            remove_references.add(reference)

    removed_pads = []
    for reference in remove_references:
        footprint = old.get(reference)
        if footprint is not None:
            removed_pads.extend(pad.GetBoundingBox() for pad in footprint.Pads())

    removed_tracks = []
    removed_footprints = []
    for item in list(board.GetTracks()):
        remove = (
            item.GetNetname() == "Q1_GATE"
            or item.m_Uuid.AsString() in TIDY_TRACK_UUIDS
        )
        if not remove and isinstance(item, pcbnew.PCB_VIA):
            remove = any(point_inside(box, item.GetPosition()) for box in removed_pads)
        elif not remove:
            remove = any(
                point_inside(box, point)
                for box in removed_pads
                for point in (item.GetStart(), item.GetEnd())
            )
        if remove:
            removed_tracks.append(item.m_Uuid.AsString())
            board.Remove(item)

    for reference in sorted(remove_references):
        footprint = old.get(reference)
        if footprint is not None:
            removed_footprints.append(reference)
            board.Remove(footprint)

    added = []
    updated = []
    for reference in sorted(NEW_REFERENCES):
        component = components[reference]
        footprint_name = (component.findtext("footprint") or "").strip()
        footprint = preserved.get(reference)
        if footprint is None:
            footprint = load_footprint(footprint_name)
            footprint.SetReference(reference)
            x, y, rotation = PARKED_PLACEMENTS[reference]
            footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            footprint.SetOrientationDegrees(rotation)
            footprint.SetLayer(pcbnew.F_Cu)
            footprint.SetLocked(False)
            footprint.SetDNP(False)
            board.Add(footprint)
            added.append(reference)
        else:
            updated.append(reference)
        footprint.SetValue((component.findtext("value") or "").strip())
        for pad in footprint.Pads():
            net_name = node_nets.get((reference, pad.GetNumber()))
            if not net_name:
                pad.SetNet(None)
                continue
            net = board.FindNet(net_name)
            if net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)

    board.BuildConnectivity()
    print(
        f"removed_footprints={sorted(removed_footprints)} "
        f"removed_tracks={len(removed_tracks)} added={len(added)} "
        f"updated_existing={len(updated)}"
    )
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
