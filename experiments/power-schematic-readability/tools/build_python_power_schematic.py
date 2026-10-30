"""Method B: re-layout the existing power-sheet symbols with explicit wiring.

This script copies the source embedded KiCad symbol definitions, places the
same symbol instances in conventional functional blocks, and emits orthogonal
wires. It never writes the source schematic or PCB.
"""

from __future__ import annotations

import argparse
import json
import math
import uuid
from collections import Counter, defaultdict
from pathlib import Path

from kicad_sexpr import (
    child,
    children,
    extract_block,
    fmt,
    parse_file,
    property_value,
    quote,
)


PLACEMENTS: dict[str, tuple[float, float, float]] = {
    # Input, reverse-polarity protection, and protected input bulk capacitance.
    "J1": (35.56, 76.20, 180),
    "F1": (58.42, 76.20, 90),
    "D1": (72.39, 60.96, 270),
    "C1": (86.36, 60.96, 0),
    "C2": (96.52, 60.96, 0),
    "Q1": (119.38, 76.20, 0),
    "D2": (142.24, 64.77, 270),
    "R1": (111.76, 96.52, 0),
    "C3": (160.02, 105.41, 0),
    "C4": (170.18, 105.41, 0),
    "C5": (180.34, 105.41, 0),
    "FLG4": (198.12, 91.44, 0),
    # 5 V buck power stage and feedback/filter components.
    "U1": (215.90, 95.25, 0),
    "C91": (195.58, 125.73, 0),
    "C86": (238.76, 76.20, 0),
    "L1": (254.00, 71.12, 90),
    "C6": (275.59, 69.85, 0),
    "C7": (285.75, 69.85, 0),
    "C10": (295.91, 69.85, 0),
    "C11": (306.07, 69.85, 0),
    "C76": (316.23, 69.85, 0),
    "FLG2": (340.36, 63.50, 0),
    "R70": (370.84, 82.55, 0),
    "R71": (370.84, 104.14, 0),
    "R72": (370.84, 125.73, 0),
    "R73": (365.76, 125.73, 180),
    # 3.3 V point-of-load regulator, ferrite filter, and status outputs.
    "U2": (390.00, 95.25, 0),
    "C13": (410.00, 112.00, 0),
    "C90": (420.00, 112.00, 0),
    "FB1": (460.00, 105.41, 90),
    "C15": (475.00, 112.00, 0),
    "FLG3": (485.14, 105.41, 0),
    "R4": (500.00, 145.00, 90),
    "D4": (515.00, 145.00, 180),
    "R5": (480.00, 165.00, 90),
    "D5": (495.00, 165.00, 180),
    # Ground reference and off-sheet rail flags.
    "FLG1": (530.20, 135.00, 0),
    "FLG5": (550.00, 90.00, 0),
    "FLG6": (550.00, 110.00, 0),
    "FLG7": (550.00, 130.00, 0),
    "FLG8": (550.00, 150.00, 0),
}


LABEL_POSITIONS: dict[str, tuple[float, float, float]] = {
    "VIN_RAW": (47.63, 76.20, 0),
    "VIN_FUSED": (63.50, 57.15, 0),
    "VIN_PROT": (140.97, 91.44, 0),
    "Q1_GATE": (126.00, 76.20, 0),
    "GND": (25.40, 135.00, 0),
    "BUCK5_SW": (231.14, 86.36, 90),
    "BUCK5_BST": (234.95, 83.82, 90),
    "VCC5": (201.93, 107.95, 0),
    "PWR_GOOD_N": (310.00, 115.57, 0),
    "FB5_TOP": (370.84, 94.00, 90),
    "FB5": (350.00, 114.30, 0),
    "+5V": (268.00, 63.50, 0),
    "+3V3": (400.05, 105.41, 0),
    "+3V3_A": (470.00, 105.41, 0),
    "PWR5_LEDA": (507.00, 145.00, 0),
    "PWR3_LEDA": (487.00, 165.00, 0),
    "+5V_ENC": (550.00, 90.00, 0),
    "+3V3_SD": (550.00, 110.00, 0),
    "+5V_ISO_IN": (550.00, 130.00, 0),
    "+12V_FIELD": (550.00, 150.00, 0),
}


