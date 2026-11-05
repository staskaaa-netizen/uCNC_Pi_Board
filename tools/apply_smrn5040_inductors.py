"""Replace L1/L2 with the selected 5x5 mm SMNR5040 inductors."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

import pcbnew

from apply_capacitor_voltage_ratings import set_symbol_property


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
BOARD = HARDWARE / "motherboard.kicad_pcb"
TARGETS = {
    "L1": {
        "value": "22uH 1.4A",
        "footprint": "LeanCam:L_SXN_SMNR5040",
        "mpn": "SMNR5040-220MT",
    },
    "L2": {
        "value": "47uH 0.9A",
        "footprint": "LeanCam:L_SXN_SMNR5040",
        "mpn": "SMNR5040-470MT",
    },
}
MANUFACTURER = "SXN (Shun Xiang Nuo Elec)"


def update_schematics() -> list[str]:
    remaining = set(TARGETS)
    updated_files = []
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        text = path.read_text(encoding="utf-8")
        original = text
        for reference, target in TARGETS.items():
            if f'(property "Reference" "{reference}"' not in text:
                continue
            text = set_symbol_property(
                text,
                reference,
                "Value",
                target["value"],
            )
            text = set_symbol_property(
                text,
                reference,
                "Footprint",
                target["footprint"],
            )
            text = set_symbol_property(
                text,
                reference,
                "MPN",
                target["mpn"],
            )
            text = set_symbol_property(
                text,
                reference,
                "Manufacturer",
                MANUFACTURER,
            )
            remaining.discard(reference)
        if text != original:
            path.write_text(text, encoding="utf-8")
            updated_files.append(path.name)
    if remaining:
        raise RuntimeError(f"Missing schematic references: {sorted(remaining)}")
    return updated_files


def update_board_values() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    updated = 0
    for footprint in board.GetFootprints():
        target = TARGETS.get(footprint.GetReference())
        if target:
            footprint.SetValue(target["value"])
            updated += 1
    if updated != len(TARGETS):
        raise RuntimeError(f"Updated {updated} PCB inductors; expected 2")
    pcbnew.SaveBoard(str(BOARD), board)
    return updated


def update_placement_manifest() -> None:
    csv_path = HARDWARE / "component-placement-manifest.csv"
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    fieldnames = list(rows[0]) if rows else []
    for row in rows:
        target = TARGETS.get(row["reference"])
        if target:
            row["value"] = target["value"]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    csv_path.write_text(buffer.getvalue(), encoding="utf-8")

    json_path = HARDWARE / "component-placement-manifest.json"
    manifest = json.loads(json_path.read_text(encoding="utf-8"))
    for component in manifest["components"]:
        target = TARGETS.get(component["reference"])
        if target:
            component["value"] = target["value"]
    json_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(TARGETS)
    if not args.apply:
        return
    print("Updated schematics:", ", ".join(update_schematics()))
    print("Updated PCB values:", update_board_values())
    update_placement_manifest()
    print("Updated placement manifest CSV and JSON")


if __name__ == "__main__":
    main()
