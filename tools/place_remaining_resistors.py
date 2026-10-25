"""Place the remaining shift, keyboard, Wi-Fi and HDMI resistor groups."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap, put_on_side


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# (x_mm, y_mm, rotation_degrees, back_side)
PLACEMENTS = {
    # Shared shift-register bus controls, in the open row between U6-U9/U10-U13.
    "R10": (80.000, 49.000, 0.0, False),
    "R11": (87.000, 49.000, 0.0, False),
    "R12": (100.000, 49.000, 0.0, False),
    "R13": (112.000, 49.000, 0.0, False),
    "RN6": (68.000, 64.000, 0.0, False),
    "RN7": (73.000, 64.000, 0.0, False),
    # Keyboard banks stay on the J16 side of the board.
    "RN20": (28.920, 39.500, 90.0, False),
    "RN21": (39.080, 39.500, 90.0, False),
    "RN22": (28.920, 55.500, 90.0, False),
    "RN24": (39.080, 55.500, 90.0, False),
    # ESP-01S pulls, vertically aligned left of J20.
    "R58": (177.000, 45.500, 0.0, False),
    "R57": (177.000, 48.000, 0.0, False),
    "R56": (177.000, 50.500, 0.0, False),
    "R55": (177.000, 53.000, 0.0, False),
    # HDMI alternate 0R links remain DNP but are placed for routing completeness.
    "RN28": (176.500, 19.000, 0.0, False),
    "RN29": (183.000, 19.000, 0.0, False),
}


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
        occupied[layer].append(box)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    missing = sorted(set(PLACEMENTS) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")
    edge_box = board.GetBoardEdgesBoundingBox()
    bounds = (
        pcbnew.ToMM(edge_box.GetLeft()),
        pcbnew.ToMM(edge_box.GetTop()),
        pcbnew.ToMM(edge_box.GetRight()),
        pcbnew.ToMM(edge_box.GetBottom()),
    )
    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        if reference in PLACEMENTS:
            continue
        x, y = point_mm(footprint.GetPosition())
        if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
            continue
        box = candidate_boxes(footprint, x, y, clearance=0.0)
        add_box(footprint, box, occupied)

    for reference, (x, y, rotation, back_side) in PLACEMENTS.items():
        footprint = footprints[reference]
        put_on_side(footprint, back=back_side)
        footprint.SetOrientationDegrees(rotation)
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        if not bbox_inside(box, 0.55):
            raise RuntimeError(f"{reference} falls outside the board")
        blockers = occupied[int(footprint.GetLayer())]
        if spans_sides(footprint):
            blockers = blockers + occupied[
                int(pcbnew.B_Cu if footprint.GetLayer() == pcbnew.F_Cu else pcbnew.F_Cu)
            ]
        if any(overlap(box, other) for other in blockers):
            raise RuntimeError(f"{reference} overlaps another footprint")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        box = candidate_boxes(footprint, x, y, clearance=0.05)
        add_box(footprint, box, occupied)
        print(
            f"{reference:4s}: ({x:.3f}, {y:.3f}) rotation={rotation:.1f} "
            f"{footprint.GetLayerName()}"
        )

    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
