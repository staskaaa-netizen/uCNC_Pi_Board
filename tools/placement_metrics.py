"""Measure weighted airwire length, crossings and congestion for a placed PCB."""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
NETLIST = HARDWARE / "motherboard.net.xml"
PCB = HARDWARE / "motherboard.kicad_pcb"


def net_weight(name: str) -> float:
    if name in {"GND", "PGND", "AGND"}:
        return 0.0
    if name.startswith("HDMI_") or name.startswith("HSTX_") or name.startswith("LVDS_"):
        return 2.5
    if name.startswith(("ESTOP", "HOLD", "START")):
        return 3.0
    if name.startswith(("SR_", "ENC")):
        return 1.5
    if name.startswith(("VIN", "BUCK", "MODULE_5V")) or name.startswith("+"):
        return 0.35
    return 1.0


def sheet_map() -> dict[str, str]:
    root = ET.parse(NETLIST).getroot()
    result = {}
    for component in root.findall("./components/comp"):
        sheet = next(
            (
                prop.get("value", "")
                for prop in component.findall("property")
                if prop.get("name") == "Sheetname"
            ),
            "",
        )
        result[component.get("ref", "")] = sheet
    return result


def mst_edges(points: list[tuple[float, float]]) -> list[tuple[tuple[float, float], tuple[float, float], float]]:
    if len(points) < 2:
        return []
    remaining = set(range(1, len(points)))
    visited = {0}
    edges = []
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                dx = points[i][0] - points[j][0]
                dy = points[i][1] - points[j][1]
                length = math.hypot(dx, dy)
                if best is None or length < best[2]:
                    best = (i, j, length)
        i, j, length = best
        edges.append((points[i], points[j], length))
        visited.add(j)
        remaining.remove(j)
    return edges


def segments_cross(a, b, c, d) -> bool:
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    shared = {a, b} & {c, d}
    if shared:
        return False
    o1 = orient(a, b, c)
    o2 = orient(a, b, d)
    o3 = orient(c, d, a)
    o4 = orient(c, d, b)
    return (o1 == 0 or o2 == 0 or o1 * o2 < 0) and (
        o3 == 0 or o4 == 0 or o3 * o4 < 0
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--board", type=Path, default=PCB)
    parser.add_argument(
        "--inside-only",
        action="store_true",
        help="Ignore intentionally parked footprints outside the board outline",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    sheets = sheet_map()
    net_pads = defaultdict(list)
    side_counts = {"F.Cu": 0, "B.Cu": 0, "THT": 0}
    board_box = board.GetBoardEdgesBoundingBox()
    x_min = pcbnew.ToMM(board_box.GetLeft())
    y_min = pcbnew.ToMM(board_box.GetTop())
    x_max = pcbnew.ToMM(board_box.GetRight())
    y_max = pcbnew.ToMM(board_box.GetBottom())
    used_footprints = 0
    for footprint in board.GetFootprints():
        position = footprint.GetPosition()
        if args.inside_only and not (
            x_min <= pcbnew.ToMM(position.x) <= x_max
            and y_min <= pcbnew.ToMM(position.y) <= y_max
        ):
            continue
        used_footprints += 1
        pth = any(
            pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
            for pad in footprint.Pads()
        )
        side = "THT" if pth else footprint.GetLayerName()
        side_counts[side] = side_counts.get(side, 0) + 1
        for pad in footprint.Pads():
            name = pad.GetNetname()
            if name:
                pos = pad.GetPosition()
                net_pads[name].append(
                    (
                        footprint.GetReference(),
                        pcbnew.ToMM(pos.x),
                        pcbnew.ToMM(pos.y),
                        side,
                    )
                )

    net_metrics = {}
    all_segments = []
    weighted_total = 0.0
    unweighted_total = 0.0
    mixed_side_nets = []
    weighted_mixed_side_nets = 0.0
    sheet_totals = defaultdict(float)
    for name, pads in sorted(net_pads.items()):
        points = [(x, y) for _, x, y, _ in pads]
        edges = mst_edges(points)
        length = sum(edge[2] for edge in edges)
        weight = net_weight(name)
        weighted = length * weight
        weighted_total += weighted
        unweighted_total += length
        component_sheets = {sheets.get(ref, "") for ref, _, _, _ in pads if sheets.get(ref)}
        block = (
            next(iter(component_sheets))
            if len(component_sheets) == 1 and weight > 0
            else "global"
        )
        sheet_totals[block] += weighted
        if weight > 0:
            all_segments.extend((name, a, b, weight) for a, b, _ in edges)
        sides = {side for _, _, _, side in pads}
        mixed = "F.Cu" in sides and "B.Cu" in sides and "THT" not in sides
        if mixed:
            mixed_side_nets.append(name)
            weighted_mixed_side_nets += weight
        net_metrics[name] = {
            "pads": len(pads),
            "length_mm": round(length, 3),
            "weight": weight,
            "weighted_length_mm": round(weighted, 3),
            "block": block,
            "mixed_side": mixed,
        }

    crossings = 0
    weighted_crossings = 0.0
    for index, (name_a, a1, a2, weight_a) in enumerate(all_segments):
        for name_b, b1, b2, weight_b in all_segments[index + 1:]:
            if name_a == name_b:
                continue
            if segments_cross(a1, a2, b1, b2):
                crossings += 1
                weighted_crossings += max(weight_a, weight_b)

    cell_size = 5.0
    cols = max(1, math.ceil(pcbnew.ToMM(board_box.GetWidth()) / cell_size))
    rows = max(1, math.ceil(pcbnew.ToMM(board_box.GetHeight()) / cell_size))
    congestion = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for _, a, b, _ in all_segments:
        steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 1.0))
        for step in range(steps + 1):
            t = step / steps
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            col = min(cols - 1, max(0, int(x / cell_size)))
            row = min(rows - 1, max(0, int(y / cell_size)))
            congestion[row][col] += 1.0 / (cols * rows)
    cells = sorted(value for row in congestion for value in row)
    p95 = cells[min(len(cells) - 1, int(len(cells) * 0.95))]
    peak = cells[-1]

    report = {
        "board_mm": [
            round(pcbnew.ToMM(board_box.GetWidth()), 3),
            round(pcbnew.ToMM(board_box.GetHeight()), 3),
        ],
        "footprints": used_footprints,
        "front_footprints": side_counts.get("F.Cu", 0),
        "back_footprints": side_counts.get("B.Cu", 0),
        "through_hole_footprints": side_counts.get("THT", 0),
        "nets": len(net_pads),
        "total_airwire_mm": round(unweighted_total, 3),
        "weighted_airwire_mm": round(weighted_total, 3),
        "crossings": crossings,
        "weighted_crossings": round(weighted_crossings, 3),
        "mixed_side_nets": len(mixed_side_nets),
        "weighted_mixed_side_nets": round(weighted_mixed_side_nets, 3),
        "congestion_p95": round(p95, 6),
        "congestion_peak": round(peak, 6),
        "per_block_weighted_mm": {
            key: round(value, 3) for key, value in sorted(sheet_totals.items())
        },
        "nets_detail": net_metrics,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "nets_detail"}, indent=2))


if __name__ == "__main__":
    main()
