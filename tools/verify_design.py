"""Verify the generated hierarchy and critical LeanCam net contracts."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from configure_netclasses import CLASSES, PATTERNS, PROJECT, RULES


ROOT = Path(__file__).resolve().parents[1]
NETLIST = ROOT / "hardware" / "motherboard.net.xml"


def main() -> None:
    root = ET.parse(NETLIST).getroot()
    components = root.findall("./components/comp")
    nets = {
        net.get("name", ""): {
            (node.get("ref", ""), node.get("pin", "")) for node in net.findall("node")
        }
        for net in root.findall("./nets/net")
    }
    references = [component.get("ref") for component in components]
    failures: list[str] = []

    project = json.loads(PROJECT.read_text(encoding="utf-8"))
    project_classes = {
        item["name"]: item
        for item in project["net_settings"]["classes"]
    }
    for expected in CLASSES:
        actual = project_classes.get(expected["name"])
        if actual is None:
            failures.append(f"Missing netclass {expected['name']}")
            continue
        for field in (
            "track_width",
            "clearance",
            "via_diameter",
            "via_drill",
            "diff_pair_width",
            "diff_pair_gap",
        ):
            if abs(float(actual[field]) - float(expected[field])) > 1e-9:
                failures.append(
                    f"Netclass {expected['name']} field {field} does not match"
                )
    project_patterns = {
        (item["netclass"], item["pattern"])
        for item in project["net_settings"]["netclass_patterns"]
    }
    for expected_pattern in PATTERNS:
        if expected_pattern not in project_patterns:
            failures.append(
                "Missing netclass pattern "
                f"{expected_pattern[1]} -> {expected_pattern[0]}"
            )
    if not RULES.exists():
        failures.append("Missing board-specific DRC rule file")
    else:
        rule_text = RULES.read_text(encoding="utf-8")
        if "memberOfFootprint('J22')" not in rule_text:
            failures.append("Missing J22-specific LVDS footprint rule")
        if "(min 0.12mm)" not in rule_text:
            failures.append("J22 LVDS footprint rule is not 0.12 mm")
        if "A.NetName == 'LVDS_*'" not in rule_text:
            failures.append("LVDS rules are not independent of rewritten netclasses")

    if len(references) != len(set(references)):
        failures.append("Duplicate reference designators")
    for bit in range(16):
        net = f"PLC_IN{bit + 1}_N"
        if not nets.get(net):
            failures.append(f"Missing input register net {net}")
    for bit in range(8):
        net = f"EXP_IN{bit}"
        if len(nets.get(net, set())) < 2:
            failures.append(f"Missing spare header input net {net}")
    for bit in range(32):
        net = f"OUT{bit}"
        endpoints = nets.get(net, set())
        if len(endpoints) < 2:
            failures.append(f"Output register bit {bit} is not in a 595-to-buffer chain")
    for bit in range(15):
        if f"MOTION{bit}" not in nets:
            failures.append(f"Missing motion output {bit}")
    for bit in range(16):
        if f"DO{bit}" not in nets:
            failures.append(f"Missing low-side output {bit}")
        led_ref = f"D{45 + bit}" if bit < 8 else f"D{49 + bit}"
        resistor_ref = f"R{34 + bit}" if bit < 8 else f"R{110 + bit}"
        if (led_ref, "1") not in nets.get(f"DO{bit}", set()):
            failures.append(f"{led_ref} is not the DO{bit} indicator")
        if (resistor_ref, "2") not in nets.get(f"DO_LED{bit}_A", set()):
            failures.append(f"{resistor_ref} is not the DO{bit} LED resistor")
    for bit in range(8):
        if f"KOUT{bit}" not in nets:
            failures.append(f"Missing keyboard output {bit}")
        if f"KIN{bit}" not in nets:
            failures.append(f"Missing keyboard input {bit}")
    for encoder in range(3):
        for signal in "ABZ":
            input_net = f"ENC{encoder}_{signal}_5V"
            output_net = f"ENC{encoder}_{signal}_3V3"
            if input_net not in nets:
                failures.append(f"Missing encoder {encoder} signal {signal}")
            elif len(nets[input_net]) != 2:
                failures.append(f"Encoder {encoder} {signal} has extra series/filter parts")
            if output_net not in nets:
                failures.append(f"Missing translated encoder {encoder} signal {signal}")

    # The first two 595/541 pairs use optimized equivalent-channel maps.
    # OUTn remains paired with BUFYn, so the firmware-visible logical map is
    # unchanged even though the physical package pins are non-sequential.
    buffer_pairs = {0: ("U10", "U24"), 1: ("U11", "U25")}
    buffer_contracts = {
        0: {0: ("1", "8", "12"), 1: ("15", "9", "11"),
            2: ("3", "6", "14"), 3: ("2", "7", "13"),
            4: ("5", "4", "16"), 5: ("4", "5", "15"),
            6: ("7", "2", "18"), 7: ("6", "3", "17")},
        1: {0: ("2", "8", "12"), 1: ("1", "9", "11"),
            2: ("15", "7", "13"), 3: ("3", "6", "14"),
            4: ("4", "5", "15"), 5: ("5", "4", "16"),
            6: ("6", "3", "17"), 7: ("7", "2", "18")},
    }
    for byte, (register_ref, buffer_ref) in buffer_pairs.items():
        for bit in range(8):
            output_bits = byte * 8 + bit
            source_pin, input_pin, output_pin = buffer_contracts[byte][bit]
            expected = {
                (register_ref, source_pin),
                (buffer_ref, input_pin),
            }
            if not expected.issubset(nets.get(f"OUT{output_bits}", set())):
                failures.append(
                    f"Misaligned 595/541 connection for output bit {output_bits}"
                )
            if (buffer_ref, output_pin) not in nets.get(f"BUFY{output_bits}", set()):
                failures.append(
                    f"Misaligned 541 output for logical bit {output_bits}"
                )

    # Bits 16-29 drive all fourteen ULN channels directly from the 3.3 V 595.
    uln_contracts = {
        16: ("U12", "1", "U26", "7", "10"),
        17: ("U12", "2", "U26", "6", "11"),
        18: ("U12", "3", "U26", "5", "12"),
        19: ("U12", "4", "U26", "4", "13"),
        20: ("U12", "5", "U26", "3", "14"),
        21: ("U12", "6", "U26", "2", "15"),
        22: ("U12", "7", "U26", "1", "16"),
        23: ("U12", "15", "U27", "7", "10"),
        24: ("U13", "15", "U27", "6", "11"),
        25: ("U13", "1", "U27", "5", "12"),
        26: ("U13", "2", "U27", "4", "13"),
        27: ("U13", "3", "U27", "3", "14"),
        28: ("U13", "4", "U27", "2", "15"),
        29: ("U13", "5", "U27", "1", "16"),
    }
    for output_bits, (
        register_ref,
        source_pin,
        uln_ref,
        uln_pin,
        output_pin,
    ) in uln_contracts.items():
        expected = {(register_ref, source_pin), (uln_ref, uln_pin)}
        if not expected.issubset(nets.get(f"OUT{output_bits}", set())):
            failures.append(f"Direct 3.3 V ULN connection missing for bit {output_bits}")
        if (uln_ref, output_pin) not in nets.get(f"DO{output_bits - 16}", set()):
            failures.append(f"ULN output channel mismatch for bit {output_bits}")
    mosfet_outputs = {
        30: ("U13", "6", "R114", "R115", "Q6", "DO14_GATE", "DO14"),
        31: ("U13", "7", "R116", "R117", "Q7", "DO15_GATE", "DO15"),
    }
    for bit, (
        register_ref,
        source_pin,
        series_ref,
        pulldown_ref,
        transistor_ref,
        gate_net,
        output_net,
    ) in mosfet_outputs.items():
        expected = {
            (register_ref, source_pin),
            (series_ref, "1"),
        }
        if not expected.issubset(nets.get(f"OUT{bit}", set())):
            failures.append(f"MOSFET output source missing for bit {bit}")
        for endpoint in (
            (series_ref, "2"),
            (pulldown_ref, "1"),
            (transistor_ref, "1"),
        ):
            if endpoint not in nets.get(gate_net, set()):
                failures.append(f"MOSFET gate contract incomplete for bit {bit}")
        if (pulldown_ref, "2") not in nets.get("GND", set()):
            failures.append(f"{pulldown_ref} is not a gate pull-down")
        if (transistor_ref, "2") not in nets.get("GND", set()):
            failures.append(f"{transistor_ref} source is not grounded")
        if (transistor_ref, "3") not in nets.get(output_net, set()):
            failures.append(f"{transistor_ref} drain is not {output_net}")

    tpd_refs = {
        component.get("ref")
        for component in components
        if (component.findtext("value") or "").strip() == "TPD4E05U06DQA"
    }
    if tpd_refs:
        failures.append(f"Removed HDMI ESD arrays remain: {sorted(tpd_refs)}")

    field_tvs = [
        component.get("ref")
        for component in components
        if (component.findtext("value") or "").strip() == "SMBJ24CA"
    ]
    if len(field_tvs) != 1:
        failures.append(f"Expected only the main-input TVS, found {len(field_tvs)}")
    testpoints = [
        component.get("ref")
        for component in components
        if "TestPoint" in (component.findtext("footprint") or "")
    ]
    if testpoints:
        failures.append(f"Unexpected test points: {testpoints}")
    solder_jumpers = [
        component.get("ref")
        for component in components
        if "SolderJumper" in (component.findtext("footprint") or "")
    ]
    if solder_jumpers != ["JP5"]:
        failures.append(f"Unexpected solder jumpers: {solder_jumpers}")
    mode_headers = [
        component.get("ref")
        for component in components
        if component.get("ref", "").startswith("JP")
        and "PinHeader_1x03" in (component.findtext("footprint") or "")
    ]
    if set(mode_headers) != {"JP2", "JP3", "JP4"}:
        failures.append(f"Unexpected input mode headers: {mode_headers}")
    for legacy in ("BL_EN", "BL_EN_REQ", "BL_VIN", "BL_RAW", "BL_GATE", "BL_GATE_NPN"):
        if legacy in nets:
            failures.append(f"Legacy backlight switching net {legacy} remains")
    if any(name.startswith("LCD_") for name in nets):
        failures.append("Removed LCD power-switching nets remain")
    keyboard_buffers = [
        component.get("ref")
        for component in components
        if (component.findtext("value") or "").strip() == "SN74LVC244ADWR"
    ]
    if keyboard_buffers:
        failures.append(f"Unexpected keyboard buffers: {keyboard_buffers}")
    if "RN14" in references or "RN15" in references:
        failures.append("Retired keyboard pull-down arrays RN14/RN15 remain")
    if "J21" in references:
        failures.append("Retired external Wi-Fi UART header J21 remains")
    retired_capacitors = {"C8", "C14", "C16", "C17", "C77"} & set(references)
    if retired_capacitors:
        failures.append(
            "Retired redundant +5V capacitors remain: "
            + ", ".join(sorted(retired_capacitors))
        )
    for reference in ("RN16", "RN17", "RN18", "RN19", "RN20", "RN21"):
        if reference not in references:
            failures.append(f"Missing 100 ohm series array {reference}")
    motion_array_pins = {
        "RN16": {
            1: "BUFY2", 8: "MOTION2", 2: "BUFY3", 7: "MOTION1",
            3: "BUFY0", 6: "AUX_GATE", 4: "BUFY1", 5: "MOTION0",
        },
        "RN17": {
            1: "BUFY6", 8: "MOTION6", 2: "BUFY7", 7: "MOTION5",
            3: "BUFY4", 6: "MOTION4", 4: "BUFY5", 5: "MOTION3",
        },
        "RN18": {
            1: "BUFY11", 8: "MOTION10", 2: "BUFY10", 7: "MOTION9",
            3: "BUFY8", 6: "MOTION8", 4: "BUFY9", 5: "MOTION7",
        },
        "RN19": {
            1: "BUFY15", 8: "MOTION14", 2: "BUFY14", 7: "MOTION13",
            3: "BUFY13", 6: "MOTION12", 4: "BUFY12", 5: "MOTION11",
        },
    }
    for reference, pin_nets in motion_array_pins.items():
        for pin, expected_net in pin_nets.items():
            if (reference, str(pin)) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not {expected_net}"
                )
    if any(net.startswith("SR_KD") for net in nets):
        failures.append("Keyboard still passes through a separate buffered net")
    component_values = {
        component.get("ref"): (component.findtext("value") or "").strip()
        for component in components
    }
    direct_control_pins = {"ESTOP_N": "24", "HOLD_N": "9", "START_N": "23"}
    for direct_net, module_pin in direct_control_pins.items():
        refs = {ref for ref, _ in nets.get(direct_net, set())}
        if "MOD1" not in refs:
            failures.append(f"{direct_net} is not connected directly to the module")
        if ("MOD1", module_pin) not in nets.get(direct_net, set()):
            failures.append(f"{direct_net} is not on MOD1 pin {module_pin}")
        if any(component_values.get(ref) == "74HC165D" for ref in refs):
            failures.append(f"{direct_net} is incorrectly routed through the input chain")
    shift_module_pins = {
        "SR_OUT_SER": "43",  # GPIO20, DATA
        "SR_SCK": "59",      # GPIO21, CLK
        "SR_LATCH": "44",    # GPIO22, LATCH
        "SR_PL_N": "45",     # GPIO24, 74HC165 load
        "SR_IN_Q7": "60",    # GPIO23, 74HC165 return
    }
    for shift_net, module_pin in shift_module_pins.items():
        if ("MOD1", module_pin) not in nets.get(shift_net, set()):
            failures.append(
                f"{shift_net} is not on MOD1 pin {module_pin} in the shift-chain map"
            )
    shift_endpoints = {
        "SR_OUT_SER": {("U10", "14")},
        "SR_SCK": {
            ("U6", "2"), ("U7", "2"), ("U8", "2"), ("U9", "2"),
            ("U10", "11"), ("U11", "11"), ("U12", "11"), ("U13", "11"),
        },
        "SR_LATCH": {
            ("U10", "12"), ("U11", "12"), ("U12", "12"), ("U13", "12"),
        },
        "SR_PL_N": {
            ("U6", "1"), ("U7", "1"), ("U8", "1"), ("U9", "1"),
        },
        "SR_IN_Q7": {("U9", "9")},
    }
    for shift_net, required_endpoints in shift_endpoints.items():
        if not required_endpoints.issubset(nets.get(shift_net, set())):
            failures.append(f"{shift_net} does not reach every required shift-chain pin")
    connector_values = set(component_values.values())
    for required in (
        "Dedicated E-stop loop",
        "Dedicated HOLD button input",
        "Dedicated START button input",
    ):
        if required not in connector_values:
            failures.append(f"Missing dedicated connector: {required}")
    hstx_pin_map = {
        "39": "HSTX_D0_P",
        "55": "HSTX_D0_N",
        "40": "HSTX_D1_P",
        "56": "HSTX_D1_N",
        "41": "HSTX_D2_P",
        "57": "HSTX_D2_N",
        "42": "HSTX_CLK_P",
        "58": "HSTX_CLK_N",
    }
    for pin, expected_net in hstx_pin_map.items():
        if ("MOD1", pin) not in nets.get(expected_net, set()):
            failures.append(f"MOD1 pin {pin} is not mapped to {expected_net}")
    if ("MOD1", "25") not in nets.get("BL_PWM_MCU", set()):
        failures.append("GPIO35/MOD1 pin 25 is not connected to BL_PWM_MCU")
    if {("R131", "1"), ("MOD1", "25")} - nets.get("BL_PWM_MCU", set()):
        failures.append("R131 is not in series with the PWM source")
    if ("R131", "2") not in nets.get("BL_PWM", set()):
        failures.append("R131 is not connected to the protected BL_PWM node")
    for channel in range(3):
        if f"AI{channel}" not in nets:
            failures.append(f"Missing analog input net AI{channel}")
        if f"AI{channel}_ADC" not in nets:
            failures.append(f"Missing analog ADC net AI{channel}_ADC")
        if f"AI{channel}_MID" in nets:
            failures.append(f"Legacy analog midpoint net AI{channel}_MID remains")
    analog_upper = {
        component.get("ref"): (component.findtext("value") or "").strip()
        for component in components
        if component.get("ref") in {"R61", "R64", "R67"}
    }
    if analog_upper != {"R61": "100k", "R64": "100k", "R67": "100k"}:
        failures.append(f"Analog upper resistors are not all 100k: {analog_upper}")
    pwm_pins = ("19", "6", "20", "5")
    for bit in range(4):
        expected = {
            f"AOUT{bit}_PWM": {("MOD1", pwm_pins[bit]), (f"R{92 + bit}", "1")},
            f"AOUT{bit}_F1": {
                (f"R{92 + bit}", "2"),
                (f"R{96 + bit}", "1"),
                (f"C{92 + bit * 2}", "1"),
            },
            f"AOUT{bit}_F2": {
                (f"R{96 + bit}", "2"),
                (f"C{93 + bit * 2}", "1"),
                ("U38", {"0": "3", "1": "5", "2": "10", "3": "12"}[str(bit)]),
            },
            f"AOUT{bit}_FB": {
                (f"R{100 + bit}", "1"),
                (f"R{104 + bit}", "1"),
                ("U38", {"0": "2", "1": "6", "2": "9", "3": "13"}[str(bit)]),
            },
            f"AOUT{bit}": {
                (f"R{100 + bit}", "2"),
                ("U38", {"0": "1", "1": "7", "2": "8", "3": "14"}[str(bit)]),
                ("J25", str(bit + 2)),
            },
        }
        for net, required in expected.items():
            if not required.issubset(nets.get(net, set())):
                failures.append(f"Analog output {bit} contract is incomplete on {net}")
        for reference, value in (
            (f"R{92 + bit}", "10k"),
            (f"R{96 + bit}", "10k"),
            (f"R{100 + bit}", "22k"),
            (f"R{104 + bit}", "10k"),
        ):
            if component_values.get(reference) != value:
                failures.append(
                    f"Analog output resistor {reference} should be {value}"
                )
    if component_values.get("U38") != "TLV2374IDR":
        failures.append("U38 is not the intended TLV2374 quad op-amp")
    if component_values.get("U37") != "L78L12ACUTR":
        failures.append("U37 is not the intended 12 V analog regulator")
    if ("U37", "1") not in nets.get("+12V_AO", set()):
        failures.append("12 V analog rail is not driven by U37")
    if ("U37", "3") not in nets.get("VIN_PROT", set()):
        failures.append("12 V analog regulator is not supplied from VIN_PROT")
    if ("MOD1", "34") not in nets.get("SD_CD_MCU", set()):
        failures.append("SD-card detect is not on the requested MOD1 pin 34")
    if component_values.get("J36") != "MicroSD alternative, SPI":
        failures.append("J36 is not the alternate microSD socket")
    microsd_pins = {
        "1": "SD_DAT2", "2": "SD_CS_N", "3": "SD_MOSI", "4": "+3V3_SD",
        "5": "SD_SCK", "6": "GND", "7": "SD_MISO", "8": "SD_DAT1",
        "9": "GND", "10": "SD_CD", "SH": "GND",
    }
    for pin, expected_net in microsd_pins.items():
        if ("J36", pin) not in nets.get(expected_net, set()):
            failures.append(f"J36 pin {pin} is not on {expected_net}")
    j36 = next(
        (component for component in components if component.get("ref") == "J36"),
        None,
    )
    j36_properties = (
        {prop.get("name"): prop.get("value") for prop in j36.findall("property")}
        if j36 is not None
        else {}
    )
    if j36_properties.get("Assembly") != "DNP":
        failures.append("J36 microSD alternate must be marked DNP")
    if ("JP5", "1") not in nets.get("SD_CD_MCU", set()):
        failures.append("JP5 pin 1 is not connected to SD_CD_MCU")
    if ("JP5", "2") not in nets.get("SD_CD", set()):
        failures.append("JP5 pin 2 is not connected to SD_CD")
    if "STATUS_LED" in nets:
        failures.append("Legacy external status-LED net remains")
    if any(name in {"PGND", "AGND"} for name in nets):
        failures.append("Legacy split-ground nets remain")
    if any(reference.startswith("NT") for reference in references):
        failures.append("Legacy ground net ties remain")
    output_enable_pins = {
        ("U10", "13"), ("U11", "13"), ("U12", "13"), ("U13", "13"),
        ("U24", "1"), ("U24", "19"), ("U25", "1"), ("U25", "19"),
    }
    for reference, pin in output_enable_pins:
        if (reference, pin) not in nets.get("GND", set()):
            failures.append(f"{reference} pin {pin} is not tied to active enable")
    for legacy in (
        "BUF_OE_N", "OUTPUT_ENABLE", "OUTPUT_ENABLE_PRE",
        "OUTPUT_ENABLE_GATE", "EN_ESTOP_OK", "SR_OE_REQ", "OUT_EN_REQ",
    ):
        if legacy in nets:
            failures.append(f"Removed output-safety net {legacy} remains")

    component_nets = {
        reference: {
            net_name
            for net_name, endpoints in nets.items()
            if any(endpoint_ref == reference for endpoint_ref, _ in endpoints)
        }
        for reference in references
    }
    if "U29" in references or "C58" in references:
        failures.append("Retired U29 encoder buffer or C58 still present")
    divider_checks = (
        ("R110", "1", "ENC2_Z_5V"),
        ("R110", "2", "ENC2_Z_3V3"),
        ("R111", "1", "ENC2_Z_3V3"),
        ("R111", "2", "GND"),
    )
    for reference, pin, expected_net in divider_checks:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected net {expected_net}"
            )
    expansion_headers = {
        "J9": {
            "1": "GND", "2": "+3V3", "3": "EXP_IN0", "4": "EXP_IN1",
            "5": "EXP_IN2", "6": "EXP_IN3",
        },
        "J27": {
            "1": "GND", "2": "+3V3", "3": "EXP_IN4", "4": "EXP_IN5",
            "5": "EXP_IN6", "6": "EXP_IN7",
        },
    }
    for reference, pins in expansion_headers.items():
        for pin, expected_net in pins.items():
            if (reference, pin) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not on expected net {expected_net}"
                )
    motion_connectors = {
        "J7": {
            1: "FIELD_IN9", 2: "FIELD_COM0",
            3: "FIELD_IN10", 4: "FIELD_COM0",
            5: "FIELD_IN11", 6: "FIELD_COM0",
            7: "FIELD_IN12", 8: "FIELD_COM0",
        },
        "J8": {
            1: "FIELD_IN1", 2: "FIELD_COM1",
            3: "FIELD_IN2", 4: "FIELD_COM1",
            5: "FIELD_IN3", 6: "FIELD_COM1",
            7: "FIELD_IN4", 8: "FIELD_COM1",
        },
        "J12": {
            1: "DO0", 2: "DO1", 3: "DO2", 4: "DO3",
            5: "DO4", 6: "DO5", 7: "DO6", 8: "DO7",
        },
        "J32": {
            1: "DO8", 2: "DO9", 3: "DO10", 4: "DO11",
            5: "DO12", 6: "DO13", 7: "DO14", 8: "DO15",
        },
        "J24": {
            1: "AI0", 2: "GND", 3: "AI1", 4: "GND", 5: "AI2",
        },
        "J10": {1: "MOTION0", 2: "MOTION1", 3: "MOTION2", 4: "GND"},
        "J11": {1: "MOTION3", 2: "MOTION4", 3: "MOTION5", 4: "GND"},
        "J28": {1: "MOTION6", 2: "MOTION7", 3: "MOTION8", 4: "GND"},
        "J29": {1: "MOTION9", 2: "MOTION10", 3: "MOTION11", 4: "GND"},
        "J30": {1: "MOTION12", 2: "MOTION13", 3: "MOTION14", 4: "GND"},
        "J31": {1: "AUX_OUT", 2: "GND"},
        "J2": {1: "+12V_BL", 2: "GND", 3: "BL_PWM", 4: "BL_LED_N"},
        "J33": {1: "DO_COM", 2: "GND"},
        "J34": {
            1: "FIELD_IN13", 2: "FIELD_COM0",
            3: "FIELD_IN14", 4: "FIELD_COM0",
            5: "FIELD_IN15", 6: "FIELD_COM0",
            7: "FIELD_IN16", 8: "FIELD_COM0",
        },
        "J35": {
            1: "FIELD_IN5", 2: "FIELD_COM1",
            3: "FIELD_IN6", 4: "FIELD_COM1",
            5: "FIELD_IN7", 6: "FIELD_COM1",
            7: "FIELD_IN8", 8: "FIELD_COM1",
        },
    }
    for reference, pins in motion_connectors.items():
        for pin, expected_net in pins.items():
            if expected_net is None:
                continue
            if (reference, str(pin)) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not on expected net {expected_net}"
                )
    aux_mosfet = {
        ("RN16", "3", "BUFY0"),
        ("RN16", "6", "AUX_GATE"),
        ("R113", "1", "AUX_GATE"),
        ("R113", "2", "GND"),
        ("Q5", "1", "AUX_GATE"),
        ("Q5", "2", "GND"),
        ("Q5", "3", "AUX_OUT"),
    }
    for reference, pin, expected_net in aux_mosfet:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected AUX net {expected_net}"
            )
    backlight_mosfet = {
        ("R129", "1", "BL_PWM_MCU"),
        ("R129", "2", "BL_SW_GATE"),
        ("R130", "1", "BL_SW_GATE"),
        ("R130", "2", "GND"),
        ("Q8", "1", "BL_SW_GATE"),
        ("Q8", "2", "GND"),
        ("Q8", "3", "BL_LED_N"),
        ("J2", "4", "BL_LED_N"),
    }
    for reference, pin, expected_net in backlight_mosfet:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected backlight net {expected_net}"
            )
    if component_values.get("Q8") != "BSS138":
        failures.append("Q8 is not the optional backlight low-side MOSFET")
    if ("U24", "8") not in nets.get("OUT0", set()):
        failures.append("U24 spare buffer input pin 8 is not OUT0")
    if ("U24", "12") not in nets.get("BUFY0", set()):
        failures.append("U24 spare buffer output pin 12 is not BUFY0")
    # The physical connector order is chosen for the shortest, crossing-free
    # PCB fanout. Firmware maps these positions to logical PLC channels.
    for block, references_for_bank in ((0, ("J7", "J34")), (1, ("J8", "J35"))):
        for half, reference in enumerate(references_for_bank):
            for local in range(4):
                number = (9 if block == 0 else 1) + half * 4 + local
                signal_pin = str(2 * local + 1)
                common_pin = str(2 * local + 2)
                if (reference, signal_pin) not in nets.get(
                    f"FIELD_IN{number}", set()
                ):
                    failures.append(
                        f"{reference} pin {signal_pin} is not FIELD_IN{number}"
                    )
                if (reference, common_pin) not in nets.get(
                    f"FIELD_COM{block}", set()
                ):
                    failures.append(
                        f"{reference} pin {common_pin} is not FIELD_COM{block}"
                    )

    plc_register_pin_numbers = {
        "U9": (5, 6, 7, 8, 4, 3, 2, 1),
        "U8": (13, 14, 15, 16, 12, 11, 10, 9),
    }
    plc_data_pins = ("11", "12", "13", "14", "3", "4", "5", "6")
    for reference, numbers in plc_register_pin_numbers.items():
        for data_pin, number in zip(plc_data_pins, numbers):
            if (reference, data_pin) not in nets.get(f"PLC_IN{number}_N", set()):
                failures.append(
                    f"{reference} data pin {data_pin} is not PLC_IN{number}_N"
                )
    keyboard_network_pins = {
        ("RN8", "1", "GND"), ("RN8", "8", "BUFY2"),
        ("RN8", "2", "GND"), ("RN8", "7", "BUFY3"),
        ("RN8", "3", "GND"), ("RN8", "6", "BUFY0"),
        ("RN8", "4", "GND"), ("RN8", "5", "BUFY1"),
        ("RN9", "1", "BUFY5"), ("RN9", "8", "GND"),
        ("RN9", "2", "BUFY4"), ("RN9", "7", "GND"),
        ("RN9", "3", "BUFY7"), ("RN9", "6", "GND"),
        ("RN9", "4", "BUFY6"), ("RN9", "5", "GND"),
        ("RN10", "1", "BUFY9"), ("RN10", "8", "GND"),
        ("RN10", "2", "BUFY8"), ("RN10", "7", "GND"),
        ("RN10", "3", "BUFY10"), ("RN10", "6", "GND"),
        ("RN10", "4", "BUFY11"), ("RN10", "5", "GND"),
        ("RN11", "1", "GND"), ("RN11", "8", "BUFY15"),
        ("RN11", "2", "GND"), ("RN11", "7", "BUFY14"),
        ("RN11", "3", "GND"), ("RN11", "6", "BUFY13"),
        ("RN11", "4", "GND"), ("RN11", "5", "BUFY12"),
        ("RN12", "1", "OUT19"), ("RN12", "8", "GND"),
        ("RN12", "2", "OUT18"), ("RN12", "7", "GND"),
        ("RN12", "3", "OUT17"), ("RN12", "6", "GND"),
        ("RN12", "4", "OUT16"), ("RN12", "5", "GND"),
        ("RN13", "2", "OUT22"), ("RN13", "7", "GND"),
        ("RN13", "3", "OUT21"), ("RN13", "6", "GND"),
        ("RN13", "4", "OUT20"), ("RN13", "5", "GND"),
        ("RN20", "1", "KOUT0"), ("RN20", "8", "OUT24"),
        ("RN20", "2", "KOUT1"), ("RN20", "7", "OUT25"),
        ("RN20", "3", "KOUT2"), ("RN20", "6", "OUT26"),
        ("RN20", "4", "KOUT3"), ("RN20", "5", "OUT27"),
        ("RN21", "1", "KOUT4"), ("RN21", "8", "OUT28"),
        ("RN21", "2", "KOUT5"), ("RN21", "7", "OUT29"),
        ("RN21", "3", "KOUT6"), ("RN21", "6", "OUT30"),
        ("RN21", "4", "KOUT7"), ("RN21", "5", "OUT31"),
        ("RN30", "1", "OUT26"), ("RN30", "8", "GND"),
        ("RN30", "2", "OUT24"), ("RN30", "7", "GND"),
        ("RN30", "3", "OUT25"), ("RN30", "6", "GND"),
        ("RN30", "4", "OUT23"), ("RN30", "5", "GND"),
        ("RN31", "1", "OUT29"), ("RN31", "8", "GND"),
        ("RN31", "2", "OUT28"), ("RN31", "7", "GND"),
        ("RN31", "3", "OUT27"), ("RN31", "6", "GND"),
        ("RN22", "1", "KIN0_FILT"), ("RN22", "8", "KIN0"),
        ("RN22", "2", "KIN1_FILT"), ("RN22", "7", "KIN1"),
        ("RN22", "3", "KIN2_FILT"), ("RN22", "6", "KIN2"),
        ("RN22", "4", "KIN3_FILT"), ("RN22", "5", "KIN3"),
        ("RN24", "1", "KIN4_FILT"), ("RN24", "8", "KIN4"),
        ("RN24", "2", "KIN5_FILT"), ("RN24", "7", "KIN5"),
        ("RN24", "3", "KIN6_FILT"), ("RN24", "6", "KIN6"),
        ("RN24", "4", "KIN7_FILT"), ("RN24", "5", "KIN7"),
    }
    for reference, pin, expected_net in keyboard_network_pins:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected keyboard net {expected_net}"
            )
    connected_pads = {
        endpoint for endpoints in nets.values() for endpoint in endpoints
    }
    spare_array_pins = {
        "RN13": ("1", "8"),
        "RN31": ("4", "5"),
    }
    for reference, pins in spare_array_pins.items():
        for pin in pins:
            if (reference, pin) in connected_pads:
                failures.append(f"{reference} spare pin {pin} is connected")
    decoupling_required = {
        "U1", "U2", "U3", "U37", "U38",
        "U6", "U7", "U8", "U9", "U10", "U11", "U12", "U13",
        "U24", "U25", "U28", "U34", "U41",
    }
    decouplers = [
        reference
        for reference, value in component_values.items()
        if reference.startswith("C") and value.startswith("100nF")
    ]
    for reference in sorted(decoupling_required):
        supply_nets = {
            net
            for net in component_nets.get(reference, set())
            if net.startswith(("+", "VIN")) or net == "DO_COM"
            and not net.endswith(("_SW", "_BST"))
        }
        has_local = any(
            supply_nets & component_nets.get(capacitor, set())
            and "GND" in component_nets.get(capacitor, set())
            for capacitor in decouplers
        )
        if not has_local:
            failures.append(f"{reference} has no 100nF capacitor to GND")

    components_by_ref = {
        component.get("ref"): component for component in components
    }
    dnp_required = {
        "RN26", "RN27",
    }
    for reference in sorted(dnp_required):
        component = components_by_ref.get(reference)
        assembly = next(
            (
                prop.get("value", "")
                for prop in component.findall("property")
                if prop.get("name") == "Assembly"
            ),
            "",
        ) if component is not None else ""
        if assembly != "DNP":
            failures.append(f"Legacy component {reference} is not marked DNP")

    lvds_required = {
        ("RN26", "1", "HSTX_D1_N"),
        ("RN26", "8", "LVDS_D1_N"),
        ("RN26", "2", "HSTX_D1_P"),
        ("RN26", "7", "LVDS_D1_P"),
        ("RN26", "3", "HSTX_D0_P"),
        ("RN26", "6", "LVDS_D0_P"),
        ("RN26", "4", "HSTX_D0_N"),
        ("RN26", "5", "LVDS_D0_N"),
        ("RN27", "1", "HSTX_CLK_N"),
        ("RN27", "8", "LVDS_CLK_N"),
        ("RN27", "2", "HSTX_CLK_P"),
        ("RN27", "7", "LVDS_CLK_P"),
        ("RN27", "3", "HSTX_D2_P"),
        ("RN27", "6", "LVDS_D2_P"),
        ("RN27", "4", "HSTX_D2_N"),
        ("RN27", "5", "LVDS_D2_N"),
    }
    for reference, pin, expected_net in lvds_required:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected LVDS net {expected_net}"
            )
    if any(name.startswith("HDMI_") or name == "+5V_HDMI" for name in nets):
        failures.append("Removed HDMI nets remain in the schematic")
    lcd_connector_pins = {
        "1": "+3V3",
        "2": "+3V3",
        "3": "+3V3",
        "4": "GND",
        "5": "GND",
        "6": "GND",
        "7": "LVDS_D0_N",
        "8": "LVDS_D0_P",
        "9": "LVDS_D1_N",
        "10": "LVDS_D1_P",
        "11": "LVDS_D2_N",
        "12": "LVDS_D2_P",
        "13": "GND",
        "14": "GND",
        "15": "LVDS_CLK_N",
        "16": "LVDS_CLK_P",
    }
    for pin, expected_net in lcd_connector_pins.items():
        if ("J22", pin) not in nets.get(expected_net, set()):
            failures.append(f"J22 pin {pin} is not on {expected_net}")
    for pin in ("17", "18", "19", "20"):
        if any(("J22", pin) in endpoints for endpoints in nets.values()):
            failures.append(f"J22 pin {pin} must remain unconnected")
    if "U41" not in references:
        failures.append("Missing active LVDS driver U41")
    lvds_driver_pins = {
        "1": "+3V3", "2": "HSTX_CLK_P", "3": "HSTX_D2_P",
        "4": "+3V3", "5": "GND", "6": "HSTX_D1_P",
        "7": "HSTX_D0_P", "8": "GND",
        "9": "LVDS_D0_N", "10": "LVDS_D0_P",
        "11": "LVDS_D1_P", "12": "LVDS_D1_N",
        "13": "LVDS_D2_N", "14": "LVDS_D2_P",
        "15": "LVDS_CLK_P", "16": "LVDS_CLK_N",
    }
    for pin, expected_net in lvds_driver_pins.items():
        if ("U41", pin) not in nets.get(expected_net, set()):
            failures.append(f"U41 pin {pin} is not on {expected_net}")
    if ("C106", "1") not in nets.get("+3V3", set()):
        failures.append("C106 is not connected to U28 +3V3")
    if ("C106", "2") not in nets.get("GND", set()):
        failures.append("C106 is not connected to GND")

    removed = {
        "C9", "C12", "C18", "C19", "C20", "C21", "C78", "C81", "C82", "C83",
        "C1", "C84", "C85", "D6", "D7", "D8", "FB3", "JP1",
        "Q1", "Q2", "Q3", "Q4", "R2", "R3", "R6", "R7", "R8",
        "R14", "R15",
        "R42", "R43", "SW1", "U4", "U14", "U15", "U16", "U17", "U22", "U23",
        "RN1", "RN2", "RN3", "RN4", "RN5", "RN23", "RN25",
        *(f"R{index}" for index in range(55, 59)),
        "R54",
        *(f"R{index}" for index in range(76, 92)),
        *(f"U{index}" for index in range(42, 54)),
        *(f"C{index}" for index in range(30, 53)),
        *(f"C{index}" for index in range(59, 67)),
    }
    remaining = sorted(removed & set(references))
    if remaining:
        failures.append(f"Obsolete components remain: {remaining}")

    quad_opto_refs = {
        reference
        for reference, value in component_values.items()
        if value == "LTV-847S"
    }
    expected_quad_opto = {f"U{index}" for index in range(18, 22)}
    if quad_opto_refs != expected_quad_opto:
        failures.append(f"Unexpected quad optocoupler set: {sorted(quad_opto_refs)}")
    for reference in sorted(expected_quad_opto):
        footprint = next(
            (
                (component.findtext("footprint") or "").strip()
                for component in components
                if component.get("ref") == reference
            ),
            "",
        )
        if footprint != "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm":
            failures.append(f"{reference} does not use the SOIC-16W optocoupler footprint")

    safety_optos = {
        reference
        for reference, value in component_values.items()
        if value == "EL3H7"
    }
    if safety_optos != {"U35", "U36", "U39"}:
        failures.append(f"Unexpected individual safety optocouplers: {sorted(safety_optos)}")

    expected_pullups = {"R74", "R75", "R109"}
    actual_pullups = {
        reference
        for reference in expected_pullups
        if component_values.get(reference) == "4.7k"
    }
    if actual_pullups != expected_pullups:
        failures.append(
            f"Missing individual 4.7k input pull-ups: {sorted(expected_pullups - actual_pullups)}"
        )

    isolated_input_contracts = []
    for bit in range(16):
        number = bit + 1
        isolated_input_contracts.append(
            {
                "channel": f"PLC input {number}",
                "R": (f"R{18 + bit}", "2.2k", {f"FIELD_IN{number}", f"FLD_LED{number}_A"}),
                "LED": (f"D{13 + 2 * bit}", "indicator", {f"FLD_OPTO{number}_A", f"FLD_LED{number}_A"}),
                "D": (
                    f"D{14 + 2 * bit}",
                    "1N4148WS",
                    {f"FLD_LED{number}_A", "ISO_GND"},
                ),
            }
        )
    isolated_input_contracts.extend(
        (
            {
                "channel": "E-stop",
                "R": ("R16", "2.2k", {"ESTOP_FIELD", "ESTOP_LED_A"}),
                "LED": ("D9", "indicator", {"ESTOP_OPTO_A", "ESTOP_LED_A"}),
                "D": ("D10", "1N4148WS", {"ESTOP_LED_A", "ISO_GND"}),
                "RV": ("R74", "4.7k", {"ESTOP_N", "+3V3"}),
            },
            {
                "channel": "HOLD",
                "R": ("R17", "2.2k", {"HOLD_FIELD", "HOLD_LED_A"}),
                "LED": ("D11", "indicator", {"HOLD_OPTO_A", "HOLD_LED_A"}),
                "D": ("D12", "1N4148WS", {"HOLD_LED_A", "ISO_GND"}),
                "RV": ("R75", "4.7k", {"HOLD_N", "+3V3"}),
            },
            {
                "channel": "START",
                "R": ("R108", "2.2k", {"START_FIELD", "START_LED_A"}),
                "LED": ("D54", "indicator", {"START_OPTO_A", "START_LED_A"}),
                "D": ("D55", "1N4148WS", {"START_LED_A", "ISO_GND"}),
                "RV": ("R109", "4.7k", {"START_N", "+3V3"}),
            },
        )
    )
    for contract in isolated_input_contracts:
        channel = contract.pop("channel")
        for role, (reference, value, expected_nets) in contract.items():
            if component_values.get(reference) != value:
                failures.append(
                    f"{channel} {role} {reference} should be {value}, "
                    f"got {component_values.get(reference)}"
                )
            actual_nets = {net for net, endpoints in nets.items() if any(ref == reference for ref, _ in endpoints)}
            if not expected_nets.issubset(actual_nets):
                failures.append(
                    f"{channel} {role} {reference} is missing nets "
                    f"{sorted(expected_nets - actual_nets)}"
                )

    for group in range(4):
        reference = f"RN{32 + group}"
        if component_values.get(reference) != "4x10k":
            failures.append(f"{reference} is not the PLC 4x10k pull-up network")
        for channel in range(4):
            number = group * 4 + channel + 1
            signal_pin = str(channel + 1)
            supply_pin = str(8 - channel)
            if (reference, signal_pin) not in nets.get(
                f"PLC_IN{number}_N", set()
            ):
                failures.append(
                    f"{reference} pin {signal_pin} is not PLC_IN{number}_N"
                )
            if (reference, supply_pin) not in nets.get("+3V3", set()):
                failures.append(
                    f"{reference} pin {supply_pin} is not +3V3"
                )

    if component_values.get("U1") != "LMR36510ADDAR":
        failures.append("U1 is not the specified LMR36510 buck")
    if component_values.get("U40") != "TBA2-0512":
        failures.append("U40 is not the isolated 5 V to 12 V converter")
    isolated_fields = {
        ("U40", "1", "+5V_ISO_IN"),
        ("U40", "2", "GND"),
        ("U40", "4", "ISO_GND"),
        ("U40", "6", "+12V_RAW"),
        ("D56", "1", "+12V_FIELD"),
        ("D56", "2", "+12V_RAW"),
        ("F4", "1", "+5V"),
        ("F4", "2", "+5V_ISO_IN"),
        ("C103", "1", "+5V_ISO_IN"),
        ("C105", "1", "+12V_FIELD"),
    }
    for reference, pin, expected_net in isolated_fields:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on isolated-field net {expected_net}"
            )
    isolated_selectors = {
        ("JP2", "1", "ISO_GND"),
        ("JP2", "2", "FIELD_COM0"),
        ("JP2", "3", "+12V_FIELD"),
        ("JP3", "1", "ISO_GND"),
        ("JP3", "2", "FIELD_COM1"),
        ("JP3", "3", "+12V_FIELD"),
        ("JP4", "1", "ISO_GND"),
        ("JP4", "2", "FIELD_SAFETY_COM"),
        ("JP4", "3", "+12V_FIELD"),
    }
    for reference, pin, expected_net in isolated_selectors:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on field-mode net {expected_net}"
            )
    if ("U35", "2") not in nets.get("ISO_GND", set()):
        failures.append("E-stop optocoupler return is not on ISO_GND")
    if ("U36", "2") not in nets.get("ISO_GND", set()):
        failures.append("HOLD optocoupler return is not on ISO_GND")
    if ("U39", "2") not in nets.get("ISO_GND", set()):
        failures.append("START optocoupler return is not on ISO_GND")
    for reference in expected_quad_opto:
        for pin in ("2", "4", "6", "8"):
            if (reference, pin) not in nets.get("ISO_GND", set()):
                failures.append(
                    f"{reference} cathode {pin} is not on ISO_GND"
                )
    if not {("U1", "2"), ("U1", "3")}.issubset(nets.get("VIN_PROT", set())):
        failures.append("LMR36510 EN pin is not tied to its VIN pin")
    for pin in ("3", "18", "64"):
        if any(("MOD1", pin) in endpoints for endpoints in nets.values()):
            failures.append(f"WeAct 3V3 output pin {pin} must remain local to the module")
    if ("MOD1", "31") not in nets.get("+5V", set()):
        failures.append("WeAct 5 V input is not connected to the main 5 V rail")
    for reference in ("D2", "D3"):
        if component_values.get(reference) != "SS16":
            failures.append(f"{reference} is not the intended 1 A input diode")
        if (reference, "1") not in nets.get(
            "VIN_PROT" if reference == "D2" else "VIN_BL_PROT", set()
        ):
            failures.append(f"{reference} cathode is not on its protected input rail")
        if (reference, "2") not in nets.get("VIN_FUSED", set()):
            failures.append(f"{reference} anode is not on VIN_FUSED")
    if "Q1" in references or "Q1_GATE" in nets:
        failures.append("Retired Q1 input MOSFET or gate net remains")
    for expected in (("U1", "4"), ("MOD1", "21"), ("R73", "1")):
        if expected not in nets.get("PWR_GOOD_N", set()):
            failures.append(f"Power-good network is missing {expected}")
    if {("U1", "6"), ("C91", "1")} - nets.get("VCC5", set()):
        failures.append("LMR36510 VCC bypass capacitor is not connected")
    if component_values.get("R70") != "34k":
        failures.append("LMR36510 feedback upper resistor is not 34k")
    if component_values.get("R71") != "46.4k":
        failures.append("LMR36510 feedback upper resistor is not 46.4k")
    if component_values.get("R72") != "20k":
        failures.append("LMR36510 feedback lower resistor is not 20k")
    if component_values.get("U2") != "AMS1117-3.3":
        failures.append("Peripheral 3.3 V rail is not supplied by its dedicated LDO")
    if component_values.get("U3") != "LMR36510ADDAR":
        failures.append("U3 is not the dedicated LMR36510 backlight buck")
    if not {("U3", "2"), ("U3", "3")}.issubset(nets.get("VIN_BL_PROT", set())):
        failures.append("Backlight buck input/enable pins are not on VIN_BL_PROT")
    if component_values.get("L2") != "47uH 1.5A":
        failures.append("Backlight buck inductor is not the TI 12 V reference value")
    if component_values.get("R126") != "100k":
        failures.append("Backlight buck upper feedback resistor is not 100k")
    if component_values.get("R127") != "9.09k":
        failures.append("Backlight buck lower feedback resistor is not 9.09k")
    if ("U3", "4") in {
        endpoint for endpoints in nets.values() for endpoint in endpoints
    }:
        failures.append("U3 power-good pin should remain unconnected")
    if "J3" in references:
        failures.append("Redundant two-pin +12 V output J3 remains")
    if component_values.get("U37") != "L78L12ACUTR":
        failures.append("The existing 0-10 V 12 V analog regulator was removed")
    if component_values.get("U34") != "AMS1117-3.3":
        failures.append("ESP8266 does not have its dedicated 3.3 V regulator")
    if ("U34", "2") not in nets.get("+3V3_WIFI", set()):
        failures.append("ESP8266 regulator is not connected to +3V3_WIFI")
    if component_values.get("RN36") != "4x10k":
        failures.append("RN36 is not the ESP 4x10k pull-up network")
    wifi_pullups = {
        "1": "+3V3_WIFI", "8": "WIFI_EN",
        "2": "+3V3_WIFI", "7": "WIFI_RST",
        "3": "+3V3_WIFI", "6": "WIFI_GPIO0",
        "4": "+3V3_WIFI", "5": "WIFI_GPIO2",
    }
    for pin, expected_net in wifi_pullups.items():
        if ("RN36", pin) not in nets.get(expected_net, set()):
            failures.append(f"RN36 pin {pin} is not on {expected_net}")

    empty_footprints = [
        component.get("ref")
        for component in components
        if not (component.findtext("footprint") or "").strip()
    ]
    report = {
        "components": len(components),
        "nets": len(nets),
        "single_node_nets": sorted(
            name for name, endpoints in nets.items() if len(endpoints) < 2
        ),
        "empty_footprints": empty_footprints,
        "failures": failures,
    }
    (ROOT / "hardware" / "netlist-validation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
