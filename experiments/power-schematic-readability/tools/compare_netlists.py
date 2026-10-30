"""Compare a generated KiCad S-expression netlist to the source sheet contract."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from kicad_sexpr import child, children, parse_file


def generated_design(path: Path):
    root = parse_file(path)
    components_node = child(root, "components")
    nets_node = child(root, "nets")
    if components_node is None or nets_node is None:
        raise RuntimeError(f"Not a KiCad netlist: {path}")
    components = {}
    for comp in children(components_node, "comp"):
        ref_node = child(comp, "ref")
        if ref_node is None:
            continue
        ref = str(ref_node[1])
        components[ref] = {
            "value": str(child(comp, "value")[1]) if child(comp, "value") else "",
            "footprint": (
                str(child(comp, "footprint")[1]) if child(comp, "footprint") else ""
            ),
        }
    nets = {}
    for net in children(nets_node, "net"):
        name_node = child(net, "name")
        name = str(name_node[1]) if name_node else "<unnamed>"
        nodes = []
        for node in children(net, "node"):
            ref = child(node, "ref")
            pin = child(node, "pin")
            if ref is not None and pin is not None:
                nodes.append((str(ref[1]), str(pin[1])))
        nets[name] = frozenset(nodes)
    return components, nets


def canonical(nets: dict[str, frozenset[tuple[str, str]]]) -> Counter:
    return Counter(nets.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    source = json.loads(args.source.read_text(encoding="utf-8"))
    source_components = {
        part["ref"]: {
            "value": part["value"],
            "footprint": part["footprint"],
        }
        for part in source["parts"]
    }
    source_nets = {
        net["name"]: frozenset(
            (str(ref), str(pin)) for ref, pin in net["connections"]
        )
        for net in source["nets"]
    }
    generated_components, generated_nets = generated_design(args.generated)
    normalized_generated_nets = {
        (name[1:] if name.startswith("/") and not name.startswith("//") else name): nodes
        for name, nodes in generated_nets.items()
        if not (
            name.startswith("unconnected-")
            and len(nodes) == 1
        )
    }

    missing_components = sorted(set(source_components) - set(generated_components))
    extra_components = sorted(set(generated_components) - set(source_components))
    value_changes = []
    footprint_changes = []
    for ref in sorted(set(source_components) & set(generated_components)):
        expected = source_components[ref]
        actual = generated_components[ref]
        if expected["value"] != actual["value"]:
            value_changes.append(
                {"ref": ref, "source": expected["value"], "generated": actual["value"]}
            )
        if expected["footprint"] != actual["footprint"]:
            footprint_changes.append(
                {
                    "ref": ref,
                    "source": expected["footprint"],
                    "generated": actual["footprint"],
                }
            )

    missing_nets = sorted(set(source_nets) - set(normalized_generated_nets))
    extra_nets = sorted(set(normalized_generated_nets) - set(source_nets))
    changed_connections = []
    for name in sorted(set(source_nets) & set(normalized_generated_nets)):
        expected = source_nets[name]
        actual = normalized_generated_nets[name]
        if expected != actual:
            changed_connections.append(
                {
                    "net": name,
                    "missing_nodes": [
                        f"{ref}.{pin}" for ref, pin in sorted(expected - actual)
                    ],
                    "extra_nodes": [
                        f"{ref}.{pin}" for ref, pin in sorted(actual - expected)
                    ],
                }
            )

    source_partition = canonical(source_nets)
    generated_partition = canonical(normalized_generated_nets)
    source_nodes = set().union(*source_nets.values()) if source_nets else set()
    generated_nodes = set().union(*generated_nets.values()) if generated_nets else set()
    report = {
        "source_netlist": str(args.source),
        "generated_netlist": str(args.generated),
        "source_component_count": len(source_components),
        "generated_component_count": len(generated_components),
        "source_net_count": len(source_nets),
        "generated_net_count": len(generated_nets),
        "root_local_label_prefix_normalized": any(
            name.startswith("/") for name in generated_nets
        ),
        "missing_components": missing_components,
        "extra_components": extra_components,
        "value_changes": value_changes,
        "footprint_changes": footprint_changes,
        "missing_net_names": missing_nets,
        "extra_net_names": extra_nets,
        "changed_named_connections": changed_connections,
        "source_nodes_missing_from_generated": [
            f"{ref}.{pin}" for ref, pin in sorted(source_nodes - generated_nodes)
        ],
        "generated_nodes_not_in_source": [
            f"{ref}.{pin}" for ref, pin in sorted(generated_nodes - source_nodes)
        ],
        "generated_connection_groups": {
            name: [f"{ref}.{pin}" for ref, pin in sorted(nodes)]
            for name, nodes in sorted(generated_nets.items())
        },
        "netlist_partition_identical": source_partition == generated_partition,
        "named_netlists_identical": (
            not missing_components
            and not extra_components
            and source_nets == normalized_generated_nets
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
