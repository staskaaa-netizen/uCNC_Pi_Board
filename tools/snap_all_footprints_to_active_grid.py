"""Snap every unlocked footprint to KiCad PCB Editor's active grid."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_SETTINGS = (
    Path(os.environ["APPDATA"]) / "kicad" / "10.0" / "pcbnew.json"
)


def parse_distance(value: str) -> float:
    match = re.fullmatch(
        r"\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|mil|in)\s*", value, re.IGNORECASE
    )
    if not match:
        raise ValueError(f"Unsupported grid distance: {value!r}")
    amount = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "mil":
        return amount * 0.0254
    if unit == "in":
        return amount * 25.4
    return amount


def active_grid_from_settings(path: Path) -> tuple[float, float, int]:
    settings = json.loads(path.read_text(encoding="utf-8"))
    grid = settings["window"]["grid"]
    index = int(grid["last_size"])
    selected = grid["sizes"][index]
    x = parse_distance(selected["x"])
    y = parse_distance(selected["y"])
    if not math.isclose(x, y, abs_tol=1e-9):
        raise ValueError(f"Rectangular grid is not supported: {selected}")
    return x, y, index


def snapped_mm(
    value: float, origin: float, pitch: float
) -> float:
    steps = (value - origin) / pitch
    return origin + math.floor(steps + 0.5) * pitch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "tmp" / "active-grid-footprint-snap-report.json",
    )
    args = parser.parse_args()

    grid_x, grid_y, grid_index = active_grid_from_settings(args.settings)
    board = pcbnew.LoadBoard(str(args.board))
    origin = board.GetDesignSettings().GetGridOrigin()
    origin_x = pcbnew.ToMM(origin.x)
    origin_y = pcbnew.ToMM(origin.y)

    moved = []
    locked = []
    unchanged = []
    max_pad_offset_error = 0
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if footprint.IsLocked():
            locked.append(reference)
            continue

        old_position = footprint.GetPosition()
        old_x = pcbnew.ToMM(old_position.x)
        old_y = pcbnew.ToMM(old_position.y)
        old_rotation = footprint.GetOrientationDegrees()
        pad_offsets = [
            (
                pad.GetNumber(),
                pad.GetPosition().x - old_position.x,
                pad.GetPosition().y - old_position.y,
            )
            for pad in footprint.Pads()
        ]

        new_x = snapped_mm(old_x, origin_x, grid_x)
        new_y = snapped_mm(old_y, origin_y, grid_y)
        new_position = pcbnew.VECTOR2I_MM(new_x, new_y)
        if new_position == old_position:
            unchanged.append(reference)
            continue

        footprint.SetPosition(new_position)
        if not math.isclose(
            footprint.GetOrientationDegrees(),
            old_rotation,
            abs_tol=1e-9,
        ):
            raise RuntimeError(f"{reference}: footprint rotation changed")

        moved_position = footprint.GetPosition()
        moved_offsets = [
            (
                pad.GetNumber(),
                pad.GetPosition().x - moved_position.x,
                pad.GetPosition().y - moved_position.y,
            )
            for pad in footprint.Pads()
        ]
        if moved_offsets != pad_offsets:
            raise RuntimeError(f"{reference}: relative pad position changed")
        max_pad_offset_error = max(
            max_pad_offset_error,
            max(
                (
                    max(
                        abs(pad.GetPosition().x - moved_position.x - offset_x),
                        abs(pad.GetPosition().y - moved_position.y - offset_y),
                    )
                    for pad, (_, offset_x, offset_y) in zip(
                        footprint.Pads(), pad_offsets
                    )
                ),
                default=0,
            ),
        )

        moved.append(
            {
                "reference": reference,
                "old_mm": [round(old_x, 6), round(old_y, 6)],
                "new_mm": [round(new_x, 6), round(new_y, 6)],
                "rotation_deg": old_rotation,
                "displacement_mm": round(
                    math.hypot(new_x - old_x, new_y - old_y), 6
                ),
            }
        )

    pcbnew.SaveBoard(str(args.board), board)
    report = {
        "board": str(args.board),
        "settings": str(args.settings),
        "grid_index": grid_index,
        "grid_mm": [grid_x, grid_y],
        "grid_origin_mm": [origin_x, origin_y],
        "footprints": len(board.GetFootprints()),
        "moved": len(moved),
        "unchanged": len(unchanged),
        "locked": len(locked),
        "max_displacement_mm": max(
            (item["displacement_mm"] for item in moved), default=0
        ),
        "max_relative_pad_offset_error_nm": max_pad_offset_error,
        "moved_references": moved,
        "unchanged_references": unchanged,
        "locked_references": locked,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key
                not in {
                    "moved_references",
                    "unchanged_references",
                    "locked_references",
                }
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
