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

from python_emit import (
    emit_instance,
    load_source,
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
DATE = "2026-11-03"

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
        title="LVDS transmitter, termination and connector",
        paper="A3",
        blocks=(
            Block("LVDS OUTPUT", ("J22", "RN26", "RN27"), columns=3),
        ),
    ),
    "encoders": Sheet(
        stem="encoders",
        source="encoders.kicad_sch",
        title="Encoder inputs and 5 V interface",
        paper="A3",
        blocks=(
            Block(
                "ENCODER POWER AND SIGNAL INTERFACE",
                ("F2", "D53", "C119", "U28", "J13", "J14", "J15", "R110", "R111"),
                columns=6,
            ),
        ),
    ),
    "storage_wifi_ui": Sheet(
        stem="storage_wifi_ui",
        source="storage_wifi_ui.kicad_sch",
        title="microSD, Wi-Fi and I2C interfaces",
        paper="A2",
        blocks=(
            Block(
                "MICROSD SOCKETS AND SERIES TERMINATION",
                ("J36", "J54", "JP5", "RN43", "RN44", "FB2", "C67", "C68"),
                columns=8,
            ),
            Block(
                "ESP-01 / ESP-01S SOCKET AND LOCAL REGULATOR",
                ("J20", "U34", "RN36", "C69", "C70", "C88", "C89"),
                columns=7,
            ),
            Block("I2C SERVICE PORT", ("J18",), columns=1),
        ),
    ),
    "analog_io": Sheet(
        stem="analog_io",
        source="analog_io.kicad_sch",
        title="Analog inputs, 0-10 V outputs and 12 V rail",
        paper="A1",
        blocks=(
            Block(
                "ANALOG INPUTS AI0-AI3",
                (
                    "J24",
                    "R61", "R63", "C73",
                    "R64", "R66", "C74",
                    "R67", "R69", "C75",
                    "R182", "R183", "C118",
                ),
                columns=7,
            ),
            Block(
                "ANALOG OUTPUTS D01-D04",
                (
                    "U38",
                    "J25",
                    *rng(92, 107),
                    *rng(92, 99, "C"),
                    "C102",
                ),
                columns=9,
            ),
            Block("ANALOG 12 V SUPPLY", ("U37", "C100", "C101"), columns=3),
        ),
    ),
    "mcu_io": Sheet(
        stem="mcu_io",
        source="mcu_io.kicad_sch",
        title="RP2350B module, shift-register chains and safety I/O",
        paper="A2",
        blocks=(
            Block(
                "WeAct RP2350B AND EXPANSION HEADER",
                ("MOD1", "J51", "R9"),
                columns=3,
            ),
            Block(
                "74HC165 INPUT SHIFT CHAIN",
                (*rng(6, 9, "U"), *rng(22, 25, "C")),
                columns=8,
            ),
            Block(
                "SN74AHCT595 OUTPUT SHIFT CHAIN",
                (*rng(10, 13, "U"), *rng(26, 29, "C")),
                columns=8,
            ),
        ),
    ),
    "field_outputs": Sheet(
        stem="field_outputs",
        source="field_outputs.kicad_sch",
        title="PLC outputs, motion interfaces and servo feedback",
        paper="A0",
        blocks=(
            Block(
                "5 V OUTPUT BUFFERS AND SERIES RESISTORS",
                ("U42", "U43", "C115", "C116", *rng(37, 40, "RN")),
                columns=6,
            ),
            Block(
                "16-CHANNEL OUTPUT OPTOISOLATION",
                rng(61, 64, "U"),
                columns=4,
            ),
            Block(
                "GENERAL OUTPUT DRIVERS AND CONNECTORS",
                (
                    "U26", "U27",
                    "J12", "J32", "J33", "J45",
                    *rng(45, 52, "D"),
                    *rng(57, 64, "D"),
                    *rng(34, 41),
                    *rng(118, 125),
                    "RN30", "RN31",
                ),
                columns=12,
            ),
            Block(
                "MOTION STEP / DIRECTION / ENABLE CONNECTORS",
                ("J10", "J11", "J28", "J29", "J30", "J46", "J47"),
                columns=7,
            ),
            Block(
                "SERVO ERROR AND ZERO INPUT CONNECTORS",
                ("J40", "J41", "J42", "J43", "J48", "J49", "J50"),
                columns=7,
            ),
            Block("OUTPUT PULL-UP NETWORKS", rng(8, 13, "RN"), columns=6),
        ),
    ),
}


SHEETS["field_inputs"] = Sheet(
    stem="field_inputs",
    source="field_inputs.kicad_sch",
    title="Isolated PLC inputs and E-stop",
    paper="A0",
    blocks=(
        Block(
            "PLC INPUTS I01-I08",
            (
                "J7", "U20", "U21",
                *rng(18, 25),
                *rng(13, 28, "D"),
                "RN34", "RN35",
            ),
            columns=12,
        ),
        Block(
            "PLC INPUTS I09-I16",
            (
                "J8", "U18", "U19",
                *rng(26, 33),
                *rng(29, 44, "D"),
                "RN32", "RN33",
            ),
            columns=12,
        ),
        Block(
            "E-STOP INPUT AND INDICATION",
            ("J5", "U35", "R16", "R74", "D9", "D10"),
            columns=6,
        ),
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


def build_sheet(
    sheet: Sheet,
    force: bool = False,
    *,
    output_dir: Path | None = None,
    output_name: str | None = None,
    date: str = DATE,
    company: str = "LeanCam / uCNC Python hierarchy experiment",
    comment: str = "Existing symbols grouped by function; local nets routed where practical",
    labels_global: bool = True,
) -> dict:
    source_path = HARDWARE / sheet.source
    design_path = INPUTS / f"source-{sheet.stem}.json"
    contract_path = INPUTS / f"source-{sheet.stem}-pin-contract.json"
    output_dir = output_dir or OUTPUT
    output_name = output_name or f"{sheet.stem}-python.kicad_sch"
    output_path = output_dir / output_name
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

    source_uuid = child(source_root, "uuid")
    root_uuid = str(source_uuid[1]) if source_uuid else stable_uuid(f"hierarchy/{sheet.stem}/root")
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
        f'\t\t(date {quote(date)})',
        f'\t\t(company {quote(company)})',
        f'\t\t(comment 1 {quote(comment)})',
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
            if labels_global:
                output.extend(
                    [
                        f"\t(global_label {quote(net)}",
                        "\t\t(shape passive)",
                        f"\t\t(at {fmt(x)} {fmt(y)} {angle})",
                        "\t\t(fields_autoplaced yes)",
                        "\t\t(effects",
                        "\t\t\t(font (size 1.27 1.27))",
                        "\t\t\t(justify left bottom)",
                        "\t\t)",
                        f'\t\t(uuid "{stable_uuid("hierarchy-global-label/" + sheet.stem + "/" + net + "/" + str(index))}")',
                        "\t)",
                    ]
                )
            else:
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
                sheet.title,
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
