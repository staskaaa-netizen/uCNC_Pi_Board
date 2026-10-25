"""Place power-stage capacitors next to the ICs they support."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pcbnew

from generate_pcb import bbox_inside, candidate_boxes, overlap


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# Placement order puts the smallest/highest-frequency capacitors closest to
# their target; bulk capacitors fill the remaining legal space.
ASSIGNMENTS = (
    ("C4", "U1"), ("C7", "U1"),
    ("C76", "U2"),
    ("C13", "U2"),
    ("C77", "U2"), ("C17", "U2"),
    ("C10", "U2"), ("C11", "U2"),
    ("C16", "U2"),
)

PREFERRED = {
    "C4": (48.5, 32.5),
    "C7": (57.8, 36.5),
    "C76": (73.0, 4.5),
    "C10": (78.0, 6.0),
    "C13": (78.0, 10.0),
    "C11": (78.0, 14.0),
    "C79": (74.0, 13.0),
    "C80": (74.0, 18.0),
    "C19": (66.5, 13.0),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--dry-run", action="store_true")
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

    def on_board(footprint) -> bool:
        position = footprint.GetPosition()
        x = pcbnew.ToMM(position.x)
        y = pcbnew.ToMM(position.y)
        return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]

    moving = {capacitor for capacitor, _ in ASSIGNMENTS}
    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    for reference, footprint in footprints.items():
        if reference in moving or not on_board(footprint):
            continue
        position = footprint.GetPosition()
        box = candidate_boxes(
            footprint,
            pcbnew.ToMM(position.x),
            pcbnew.ToMM(position.y),
            clearance=0.0,
        )
        occupied[int(footprint.GetLayer())].append(box)

    for capacitor_ref, ic_ref in ASSIGNMENTS:
        capacitor = footprints[capacitor_ref]
        ic = footprints[ic_ref]
        if capacitor.GetLayer() != ic.GetLayer():
            raise RuntimeError(f"{capacitor_ref} and {ic_ref} are on different sides")

        cap_nets = {
            pad.GetNetname()
            for pad in capacitor.Pads()
            if pad.GetNetname()
        }
        targets = []
        for pad in ic.Pads():
            if pad.GetNetname() not in cap_nets:
                continue
            position = pad.GetPosition()
            targets.append((pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)))
        if not targets:
            raise RuntimeError(f"No shared pad net between {capacitor_ref} and {ic_ref}")
        target_x = sum(x for x, _ in targets) / len(targets)
        target_y = sum(y for _, y in targets) / len(targets)
        preferred_x, preferred_y = PREFERRED.get(
            capacitor_ref,
            (target_x, target_y),
        )

        best = None
        for dx_step in range(-30, 31):
            for dy_step in range(-30, 31):
                x = preferred_x + dx_step * 0.635
                y = preferred_y + dy_step * 0.635
                for rotation in (0, 90, 180, 270):
                    capacitor.SetOrientationDegrees(rotation)
                    box = candidate_boxes(capacitor, x, y, clearance=0.0)
                    if not bbox_inside(box, 0.8):
                        continue
                    if any(overlap(box, other) for other in occupied[int(capacitor.GetLayer())]):
                        continue
                    score = math.hypot(x - preferred_x, y - preferred_y)
                    score += 0.08 * math.hypot(x - target_x, y - target_y)
                    score += 0.0005 * abs(rotation)
                    if best is None or score < best[0]:
                        best = (score, x, y, rotation, box)
        if best is None:
            raise RuntimeError(f"No legal decoupling location for {capacitor_ref}")
        score, x, y, rotation, box = best
        capacitor.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        capacitor.SetOrientationDegrees(rotation)
        occupied[int(capacitor.GetLayer())].append(box)
        print(
            f"{capacitor_ref} -> {ic_ref}: ({x:6.2f},{y:6.2f}) "
            f"rot={rotation:3.0f} distance={score:5.2f}"
        )

    if not args.dry_run:
        pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
