"""Snap footprints and their directly attached track endpoints to a coarse grid."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def snap(value: float, grid: float, origin: float) -> float:
    return origin + round((value - origin) / grid) * grid


def point_key(point) -> tuple[int, int]:
    return point.x, point.y


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--grid-mm", type=float, default=1.27)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--exclude-ref", action="append", default=[])
    parser.add_argument(
        "--unrouted-only",
        action="store_true",
        help="Move only footprints with no track or via endpoint on a pad",
    )
    parser.add_argument(
        "--max-attached-endpoints",
        type=int,
        help="Allow moving footprints with at most this many attached track endpoints",
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    grid = args.grid_mm
    origin = board.GetDesignSettings().GetGridOrigin()
    origin_x, origin_y = pcbnew.ToMM(origin.x), pcbnew.ToMM(origin.y)

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    old_pad_nets: dict[tuple[int, int], set[tuple[str, str]]] = defaultdict(set)
    attached_counts: dict[str, int] = defaultdict(int)
    tracks = list(board.GetTracks())
    for reference, footprint in footprints.items():
        for pad in footprint.Pads():
            position = pad.GetPosition()
            for track in tracks:
                points = (
                    [track.GetPosition()]
                    if isinstance(track, pcbnew.PCB_VIA)
                    else [track.GetStart(), track.GetEnd()]
                )
                if any(
                    abs(point.x - position.x) <= 1000
                    and abs(point.y - position.y) <= 1000
                    for point in points
                ):
                    attached_counts[reference] += 1

    if args.unrouted_only:
        selected = set(footprints) - set(attached_counts)
    elif args.max_attached_endpoints is not None:
        selected = {
            reference
            for reference in footprints
            if attached_counts.get(reference, 0) <= args.max_attached_endpoints
        }
    else:
        selected = set(footprints)
    selected -= set(args.exclude_ref)
    moves = {}
    for reference, footprint in footprints.items():
        position = footprint.GetPosition()
        old_x, old_y = pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)
        new_x = snap(old_x, grid, origin_x)
        new_y = snap(old_y, grid, origin_y)
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net:
                old_pad_nets[point_key(pad.GetPosition())].add((reference, net))
        if reference in selected:
            moves[reference] = {
                "old": (old_x, old_y),
                "new": (new_x, new_y),
                "rotation": footprint.GetOrientationDegrees(),
            }

    # Track endpoint transforms use the pre-move pad coordinates.
    endpoint_moves = {}
    for point, owners in old_pad_nets.items():
        if not owners:
            continue
        reference, _ = next(iter(owners))
        if reference not in moves:
            continue
        move = moves[reference]
        target = pcbnew.VECTOR2I_MM(*move["new"])
        footprint = footprints[reference]
        local = None
        for pad in footprint.Pads():
            if point_key(pad.GetPosition()) == point:
                old_pos = pad.GetPosition()
                local = (
                    old_pos.x - pcbnew.FromMM(move["old"][0]),
                    old_pos.y - pcbnew.FromMM(move["old"][1]),
                )
                break
        if local is not None:
            endpoint_moves[point] = (target.x + local[0], target.y + local[1])

    for reference, move in moves.items():
        footprints[reference].SetPosition(pcbnew.VECTOR2I_MM(*move["new"]))

    adjusted_endpoints = 0
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            continue
        net = track.GetNetname()
        for side in ("Start", "End"):
            point = track.GetStart() if side == "Start" else track.GetEnd()
            owners = old_pad_nets.get(point_key(point), set())
            if not any(owner_net == net for _, owner_net in owners):
                continue
            target = endpoint_moves.get(point_key(point))
            if target is None:
                continue
            if side == "Start":
                track.SetStart(pcbnew.VECTOR2I(*target))
            else:
                track.SetEnd(pcbnew.VECTOR2I(*target))
            adjusted_endpoints += 1

    # Report courtyard collisions after the coarse snap.
    boxes = {}
    collisions = []
    outside = []
    references = sorted(footprints)
    for reference in references:
        footprint = footprints[reference]
        position = footprint.GetPosition()
        x, y = pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        boxes[reference] = box
        if not bbox_inside(box):
            outside.append(reference)
    for index, ref_a in enumerate(references):
        a = footprints[ref_a]
        for ref_b in references[index + 1:]:
            b = footprints[ref_b]
            if a.GetLayer() != b.GetLayer():
                continue
            if overlap(boxes[ref_a], boxes[ref_b]):
                collisions.append([ref_a, ref_b])

    moved = [
        {
            "reference": reference,
            "old_mm": [round(move["old"][0], 6), round(move["old"][1], 6)],
            "new_mm": [round(move["new"][0], 6), round(move["new"][1], 6)],
            "displacement_mm": round(
                math.hypot(
                    move["new"][0] - move["old"][0],
                    move["new"][1] - move["old"][1],
                ),
                6,
            ),
            "rotation_degrees": move["rotation"],
        }
        for reference, move in moves.items()
        if move["old"] != move["new"]
    ]
    report = {
        "board": str(args.board),
        "grid_mm": grid,
        "grid_origin_mm": [origin_x, origin_y],
        "footprints": len(footprints),
        "selected_footprints": len(moves),
        "unrouted_only": args.unrouted_only,
        "max_attached_endpoints": args.max_attached_endpoints,
        "excluded_references": sorted(set(args.exclude_ref)),
        "moved": len(moved),
        "adjusted_track_endpoints": adjusted_endpoints,
        "collisions": collisions,
        "outside_board": outside,
        "moved_references": moved,
        "apply": args.apply,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key != "moved_references"
            },
            indent=2,
        )
    )
    if args.apply and (args.force or (not collisions and not outside)):
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")
    elif args.apply:
        raise SystemExit("Refusing to apply a snap with collisions or off-board parts")


if __name__ == "__main__":
    main()
