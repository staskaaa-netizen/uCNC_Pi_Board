"""Optimize RN12/RN13/RN20/RN21 pin maps without moving footprints."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_REPORT = ROOT / "tmp" / "fixed-rn-pin-maps.json"

ELEMENTS = ((1, 8), (2, 7), (3, 6), (4, 5))
PACKAGE_GROUPS = {
    "rn12-21": {
        "RN12": [(f"OUT{bit}", "GND") for bit in range(16, 20)],
        "RN13": [(f"OUT{bit}", "GND") for bit in range(20, 24)],
        "RN20": [(f"OUT{bit}", f"KOUT{bit - 24}") for bit in range(24, 28)],
        "RN21": [(f"OUT{bit}", f"KOUT{bit - 24}") for bit in range(28, 32)],
    },
    "rn13": {
        "RN13": [(f"OUT{bit}", "GND") for bit in range(20, 23)]
        + [(None, None)],
    },
    "outputs": {
        "RN8": [(f"BUFY{bit}", "GND") for bit in range(0, 4)],
        "RN9": [(f"BUFY{bit}", "GND") for bit in range(4, 8)],
        "RN10": [(f"BUFY{bit}", "GND") for bit in range(8, 12)],
        "RN11": [(f"BUFY{bit}", "GND") for bit in range(12, 16)],
    },
    "rn30-31": {
        "RN30": [(f"OUT{bit}", "GND") for bit in range(23, 27)],
        "RN31": [
            (f"OUT{bit}", "GND") for bit in range(27, 30)
        ] + [(None, None)],
    },
}
FOCUS_REGIONS_MM = {
    "rn12-21": (20.0, 20.0, 76.0, 58.0),
    "rn13": (45.0, 22.0, 72.0, 44.0),
    "outputs": (60.0, 15.0, 125.0, 34.0),
    "rn30-31": (28.0, 24.0, 54.0, 34.0),
}


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def closest_point_on_segment(point, start, end):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return start
    factor = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / length_squared
    factor = max(0.0, min(1.0, factor))
    return start[0] + factor * dx, start[1] + factor * dy


def orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (
        b[1] - a[1]
    ) * (c[0] - a[0])


def segments_cross(a, b, c, d) -> bool:
    if {a, b} & {c, d}:
        return False
    return (
        orientation(a, b, c) * orientation(a, b, d) < 0
        and orientation(c, d, a) * orientation(c, d, b) < 0
    )


def segment_near_region(start, end, region) -> bool:
    return not (
        max(start[0], end[0]) < region[0]
        or min(start[0], end[0]) > region[2]
        or max(start[1], end[1]) < region[1]
        or min(start[1], end[1]) > region[3]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--group", choices=tuple(PACKAGE_GROUPS), default="rn12-21"
    )
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    package_channels = PACKAGE_GROUPS[args.group]
    focus_region = FOCUS_REGIONS_MM[args.group]
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    packages = list(package_channels)

    fixed_pads = defaultdict(list)
    for reference, footprint in footprints.items():
        if reference in package_channels:
            continue
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if net:
                fixed_pads[net].append(point_mm(pad.GetPosition()))

    fixed_tracks = []
    for item in board.GetTracks():
        start = point_mm(item.GetStart())
        end = point_mm(item.GetEnd())
        if not segment_near_region(start, end, focus_region):
            continue
        fixed_tracks.append((item.GetNetname(), start, end))
    tracks_by_net = defaultdict(list)
    for net, start, end in fixed_tracks:
        tracks_by_net[net].append((start, end))

    def target_for(net: str, pad_point: tuple[float, float]):
        candidates = [
            closest_point_on_segment(pad_point, start, end)
            for start, end in tracks_by_net.get(net, ())
        ]
        candidates.extend(fixed_pads.get(net, ()))
        if not candidates:
            raise RuntimeError(f"No fixed target for {net}")
        return min(candidates, key=lambda point: math.dist(pad_point, point))

    def pin_points(reference: str):
        footprint = footprints[reference]
        return {
            pad.GetNumber(): point_mm(pad.GetPosition())
            for pad in footprint.Pads()
        }

    current = {}
    for reference in package_channels:
        footprint = footprints[reference]
        pads = {pad.GetNumber(): pad for pad in footprint.Pads()}
        points = {
            number: point_mm(pad.GetPosition())
            for number, pad in pads.items()
        }
        current[reference] = {
            "pairs": [
                (pads[str(pin_a)].GetNetname(), pads[str(pin_b)].GetNetname())
                for pin_a, pin_b in ELEMENTS
            ],
            "pads": points,
        }

    candidates = {}
    for reference, channels in package_channels.items():
        points = pin_points(reference)
        options = []
        for order in itertools.permutations(range(4)):
            for flips in itertools.product((False, True), repeat=4):
                pairs = []
                for channel_index, flip in zip(order, flips):
                    pair = channels[channel_index]
                    pairs.append(tuple(reversed(pair)) if flip else pair)
                options.append({"pairs": pairs, "pads": points})
        candidates[reference] = options

    def score(mapping):
        stubs = []
        for reference, mapping_data in mapping.items():
            points = mapping_data["pads"]
            for element_index, pair in enumerate(mapping_data["pairs"]):
                pin_a, pin_b = ELEMENTS[element_index]
                for pin, net in zip((pin_a, pin_b), pair):
                    if not net or net == "GND":
                        continue
                    pad_point = points[str(pin)]
                    stubs.append(
                        (net, pad_point, target_for(net, pad_point))
                    )
        length = sum(math.dist(start, end) for _, start, end in stubs)
        crossings = 0
        for index, (net, start, end) in enumerate(stubs):
            for track_net, track_start, track_end in fixed_tracks:
                if net != track_net and segments_cross(
                    start, end, track_start, track_end
                ):
                    crossings += 1
            for other_net, other_start, other_end in stubs[index + 1:]:
                if net == other_net:
                    continue
                if segments_cross(start, end, other_start, other_end):
                    crossings += 1
        return crossings, length

    initial_score = score(current)
    passes = []
    for pass_index in range(4):
        changed = False
        for reference in packages:
            baseline = score(current)
            best = (baseline, current[reference])
            for candidate in candidates[reference]:
                trial = {**current, reference: candidate}
                result = score(trial)
                if result < best[0]:
                    best = (result, candidate)
            if best[0] < baseline:
                current[reference] = best[1]
                changed = True
        passes.append(
            {
                "pass": pass_index + 1,
                "crossings": score(current)[0],
                "length_mm": round(score(current)[1], 3),
            }
        )
        if not changed:
            break

    final_score = score(current)
    mapping_report = {}
    for reference, mapping_data in current.items():
        mapping_report[reference] = []
        for element_index, pair in enumerate(mapping_data["pairs"]):
            pin_a, pin_b = ELEMENTS[element_index]
            mapping_report[reference].append(
                {
                    "element": element_index + 1,
                    f"pin_{pin_a}": pair[0],
                    f"pin_{pin_b}": pair[1],
                }
            )

    report = {
        "board": str(args.board),
        "group": args.group,
        "initial": {
            "crossings": initial_score[0],
            "length_mm": round(initial_score[1], 3),
        },
        "final": {
            "crossings": final_score[0],
            "length_mm": round(final_score[1], 3),
        },
        "passes": passes,
        "mapping": mapping_report,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
