"""Move conflicting visible reference/value fields to clear silkscreen space."""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
SILK_LAYERS = {pcbnew.F_SilkS, pcbnew.B_SilkS}
TEXT_SIZE_MM = 0.8
TEXT_THICKNESS_MM = 0.12
CLEARANCE_MM = 0.18
BOARD_MARGIN_MM = 0.5
GRID_MM = 1.27

Box = tuple[float, float, float, float]


@dataclass
class Field:
    footprint: object
    kind: str
    item: object
    layer: int
    anchor: tuple[float, float]
    origin: tuple[float, float]
    box: Box

    @property
    def key(self) -> str:
        return f"{self.footprint.GetReference()}.{self.kind}"


def bbox(item) -> Box:
    box = item.GetBoundingBox()
    return (
        pcbnew.ToMM(box.GetLeft()),
        pcbnew.ToMM(box.GetTop()),
        pcbnew.ToMM(box.GetRight()),
        pcbnew.ToMM(box.GetBottom()),
    )


def overlaps(first: Box, second: Box, clearance: float = CLEARANCE_MM) -> bool:
    return not (
        first[2] + clearance <= second[0]
        or second[2] + clearance <= first[0]
        or first[3] + clearance <= second[1]
        or second[3] + clearance <= first[1]
    )


def inside(box: Box, bounds: Box) -> bool:
    return (
        box[0] >= bounds[0] + BOARD_MARGIN_MM
        and box[1] >= bounds[1] + BOARD_MARGIN_MM
        and box[2] <= bounds[2] - BOARD_MARGIN_MM
        and box[3] <= bounds[3] - BOARD_MARGIN_MM
    )


def field_angle(field: Field) -> float:
    return field.item.GetTextAngleDegrees()


def normalize_field(field: Field) -> None:
    field.item.SetTextSize(pcbnew.VECTOR2I_MM(TEXT_SIZE_MM, TEXT_SIZE_MM))
    field.item.SetTextThickness(pcbnew.FromMM(TEXT_THICKNESS_MM))
    field.item.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    field.item.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    field.item.ClearBoundingBoxCache()


def standardize_visible_fields(board) -> int:
    """Use one legal text size for every visible footprint reference/value."""
    count = 0
    for footprint in board.GetFootprints():
        for field in (footprint.Reference(), footprint.Value()):
            if not field.IsVisible() or field.GetLayer() not in SILK_LAYERS:
                continue
            field.SetTextSize(pcbnew.VECTOR2I_MM(TEXT_SIZE_MM, TEXT_SIZE_MM))
            field.SetTextThickness(pcbnew.FromMM(TEXT_THICKNESS_MM))
            field.ClearBoundingBoxCache()
            count += 1
    return count


def preferred_text_angle(footprint) -> float:
    """Run two-terminal parts lengthwise through the gap between their pads."""
    pads = list(footprint.Pads())
    if len(pads) != 2:
        return 0.0
    first = pads[0].GetPosition()
    second = pads[1].GetPosition()
    dx = abs(second.x - first.x)
    dy = abs(second.y - first.y)
    return 90.0 if dx >= dy else 0.0


def promote_fab_references(board) -> list[str]:
    promoted = []
    for footprint in board.GetFootprints():
        field = footprint.Reference()
        if field.GetLayer() not in {pcbnew.F_Fab, pcbnew.B_Fab}:
            continue
        layer = (
            pcbnew.B_SilkS
            if footprint.GetLayer() == pcbnew.B_Cu
            else pcbnew.F_SilkS
        )
        field.SetLayer(layer)
        field.SetVisible(True)
        field.SetMirrored(layer == pcbnew.B_SilkS)
        field.SetTextSize(pcbnew.VECTOR2I_MM(TEXT_SIZE_MM, TEXT_SIZE_MM))
        field.SetTextThickness(pcbnew.FromMM(TEXT_THICKNESS_MM))
        field.SetPosition(footprint.GetPosition())
        field.SetTextAngleDegrees(preferred_text_angle(footprint))
        field.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
        field.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        field.ClearBoundingBoxCache()
        promoted.append(footprint.GetReference())
    return promoted


