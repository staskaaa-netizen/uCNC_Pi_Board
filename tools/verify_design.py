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
    for bit in range(32):
        net = f"OUT{bit}"
        endpoints = nets.get(net, set())
        if len(endpoints) < 2:
            failures.append(f"Output register bit {bit} does not reach its load")
    for axis in range(7):
        for signal in ("STEP", "DIR"):
            if f"AX{axis}_{signal}" not in nets:
                failures.append(f"Missing AX{axis}_{signal} output")
    for bit in range(16):
        if f"DO{bit}" not in nets:
            failures.append(f"Missing low-side output {bit}")
        led_ref = f"D{45 + bit}" if bit < 8 else f"D{49 + bit}"
        resistor_ref = f"R{34 + bit}" if bit < 8 else f"R{110 + bit}"
        if (led_ref, "1") not in nets.get(f"DO{bit}", set()):
            failures.append(f"{led_ref} is not the DO{bit} indicator")
        if (resistor_ref, "2") not in nets.get(f"DO_LED{bit}_A", set()):
            failures.append(f"{resistor_ref} is not the DO{bit} LED resistor")
    if any(
        name.startswith(("KIN", "KOUT"))
        for name in nets
    ):
        failures.append("Retired keyboard nets remain")
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

    # The physical Q-pin maps remain non-sequential for layout compatibility,
    # but every logical OUTn now leaves its AHCT595 and drives the load directly.
    output_register_contracts = {
        "U10": {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 15: 7},
        "U11": {1: 8, 2: 9, 3: 10, 4: 11, 5: 12, 6: 13, 7: 14, 15: 15},
        "U12": {1: 16, 2: 17, 3: 18, 4: 19, 5: 20, 6: 21, 7: 22, 15: 23},
        "U13": {1: 24, 2: 25, 3: 26, 4: 27, 5: 28, 6: 29, 7: 30, 15: 31},
    }
    for register_ref, pin_bits in output_register_contracts.items():
        for source_pin, output_bit in pin_bits.items():
            if (register_ref, str(source_pin)) not in nets.get(
                f"OUT{output_bit}", set()
            ):
                failures.append(
                    f"{register_ref} pin {source_pin} is not OUT{output_bit}"
                )

    motion_buffer_pins = {
        "U42": {2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1, 9: 0},
        "U43": {2: 15, 3: 14, 4: 13, 5: 12, 6: 11, 7: 10, 8: 9, 9: 8},
    }
    buffer_input_order = (2, 3, 4, 5, 6, 7, 8, 9)
    buffer_output_by_input = dict(zip(buffer_input_order, range(18, 10, -1)))
    motion_net_by_bit = {}
    for axis in range(7):
        motion_net_by_bit[axis * 2] = f"AX{axis}_STEP"
        motion_net_by_bit[axis * 2 + 1] = f"AX{axis}_DIR"
    for reference, pin_bits in motion_buffer_pins.items():
        for input_pin, bit in pin_bits.items():
            if (reference, str(input_pin)) not in nets.get(f"OUT{bit}", set()):
                failures.append(
                    f"{reference} input pin {input_pin} is not OUT{bit}"
                )
            output_pin = buffer_output_by_input[input_pin]
            output_net = motion_net_by_bit.get(bit)
            if output_net is None:
                continue
            if (reference, str(output_pin)) not in nets.get(output_net, set()):
                failures.append(
                    f"{reference} output pin {output_pin} is not "
                    f"{output_net}"
                )

    uln_package_channels = (
        ("U26", tuple(range(7, -1, -1))),
        ("U27", tuple(range(15, 7, -1))),
    )
    uln_input_pins = tuple(range(1, 9))
    uln_output_pins = tuple(range(18, 10, -1))
    for uln_ref, channel_indices in uln_package_channels:
        for channel, index in enumerate(channel_indices):
            source_net = f"OUT{16 + index}"
            final_net = f"DO{index}"
            opto_ref = f"U{61 + index // 4}"
            led_anode = f"DO_OPTO_LED{index}_A"
            driver_net = f"DO_DRV{index}"
            opto_slot = index % 4
            led_network = f"RN{37 + index // 4}"
            led_input_pin = str(4 - opto_slot)
            led_output_pin = str(8 - opto_slot)
            if (led_network, led_input_pin) not in nets.get(source_net, set()):
                failures.append(
                    f"{led_network} pin {led_input_pin} is not {source_net}"
                )
            if (led_network, led_output_pin) not in nets.get(led_anode, set()):
                failures.append(
                    f"{led_network} pin {led_output_pin} is not {led_anode}"
                )
            opto_contract = {
                str(1 + opto_slot * 2): led_anode,
                str(2 + opto_slot * 2): "GND",
                str(15 - opto_slot * 2): (
                    f"DO_DRV{(index // 4) * 4 + (3 - opto_slot)}"
                ),
                str(16 - opto_slot * 2): "+24V_FIELD",
            }
            for pin, expected_net in opto_contract.items():
                if (opto_ref, pin) not in nets.get(expected_net, set()):
                    failures.append(
                        f"{opto_ref} pin {pin} is not on {expected_net}"
                    )
            input_pin = uln_input_pins[channel]
            output_pin = uln_output_pins[channel]
            if (uln_ref, str(input_pin)) not in nets.get(driver_net, set()):
                failures.append(
                    f"{uln_ref} input pin {input_pin} is not {driver_net}"
                )
            if (uln_ref, str(output_pin)) not in nets.get(final_net, set()):
                failures.append(
                    f"{uln_ref} output pin {output_pin} is not {final_net}"
                )

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
    if mode_headers:
        failures.append(f"Retired input mode headers remain: {mode_headers}")
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
    if any(net.startswith("SR_KD") for net in nets):
        failures.append("Keyboard still passes through a separate buffered net")
    components_by_ref = {
        component.get("ref"): component for component in components
    }
    component_values = {
        component.get("ref"): (component.findtext("value") or "").strip()
        for component in components
    }
    for reference in ("RN37", "RN38", "RN39", "RN40"):
        if component_values.get(reference) != "4x1k":
            failures.append(f"{reference} is not a 4x1k output opto-drive network")
    for reference in ("U10", "U11", "U12", "U13"):
        if component_values.get(reference) != "SN74AHCT595DR":
            failures.append(f"{reference} is not an SN74AHCT595DR")
        component = components_by_ref.get(reference)
        if not component or not (component.findtext("footprint") or "").strip().startswith(
            "Package_SO:SOIC-16"
        ):
            failures.append(f"{reference} is not in a SOIC-16 package")
        for pin in ("10", "16"):
            if (reference, pin) not in nets.get("+5V", set()):
                failures.append(f"{reference} pin {pin} is not powered from +5V")
    for reference in ("U6", "U7", "U8", "U9"):
        if component_values.get(reference) != "74HC165D":
            failures.append(f"{reference} is not a 74HC165D input register")
        component = components_by_ref.get(reference)
        if not component or not (component.findtext("footprint") or "").strip().startswith(
            "Package_SO:SOIC-16"
        ):
            failures.append(f"{reference} is not in a SOIC-16 package")
        if (reference, "16") not in nets.get("+3V3", set()):
            failures.append(f"{reference} input register is not powered from +3V3")
    for reference in ("U42", "U43"):
        if component_values.get(reference) != "TC74AC541F":
            failures.append(f"{reference} is not a TC74AC541F motion buffer")
        component = components_by_ref.get(reference)
        if not component or not (component.findtext("footprint") or "").strip().startswith(
            "Package_SO:SOIC-20W"
        ):
            failures.append(f"{reference} is not in a SOIC-20W package")
        if (reference, "20") not in nets.get("+5V", set()):
            failures.append(f"{reference} is not powered from +5V")
    for reference in ("U26", "U27"):
        if component_values.get(reference) != "TBD62083AFG":
            failures.append(f"{reference} is not a TBD62083AFG output driver")
        component = components_by_ref.get(reference)
        if not component or not (component.findtext("footprint") or "").strip().startswith(
            "Package_SO:SOP-18_7.495x11.515mm"
        ):
            failures.append(f"{reference} is not in the TBD62083AFG SOP-18 package")
        if (reference, "9") not in nets.get("ISO_GND", set()):
            failures.append(f"{reference} field ground is not ISO_GND")
        if (reference, "10") not in nets.get("+24V_FIELD", set()):
            failures.append(f"{reference} clamp pin is not +24V_FIELD")
    if any(
        reference in references
        for reference in ("U24", "U25", "C53", "C54")
    ):
        failures.append("Retired motion buffer U24/U25 or bypass remains")
    direct_control_pins = {"ESTOP_N": "53"}
    for direct_net, module_pin in direct_control_pins.items():
        refs = {ref for ref, _ in nets.get(direct_net, set())}
        if "MOD1" not in refs:
            failures.append(f"{direct_net} is not connected directly to the module")
        if ("MOD1", module_pin) not in nets.get(direct_net, set()):
            failures.append(f"{direct_net} is not on MOD1 pin {module_pin}")
        if any(component_values.get(ref) == "74HC165D" for ref in refs):
            failures.append(f"{direct_net} is incorrectly routed through the input chain")
    for module_pin, expected_net in (("9", "I2C_SDA"), ("23", "I2C_SCL")):
        if ("MOD1", module_pin) not in nets.get(expected_net, set()):
            failures.append(
                f"Hardware I2C1 {expected_net} is not on MOD1 pin {module_pin}"
            )
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
        "SR_OUT_SER": {("U13", "14")},
        "SR_OUT_CHAIN1": {("U13", "9"), ("U12", "14")},
        "SR_OUT_CHAIN2": {("U12", "9"), ("U11", "14")},
        "SR_OUT_CHAIN3": {("U11", "9"), ("U10", "14")},
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
    for reference in ("R10", "R11", "R12", "R13"):
        if reference in references:
            failures.append(f"Discrete shift-control resistor {reference} remains")
    shift_pullup_contract = {
        "1": "SR_SCK",
        "8": "GND",
        "2": "SR_PL_N",
        "7": "+3V3",
        "3": "SR_OUT_SER",
        "6": "GND",
        "4": "SR_LATCH",
        "5": "GND",
    }
    for pin, expected_net in shift_pullup_contract.items():
        if ("RN41", pin) not in nets.get(expected_net, set()):
            failures.append(
                f"RN41 pin {pin} is not connected to {expected_net}"
            )
    connector_values = set(component_values.values())
    for required in ("Dedicated E-stop loop",):
        if required not in connector_values:
            failures.append(f"Missing dedicated connector: {required}")
    for retired in (
        "Dedicated HOLD button input",
        "Dedicated START button input",
    ):
        if retired in connector_values:
            failures.append(f"Retired control connector remains: {retired}")
    for retired_net in ("HOLD_N", "START_N", "HOLD_FIELD", "START_FIELD"):
        if retired_net in nets:
            failures.append(f"Retired control net remains: {retired_net}")
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
    for channel in range(4):
        if f"AI{channel}" not in nets:
            failures.append(f"Missing analog input net AI{channel}")
        if f"AI{channel}_ADC" not in nets:
            failures.append(f"Missing analog ADC net AI{channel}_ADC")
        if f"AI{channel}_MID" in nets:
            failures.append(f"Legacy analog midpoint net AI{channel}_MID remains")
    analog_upper = {
        component.get("ref"): (component.findtext("value") or "").strip()
        for component in components
        if component.get("ref") in {"R61", "R64", "R67", "R182"}
    }
    if analog_upper != {
        "R61": "100k", "R64": "100k", "R67": "100k", "R182": "100k",
    }:
        failures.append(f"Analog upper resistors are not all 100k: {analog_upper}")
    analog_module_pins = {
        "8": "AI0_ADC", "7": "AI1_ADC", "22": "AI2_ADC", "21": "AI3_ADC",
    }
    for module_pin, expected_net in analog_module_pins.items():
        if ("MOD1", module_pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{expected_net} is not on MOD1 pin {module_pin}"
            )
    pwm_pins = ("5", "6", "20", "19")
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
    sd_module_pins = {
        "10": "SD_MISO_MCU",
        "11": "SD_SCK_MCU",
        "25": "SD_MOSI_MCU",
        "24": "SD_CS_MCU",
    }
    for module_pin, expected_net in sd_module_pins.items():
        if ("MOD1", module_pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{expected_net} is not on MOD1 pin {module_pin}"
            )
    if component_values.get("J36") != "Open-Smart TF Card Breakout":
        failures.append("J36 is not the Open-Smart TF card breakout header")
    microsd_pins = {
        "1": "SD_CD", "2": "SD_DAT1", "3": "SD_MISO",
        "4": "GND", "5": "SD_SCK", "6": "+3V3_SD",
        "7": "SD_MOSI", "8": "SD_CS_N", "9": "SD_DAT2",
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
    if j36_properties.get("Assembly") == "DNP":
        failures.append("J36 Open-Smart breakout header must be fitted")
    if "J19" in references:
        failures.append("Retired full-size SD socket J19 remains")
    for reference in ("R44", "R45", "R46", "R47", "R48", "R49"):
        if reference in references:
            failures.append(f"Discrete SD pull-up {reference} remains")
    sd_pullup_contract = {
        "1": "SD_CS_N", "8": "+3V3_SD",
        "2": "SD_MOSI", "7": "+3V3_SD",
        "3": "SD_MISO", "6": "+3V3_SD",
        "4": "SD_CD", "5": "+3V3_SD",
    }
    for pin, expected_net in sd_pullup_contract.items():
        if ("RN42", pin) not in nets.get(expected_net, set()):
            failures.append(f"RN42 pin {pin} is not connected to {expected_net}")
    sd_data_pullup_contract = {
        "1": "SD_DAT1", "8": "+3V3_SD",
        "2": "SD_DAT2", "7": "+3V3_SD",
    }
    for pin, expected_net in sd_data_pullup_contract.items():
        if ("RN43", pin) not in nets.get(expected_net, set()):
            failures.append(f"RN43 pin {pin} is not connected to {expected_net}")
    if component_values.get("RN44") != "4x22R":
        failures.append("RN44 is not the SD series-resistor network")
    sd_series_contract = {
        "1": "SD_CS_MCU", "8": "SD_CS_N",
        "2": "SD_MOSI_MCU", "7": "SD_MOSI",
        "3": "SD_SCK_MCU", "6": "SD_SCK",
        "4": "SD_MISO_MCU", "5": "SD_MISO",
    }
    for pin, expected_net in sd_series_contract.items():
        if ("RN44", pin) not in nets.get(expected_net, set()):
            failures.append(f"RN44 pin {pin} is not connected to {expected_net}")
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
        ("U42", "1"), ("U42", "19"), ("U43", "1"), ("U43", "19"),
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
    encoder_module_pins = {
        "26": "ENC0_A_3V3",
        "12": "ENC0_B_3V3",
        "27": "ENC0_Z_3V3",
        "13": "ENC1_A_3V3",
        "28": "ENC1_B_3V3",
        "14": "ENC1_Z_3V3",
        "29": "ENC2_A_3V3",
        "15": "ENC2_B_3V3",
        "30": "ENC2_Z_3V3",
    }
    for module_pin, expected_net in encoder_module_pins.items():
        if ("MOD1", module_pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{expected_net} is not on MOD1 encoder pin {module_pin}"
            )
    for retired_net in sorted(name for name in nets if name.startswith("EXP_")):
        failures.append(f"Retired expansion-input net {retired_net} remains")
    motion_connectors = {
        "J7": {
            1: "FIELD_IN1", 2: "FIELD_IN2", 3: "FIELD_IN3",
            4: "FIELD_IN4", 5: "FIELD_IN5", 6: "FIELD_IN6",
            7: "FIELD_IN7", 8: "FIELD_IN8",
        },
        "J8": {
            1: "FIELD_IN9", 2: "FIELD_IN10", 3: "FIELD_IN11",
            4: "FIELD_IN12", 5: "FIELD_IN13", 6: "FIELD_IN14",
            7: "FIELD_IN15", 8: "FIELD_IN16",
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
            1: "GND", 2: "AI0", 3: "AI1", 4: "AI2", 5: "AI3",
        },
        "J18": {1: "I2C_SDA", 2: "I2C_SCL", 3: "+3V3", 4: "+5V", 5: "GND"},
        "J10": {1: "EN_3AX", 2: "AX0_STEP", 3: "AX0_DIR"},
        "J11": {1: "EN_3AX", 2: "AX1_STEP", 3: "AX1_DIR"},
        "J28": {1: "EN_3AX", 2: "AX2_STEP", 3: "AX2_DIR"},
        "J29": {1: "EN_4AX", 2: "AX3_STEP", 3: "AX3_DIR"},
        "J30": {1: "EN_4AX", 2: "AX4_STEP", 3: "AX4_DIR"},
        "J46": {1: "EN_4AX", 2: "AX5_STEP", 3: "AX5_DIR"},
        "J47": {1: "EN_4AX", 2: "AX6_STEP", 3: "AX6_DIR"},
        "J40": {1: "AX0_ZERO", 2: "AX0_ERROR_N", 3: "GND"},
        "J41": {1: "AX1_ZERO", 2: "AX1_ERROR_N", 3: "GND"},
        "J42": {1: "AX2_ZERO", 2: "AX2_ERROR_N", 3: "GND"},
        "J43": {1: "AX3_ZERO", 2: "AX3_ERROR_N", 3: "GND"},
        "J48": {1: "AX4_ZERO", 2: "AX4_ERROR_N", 3: "GND"},
        "J49": {1: "AX5_ZERO", 2: "AX5_ERROR_N", 3: "GND"},
        "J50": {1: "AX6_ZERO", 2: "AX6_ERROR_N", 3: "GND"},
        "J2": {1: "+12V_BL", 2: "ISO_GND"},
        "J33": {1: "+24V_FIELD", 2: "ISO_GND"},
        "J45": {1: "+24V_FIELD", 2: "ISO_GND"},
        "J13": {1: "+5V_ENC", 2: "ENC0_A_5V", 3: "ENC0_B_5V", 4: "ENC0_Z_5V", 5: "GND"},
        "J14": {1: "+5V_ENC", 2: "ENC1_A_5V", 3: "ENC1_B_5V", 4: "ENC1_Z_5V", 5: "GND"},
        "J15": {1: "+5V_ENC", 2: "ENC2_A_5V", 3: "ENC2_B_5V", 4: "ENC2_Z_5V", 5: "GND"},
    }
    for reference, pins in motion_connectors.items():
        for pin, expected_net in pins.items():
            if expected_net is None:
                continue
            if (reference, str(pin)) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not on expected net {expected_net}"
                )
    connector_footprints = {
        "J7": "PhoenixContact_MCV_1,5_8-G-3.5_1x08_P3.50mm_Vertical",
        "J8": "PhoenixContact_MCV_1,5_8-G-3.5_1x08_P3.50mm_Vertical",
        "J12": "PhoenixContact_MCV_1,5_8-G-3.5_1x08_P3.50mm_Vertical",
        "J32": "PhoenixContact_MCV_1,5_8-G-3.5_1x08_P3.50mm_Vertical",
        "J10": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J11": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J28": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J29": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J30": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J46": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J47": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J13": "PhoenixContact_MCV_1,5_5-G-3.5_1x05_P3.50mm_Vertical",
        "J14": "PhoenixContact_MCV_1,5_5-G-3.5_1x05_P3.50mm_Vertical",
        "J15": "PhoenixContact_MCV_1,5_5-G-3.5_1x05_P3.50mm_Vertical",
        "J40": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J41": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J42": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J43": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J48": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J49": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J50": "PhoenixContact_MCV_1,5_3-G-3.5_1x03_P3.50mm_Vertical",
        "J18": "PhoenixContact_MCV_1,5_5-G-3.5_1x05_P3.50mm_Vertical",
        "J45": "PhoenixContact_MCV_1,5_2-G-3.5_1x02_P3.50mm_Vertical",
        "J36": "PinHeader_1x09_P2.54mm_Vertical",
    }
    for reference, expected_name in connector_footprints.items():
        component = components_by_ref.get(reference)
        footprint = (
            (component.findtext("footprint") or "").strip()
            if component is not None
            else ""
        )
        if footprint.rsplit(":", 1)[-1] != expected_name:
            failures.append(
                f"{reference} is not in the expected single-row footprint"
            )
    if component_values.get("U3") != "LMR36510ADDAR":
        failures.append("U3 is not the isolated 24 V to 12 V LMR36510 buck")
    u3_contract = {
        "1": "ISO_GND", "2": "VIN_BL_PROT", "3": "VIN_BL_PROT",
        "5": "FB12", "6": "VCC12", "7": "BUCK12_BST",
        "8": "BUCK12_SW", "9": "ISO_GND",
    }
    for pin, expected_net in u3_contract.items():
        if ("U3", pin) not in nets.get(expected_net, set()):
            failures.append(f"U3 pin {pin} is not {expected_net}")
    if ("D3", "1") not in nets.get("VIN_BL_PROT", set()):
        failures.append("D3 cathode is not on VIN_BL_PROT")
    if ("D3", "2") not in nets.get("+24V_FIELD", set()):
        failures.append("D3 anode is not on +24V_FIELD")
    for reference, value in (
        ("L2", "47uH 1.5A"), ("R126", "100k"),
        ("R127", "10k"), ("R128", "100k"),
    ):
        if component_values.get(reference) != value:
            failures.append(f"{reference} is not {value}")
    if {"C55", "C56", "C117"} & set(references):
        failures.append("Redundant ULN DO_COM bypass capacitors remain")
    for retired_net in ("AUX_GATE", "DO14_GATE", "DO15_GATE"):
        if retired_net in nets:
            failures.append(f"Retired MOSFET output net {retired_net} remains")
    plc_register_pin_numbers = {
        "U8": tuple(range(1, 9)),
        "U9": tuple(range(9, 17)),
    }
    plc_data_pins = ("11", "12", "13", "14", "3", "4", "5", "6")
    for reference, numbers in plc_register_pin_numbers.items():
        for data_pin, number in zip(plc_data_pins, numbers):
            if (reference, data_pin) not in nets.get(f"PLC_IN{number}_N", set()):
                failures.append(
                    f"{reference} data pin {data_pin} is not PLC_IN{number}_N"
                )
    status_register_contracts = {
        "U6": {
            "11": "AX0_ZERO", "12": "AX0_ERROR_N",
            "13": "AX6_ZERO", "14": "AX6_ERROR_N",
            "3": "AX4_ERROR_N", "4": "AX4_ZERO",
            "5": "AX5_ERROR_N", "6": "AX5_ZERO",
        },
        "U7": {
            "11": "AX3_ZERO", "12": "AX3_ERROR_N",
            "13": "GND", "14": "GND",
            "3": "AX1_ZERO", "4": "AX1_ERROR_N",
            "5": "AX2_ZERO", "6": "AX2_ERROR_N",
        },
    }
    for reference, pin_contract in status_register_contracts.items():
        for data_pin, expected_net in pin_contract.items():
            if (reference, data_pin) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} data pin {data_pin} is not {expected_net}"
                )
    keyboard_network_pins = {
        ("RN8", "1", "GND"), ("RN8", "8", "OUT7"),
        ("RN8", "2", "GND"), ("RN8", "7", "OUT6"),
        ("RN8", "3", "GND"), ("RN8", "6", "OUT5"),
        ("RN8", "4", "GND"), ("RN8", "5", "OUT4"),
        ("RN9", "1", "OUT0"), ("RN9", "8", "GND"),
        ("RN9", "2", "OUT1"), ("RN9", "7", "GND"),
        ("RN9", "3", "OUT2"), ("RN9", "6", "GND"),
        ("RN9", "4", "OUT3"), ("RN9", "5", "GND"),
        ("RN10", "1", "OUT8"), ("RN10", "8", "GND"),
        ("RN10", "2", "OUT9"), ("RN10", "7", "GND"),
        ("RN10", "3", "OUT10"), ("RN10", "6", "GND"),
        ("RN10", "4", "OUT11"), ("RN10", "5", "GND"),
        ("RN11", "1", "GND"), ("RN11", "8", "OUT15"),
        ("RN11", "2", "GND"), ("RN11", "7", "OUT14"),
        ("RN11", "3", "GND"), ("RN11", "6", "OUT13"),
        ("RN11", "4", "GND"), ("RN11", "5", "OUT12"),
        ("RN12", "1", "OUT19"), ("RN12", "8", "GND"),
        ("RN12", "2", "OUT18"), ("RN12", "7", "GND"),
        ("RN12", "3", "OUT17"), ("RN12", "6", "GND"),
        ("RN12", "4", "OUT16"), ("RN12", "5", "GND"),
        ("RN13", "1", "OUT23"), ("RN13", "8", "GND"),
        ("RN13", "2", "OUT22"), ("RN13", "7", "GND"),
        ("RN13", "3", "OUT21"), ("RN13", "6", "GND"),
        ("RN13", "4", "OUT20"), ("RN13", "5", "GND"),
        ("RN30", "1", "OUT27"), ("RN30", "8", "GND"),
        ("RN30", "2", "OUT26"), ("RN30", "7", "GND"),
        ("RN30", "3", "OUT25"), ("RN30", "6", "GND"),
        ("RN30", "4", "OUT24"), ("RN30", "5", "GND"),
        ("RN31", "1", "OUT31"), ("RN31", "8", "GND"),
        ("RN31", "2", "OUT30"), ("RN31", "7", "GND"),
        ("RN31", "3", "OUT29"), ("RN31", "6", "GND"),
        ("RN31", "4", "OUT28"), ("RN31", "5", "GND"),
    }
    for reference, pin, expected_net in keyboard_network_pins:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected network {expected_net}"
            )
    connected_pads = {
        endpoint for endpoints in nets.values() for endpoint in endpoints
    }
    spare_array_pins = {}
    for reference, pins in spare_array_pins.items():
        for pin in pins:
            if (reference, pin) in connected_pads:
                failures.append(f"{reference} spare pin {pin} is connected")
    decoupling_required = {
        "U1", "U2", "U3", "U37", "U38",
        "U6", "U7", "U8", "U9", "U10", "U11", "U12", "U13",
        "U28", "U34", "U42", "U43",
    }
    decouplers = [
        reference
        for reference, value in component_values.items()
        if reference.startswith("C") and value.startswith("100nF")
    ]
    for reference in sorted(decoupling_required):
        return_net = "ISO_GND" if reference == "U3" else "GND"
        supply_nets = {
            net
            for net in component_nets.get(reference, set())
            if net.startswith(("+", "VIN"))
            and not net.endswith(("_SW", "_BST"))
        }
        has_local = any(
            supply_nets & component_nets.get(capacitor, set())
            and return_net in component_nets.get(capacitor, set())
            for capacitor in decouplers
        )
        if not has_local:
            failures.append(
                f"{reference} has no 100nF capacitor to {return_net}"
            )

    fitted_passive_lvds = {"RN26", "RN27"}
    for reference in sorted(fitted_passive_lvds):
        component = components_by_ref.get(reference)
        assembly = next(
            (
                prop.get("value", "")
                for prop in component.findall("property")
                if prop.get("name") == "Assembly"
            ),
            "",
        ) if component is not None else ""
        if assembly == "DNP":
            failures.append(f"Passive LVDS component {reference} must be fitted")

    lvds_required = {
        ("RN26", "1", "HSTX_D0_P"),
        ("RN26", "8", "LVDS_D0_P"),
        ("RN26", "2", "HSTX_D0_N"),
        ("RN26", "7", "LVDS_D0_N"),
        ("RN26", "3", "HSTX_D1_P"),
        ("RN26", "6", "LVDS_D1_P"),
        ("RN26", "4", "HSTX_D1_N"),
        ("RN26", "5", "LVDS_D1_N"),
        ("RN27", "1", "HSTX_D2_P"),
        ("RN27", "8", "LVDS_D2_P"),
        ("RN27", "2", "HSTX_D2_N"),
        ("RN27", "7", "LVDS_D2_N"),
        ("RN27", "3", "HSTX_CLK_P"),
        ("RN27", "6", "LVDS_CLK_P"),
        ("RN27", "4", "HSTX_CLK_N"),
        ("RN27", "5", "LVDS_CLK_N"),
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
    if "U41" in references:
        failures.append("Retired LVDS driver U41 remains")
    if "C106" in references:
        failures.append("Retired LVDS driver bypass C106 remains")
    removed = {
        "C9", "C12", "C18", "C19", "C20", "C21", "C57", "C78", "C81", "C82", "C83",
        "C1", "C84", "C85", "D6", "D7", "D8", "FB3", "JP1",
        "Q1", "Q2", "Q3", "Q4", "Q8", "R2", "R3", "R6", "R7", "R8",
        "R14", "R15",
        "R42", "R43",
        *(f"R{index}" for index in range(132, 148)),
        *(f"R{index}" for index in range(148, 165)),
        "J6", "J19", "J26", "J31", "J34", "J35", "J37", "J38", "J39",
        "J44", "J51", "R131",
        "JP2", "JP3", "JP4",
        "R17", "R50", "R51", "R52", "R53", "R75", "R108", "R109",
        *(f"R{index}" for index in range(44, 50)),
        "D11", "D12", "D54", "D55", "C106", "U41",
        "U45", "U46",
        "U36", "U39", "R129", "R130",
        *(f"R{index}" for index in range(166, 174)),
        *(f"D{index}" for index in range(65, 73)),
        *(f"D{index}" for index in range(81, 89)),
        "U40", "F4", "D56", "C103", "C105",
        "RN23", "RN25",
        *(f"R{index}" for index in range(174, 182)),
        *(f"D{index}" for index in range(73, 81)),
        *(f"D{index}" for index in range(89, 97)),
        "SW1", "U4", "U14", "U15", "U16", "U17", "U22", "U23", "U44", "U65",
        *(f"U{index}" for index in range(47, 61)),
        *(f"U{index}" for index in range(66, 78)),
        "U24", "U25", "C53", "C54", "C55", "C56", "C117",
        "Q5", "Q6", "Q7", "R113", "R114", "R115", "R116", "R117",
        "RN1", "RN2", "RN3", "RN4", "RN5", "RN6", "RN7",
        "RN14", "RN15",
        *(f"RN{index}" for index in range(16, 23)),
        "RN24",
        "J9", "J16", "J17", "J27",
        *(f"R{index}" for index in range(55, 59)),
        "R54",
        *(f"R{index}" for index in range(76, 92)),
        *(f"C{index}" for index in range(30, 53)),
        *(f"C{index}" for index in range(59, 67)),
    }
    remaining = sorted(removed & set(references))
    if remaining:
        failures.append(f"Obsolete components remain: {remaining}")

    expected_optos = (
        {f"U{index}" for index in range(18, 22)}
        | {f"U{index}" for index in range(61, 65)}
    )
    opto_refs = {
        reference
        for reference, value in component_values.items()
        if value == "TLP291-4"
    }
    if opto_refs != expected_optos:
        failures.append(
            f"Unexpected TLP291-4 optocoupler set: {sorted(opto_refs)}"
        )
    for reference in sorted(expected_optos):
        footprint = next(
            (
                (component.findtext("footprint") or "").strip()
                for component in components
                if component.get("ref") == reference
            ),
            "",
        )
        if footprint != "Package_SO:SOIC-16_4.55x10.3mm_P1.27mm":
            failures.append(f"{reference} does not use the TLP291-4 SOIC-16 footprint")
    if component_values.get("U35") != "TLP291":
        failures.append("U35 is not the single-channel TLP291 E-stop optocoupler")
    u35_component = components_by_ref.get("U35")
    if not u35_component or (u35_component.findtext("footprint") or "").strip() != (
        "Package_SO:SOIC-4_4.55x2.6mm_P1.27mm"
    ):
        failures.append("U35 does not use the TLP291 SOIC-4 footprint")

    for reference, output_net in (("R74", "ESTOP_N"),):
        if component_values.get(reference) != "4.7k":
            failures.append(f"{reference} is not a 4.7k safety pull-up")
        if (reference, "1") not in nets.get(output_net, set()):
            failures.append(f"{reference} is not connected to {output_net}")
        if (reference, "2") not in nets.get("+3V3", set()):
            failures.append(f"{reference} is not pulled to +3V3")

    isolated_input_contracts = []
    for bit in range(16):
        number = bit + 1
        isolated_input_contracts.append(
            {
                "channel": f"PLC input {number}",
                "R": (f"R{18 + bit}", "2.2k", {f"FLD_LED{number}_A", f"FLD_OPTO{number}_A"}),
                "LED": (f"D{13 + 2 * bit}", "indicator", {f"FIELD_IN{number}", f"FLD_LED{number}_A"}),
                "D": (
                    f"D{14 + 2 * bit}",
                    "1N4148WS",
                    {f"FLD_LED{number}_A", "ISO_GND"},
                ),
                "OPTO": (
                    ("U21", "U20", "U19", "U18")[bit // 4],
                    "TLP291-4",
                    {
                        f"FLD_OPTO{number}_A",
                        "ISO_GND",
                        "GND",
                        f"PLC_IN{number}_N",
                    },
                ),
            }
        )
    isolated_input_contracts.extend(
        (
            {
                "channel": "E-stop",
                "R": ("R16", "2.2k", {"ESTOP_LED_A", "ESTOP_OPTO_A"}),
                "LED": ("D9", "indicator", {"ESTOP_FIELD", "ESTOP_LED_A"}),
                "D": ("D10", "1N4148WS", {"ESTOP_LED_A", "ISO_GND"}),
                "OPTO": (
                    "U35",
                    "TLP291",
                    {"ESTOP_OPTO_A", "ISO_GND", "GND", "ESTOP_N"},
                ),
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

    isolated_input_pins = []
    for bit in range(16):
        number = bit + 1
        isolated_input_pins.extend(
            (
                (f"R{18 + bit}", "1", f"FLD_LED{number}_A"),
                (f"R{18 + bit}", "2", f"FLD_OPTO{number}_A"),
                (f"D{13 + 2 * bit}", "1", f"FLD_LED{number}_A"),
                (f"D{13 + 2 * bit}", "2", f"FIELD_IN{number}"),
                (f"D{14 + 2 * bit}", "1", f"FLD_LED{number}_A"),
                (f"D{14 + 2 * bit}", "2", "ISO_GND"),
            )
        )
    isolated_input_pins.extend(
        (
            ("R16", "1", "ESTOP_LED_A"),
            ("R16", "2", "ESTOP_OPTO_A"),
            ("D9", "1", "ESTOP_LED_A"),
            ("D9", "2", "ESTOP_FIELD"),
            ("D10", "1", "ESTOP_LED_A"),
            ("D10", "2", "ISO_GND"),
        )
    )
    for reference, pin, expected_net in isolated_input_pins:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"Input indicator chain {reference} pin {pin} is not "
                f"{expected_net}"
            )

    for bit in range(16):
        number = bit + 1
        reference = ("U21", "U20", "U19", "U18")[bit // 4]
        slot = bit % 4
        pin_contract = {
            str(1 + slot * 2): f"FLD_OPTO{number}_A",
            str(2 + slot * 2): "ISO_GND",
            str(15 - slot * 2): "GND",
            str(16 - slot * 2): f"PLC_IN{number}_N",
        }
        for pin, expected_net in pin_contract.items():
            if (reference, pin) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not {expected_net}"
                )
    estop_opto_pins = {
        "1": "ESTOP_OPTO_A",
        "2": "ISO_GND",
        "3": "GND",
        "4": "ESTOP_N",
    }
    for pin, expected_net in estop_opto_pins.items():
        if ("U35", pin) not in nets.get(expected_net, set()):
            failures.append(f"U35 pin {pin} is not {expected_net}")

    pullup_references = ("RN35", "RN34", "RN33", "RN32")
    for group in range(4):
        reference = pullup_references[group]
        if component_values.get(reference) != "4x10k":
            failures.append(f"{reference} is not the PLC 4x10k pull-up network")
        for channel in range(4):
            number = group * 4 + 4 - channel
            signal_pin = str(channel + 1)
            supply_pin = str(8 - channel)
            if (reference, signal_pin) not in nets.get(
                f"PLC_IN{number}_N", set()
            ):
                failures.append(
                    f"{reference} pin {signal_pin} is not PLC_IN{number}_N"
                )
            if (reference, supply_pin) not in nets.get("+3V3", set()):
                failures.append(f"{reference} pin {supply_pin} is not +3V3")

    if component_values.get("U1") != "LMR36510ADDAR":
        failures.append("U1 is not the specified LMR36510 buck")
    for retired_net in (
        "+5V_ISO_IN", "+12V_FIELD", "+12V_RAW", "DO_COM", "DO_GND",
        "BL_PWM_MCU", "BL_PWM", "BL_SW_GATE", "BL_LED_N", "AUX_OUT",
        "FIELD_COM0", "FIELD_COM1", "FIELD_SAFETY_COM",
    ):
        if retired_net in nets:
            failures.append(f"Retired isolated-field net {retired_net} remains")
    for prefix in ("MOTION", "AX0_SERVO_", "AX1_SERVO_", "AX2_SERVO_",
                   "AX3_SERVO_", "AX4_SERVO_", "SERVO_DIAG_"):
        for retired_net in sorted(name for name in nets if name.startswith(prefix)):
            failures.append(f"Retired motion/diagnostic net {retired_net} remains")
    if ("J33", "1") not in nets.get("+24V_FIELD", set()):
        failures.append("J33 pin 1 is not the external field +24 V input")
    if ("J33", "2") not in nets.get("ISO_GND", set()):
        failures.append("J33 pin 2 is not the isolated field return")
    if ("J45", "1") not in nets.get("+24V_FIELD", set()):
        failures.append("J45 pin 1 is not in parallel with J33")
    if ("J45", "2") not in nets.get("ISO_GND", set()):
        failures.append("J45 pin 2 is not in parallel with J33")
    for pin, channel in (("2", "E-stop"),):
        if ("U35", pin) not in nets.get("ISO_GND", set()):
            failures.append(f"{channel} optocoupler return is not on ISO_GND")
    if not {("U1", "2"), ("U1", "3")}.issubset(nets.get("VIN_PROT", set())):
        failures.append("LMR36510 EN pin is not tied to its VIN pin")
    for pin in ("3", "18", "64"):
        if any(("MOD1", pin) in endpoints for endpoints in nets.values()):
            failures.append(f"WeAct 3V3 output pin {pin} must remain local to the module")
    if ("MOD1", "31") not in nets.get("+5V", set()):
        failures.append("WeAct 5 V input is not connected to the main 5 V rail")
    if component_values.get("D2") != "SS16":
        failures.append("D2 is not the intended 1 A input diode")
    if ("D2", "1") not in nets.get("VIN_PROT", set()):
        failures.append("D2 cathode is not on VIN_PROT")
    if ("D2", "2") not in nets.get("VIN_FUSED", set()):
        failures.append("D2 anode is not on VIN_FUSED")
    if "Q1" in references or "Q1_GATE" in nets:
        failures.append("Retired Q1 input MOSFET or gate net remains")
    for expected in (("U1", "4"), ("MOD1", "50"), ("R73", "1")):
        if expected not in nets.get("PWR_GOOD_N", set()):
            failures.append(f"Power-good network is missing {expected}")
    if {("U1", "6"), ("C91", "1")} - nets.get("VCC5", set()):
        failures.append("LMR36510 VCC bypass capacitor is not connected")
    if component_values.get("R70") != "33k":
        failures.append("LMR36510 feedback upper resistor is not 33k")
    if component_values.get("R71") != "100k":
        failures.append("LMR36510 feedback upper resistor is not 100k")
    if component_values.get("R72") != "33k":
        failures.append("LMR36510 feedback lower resistor is not 33k")
    if component_values.get("U2") != "AMS1117-3.3":
        failures.append("Peripheral 3.3 V rail is not supplied by its dedicated LDO")
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
