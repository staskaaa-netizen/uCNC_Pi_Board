"""Synchronize capacitor footprints from the netlist without moving parts."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_NETLIST = ROOT / "hardware" / "motherboard.net.xml"


def point_mm(point: pcbnew.VECTOR2I) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def same_point(
    lhs: pcbnew.VECTOR2I,
    rhs: pcbnew.VECTOR2I,
    tolerance_mm: float = 0.01,
) -> bool:
    lx, ly = point_mm(lhs)
    rx, ry = point_mm(rhs)
    return abs(lx - rx) <= tolerance_mm and abs(ly - ry) <= tolerance_mm


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
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    replacements = []
    for reference, component in sorted(components.items()):
        if not reference.startswith("C") or reference not in footprints:
            continue
        expected_id = (component.findtext("footprint") or "").strip()
        if not expected_id:
            continue
        footprint = footprints[reference]
        expected_name = expected_id.rsplit(":", 1)[-1]
        actual_name = str(footprint.GetFPID().GetLibItemName())
        if actual_name != expected_name:
            replacements.append((reference, expected_id, footprint))

    print(f"capacitor_replacements={[(ref, fp_id) for ref, fp_id, _ in replacements]}")
    if not replacements:
        return

    endpoint_changes = []
    for reference, footprint_id, old in replacements:
        position = old.GetPosition()
        rotation = old.GetOrientationDegrees()
        layer = old.GetLayer()
        old_pads = {pad.GetNumber(): pad.GetPosition() for pad in old.Pads()}
        new = load_footprint(footprint_id)
        new.SetReference(reference)
        new.SetValue((components[reference].findtext("value") or "").strip())
        new.SetPosition(position)
        new.SetOrientationDegrees(rotation)
        new.SetLayer(layer)
        new.SetLocked(False)
        new.SetDNP(False)
        new_pads = {pad.GetNumber(): pad.GetPosition() for pad in new.Pads()}

        for track in board.GetTracks():
            if track.GetClass() != "PCB_TRACK":
                continue
            for pin in set(old_pads) & set(new_pads):
                old_pad = old_pads[pin]
                new_pad = new_pads[pin]
                if same_point(track.GetStart(), old_pad):
                    endpoint_changes.append(
                        (reference, pin, track.m_Uuid.AsString(), "start",
                         point_mm(old_pad), point_mm(new_pad))
                    )
                    if args.apply:
                        track.SetStart(new_pad)
                elif same_point(track.GetEnd(), old_pad):
                    endpoint_changes.append(
                        (reference, pin, track.m_Uuid.AsString(), "end",
                         point_mm(old_pad), point_mm(new_pad))
                    )
                    if args.apply:
                        track.SetEnd(new_pad)

        for pad in new.Pads():
            net_name = node_nets.get((reference, pad.GetNumber()), "")
            net = board.FindNet(net_name) if net_name else None
            if net_name and net is None:
                net = pcbnew.NETINFO_ITEM(board, net_name)
                board.Add(net)
            pad.SetNet(net)

        if args.apply:
            board.Remove(old)
            board.Add(new)

    print(f"track_endpoint_changes={endpoint_changes}")
    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
