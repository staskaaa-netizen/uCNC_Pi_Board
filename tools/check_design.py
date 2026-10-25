"""Inspect schematic label collisions, netlist connectivity and ERC results."""

from __future__ import annotations

import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"


def check_labels() -> None:
    pattern = re.compile(
        r'\(global_label "([^"]+)"\n\s*'
        r"\(shape [^\n]+\)\n\s*"
        r"\(at ([^ ]+) ([^ ]+)"
    )
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        labels = pattern.findall(path.read_text(encoding="utf-8"))
        positions: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
        for name, x, y in labels:
            positions[(x, y)].add(name)
        collisions = {
            position: names for position, names in positions.items() if len(names) > 1
        }
        print(f"{path.name}: {len(labels)} labels, {len(collisions)} coordinate collisions")
        for position, names in collisions.items():
            print(f"  {position}: {sorted(names)}")


def check_netlist() -> None:
    path = HARDWARE / "motherboard.net.xml"
    if not path.exists():
        print("netlist missing")
        return
    root = ET.parse(path).getroot()
    components = root.findall("./components/comp")
    nets = root.findall("./nets/net")
    references = [component.get("ref") for component in components]
    duplicates = sorted(
        reference
        for reference in set(references)
        if sum(item == reference for item in references) > 1
    )
    single = [
        (net.get("name"), len(net.findall("node")))
        for net in nets
        if len(net.findall("node")) < 2
        and not net.get("name", "").startswith("unconnected-")
    ]
    print(f"netlist: {len(components)} components, {len(nets)} nets")
    print(f"duplicate references: {duplicates}")
    print(f"single-node nets: {single}")


def check_erc() -> None:
    path = HARDWARE / "erc.json"
    if not path.exists():
        print("ERC report missing")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    violations = [
        violation
        for sheet in data.get("sheets", [])
        for violation in sheet.get("violations", [])
    ]
    counts = collections.Counter(
        (violation["severity"], violation["type"], violation["description"])
        for violation in violations
    )
    print(f"ERC violations: {len(violations)}")
    for (severity, kind, description), count in counts.items():
        print(f"  {severity:7} {count:3} {kind}: {description}")


if __name__ == "__main__":
    check_labels()
    check_netlist()
    check_erc()