def candidate_positions(anchor: tuple[float, float], initial_angle: float):
    angles = [initial_angle]
    for angle in (0.0, 90.0, 270.0):
        if angle not in angles:
            angles.append(angle)

    grid_x = round(anchor[0] / GRID_MM) * GRID_MM
    grid_y = round(anchor[1] / GRID_MM) * GRID_MM
    candidates = [(anchor[0], anchor[1], math.inf)]
    for x_index in range(-20, 21):
        for y_index in range(-20, 21):
            x = grid_x + x_index * GRID_MM
            y = grid_y + y_index * GRID_MM
            distance = math.hypot(x - anchor[0], y - anchor[1])
            candidates.append((x, y, distance))
    for x, y, _distance in sorted(candidates, key=lambda item: item[2]):
        for angle in angles:
            yield x, y, angle


def collect_fields(board) -> list[Field]:
    fields = []
    for footprint in board.GetFootprints():
        position = footprint.GetPosition()
        anchor = (pcbnew.ToMM(position.x), pcbnew.ToMM(position.y))
        for kind, field in (
            ("REF", footprint.Reference()),
            ("VAL", footprint.Value()),
        ):
            if field.IsVisible() and field.GetLayer() in SILK_LAYERS:
                fields.append(
                    Field(
                        footprint=footprint,
                        kind=kind,
                        item=field,
                        layer=field.GetLayer(),
                        anchor=anchor,
                        origin=(
                            pcbnew.ToMM(field.GetPosition().x),
                            pcbnew.ToMM(field.GetPosition().y),
                        ),
                        box=bbox(field),
                    )
                )
    return fields


def collect_obstacles(board) -> dict[int, list[Box]]:
    obstacles = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for footprint in board.GetFootprints():
        obstacles[pcbnew.F_SilkS].extend(bbox(pad) for pad in footprint.Pads())
        obstacles[pcbnew.B_SilkS].extend(bbox(pad) for pad in footprint.Pads())
        for item in footprint.GraphicalItems():
            layer = item.GetLayer()
            if layer in SILK_LAYERS:
                obstacles[layer].append(bbox(item))
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            track_box = bbox(item)
            obstacles[pcbnew.F_SilkS].append(track_box)
            obstacles[pcbnew.B_SilkS].append(track_box)
    for item in board.GetDrawings():
        layer = item.GetLayer()
        if layer in SILK_LAYERS:
            obstacles[layer].append(bbox(item))
    return obstacles


def conflicting_fields(
    fields: list[Field],
    obstacles: dict[int, list[Box]],
    bounds: Box,
) -> list[Field]:
    boxes_by_layer = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    for field in fields:
        boxes_by_layer[field.layer].append(field.box)

    conflicts = []
    for field in fields:
        others = boxes_by_layer[field.layer]
        if (
            not inside(field.box, (
                bounds[0] - BOARD_MARGIN_MM,
                bounds[1] - BOARD_MARGIN_MM,
                bounds[2] + BOARD_MARGIN_MM,
                bounds[3] + BOARD_MARGIN_MM,
            ))
            or any(
                overlaps(field.box, obstacle, clearance=0.0)
                for obstacle in obstacles[field.layer]
            )
            or sum(
                overlaps(field.box, other, clearance=0.0)
                for other in others
            ) > 1
        ):
            conflicts.append(field)
    return conflicts


def place_field(
    field: Field,
    obstacles: list[Box],
    placed_boxes: list[Box],
    bounds: Box,
) -> tuple[bool, tuple[float, float, float], float]:
    normalize_field(field)
    initial_angle = round(field_angle(field) / 90.0) * 90.0
    for x, y, angle in candidate_positions(field.origin, initial_angle):
        field.item.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        field.item.SetTextAngleDegrees(angle)
        field.item.ClearBoundingBoxCache()
        candidate_box = bbox(field.item)
        if not inside(candidate_box, bounds):
            continue
        if any(overlaps(candidate_box, obstacle) for obstacle in obstacles):
            continue
        if any(overlaps(candidate_box, other) for other in placed_boxes):
            continue
        distance = math.hypot(x - field.origin[0], y - field.origin[1])
        return True, (x, y, angle), distance

    return False, (0.0, 0.0, initial_angle), math.inf


