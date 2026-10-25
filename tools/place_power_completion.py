"""Place the remaining main-power passives and front-panel power indicators."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from generate_pcb import (
    bbox_inside,
    candidate_boxes,
    net_weight,
    overlap,
    put_on_side,
)


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

POSITIONS = {
    # U1 +5 V output bank, immediately left of C6/C11.
    "C7": (181.000, 101.200, 90.0),
    "C8": (181.000, 104.500, 0.0),
    "C17": (181.000, 107.500, 0.0),
    "C16": (176.000, 105.500, 90.0),
    "C77": (176.000, 100.500, 90.0),
    # Dedicated ESP-01S regulator rail.
    "C88": (202.800, 37.000, 0.0),
    "C89": (197.800, 37.000, 0.0),
    "C70": (190.200, 41.200, 90.0),
    "C69": (195.000, 49.000, 0.0),
    # ADC/reference prefilter beside MOD1 pin 48.
    "FB1": (161.500, 49.370, 0.0),
    "C15": (168.000, 49.370, 0.0),
    "C14": (168.000, 54.200, 0.0),
    # Power-good pull-up, roughly between U1 PG and MOD1 GPIO43.
    "R73": (183.000, 87.500, 0.0),
    # Visible power indicators between the RP2350 and the two regulators.
    "R4": (162.000, 85.000, 0.0),
    "D4": (168.000, 85.000, 180.0),
    "R5": (162.000, 92.000, 0.0),
    "D5": (168.000, 92.000, 180.0),
}


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def spans_sides(footprint) -> bool:
    return any(
        pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
        for pad in footprint.Pads()
    )


def add_occupancy(footprint, box, occupied) -> None:
    layers = (
        (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
        if spans_sides(footprint)
        else (int(footprint.GetLayer()),)
    )
    for layer in layers:
        occupied.setdefault(layer, []).append(box)


def mst_edges(points):
    unique = list(dict.fromkeys(points))
    if len(unique) < 2:
        return []
    remaining = set(range(1, len(unique)))
    visited = {0}
    edges = []
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                length = math.dist(unique[i], unique[j])
                if best is None or length < best[0]:
                    best = (length, i, j)
        length, i, j = best
        edges.append((unique[i], unique[j], length))
        visited.add(j)
        remaining.remove(j)
    return edges


def orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_cross(a, b, c, d) -> bool:
    if {a, b} & {c, d}:
        return False
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    return (o1 == 0 or o2 == 0 or o1 * o2 < 0) and (
        o3 == 0 or o4 == 0 or o3 * o4 < 0
    )


def net_metrics(net_points, nets):
    raw = 0.0
    weighted = 0.0
    segments = []
    for net in nets:
        if net_weight(net) == 0:
            continue
        edges = mst_edges(net_points.get(net, []))
        length = sum(edge[2] for edge in edges)
        raw += length
        weighted += length * net_weight(net)
        segments.extend((net, start, end) for start, end, _ in edges)
    crossings = 0
    for index, (net_a, a1, a2) in enumerate(segments):
        for net_b, b1, b2 in segments[index + 1:]:
            if net_a != net_b and segments_cross(a1, a2, b1, b2):
                crossings += 1
    return raw, weighted, crossings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    missing = sorted(set(POSITIONS) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")

    edges = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edges.GetLeft()),
        pcbnew.ToMM(edges.GetTop()),
        pcbnew.ToMM(edges.GetRight()),
        pcbnew.ToMM(edges.GetBottom()),
    )
    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        position = point_mm(footprint.GetPosition())
        if reference in POSITIONS:
            continue
        if not (
            bounds[0] <= position[0] <= bounds[2]
            and bounds[1] <= position[1] <= bounds[3]
        ):
            continue
        box = candidate_boxes(footprint, position[0], position[1], clearance=0.0)
        add_occupancy(footprint, box, occupied)

    moving_nets = set()
    for reference in POSITIONS:
        for pad in footprints[reference].Pads():
            if pad.GetNetname():
                moving_nets.add(pad.GetNetname())

    net_points = {net: [] for net in moving_nets}
    for reference, footprint in footprints.items():
        if reference in POSITIONS:
            continue
        position = point_mm(footprint.GetPosition())
        if not (
            bounds[0] <= position[0] <= bounds[2]
            and bounds[1] <= position[1] <= bounds[3]
        ):
            continue
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net in net_points:
                net_points[net].append(point_mm(pad.GetPosition()))

    placements = {}
    for reference, (x, y, rotation) in POSITIONS.items():
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetOrientationDegrees(rotation)
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        if not bbox_inside(box, 0.55):
            raise RuntimeError(f"{reference} template position is outside the board")
        blockers = occupied[int(pcbnew.F_Cu)]
        if any(overlap(box, other) for other in blockers):
            conflicts = []
            for other_reference, other in footprints.items():
                if other_reference in POSITIONS:
                    continue
                other_position = point_mm(other.GetPosition())
                if not (
                    bounds[0] <= other_position[0] <= bounds[2]
                    and bounds[1] <= other_position[1] <= bounds[3]
                ):
                    continue
                other_box = candidate_boxes(
                    other, other_position[0], other_position[1], clearance=0.0
                )
                if overlap(box, other_box):
                    conflicts.append(other_reference)
            raise RuntimeError(
                f"{reference} template position overlaps: {', '.join(conflicts)}"
            )
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        add_occupancy(footprint, box, occupied)
        placements[reference] = {
            "x": x,
            "y": y,
            "rotation": rotation,
        }
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net in net_points:
                net_points[net].append(point_mm(pad.GetPosition()))

    raw, weighted, crossings = net_metrics(net_points, moving_nets)
    report = {
        "board": str(args.board),
        "moving": sorted(POSITIONS),
        "group_airwire_mm": round(raw, 3),
        "group_weighted_airwire_mm": round(weighted, 3),
        "group_crossings": crossings,
        "placements": placements,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
