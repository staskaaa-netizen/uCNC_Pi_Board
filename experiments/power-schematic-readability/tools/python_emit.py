"""Shared symbol and grid helpers for the Python schematic experiments."""

from __future__ import annotations

import math
import uuid
from pathlib import Path

from kicad_sexpr import child, children, fmt, parse_file, property_value, quote


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
    project_name: str,
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
            f"\t\t\t(project {quote(project_name)}",
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
