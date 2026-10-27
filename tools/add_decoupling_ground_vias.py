"""Add one GND stitching via beside each decoupling capacitor."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_REPORT = ROOT / "tmp" / "decoupling-ground-vias.json"
VIA_DIAMETER_MM = 0.6
VIA_DRILL_MM = 0.3
STUB_WIDTH_MM = 0.5
OFFSETS_MM = (1.15, 1.35, 1.55, 1.8, 2.1)
ANGLE_OFFSETS = (0, 30, -30, 60, -60, 90, -90, 180)
MIN_CENTER_CLEARANCE_MM = 0.35


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def distance_to_segment(point, start, end) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return math.dist(point, start)
    factor = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / length_squared
    factor = max(0.0, min(1.0, factor))
    closest = start[0] + factor * dx, start[1] + factor * dy
    return math.dist(point, closest)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = list(board.GetFootprints())
    board_box = board.GetBoardEdgesBoundingBox()
    min_x = pcbnew.ToMM(board_box.GetLeft()) + 1.0
    max_x = pcbnew.ToMM(board_box.GetRight()) - 1.0
    min_y = pcbnew.ToMM(board_box.GetTop()) + 1.0
    max_y = pcbnew.ToMM(board_box.GetBottom()) - 1.0

    existing_gnd_vias = [
        point_mm(item.GetPosition())
        for item in board.GetTracks()
        if isinstance(item, pcbnew.PCB_VIA)
        and item.GetNetname() == "GND"
    ]
    track_segments = [
        (
            item.GetNetname(),
            point_mm(item.GetStart()),
            point_mm(item.GetEnd()),
        )
        for item in board.GetTracks()
        if item.GetClass() == "PCB_TRACK"
    ]
    all_pads = [
        pad
        for footprint in footprints
        for pad in footprint.Pads()
    ]

    placements = []
    skipped = []
    for footprint in footprints:
        reference = footprint.GetReference()
        if not reference.startswith("C") or footprint.GetValue() != "100nF":
            continue
        pads = list(footprint.Pads())
        gnd_pads = [pad for pad in pads if pad.GetNetname() == "GND"]
        if len(pads) != 2 or len(gnd_pads) != 1:
            continue
        gnd_pad = gnd_pads[0]
        signal_pad = next(pad for pad in pads if pad is not gnd_pad)
        gnd_point = point_mm(gnd_pad.GetPosition())
        signal_point = point_mm(signal_pad.GetPosition())
        if any(
            math.dist(gnd_point, existing) <= 3.5
            for existing in existing_gnd_vias
        ):
            skipped.append({"reference": reference, "reason": "existing GND via"})
            continue

        dx = gnd_point[0] - signal_point[0]
        dy = gnd_point[1] - signal_point[1]
        length = math.hypot(dx, dy)
        if not length:
            skipped.append({"reference": reference, "reason": "coincident pads"})
            continue
        base_angle = math.atan2(dy, dx)
        candidates = []
        for offset in OFFSETS_MM:
            for angle_offset in ANGLE_OFFSETS:
                angle = base_angle + math.radians(angle_offset)
                candidate = (
                    gnd_point[0] + offset * math.cos(angle),
                    gnd_point[1] + offset * math.sin(angle),
                )
                if not (min_x <= candidate[0] <= max_x and min_y <= candidate[1] <= max_y):
                    continue
                pad_clearance = min(
                    (
                        math.dist(candidate, point_mm(pad.GetPosition()))
                        - VIA_DIAMETER_MM / 2
                        for pad in all_pads
                        if pad.GetNetname() not in ("", "GND")
                    ),
                    default=1000.0,
                )
                track_clearance = min(
                    (
                        distance_to_segment(
                            candidate,
                            point_mm(track.GetStart()),
                            point_mm(track.GetEnd()),
                        )
                        - VIA_DIAMETER_MM / 2
                        for track in board.GetTracks()
                if track.GetClass() == "PCB_TRACK"
                        and track.GetNetname() not in ("", "GND")
                    ),
                    default=1000.0,
                )
                score = min(pad_clearance, track_clearance)
                if score >= MIN_CENTER_CLEARANCE_MM:
                    candidates.append((offset, -score, candidate))
        if not candidates:
            skipped.append({"reference": reference, "reason": "no legal via site"})
            continue
        offset, negative_score, selected = min(candidates)
        placements.append(
            {
                "reference": reference,
                "gnd_pad": gnd_pad.GetNumber(),
                "gnd_pad_mm": [round(value, 3) for value in gnd_point],
                "via_mm": [round(value, 3) for value in selected],
                "offset_mm": round(offset, 3),
                "clearance_estimate_mm": round(-negative_score, 3),
            }
        )

    if args.apply:
        net = board.FindNet("GND")
        for placement in placements:
            via_x, via_y = placement["via_mm"]
            pad_x, pad_y = placement["gnd_pad_mm"]

            via = pcbnew.PCB_VIA(board)
            via.SetPosition(pcbnew.VECTOR2I_MM(via_x, via_y))
            via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
            via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetNet(net)
            board.Add(via)

            stub = pcbnew.PCB_TRACK(board)
            stub.SetStart(pcbnew.VECTOR2I_MM(pad_x, pad_y))
            stub.SetEnd(pcbnew.VECTOR2I_MM(via_x, via_y))
            stub.SetWidth(pcbnew.FromMM(STUB_WIDTH_MM))
            stub.SetLayer(pcbnew.F_Cu)
            stub.SetNet(net)
            board.Add(stub)
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)

    report = {
        "board": str(args.board),
        "apply": args.apply,
        "via_diameter_mm": VIA_DIAMETER_MM,
        "via_drill_mm": VIA_DRILL_MM,
        "stub_width_mm": STUB_WIDTH_MM,
        "added": len(placements),
        "skipped": len(skipped),
        "placements": placements,
        "skipped_details": skipped,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
