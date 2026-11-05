"""Set rail-appropriate voltage ratings for the 22 uF 1210 capacitors."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
BOARD = HARDWARE / "motherboard.kicad_pcb"

RATINGS = {
    # 24 V input and isolated field-input rails: retain 50 V parts.
    "C3": "50V",
    "C5": "50V",
    "C100": "50V",
    "C107": "50V",
    # 5 V and 3.3 V rails.
    "C6": "10V",
    "C10": "10V",
    "C11": "10V",
    "C69": "10V",
    "C88": "10V",
    "C90": "10V",
    # 12 V rails.
    "C101": "25V",
    "C109": "25V",
    "C110": "25V",
    "C111": "25V",
}


def set_symbol_property(
    text: str,
    reference: str,
    property_name: str,
    value: str,
) -> str:
    marker = f'(property "Reference" "{reference}"'
    position = text.find(marker)
    if position < 0:
        return text
    block_start = text.rfind("\n\t(symbol", 0, position)
    block_end = text.find("\n\t(symbol", position)
    if block_start < 0:
        raise RuntimeError(f"{reference}: symbol block start not found")
    if block_end < 0:
        block_end = len(text)
    block = text[block_start:block_end]
    pattern = re.compile(
        rf'(\(property "{re.escape(property_name)}" ")[^"]*(")'
    )
    updated, count = pattern.subn(
        lambda match: match.group(1) + value + match.group(2),
        block,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"{reference}: {property_name} property not found")
    return text[:block_start] + updated + text[block_end:]


def update_schematics() -> list[str]:
    remaining = set(RATINGS)
    updated_files = []
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        text = path.read_text(encoding="utf-8")
        original = text
        for reference, voltage in RATINGS.items():
            if f'(property "Reference" "{reference}"' not in text:
                continue
            text = set_symbol_property(
                text,
                reference,
                "Value",
                f"22uF {voltage}",
            )
            text = set_symbol_property(
                text,
                reference,
                "MPN",
                f"CL32 series 1210 X7R 22uF {voltage}",
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
        reference = footprint.GetReference()
        voltage = RATINGS.get(reference)
        if voltage and footprint.GetValue().startswith("22uF"):
            footprint.SetValue(f"22uF {voltage}")
            updated += 1
    if updated != len(RATINGS):
        raise RuntimeError(
            f"Updated {updated} PCB capacitors; expected {len(RATINGS)}"
        )
    pcbnew.SaveBoard(str(BOARD), board)
    return updated


def update_placement_manifest() -> None:
    csv_path = HARDWARE / "component-placement-manifest.csv"
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))
    fieldnames = list(rows[0]) if rows else []
    for row in rows:
        voltage = RATINGS.get(row["reference"])
        if voltage:
            row["value"] = f"22uF {voltage}"
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
        voltage = RATINGS.get(component["reference"])
        if voltage:
            component["value"] = f"22uF {voltage}"
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
            reference: rating
            for reference, rating in sorted(RATINGS.items())
        }
    )
    if not args.apply:
        return
    print("Updated schematics:", ", ".join(update_schematics()))
    print("Updated PCB capacitors:", update_board())
    update_placement_manifest()
    print("Updated placement manifest CSV and JSON")


if __name__ == "__main__":
    main()