TITLES = [
    ("INPUT • FUSE • REVERSE-POLARITY PROTECTION", 22.86, 38.10),
    ("5 V BUCK POWER STAGE", 205.74, 38.10),
    ("3V3 LDO • FILTER • STATUS", 382.62, 38.10),
    ("OFF-SHEET RAIL FLAGS", 535.00, 127.00),
]


def stable_uuid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"lean-power-readability/{name}"))


def world_pin(
    x: float, y: float, angle: float, local_x: float, local_y: float
) -> tuple[float, float]:
    radians = math.radians(angle)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    wx = x + local_x * cosine - local_y * sine
    wy = y - (local_x * sine + local_y * cosine)
    return round(wx, 4), round(wy, 4)


def point_on_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    tolerance: float = 1e-5,
) -> bool:
    px, py = point
    x1, y1 = start
    x2, y2 = end
    if abs(x1 - x2) <= tolerance:
        return (
            abs(px - x1) <= tolerance
            and min(y1, y2) - tolerance <= py <= max(y1, y2) + tolerance
        )
    if abs(y1 - y2) <= tolerance:
        return (
            abs(py - y1) <= tolerance
            and min(x1, x2) - tolerance <= px <= max(x1, x2) + tolerance
        )
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    return abs(cross) <= tolerance


class Layout:
    def __init__(self) -> None:
        self.segments: list[tuple[str, tuple[float, float], tuple[float, float]]] = []
        self.labels = {
            net: (snap(x), snap(y), angle)
            for net, (x, y, angle) in LABEL_POSITIONS.items()
        }

    def path(self, net: str, points: list[tuple[float, float]]) -> None:
        points = [(snap(x), snap(y)) for x, y in points]
        for start, end in zip(points, points[1:]):
            start = (round(start[0], 4), round(start[1], 4))
            end = (round(end[0], 4), round(end[1], 4))
            if start == end:
                continue
            if abs(start[0] - end[0]) > 1e-5 and abs(start[1] - end[1]) > 1e-5:
                raise RuntimeError(f"Non-orthogonal wire on {net}: {start} -> {end}")
            segment = (net, start, end)
            if segment not in self.segments:
                self.segments.append(segment)

    def junctions(self) -> list[tuple[float, float]]:
        points: dict[tuple[float, float], set[str]] = defaultdict(set)
        endpoints = Counter()
        for net, start, end in self.segments:
            endpoints[start] += 1
            endpoints[end] += 1
            points[start].add(net)
            points[end].add(net)
        result = []
        for point, nets in points.items():
            if len(nets) != 1:
                raise RuntimeError(f"Wire endpoint short at {point}: {sorted(nets)}")
            touching = sum(
                1
                for _, start, end in self.segments
                if point_on_segment(point, start, end)
            )
            if touching >= 3 or (endpoints[point] >= 1 and touching > endpoints[point]):
                result.append(point)
        return sorted(set(result))

    def pin_junctions(
        self,
        pin_points: dict[tuple[str, str], tuple[float, float]],
        pin_nets: dict[tuple[str, str], str],
    ) -> list[tuple[float, float]]:
        result = set()
        for pin_key, point in pin_points.items():
            net = pin_nets.get(pin_key)
            if net is None:
                continue
            touches = [
                (start, end)
                for segment_net, start, end in self.segments
                if segment_net == net and point_on_segment(point, start, end)
            ]
            if touches and not any(point in {start, end} for start, end in touches):
                result.add(point)
        return sorted(result)

    def verify_no_overlapping_nets(self) -> None:
        for index, (net_a, a1, a2) in enumerate(self.segments):
            for net_b, b1, b2 in self.segments[index + 1 :]:
                if net_a == net_b:
                    continue
                a_vertical = abs(a1[0] - a2[0]) < 1e-5
                b_vertical = abs(b1[0] - b2[0]) < 1e-5
                a_horizontal = abs(a1[1] - a2[1]) < 1e-5
                b_horizontal = abs(b1[1] - b2[1]) < 1e-5
                if a_vertical and b_vertical and abs(a1[0] - b1[0]) < 1e-5:
                    overlap = min(max(a1[1], a2[1]), max(b1[1], b2[1])) - max(
                        min(a1[1], a2[1]), min(b1[1], b2[1])
                    )
                    if overlap > 1e-5:
                        raise RuntimeError(
                            f"Overlapping vertical wires on {net_a} and {net_b}: "
                            f"{a1}->{a2}, {b1}->{b2}"
                        )
                if a_horizontal and b_horizontal and abs(a1[1] - b1[1]) < 1e-5:
                    overlap = min(max(a1[0], a2[0]), max(b1[0], b2[0])) - max(
                        min(a1[0], a2[0]), min(b1[0], b2[0])
                    )
                    if overlap > 1e-5:
                        raise RuntimeError(
                            f"Overlapping horizontal wires on {net_a} and {net_b}: "
                            f"{a1}->{a2}, {b1}->{b2}"
                        )

    def verify_net_pins(
        self,
        net: str,
        pin_points: list[tuple[float, float]],
    ) -> None:
        segments = [
            (start, end) for segment_net, start, end in self.segments if segment_net == net
        ]
        missing = [
            point
            for point in pin_points
            if not any(point_on_segment(point, start, end) for start, end in segments)
        ]
        if missing:
            raise RuntimeError(f"{net}: pins not touched by wire: {missing}")


