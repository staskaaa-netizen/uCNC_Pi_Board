"""Audit local 100 nF decoupling for placed ICs."""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
NETLIST = ROOT / "hardware" / "motherboard.net.xml"
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
GROUNDS = {"GND", "PGND", "AGND"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--netlist", type=Path, default=NETLIST)
    parser.add_argument("--max-mm", type=float, default=12.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    edges = board.GetBoardEdgesBoundingBox()
    x_min, y_min = pcbnew.ToMM(edges.GetLeft()), pcbnew.ToMM(edges.GetTop())
    x_max, y_max = pcbnew.ToMM(edges.GetRight()), pcbnew.ToMM(edges.GetBottom())

    root = ET.parse(args.netlist).getroot()
    component_nets = defaultdict(set)
    for net in root.findall("./nets/net"):
        for node in net.findall("node"):
            component_nets[node.get("ref", "")].add(net.get("name", ""))
    values = {
        component.get("ref", ""): (component.findtext("value") or "").strip()
        for component in root.findall("./components/comp")
    }

    def position(reference: str):
        point = footprints[reference].GetPosition()
        return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)

    def inside(reference: str) -> bool:
        x, y = position(reference)
        return x_min <= x <= x_max and y_min <= y <= y_max

    def pad_distance(ref_a: str, net_a: str, ref_b: str, net_b: str) -> float:
        points_a = []
        points_b = []
        for pad in footprints[ref_a].Pads():
            if pad.GetNetname() == net_a:
                point = pad.GetPosition()
                points_a.append((pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)))
        for pad in footprints[ref_b].Pads():
            if pad.GetNetname() == net_b:
                point = pad.GetPosition()
                points_b.append((pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)))
        return min(math.dist(a, b) for a in points_a for b in points_b)

    capacitors = [
        reference
        for reference, value in values.items()
        if reference.startswith("C")
        and "100nF" in value.replace(" ", "")
        and reference in footprints
    ]
    report = []
    for reference, nets in sorted(component_nets.items()):
        if not reference.startswith("U") or reference not in footprints:
            continue
        supplies = {
            net
            for net in nets
            if net not in GROUNDS
            and (
                net.startswith("+")
                or net.startswith("VIN")
                or net.startswith("BUCK")
                or net == "DO_COM"
            )
        }
        if not supplies:
            continue
        ix, iy = position(reference)
        candidates = []
        for capacitor in capacitors:
            cap_nets = component_nets[capacitor]
            shared_supply = supplies & cap_nets
            if shared_supply and cap_nets & GROUNDS:
                cx, cy = position(capacitor)
                supply_net = min(
                    shared_supply,
                    key=lambda net: pad_distance(reference, net, capacitor, net),
                )
                ground_net = next(iter(cap_nets & GROUNDS))
                loop_distance = (
                    pad_distance(reference, supply_net, capacitor, supply_net)
                    + pad_distance(reference, ground_net, capacitor, ground_net)
                )
                candidates.append(
                    {
                        "ref": capacitor,
                        "distance_mm": round(math.hypot(cx - ix, cy - iy), 3),
                        "loop_mm": round(loop_distance, 3),
                        "nets": sorted(cap_nets),
                    }
                )
        candidates.sort(key=lambda item: item["loop_mm"])
        nearest = candidates[0] if candidates else None
        status = "ok"
        if not inside(reference):
            status = "parked"
        elif nearest is None:
            status = "missing"
        elif nearest["loop_mm"] > args.max_mm:
            status = "far"
        report.append(
            {
                "ref": reference,
                "value": values.get(reference, ""),
                "inside_board": inside(reference),
                "supplies": sorted(supplies),
                "nearest_100nF": nearest,
                "status": status,
            }
        )

    payload = {"max_distance_mm": args.max_mm, "ics": report}
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for item in report:
        nearest = item["nearest_100nF"]
        distance = f"{nearest['distance_mm']:.2f} mm {nearest['ref']}" if nearest else "none"
        print(
            f"{item['ref']:5s} {item['status']:7s} "
            f"{','.join(item['supplies']):20s} nearest={distance}"
        )


if __name__ == "__main__":
    main()
