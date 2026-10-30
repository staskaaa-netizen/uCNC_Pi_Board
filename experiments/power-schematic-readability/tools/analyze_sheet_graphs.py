"""Report signal-connected clusters for each extracted hierarchy sheet."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


RAIL_RE = re.compile(
    r"^(?:GND\w*|AGND|PGND|DGND|VBUS|VCC\d*|VDD\d*|VIN\w*|"
    r"[+-]?\d+V\d*|[+-]\d+V\d*|3V3\w*|5V\w*|12V\w*)$"
)


def clusters(design: dict) -> list[list[str]]:
    refs = {part["ref"] for part in design["parts"]}
    adjacency = {ref: set() for ref in refs}
    for net in design["nets"]:
        if net["is_power"] or len(net["connections"]) < 2:
            continue
        members = [ref for ref, _pin in net["connections"] if ref in refs]
        for ref in members:
            adjacency[ref].update(item for item in members if item != ref)
    result = []
    unseen = set(refs)
    while unseen:
        seed = min(unseen)
        stack = [seed]
        unseen.remove(seed)
        group = []
        while stack:
            ref = stack.pop()
            group.append(ref)
            for other in adjacency[ref]:
                if other in unseen:
                    unseen.remove(other)
                    stack.append(other)
        result.append(sorted(group))
    return sorted(result, key=lambda group: (-len(group), group[0]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = {}
    for path in sorted(args.inputs.glob("source-*.json")):
        if "pin-contract" in path.name or path.name == "source-power.json":
            continue
        design = json.loads(path.read_text(encoding="utf-8"))
        if "parts" not in design or "nets" not in design:
            continue
        groups = clusters(design)
        report[path.stem.removeprefix("source-")] = {
            "components": len(design["parts"]),
            "nets": len(design["nets"]),
            "clusters": groups,
            "cluster_sizes": [len(group) for group in groups],
            "net_size_histogram": {
                str(size): sum(
                    1 for net in design["nets"] if len(net["connections"]) == size
                )
                for size in sorted({len(net["connections"]) for net in design["nets"]})
            },
        }
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for sheet, data in report.items():
        print(
            f"{sheet:18s} components={data['components']:3d} "
            f"clusters={len(data['clusters']):3d} sizes={data['cluster_sizes']} "
            f"net_sizes={data['net_size_histogram']}"
        )


if __name__ == "__main__":
    main()
