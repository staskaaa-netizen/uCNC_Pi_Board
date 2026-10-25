"""Audit interchangeable shift-register and driver channel assignments."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "hardware" / "motherboard.kicad_pcb"
NETLIST = ROOT / "hardware" / "motherboard.net.xml"


def segments_cross(a, b, c, d) -> bool:
    def cross(origin, point_a, point_b):
        return (
            (point_a[0] - origin[0]) * (point_b[1] - origin[1])
            - (point_a[1] - origin[1]) * (point_b[0] - origin[0])
        )

    ab_c = cross(a, b, c)
    ab_d = cross(a, b, d)
    cd_a = cross(c, d, a)
    cd_b = cross(c, d, b)
    return (ab_c * ab_d < 0.0) and (cd_a * cd_b < 0.0)


def crossing_count(segments) -> int:
    return sum(
        segments_cross(*segments[index], *segments[other])
        for index in range(len(segments))
        for other in range(index + 1, len(segments))
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(PCB))
    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    root = ET.parse(NETLIST).getroot()
    net_pads = defaultdict(list)
    for net in root.findall("./nets/net"):
        for node in net.findall("node"):
            fp = footprints.get(node.get("ref", ""))
            if fp is None:
                continue
            pad = fp.FindPadByNumber(node.get("pin", ""))
            if pad is None:
                continue
            pos = pad.GetPosition()
            net_pads[net.get("name", "")].append(
                (node.get("ref", ""), pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y))
            )

    def pin_position(ref: str, pin: str):
        pad = footprints[ref].FindPadByNumber(pin)
        if pad is None:
            return None
        pos = pad.GetPosition()
        return pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)

    def net_attachment_cost(ref: str, net: str, pin: str) -> float:
        if not net:
            return 0.0
        point = pin_position(ref, pin)
        others = [(x, y) for other_ref, x, y in net_pads[net] if other_ref != ref]
        if not others:
            return 0.0
        return min(math.hypot(point[0] - x, point[1] - y) for x, y in others)

    report = {"analyses": []}

    # 74HC165 D0-D7 are interchangeable. Compare current pin mapping with the
    # best full permutation for each physical register.
    for ref in ("U6", "U7", "U8", "U9"):
        pins = ("11", "12", "13", "14", "3", "4", "5", "6")
        current = []
        for pin in pins:
            pad = footprints[ref].FindPadByNumber(pin)
            current.append(pad.GetNetname())
        if any(not net for net in current):
            continue
        current_cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(current, pins))
        best_cost = current_cost
        best_order = list(current)
        for order in itertools.permutations(current):
            cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(order, pins))
            if cost < best_cost:
                best_cost = cost
                best_order = list(order)
        report["analyses"].append(
            {
                "type": "74HC165",
                "ref": ref,
                "current_mm": round(current_cost, 3),
                "best_mm": round(best_cost, 3),
                "improvement_mm": round(current_cost - best_cost, 3),
                "current": dict(zip(pins, current)),
                "best": dict(zip(pins, best_order)),
                "changed": current != best_order,
            }
        )

    # ULN2003 input channels are interchangeable within each package. Output
    # numbering is fixed by the connector, so only source-to-input cost varies.
    for ref in ("U26", "U27"):
        pins = ("1", "2", "3", "4")
        current = [footprints[ref].FindPadByNumber(pin).GetNetname() for pin in pins]
        if any(not net for net in current):
            continue
        current_cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(current, pins))
        best_cost = current_cost
        best_order = list(current)
        for order in itertools.permutations(current):
            cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(order, pins))
            if cost < best_cost:
                best_cost = cost
                best_order = list(order)
        report["analyses"].append(
            {
                "type": "ULN2003",
                "ref": ref,
                "current_mm": round(current_cost, 3),
                "best_mm": round(best_cost, 3),
                "improvement_mm": round(current_cost - best_cost, 3),
                "current": dict(zip(pins, current)),
                "best": dict(zip(pins, best_order)),
                "changed": current != best_order,
            }
        )

    # Optimize U12 -> U26/U27 -> J12 as one path. Each logical OUT16-23
    # remains paired with DO0-7; U12 Q pins and ULN input/output channels are
    # equivalent physical assignments.
    uln_channels = [
        (ref, input_pin, output_pin)
        for ref, input_numbers, output_numbers in (
            ("U26", ("1", "2", "3", "4"), ("16", "15", "14", "13")),
            ("U27", ("1", "2", "3", "4"), ("16", "15", "14", "13")),
        )
        for input_pin, output_pin in zip(input_numbers, output_numbers)
    ]
    logical_bits = tuple(range(16, 24))
    q_pins = ("15", "1", "2", "3", "4", "5", "6", "7")

    best_q_order = None
    best_input_cost = None
    best_input_crossings = None
    for q_order in itertools.permutations(q_pins):
        segments = [
            (
                pin_position("U12", q_pin),
                pin_position(channel_ref, input_pin),
            )
            for q_pin, (channel_ref, input_pin, _) in zip(q_order, uln_channels)
        ]
        cost = sum(math.dist(a, b) for a, b in segments)
        crossings = crossing_count(segments)
        if (
            best_input_cost is None
            or (crossings, cost) < (best_input_crossings, best_input_cost)
        ):
            best_input_cost = cost
            best_input_crossings = crossings
            best_q_order = q_order

    best_input_segments = [
        (
            pin_position("U12", q_pin),
            pin_position(channel_ref, input_pin),
        )
        for q_pin, (channel_ref, input_pin, _) in zip(best_q_order, uln_channels)
    ]
    best_logical_order = None
    best_total_cost = None
    best_total_crossings = None
    for logical_order in itertools.permutations(logical_bits):
        output_segments = []
        for (channel_ref, _, output_pin), bit in zip(uln_channels, logical_order):
            point = pin_position(channel_ref, output_pin)
            do_bit = bit - 16
            targets = [
                (x, y)
                for ref, x, y in net_pads[f"DO{do_bit}"]
                if ref not in {"U26", "U27"}
            ]
            output_segments.append(
                (point, min(targets, key=lambda target: math.dist(point, target)))
            )
        segments = best_input_segments + output_segments
        cost = sum(math.dist(a, b) for a, b in segments)
        crossings = crossing_count(segments)
        if (
            best_total_cost is None
            or (crossings, cost) < (best_total_crossings, best_total_cost)
        ):
            best_total_crossings = crossings
            best_total_cost = cost
            best_logical_order = logical_order

    current_q_order = []
    current_logical_order = []
    current_segments = []
    for channel_ref, input_pin, output_pin in uln_channels:
        input_net = footprints[channel_ref].FindPadByNumber(input_pin).GetNetname()
        output_net = footprints[channel_ref].FindPadByNumber(output_pin).GetNetname()
        bit = int(input_net[3:])
        current_logical_order.append(int(output_net[2:]) + 16)
        q_pin = next(
            pin
            for pin in q_pins
            if footprints["U12"].FindPadByNumber(pin).GetNetname() == input_net
        )
        current_q_order.append(q_pin)
        current_segments.append(
            (pin_position("U12", q_pin), pin_position(channel_ref, input_pin))
        )
        current_segments.append(
            (
                pin_position(channel_ref, output_pin),
                min(
                    [
                        (x, y)
                        for ref, x, y in net_pads[output_net]
                        if ref not in {"U26", "U27"}
                    ],
                    key=lambda target: math.dist(
                        pin_position(channel_ref, output_pin), target
                    ),
                ),
            )
        )

    best_output_segments = []
    for (channel_ref, _, output_pin), bit in zip(uln_channels, best_logical_order):
        point = pin_position(channel_ref, output_pin)
        do_bit = bit - 16
        targets = [
            (x, y)
            for ref, x, y in net_pads[f"DO{do_bit}"]
            if ref not in {"U26", "U27"}
        ]
        best_output_segments.append(
            (point, min(targets, key=lambda target: math.dist(point, target)))
        )
    current_cost = sum(math.dist(a, b) for a, b in current_segments)
    best_segments = best_input_segments + best_output_segments
    report["analyses"].append(
        {
            "type": "74HC595_ULN2003_path",
            "register": "U12",
            "packages": ["U26", "U27"],
            "current_mm": round(current_cost, 3),
            "best_mm": round(best_total_cost, 3),
            "improvement_mm": round(current_cost - best_total_cost, 3),
            "current_q_pins_by_channel": current_q_order,
            "best_q_pins_by_channel": list(best_q_order),
            "current_out_by_channel": current_logical_order,
            "best_out_by_channel": list(best_logical_order),
            "current_crossings": crossing_count(current_segments),
            "best_crossings": crossing_count(best_segments),
            "changed": (
                crossing_count(current_segments) != crossing_count(best_segments)
                or current_cost - best_total_cost > 0.05
            ),
        }
    )

    # Audit the fixed source/connector orientation of each 4x100R array.
    # Resistor terminals are not flipped; only the net assigned to each
    # source-side pin 1-4 and connector-side pin 8-5 is reported.
    for ref, base_bit in (("RN16", 0), ("RN17", 4), ("RN18", 8), ("RN19", 12)):
        bits = tuple(range(base_bit, base_bit + 4))
        channels = (0, 1, 2, 3)
        source_pins = tuple(str(channel + 1) for channel in channels)
        connector_pins = tuple(str(8 - channel) for channel in channels)

        def nearest_other(net: str, reference: str) -> tuple[float, float]:
            points = [(x, y) for owner, x, y in net_pads[net] if owner != reference]
            return points

        source_bits = [
            int(footprints[ref].FindPadByNumber(pin).GetNetname()[4:])
            for pin in source_pins
        ]
        connector_bits = [
            int(footprints[ref].FindPadByNumber(pin).GetNetname()[6:])
            for pin in connector_pins
        ]
        def output_metrics(output_order):
            segments = []
            cost = 0.0
            for source_pin, connector_pin, source_bit, connector_bit in zip(
                source_pins, connector_pins, source_bits, output_order
            ):
                source_point = pin_position(ref, source_pin)
                connector_point = pin_position(ref, connector_pin)
                source = min(
                    nearest_other(f"BUFY{source_bit}", ref),
                    key=lambda point: math.dist(source_point, point),
                )
                connector = min(
                    nearest_other(f"MOTION{connector_bit}", ref),
                    key=lambda point: math.dist(connector_point, point),
                )
                segments.extend(((source_point, source), (connector_point, connector)))
                cost += math.dist(source_point, source) + math.dist(connector_point, connector)
            return crossing_count(segments), cost

        current_crossings, cost = output_metrics(connector_bits)
        best_output_bits = tuple(connector_bits)
        best_crossings = current_crossings
        best_cost = cost
        for output_order in itertools.permutations(connector_bits):
            crossings, candidate_cost = output_metrics(output_order)
            if (crossings, candidate_cost) < (best_crossings, best_cost):
                best_output_bits = output_order
                best_crossings = crossings
                best_cost = candidate_cost
        report["analyses"].append(
            {
                "type": "4x100R",
                "ref": ref,
                "current_mm": round(cost, 3),
                "best_mm": round(best_cost, 3),
                "improvement_mm": round(cost - best_cost, 3),
                "source_bits_by_channel": source_bits,
                "connector_bits_by_channel": connector_bits,
                "best_connector_bits_by_channel": list(best_output_bits),
                "source_by_pin": {
                    pin: f"BUFY{bit}" for pin, bit in zip(source_pins, source_bits)
                },
                "connector_by_pin": {
                    pin: f"MOTION{bit}" for pin, bit in zip(connector_pins, connector_bits)
                },
                "best_connector_by_pin": {
                    pin: f"MOTION{bit}"
                    for pin, bit in zip(connector_pins, best_output_bits)
                },
                "crossings": [current_crossings, best_crossings],
                "changed": (
                    current_crossings != best_crossings or cost - best_cost > 0.05
                ),
            }
        )

    # 74HC595 Q outputs are interchangeable. Compare their current bit order
    # with the best physical permutation based on the downstream attachment.
    for ref in ("U10", "U11", "U12", "U13"):
        pins = ("15", "1", "2", "3", "4", "5", "6", "7")
        current = [footprints[ref].FindPadByNumber(pin).GetNetname() for pin in pins]
        if any(not net for net in current):
            continue
        current_cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(current, pins))
        best_cost = current_cost
        best_order = list(current)
        for order in itertools.permutations(current):
            cost = sum(net_attachment_cost(ref, net, pin) for net, pin in zip(order, pins))
            if cost < best_cost:
                best_cost = cost
                best_order = list(order)
        report["analyses"].append(
            {
                "type": "74HC595",
                "ref": ref,
                "current_mm": round(current_cost, 3),
                "best_mm": round(best_cost, 3),
                "improvement_mm": round(current_cost - best_cost, 3),
                "current": dict(zip(pins, current)),
                "best": dict(zip(pins, best_order)),
                "changed": current != best_order,
            }
        )

    # 541 input/output channels are fixed pairs. Compare the current OUT-bit
    # assignment with the best permutation across the eight package channels.
    for ref in ("U24", "U25"):
        input_pins = ("2", "3", "4", "5", "6", "7", "8", "9")
        output_pins = ("18", "17", "16", "15", "14", "13", "12", "11")
        current = [footprints[ref].FindPadByNumber(pin).GetNetname() for pin in input_pins]
        if any(not net for net in current):
            continue
        current_cost = sum(
            net_attachment_cost(ref, net, pin)
            for net, pin in zip(current, input_pins)
        )
        best_cost = current_cost
        best_order = list(current)
        for order in itertools.permutations(current):
            cost = sum(
                net_attachment_cost(ref, net, pin)
                for net, pin in zip(order, input_pins)
            )
            if cost < best_cost:
                best_cost = cost
                best_order = list(order)
        report["analyses"].append(
            {
                "type": "74AHCT541",
                "ref": ref,
                "current_mm": round(current_cost, 3),
                "best_mm": round(best_cost, 3),
                "improvement_mm": round(current_cost - best_cost, 3),
                "current": dict(zip(input_pins, current)),
                "best": dict(zip(input_pins, best_order)),
                "changed": current != best_order,
            }
        )

    # Jointly optimize the 595 Q-pin-to-541-channel matching and the logical
    # OUT-bit-to-541-channel assignment. For every selected logical bit, the 595
    # Q pin is relabelled OUTn and the 541 output remains BUFYn. This preserves
    # the firmware-visible OUTn -> BUFYn -> MOTIONn mapping.
    buffer_output_to_downstream = {
        "U24": ({0: "BUFY0", 1: "BUFY1", 2: "BUFY2", 3: "BUFY3",
                4: "BUFY4", 5: "BUFY5", 6: "BUFY6", 7: "BUFY7"}, 0),
        "U25": ({0: "BUFY8", 1: "BUFY9", 2: "BUFY10", 3: "BUFY11",
                4: "BUFY12", 5: "BUFY13", 6: "BUFY14", 7: "BUFY15"}, 8),
    }
    for register_ref, buffer_ref in (("U10", "U24"), ("U11", "U25")):
        q_pins = ("15", "1", "2", "3", "4", "5", "6", "7")
        input_pins = ("2", "3", "4", "5", "6", "7", "8", "9")
        output_pins = ("18", "17", "16", "15", "14", "13", "12", "11")
        downstream_nets, base_bit = buffer_output_to_downstream[buffer_ref]
        logical_bits = tuple(range(base_bit, base_bit + 8))

        best_q_order = None
        best_input_cost = None
        best_input_crossings = None
        for q_order in itertools.permutations(q_pins):
            segments = [
                (pin_position(register_ref, q_pin), pin_position(buffer_ref, input_pin))
                for q_pin, input_pin in zip(q_order, input_pins)
            ]
            cost = sum(math.dist(a, b) for a, b in segments)
            crossings = crossing_count(segments)
            if (
                best_input_cost is None
                or (crossings, cost) < (best_input_crossings, best_input_cost)
            ):
                best_input_crossings = crossings
                best_input_cost = cost
                best_q_order = q_order

        best_input_segments = [
            (pin_position(register_ref, q_pin), pin_position(buffer_ref, input_pin))
            for q_pin, input_pin in zip(best_q_order, input_pins)
        ]
        best_logical_order = None
        best_total_cost = None
        best_total_crossings = None
        for logical_order in itertools.permutations(logical_bits):
            output_segments = []
            for channel, bit in enumerate(logical_order):
                point = pin_position(buffer_ref, output_pins[channel])
                target_net = f"BUFY{bit}"
                targets = [(x, y) for ref, x, y in net_pads[target_net] if ref != buffer_ref]
                nearest = min(targets, key=lambda target: math.dist(point, target))
                output_segments.append((point, nearest))
            segments = best_input_segments + output_segments
            cost = sum(math.dist(a, b) for a, b in segments)
            crossings = crossing_count(segments)
            if (
                best_total_cost is None
                or (crossings, cost) < (best_total_crossings, best_total_cost)
            ):
                best_total_crossings = crossings
                best_total_cost = cost
                best_logical_order = logical_order

        current_logical_order = tuple(
            int(footprints[buffer_ref].FindPadByNumber(pin).GetNetname()[4:])
            for pin in output_pins
        )
        current_q_order = tuple(
            next(
                q_pin
                for q_pin in q_pins
                if footprints[register_ref].FindPadByNumber(q_pin).GetNetname()
                == f"OUT{bit}"
            )
            for bit in current_logical_order
        )
        current_input_cost = sum(
            math.dist(pin_position(register_ref, q_pin), pin_position(buffer_ref, input_pin))
            for q_pin, input_pin in zip(current_q_order, input_pins)
        )
        current_input_segments = [
            (pin_position(register_ref, q_pin), pin_position(buffer_ref, input_pin))
            for q_pin, input_pin in zip(current_q_order, input_pins)
        ]
        current_output_segments = []
        for channel, bit in enumerate(current_logical_order):
            point = pin_position(buffer_ref, output_pins[channel])
            targets = [
                (x, y) for ref, x, y in net_pads[f"BUFY{bit}"] if ref != buffer_ref
            ]
            current_output_segments.append(
                (point, min(targets, key=lambda target: math.dist(point, target)))
            )
        current_output_cost = sum(
            math.dist(a, b) for a, b in current_output_segments
        )
        current_total = current_input_cost + current_output_cost
        best_total = sum(
            math.dist(a, b) for a, b in best_input_segments
        ) + sum(
            math.dist(
                pin_position(buffer_ref, output_pins[channel]),
                min(
                    [(x, y) for ref, x, y in net_pads[f"BUFY{bit}"] if ref != buffer_ref],
                    key=lambda target: math.dist(
                        pin_position(buffer_ref, output_pins[channel]), target
                    ),
                ),
            )
            for channel, bit in enumerate(best_logical_order)
        )
        current_segments = current_input_segments + current_output_segments
        best_output_segments = []
        for channel, bit in enumerate(best_logical_order):
            point = pin_position(buffer_ref, output_pins[channel])
            targets = [
                (x, y) for ref, x, y in net_pads[f"BUFY{bit}"] if ref != buffer_ref
            ]
            best_output_segments.append(
                (point, min(targets, key=lambda target: math.dist(point, target)))
            )
        best_segments = best_input_segments + best_output_segments
        report["analyses"].append(
            {
                "type": "paired_74HC595_74AHCT541",
                "register": register_ref,
                "buffer": buffer_ref,
                "current_mm": round(current_total, 3),
                "best_mm": round(best_total, 3),
                "improvement_mm": round(current_total - best_total, 3),
                "register_q_pins_by_channel": list(best_q_order),
                "logical_out_by_channel": list(best_logical_order),
                "register_out_by_pin": {
                    q_pin: f"OUT{bit}"
                    for q_pin, bit in zip(best_q_order, best_logical_order)
                },
                "buffer_input_by_channel": {
                    input_pin: f"OUT{bit}"
                    for input_pin, bit in zip(input_pins, best_logical_order)
                },
                "buffer_output_by_channel": {
                    output_pin: f"BUFY{bit}"
                    for output_pin, bit in zip(output_pins, best_logical_order)
                },
                "current_register_q_pins_by_channel": list(current_q_order),
                "current_logical_out_by_channel": list(current_logical_order),
                "input_crossings": [
                    crossing_count(current_input_segments),
                    crossing_count(best_input_segments),
                ],
                "output_crossings": [
                    crossing_count(current_output_segments),
                    crossing_count(best_output_segments),
                ],
                "total_crossings": [
                    crossing_count(current_segments),
                    crossing_count(best_segments),
                ],
                "changed": current_total - best_total > 0.05,
            }
        )

    report["total_improvement_mm"] = round(
        sum(item.get("improvement_mm", 0.0) for item in report["analyses"]), 3
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
