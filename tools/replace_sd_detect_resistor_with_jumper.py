"""Replace the SD-card-detect 0R resistor with an open solder jumper."""

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
    if "JP5" not in components:
        raise SystemExit("Netlist does not contain JP5")
    node_nets = {
        (node.get("ref", ""), node.get("pin", "")): net.get("name", "")
        for net in root.findall("./nets/net")
        for node in net.findall("node")
        if not net.get("name", "").startswith("unconnected-")
    }

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    r54 = footprints.get("R54")
    if r54 is None:
        raise SystemExit("R54 is missing")
    old_pads = {pad.GetNumber(): pad.GetPosition() for pad in r54.Pads()}
    center = r54.GetPosition()
    rotation = r54.GetOrientationDegrees()
    layer = r54.GetLayer()
    if layer != pcbnew.F_Cu:
        raise SystemExit("R54 is not on F.Cu")

    component = components["JP5"]
    footprint_name = (component.findtext("footprint") or "").strip()
    jumper = load_footprint(footprint_name)
    jumper.SetReference("JP5")
    jumper.SetValue((component.findtext("value") or "").strip())
    jumper.SetPosition(center)
    jumper.SetOrientationDegrees(rotation)
    jumper.SetLayer(pcbnew.F_Cu)
    jumper.SetLocked(False)
    jumper.SetDNP(False)
    for pad in jumper.Pads():
        net_name = node_nets.get(("JP5", pad.GetNumber()), "")
        net = board.FindNet(net_name) if net_name else None
        if net_name and net is None:
            net = pcbnew.NETINFO_ITEM(board, net_name)
            board.Add(net)
        pad.SetNet(net)

    new_pads = {pad.GetNumber(): pad.GetPosition() for pad in jumper.Pads()}
    endpoint_changes = []
    for track in board.GetTracks():
        if track.GetClass() != "PCB_TRACK":
            continue
        for side in ("1", "2"):
            old = old_pads[side]
            new = new_pads[side]
            if same_point(track.GetStart(), old):
                endpoint_changes.append(
                    (track.m_Uuid.AsString(), "start", point_mm(old), point_mm(new))
                )
                if args.apply:
                    track.SetStart(new)
            elif same_point(track.GetEnd(), old):
                endpoint_changes.append(
                    (track.m_Uuid.AsString(), "end", point_mm(old), point_mm(new))
                )
                if args.apply:
                    track.SetEnd(new)

    print(f"replace R54 at {point_mm(center)} with JP5")
    print(f"JP5 pads={ {key: point_mm(value) for key, value in new_pads.items()} }")
    print(f"endpoint_changes={endpoint_changes}")
    if args.apply:
        board.Remove(r54)
        board.Add(jumper)
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"saved {args.board}")


if __name__ == "__main__":
    main()
