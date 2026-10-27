"""Optimize the LCD LVDS interface as a local placement block.

The board is treated as authoritative.  Candidate placements are evaluated on
the current pad nets, with a fixed set of surrounding footprints treated as
obstacles.  The board is only written when ``--apply`` is supplied.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap, put_on_side
from placement_metrics import mst_edges, segments_cross


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

MOVING = (
    "RN27",
    "RN26",
)

REGIONS = {
    "RN27": (122.0, 42.0, 154.0, 50.0),
    "RN26": (122.0, 42.0, 154.0, 50.0),
}

# The display block is the only area under active local optimization.  These
# nets are deliberately isolated from unrelated board domains so global user
# edits cannot pull these parts away from their connector.
DISPLAY_PREFIXES = ("HSTX_", "LVDS_")
DISPLAY_POWER: set[str] = set()
GRID_MM = 1.0


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def footprint_spans_sides(footprint) -> bool:
    return any(
        pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
        for pad in footprint.Pads()
    )


def box_at(footprint, x: float, y: float, rotation: float):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(rotation)
    return candidate_boxes(footprint, x, y, clearance=0.05)


def occupancy_for(
    footprints: dict,
    excluded: set[str],
) -> dict[int, list]:
    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    board = next(iter(footprints.values())).GetBoard()
    bounds = board.GetBoardEdgesBoundingBox()
    left, right = pcbnew.ToMM(bounds.GetLeft()), pcbnew.ToMM(bounds.GetRight())
    top, bottom = pcbnew.ToMM(bounds.GetTop()), pcbnew.ToMM(bounds.GetBottom())
    for reference, footprint in footprints.items():
        if reference in excluded:
            continue
        x, y = point_mm(footprint.GetPosition())
        if not (left - 0.1 <= x <= right + 0.1 and top - 0.1 <= y <= bottom + 0.1):
            continue
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        layers = (
            (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
            if footprint_spans_sides(footprint)
            else (int(footprint.GetLayer()),)
        )
        for layer in layers:
            occupied[layer].append(box)
    return occupied


def is_display_net(name: str) -> bool:
    return name.startswith(DISPLAY_PREFIXES) or name in DISPLAY_POWER


def display_segments(board) -> tuple[float, float]:
    pads_by_net = defaultdict(list)
    for footprint in board.GetFootprints():
        if footprint.GetReference().startswith(("U", "RN", "C", "R", "J", "MOD")):
            for pad in footprint.Pads():
                net = pad.GetNetname()
                if not is_display_net(net):
                    continue
                x, y = point_mm(pad.GetPosition())
                pads_by_net[net].append((x, y))

    segments = []
    weighted_length = 0.0
    for net, points in pads_by_net.items():
        weight = 2.5
        for a, b, length in mst_edges(points):
            weighted_length += weight * length
            segments.append((net, a, b, weight))

    weighted_crossings = 0.0
    crossings = 0
    for index, (net_a, a1, a2, weight_a) in enumerate(segments):
        for net_b, b1, b2, weight_b in segments[index + 1 :]:
            if net_a == net_b:
                continue
            if segments_cross(a1, a2, b1, b2):
                crossings += 1
                weighted_crossings += max(weight_a, weight_b)
    return weighted_length, weighted_crossings


def candidate_local_score(board, footprint) -> float:
    external = defaultdict(list)
    reference = footprint.GetReference()
    for other in board.GetFootprints():
        if other.GetReference() == reference:
            continue
        for pad in other.Pads():
            net = pad.GetNetname()
            if not is_display_net(net):
                continue
            external[net].append(point_mm(pad.GetPosition()))

    score = 0.0
    for pad in footprint.Pads():
        net = pad.GetNetname()
        if not is_display_net(net) or not external[net]:
            continue
        x, y = point_mm(pad.GetPosition())
        weight = 2.5
        score += weight * min(math.hypot(x - ex, y - ey) for ex, ey in external[net])
    return score


def candidate_placements(
    footprint,
    region: tuple[float, float, float, float],
    occupied,
):
    x1, y1, x2, y2 = region
    original = (
        point_mm(footprint.GetPosition()),
        footprint.GetOrientationDegrees(),
    )
    candidates = []
    x = math.ceil(x1 / GRID_MM) * GRID_MM
    while x <= x2:
        y = math.ceil(y1 / GRID_MM) * GRID_MM
        while y <= y2:
            for rotation in (0.0, 90.0, 180.0, 270.0):
                box = box_at(footprint, x, y, rotation)
                if not bbox_inside(box, 0.55):
                    continue
                layers = (
                    (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
                    if footprint_spans_sides(footprint)
                    else (int(pcbnew.F_Cu),)
                )
                if any(
                    overlap(box, other)
                    for layer in layers
                    for other in occupied[layer]
                ):
                    continue
                candidates.append((x, y, rotation))
            y += GRID_MM
        x += GRID_MM
    footprint.SetPosition(pcbnew.VECTOR2I_MM(*original[0]))
    footprint.SetOrientationDegrees(original[1])
    return candidates


def apply_placement(footprint, placement) -> None:
    x, y, rotation = placement
    put_on_side(footprint, back=False)
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(rotation)


def optimize(board, footprints, passes: int, moving: tuple[str, ...]):
    history = []
    for pass_index in range(passes):
        pass_changes = []
        for reference in moving:
            footprint = footprints[reference]
            old = (
                *point_mm(footprint.GetPosition()),
                footprint.GetOrientationDegrees(),
            )
            occupied = occupancy_for(footprints, {reference})
            candidates = candidate_placements(
                footprint,
                REGIONS[reference],
                occupied,
            )
            if not candidates:
                raise RuntimeError(f"No collision-free placement for {reference}")

            # Use a cheap nearest-endpoint score to shortlist half-grid
            # positions, then compare the shortlist with the complete display
            # block metric.  This keeps the search interactive while still
            # accounting for crossings between all display nets.
            local_ranked = []
            for candidate in candidates:
                apply_placement(footprint, candidate)
                local_ranked.append((candidate_local_score(board, footprint), candidate))
            local_ranked.sort(key=lambda item: (item[0], item[1]))
            shortlist = [candidate for _, candidate in local_ranked[:60]]

            best = None
            for candidate in shortlist:
                apply_placement(footprint, candidate)
                length, crossings = display_segments(board)
                objective = length + 4.0 * crossings
                ranked = (round(objective, 6), crossings, length, candidate)
                if best is None or ranked < best[0]:
                    best = (ranked, candidate, length, crossings)
            if best is None:
                raise RuntimeError(f"No scored placement for {reference}")
            _, candidate, length, crossings = best
            apply_placement(footprint, candidate)
            if (
                abs(candidate[0] - old[0]) > 0.001
                or abs(candidate[1] - old[1]) > 0.001
                or abs(candidate[2] - old[2]) > 0.001
            ):
                pass_changes.append(
                    {
                        "ref": reference,
                        "old": [round(old[0], 3), round(old[1], 3), old[2]],
                        "new": [round(candidate[0], 3), round(candidate[1], 3), candidate[2]],
                        "weighted_length_mm": round(length, 3),
                        "weighted_crossings": round(crossings, 3),
                    }
                )
        history.append({"pass": pass_index + 1, "changes": pass_changes})
        if not pass_changes:
            break
    return history


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--passes", type=int, default=4)
    parser.add_argument("--ref", action="append")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    moving = tuple(args.ref) if args.ref else MOVING
    unknown = sorted(set(moving) - REGIONS.keys())
    if unknown:
        raise SystemExit(f"No candidate region for: {', '.join(unknown)}")
    missing = sorted(set(moving) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")

    before = display_segments(board)
    history = optimize(board, footprints, args.passes, moving)
    after = display_segments(board)
    report = {
        "board": str(args.board),
        "moving": list(moving),
        "before": {
            "weighted_length_mm": round(before[0], 3),
            "weighted_crossings": round(before[1], 3),
        },
        "after": {
            "weighted_length_mm": round(after[0], 3),
            "weighted_crossings": round(after[1], 3),
        },
        "placements": {
            reference: {
                "x": round(point_mm(footprints[reference].GetPosition())[0], 3),
                "y": round(point_mm(footprints[reference].GetPosition())[1], 3),
                "rotation": round(footprints[reference].GetOrientationDegrees(), 3),
                "side": footprints[reference].GetLayerName(),
            }
            for reference in moving
        },
        "passes": history,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
