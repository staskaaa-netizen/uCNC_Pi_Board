"""Place the full-size SD-card passives around the fixed J19 connector."""

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
CONNECTOR = "J19"
REGION = (158.0, 50.0, 180.7, 85.0)
GRID_MM = 0.635
ORIENTATIONS = (0.0, 90.0, 180.0, 270.0)

SERIES = ("R53", "R51", "R50", "R52", "R54")
PULLUPS = ("R44", "R45", "R49", "R46", "R48", "R47")
SUPPORT = ("FB2", "C67", "C68")
MOVING = (*SERIES, *PULLUPS, *SUPPORT)

INITIAL_POSITIONS = {
    "R53": (178.70, 60.12, 0.0),
    "R51": (178.70, 62.62, 0.0),
    "R50": (178.70, 70.12, 0.0),
    "R52": (178.70, 75.06, 0.0),
    "R54": (178.70, 78.06, 0.0),
    "R49": (172.60, 57.62, 0.0),
    "R44": (172.60, 60.12, 0.0),
    "R45": (172.60, 62.62, 0.0),
    "R46": (172.60, 73.00, 0.0),
    "R48": (172.60, 76.75, 0.0),
    "R47": (172.60, 79.50, 0.0),
    "FB2": (166.80, 67.62, 0.0),
    "C68": (166.80, 70.80, 90.0),
    "C67": (166.80, 75.70, 90.0),
}