def drc_field_keys(report_path: Path) -> set[str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    keys = set()
    for violation in report.get("violations", []):
        for item in violation.get("items", []):
            match = re.search(
                r"(Reference|Value) field of (\w+)",
                item.get("description", ""),
            )
            if match:
                kind = "REF" if match.group(1) == "Reference" else "VAL"
                keys.add(f"{match.group(2)}.{kind}")
    return keys


def place_silkscreen_fields(
    board,
    selected_keys: set[str] | None = None,
) -> dict:
    standardized_fields = standardize_visible_fields(board)
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )
    fields = collect_fields(board)
    obstacles = collect_obstacles(board)
    detected_conflicts = conflicting_fields(fields, obstacles, bounds)
    if selected_keys is None:
        conflicts = detected_conflicts
        missing_keys = []
    else:
        by_key = {field.key: field for field in fields}
        conflicts = [
            by_key[key] for key in sorted(selected_keys) if key in by_key
        ]
        missing_keys = sorted(selected_keys - set(by_key))
    conflict_keys = {field.key for field in conflicts}

    placed_boxes = {
        pcbnew.F_SilkS: [
            field.box for field in fields
            if field.key not in conflict_keys and field.layer == pcbnew.F_SilkS
        ],
        pcbnew.B_SilkS: [
            field.box for field in fields
            if field.key not in conflict_keys and field.layer == pcbnew.B_SilkS
        ],
    }
    moved = []
    failures = []
    for field in conflicts:
        ok, position, distance = place_field(
            field,
            obstacles[field.layer],
            placed_boxes[field.layer],
            bounds,
        )
        if not ok:
            failures.append(field.key)
            continue
        field.item.ClearBoundingBoxCache()
        placed_boxes[field.layer].append(bbox(field.item))
        moved.append(
            {
                "field": field.key,
                "position_mm": [
                    round(position[0], 3),
                    round(position[1], 3),
                ],
                "angle_deg": position[2],
                "distance_mm": round(distance, 3),
            }
        )

    return {
        "visible_fields": len(fields),
        "standardized_fields": standardized_fields,
        "detected_conflicting_fields": len(detected_conflicts),
        "conflicting_fields": len(conflicts),
        "moved_fields": len(moved),
        "unplaced_fields": failures,
        "missing_report_fields": missing_keys,
        "placements": moved,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--drc-report", type=Path)
    parser.add_argument("--promote-fab-references", action="store_true")
    parser.add_argument("--standardize-only", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    if args.standardize_only:
        standardized = standardize_visible_fields(board)
        if args.apply:
            pcbnew.SaveBoard(str(args.board), board)
            print(f"Saved {args.board}")
        print(
            {
                "standardized_fields": standardized,
                "text_size_mm": TEXT_SIZE_MM,
                "text_thickness_mm": TEXT_THICKNESS_MM,
            }
        )
        return
    promoted = (
        promote_fab_references(board)
        if args.promote_fab_references
        else []
    )
    selected_keys = (
        drc_field_keys(args.drc_report)
        if args.drc_report
        else None
    )
    if promoted:
        promoted_keys = {f"{reference}.REF" for reference in promoted}
        selected_keys = (
            promoted_keys
            if selected_keys is None
            else selected_keys | promoted_keys
        )
    report = place_silkscreen_fields(board, selected_keys)
    report["promoted_fab_references"] = len(promoted)
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")
    print(
        {
            key: report[key]
            for key in (
                "visible_fields",
                "standardized_fields",
                "promoted_fab_references",
                "detected_conflicting_fields",
                "conflicting_fields",
                "moved_fields",
                "unplaced_fields",
                "missing_report_fields",
            )
        }
    )
    if report["placements"]:
        print("Moved fields:")
        for placement in report["placements"]:
            print(
                f"  {placement['field']}: "
                f"{placement['position_mm']} "
                f"{placement['angle_deg']:.0f} deg "
                f"({placement['distance_mm']:.2f} mm)"
            )


if __name__ == "__main__":
    main()
