"""Build the placed two-layer LeanCam motherboard from the KiCad netlist."""

from __future__ import annotations

import csv
import json
import math
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import pcbnew

from configure_netclasses import configure_netclasses


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
NETLIST = HARDWARE / "motherboard.net.xml"
PCB_PATH = HARDWARE / "motherboard.kicad_pcb"
CUSTOM_FP = HARDWARE / "libraries" / "LeanCam.pretty"
KICAD_FP = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\share\kicad\footprints"
)

BOARD_WIDTH_MM = 200.0
BOARD_HEIGHT_MM = 150.0

@dataclass
class Component:
    reference: str
    value: str
    footprint: str
    sheet: str
    dnp: bool
    nets: dict[str, str]


MAJOR: dict[str, tuple[float, float, float]] = {
    "J1": (177.368, 144.942, 0),
    "J3": (152, 6, 90),
    "J4": (80.5, 25.84, 0),
    "J5": (7, 29.5, 90),
    "J6": (7, 40.5, 90),
    "J7": (8.0, 12.0, 270),
    "J8": (8.0, 74.5, 270),
    "J9": (126.46, 112, 0),
    "J10": (68.0, 5.5, 180),
    "J11": (85.5, 5.5, 180),
    "J12": (86.132, 6.558, 180),
    "J13": (35.5, 144.75, 180),
    "J14": (58.5, 144.75, 180),
    "J15": (82, 144.75, 180),
    "J16": (133, 80, 0),
    "J17": (30.0, 31.0, 270),
    "J18": (154.0, 48.0, 270),
    "J19": (181.610, 68.580, 90),
    "J20": (172.085, 40.640, 0),
    "J21": (83, 7, 0),
    "J22": (145.5, 34.0, 270),
    "J9": (64.0, 61.0, 0),
    "J27": (77.0, 61.0, 0),
    "J28": (103.0, 5.5, 180),
    "J29": (120.5, 5.5, 180),
    "J30": (137.5, 5.5, 180),
    "J31": (147.5, 5.5, 180),
    "J32": (43.0, 6.5, 180),
    "J33": (173.5, 145.0, 180),
    "J34": (8.0, 43.25, 270),
    "J35": (8.0, 105.75, 270),
    "J33": (20.25, 6.75, 180),
    "J34": (8.0, 53.5, 270),
    "J35": (8.0, 116.5, 270),
    "RN26": (143.0, 40.0, 90),
    "RN27": (135.5, 40.0, 90),
    "U41": (161.290, 27.940, 90),
    "C106": (170.180, 27.940, 0),
    "J24": (118.75, 145.0, 0),
    "J25": (149.75, 145.0, 0),
    "MOD1": (105, 40, 180),
    "SW1": (62.5, 61, 0),
    "SW2": (151.130, 35.560, 0),
    "Q1": (48, 43, 0),
    "U1": (54, 30.86, 0),
    "U2": (198.12, 94.0, 0),
    "U3": (91, 9, 0),
    "U4": (92, 15, 0),
    "U6": (112, 70, 0),
    "U7": (112, 84, 0),
    "U8": (112, 98, 0),
    "U9": (112, 112, 0),
    # The output registers are paired physically with their buffers/ULNs near
    # the bottom-edge output connectors. Register roles stay unchanged.
    "U10": (155, 115, 0),
    "U11": (102, 92, 0),
    "U12": (75, 112, 0),
    "U13": (148, 85, 0),
    "U18": (43, 88, 0),
    "U19": (43, 108, 0),
    "U20": (43, 124, 0),
    "U21": (65, 124, 0),
    "U24": (175, 115, 0),
    "U25": (122, 92, 0),
    "U26": (97, 110, 0),
    "U27": (97, 124, 0),
    "U28": (92, 121, 0),
    "R110": (85.500, 133.300, 0),
    "R111": (90.000, 133.300, 0),
    "R10": (80.000, 49.000, 0),
    "R11": (87.000, 49.000, 0),
    "R12": (100.000, 49.000, 0),
    "R13": (112.000, 49.000, 0),
    "RN6": (68.000, 64.000, 0),
    "RN7": (73.000, 64.000, 0),
    "RN20": (28.920, 39.500, 90),
    "RN21": (39.080, 39.500, 90),
    "RN22": (24.000, 54.000, 90),
    "RN24": (36.500, 53.500, 90),
    "R58": (161.925, 39.370, 0),
    "R57": (161.925, 42.545, 0),
    "R55": (161.925, 48.260, 0),
    "R56": (161.925, 50.800, 0),
    "R113": (142.500, 15.000, 90),
    "Q5": (145.000, 12.000, 0),
    "Q6": (50.0, 36.5, 0),
    "Q7": (55.5, 36.5, 0),
    "R114": (48.5, 39.5, 0),
    "R115": (50.0, 42.0, 0),
    "R116": (54.0, 39.5, 0),
    "R117": (55.5, 42.0, 0),
    "D57": (41.536, 14.143, 90),
    "D58": (37.536, 14.143, 90),
    "D59": (34.536, 14.143, 90),
    "D60": (30.536, 14.143, 90),
    "D61": (27.536, 14.143, 90),
    "D62": (23.536, 14.143, 90),
    "D63": (20.536, 14.143, 90),
    "D64": (16.536, 14.143, 90),
    "R118": (41.536, 19.142, 90),
    "R119": (37.536, 19.142, 90),
    "R120": (34.536, 19.142, 90),
    "R121": (30.536, 19.142, 90),
    "R122": (27.536, 19.142, 90),
    "R123": (23.536, 19.142, 90),
    "R124": (20.536, 19.142, 90),
    "R125": (16.536, 19.142, 90),
    "RN30": (50.5, 24.0, 0),
    "RN31": (31.0, 25.0, 0),
    "U40": (39.000, 130.500, 270),
    "F4": (44.500, 130.500, 270),
    "C103": (37.000, 134.000, 180),
    "C105": (27.500, 134.000, 0),
    "D56": (17.500, 132.500, 90),
    "JP2": (15.000, 69.500, 0),
    "JP3": (15.000, 90.000, 0),
    "JP4": (15.000, 110.000, 0),
    "F1": (41, 23, 0),
    "F2": (152, 108, 0),
    "FB3": (51, 56, 0),
    "L1": (60.5, 30.86, 0),
    "L2": (64, 10, 0),
    "C4": (48.5, 32.5, 90),
    "C5": (45, 38, 0),
    "C6": (63.5, 36.5, 0),
    "C7": (57.8, 36.5, 0),
    "C86": (54, 35, 0),
    "C76": (191.135, 94.0, 90),
    "C13": (191.135, 89.555, 90),
    "C10": (191.135, 99.080, 90),
    "C90": (195.580, 87.015, 0),
    "C7": (181.000, 101.200, 90),
    "C8": (181.000, 104.500, 0),
    "C88": (189.230, 44.450, 270),
    "C89": (185.420, 37.465, 180),
    "C70": (170.815, 37.465, 0),
    "C69": (176.530, 37.465, 0),
    "C22": (60.000, 57.480, 0),
    "C23": (78.000, 57.480, 0),
    "C24": (94.500, 56.980, 0),
    "C25": (110.500, 56.980, 0),
    "C26": (110.500, 42.980, 0),
    "C27": (94.500, 42.980, 0),
    "C28": (77.500, 42.980, 0),
    "C29": (59.500, 42.980, 0),
    "FB1": (133.350, 66.040, 0),
    "C15": (139.700, 66.040, 0),
    "R73": (183.000, 87.500, 0),
    "R4": (162.000, 85.000, 0),
    "D4": (168.000, 85.000, 180),
    "R5": (162.000, 92.000, 0),
    "D5": (168.000, 92.000, 180),
    "R53": (178.700, 60.120, 0),
    "R51": (178.700, 62.620, 0),
    "R50": (178.700, 70.120, 0),
    "R52": (178.700, 75.060, 0),
    "R54": (178.700, 78.060, 0),
    "R44": (172.600, 60.120, 0),
    "R45": (172.600, 62.620, 0),
    "R49": (172.600, 57.620, 0),
    "R46": (172.600, 73.000, 0),
    "R48": (172.600, 76.750, 0),
    "R47": (172.600, 79.500, 0),
    "FB2": (166.370, 61.595, 90),
    "C68": (166.370, 67.310, 90),
    "C67": (166.370, 73.025, 90),
    "U34": (182.880, 44.450, 180),
    "D3": (420, 50, 0),
}

