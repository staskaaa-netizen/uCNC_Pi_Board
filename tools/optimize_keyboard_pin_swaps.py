"""Choose equivalent RN20/21/22/24 element and terminal assignments."""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import pcbnew

from generate_pcb import net_weight


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
PACKAGES = {
    "RN20": ([f"OUT{bit}" for bit in range(24, 28)], [f"KOUT{bit}" for bit in range(0, 4)]),
    "RN21": ([f"OUT{bit}" for bit in range(28, 32)], [f"KOUT{bit}" for bit in range(4, 8)]),
    "RN22": ([f"KIN{bit}" for bit in range(0, 4)], [f"KIN{bit}_FILT" for bit in range(0, 4)]),
    "RN24": ([f"KIN{bit}" for bit in range(4, 8)], [f"KIN{bit}_FILT" for bit in range(4, 8)]),
}
ELEMENTS = ((1, 8), (2, 7), (3, 6), (4, 5))


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def mst_edges(points):
    unique = list(dict.fromkeys(points))
    if len(unique) < 2:
        return []
    remaining = set(range(1, len(unique)))
    visited = {0}
    edges = []
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                length = math.dist(unique[i], unique[j])
                if best is None or length < best[0]:
                    best = (length, i, j)
        length, i, j = best
        edges.append((unique[i], unique[j], length))
        visited.add(j)
        remaining.remove(j)
    return edges


def orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_cross(a, b, c, d) -> bool:
    if {a, b} & {c, d}:
        return False
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    return (o1 == 0 or o2 == 0 or o1 * o2 < 0) and (
        o3 == 0 or o4 == 0 or o3 * o4 < 0
    )


def score(segments, fixed_segments):
    length = sum(math.dist(start, end) for _, start, end in segments)
    crossings = 0
    for index, (_, start, end) in enumerate(segments):
        for _, fixed_start, fixed_end in fixed_segments:
            if segments_cross(start, end, fixed_start, fixed_end):
                crossings += 1
        for _, other_start, other_end in segments[index + 1:]:
            if segments_cross(start, end, other_start, other_end):
                crossings += 1
    return crossings, length


def candidate_mappings(package, footprints, fixed_endpoints):
    footprint = footprints[package]
    pads = {pad.GetNumber(): point_mm(pad.GetPosition()) for pad in footprint.Pads()}
    source_nets, target_nets = PACKAGES[package]
    channels = list(zip(source_nets, target_nets))
    results = []
    for order in itertools.permutations(range(4)):
        for flips in itertools.product((False, True), repeat=4):
            pairs = []
            segments = []
            for element_index, channel_index, flip in zip(range(4), order, flips):
                source, target = channels[channel_index]
                pin_a, pin_b = ELEMENTS[element_index]
                point_a, point_b = pads[str(pin_a)], pads[str(pin_b)]
                if flip:
                    point_a, point_b = point_b, point_a
                pair = (source, target) if not flip else (target, source)
                pairs.append(pair)
                segments.append((source, point_a, fixed_endpoints[source]))
                segments.append((target, point_b, fixed_endpoints[target]))
            results.append(
                {
                    "pairs": pairs,
                    "segments": segments,
                }
            )
    return results


def current_mapping(package, footprints, fixed_endpoints):
    footprint = footprints[package]
    pads = {pad.GetNumber(): pad.GetNetname() for pad in footprint.Pads()}
    source_nets, target_nets = PACKAGES[package]
    source_set, target_set = set(source_nets), set(target_nets)
    pairs = []
    segments = []
    for pin_a, pin_b in ELEMENTS:
        net_a, net_b = pads[str(pin_a)], pads[str(pin_b)]
        if net_a in source_set and net_b in target_set:
            source, target = net_a, net_b
            flip = False
        elif net_b in source_set and net_a in target_set:
            source, target = net_b, net_a
            flip = True
        else:
            raise RuntimeError(f"Unexpected mapping in {package}: {net_a}, {net_b}")
        pairs.append((source, target) if not flip else (target, source))
        point_a = point_mm(next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pin_a)).GetPosition())
        point_b = point_mm(next(pad for pad in footprint.Pads() if pad.GetNumber() == str(pin_b)).GetPosition())
        if flip:
            point_a, point_b = point_b, point_a
        segments.append((source, point_a, fixed_endpoints[source]))
        segments.append((target, point_b, fixed_endpoints[target]))
    return {"pairs": pairs, "segments": segments}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=BOARD)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    all_network_nets = {
        net for sources, targets in PACKAGES.values() for net in (*sources, *targets)
    }
    fixed_points = {}
    fixed_segments = []
    for reference, footprint in footprints.items():
        for pad in footprint.Pads():
            net = pad.GetNetname()
            if not net or net in all_network_nets:
                continue
            fixed_points.setdefault(net, []).append(point_mm(pad.GetPosition()))
    for net, points in fixed_points.items():
        if net_weight(net) == 0:
            continue
        fixed_segments.extend((net, a, b) for a, b, _ in mst_edges(points))

    fixed_endpoints = {}
    for sources, targets in PACKAGES.values():
        for net in (*sources, *targets):
            points = []
            for reference, footprint in footprints.items():
                if reference in PACKAGES:
                    continue
                for pad in footprint.Pads():
                    if pad.GetNetname() == net:
                        points.append(point_mm(pad.GetPosition()))
            if len(points) != 1:
                raise RuntimeError(f"{net}: expected one fixed endpoint, found {len(points)}")
            fixed_endpoints[net] = points[0]

    candidates = {
        package: candidate_mappings(package, footprints, fixed_endpoints)
        for package in PACKAGES
    }
    current = {
        package: current_mapping(package, footprints, fixed_endpoints)
        for package in PACKAGES
    }

    def combined_score(overrides):
        mappings = {**current, **overrides}
        segments = [segment for result in mappings.values() for segment in result["segments"]]
        return score(segments, fixed_segments)

    initial_crossings, initial_length = combined_score({})
    for pass_index in range(3):
        changed = False
        for package in PACKAGES:
            baseline = combined_score({})
            best = (baseline, current[package])
            for candidate in candidates[package]:
                value = combined_score({package: candidate})
                if value < best[0]:
                    best = (value, candidate)
            if best[0] < baseline:
                current[package] = best[1]
                changed = True
        print(f"pass {pass_index + 1}: crossings={combined_score({})[0]}, length={combined_score({})[1]:.3f}")
        if not changed:
            break

    final_crossings, final_length = combined_score({})
    result = {
        "initial": {"crossings": initial_crossings, "length_mm": round(initial_length, 3)},
        "final": {"crossings": final_crossings, "length_mm": round(final_length, 3)},
        "mappings": {
            package: [[list(pair) for pair in current[package]["pairs"]]]
            for package in PACKAGES
        },
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