def load_source(path: Path):
    text = path.read_text(encoding="utf-8")
    root = parse_file(path)
    library = child(root, "lib_symbols")
    if library is None:
        raise RuntimeError("Missing lib_symbols")
    pin_sets: dict[str, dict[str, dict]] = {}
    for symbol in children(library, "symbol"):
        lib_id = str(symbol[1])
        pins = {}
        pending = list(children(symbol, "symbol"))
        while pending:
            sub = pending.pop(0)
            pending.extend(children(sub, "symbol"))
            for pin in children(sub, "pin"):
                at = child(pin, "at")
                number_node = child(pin, "number")
                name_node = child(pin, "name")
                if at is None or number_node is None:
                    continue
                number = str(number_node[1])
                pins[number] = {
                    "x": float(at[1]),
                    "y": float(at[2]),
                    "name": str(name_node[1]) if name_node else "",
                }
        pin_sets[lib_id] = pins

    instances = {}
    for symbol in children(root, "symbol"):
        lib_node = child(symbol, "lib_id")
        at = child(symbol, "at")
        if lib_node is None or at is None:
            continue
        ref = property_value(symbol, "Reference")
        instances[ref] = {
            "lib_id": str(lib_node[1]),
            "properties": {
                str(prop[1]): str(prop[2])
                for prop in children(symbol, "property")
                if len(prop) >= 3
            },
            "source_placement": (
                float(at[1]),
                float(at[2]),
                float(at[3]) if len(at) > 3 else 0.0,
            ),
        }
    return text, pin_sets, instances


def property_block(name: str, value: str, x: float, y: float, hide: bool) -> str:
    hidden = "\n\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property {quote(name)} {quote(value)}\n'
        f"\t\t\t(at {fmt(x)} {fmt(y)} 0){hidden}\n"
        "\t\t\t(show_name no)\n"
        "\t\t\t(do_not_autoplace no)\n"
        "\t\t\t(effects\n"
        "\t\t\t\t(font\n"
        "\t\t\t\t\t(size 1.27 1.27)\n"
        "\t\t\t\t)\n"
        "\t\t\t\t(justify left)\n"
        "\t\t\t)\n"
        "\t\t)"
    )


