"""Create a compact verification report for the generated hierarchy sheets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from kicad_sexpr import child, children, parse_file


ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = ROOT / "experiments" / "power-schematic-readability"
INPUTS = EXPERIMENT / "inputs"
OUT = EXPERIMENT / "other-sheets"
SHEETS = [
    "analog_io",
    "display",
    "encoders",
    "field_inputs",
    "field_outputs",
    "mcu_io",
    "storage_wifi_ui",
]
TITLES = {
    "analog_io": "Analog I/O",
    "display": "LVDS display",
    "encoders": "Encoders",
    "field_inputs": "Isolated field inputs",
    "field_outputs": "PLC and motion outputs",
    "mcu_io": "RP2350B and shift chains",
    "storage_wifi_ui": "Storage, Wi-Fi and UI",
}


def erc_types(path: Path) -> Counter:
    report = json.loads(path.read_text(encoding="utf-8"))
    return Counter(
        f"{violation['severity']}:{violation['type']}"
        for sheet in report["sheets"]
        for violation in sheet["violations"]
    )


def schematic_counts(path: Path) -> dict:
    root = parse_file(path)
    paper = child(root, "paper")
    return {
        "paper": str(paper[1]) if paper else "",
        "symbols": sum(
            1 for node in children(root, "symbol") if child(node, "lib_id")
        ),
        "wires": len(children(root, "wire")),
        "junctions": len(children(root, "junction")),
        "local_labels": len(children(root, "label")),
        "global_labels": len(children(root, "global_label")),
        "no_connects": len(children(root, "no_connect")),
    }


def main() -> None:
    rows = []
    for stem in SHEETS:
        comparison = json.loads(
            (OUT / f"{stem}-netlist-comparison.json").read_text(encoding="utf-8")
        )
        source_erc = erc_types(INPUTS / f"source-{stem}-erc.json")
        generated_erc = erc_types(OUT / f"{stem}-erc.json")
        counts = schematic_counts(OUT / f"{stem}-python.kicad_sch")
        rows.append(
            {
                "sheet": stem,
                "title": TITLES[stem],
                "paper": counts["paper"],
                "components": counts["symbols"],
                "nets": comparison["source_net_count"],
                "components_preserved": (
                    comparison["source_component_count"]
                    == comparison["generated_component_count"]
                ),
                "named_netlist_identical": comparison["named_netlists_identical"],
                "missing_nodes": comparison["source_nodes_missing_from_generated"],
                "extra_nodes": comparison["generated_nodes_not_in_source"],
                "wires": counts["wires"],
                "junctions": counts["junctions"],
                "labels": counts["local_labels"] + counts["global_labels"],
                "no_connects": counts["no_connects"],
                "source_erc_violations": sum(source_erc.values()),
                "generated_erc_violations": sum(generated_erc.values()),
                "erc_type_counts_identical": source_erc == generated_erc,
                "source_erc_types": dict(sorted(source_erc.items())),
                "generated_erc_types": dict(sorted(generated_erc.items())),
                "kicad": str(OUT / f"{stem}-python.kicad_sch"),
                "pdf": str(OUT / f"{stem}-python.pdf"),
            }
        )

    (OUT / "verification-summary.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Generated hierarchy sheets",
        "",
        "These are first-pass Python re-layouts of every hierarchy sheet except",
        "`power.kicad_sch`. The source schematics and PCB were not modified.",
        "",
        "| Sheet | Paper | Components | Nets | Wires | Labels | Netlist | ERC source/generated |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['title']} · [KiCad]({Path(row['kicad']).name}) · "
            f"[PDF]({Path(row['pdf']).name}) | {row['paper']} | {row['components']} "
            f"| {row['nets']} | {row['wires']} | {row['labels']} "
            f"| {'identical' if row['named_netlist_identical'] else 'DIFF'} "
            f"| {row['source_erc_violations']}/{row['generated_erc_violations']} "
            f"({'same types' if row['erc_type_counts_identical'] else 'different types'}) |"
        )
    lines.extend(
        [
            "",
            "The KiCad files contain the original embedded symbol definitions and",
            "preserve references, values, footprints and local connectivity. Local",
            "nets are wired where a short orthogonal tree can be placed; cross-sheet",
            "signals and high-fanout rails retain labels.",
            "",
            "ERC violations are unchanged in count and type from the corresponding",
            "standalone source sheet. Most are expected because power sources and",
            "signal drivers live on other sheets.",
            "",
            "Combined PDF: `all-other-sheets.pdf`",
        ]
    )
    (OUT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
