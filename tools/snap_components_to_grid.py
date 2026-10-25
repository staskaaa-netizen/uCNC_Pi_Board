"""Snap in-board ICs and passives to a shared placement grid."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
MOVABLE_PREFIXES = ("U", "R", "C", "D", "L", "FB", "F", "Q")
CONNECTOR_PREFIXES = ("J", "MOD", "SW")
FIXED_PREFIXES = ("H", "FLG", "TP")


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def spans_sides(footprint) -> bool:
    return any(
        pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
        for pad in footprint.Pads()
    )


def add_box(footprint, box, occupied) -> None:
    layers = (
        (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
        if spans_sides(footprint)
        else (int(footprint.GetLayer()),)
    )
    for layer in layers:
        occupied[layer].append((footprint.GetReference(), box))


def replace_box(footprint, box, occupied) -> None:
    """Replace all stale occupancy entries for a footprint after a move."""
    reference = footprint.GetReference()
    for layer in occupied:
        occupied[layer] = [
            item for item in occupied[layer] if item[0] != reference
        ]
    add_box(footprint, box, occupied)


def is_movable(reference: str, include_connectors: bool) -> bool:
    prefixes = MOVABLE_PREFIXES + (CONNECTOR_PREFIXES if include_connectors else ())
    return reference.startswith(prefixes) and not reference.startswith(FIXED_PREFIXES)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--grid", type=float, default=0.635)
    parser.add_argument("--max-displacement", type=float, default=1.27)
    parser.add_argument("--include-connectors", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )

    def inside(footprint) -> bool:
        x, y = point_mm(footprint.GetPosition())
        return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]

    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        if not inside(footprint):
            continue
        x, y = point_mm(footprint.GetPosition())
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        replace_box(footprint, box, occupied)

    moving = sorted(
        (
            footprint
            for reference, footprint in footprints.items()
            if inside(footprint) and is_movable(reference, args.include_connectors)
        ),
        key=lambda footprint: (
            0 if footprint.GetReference().startswith("U") else 1,
            1 if footprint.GetReference().startswith(CONNECTOR_PREFIXES) else 2,
            -footprint.GetBoundingBox(False, False).GetWidth(),
        ),
    )

    changes = []
    skipped = []
    for footprint in moving:
        reference = footprint.GetReference()
        old_x, old_y = point_mm(footprint.GetPosition())
        old_rotation = footprint.GetOrientationDegrees()
        target_x = round(old_x / args.grid) * args.grid
        target_y = round(old_y / args.grid) * args.grid
        target_rotation = round(old_rotation / 90.0) * 90.0 % 360.0
        layer = int(footprint.GetLayer())
        blockers = [item for item in occupied[layer] if item[0] != reference]
        if spans_sides(footprint):
            other = int(pcbnew.B_Cu if layer == pcbnew.F_Cu else pcbnew.F_Cu)
            blockers = blockers + [
                item for item in occupied[other] if item[0] != reference
            ]

        best = None
        max_radius = max(0, math.ceil(args.max_displacement / args.grid))
        for radius in range(0, max_radius + 1):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if max(abs(dx), abs(dy)) != radius:
                        continue
                    x = target_x + dx * args.grid
                    y = target_y + dy * args.grid
                    footprint.SetOrientationDegrees(target_rotation)
                    box = candidate_boxes(footprint, x, y, clearance=0.05)
                    if not bbox_inside(box, 0.55):
                        continue
                    if any(overlap(box, blocker) for _, blocker in blockers):
                        continue
                    displacement = math.hypot(x - old_x, y - old_y)
                    if displacement > args.max_displacement + 1e-6:
                        continue
                    score = displacement
                    if best is None or score < best[0]:
                        best = (score, x, y, target_rotation, box)
            if best is not None:
                break
        if best is None:
            footprint.SetPosition(pcbnew.VECTOR2I_MM(old_x, old_y))
            footprint.SetOrientationDegrees(old_rotation)
            skipped.append(reference)
            print(f"{reference:5s} unchanged: no legal snap within {args.max_displacement:.2f} mm")
            continue
        score, x, y, rotation, box = best
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(rotation)
        add_box(footprint, box, occupied)
        changes.append(
            {
                "reference": reference,
                "old": [round(old_x, 3), round(old_y, 3), old_rotation],
                "new": [round(x, 3), round(y, 3), rotation],
                "distance_mm": round(score, 3),
            }
        )
        print(
            f"{reference:5s} ({old_x:7.3f},{old_y:7.3f}) -> "
            f"({x:7.3f},{y:7.3f})  d={score:.3f}"
        )

    report = {
        "grid_mm": args.grid,
        "moved": len(changes),
        "skipped": skipped,
        "max_displacement_mm": max((item["distance_mm"] for item in changes), default=0.0),
        "mean_displacement_mm": (
            sum(item["distance_mm"] for item in changes) / len(changes)
            if changes else 0.0
        ),
        "changes": changes,
    }
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "changes"}, indent=2))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
