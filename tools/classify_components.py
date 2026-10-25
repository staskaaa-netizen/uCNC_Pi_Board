"""Generate a placement manifest from the current netlist and PCB."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
NETLIST = ROOT / "hardware" / "motherboard.net.xml"
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
CSV_OUTPUT = ROOT / "hardware" / "component-placement-manifest.csv"
JSON_OUTPUT = ROOT / "hardware" / "component-placement-manifest.json"

POWER_SUPPLIES = {
    "+3V3", "+3V3_A", "+3V3_SD", "+3V3_WIFI", "+5V", "+5V_HDMI",
    "+5V_ENC", "+12V_AO", "VIN_PROT", "VCC5",
}
DECOUPLING_IC = {
    "C22": "U6", "C23": "U7", "C24": "U8", "C25": "U9",
    "C26": "U10", "C27": "U11", "C28": "U12", "C29": "U13",
    "C53": "U24", "C54": "U25", "C55": "U26", "C56": "U27",
    "C57": "U28",
    "C10": "U2 input", "C76": "U2 input",
    "C13": "U2 output", "C90": "U2 output",
    "C88": "U34 input", "C89": "U34 input",
    "C69": "U34 output", "C70": "U34 output",
    "C3": "U1 input", "C4": "U1 input", "C5": "U1 input",
    "C6": "U1 output", "C7": "U1 output", "C8": "U1 output", "C11": "U1 output",
    "C86": "U1 BOOT", "C91": "U1 VCC",
}
CAP_ROLE_OVERRIDES = {
    "C1": ("bulk input capacitor", "VIN_FUSED input filter"),
    "C2": ("input bypass capacitor", "VIN_FUSED input filter"),
    "C3": ("bulk input capacitor", "U1 input"),
    "C4": ("decoupling capacitor", "U1 input"),
    "C5": ("bulk input capacitor", "U1 input"),
    "C6": ("bulk output capacitor", "U1 output"),
    "C7": ("decoupling capacitor", "U1 output"),
    "C8": ("bulk output capacitor", "U1 output"),
    "C10": ("bulk input capacitor", "U2 input"),
    "C11": ("bulk output capacitor", "U1 output"),
    "C13": ("decoupling capacitor", "U2 output"),
    "C14": ("bulk rail capacitor", "+3V3_A filter"),
    "C15": ("decoupling capacitor", "+3V3_A filter"),
    "C16": ("bulk rail capacitor", "+5V rail"),
    "C17": ("decoupling capacitor", "+5V rail"),
    "C21": ("reset capacitor", "retired"),
    "C55": ("output clamp capacitor", "U26 DO_COM"),
    "C56": ("output clamp capacitor", "U27 DO_COM"),
    "C67": ("bulk rail capacitor", "SD +3V3_SD"),
    "C68": ("decoupling capacitor", "SD +3V3_SD"),
    "C69": ("bulk output capacitor", "U34 output"),
    "C70": ("decoupling capacitor", "U34 output"),
    "C71": ("bulk rail capacitor", "HDMI +5V"),
    "C72": ("decoupling capacitor", "HDMI +5V"),
    "C76": ("decoupling capacitor", "U2 input"),
    "C77": ("decoupling capacitor", "+5V rail"),
    "C86": ("bootstrap capacitor", "U1 BOOT to SW"),
    "C88": ("bulk input capacitor", "U34 input"),
    "C89": ("decoupling capacitor", "U34 input"),
    "C90": ("bulk output capacitor", "U2 output"),
    "C91": ("IC VCC bypass capacitor", "U1 VCC"),
    "C100": ("decoupling capacitor", "U37 input"),
    "C101": ("bulk output capacitor", "U37 output"),
    "C102": ("decoupling capacitor", "U38 +12V_AO"),
}
ANALOG_ROLE_OVERRIDES = {
    "R61": ("divider upper resistor", "AI0 to AI0_ADC"),
    "R63": ("divider lower resistor", "AI0 ADC to GND"),
    "R64": ("divider upper resistor", "AI1 to AI1_ADC"),
    "R66": ("divider lower resistor", "AI1 ADC to GND"),
    "R67": ("divider upper resistor", "AI2 to AI2_ADC"),
    "R69": ("divider lower resistor", "AI2 ADC to GND"),
    "C73": ("ADC filter capacitor", "AI0_ADC / MOD1 pin 8"),
    "C74": ("ADC filter capacitor", "AI1_ADC / MOD1 pin 22"),
    "C75": ("ADC filter capacitor", "AI2_ADC / MOD1 pin 7"),
}


def component_properties(component: ET.Element) -> dict[str, str]:
    return {
        prop.get("name", ""): prop.get("value", "")
        for prop in component.findall("property")
    }


def channels_from_nets(nets: set[str]) -> list[str]:
    channels: set[str] = set()
    patterns = (
        (r"^AI([0-2])(?:_|$)", "analog input {}"),
        (r"^AOUT([0-3])(?:_|$)", "analog output {}"),
        (r"^PLC_IN(\d+)_N$", "PLC input {}"),
        (r"^FIELD_IN(\d+)$", "PLC input {}"),
        (r"^EXP_IN(\d+)$", "expansion input {}"),
        (r"^KIN(\d+)(?:_|$)", "keyboard input {}"),
        (r"^KOUT(\d+)$", "keyboard output {}"),
        (r"^MOTION(\d+)$", "motion output {}"),
        (r"^BUFY(\d+)$", "motion output {}"),
        (r"^OUT(\d+)$", "output bit {}"),
        (r"^DO(\d+)$", "ULN output {}"),
        (r"^ENC([0-2])_", "encoder {}"),
        (r"^FLD_(?:OPTO|LED)(\d+)_", "PLC input {}"),
    )
    for net in nets:
        for pattern, label in patterns:
            match = re.match(pattern, net)
            if match:
                channels.add(label.format(match.group(1)))
    return sorted(channels, key=lambda item: (item.split()[-1], item))


def role_for(reference: str, value: str, footprint: str, nets: set[str]) -> tuple[str, str, str]:
    if reference == "MOD1":
        return "module", "socketed controller module", "anchor; do not move without approval"
    if reference.startswith("H"):
        return "mounting hole", "mechanical mounting", "anchor; keep fixed"
    if reference.startswith("J"):
        return "connector", "external or board-level connection", "anchor; keep at approved board edge"
    if reference in {"RN28", "RN29"}:
        return "optional link array", "alternate HDMI population", "park; fit only for HDMI option"
    if reference.startswith("RN"):
        return "resistor network", "isolated multi-channel passive network", "place local to its channel bank"
    if reference.startswith("C"):
        if reference in ANALOG_ROLE_OVERRIDES:
            role, associated = ANALOG_ROLE_OVERRIDES[reference]
            return role, associated, "place at ADC node; minimize high-impedance trace"
        if reference in CAP_ROLE_OVERRIDES:
            role, associated = CAP_ROLE_OVERRIDES[reference]
            if role in {"decoupling capacitor", "IC VCC bypass capacitor"}:
                rule = "place within 3 mm of associated supply/ground pins; minimize loop"
            elif role == "bootstrap capacitor":
                rule = "place directly across BOOT and SW pins"
            elif role.startswith("bulk"):
                rule = "place at regulator/load rail entry; preserve short current loop"
            elif role == "output clamp capacitor":
                rule = "place at ULN clamp rail entry"
            else:
                rule = "place at associated rail/load entry"
            return role, associated, rule
        if reference in DECOUPLING_IC:
            return "decoupling capacitor", DECOUPLING_IC[reference], "place within 3 mm of associated supply/ground pins"
        if "100nF" in value and nets & POWER_SUPPLIES and "GND" in nets:
            return "decoupling capacitor", "power rail", "place next to the powered IC supply/ground pins"
        if "uF" in value and nets & POWER_SUPPLIES and "GND" in nets:
            return "bulk/rail capacitor", "power rail", "place near regulator/load entry; preserve loop area"
        if "GND" in nets:
            return "signal filter capacitor", "signal conditioning", "place at the protected/filtered signal node"
        return "capacitor", "support passive", "place with associated functional block"
    if reference.startswith("R"):
        if reference in ANALOG_ROLE_OVERRIDES:
            role, associated = ANALOG_ROLE_OVERRIDES[reference]
            return role, associated, "group by analog channel and place filter capacitor closest to ADC pin"
        if "GND" in nets and nets & POWER_SUPPLIES:
            return "pull-down resistor", "digital state definition", "place close to the driven IC pin"
        if nets & POWER_SUPPLIES and len(nets - POWER_SUPPLIES - {"GND"}) == 1:
            return "pull-up resistor", "digital state definition", "place close to the driven IC pin"
        return "resistor", "series/divider/limit passive", "place local to associated channel"
    if reference.startswith("FB"):
        return "ferrite bead", "rail filtering", "place at rail entry/filter boundary"
    if reference.startswith(("D", "LED")):
        if "LED" in footprint or value in {"indicator", "5V_PWR", "3V3_PWR", "STATUS"} or value.startswith("DO"):
            return "LED", "indicator/protection", "place local to its display or protection channel"
        return "diode", "protection/clamp/rectification", "place at its connector or channel entry"
    if reference.startswith("Q"):
        return "transistor", "switching or interface", "place local to controlled signal and load pins"
    if reference.startswith("L"):
        return "inductor", "switching power stage", "place directly at regulator switch node"
    if reference.startswith("F"):
        return "fuse", "input/load protection", "place at rail or connector entry"
    if reference.startswith("SW"):
        return "switch", "user control", "mechanical anchor; preserve access"
    if reference.startswith("U"):
        return "IC", "active device", "place with its local channel cluster and decoupling"
    return "component", "other", "review manually"


def functional_block(reference: str, sheet: str, nets: set[str], role: str) -> str:
    if reference == "MOD1":
        return "controller module"
    if reference.startswith("H"):
        return "mechanical"
    if reference.startswith("J"):
        if reference in {"J13", "J14", "J15"}:
            return f"encoder {int(reference[1:]) - 13} connector"
        if reference in {"J7", "J8"}:
            return "isolated PLC input connectors"
        if reference in {"J5", "J6"}:
            return "dedicated safety input connector"
        if reference == "J26":
            return "START button input connector"
        if reference in {"J9", "J16"}:
            return "spare keyboard/expansion interface"
        if reference == "J24":
            return "analog inputs connector"
        if reference == "J25":
            return "analog outputs connector"
        if reference in {"J10", "J11"}:
            return "motion output connector"
        if reference == "J12":
            return "ULN output connector"
        if reference in {"J22", "J23"}:
            return "display connector"
        if reference == "J1":
            return "main power connector"
        if reference in {"J19", "J20"}:
            return "storage/wireless connector"
    if sheet == "Analog I/O":
        if (
            reference in {"U37", "C100", "C101", "C102"}
            or "+12V_AO" in nets
            and not any(net.startswith("AOUT") for net in nets)
        ):
            return "analog output power"
        channels = channels_from_nets(nets)
        if any(channel.startswith("analog output") for channel in channels):
            return channels[0]
        return channels[0] if channels else "analog input front end"
    if sheet == "Encoders":
        channels = [item for item in channels_from_nets(nets) if item.startswith("encoder")]
        return channels[0] if channels else "encoder interface"
    if sheet == "Display":
        return "HDMI/LVDS display"
    if sheet == "Storage, Wi-Fi and UI":
        if any(net.startswith("SD_") for net in nets):
            return "SD interface"
        if any(net.startswith("WIFI_") or net == "+3V3_WIFI" for net in nets):
            return "ESP-01S interface"
        if any(net.startswith(("KIN", "KOUT")) for net in nets):
            return "keyboard matrix"
        return "storage/UI support"
    if sheet == "Power and supervision":
        if reference in {"U1", "L1", "C3", "C4", "C5", "C6", "C7", "C8", "C11", "C86", "C91", "R70", "R71", "R72"}:
            return "24V to 5V buck"
        if reference in {"U2", "C10", "C13", "C76", "C90", "C16", "C17", "C77"}:
            return "peripheral 3.3V regulator"
        if reference in {"U34", "C69", "C70", "C88", "C89"}:
            return "ESP 3.3V regulator"
        if reference in {"D4", "R4", "D5", "R5"}:
            return "power indicators"
        return "input protection and power"
    if sheet == "MCU, shift chains and safety":
        if reference in {"U6", "U7", "U8", "U9"}:
            return "74HC165 input chain"
        if reference in {"U10", "U11", "U12", "U13"}:
            return "74HC595 output chain"
        return "MCU and shift-chain support"
    if sheet == "16 PLC inputs and expansion":
        channels = channels_from_nets(nets)
        if any("ESTOP" in net for net in nets):
            return "dedicated E-stop input"
        if any("HOLD" in net for net in nets):
            return "dedicated HOLD input"
        if any("START" in net for net in nets):
            return "dedicated START input"
        return channels[0] if channels else "isolated PLC input channel"
    if sheet == "24 PLC outputs":
        if reference in {"U26", "U27"} or any(net.startswith("DO") for net in nets):
            return "ULN open-collector outputs"
        channels = channels_from_nets(nets)
        return channels[0] if channels else "motion output channel"
    return sheet


def placement_rule(role: str, block: str, nets: set[str]) -> str:
    if role in {"module", "mounting hole", "connector"}:
        return "mechanical anchor; do not move without approval"
    if role == "ADC filter capacitor":
        return "place beside J24 with its channel divider; keep the high-impedance branch short"
    if role in {"decoupling capacitor", "IC VCC bypass capacitor"}:
        return "place immediately beside associated IC supply and GND pins; minimize loop"
    if role in {"bulk/rail capacitor", "bulk input capacitor", "bulk output capacitor", "bulk backlight capacitor", "bulk rail capacitor"}:
        return "place at regulator/load entry; preserve short power loop"
    if role == "bootstrap capacitor":
        return "place directly between regulator BOOT and SW pins"
    if role == "output clamp capacitor":
        return "place at ULN clamp rail entry"
    if role == "signal filter capacitor":
        return "place at protected node; keep branch short"
    if "analog input" in block:
        return "group divider/filter beside J24; keep the ADC branch compact and away from switching nodes"
    if block == "analog output power":
        return "keep U37 input/output capacitors at its pins and C102 at U38 supply"
    if "analog output" in block:
        return "keep each PWM filter and feedback group beside U38/J25; preserve channel order"
    if "PLC input" in block or "E-stop" in block or "HOLD" in block or "START" in block:
        return "keep field-side passives together at connector; preserve isolation barrier"
    if "motion output" in block or "ULN" in block:
        return "place with source register/buffer and output connector; preserve channel order"
    if "keyboard" in block:
        return "place at keyboard connector and corresponding shift-register byte"
    if "encoder" in block:
        return "place between connector and buffer; keep A/B/Z channel grouping"
    if "buck" in block or "regulator" in block:
        return "keep switching/input/output loop compact at regulator pins"
    if "GND" in nets:
        return "place in functional block; keep GND return short"
    return "place with functional block; review after placement"


def main() -> None:
    root = ET.parse(NETLIST).getroot()
    net_members = defaultdict(set)
    all_nets = defaultdict(set)
    for net in root.findall("./nets/net"):
        name = net.get("name", "")
        for node in net.findall("node"):
            all_nets[node.get("ref", "")].add(name)
            net_members[name].add((node.get("ref", ""), node.get("pin", "")))

    board = pcbnew.LoadBoard(str(BOARD))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    edge_box = board.GetBoardEdgesBoundingBox()
    x_min, y_min = pcbnew.ToMM(edge_box.GetLeft()), pcbnew.ToMM(edge_box.GetTop())
    x_max, y_max = pcbnew.ToMM(edge_box.GetRight()), pcbnew.ToMM(edge_box.GetBottom())

    rows = []
    for component in root.findall("./components/comp"):
        reference = component.get("ref", "")
        footprint = (component.findtext("footprint") or "").strip()
        if not footprint:
            continue
        properties = component_properties(component)
        nets = all_nets[reference]
        value = (component.findtext("value") or "").strip()
        role, associated, role_rule = role_for(reference, value, footprint, nets)
        block = functional_block(reference, properties.get("Sheetname", ""), nets, role)
        rule = placement_rule(role, block, nets)
        if rule == "mechanical anchor; do not move without approval" and role not in {"module", "mounting hole", "connector"}:
            rule = role_rule

        if block.startswith("analog input"):
            associated = next(
                (
                    f"{net} / MOD1 pin {next(pin for owner, pin in net_members[net] if owner == 'MOD1')}"
                    for net in sorted(nets)
                    if net.endswith("_ADC")
                    and any(owner == "MOD1" for owner, _ in net_members[net])
                ),
                associated,
            )
        if not associated:
            if block.startswith("analog input"):
                associated = next(
                    (net for net in sorted(nets) if net != "GND"),
                    "",
                )
            elif nets & POWER_SUPPLIES:
                associated = sorted(nets & POWER_SUPPLIES)[0]
            else:
                associated = next(
                    (net for net in sorted(nets) if net not in {"GND"}),
                    "",
                )

        footprint_item = footprints.get(reference)
        if footprint_item is None:
            current = "missing"
            side = ""
            x = y = None
        else:
            position = footprint_item.GetPosition()
            x = round(pcbnew.ToMM(position.x), 3)
            y = round(pcbnew.ToMM(position.y), 3)
            side = board.GetLayerName(footprint_item.GetLayer())
            current = "inside" if x_min <= x <= x_max and y_min <= y <= y_max else "parked"

        rows.append(
            {
                "reference": reference,
                "value": value,
                "sheet": properties.get("Sheetname", ""),
                "functional_block": block,
                "channels": "; ".join(channels_from_nets(nets)),
                "role": role,
                "associated_ic_or_net": associated,
                "placement_rule": rule,
                "current_status": current,
                "side": side,
                "x_mm": x,
                "y_mm": y,
                "dnp": properties.get("Assembly") == "DNP",
                "nets": "; ".join(sorted(nets)),
            }
        )

    fieldnames = list(rows[0])
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "components": len(rows),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "by_block": dict(sorted(Counter(row["functional_block"] for row in rows).items())),
        "parked": [row["reference"] for row in rows if row["current_status"] == "parked"],
    }
    JSON_OUTPUT.write_text(json.dumps({"summary": summary, "components": rows}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