def emit_instance(
    ref: str,
    metadata: dict,
    placement: tuple[float, float, float],
    pins: dict[str, dict],
    root_uuid: str,
) -> str:
    x, y, angle = placement
    properties = metadata["properties"]
    value = properties.get("Value", "?")
    footprint = properties.get("Footprint", "")
    lines = [
        "\t(symbol",
        f"\t\t(lib_id {quote(metadata['lib_id'])})",
        f"\t\t(at {fmt(x)} {fmt(y)} {fmt(angle)})",
        "\t\t(unit 1)",
        "\t\t(body_style 1)",
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom yes)",
        "\t\t(on_board yes)",
        "\t\t(in_pos_files yes)",
        "\t\t(dnp no)",
        f'\t\t(uuid "{stable_uuid("symbol/" + ref)}")',
        property_block("Reference", ref, x - 8.0, y - 10.0, False),
        property_block("Value", value, x - 8.0, y + 11.5, False),
        property_block("Footprint", footprint, x, y, True),
        property_block("Datasheet", properties.get("Datasheet", ""), x, y, True),
        property_block("Description", properties.get("Description", ""), x, y, True),
    ]
    for extra_name in ("MPN", "Manufacturer"):
        if properties.get(extra_name):
            lines.append(property_block(extra_name, properties[extra_name], x, y, True))
    for pin_number in sorted(
        pins, key=lambda item: (0, int(item)) if item.isdigit() else (1, item)
    ):
        lines.extend(
            [
                f"\t\t(pin {quote(pin_number)}",
                f'\t\t\t(uuid "{stable_uuid("pin/" + ref + "/" + pin_number)}")',
                "\t\t)",
            ]
        )
    lines.extend(
        [
            "\t\t(instances",
            '\t\t\t(project "lean-power-readability"',
            f'\t\t\t\t(path "/{root_uuid}"',
            f"\t\t\t\t\t(reference {quote(ref)})",
            "\t\t\t\t\t(unit 1)",
            "\t\t\t\t)",
            "\t\t\t)",
            "\t\t)",
            "\t)",
        ]
    )
    return "\n".join(lines)


