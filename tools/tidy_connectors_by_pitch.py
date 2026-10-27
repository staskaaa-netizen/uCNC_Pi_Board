"""Normalize connector anchors and align metric connector edge rows."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_REPORT = ROOT / "tmp" / "connector-tidy-report.json"

METRIC_35_GRID_MM = 0.25
IMPERIAL_254_GRID_MM = 0.635
DEFAULT_GRID_MM = 0.5
TOP_ROW_ANCHOR_Y_MM = 6.75
BOTTOM_ROW_ANCHOR_Y_MM = 145.0


def snap(value: float, grid: float) -> float:
    return math.floor(value / grid + 0.5) * grid


def classify(footprint) -> tuple[str, float]:
    name = str(footprint.GetFPID().GetLibItemName())
    if "P3.50mm" in name:
        return "phoenix_3.5mm", METRIC_35_GRID_MM
    if "P2.54mm" in name:
        return "header_2.54mm", IMPERIAL_254_GRID_MM
    return "other_connector", DEFAULT_GRID_MM


def target_y(
    family: str, grid: float, footprint, old_y: float
) -> float:
    if family != "phoenix_3.5mm":
        return snap(old_y, grid)
    rotation = footprint.GetOrientationDegrees() % 360
    if math.isclose(rotation, 180.0, abs_tol=1e-6) and old_y < 20.0:
        return TOP_ROW_ANCHOR_Y_MM
    if math.isclose(rotation, 0.0, abs_tol=1e-6) and old_y > 130.0:
        return BOTTOM_ROW_ANCHOR_Y_MM
    return snap(old_y, grid)


def courtyard_box(footprint):
    footprint.BuildCourtyardCaches()
    layer = (
        pcbnew.B_CrtYd
        if footprint.GetLayer() == pcbnew.B_Cu
        else pcbnew.F_CrtYd
    )
    courtyard = footprint.GetCourtyard(layer)
    return (
        courtyard.BBox()
        if courtyard.OutlineCount()
        else footprint.GetBoundingBox(False, False)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    connectors = sorted(
        (
            footprint
            for footprint in board.GetFootprints()
            if footprint.GetReference().startswith(("J", "JP"))
        ),
        key=lambda footprint: footprint.GetReference(),
    )
    changes = []
    skipped_locked = []
    for footprint in connectors:
        reference = footprint.GetReference()
        if footprint.IsLocked():
            skipped_locked.append(reference)
            continue

        family, grid = classify(footprint)
        old_position = footprint.GetPosition()
        old_x = pcbnew.ToMM(old_position.x)
        old_y = pcbnew.ToMM(old_position.y)
        old_rotation = footprint.GetOrientationDegrees()
        old_offsets = sorted(
            (
                pad.GetNumber(),
                pad.GetPosition().x - old_position.x,
                pad.GetPosition().y - old_position.y,
            )
            for pad in footprint.Pads()
        )

        new_x = snap(old_x, grid)
        new_y = target_y(family, grid, footprint, old_y)
        new_position = pcbnew.VECTOR2I_MM(new_x, new_y)
        if new_position == old_position:
            continue

        footprint.SetPosition(new_position)
        if footprint.GetOrientationDegrees() != old_rotation:
            raise RuntimeError(f"{reference}: rotation changed")
        moved_position = footprint.GetPosition()
        new_offsets = sorted(
            (
                pad.GetNumber(),
                pad.GetPosition().x - moved_position.x,
                pad.GetPosition().y - moved_position.y,
            )
            for pad in footprint.Pads()
        )
        if old_offsets != new_offsets:
            raise RuntimeError(f"{reference}: relative pad position changed")

        changes.append(
            {
                "reference": reference,
                "family": family,
                "grid_mm": grid,
                "old_mm": [round(old_x, 6), round(old_y, 6)],
                "new_mm": [round(new_x, 6), round(new_y, 6)],
                "rotation_deg": old_rotation,
                "displacement_mm": round(
                    math.hypot(new_x - old_x, new_y - old_y), 6
                ),
            }
        )

    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)

    row_edges = {}
    for reference in (
        "J1", "J5", "J6", "J13", "J14", "J15",
        "J24", "J25", "J26",
        "J10", "J11", "J12", "J28", "J29", "J30", "J31",
    ):
        footprint = next(
            (item for item in connectors if item.GetReference() == reference),
            None,
        )
        if footprint is None:
            continue
        box = courtyard_box(footprint)
        row_edges[reference] = {
            "left_mm": round(pcbnew.ToMM(box.GetLeft()), 3),
            "top_mm": round(pcbnew.ToMM(box.GetTop()), 3),
            "right_mm": round(pcbnew.ToMM(box.GetRight()), 3),
            "bottom_mm": round(pcbnew.ToMM(box.GetBottom()), 3),
        }

    report = {
        "board": str(args.board),
        "applied": args.apply,
        "connectors": len(connectors),
        "moved": len(changes),
        "skipped_locked": skipped_locked,
        "changes": changes,
        "courtyards": row_edges,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"changes", "courtyards"}
            },
            indent=2,
        )
    )
    for change in changes:
        print(
            f"{change['reference']:4s} {change['family']:16s} "
            f"{change['old_mm']} -> {change['new_mm']} "
            f"rot={change['rotation_deg']:g} d={change['displacement_mm']:.3f}"
        )


if __name__ == "__main__":
    main()
