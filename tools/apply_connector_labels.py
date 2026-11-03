"""Set unambiguous connector values without changing pad-to-net assignments."""

from __future__ import annotations

import re
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
BOARD = HARDWARE / "motherboard.kicad_pcb"

CONNECTOR_VALUES = {
    "J1": "24+ GND",
    "J2": "BL12+ PLC_0V",
    "J5": "ESTOP PLC_0V",
    "J7": "I01 I02 I03 I04 I05 I06 I07 I08",
    "J8": "I09 I10 I11 I12 I13 I14 I15 I16",
    "J10": "EN3 STP0 DIR0",
    "J11": "EN3 STP1 DIR1",
    "J12": "D01 D02 D03 D04 D05 D06 D07 D08",
    "J13": "+5V A0 B0 Z0 GND",
    "J14": "+5V A1 B1 Z1 GND",
    "J15": "+5V A2 B2 Z2 GND",
    "J18": "SDA SCL 3V3 5V GND",
    "J24": "GND AI0 AI1 AI2 AI3",
    "J25": "GND AO0 AO1 AO2 AO3",
    "J28": "EN3 STP2 DIR2",
    "J29": "EN4 STP3 DIR3",
    "J30": "EN4 STP6 DIR6",
    "J32": "D09 D10 D11 D12 D13 D14 D15 D16",
    "J33": "PLC24+ PLC_0V",
    "J40": "GND ERR0 Z0",
    "J41": "GND ERR1 Z1",
    "J42": "GND ERR2 Z2",
    "J43": "GND ERR3 Z3",
    "J45": "PLC24+ PLC_0V",
    "J46": "EN4 STP5 DIR5",
    "J47": "EN4 STP4 DIR4",
    "J48": "GND ERR6 Z6",
    "J49": "GND ERR5 Z5",
    "J50": "GND ERR4 Z4",
    "J51": "3V3 GND IO4 IO5 IO6 IO7 IO8",
}

BOARD_VALUE_OVERRIDES = {
    "J1": "GND 24+",
    "J2": "PLC_0V BL12+",
    "J45": "PLC_0V PLC24+",
    "J10": "DIR0 STP0 EN3",
    "J11": "DIR1 STP1 EN3",
    "J28": "DIR2 STP2 EN3",
    "J29": "DIR3 STP3 EN4",
    "J47": "DIR4 STP4 EN4",
    "J46": "DIR5 STP5 EN4",
    "J30": "DIR6 STP6 EN4",
}

BOARD_TEXT_ANGLES = {
    "J1": 0.0,
    "J2": 0.0,
    "J5": 0.0,
    "J7": 0.0,
    "J8": 0.0,
    "J10": 270.0,
    "J11": 270.0,
    "J12": 180.0,
    "J13": 0.0,
    "J14": 0.0,
    "J15": 0.0,
    "J18": 90.0,
    "J24": 90.0,
    "J25": 90.0,
    "J28": 270.0,
    "J29": 270.0,
    "J30": 270.0,
    "J32": 180.0,
    "J33": 0.0,
    "J40": 90.0,
    "J41": 90.0,
    "J42": 90.0,
    "J43": 90.0,
    "J45": 0.0,
    "J46": 270.0,
    "J47": 270.0,
    "J48": 90.0,
    "J49": 90.0,
    "J50": 90.0,
    "J51": 270.0,
}


def set_symbol_value(text: str, reference: str, value: str) -> str:
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
    pattern = re.compile(r'(\(property "Value" ")[^"]*(")')
    updated, count = pattern.subn(
        lambda match: match.group(1) + value + match.group(2),
        block,
        count=1,
    )
    if count != 1:
        raise RuntimeError(f"{reference}: Value property not found")
    return text[:block_start] + updated + text[block_end:]


def main() -> None:
    updated_schematics = {}
    missing = set(CONNECTOR_VALUES)
    for path in sorted(HARDWARE.glob("*.kicad_sch")):
        text = path.read_text(encoding="utf-8")
        changes = []
        for reference, value in CONNECTOR_VALUES.items():
            if f'(property "Reference" "{reference}"' in text:
                missing.discard(reference)
            before = text
            text = set_symbol_value(text, reference, value)
            if text != before:
                changes.append(reference)
        if changes:
            path.write_text(text, encoding="utf-8")
            updated_schematics[path.name] = changes
    if missing:
        raise SystemExit(f"Connector symbols not found in schematics: {sorted(missing)}")

    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    board_missing = sorted(set(CONNECTOR_VALUES) - set(footprints))
    if board_missing:
        raise SystemExit(f"Connector footprints not found: {board_missing}")
    for reference, value in CONNECTOR_VALUES.items():
        footprint = footprints[reference]
        footprint.SetValue(BOARD_VALUE_OVERRIDES.get(reference, value))
        footprint.Value().SetTextAngleDegrees(BOARD_TEXT_ANGLES[reference])
    pcbnew.SaveBoard(str(BOARD), board)

    for filename, references in updated_schematics.items():
        print(f"{filename}: {', '.join(references)}")
    print(f"board: {', '.join(sorted(CONNECTOR_VALUES))}")


if __name__ == "__main__":
    main()
