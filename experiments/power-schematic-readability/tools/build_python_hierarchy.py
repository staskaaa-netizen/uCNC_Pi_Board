"""Generate symbol-preserving Python re-layouts for the remaining hierarchy.

The tool groups components into functional blocks, routes short local nets with
orthogonal wires, and falls back to named labels for single-pin, cross-block and
high-fanout nets. Source schematics and the PCB are read-only inputs.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from build_python_power_schematic import (
    emit_instance,
    load_source,
    property_block,
    stable_uuid,
    world_pin,
)
from kicad_sexpr import child, children, extract_block, fmt, quote


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = ROOT / "experiments" / "power-schematic-readability"
INPUTS = EXPERIMENT / "inputs"
HARDWARE = ROOT / "hardware"
OUTPUT = EXPERIMENT / "other-sheets"
GRID = 1.27

PAPERS = {
    "A3": (420.0, 297.0),
    "A2": (594.0, 420.0),
    "A1": (841.0, 594.0),
    "A0": (1189.0, 841.0),
}


@dataclass(frozen=True)
class Block:
    title: str
    refs: tuple[str, ...]
    columns: int = 8


@dataclass(frozen=True)
class Sheet:
    stem: str
    source: str
    title: str
    paper: str
    blocks: tuple[Block, ...]


def rng(start: int, end: int, prefix: str = "R") -> tuple[str, ...]:
    return tuple(f"{prefix}{index}" for index in range(start, end + 1))


SHEETS = {
    "display": Sheet(
        stem="display",
        source="display.kicad_sch",
        title="LVDS display interface",
        paper="A3",
        blocks=(
            Block(
                "LVDS TRANSMITTER AND CONNECTOR",
                ("U41", "RN26", "RN27", "J22", "C106"),
                columns=5,
            ),
        ),
    ),
    "encoders": Sheet(
        stem="encoders",
        source="encoders.kicad_sch",
        title="Encoder receiver and 5 V protection",
        paper="A3",
        blocks=(
            Block(
                "ENCODER INPUTS 0-2",
                ("F2", "D53", "C57", "U28", "J13", "J14", "J15", "R110", "R111"),
                columns=5,
            ),
        ),
    ),
    "storage_wifi_ui": Sheet(
        stem="storage_wifi_ui",
        source="storage_wifi_ui.kicad_sch",
        title="Storage, Wi-Fi, keyboard and service interfaces",
        paper="A2",
        blocks=(
            Block("KEYBOARD MATRIX INTERFACE", ("J16", "J17", "RN22", "RN24"), columns=4),
            Block(
                "MICRO SD INTERFACE",
                (
                    "J19",
                    *rng(44, 54),
                    "C67",
                    "C68",
                    "FB2",
                ),
                columns=8,
            ),
            Block(
                "ESP-01 / ESP-01S SOCKET",
                (
                    "U34",
                    "J20",
                    "SW2",
                    *rng(55, 58),
                    "C69",
                    "C70",
                    "C88",
                    "C89",
                ),
                columns=8,
            ),
            Block("I2C SERVICE PORT", ("J18",), columns=1),
        ),
    ),
    "analog_io": Sheet(
        stem="analog_io",
        source="analog_io.kicad_sch",
        title="Analog inputs and filtered 0-10 V outputs",
        paper="A1",
        blocks=(
            Block(
                "ANALOG INPUTS AI0-AI2",
                (
                    "J24",
                    "R61",
                    "C73",
                    "R63",
                    "R64",
                    "C74",
                    "R66",
                    "R67",
                    "C75",
                    "R69",
                ),
                columns=4,
            ),
            Block(
                "ANALOG OUTPUTS AO0-AO3",
                (
                    "U38",
                    "J25",
                    *tuple(
                        ref
                        for index in range(4)
                        for ref in (
                            f"R{100 + index}",
                            f"R{92 + index}",
                            f"R{96 + index}",
                            f"C{92 + 2 * index}",
                            f"C{93 + 2 * index}",
                            f"R{104 + index}",
                        )
                    ),
                ),
                columns=6,
            ),
            Block("ANALOG 12 V SUPPLY", ("U37", "C100", "C101", "C102"), columns=4),
        ),
    ),
    "mcu_io": Sheet(
        stem="mcu_io",
        source="mcu_io.kicad_sch",
        title="RP2350B module, shift-register chains and safety I/O",
        paper="A2",
        blocks=(
            Block(
                "WeAct RP2350B AND DECOUPLING",
                ("MOD1", "J4", *rng(22, 29, "C")),
                columns=5,
            ),
            Block(
                "74HC165 / 74HC595 CHAINS",
                (*rng(6, 9, "U"), *rng(10, 13, "U"), *rng(9, 13)),
                columns=9,
            ),
        ),
    ),
    "field_outputs": Sheet(
        stem="field_outputs",
        source="field_outputs.kicad_sch",
        title="PLC outputs, motion outputs and auxiliary drivers",
        paper="A1",
        blocks=(
            Block(
                "5 V OUTPUT BUFFERS",
                (
                    "U24",
                    "U25",
                    "RN8",
                    "RN9",
                    "RN10",
                    "RN11",
                    "C53",
                    "C54",
                ),
                columns=8,
            ),
            Block(
                "GENERAL AND MOTION OUTPUTS",
                (
                    "U26",
                    "U27",
                    "RN12",
                    "RN13",
                    "RN16",
                    "RN17",
                    "RN18",
                    "RN19",
                    "J10",
                    "J11",
                    "J12",
                    "J28",
                    "J29",
                    "J30",
                    "J32",
                    "J33",
                    "C55",
                    "C56",
                    *tuple(
                        ref
                        for index in range(8)
                        for ref in (f"D{45 + index}", f"R{34 + index}")
                    ),
                    *tuple(
                        ref
                        for index in range(6)
                        for ref in (f"D{57 + index}", f"R{118 + index}")
                    ),
                    "D63",
                    "R124",
                    "D64",
                    "R125",
                ),
                columns=10,
            ),
            Block(
                "AUXILIARY AND HIGH-CURRENT OUTPUTS",
                (
                    "Q5",
                    "Q6",
                    "Q7",
                    "R113",
                    "R114",
                    "R115",
                    "R116",
                    "R117",
                    "RN20",
                    "RN21",
                    "RN30",
                    "RN31",
                    "J31",
                ),
                columns=8,
            ),
        ),
    ),
}


FIELD_INPUT_BANK_1 = (
    "J8",
    "J35",
    "JP2",
    "U18",
    "U19",
    *tuple(
        ref
        for index in range(1, 9)
        for ref in (
            f"R{17 + index}",
            f"D{11 + 2 * index}",
            f"D{12 + 2 * index}",
            f"R{75 + index}",
        )
    ),
)
FIELD_INPUT_BANK_2 = (
    "J7",
    "J34",
    "JP3",
    "U20",
    "U21",
    *tuple(
        ref
        for index in range(9, 17)
        for ref in (
            f"R{17 + index}",
            f"D{11 + 2 * index}",
            f"D{12 + 2 * index}",
            f"R{75 + index}",
        )
    ),
)
SHEETS["field_inputs"] = Sheet(
    stem="field_inputs",
    source="field_inputs.kicad_sch",
    title="Isolated PLC inputs and safety inputs",
    paper="A0",
    blocks=(
        Block("ISOLATED 5 V-TO-12 V SUPPLY", ("F4", "U40", "C103", "C105", "D56"), columns=5),
        Block("EXPANSION INPUTS 0-7", ("J9", "J27", "RN6", "RN7"), columns=4),
        Block(
            "SAFETY INPUTS",
            (
                "J5",
                "J6",
                "J26",
                "JP4",
                "U35",
                "U36",
                "U39",
                "D9",
                "D10",
                "D11",
                "D12",
                "D54",
                "D55",
                "R16",
                "R17",
                "R74",
                "R75",
                "R108",
                "R109",
            ),
            columns=8,
        ),
        Block("ISOLATED PLC INPUTS 1-8", FIELD_INPUT_BANK_1, columns=12),
        Block("ISOLATED PLC INPUTS 9-16", FIELD_INPUT_BANK_2, columns=12),
    ),
)


def snap(value: float) -> float:
    return round(round(value / GRID) * GRID, 4)


def collect_geometry(node: list, points: list[tuple[float, float]]) -> None:
    for item in node:
        if not isinstance(item, list) or not item:
            continue
        head = item[0]
        if head in {"rectangle", "start", "end"}:
            if head == "rectangle":
                collect_geometry(item, points)
            elif len(item) >= 3:
                try:
                    points.append((float(item[1]), float(item[2])))
                except (TypeError, ValueError):
                    pass
        elif head == "polyline":
            pts = child(item, "pts")
            if pts:
                for xy in children(pts, "xy"):
                    points.append((float(xy[1]), float(xy[2])))
        elif head == "circle":
            center = child(item, "center")
            radius = child(item, "radius")
            if center and radius:
                cx, cy, r = float(center[1]), float(center[2]), float(radius[1])
                points.extend([(cx - r, cy - r), (cx + r, cy + r)])
        elif head == "arc":
            start = child(item, "start")
            end = child(item, "end")
            if start:
                points.append((float(start[1]), float(start[2])))
            if end:
                points.append((float(end[1]), float(end[2])))
        elif head == "pin":
            at = child(item, "at")
            if at:
                points.append((float(at[1]), float(at[2])))
        elif head == "symbol":
            collect_geometry(item[1:], points)


def symbol_bboxes(source_root: list) -> dict[str, tuple[float, float, float, float]]:
    result = {}
    library = child(source_root, "lib_symbols")
    if library is None:
        raise RuntimeError("Missing lib_symbols")
    for symbol in children(library, "symbol"):
        points: list[tuple[float, float]] = []
        collect_geometry(symbol[1:], points)
        if not points:
            points = [(-6.35, -6.35), (6.35, 6.35)]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        width = max(12.7, max(xs) - min(xs) + 5.08)
        height = max(12.7, max(ys) - min(ys) + 5.08)
        result[str(symbol[1])] = (-width / 2, -height / 2, width, height)
    return result


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
    return False


def segment_intersects_rect(
    start: tuple[float, float],
    end: tuple[float, float],
    rect: tuple[float, float, float, float],
) -> bool:
    x1, y1 = start
    x2, y2 = end
    left, top, width, height = rect
    right, bottom = left + width, top + height
    if abs(y1 - y2) < 1e-5:
        return top <= y1 <= bottom and not (max(x1, x2) < left or min(x1, x2) > right)
    if abs(x1 - x2) < 1e-5:
        return left <= x1 <= right and not (max(y1, y2) < top or min(y1, y2) > bottom)
    return True


def crossing_count(
    start: tuple[float, float],
    end: tuple[float, float],
    segments: list[tuple[str, tuple[float, float], tuple[float, float]]],
) -> int:
    count = 0
    for _net, s2, e2 in segments:
        if segment_intersects_rect(start, end, (s2[0], s2[1], 0.0001, 0.0001)):
            continue
        if abs(start[0] - end[0]) < 1e-5:
            x = start[0]
            if min(s2[0], e2[0]) <= x <= max(s2[0], e2[0]):
                y = s2[1]
                if min(start[1], end[1]) <= y <= max(start[1], end[1]):
                    count += 1
        else:
            y = start[1]
            if min(s2[1], e2[1]) <= y <= max(s2[1], e2[1]):
                x = s2[0]
                if min(start[0], end[0]) <= x <= max(start[0], end[0]):
                    count += 1
    return count


def candidate_paths(
    start: tuple[float, float], end: tuple[float, float]
) -> list[list[tuple[float, float]]]:
    start = (snap(start[0]), snap(start[1]))
    end = (snap(end[0]), snap(end[1]))
    if start == end:
        return []
    paths = []
    if abs(start[0] - end[0]) < 1e-5 or abs(start[1] - end[1]) < 1e-5:
        paths.append([start, end])
    paths.extend(
        [
            [start, (end[0], start[1]), end],
            [start, (start[0], end[1]), end],
        ]
    )
    for fraction in (0.25, 0.5, 0.75):
        x_mid = snap(start[0] + (end[0] - start[0]) * fraction)
        y_mid = snap(start[1] + (end[1] - start[1]) * fraction)
        paths.append([start, (x_mid, start[1]), (x_mid, end[1]), end])
        paths.append([start, (start[0], y_mid), (end[0], y_mid), end])
    unique = []
    seen = set()
    for path in paths:
        compact = [path[0]]
        for point in path[1:]:
            if point != compact[-1]:
                compact.append(point)
        key = tuple(compact)
        if len(compact) >= 2 and key not in seen:
            seen.add(key)
            unique.append(compact)
    return unique


class Router:
    def __init__(
        self,
        pin_points: dict[tuple[str, str], tuple[float, float]],
        pin_bboxes: dict[tuple[str, str], tuple[float, float, float, float]],
        block_by_ref: dict[str, str],
        bounds: tuple[float, float, float, float],
    ) -> None:
        self.pin_points = pin_points
        self.pin_bboxes = pin_bboxes
        self.block_by_ref = block_by_ref
        self.bounds = bounds
        self.segments: list[tuple[str, tuple[float, float], tuple[float, float]]] = []
        self.labels: dict[str, list[tuple[float, float, int]]] = {}

    def path_is_safe(
        self,
        net: str,
        path: list[tuple[float, float]],
        own_pins: set[tuple[str, str]],
    ) -> bool:
        x_min, y_min, x_max, y_max = self.bounds
        for point in path:
            if not (x_min <= point[0] <= x_max and y_min <= point[1] <= y_max):
                return False
        for start, end in zip(path, path[1:]):
            for pin_key, pin in self.pin_points.items():
                if pin_key in own_pins:
                    continue
                if point_on_segment(pin, start, end):
                    return False
            for other_net, o_start, o_end in self.segments:
                if other_net == net:
                    continue
                same_vertical = (
                    abs(start[0] - end[0]) < 1e-5
                    and abs(o_start[0] - o_end[0]) < 1e-5
                    and abs(start[0] - o_start[0]) < 1e-5
                )
                same_horizontal = (
                    abs(start[1] - end[1]) < 1e-5
                    and abs(o_start[1] - o_end[1]) < 1e-5
                    and abs(start[1] - o_start[1]) < 1e-5
                )
                if same_vertical:
                    overlap = min(max(start[1], end[1]), max(o_start[1], o_end[1])) - max(
                        min(start[1], end[1]), min(o_start[1], o_end[1])
                    )
                    if overlap > 1e-5:
                        return False
                if same_horizontal:
                    overlap = min(max(start[0], end[0]), max(o_start[0], o_end[0])) - max(
                        min(start[0], end[0]), min(o_start[0], o_end[0])
                    )
                    if overlap > 1e-5:
                        return False
                if point_on_segment(start, o_start, o_end) or point_on_segment(
                    end, o_start, o_end
                ):
                    return False
                if point_on_segment(o_start, start, end) or point_on_segment(
                    o_end, start, end
                ):
                    return False
        return True

    def score_path(
        self,
        net: str,
        path: list[tuple[float, float]],
        own_pins: set[tuple[str, str]],
    ) -> float:
        score = 0.0
        for start, end in zip(path, path[1:]):
            score += abs(end[0] - start[0]) + abs(end[1] - start[1])
            score += crossing_count(start, end, self.segments) * 4.0
            for pin_key, rect in self.pin_bboxes.items():
                if pin_key in own_pins:
                    continue
                if segment_intersects_rect(start, end, rect):
                    score += 25.0
        score += max(0, len(path) - 2) * 2.0
        return score

    def attempt_net(
        self,
        net: str,
        pin_keys: list[tuple[str, str]],
    ) -> tuple[list[tuple[str, tuple[float, float], tuple[float, float]]], list] | None:
        blocks = {self.block_by_ref.get(ref) for ref, _pin in pin_keys}
        if len(blocks) != 1 or len(pin_keys) < 2 or len(pin_keys) > 4:
            return None
        own_pins = set(pin_keys)
        points = [self.pin_points[key] for key in pin_keys]
        candidates = sorted(points, key=lambda point: (point[1], point[0]))
        temp_segments = []
        tree_nodes = set()
        first = candidates[0]
        tree_nodes.add(first)
        for end in candidates[1:]:
            best = None
            targets = list(tree_nodes)
            for _net, start, finish in temp_segments:
                if abs(start[0] - finish[0]) < 1e-5:
                    if min(start[1], finish[1]) <= end[1] <= max(start[1], finish[1]):
                        targets.append((start[0], end[1]))
                elif abs(start[1] - finish[1]) < 1e-5:
                    if min(start[0], finish[0]) <= end[0] <= max(start[0], finish[0]):
                        targets.append((end[0], start[1]))
            for target in targets:
                for path in candidate_paths(end, target):
                    local_segments = [
                        (net, first_point, second_point)
                        for first_point, second_point in zip(path, path[1:])
                    ]
                    if not self.path_is_safe(net, path, own_pins):
                        continue
                    score = self.score_path(net, path, own_pins)
                    if best is None or score < best[0]:
                        best = (score, path, local_segments)
            if best is None:
                return None
            _, path, local_segments = best
            temp_segments.extend(local_segments)
            tree_nodes.update(path)
        return temp_segments, sorted(tree_nodes)

    def route(self, nets: list[dict]) -> tuple[list, list]:
        routed = []
        junctions = set()
        ordered = sorted(nets, key=lambda net: (len(net["connections"]), net["name"]))
        for source_net in ordered:
            name = source_net["name"]
            pin_keys = [
                (str(ref), str(pin)) for ref, pin in source_net["connections"]
            ]
            result = self.attempt_net(name, pin_keys)
            if result is None:
                for ref, pin in pin_keys:
                    point = self.pin_points[(ref, pin)]
                    self.labels.setdefault(name, []).append(
                        (point[0], point[1], 0)
                    )
                continue
            local_segments, _nodes = result
            self.segments.extend(local_segments)
            first = pin_keys[0]
            x, y = self.pin_points[first]
            self.labels.setdefault(name, []).append((x, y, 0))
            routed.append(name)

        # Mark every T-joint and same-net wire intersection.
        endpoints = defaultdict(int)
        for _net, start, end in self.segments:
            endpoints[start] += 1
            endpoints[end] += 1
        for point, count in endpoints.items():
            touching = sum(
                1
                for _net, start, end in self.segments
                if point_on_segment(point, start, end)
            )
            if count >= 3 or (count >= 1 and touching > count):
                junctions.add(point)
        return routed, sorted(junctions)


def place_blocks(
    sheet: Sheet,
    instances: dict,
    pin_sets: dict,
    bboxes: dict,
) -> tuple[dict[str, tuple[float, float, float]], list[tuple[str, float, float, float, float]], dict[str, str], float]:
    page_width, page_height = PAPERS[sheet.paper]
    left_margin, right_margin, top_margin = 20.0, 20.0, 25.0
    available_width = page_width - left_margin - right_margin
    placements = {}
    block_boxes = []
    block_by_ref = {}
    y = top_margin
    for block in sheet.blocks:
        x_cursor = left_margin + 5
        row_y = y + 12
        row_height = 0.0
        block_top = y
        block_placements = {}
        max_right = x_cursor
        row_items = 0
        for ref in block.refs:
            lib_id = instances[ref]["lib_id"]
            _bx, _by, width, height = bboxes[lib_id]
            cell_width = max(32.0, width + 12.0)
            cell_height = max(32.0, height + 16.0)
            if (
                row_items >= block.columns
                or x_cursor + cell_width > left_margin + available_width - 5
            ):
                row_y += row_height + 7
                x_cursor = left_margin + 5
                row_height = 0.0
                row_items = 0
            center_x = snap(x_cursor + cell_width / 2)
            center_y = snap(row_y + cell_height / 2)
            block_placements[ref] = (center_x, center_y, 0.0)
            block_by_ref[ref] = block.title
            x_cursor += cell_width
            row_items += 1
            max_right = max(max_right, x_cursor)
            row_height = max(row_height, cell_height)
        used_width = max_right - (left_margin + 5)
        shift_x = snap(max(0.0, (available_width - used_width) / 2))
        for ref, (center_x, center_y, angle) in block_placements.items():
            placements[ref] = (snap(center_x + shift_x), center_y, angle)
        block_height = row_y + row_height - block_top + 7
        block_boxes.append(
            (
                block.title,
                left_margin + shift_x,
                block_top + 2,
                used_width,
                block_height,
            )
        )
        y += block_height + 8
    if y > page_height - 10:
        raise RuntimeError(
            f"{sheet.stem}: content height {y:.1f} mm exceeds {sheet.paper}"
        )
    return placements, block_boxes, block_by_ref, y


def emit_text(title: str, x: float, y: float, size: float, key: str) -> list[str]:
    return [
        f"\t(text {quote(title)}",
        "\t\t(exclude_from_sim no)",
        f"\t\t(at {fmt(x)} {fmt(y)} 0)",
        "\t\t(effects",
        "\t\t\t(font",
        f"\t\t\t\t(size {fmt(size)} {fmt(size)})",
        f"\t\t\t\t(thickness {fmt(0.3 if size >= 1.8 else 0.2)})",
        "\t\t\t\t(bold yes)",
        "\t\t\t\t(color 46 91 145 1)",
        "\t\t\t)",
        "\t\t\t(justify left)",
        "\t\t)",
        f'\t\t(uuid "{stable_uuid("hierarchy-title/" + key)}")',
        "\t)",
    ]


def build_sheet(sheet: Sheet, force: bool = False) -> dict:
    source_path = HARDWARE / sheet.source
    design_path = INPUTS / f"source-{sheet.stem}.json"
    contract_path = INPUTS / f"source-{sheet.stem}-pin-contract.json"
    output_path = OUTPUT / f"{sheet.stem}-python.kicad_sch"
    source_text, pin_sets, instances = load_source(source_path)
    source_root = __import__("kicad_sexpr").parse_file(source_path)
    bboxes = symbol_bboxes(source_root)
    design = json.loads(design_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    planned_refs = [ref for block in sheet.blocks for ref in block.refs]
    if len(planned_refs) != len(set(planned_refs)):
        raise RuntimeError(f"{sheet.stem}: duplicate refs in block definitions")
    if set(planned_refs) != set(instances):
        missing = sorted(set(instances) - set(planned_refs))
        extra = sorted(set(planned_refs) - set(instances))
        raise RuntimeError(
            f"{sheet.stem}: block coverage mismatch; missing={missing}, extra={extra}"
        )

    placements, block_boxes, block_by_ref, content_bottom = place_blocks(
        sheet, instances, pin_sets, bboxes
    )
    pin_points = {}
    for ref, metadata in instances.items():
        x, y, angle = placements[ref]
        for number, pin in pin_sets[metadata["lib_id"]].items():
            pin_points[(ref, number)] = world_pin(x, y, angle, pin["x"], pin["y"])

    pin_to_net = {}
    for ref, pins in contract.items():
        for pin, net in pins.items():
            pin_to_net[(ref, pin)] = net
    pin_bboxes = {}
    for (ref, pin), point in pin_points.items():
        pin_bboxes[(ref, pin)] = (point[0] - 1.27, point[1] - 1.27, 2.54, 2.54)

    page_width, page_height = PAPERS[sheet.paper]
    router = Router(
        pin_points,
        pin_bboxes,
        block_by_ref,
        (15.0, 15.0, page_width - 15.0, page_height - 15.0),
    )
    routed_nets, junctions = router.route(design["nets"])

    # Single-node nets and any high-fanout/cross-block net get one pin label.
    for net in design["nets"]:
        if net["name"] in router.labels:
            continue
        for ref, pin in net["connections"]:
            x, y = pin_points[(str(ref), str(pin))]
            router.labels.setdefault(net["name"], []).append((x, y, 0))

    root_uuid = stable_uuid(f"hierarchy/{sheet.stem}/root")
    library = extract_block(source_text, "lib_symbols")
    output = [
        "(kicad_sch",
        "\t(version 20260306)",
        '\t(generator "eeschema")',
        '\t(generator_version "10.0")',
        f'\t(uuid "{root_uuid}")',
        f'\t(paper "{sheet.paper}")',
        "\t(title_block",
        f"\t\t(title {quote(sheet.title)})",
        '\t\t(date "2026-10-29")',
        '\t\t(company "LeanCam / uCNC Python hierarchy experiment")',
        '\t\t(comment 1 "Existing symbols grouped by function; local nets routed where practical")',
        "\t)",
        library,
    ]
    output.extend(
        emit_text(
            f"{sheet.title}  |  {len(instances)} components  |  {len(design['nets'])} local nets",
            20.0,
            16.0,
            2.0,
            "sheet-title",
        )
    )
    for title, x, y, width, height in block_boxes:
        output.extend(
            [
                f"\t(rectangle (start {fmt(x)} {fmt(y)}) "
                f"(end {fmt(x + width)} {fmt(y + height)})",
                "\t\t(stroke (width 0.2) (type dash) (color 62 110 165 1))",
                "\t\t(fill (type none))",
                f'\t\t(uuid "{stable_uuid("hierarchy-block/" + sheet.stem + "/" + title)}")',
                "\t)",
            ]
        )
        output.extend(
            emit_text(
                title,
                x + 2.0,
                y + 6.0,
                1.7,
                f"block-title/{sheet.stem}/{title}",
            )
        )

    for net, start, end in router.segments:
        output.extend(
            [
                "\t(wire",
                f"\t\t(pts (xy {fmt(start[0])} {fmt(start[1])}) "
                f"(xy {fmt(end[0])} {fmt(end[1])}))",
                "\t\t(stroke (width 0) (type default))",
                f'\t\t(uuid "{stable_uuid("hierarchy-wire/" + sheet.stem + "/" + net + "/" + repr((start, end)))}")',
                "\t)",
            ]
        )
    for point in junctions:
        output.extend(
            [
                f"\t(junction (at {fmt(point[0])} {fmt(point[1])})",
                "\t\t(diameter 0)",
                "\t\t(color 0 0 0 0)",
                f'\t\t(uuid "{stable_uuid("hierarchy-junction/" + sheet.stem + "/" + repr(point))}")',
                "\t)",
            ]
        )
    for net, positions in sorted(router.labels.items()):
        for index, (x, y, angle) in enumerate(positions):
            output.extend(
                [
                    f"\t(label {quote(net)}",
                    f"\t\t(at {fmt(x)} {fmt(y)} {angle})",
                    "\t\t(effects",
                    "\t\t\t(font (size 1.27 1.27))",
                    "\t\t\t(justify left)",
                    "\t\t)",
                    f'\t\t(uuid "{stable_uuid("hierarchy-label/" + sheet.stem + "/" + net + "/" + str(index))}")',
                    "\t)",
                ]
            )

    unconnected = []
    for ref, metadata in instances.items():
        for pin in pin_sets[metadata["lib_id"]]:
            if (ref, pin) not in pin_to_net:
                unconnected.append((ref, pin, pin_points[(ref, pin)]))
    for _ref, _pin, point in unconnected:
        output.append(
            f'\t(no_connect (at {fmt(point[0])} {fmt(point[1])}) '
            f'(uuid "{stable_uuid("hierarchy-nc/" + sheet.stem + "/" + _ref + "/" + _pin)}"))'
        )

    for ref in sorted(instances):
        output.append(
            emit_instance(
                ref,
                instances[ref],
                placements[ref],
                pin_sets[instances[ref]["lib_id"]],
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

    if output_path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite {output_path}; pass --force")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    result = {
        "sheet": sheet.stem,
        "output": str(output_path),
        "paper": sheet.paper,
        "components": len(instances),
        "nets": len(design["nets"]),
        "blocks": [block.title for block in sheet.blocks],
        "routed_nets": len(routed_nets),
        "label_only_nets": len(design["nets"]) - len(routed_nets),
        "wire_segments": len(router.segments),
        "junctions": len(junctions),
        "labels": sum(len(positions) for positions in router.labels.values()),
        "no_connects": len(unconnected),
        "content_bottom_mm": round(content_bottom, 3),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", choices=sorted(SHEETS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    selected = [args.sheet] if args.sheet else sorted(SHEETS)
    reports = [build_sheet(SHEETS[stem], force=args.force) for stem in selected]
    report_path = OUTPUT / "generation-report.json"
    report_path.write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