REGIONS = {
    "Power and supervision": (38, 8, 82, 58),
    "MCU, shift chains and safety": (80, 12, 132, 65),
    "16 PLC inputs and expansion": (18, 60, 80, 137),
    "24 PLC outputs": (78, 96, 202, 138),
    "Encoders": (78, 106, 112, 138),
    "Display": (132, 2, 203, 32),
    "Storage, Wi-Fi and UI": (95, 35, 202, 102),
    "Analog inputs": (10, 116, 34, 138),
}


def parse_property(component: ET.Element, name: str) -> str:
    for prop in component.findall("property"):
        if prop.get("name") == name:
            return prop.get("value", "")
    return ""


def parse_netlist() -> list[Component]:
    root = ET.parse(NETLIST).getroot()
    node_nets: dict[tuple[str, str], str] = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        if name.startswith("unconnected-"):
            continue
        for node in net.findall("node"):
            node_nets[(node.get("ref", ""), node.get("pin", ""))] = name

    components = []
    for node in root.findall("./components/comp"):
        reference = node.get("ref", "")
        footprint = (node.findtext("footprint") or "").strip()
        if not footprint:
            continue
        pin_numbers = [pin.get("num", "") for pin in node.findall("./units/unit/pins/pin")]
        nets = {
            pin: node_nets[(reference, pin)]
            for pin in pin_numbers
            if (reference, pin) in node_nets
        }
        components.append(
            Component(
                reference=reference,
                value=(node.findtext("value") or "").strip(),
                footprint=footprint,
                sheet=parse_property(node, "Sheetname"),
                dnp=parse_property(node, "Assembly") == "DNP",
                nets=nets,
            )
        )
    return components