def build_routes(pin_points: dict[tuple[str, str], tuple[float, float]]) -> Layout:
    layout = Layout()
    p = lambda ref, pin: pin_points[(ref, pin)]

    # Input and reverse-polarity protection.
    layout.path("VIN_RAW", [p("J1", "1"), p("F1", "1")])
    vin_fused_bus_y = 57.15
    layout.path(
        "VIN_FUSED",
        [(62.23, vin_fused_bus_y), (142.24, vin_fused_bus_y)],
    )
    layout.path(
        "VIN_FUSED",
        [p("F1", "2"), (62.23, 76.20), (62.23, vin_fused_bus_y)],
    )
    for ref, pin in (("Q1", "5"), ("Q1", "6"), ("Q1", "7"), ("Q1", "8")):
        layout.path("VIN_FUSED", [p(ref, pin), (p(ref, pin)[0], vin_fused_bus_y)])
    layout.path("VIN_FUSED", [p("D2", "1"), (142.24, vin_fused_bus_y)])

    q1_sources = [p("Q1", pin) for pin in ("1", "2", "3")]
    layout.path("VIN_PROT", [q1_sources[0], q1_sources[-1]])
    layout.path("VIN_PROT", [(q1_sources[1][0], q1_sources[1][1]), (119.38, 91.44)])
    layout.path("VIN_PROT", [(119.38, 91.44), (205.74, 91.44)])
    for ref in ("C3", "C4", "C5"):
        point = p(ref, "1")
        layout.path("VIN_PROT", [point, (point[0], 91.44)])
    layout.path("VIN_PROT", [p("U1", "2"), (205.74, 91.44)])
    layout.path("VIN_PROT", [p("U1", "3"), (205.74, 91.44)])

    layout.path(
        "Q1_GATE",
        [p("D2", "2"), (142.24, 76.20), p("Q1", "4")],
    )
    layout.path("Q1_GATE", [(111.76, 76.20), p("R1", "1")])

    # Buck controller, switch node, and bootstrap capacitor.
    layout.path(
        "BUCK5_SW",
        [
            p("U1", "8"),
            (231.14, 92.71),
            (231.14, 80.01),
            p("C86", "2"),
            (246.38, 80.01),
            (246.38, 71.12),
            p("L1", "1"),
        ],
    )
    layout.path(
        "BUCK5_BST",
        [
            p("U1", "7"),
            (234.95, 90.17),
            (234.95, 72.39),
            p("C86", "1"),
        ],
    )
    layout.path(
        "VCC5",
        [
            p("U1", "6"),
            (201.93, 100.33),
            (201.93, 110.49),
            (195.58, 110.49),
            p("C91", "1"),
        ],
    )

    # +5 V rail.
    red_5v_bus_y = 63.50
    layout.path(
        "+5V",
        [
            (p("L1", "2")[0], red_5v_bus_y),
            (p("R4", "1")[0], red_5v_bus_y),
        ],
    )
    layout.path("+5V", [p("L1", "2"), (257.81, red_5v_bus_y)])
    for ref in ("C6", "C7", "C10", "C11", "C76"):
        point = p(ref, "1")
        layout.path("+5V", [point, (point[0], red_5v_bus_y)])
    layout.path("+5V", [p("R70", "1"), (370.84, red_5v_bus_y)])
    layout.path(
        "+5V",
        [
            p("U2", "3"),
            (p("U2", "3")[0], red_5v_bus_y),
        ],
    )
    layout.path(
        "+5V",
        [p("R4", "1"), (p("R4", "1")[0], red_5v_bus_y)],
    )
    layout.path("+5V", [(340.36, red_5v_bus_y), p("FLG2", "1")])

    # Feedback divider and power-good pull-up.
    layout.path("FB5_TOP", [p("R70", "2"), p("R71", "1")])
    layout.path("FB5", [p("R71", "2"), p("R72", "1")])
    layout.path(
        "FB5",
        [
            p("U1", "5"),
            (350.00, 97.79),
            (350.00, 114.30),
            (370.84, 114.30),
        ],
    )
    layout.path(
        "PWR_GOOD_N",
        [
            p("U1", "4"),
            (226.06, 115.57),
            (350.00, 115.57),
            (350.00, 129.54),
            p("R73", "1"),
        ],
    )

    # +3V3 point-of-load rail, ferrite-filtered analog rail, and status LEDs.
    layout.path(
        "+3V3",
        [
            (p("R73", "2")[0], 105.41),
            (p("FB1", "1")[0], 105.41),
        ],
    )
    layout.path("+3V3", [p("R73", "2"), (365.76, 121.92), (365.76, 105.41)])
    layout.path(
        "+3V3",
        [
            p("U2", "2"),
            (p("U2", "2")[0], 105.41),
        ],
    )
    for ref in ("C13", "C90"):
        point = p(ref, "1")
        layout.path("+3V3", [point, (point[0], 105.41)])
    layout.path(
        "+3V3",
        [p("R5", "1"), (451.19, 165.10), (451.19, 105.41)],
    )
    layout.path("+3V3_A", [p("FB1", "2"), p("FLG3", "1")])
    layout.path(
        "+3V3_A",
        [p("C15", "1"), (p("C15", "1")[0], 105.41)],
    )

    # Status LEDs.
    layout.path(
        "PWR5_LEDA",
        [p("R4", "2"), p("D4", "2")],
    )
    layout.path(
        "PWR3_LEDA",
        [p("R5", "2"), p("D5", "2")],
    )

    # One explicit ground bus makes the return path visually obvious.
    ground_y = 135.00
    layout.path("GND", [(25.40, ground_y), (530.20, ground_y)])
    ground_pins = [
        ("C1", "2"),
        ("C2", "2"),
        ("D1", "2"),
        ("R1", "2"),
        ("C3", "2"),
        ("C4", "2"),
        ("C5", "2"),
        ("U1", "1"),
        ("U1", "9"),
        ("C91", "2"),
        ("C6", "2"),
        ("C7", "2"),
        ("C10", "2"),
        ("C11", "2"),
        ("C76", "2"),
        ("C13", "2"),
        ("C90", "2"),
        ("C15", "2"),
        ("R72", "2"),
        ("D4", "1"),
        ("D5", "1"),
    ]
    for ref, pin in ground_pins:
        point = p(ref, pin)
        layout.path("GND", [point, (point[0], ground_y)])
    # The connector's two pins share an X coordinate; leave the pin row before
    # descending so the ground lead cannot overlap VIN_RAW.
    layout.path(
        "GND",
        [p("J1", "2"), (33.02, 73.66), (33.02, ground_y)],
    )
    # Route U2 ground to the left of the +3V3 bus before descending.
    layout.path(
        "GND",
        [
            p("U2", "1"),
            (p("U2", "1")[0] - 30.48, 102.87),
            (p("U2", "1")[0] - 30.48, ground_y),
        ],
    )
    layout.path("GND", [p("FLG1", "1"), (530.20, ground_y)])

    # Single-node off-sheet rails are represented by their own flag and label.
    for ref in ("FLG5", "FLG6", "FLG7", "FLG8"):
        point = p(ref, "1")
        layout.labels[source_net_for_pin(ref, "1")] = (point[0], point[1], 0)

    return layout


