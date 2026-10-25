"""Optimize PLC connector-to-chain and optocoupler-to-shift-register mappings.

Logical PLC channel numbers are intentionally treated as software aliases.
The PCB objective is minimum ratline crossing count followed by total length.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import pcbnew

from placement_metrics import segments_cross


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
CONNECTORS = ("J7", "J8")
REGISTERS = ("U8", "U9")
DATA_PINS = ("11", "12", "13", "14", "3", "4", "5", "6")


def point_mm(point) -> tuple[float, float]:
    return pcbnew.ToMM(point.x), pcbnew.ToMM(point.y)


def crossing_count(segments) -> int:
    return sum(
        segments_cross(*segments[index], *segments[other])
        for index in range(len(segments))
        for other in range(index + 1, len(segments))
    )


def length(segments) -> float:
    return sum(math.dist(a, b) for a, b in segments)


def objective(segments) -> tuple[int, float]:
    return crossing_count(segments), round(length(segments), 3)


def optimize_target_order(initial, sources, source_points, target_points):
    best = list(initial)

    def score(order):
        segments = [
            (source_points[source], target_points[target])
            for source, target in zip(sources, order)
        ]
        crossings, total = objective(segments)
        return crossings, total

    best_score = score(best)
    changed = True
    while changed:
        changed = False
        for left, right in itertools.combinations(range(len(best)), 2):
            candidate = list(best)
            candidate[left], candidate[right] = candidate[right], candidate[left]
            candidate_score = score(candidate)
            if candidate_score < best_score:
                best = candidate
                best_score = candidate_score
                changed = True
                break
    return best, best_score


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    missing = sorted(set(CONNECTORS + REGISTERS) - footprints.keys())
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")

    # Stage A: field connector signal pins to the first 2.2 k resistor pad.
    connector_pads = []
    for reference in CONNECTORS:
        connector = footprints[reference]
        for pad in connector.Pads():
            net = pad.GetNetname()
            if net.startswith("FIELD_IN"):
                connector_pads.append(
                    (
                        reference,
                        pad.GetNumber(),
                        net,
                        point_mm(pad.GetPosition()),
                    )
                )
    connector_pads.sort(key=lambda item: (item[3][1], item[0], int(item[1])))

    chain_pads = {}
    for number in range(1, 17):
        net = f"FIELD_IN{number}"
        candidates = []
        for reference in (f"R{17 + number}",):
            footprint = footprints[reference]
            pad = next((p for p in footprint.Pads() if p.GetNetname() == net), None)
            if pad is not None:
                candidates.append((reference, pad.GetNumber(), point_mm(pad.GetPosition())))
        if len(candidates) != 1:
            raise RuntimeError(f"Expected one chain input for {net}, got {candidates}")
        chain_pads[net] = candidates[0]

    chain_order = sorted(chain_pads, key=lambda net: (chain_pads[net][2][1], net))
    current_a = [
        (item[3], chain_pads[item[2]][2]) for item in connector_pads
    ]
    sorted_a = [
        (connector_pads[i][3], chain_pads[chain_order[i]][2])
        for i in range(16)
    ]

    # Stage B: optocoupler collector nodes to 74HC165 data inputs.
    source_points = {}
    for number in range(1, 17):
        net = f"PLC_IN{number}_N"
        for reference in ("U18", "U19", "U20", "U21"):
            for pad in footprints[reference].Pads():
                if pad.GetNetname() == net:
                    source_points[net] = point_mm(pad.GetPosition())
        if net not in source_points:
            raise RuntimeError(f"Missing optocoupler output {net}")

    target_points = {}
    target_meta = {}
    for reference in REGISTERS:
        for pin in DATA_PINS:
            pad = footprints[reference].FindPadByNumber(pin)
            net = pad.GetNetname()
            if not net.startswith("PLC_IN"):
                continue
            target_points[net] = point_mm(pad.GetPosition())
            target_meta[net] = {"register": reference, "pin": pin}
    if len(target_points) != 16:
        raise RuntimeError(f"Expected 16 populated PLC data pins, got {len(target_points)}")

    current_nets = list(target_points)
    current_b = [
        (source_points[net], target_points[net]) for net in current_nets
    ]

    # Candidate assignments keep the optocoupler source order fixed and
    # permute which legal register input receives each source node.
    source_nets = sorted(
        source_points,
        key=lambda net: int(net.removeprefix("PLC_IN").removesuffix("_N")),
    )
    target_nets = sorted(
        target_points,
        key=lambda net: int(net.removeprefix("PLC_IN").removesuffix("_N")),
    )
    initial_targets = list(target_nets)
    optimized_targets, best_b_score = optimize_target_order(
        initial_targets,
        source_nets,
        source_points,
        target_points,
    )

    # A second start based on vertical source/target order avoids a weak local
    # minimum when two registers occupy different columns.
    source_by_y = sorted(source_points, key=lambda net: (source_points[net][1], net))
    target_by_y = sorted(target_points, key=lambda net: (target_points[net][1], net))
    y_initial_targets = list(target_by_y)
    y_optimized_targets, y_score = optimize_target_order(
        y_initial_targets,
        source_nets,
        source_points,
        target_points,
    )
    if y_score < best_b_score:
        optimized_targets = y_optimized_targets
        best_b_score = y_score

    current_mapping = {source: source for source in source_nets}
    optimized_mapping = dict(zip(source_nets, optimized_targets))
    register_bit = {}
    for net, meta in target_meta.items():
        bit = 8 if meta["register"] == "U8" else 0
        bit += DATA_PINS.index(meta["pin"])
        register_bit[net] = bit

    report = {
        "stage_a_connector_to_field_chain": {
            "current": objective(current_a),
            "sorted": objective(sorted_a),
            "connector_by_y": [
                {
                    "connector": item[0],
                    "pin": int(item[1]),
                    "field_net": chain_order[index],
                }
                for index, item in enumerate(connector_pads)
            ],
        },
        "stage_b_opto_to_74hc165": {
            "current": objective(current_b),
            "optimized": best_b_score,
            "current_mapping": current_mapping,
            "optimized_mapping": optimized_mapping,
            "optimized_targets": {
                source: target_meta[target]
                for source, target in optimized_mapping.items()
            },
        },
        "firmware_input_bits_by_field_net": {
            field_net: register_bit[optimized_mapping[field_net]]
            for field_net in source_nets
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