def load_footprint(footprint_id: str):
    library, name = footprint_id.split(":", 1)
    directory = CUSTOM_FP if library == "LeanCam" else KICAD_FP / f"{library}.pretty"
    footprint = pcbnew.FootprintLoad(str(directory), name)
    if footprint is None:
        raise FileNotFoundError(f"Footprint not found: {footprint_id} ({directory})")
    return footprint


def add_outline(board) -> None:
    points = [
        (0, 0),
        (BOARD_WIDTH_MM, 0),
        (BOARD_WIDTH_MM, BOARD_HEIGHT_MM),
        (0, BOARD_HEIGHT_MM),
    ]
    for start, end in zip(points, points[1:] + points[:1]):
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(pcbnew.VECTOR2I_MM(*start))
        line.SetEnd(pcbnew.VECTOR2I_MM(*end))
        line.SetLayer(pcbnew.Edge_Cuts)
        line.SetWidth(pcbnew.FromMM(0.15))
        board.Add(line)


def add_board_text(board, text: str, x: float, y: float, size: float = 1.5, layer=pcbnew.F_SilkS):
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    item.SetLayer(layer)
    item.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
    item.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(item)


def bbox_inside(box, margin: float = 0.5) -> bool:
    return (
        pcbnew.ToMM(box.GetLeft()) >= margin
        and pcbnew.ToMM(box.GetTop()) >= margin
        and pcbnew.ToMM(box.GetRight()) <= BOARD_WIDTH_MM - margin
        and pcbnew.ToMM(box.GetBottom()) <= BOARD_HEIGHT_MM - margin
    )


def overlap(a, b) -> bool:
    return not (
        a.GetRight() < b.GetLeft()
        or a.GetLeft() > b.GetRight()
        or a.GetBottom() < b.GetTop()
        or a.GetTop() > b.GetBottom()
    )


def candidate_boxes(footprint, x: float, y: float, clearance: float = 0.25):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.BuildCourtyardCaches()
    courtyard_layer = pcbnew.B_CrtYd if footprint.GetLayer() == pcbnew.B_Cu else pcbnew.F_CrtYd
    courtyard = footprint.GetCourtyard(courtyard_layer)
    box = courtyard.BBox() if courtyard.OutlineCount() else footprint.GetBoundingBox(False, False)
    snapshot = pcbnew.BOX2I(box.GetPosition(), box.GetSize())
    # Preserve the tightly packed manual connector anchors. KiCad placement
    # DRC remains the final authority on courtyard and solder-mask collisions.
    snapshot.Inflate(pcbnew.FromMM(clearance))
    return snapshot


def choose_spot(footprint, preferred, occupied, step: float = 2.54):
    x1, y1, x2, y2 = preferred
    y = y1
    while y <= y2:
        x = x1
        while x <= x2:
            box = candidate_boxes(footprint, x, y)
            if bbox_inside(box) and not any(overlap(box, other) for other in occupied):
                return x, y, box
            x += step
        y += step
    # Fallback across the whole board.
    y = 5.0
    while y <= BOARD_HEIGHT_MM - 5:
        x = 5.0
        while x <= BOARD_WIDTH_MM - 5:
            box = candidate_boxes(footprint, x, y)
            if bbox_inside(box) and not any(overlap(box, other) for other in occupied):
                return x, y, box
            x += step
        y += step
    raise RuntimeError(f"No placement room for {footprint.GetReference()}")


def net_weight(name: str) -> float:
    if name in {"GND", "PGND", "AGND"}:
        return 0.0
    if name.startswith(("HSTX_", "LVDS_")):
        return 2.5
    if name.startswith(("ESTOP", "HOLD", "START")):
        return 3.0
    if name.startswith(("SR_", "ENC")):
        return 1.5
    if name.startswith(("VIN", "BUCK", "MODULE_5V", "+12V_AO")) or name.startswith("+"):
        return 0.35
    return 1.0


def component_points(component: Component, footprint, x: float, y: float, rotation: float):
    footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    footprint.SetOrientationDegrees(rotation)
    points = []
    for pad in footprint.Pads():
        net = component.nets.get(pad.GetNumber())
        if not net:
            continue
        pos = pad.GetPosition()
        points.append((net, pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)))
    return points


def candidate_wire_score(points, net_points) -> float:
    score = 0.0
    for net, x, y in points:
        weight = net_weight(net)
        if weight == 0:
            continue
        endpoints = net_points.get(net)
        if not endpoints:
            continue
        score += weight * min(math.hypot(x - ex, y - ey) for _, ex, ey in endpoints)
    return score


def orientations_for(component: Component) -> tuple[float, ...]:
    return (0, 90, 180, 270)


