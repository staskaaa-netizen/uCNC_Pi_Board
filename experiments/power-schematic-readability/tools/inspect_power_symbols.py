"""Print source-symbol pins and instance placements for layout planning."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from kicad_sexpr import (
    child,
    children,
    number,
    parse_file,
    property_value,
)


def centered(value: float) -> float:
    return 0.0 if abs(value) < 1e-9 else value


def world_pin(x: float, y: float, angle: float, px: float, py: float):
    radians = math.radians(angle)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        centered(x + px * cosine - py * sine),
        centered(y - (px * sine + py * cosine)),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schematic", type=Path)
    args = parser.parse_args()
    root = parse_file(args.schematic)
    library_node = child(root, "lib_symbols")
    if library_node is None:
        raise RuntimeError("No lib_symbols block")

    pin_sets = {}
    for symbol in children(library_node, "symbol"):
        lib_id = symbol[1]
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
                pin_number = str(number_node[1])
                pins[pin_number] = {
                    "x": float(at[1]),
                    "y": float(at[2]),
                    "angle": float(at[3]) if len(at) > 3 else 0.0,
                    "name": str(name_node[1]) if name_node else "",
                }
        pin_sets[lib_id] = pins

    for symbol in children(root, "symbol"):
        lib_node = child(symbol, "lib_id")
        at = child(symbol, "at")
        if lib_node is None or at is None:
            continue
        ref = property_value(symbol, "Reference")
        value = property_value(symbol, "Value")
        x, y = float(at[1]), float(at[2])
        angle = float(at[3]) if len(at) > 3 else 0.0
        pins = pin_sets[lib_node[1]]
        world = []
        for pin_number, pin in sorted(
            pins.items(), key=lambda item: (0, int(item[0])) if item[0].isdigit() else (1, item[0])
        ):
            wx, wy = world_pin(x, y, angle, pin["x"], pin["y"])
            world.append(f"{pin_number}:{pin['name']}@{wx:.2f},{wy:.2f}")
        print(
            f"{ref:5s} {value:15.15s} {lib_node[1]:35.35s} "
            f"at=({x:.2f},{y:.2f},{angle:g}) pins={' '.join(world)}"
        )


if __name__ == "__main__":
    main()
