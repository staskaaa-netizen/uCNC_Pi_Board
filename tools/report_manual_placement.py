"""Report footprint position/orientation changes relative to a placement JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]


def wrap_delta(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--board",
        type=Path,
        default=ROOT / "hardware" / "motherboard.kicad_pcb",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        default=ROOT / "hardware" / "placement-optimized.json",
    )
    parser.add_argument(
        "--reference-board",
        type=Path,
        help="Compare against another PCB instead of the placement JSON",
    )
    parser.add_argument(
        "--refs",
        help="Comma-separated references to print even when their position is unchanged",
    )
    parser.add_argument(
        "--connectors",
        action="store_true",
        help="Print every connector with footprint, side and board position",
    )
    parser.add_argument(
        "--outside",
        action="store_true",
        help="Print counts and references for footprints parked off-board",
    )
    parser.add_argument(
        "--only-refs",
        action="store_true",
        help="Suppress the full changed-footprint report",
    )
    parser.add_argument(
        "--region",
        help="Print all footprints whose centers lie inside x1,y1,x2,y2",
    )
    parser.add_argument(
        "--pads",
        help="Print pad numbers, nets and coordinates for a reference",
    )
    args = parser.parse_args()

    if args.reference_board:
        reference_board = pcbnew.LoadBoard(str(args.reference_board))
        prior = {}
        for footprint in reference_board.GetFootprints():
            position = footprint.GetPosition()
            prior[footprint.GetReference()] = {
                "x": pcbnew.ToMM(position.x),
                "y": pcbnew.ToMM(position.y),
                "rotation": footprint.GetOrientationDegrees(),
            }
    else:
        prior = json.loads(args.reference.read_text(encoding="utf-8"))
    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    edge_box = board.GetBoardEdgesBoundingBox()
    left = pcbnew.ToMM(edge_box.GetLeft())
    top = pcbnew.ToMM(edge_box.GetTop())
    right = pcbnew.ToMM(edge_box.GetRight())
    bottom = pcbnew.ToMM(edge_box.GetBottom())

    def describe(footprint) -> str:
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        return (
            f"{footprint.GetReference():6s} {footprint.GetLayerName():4s} "
            f"now=({x:7.2f},{y:7.2f}) rot={footprint.GetOrientationDegrees() % 360.0:6.1f} "
            f"fp={footprint.GetFPID().GetLibItemName()} value={footprint.GetValue()}"
        )

    if args.connectors:
        for reference in sorted(ref for ref in footprints if ref.startswith("J")):
            print(describe(footprints[reference]))

    if args.outside:
        outside = []
        for footprint in footprints.values():
            position = footprint.GetPosition()
            x = pcbnew.ToMM(position.x)
            y = pcbnew.ToMM(position.y)
            if not (left <= x <= right and top <= y <= bottom):
                outside.append(footprint.GetReference())
        print(f"outside={len(outside)} refs={','.join(sorted(outside))}")

    if args.region:
        x1, y1, x2, y2 = (float(value) for value in args.region.split(","))
        for reference, footprint in sorted(footprints.items()):
            position = footprint.GetPosition()
            x = pcbnew.ToMM(position.x)
            y = pcbnew.ToMM(position.y)
            if x1 <= x <= x2 and y1 <= y <= y2:
                print(describe(footprint))

    if args.pads:
        footprint = footprints.get(args.pads)
        if footprint is None:
            print(f"{args.pads} missing")
        else:
            for pad in footprint.Pads():
                position = pad.GetPosition()
                print(
                    f"{args.pads}.{pad.GetNumber():<3s} "
                    f"{pad.GetNetname():18s} "
                    f"({pcbnew.ToMM(position.x):7.2f},{pcbnew.ToMM(position.y):7.2f})"
                )

    changed = []
    for footprint in footprints.values():
        reference = footprint.GetReference()
        if reference not in prior:
            continue
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        rotation = footprint.GetOrientationDegrees() % 360.0
        old = prior[reference]
        dx = x - old["x"]
        dy = y - old["y"]
        dr = wrap_delta(rotation - old["rotation"])
        if abs(dx) > 0.011 or abs(dy) > 0.011 or abs(dr) > 0.011:
            changed.append(
                (reference, x, y, rotation, dx, dy, dr)
            )

    if not args.only_refs:
        for reference, x, y, rotation, dx, dy, dr in sorted(changed):
            layer = footprints[reference].GetLayerName()
            print(
                f"{reference:6s} {layer:4s} now=({x:7.2f},{y:7.2f}) rot={rotation:6.1f} "
                f"delta=({dx:+7.2f},{dy:+7.2f}) rot={dr:+6.1f}"
            )
    for reference in filter(None, (args.refs or "").split(",")):
        footprint = footprints.get(reference.strip())
        if footprint is None:
            print(f"{reference.strip():6s} missing")
            continue
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        footprint.BuildCourtyardCaches()
        courtyard_layer = (
            pcbnew.B_CrtYd if footprint.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd
        )
        courtyard = footprint.GetCourtyard(courtyard_layer)
        box = courtyard.BBox() if courtyard.OutlineCount() else footprint.GetBoundingBox(False, False)
        print(
            describe(footprint)
            + (
                f" box=({pcbnew.ToMM(box.GetWidth()):5.2f}x"
                f"{pcbnew.ToMM(box.GetHeight()):5.2f})"
                f" bounds=({pcbnew.ToMM(box.GetLeft()):6.2f},"
                f"{pcbnew.ToMM(box.GetTop()):6.2f})-"
                f"({pcbnew.ToMM(box.GetRight()):6.2f},"
                f"{pcbnew.ToMM(box.GetBottom()):6.2f})"
            )
        )
    print(f"changed={len(changed)} total={len(list(board.GetFootprints()))}")


if __name__ == "__main__":
    main()