def put_on_side(footprint, back: bool) -> None:
    if back and footprint.GetLayer() != pcbnew.B_Cu:
        footprint.Flip(footprint.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    elif not back and footprint.GetLayer() != pcbnew.F_Cu:
        footprint.Flip(footprint.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)


def component_is_back(component: Component) -> bool:
    if component.reference in {"J9", "J16", "J17"}:
        return True
    if component.reference in {
        "U28", "U40", "R10", "R11", "R12", "R13", "R113", "Q5",
        "Q6", "Q7", "R114", "R115", "R116", "R117",
        "D57", "D58", "D59", "D60", "D61", "D62", "D63", "D64",
        "R118", "R119", "R120", "R121", "R122", "R123", "R124", "R125",
        "F4", "C103", "C105",
        "RN6", "RN7", "RN20", "RN21", "RN22", "RN24",
        "R55", "R56", "R57", "R58", "R110", "R111",
    }:
        return False
    if component.reference.startswith(("J", "MOD", "SW", "D")):
        return False
    return component.sheet not in {"Power and supervision", "Display"}


def footprint_spans_sides(footprint) -> bool:
    return any(
        pad.IsOnLayer(pcbnew.F_Cu) and pad.IsOnLayer(pcbnew.B_Cu)
        for pad in footprint.Pads()
    )


def add_to_occupancy(footprint, box, occupied) -> None:
    layers = (
        (int(pcbnew.F_Cu), int(pcbnew.B_Cu))
        if footprint_spans_sides(footprint)
        else (int(footprint.GetLayer()),)
    )
    for layer in layers:
        occupied[layer].append(box)


def occupancy_for(footprint, occupied):
    if footprint_spans_sides(footprint):
        return occupied[int(pcbnew.F_Cu)] + occupied[int(pcbnew.B_Cu)]
    return occupied[int(footprint.GetLayer())]


def choose_connected_spot(
    component: Component,
    footprint,
    preferred,
    occupied,
    net_points,
    step: float = 2.54,
):
    x1, y1, x2, y2 = preferred
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    best = None
    for rotation in orientations_for(component):
        footprint.SetOrientationDegrees(rotation)
        y = y1
        while y <= y2:
            x = x1
            while x <= x2:
                box = candidate_boxes(footprint, x, y)
                if bbox_inside(box, 0.8) and not any(overlap(box, other) for other in occupied):
                    points = component_points(component, footprint, x, y, rotation)
                    score = candidate_wire_score(points, net_points)
                    score += 0.015 * math.hypot(x - center_x, y - center_y)
                    score += rotation / 3600.0
                    if best is None or score < best[0]:
                        best = (score, x, y, rotation, box, points)
                x += step
            y += step
    if best is not None:
        return best

    # Expand beyond the nominal block before failing the build.
    for rotation in orientations_for(component):
        footprint.SetOrientationDegrees(rotation)
        y = 5.0
        while y <= BOARD_HEIGHT_MM - 5:
            x = 5.0
            while x <= BOARD_WIDTH_MM - 5:
                box = candidate_boxes(footprint, x, y)
                if bbox_inside(box, 0.8) and not any(overlap(box, other) for other in occupied):
                    points = component_points(component, footprint, x, y, rotation)
                    score = candidate_wire_score(points, net_points)
                    if best is None or score < best[0]:
                        best = (score, x, y, rotation, box, points)
                x += step
            y += step
    if best is None:
        raise RuntimeError(f"No placement room for {component.reference}")
    return best


def net_mst_length(points) -> float:
    unique = list(dict.fromkeys((point[-2], point[-1]) for point in points))
    if len(unique) < 2:
        return 0.0
    remaining = set(range(1, len(unique)))
    visited = {0}
    length = 0.0
    while remaining:
        best = None
        for i in visited:
            for j in remaining:
                value = math.hypot(unique[i][0] - unique[j][0], unique[i][1] - unique[j][1])
                if best is None or value < best[0]:
                    best = (value, j)
        value, j = best
        length += value
        visited.add(j)
        remaining.remove(j)
    return length


def refine_placement(
    components,
    footprints,
    fixed_refs,
    boxes_by_ref,
    net_points,
    region_for,
) -> dict[str, tuple[float, float, float]]:
    positions = {}
    moving = [component for component in components if component.reference not in fixed_refs]
    for pass_index in range(3):
        improvements = 0
        gain = 0.0
        for component in moving:
            ref = component.reference
            footprint = footprints[ref]
            pos = footprint.GetPosition()
            current_x = pcbnew.ToMM(pos.x)
            current_y = pcbnew.ToMM(pos.y)
            current_rot = footprint.GetOrientationDegrees()
            nets = sorted(set(component.nets.values()))
            before = sum(
                net_weight(net) * net_mst_length(net_points.get(net, []))
                for net in nets
                if net_weight(net) > 0
            )
            region = region_for(component)
            best = None
            for delta_x, delta_y in (
                (0, 0), (-5.08, 0), (5.08, 0), (0, -5.08), (0, 5.08),
                (-2.54, 0), (2.54, 0), (0, -2.54), (0, 2.54),
            ):
                x = current_x + delta_x
                y = current_y + delta_y
                if not (region[0] <= x <= region[2] and region[1] <= y <= region[3]):
                    continue
                for rotation in (current_rot, (current_rot + 90) % 360):
                    footprint.SetOrientationDegrees(rotation)
                    box = candidate_boxes(footprint, x, y)
                    if not bbox_inside(box, 0.8):
                        continue
                    if any(
                        overlap(box, other)
                        for other_ref, other in boxes_by_ref.items()
                        if other_ref != ref
                        and (
                            other_ref.startswith("H")
                            or footprint_spans_sides(footprints[other_ref])
                            or footprints[other_ref].GetLayer() == footprint.GetLayer()
                        )
                    ):
                        continue
                    points = component_points(component, footprint, x, y, rotation)
                    candidate_nets = {net for net, _, _ in points}
                    after = 0.0
                    for net in candidate_nets | set(nets):
                        weight = net_weight(net)
                        if weight == 0:
                            continue
                        updated = [
                            (px, py) for other_ref, px, py in net_points.get(net, [])
                            if other_ref != ref
                        ]
                        updated.extend((px, py) for point_net, px, py in points if point_net == net)
                        after += weight * net_mst_length(updated)
                    improvement = before - after
                    if improvement > 0.05 and (best is None or improvement > best[0]):
                        best = (improvement, x, y, rotation, box, points)
            if best is not None:
                improvement, x, y, rotation, box, points = best
                footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
                footprint.SetOrientationDegrees(rotation)
                boxes_by_ref[ref] = box
                for net in nets:
                    net_points[net] = [
                        (other_ref, px, py)
                        for other_ref, px, py in net_points.get(net, [])
                        if other_ref != ref
                    ]
                for net, px, py in points:
                    net_points[net].append((ref, px, py))
                improvements += 1
                gain += improvement
            else:
                footprint.SetPosition(pcbnew.VECTOR2I_MM(current_x, current_y))
                footprint.SetOrientationDegrees(current_rot)
            positions[ref] = (
                pcbnew.ToMM(footprint.GetPosition().x),
                pcbnew.ToMM(footprint.GetPosition().y),
                footprint.GetOrientationDegrees(),
            )
        print(f"placement pass {pass_index + 1}: {improvements} improved, gain {gain:.1f} mm")
        if not improvements:
            break
    return positions


def add_mounting_holes(board):
    boxes = {}
    occupied = []
    positions = [(5, 5), (191.5, 5), (5, 145), (191.5, 145)]
    for index, (x, y) in enumerate(positions, 1):
        fp = pcbnew.FootprintLoad(
            str(KICAD_FP / "MountingHole.pretty"), "MountingHole_3.2mm_M3"
        )
        if fp is None:
            raise FileNotFoundError("Mounting hole footprint missing")
        fp.SetReference(f"H{index}")
        fp.SetValue("M3")
        fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        board.Add(fp)
        box = candidate_boxes(fp, x, y)
        occupied.append(box)
        boxes[fp.GetReference()] = box
    return occupied, boxes


def add_zones(board, net_map) -> None:
    # Keep the front side visually clear for manual placement. The complete
    # GND plane remains on B.Cu, and stitched vias connect to it.
    for layer in (pcbnew.B_Cu,):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(net_map["GND"].GetNetCode())
        zone.SetLocalClearance(pcbnew.FromMM(0.3))
        zone.SetMinThickness(pcbnew.FromMM(0.25))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline = zone.Outline()
        outline.NewOutline()
        for x, y in [
            (0.5, 0.5),
            (BOARD_WIDTH_MM - 0.5, 0.5),
            (BOARD_WIDTH_MM - 0.5, BOARD_HEIGHT_MM - 0.5),
            (0.5, BOARD_HEIGHT_MM - 0.5),
        ]:
            outline.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
        board.Add(zone)


def build_board() -> None:
    placement_mode = os.environ.get("LEANCAM_PLACEMENT_MODE", "optimized")
    seed_path = os.environ.get("LEANCAM_STAGED_BOARD")
    seeded = {}
    seeded_tracks = []
    seeded_vias = []
    if seed_path:
        seed_board = pcbnew.LoadBoard(seed_path)
        for footprint in seed_board.GetFootprints():
            position = footprint.GetPosition()
            seeded[footprint.GetReference()] = {
                "x": pcbnew.ToMM(position.x),
                "y": pcbnew.ToMM(position.y),
                "rotation": footprint.GetOrientationDegrees(),
                "back": footprint.GetLayer() == pcbnew.B_Cu,
            }
        for track in seed_board.GetTracks():
            if isinstance(track, pcbnew.PCB_VIA):
                seeded_vias.append(
                    {
                        "position": track.GetPosition(),
                        "width": track.GetWidth(pcbnew.F_Cu),
                        "drill": track.GetDrillValue(),
                        "top_layer": track.TopLayer(),
                        "bottom_layer": track.BottomLayer(),
                        "net": track.GetNetname(),
                    }
                )
                continue
            if not isinstance(track, pcbnew.PCB_TRACK):
                continue
            seeded_tracks.append(
                {
                    "start": track.GetStart(),
                    "end": track.GetEnd(),
                    "width": track.GetWidth(),
                    "layer": track.GetLayer(),
                    "net": track.GetNetname(),
                }
            )
        placement_mode = "staged"
    components = parse_netlist()
    board = pcbnew.BOARD()
    board.SetFileName(str(PCB_PATH))
    board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
    add_outline(board)

    nets = {
        "GND",
        "+5V",
        "+12V_AO",
        "+3V3",
        "+3V3_A",
        "+3V3_SD",
        "+3V3_WIFI",
        "+5V_ENC",
        "+5V_MCU",
        "VIN_RAW",
        "VIN_FUSED",
        "VIN_PROT",
    }
    for component in components:
        nets.update(component.nets.values())
    net_map = {}
    for name in sorted(nets):
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        net_map[name] = net

    # Preserve already approved copper, including explicit stitching and
    # thermal vias, when rebuilding from the staged board.
    for track_data in seeded_tracks:
        if track_data["net"] not in net_map:
            continue
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(track_data["start"])
        track.SetEnd(track_data["end"])
        track.SetWidth(track_data["width"])
        track.SetLayer(track_data["layer"])
        track.SetNet(net_map[track_data["net"]])
        board.Add(track)
    for via_data in seeded_vias:
        if via_data["net"] not in net_map:
            continue
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(via_data["position"])
        via.SetWidth(via_data["width"])
        via.SetDrill(via_data["drill"])
        via.SetLayerPair(via_data["top_layer"], via_data["bottom_layer"])
        via.SetNet(net_map[via_data["net"]])
        board.Add(via)

    occupied = {int(pcbnew.F_Cu): [], int(pcbnew.B_Cu): []}
    footprints = {}
    positions = {}
    boxes_by_ref = {}
    net_points = defaultdict(list)
    component_by_ref = {component.reference: component for component in components}
    ordered = sorted(
        components,
        key=lambda component: (0 if component.reference.startswith(("J", "MOD", "U", "SW", "Q", "L")) else 1)
    )
    parked_index = 0
    for component in ordered:
        fp = load_footprint(component.footprint)
        fp.SetReference(component.reference)
        fp.SetValue(component.value)
        fp.SetDNP(component.dnp)
        board.Add(fp)
        if component.reference in seeded:
            seed = seeded[component.reference]
            put_on_side(fp, seed["back"])
            fp.SetPosition(pcbnew.VECTOR2I_MM(seed["x"], seed["y"]))
            fp.SetOrientationDegrees(seed["rotation"])
            x, y, rotation = seed["x"], seed["y"], seed["rotation"]
            box = candidate_boxes(fp, x, y)
            add_to_occupancy(fp, box, occupied)
            boxes_by_ref[component.reference] = box
            positions[component.reference] = (x, y, rotation)
            for net, px, py in component_points(component, fp, x, y, rotation):
                net_points[net].append((component.reference, px, py))
        elif placement_mode == "staged":
            put_on_side(fp, component_is_back(component))
            x = 620 + (parked_index // 20) * 24
            y = 20 + (parked_index % 20) * 15
            fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            positions[component.reference] = (x, y, fp.GetOrientationDegrees())
            parked_index += 1
        elif component.reference in MAJOR:
            put_on_side(fp, component_is_back(component))
            x, y, rotation = MAJOR[component.reference]
            fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            fp.SetOrientationDegrees(rotation)
            box = candidate_boxes(fp, x, y)
            add_to_occupancy(fp, box, occupied)
            boxes_by_ref[component.reference] = box
            positions[component.reference] = (x, y, rotation)
            for net, px, py in component_points(component, fp, x, y, rotation):
                net_points[net].append((component.reference, px, py))
        footprints[component.reference] = fp

    fixed_refs = (
        {component.reference for component in components}
        if placement_mode == "staged"
        else set(MAJOR)
    )
    if placement_mode != "staged":
        fixed_items = sorted(fixed_refs)
        for index, ref_a in enumerate(fixed_items):
            x_a, y_a, rotation_a = positions[ref_a]
            box_a = candidate_boxes(footprints[ref_a], x_a, y_a, clearance=0.0)
            footprints[ref_a].SetOrientationDegrees(rotation_a)
            for ref_b in fixed_items[index + 1:]:
                x_b, y_b, rotation_b = positions[ref_b]
                footprints[ref_b].SetOrientationDegrees(rotation_b)
                box_b = candidate_boxes(footprints[ref_b], x_b, y_b, clearance=0.0)
                if (
                    (
                        footprints[ref_a].GetLayer() == footprints[ref_b].GetLayer()
                        or footprint_spans_sides(footprints[ref_a])
                        or footprint_spans_sides(footprints[ref_b])
                    )
                    and overlap(box_a, box_b)
                ):
                    def box_text(box):
                        return (
                            f"({pcbnew.ToMM(box.GetLeft()):.2f},"
                            f"{pcbnew.ToMM(box.GetTop()):.2f})-"
                            f"({pcbnew.ToMM(box.GetRight()):.2f},"
                            f"{pcbnew.ToMM(box.GetBottom()):.2f})"
                        )
                    raise RuntimeError(
                        f"Fixed placement overlap: {ref_a} {box_text(box_a)} "
                        f"and {ref_b} {box_text(box_b)}"
                    )

    hole_boxes, hole_box_map = add_mounting_holes(board)
    occupied[int(pcbnew.F_Cu)].extend(hole_boxes)
    occupied[int(pcbnew.B_Cu)].extend(hole_boxes)
    boxes_by_ref.update(hole_box_map)

    # Place remaining components by connectivity. Each step chooses the part
    # with the most already-placed electrical neighbours, then the lowest
    # weighted airwire cost among legal positions and rotations.
    pending = [component for component in components if component.reference not in fixed_refs]
    if placement_mode == "baseline":
        for index, component in enumerate(pending, start=1):
            fp = footprints[component.reference]
            region = REGIONS.get(component.sheet, (10, 10, 200, 140))
            x, y, box = choose_spot(fp, region, occupancy_for(fp, occupied))
            fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            add_to_occupancy(fp, box, occupied)
            boxes_by_ref[component.reference] = box
            positions[component.reference] = (x, y, fp.GetOrientationDegrees())
            if index % 25 == 0:
                print(f"baseline placement: {index}/{len(pending)}")
    else:
        while pending:
            def priority(component: Component):
                nets = {net for net in component.nets.values() if net_weight(net) > 0}
                attached = sum(1 for net in nets if net_points.get(net))
                active = component.reference.startswith(("U", "Q", "L"))
                return (attached, active, len(nets), len(component.nets))

            component = max(pending, key=lambda item: (priority(item), item.reference))
            fp = footprints[component.reference]
            region = REGIONS.get(component.sheet, (10, 10, 200, 140))
            score, x, y, rotation, box, points = choose_connected_spot(
                component, fp, region, occupancy_for(fp, occupied), net_points
            )
            fp.SetPosition(pcbnew.VECTOR2I_MM(x, y))
            fp.SetOrientationDegrees(rotation)
            add_to_occupancy(fp, box, occupied)
            boxes_by_ref[component.reference] = box
            positions[component.reference] = (x, y, rotation)
            for net, px, py in points:
                net_points[net].append((component.reference, px, py))
            pending.remove(component)
            placed_count = len(components) - len(pending)
            if placed_count % 25 == 0:
                print(f"connectivity placement: {placed_count}/{len(components)}")

        refined = refine_placement(
            components,
            footprints,
            fixed_refs,
            boxes_by_ref,
            net_points,
            lambda component: REGIONS.get(component.sheet, (10, 10, 200, 140)),
        )
        positions.update(refined)

    (HARDWARE / f"placement-{placement_mode}.json").write_text(
        json.dumps(
            {
                ref: {"x": round(pos[0], 3), "y": round(pos[1], 3), "rotation": round(pos[2], 3)}
                for ref, pos in sorted(positions.items())
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    assigned = 0
    missing_pads = []
    for component in components:
        fp = footprints[component.reference]
        for pad in fp.Pads():
            net_name = component.nets.get(pad.GetNumber())
            if net_name:
                pad.SetNet(net_map[net_name])
                assigned += 1
            elif pad.GetNumber():
                missing_pads.append(f"{component.reference}.{pad.GetNumber()}")

    # LMR36510 exposed pad: six 0.30 mm drill thermal vias tied to GND.
    if "U1" in footprints:
        exposed_pad = footprints["U1"].FindPadByNumber("9")
        if exposed_pad is not None:
            # Pad global positions are not reliable until connectivity has
            # been rebuilt; the exposed pad is centered on the SOT-23-8 body.
            u1 = footprints["U1"]
            center = u1.GetPosition()
            angle = math.radians(u1.GetOrientationDegrees())
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            for dx, dy in (
                (-0.6, -1.2), (0.6, -1.2),
                (-0.6, 0.0), (0.6, 0.0),
                (-0.6, 1.2), (0.6, 1.2),
            ):
                rotated_dx = dx * cos_angle - dy * sin_angle
                rotated_dy = dx * sin_angle + dy * cos_angle
                via = pcbnew.PCB_VIA(board)
                via.SetPosition(
                    pcbnew.VECTOR2I(
                        center.x + pcbnew.FromMM(rotated_dx),
                        center.y + pcbnew.FromMM(rotated_dy),
                    )
                )
                if any(
                    isinstance(existing, pcbnew.PCB_VIA)
                    and existing.GetNetname() == "GND"
                    and abs(existing.GetPosition().x - via.GetPosition().x) <= pcbnew.FromMM(0.001)
                    and abs(existing.GetPosition().y - via.GetPosition().y) <= pcbnew.FromMM(0.001)
                    for existing in board.GetTracks()
                ):
                    continue
                via.SetDrill(pcbnew.FromMM(0.3))
                via.SetWidth(pcbnew.FromMM(0.6))
                via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                via.SetNet(net_map["GND"])
                board.Add(via)

    # Give every 100 nF decoupling capacitor a short, direct B.Cu ground return.
    # The via sits beyond the GND pad on the side away from the supply pin.
    for component in components:
        if not component.reference.startswith("C") or component.value != "100nF":
            continue
        footprint = footprints[component.reference]
        pads = list(footprint.Pads())
        gnd_pads = [pad for pad in pads if pad.GetNetname() == "GND"]
        if len(pads) != 2 or len(gnd_pads) != 1:
            continue
        gnd_pad = gnd_pads[0]
        signal_pad = next(pad for pad in pads if pad is not gnd_pad)
        if not gnd_pad.IsOnLayer(pcbnew.F_Cu):
            continue
        gnd_point = gnd_pad.GetPosition()
        signal_point = signal_pad.GetPosition()
        dx = gnd_point.x - signal_point.x
        dy = gnd_point.y - signal_point.y
        distance = math.hypot(dx, dy)
        if not distance:
            continue
        offset = pcbnew.FromMM(1.15)
        via_point = pcbnew.VECTOR2I(
            gnd_point.x + round(dx / distance * offset),
            gnd_point.y + round(dy / distance * offset),
        )
        if any(
            isinstance(existing, pcbnew.PCB_VIA)
            and existing.GetNetname() == "GND"
            and math.hypot(
                existing.GetPosition().x - via_point.x,
                existing.GetPosition().y - via_point.y,
            ) <= pcbnew.FromMM(2.0)
            for existing in board.GetTracks()
        ):
            continue
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(via_point)
        via.SetDrill(pcbnew.FromMM(0.3))
        via.SetWidth(pcbnew.FromMM(0.6))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(net_map["GND"])
        board.Add(via)

        stub = pcbnew.PCB_TRACK(board)
        stub.SetStart(gnd_point)
        stub.SetEnd(via_point)
        stub.SetWidth(pcbnew.FromMM(0.5))
        stub.SetLayer(pcbnew.F_Cu)
        stub.SetNet(net_map["GND"])
        board.Add(stub)

    # Keep silkscreen readable on the dense board by moving small passive and
    # active references to the fabrication layer.
    for component in components:
        fp = footprints[component.reference]
        if component.reference.startswith(("R", "C", "D", "L", "Q", "U", "RN", "FB", "J")):
            fab_layer = pcbnew.B_Fab if fp.GetLayer() == pcbnew.B_Cu else pcbnew.F_Fab
            fp.Reference().SetLayer(fab_layer)

    # Make power and motor nets wider than logic nets.
    power_nets = {
        "GND", "VIN_RAW", "VIN_FUSED", "VIN_PROT",
        "+5V", "+12V_AO", "+5V_MCU", "+5V_ENC", "+3V3", "+3V3_A",
        "+3V3_SD", "+3V3_WIFI", "BL_RAW", "BL_VIN", "DO_COM",
    }
    netclasses = board.GetNetClasses()
    power_class = pcbnew.NETCLASS("Power")
    power_class.SetClearance(pcbnew.FromMM(0.3))
    power_class.SetTrackWidth(pcbnew.FromMM(0.8))
    power_class.SetViaDiameter(pcbnew.FromMM(0.8))
    power_class.SetViaDrill(pcbnew.FromMM(0.4))
    netclasses["Power"] = power_class
    for name, net in net_map.items():
        if name in power_nets:
            net.SetNetClass(power_class)
    board.SynchronizeNetsAndNetClasses(False)

    add_zones(board, net_map)
    board.BuildConnectivity()

    pcbnew.SaveBoard(str(PCB_PATH), board)
    configure_netclasses()
    print(f"placed {len(components)} components, assigned {assigned} pads")
    if missing_pads:
        print(f"unassigned pads: {len(missing_pads)}")
        print(", ".join(missing_pads[:30]))


def export_bom() -> None:
    components = parse_netlist()
    root = ET.parse(NETLIST).getroot()
    by_ref = {item.get("ref"): item for item in root.findall("./components/comp")}
    output = ROOT / "manufacturing" / "bom.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for component in components:
        if component.dnp:
            continue
        node = by_ref[component.reference]
        mpn = parse_property(node, "MPN")
        manufacturer = parse_property(node, "Manufacturer")
        grouped[(component.value, component.footprint, manufacturer, mpn)].append(
            component.reference
        )
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Quantity", "Value", "Footprint", "Manufacturer", "MPN", "References"])
        for (value, footprint, manufacturer, mpn), refs in sorted(grouped.items()):
            writer.writerow([len(refs), value, footprint, manufacturer, mpn, " ".join(refs)])
    print(f"BOM: {output}")


if __name__ == "__main__":
    build_board()
    export_bom()
