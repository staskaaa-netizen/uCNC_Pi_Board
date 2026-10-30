"""Summarize visual/electrical structure of a KiCad schematic text file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kicad_sexpr import child, children, parse_file


def wire_length(nodes) -> float:
    total = 0.0
    for node in nodes:
        if not isinstance(node, list) or not node or node[0] != "wire":
            continue
        points = child(node, "pts")
        if points is None:
            continue
        xy = children(points, "xy")
        if len(xy) == 2:
            total += abs(float(xy[0][1]) - float(xy[1][1]))
            total += abs(float(xy[0][2]) - float(xy[1][2]))
    return round(total, 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    root = parse_file(args.source)
    symbols = [
        node
        for node in children(root, "symbol")
        if child(node, "lib_id") is not None
    ]
    wires = children(root, "wire")
    junctions = children(root, "junction")
    labels = children(root, "label")
    global_labels = children(root, "global_label")
    no_connects = children(root, "no_connect")
    texts = children(root, "text")
    report = {
        "label": args.label or args.source.stem,
        "schematic": str(args.source),
        "version": str(child(root, "version")[1]),
        "symbol_instances": len(symbols),
        "wires": len(wires),
        "wire_segments": len(wires),
        "wire_length_mm": wire_length(root),
        "junctions": len(junctions),
        "local_labels": len(labels),
        "global_labels": len(global_labels),
        "unique_label_names": len(
            {
                str(node[1])
                for node in labels + global_labels
                if len(node) > 1
            }
        ),
        "no_connects": len(no_connects),
        "text_annotations": len(texts),
    }
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