def source_net_for_pin(ref: str, pin: str) -> str:
    contract_path = SOURCE_DIR / "source-pin-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    return contract[ref][pin]


SOURCE_DIR = Path("experiments/power-schematic-readability/inputs")
GRID = 1.27


def snap(value: float) -> float:
    return round(round(value / GRID) * GRID, 4)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("hardware/power.kicad_sch")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/power-schematic-readability/method-b/lean-power-b.kicad_sch"),
    )
    args = parser.parse_args()

    source_text, pin_sets, instances = load_source(args.source)
    if set(instances) != set(PLACEMENTS):
        missing = sorted(set(instances) - set(PLACEMENTS))
        extra = sorted(set(PLACEMENTS) - set(instances))
        raise RuntimeError(f"Placement mismatch; missing={missing}, extra={extra}")

    pin_points = {}
    placements = {
        ref: (snap(x), snap(y), angle) for ref, (x, y, angle) in PLACEMENTS.items()
    }
    for ref, metadata in instances.items():
        x, y, angle = placements[ref]
        for number, pin in pin_sets[metadata["lib_id"]].items():
            pin_points[(ref, number)] = world_pin(x, y, angle, pin["x"], pin["y"])

    contract = json.loads((SOURCE_DIR / "source-pin-contract.json").read_text())
    wires = build_routes(pin_points)
    pins_by_net: dict[str, list[tuple[float, float]]] = defaultdict(list)
    pin_nets = {}
    for ref, pin_map in contract.items():
        for pin, net in pin_map.items():
            pins_by_net[net].append(pin_points[(ref, pin)])
            pin_nets[(ref, pin)] = net
    for net, points in pins_by_net.items():
        if len(points) == 1 and net in wires.labels:
            label_x, label_y, _ = wires.labels[net]
            if (round(label_x, 4), round(label_y, 4)) == points[0]:
                continue
        wires.verify_net_pins(net, points)
    wires.verify_no_overlapping_nets()
    junctions = sorted(set(wires.junctions()) | set(wires.pin_junctions(pin_points, pin_nets)))

    lib_symbols = extract_block(source_text, "lib_symbols")
    root_uuid = stable_uuid("root")
    output = [
        "(kicad_sch",
        "\t(version 20260306)",
        '\t(generator "eeschema")',
        '\t(generator_version "10.0")',
        f'\t(uuid "{root_uuid}")',
        '\t(paper "A2")',
        "\t(title_block",
        '\t\t(title "LeanCam NCC RP2350B - Power and Supervision (Python re-layout)")',
        '\t\t(date "2026-10-29")',
        '\t\t(company "LeanCam / uCNC experiment")',
        '\t\t(comment 1 "Method B: existing symbols, explicit orthogonal wiring")',
        "\t)",
        lib_symbols,
    ]
    for title, x, y in TITLES:
        output.extend(
            [
                f"\t(text {quote(title)}",
                "\t\t(exclude_from_sim no)",
                f"\t\t(at {fmt(x)} {fmt(y)} 0)",
                "\t\t(effects",
                "\t\t\t(font",
                "\t\t\t\t(size 2 2)",
                "\t\t\t\t(thickness 0.4)",
                "\t\t\t\t(bold yes)",
                "\t\t\t\t(color 46 91 145 1)",
                "\t\t\t)",
                "\t\t\t(justify left)",
                "\t\t)",
                f'\t\t(uuid "{stable_uuid("title/" + title)}")',
                "\t)",
            ]
        )
    output.extend(
        [
            "\t(text \"Power flow: 24 V input  ->  fused/protected VIN  ->  5 V buck  ->  3V3 LDO\"",
            "\t\t(exclude_from_sim no)",
            "\t\t(at 22.86 30.48 0)",
            "\t\t(effects",
            "\t\t\t(font",
            "\t\t\t\t(size 1.5 1.5)",
            "\t\t\t\t(color 70 70 70 1)",
            "\t\t\t)",
            "\t\t\t(justify left)",
            "\t\t)",
            f'\t\t(uuid "{stable_uuid("flow-note")}")',
            "\t)",
        ]
    )

    for net, start, end in wires.segments:
        output.extend(
            [
                "\t(wire",
                f"\t\t(pts (xy {fmt(start[0])} {fmt(start[1])}) (xy {fmt(end[0])} {fmt(end[1])}))",
                "\t\t(stroke (width 0) (type default))",
                f'\t\t(uuid "{stable_uuid("wire/" + net + "/" + repr((start, end)))}")',
                "\t)",
            ]
        )
    for point in junctions:
        output.extend(
            [
                f"\t(junction (at {fmt(point[0])} {fmt(point[1])})",
                "\t\t(diameter 0)",
                "\t\t(color 0 0 0 0)",
                f'\t\t(uuid "{stable_uuid("junction/" + repr(point))}")',
                "\t)",
            ]
        )
    for net, (x, y, angle) in sorted(wires.labels.items()):
        output.extend(
            [
                f"\t(label {quote(net)}",
                f"\t\t(at {fmt(x)} {fmt(y)} {fmt(angle)})",
                "\t\t(effects",
                "\t\t\t(font (size 1.27 1.27))",
                "\t\t\t(justify left)",
                "\t\t)",
                f'\t\t(uuid "{stable_uuid("label/" + net)}")',
                "\t)",
            ]
        )
    for ref in sorted(instances):
        metadata = instances[ref]
        lib_id = metadata["lib_id"]
        output.append(
            emit_instance(
                ref,
                metadata,
                placements[ref],
                pin_sets[lib_id],
                root_uuid,
            )
        )
    output.extend(
        [
            "\t(sheet_instances",
            '\t\t(path "/" (page "1"))',
            "\t)",
            ")",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "components": len(instances),
                "wire_segments": len(wires.segments),
                "junctions": len(junctions),
                "labels": len(wires.labels),
                "pin_endpoints_checked": len(pin_points),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
