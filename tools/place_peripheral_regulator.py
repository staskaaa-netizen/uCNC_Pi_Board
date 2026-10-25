"""Place the peripheral 3.3 V regulator by power-rail demand.

This is a focused placement pass for U2 and its four local capacitors. It
does not move other footprints. The scoring separates the regulator's local
input/output loops from the complete +5 V and +3V3 distribution.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

REGULATOR = "U2"
CAPACITORS = ("C76", "C13", "C10", "C90")
MOVING = {REGULATOR, *CAPACITORS}
POWER_NETS = ("+5V", "+3V3")
ORIENTATIONS = (0.0, 90.0, 180.0, 270.0)


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def inside_board(footprint, bounds) -> bool:
    x, y = point_mm(footprint.GetPosition())
    return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]


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


def box_at(footprint, x: float, y: float, rotation: float, clearance: float):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(rotation)
    return candidate_boxes(footprint, x, y, clearance=clearance)


def legal_box(footprint, box, occupied, clearance: float = 0.7) -> bool:
    if not bbox_inside(box, clearance):
        return False
    blockers = occupied.get(int(pcbnew.F_Cu), [])
    if spans_sides(footprint):
        blockers = blockers + occupied.get(int(pcbnew.B_Cu), [])
    return not any(overlap(box, other) for other in blockers)


def mst_length(points: list[tuple[float, float]]) -> float:
    unique = list(dict.fromkeys(points))
    if len(unique) < 2:
        return 0.0
    remaining = set(range(1, len(unique)))
    visited = {0}
    total = 0.0
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                length = math.dist(unique[i], unique[j])
                if best is None or length < best[0]:
                    best = (length, j)
        length, j = best
        total += length
        visited.add(j)
        remaining.remove(j)
    return total


def net_points(footprints, moving):
    points = {net: [] for net in POWER_NETS}
    for reference, footprint in footprints.items():
        position = footprint.GetPosition()
        if reference in moving:
            continue
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net in points:
                points[net].append(point_mm(pad.GetPosition()))
    return points


def footprint_net_pads(footprint, net: str):
    return [
        point_mm(pad.GetPosition())
        for pad in footprint.Pads()
        if pad.GetNetname() == net
    ]


def nearest_pad_distance(source, source_net: str, target, target_net: str) -> float:
    source_points = footprint_net_pads(source, source_net)
    target_points = footprint_net_pads(target, target_net)
    if not source_points or not target_points:
        return 100.0
    return min(math.dist(a, b) for a in source_points for b in target_points)


def local_loop(regulator, capacitor) -> float:
    shared = sorted(
        {
            pad.GetNetname()
            for pad in regulator.Pads()
            if pad.GetNetname() in {p.GetNetname() for p in capacitor.Pads()}
        }
    )
    return sum(nearest_pad_distance(regulator, net, capacitor, net) for net in shared)


def distribution_score(regulator, base_points) -> float:
    points = {net: list(values) for net, values in base_points.items()}
    for pad in regulator.Pads():
        net = pad.GetNetname()
        if net in points:
            points[net].append(point_mm(pad.GetPosition()))
    return sum(mst_length(points[net]) for net in POWER_NETS)


def crowd_penalty(box, occupied, radius: float = 12.0) -> float:
    x = pcbnew.ToMM(box.GetCenter().x)
    y = pcbnew.ToMM(box.GetCenter().y)
    penalty = 0.0
    for other in occupied.get(int(pcbnew.F_Cu), []):
        other_x = pcbnew.ToMM(other.GetCenter().x)
        other_y = pcbnew.ToMM(other.GetCenter().y)
        distance = math.hypot(x - other_x, y - other_y)
        if distance < radius:
            penalty += (radius - distance) / radius
    return penalty


def spaced(candidates, count: int, spacing: float = 14.0):
    selected = []
    for candidate in candidates:
        x, y = candidate["x"], candidate["y"]
        if all(math.hypot(x - other["x"], y - other["y"]) >= spacing for other in selected):
            selected.append(candidate)
        if len(selected) == count:
            break
    return selected


def coarse_candidates(regulator, occupied, base_points):
    candidates = []
    x = 12.0
    while x <= 198.0:
        y = 12.0
        while y <= 138.0:
            for rotation in ORIENTATIONS:
                box = box_at(regulator, x, y, rotation, 0.7)
                if not legal_box(regulator, box, occupied):
                    continue
                distribution = distribution_score(regulator, base_points)
                crowd = crowd_penalty(box, occupied)
                score = distribution + 0.30 * crowd
                candidates.append(
                    {
                        "x": round(x, 3),
                        "y": round(y, 3),
                        "rotation": rotation,
                        "score": round(score, 3),
                        "distribution_mm": round(distribution, 3),
                        "crowd_penalty": round(crowd, 3),
                    }
                )
            y += 2.54
        x += 2.54
    candidates.sort(key=lambda item: item["score"])
    return spaced(candidates, 10)


def refine_regulator_candidates(regulator, occupied, base_points, coarse):
    candidates = []
    for origin in coarse:
        for dx_step in range(-5, 6):
            for dy_step in range(-5, 6):
                x = origin["x"] + dx_step * 0.635
                y = origin["y"] + dy_step * 0.635
                for rotation in ORIENTATIONS:
                    box = box_at(regulator, x, y, rotation, 0.7)
                    if not legal_box(regulator, box, occupied):
                        continue
                    distribution = distribution_score(regulator, base_points)
                    crowd = crowd_penalty(box, occupied)
                    score = distribution + 0.30 * crowd
                    candidates.append(
                        {
                            "x": round(x, 3),
                            "y": round(y, 3),
                            "rotation": rotation,
                            "score": round(score, 3),
                            "distribution_mm": round(distribution, 3),
                            "crowd_penalty": round(crowd, 3),
                        }
                    )
    candidates.sort(key=lambda item: item["score"])
    return spaced(candidates, 20, spacing=4.0)


def cap_candidates(cap, regulator, occupied, base_points):
    regulator_position = regulator.GetPosition()
    center_x, center_y = point_mm(regulator_position)
    best = None
    for dx_step in range(-20, 21):
        for dy_step in range(-20, 21):
            x = center_x + dx_step * 0.635
            y = center_y + dy_step * 0.635
            if math.hypot(x - center_x, y - center_y) > 12.5:
                continue
            for rotation in (0.0, 90.0):
                box = box_at(cap, x, y, rotation, 0.45)
                if not legal_box(cap, box, occupied):
                    continue
                loop = local_loop(regulator, cap)
                crowd = crowd_penalty(box, occupied, radius=8.0)
                score = loop + 0.10 * math.hypot(x - center_x, y - center_y) + 0.10 * crowd
                candidate = {
                    "x": round(x, 3),
                    "y": round(y, 3),
                    "rotation": rotation,
                    "loop_mm": round(loop, 3),
                    "score": round(score, 3),
                }
                if best is None or score < best[0]:
                    best = (score, candidate, box)
    return best


def place_group(regulator, capacitors, occupied, base_points, candidate):
    original = {
        footprint.GetReference(): (
            *point_mm(footprint.GetPosition()),
            footprint.GetOrientationDegrees(),
        )
        for footprint in (regulator, *capacitors)
    }
    group_occupied = {layer: list(boxes) for layer, boxes in occupied.items()}
    regulator_box = box_at(
        regulator,
        candidate["x"],
        candidate["y"],
        candidate["rotation"],
        0.7,
    )
    add_occupancy(regulator, regulator_box, group_occupied)
    placed = {}
    cap_loops = {}
    for cap in capacitors:
        best = cap_candidates(cap, regulator, group_occupied, base_points)
        if best is None:
            for reference, (x, y, rotation) in original.items():
                (regulator if reference == REGULATOR else next(
                    item for item in capacitors if item.GetReference() == reference
                )).SetPosition(pcbnew.VECTOR2I_MM(x, y))
                (regulator if reference == REGULATOR else next(
                    item for item in capacitors if item.GetReference() == reference
                )).SetOrientationDegrees(rotation)
            return None
        _, placement, box = best
        add_occupancy(cap, box, group_occupied)
        placed[cap.GetReference()] = placement
        cap_loops[cap.GetReference()] = placement["loop_mm"]
    distribution = distribution_score(regulator, base_points)
    total_loop = sum(cap_loops.values())
    score = distribution + 2.5 * total_loop
    return {
        **candidate,
        "group_score": round(score, 3),
        "distribution_mm": round(distribution, 3),
        "local_loop_mm": round(total_loop, 3),
        "capacitors": placed,
        "capacitor_loops_mm": cap_loops,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--candidate-index",
        type=int,
        default=0,
        help="Choose a ranked group result; 0 is the raw score minimum",
    )
    parser.add_argument(
        "--from-report",
        type=Path,
        help="Apply the selected placement from an existing proposal",
    )
    parser.add_argument(
        "--lock-regulator",
        action="store_true",
        help="Keep the hand-placed U2 fixed and optimize only its capacitors",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    missing = sorted(MOVING - footprints.keys())
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
        if reference in MOVING or not inside_board(footprint, bounds):
            continue
        position = footprint.GetPosition()
        x, y = point_mm(position)
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        add_occupancy(footprint, box, occupied)

    regulator = footprints[REGULATOR]
    capacitors = tuple(footprints[reference] for reference in CAPACITORS)
    if args.lock_regulator:
        x, y = point_mm(regulator.GetPosition())
        candidate = {
            "x": round(x, 3),
            "y": round(y, 3),
            "rotation": regulator.GetOrientationDegrees(),
            "score": 0.0,
            "distribution_mm": 0.0,
            "crowd_penalty": 0.0,
        }
        base_points = net_points(footprints, MOVING)
        selected = place_group(regulator, capacitors, occupied, base_points, candidate)
        if selected is None:
            raise SystemExit("No legal capacitor placement found around locked U2")
        alternatives = []
        candidate_index = 0
    elif args.from_report:
        prior_report = json.loads(args.from_report.read_text(encoding="utf-8"))
        selected = prior_report["selected"]
        alternatives = prior_report.get("alternatives", [])
        candidate_index = prior_report.get("candidate_index", 0)
    else:
        base_points = net_points(footprints, MOVING)
        coarse = coarse_candidates(regulator, occupied, base_points)
        refined = refine_regulator_candidates(regulator, occupied, base_points, coarse)

        group_results = []
        for candidate in refined:
            result = place_group(regulator, capacitors, occupied, base_points, candidate)
            if result is not None:
                group_results.append(result)
        group_results.sort(key=lambda item: item["group_score"])
        if not group_results:
            raise SystemExit("No legal regulator placement found")
        if not 0 <= args.candidate_index < len(group_results):
            raise SystemExit(
                f"candidate-index must be between 0 and {len(group_results) - 1}"
            )
        selected = group_results[args.candidate_index]
        candidate_index = args.candidate_index
        alternatives = [
            result for index, result in enumerate(group_results[:12])
            if index != candidate_index
        ]
    regulator.SetPosition(pcbnew.VECTOR2I_MM(selected["x"], selected["y"]))
    regulator.SetOrientationDegrees(selected["rotation"])
    for cap in capacitors:
        placement = selected["capacitors"][cap.GetReference()]
        cap.SetPosition(pcbnew.VECTOR2I_MM(placement["x"], placement["y"]))
        cap.SetOrientationDegrees(placement["rotation"])

    report = {
        "board": str(args.board),
        "moving": sorted(MOVING),
        "power_nets": list(POWER_NETS),
        "candidate_index": candidate_index,
        "selected": selected,
        "alternatives": alternatives,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "alternatives"}, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