CONNECTOR_NETS = {
    "SD_CS_N",
    "SD_MOSI",
    "SD_SCK",
    "SD_MISO",
    "SD_DAT1",
    "SD_DAT2",
    "SD_CD",
    "+3V3_SD",
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


def box_at(footprint, x: float, y: float, rotation: float, clearance: float = 0.05):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(rotation)
    return candidate_boxes(footprint, x, y, clearance=clearance)


def legal_box(footprint, box, occupied, clearance: float = 0.55) -> bool:
    if not bbox_inside(box, clearance):
        return False
    blockers = occupied.get(int(pcbnew.F_Cu), [])
    if spans_sides(footprint):
        blockers = blockers + occupied.get(int(pcbnew.B_Cu), [])
    return not any(overlap(box, other) for other in blockers)


def mst_edges(points: list[tuple[float, float]]):
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


def mst_length(points: list[tuple[float, float]]) -> float:
    return sum(edge[2] for edge in mst_edges(points))


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


def crossing_count(net_points) -> int:
    segments = []
    for net, points in net_points.items():
        if net_weight(net) == 0:
            continue
        segments.extend((net, a, b) for a, b, _ in mst_edges(points))
    crossings = 0
    for index, (net_a, a1, a2) in enumerate(segments):
        for net_b, b1, b2 in segments[index + 1:]:
            if net_a != net_b and segments_cross(a1, a2, b1, b2):
                crossings += 1
    return crossings


def footprint_points(footprint, net_points):
    result = dict(net_points)
    touched = set()
    for pad in footprint.Pads():
        net = pad.GetNetname()
        if not net:
            continue
        result.setdefault(net, []).append(point_mm(pad.GetPosition()))
        touched.add(net)
    return result, touched


def connector_anchor(footprint, connector, connector_points) -> float:
    distances = []
    for pad in footprint.Pads():
        net = pad.GetNetname()
        if net not in CONNECTOR_NETS or net not in connector_points:
            continue
        position = point_mm(pad.GetPosition())
        distances.append(
            min(math.dist(position, target) for target in connector_points[net])
        )
    return min(distances) if distances else 50.0


def score_candidate(
    footprint,
    net_points,
    touched,
    connector,
    connector_points,
) -> float:
    score = sum(
        net_weight(net) * mst_length(net_points.get(net, []))
        for net in touched
    )
    score += 0.75 * connector_anchor(footprint, connector, connector_points)
    position = point_mm(footprint.GetPosition())
    connector_position = point_mm(connector.GetPosition())
    score += 0.06 * math.dist(position, connector_position)
    return score


def best_placement(
    footprint,
    net_points,
    occupied,
    connector,
    connector_points,
    region=REGION,
    centers=None,
    radius: float = 0.0,
):
    best = None
    if centers is None:
        x_values = []
        x = region[0]
        while x <= region[2]:
            x_values.append(x)
            x += GRID_MM
        y_values = []
        y = region[1]
        while y <= region[3]:
            y_values.append(y)
            y += GRID_MM
        positions = ((x, y) for y in y_values for x in x_values)
    else:
        positions = (
            (center[0] + dx * GRID_MM, center[1] + dy * GRID_MM)
            for center in centers
            for dx in range(-int(radius / GRID_MM), int(radius / GRID_MM) + 1)
            for dy in range(-int(radius / GRID_MM), int(radius / GRID_MM) + 1)
        )

    for x, y in positions:
        if not (region[0] <= x <= region[2] and region[1] <= y <= region[3]):
            continue
        for rotation in ORIENTATIONS:
            box = box_at(footprint, x, y, rotation)
            if not legal_box(footprint, box, occupied):
                continue
            updated, touched = footprint_points(footprint, net_points)
            score = score_candidate(
                footprint,
                updated,
                touched,
                connector,
                connector_points,
            )
            if best is None or score < best[0]:
                best = (score, x, y, rotation, box, updated, touched)
    return best


def place_all(
    footprints,
    moving,
    connector,
    connector_points,
    occupied,
    net_points,
    order,
) -> tuple[dict, float]:
    placements = {}
    for reference in order:
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        best = best_placement(
            footprint,
            net_points,
            occupied,
            connector,
            connector_points,
        )
        if best is None:
            raise RuntimeError(f"No legal placement for {reference}")
        score, x, y, rotation, box, updated, touched = best
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        add_occupancy(footprint, box, occupied)
        net_points = updated
        placements[reference] = {
            "x": round(x, 3),
            "y": round(y, 3),
            "rotation": rotation,
        }
        print(f"{reference:4s} -> ({x:6.2f}, {y:6.2f}) rot={rotation:3.0f} score={score:8.3f}")
    return placements, group_score(net_points, moving)


def group_score(net_points, moving_nets) -> float:
    return sum(
        net_weight(net) * mst_length(net_points.get(net, []))
        for net in moving_nets
    )


def moving_nets(footprints, moving) -> set[str]:
    nets = set()
    for reference in moving:
        for pad in footprints[reference].Pads():
            if pad.GetNetname():
                nets.add(pad.GetNetname())
    return nets


def rebuild_net_points(
    footprints,
    occupancy_bounds,
    moving,
    all_net_names,
    include_moving: bool = False,
    exclude_reference: str | None = None,
):
    points = {net: [] for net in all_net_names}
    layer_boxes = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        if reference == exclude_reference:
            continue
        if reference in moving and not include_moving:
            continue
        position = point_mm(footprint.GetPosition())
        if not (
            occupancy_bounds[0] <= position[0] <= occupancy_bounds[2]
            and occupancy_bounds[1] <= position[1] <= occupancy_bounds[3]
        ):
            continue
        box = candidate_boxes(footprint, position[0], position[1], clearance=0.0)
        add_occupancy(footprint, box, layer_boxes)
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net in points:
                points[net].append(point_mm(pad.GetPosition()))
    return points, layer_boxes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--no-refine",
        action="store_true",
        help="Apply the connector-aligned template without local coordinate search",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    missing = sorted(set(MOVING) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")

    edges = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edges.GetLeft()),
        pcbnew.ToMM(edges.GetTop()),
        pcbnew.ToMM(edges.GetRight()),
        pcbnew.ToMM(edges.GetBottom()),
    )
    all_group_nets = moving_nets(footprints, MOVING)
    net_points, occupied = rebuild_net_points(
        footprints, bounds, MOVING, all_group_nets | CONNECTOR_NETS
    )
    connector = footprints[CONNECTOR]
    connector_points = {net: [] for net in CONNECTOR_NETS}
    for pad in connector.Pads():
        net = pad.GetNetname()
        if net in connector_points:
            connector_points[net].append(point_mm(pad.GetPosition()))

    order = (*SERIES, *PULLUPS, *SUPPORT)
    placements = {}
    for reference in order:
        footprint = footprints[reference]
        x, y, rotation = INITIAL_POSITIONS[reference]
        put_on_side(footprint, back=False)
        box = box_at(footprint, x, y, rotation)
        if not legal_box(footprint, box, occupied):
            raise RuntimeError(
                f"SD template position for {reference} is blocked: "
                f"({x:.2f}, {y:.2f})"
            )
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        add_occupancy(footprint, box, occupied)
        placements[reference] = {
            "x": round(x, 3),
            "y": round(y, 3),
            "rotation": rotation,
        }
        print(
            f"{reference:4s} seed -> ({x:6.2f}, {y:6.2f}) rot={rotation:3.0f}",
            flush=True,
        )

    net_points, _ = rebuild_net_points(
        footprints,
        bounds,
        MOVING,
        all_group_nets | CONNECTOR_NETS,
        include_moving=True,
    )
    initial_score = group_score(net_points, all_group_nets)

    # Coordinate-descent pass around the first legal layout.
    for pass_index in range(0 if args.no_refine else 2):
        improved = 0
        for reference in order:
            footprint = footprints[reference]
            center = point_mm(footprint.GetPosition())
            current_rotation = footprint.GetOrientationDegrees()
            net_points_without, _ = rebuild_net_points(
                footprints,
                bounds,
                MOVING,
                all_group_nets | CONNECTOR_NETS,
                include_moving=True,
                exclude_reference=reference,
            )
            # Rebuild occupancy from scratch so the current footprint can move.
            occupancy_without = {
                int(pcbnew.F_Cu): [],
                int(pcbnew.B_Cu): [],
            }
            for other_reference, other in footprints.items():
                if other_reference == reference or other_reference in MOVING:
                    continue
                position = point_mm(other.GetPosition())
                if not (
                    bounds[0] <= position[0] <= bounds[2]
                    and bounds[1] <= position[1] <= bounds[3]
                ):
                    continue
                box = candidate_boxes(
                    other, position[0], position[1], clearance=0.0
                )
                add_occupancy(other, box, occupancy_without)
            for other_reference in order:
                if other_reference == reference:
                    continue
                other = footprints[other_reference]
                position = point_mm(other.GetPosition())
                box = candidate_boxes(
                    other, position[0], position[1], clearance=0.0
                )
                add_occupancy(other, box, occupancy_without)

            current_points, _ = footprint_points(footprint, net_points_without)
            baseline = score_candidate(
                footprint,
                current_points,
                all_group_nets,
                connector,
                connector_points,
            )
            best = best_placement(
                footprint,
                net_points_without,
                occupancy_without,
                connector,
                connector_points,
                centers=[center],
                radius=2.54,
            )
            if best is not None and best[0] < baseline - 0.1:
                score, x, y, rotation, box, updated, _ = best
                footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                footprint.SetOrientationDegrees(rotation)
                placements[reference] = {
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "rotation": rotation,
                }
                improved += 1
            else:
                footprint.SetPosition(pcbnew.VECTOR2I_MM(center[0], center[1]))
                footprint.SetOrientationDegrees(current_rotation)
        print(f"SD local pass {pass_index + 1}: {improved} improved")
        if not improved:
            break

    final_points, _ = rebuild_net_points(
        footprints,
        bounds,
        MOVING,
        all_group_nets | CONNECTOR_NETS,
        include_moving=True,
    )
    final_score = group_score(final_points, all_group_nets)
    report = {
        "board": str(args.board),
        "connector": CONNECTOR,
        "region_mm": list(REGION),
        "moving": list(MOVING),
        "initial_group_airwire_mm": round(initial_score, 3),
        "final_group_airwire_mm": round(final_score, 3),
        "group_crossings": crossing_count(final_points),
        "placements": placements,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
