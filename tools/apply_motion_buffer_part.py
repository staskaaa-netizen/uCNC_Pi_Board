"""Replace U42/U43 with the wide-body SN74AC541DW assembly variant."""

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
REFERENCES = {"U42", "U43"}
OLD_VALUE = "SN74AC541DW"
NEW_VALUE = "MC74AC541DWR2G"
NEW_MPN = "MC74AC541DWR2G"
NEW_MANUFACTURER = "onsemi"


def update_schematics() -> list[str]:
    remaining = set(REFERENCES)
    updated_files = []
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        text = path.read_text(encoding="utf-8")
        original = text
        for reference in REFERENCES:
            if f'(property "Reference" "{reference}"' not in text:
                continue
            text = set_symbol_property(
                text,
                reference,
                "Value",
                NEW_VALUE,
            )
            text = set_symbol_property(
                text,
                reference,
                "MPN",
                NEW_MPN,
            )
            text = set_symbol_property(
                text,
                reference,
                "Manufacturer",
                NEW_MANUFACTURER,
            )
            remaining.discard(reference)
        if text != original:
            path.write_text(text, encoding="utf-8")
            updated_files.append(path.name)
    if remaining:
        raise RuntimeError(f"Missing schematic references: {sorted(remaining)}")
    return updated_files


def update_board() -> int:
    board = pcbnew.LoadBoard(str(BOARD))
    updated = 0
    for footprint in board.GetFootprints():
        if footprint.GetReference() in REFERENCES:
            if footprint.GetValue() != OLD_VALUE:
                raise RuntimeError(
                    f"{footprint.GetReference()} has unexpected value "
                    f"{footprint.GetValue()}"
                )
            footprint.SetValue(NEW_VALUE)
            updated += 1
    if updated != len(REFERENCES):
        raise RuntimeError(f"Updated {updated} board parts; expected 2")
    pcbnew.SaveBoard(str(BOARD), board)
    return updated


def update_placement_manifest() -> None:
    csv_path = HARDWARE / "component-placement-manifest.csv"
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    fieldnames = list(rows[0]) if rows else []
    for row in rows:
        if row["reference"] in REFERENCES:
            row["value"] = NEW_VALUE
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
        if component["reference"] in REFERENCES:
            component["value"] = NEW_VALUE
    json_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(
        {
            "references": sorted(REFERENCES),
            "old_value": OLD_VALUE,
            "new_value": NEW_VALUE,
            "manufacturer": NEW_MANUFACTURER,
        }
    )
    if not args.apply:
        return
    print("Updated schematics:", ", ".join(update_schematics()))
    print("Updated PCB parts:", update_board())
    update_placement_manifest()
    print("Updated placement manifest CSV and JSON")


if __name__ == "__main__":
    main()
