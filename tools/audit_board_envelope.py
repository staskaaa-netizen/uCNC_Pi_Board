"""Report footprint courtyard extents and available board-edge reduction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def mm(value: float) -> float:
    return round(pcbnew.ToMM(value), 3)


def footprint_box(footprint):
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--edge-clearance", type=float, default=1.0)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    drawings = [
        item
        for item in board.GetDrawings()
        if item.GetLayer() == pcbnew.Edge_Cuts
    ]
    xs = [
        coordinate
        for item in drawings
        for coordinate in (
            mm(item.GetStart().x),
            mm(item.GetEnd().x),
        )
    ]
    ys = [
        coordinate
        for item in drawings
        for coordinate in (
            mm(item.GetStart().y),
            mm(item.GetEnd().y),
        )
    ]
    outline = {"left": min(xs), "top": min(ys), "right": max(xs), "bottom": max(ys)}

    entries = []
    for footprint in board.GetFootprints():
        position = footprint.GetPosition()
        x, y = mm(position.x), mm(position.y)
        if not (
            outline["left"] <= x <= outline["right"]
            and outline["top"] <= y <= outline["bottom"]
        ):
            continue
        box = footprint_box(footprint)
        entries.append(
            {
                "ref": footprint.GetReference(),
                "side": footprint.GetLayerName(),
                "bounds": [
                    mm(box.GetLeft()),
                    mm(box.GetTop()),
                    mm(box.GetRight()),
                    mm(box.GetBottom()),
                ],
            }
        )

    left = min(entry["bounds"][0] for entry in entries)
    top = min(entry["bounds"][1] for entry in entries)
    right = max(entry["bounds"][2] for entry in entries)
    bottom = max(entry["bounds"][3] for entry in entries)
    margin = args.edge_clearance

    def closest(edge):
        index = {"left": 0, "top": 1, "right": 2, "bottom": 3}[edge]
        if edge in {"left", "top"}:
            return sorted(entries, key=lambda entry: entry["bounds"][index])[:12]
        return sorted(entries, key=lambda entry: entry["bounds"][index], reverse=True)[:12]

    report = {
        "outline": outline,
        "occupied_envelope": {
            "left": round(left, 3),
            "top": round(top, 3),
            "right": round(right, 3),
            "bottom": round(bottom, 3),
        },
        "edge_clearance_mm": margin,
        "minimum_rectangular_outline": {
            "width": round(right - left + 2 * margin, 3),
            "height": round(bottom - top + 2 * margin, 3),
        },
        "closest_to_edges": {
            edge: closest(edge) for edge in ("left", "top", "right", "bottom")
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
