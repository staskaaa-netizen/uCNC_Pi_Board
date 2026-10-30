"""Inventory source hierarchy sheets and their local electrical subgraphs."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from kicad_sexpr import child, children, parse_file


def property_value(node: ET.Element, name: str) -> str:
    for prop in node.findall("./property"):
        if prop.get("name") == name:
            return prop.get("value", "")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", required=True, type=Path)
    parser.add_argument("--hardware", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    by_sheet: dict[str, list[str]] = defaultdict(list)
    for comp in root.findall("./components/comp"):
        sheet = property_value(comp, "Sheetfile")
        if sheet:
            by_sheet[sheet].append(comp.get("ref", ""))

    rows = []
    for filename, refs in sorted(by_sheet.items(), key=lambda item: item[0]):
        ref_set = set(refs)
        connected_nodes = 0
        net_memberships = 0
        local_nets = set()
        for net in root.findall("./nets/net"):
            local = [
                node
                for node in net.findall("./node")
                if node.get("ref", "") in ref_set
            ]
            if local:
                local_nets.add(net.get("name", ""))
                connected_nodes += len(local)
                net_memberships += 1
        path = args.hardware / filename
        source = parse_file(path)
        symbol_instances = [
            node
            for node in children(source, "symbol")
            if child(node, "lib_id") is not None
        ]
        paper = child(source, "paper")
        rows.append(
            {
                "sheet": filename,
                "paper": str(paper[1]) if paper else "",
                "components": len(refs),
                "local_nets": len(local_nets),
                "connected_pins": connected_nodes,
                "net_endpoints": net_memberships,
                "wires": len(children(source, "wire")),
                "junctions": len(children(source, "junction")),
                "local_labels": len(children(source, "label")),
                "global_labels": len(children(source, "global_label")),
                "symbol_instances_parsed": len(symbol_instances),
            }
        )
    args.out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
