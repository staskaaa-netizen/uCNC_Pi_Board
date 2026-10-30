"""Extract the power-sheet subdesign from KiCad's authoritative XML netlist.

The source schematic and PCB are never opened for writing. The resulting JSON
uses schemagen's documented input format and also serves as the connectivity
contract for the independent Python-layout experiment.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


RAIL_RE = re.compile(
    r"^(GND\w*|AGND|PGND|DGND|VBUS|VCC\d*|VDD\d*|VIN\w*|"
    r"[+-]?\d+V\d*|[+-]\d+V\d*|3V3\w*|5V\w*|12V\w*)$"
)


def child_text(node: ET.Element | None, tag: str, default: str = "") -> str:
    if node is None:
        return default
    child = node.find(tag)
    return (child.text or default) if child is not None else default


def property_value(node: ET.Element, name: str) -> str:
    for prop in node.findall("./property"):
        if prop.get("name") == name:
            return prop.get("value", "")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--netlist", required=True, type=Path)
    parser.add_argument("--sheet", default="power.kicad_sch")
    parser.add_argument("--outdir", required=True, type=Path)
    args = parser.parse_args()

    root = ET.parse(args.netlist).getroot()
    library: dict[tuple[str, str], ET.Element] = {}
    for libpart in root.findall("./libparts/libpart"):
        library[(libpart.get("lib", ""), libpart.get("part", ""))] = libpart

    power_components: dict[str, dict] = {}
    for comp in root.findall("./components/comp"):
        if property_value(comp, "Sheetfile") != args.sheet:
            continue
        ref = comp.get("ref", "")
        source = comp.find("./libsource")
        lib = source.get("lib", "") if source is not None else ""
        part_name = source.get("part", "") if source is not None else ""
        part_desc = source.get("description", "") if source is not None else ""
        libpart = library.get((lib, part_name))
        pins = []
        if libpart is not None:
            for pin in libpart.findall("./pins/pin"):
                pins.append(
                    {
                        "number": pin.get("num", ""),
                        "name": pin.get("name", "~") or "~",
                        "type": pin.get("type", "passive") or "passive",
                    }
                )
        power_components[ref] = {
            "ref": ref,
            "value": child_text(comp, "value", "?"),
            "footprint": child_text(comp, "footprint"),
            "lib": lib,
            "part": part_name,
            "description": part_desc,
            "datasheet": child_text(source, "datasheet") if source is not None else "",
            "pins": pins,
        }

    nets: dict[str, dict] = {}
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        local_nodes = [
            [node.get("ref", ""), node.get("pin", "")]
            for node in net.findall("./node")
            if node.get("ref", "") in power_components
        ]
        if local_nodes:
            nets[name] = {
                "name": name,
                "is_power": bool(RAIL_RE.match(name)),
                "connections": sorted(local_nodes, key=lambda item: (item[0], item[1])),
            }

    pin_contract = defaultdict(dict)
    for net_name, net in nets.items():
        for ref, pin in net["connections"]:
            pin_contract[ref][pin] = net_name

    design = {
        "title": f"LeanCam NCC RP2350B - {Path(args.sheet).stem}",
        "parts": list(sorted(power_components.values(), key=lambda item: item["ref"])),
        "nets": list(nets.values()),
    }
    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.sheet).stem
    (args.outdir / f"source-{stem}.json").write_text(
        json.dumps(design, indent=2) + "\n", encoding="utf-8"
    )
    (args.outdir / f"source-{stem}-pin-contract.json").write_text(
        json.dumps(dict(sorted(pin_contract.items())), indent=2) + "\n",
        encoding="utf-8",
    )

    with (args.outdir / f"source-{stem}-components.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["Reference", "Value", "LibId", "PinCount"])
        for part in sorted(power_components.values(), key=lambda item: item["ref"]):
            writer.writerow(
                [
                    part["ref"],
                    part["value"],
                    f'{part["lib"]}:{part["part"]}',
                    len(part["pins"]),
                ]
            )

    with (args.outdir / f"source-{stem}-nets.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(["Net", "NodeCount", "Connections"])
        for net in sorted(nets.values(), key=lambda item: item["name"]):
            writer.writerow(
                [
                    net["name"],
                    len(net["connections"]),
                    " ".join(f"{ref}.{pin}" for ref, pin in net["connections"]),
                ]
            )

    print(
        json.dumps(
            {
                "components": len(power_components),
                "nets": len(nets),
                "pin_connections": sum(len(value) for value in pin_contract.values()),
                "unconnected_declared_pins": sum(
                    len(part["pins"]) - len(pin_contract.get(part["ref"], {}))
                    for part in power_components.values()
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
