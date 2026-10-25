"""Verify the generated hierarchy and critical LeanCam net contracts."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


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
    for bit in range(16):
        if f"MOTION{bit}" not in nets:
            failures.append(f"Missing motion output {bit}")
    for bit in range(8):
        if f"DO{bit}" not in nets:
            failures.append(f"Missing ULN output {bit}")
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

    # Bits 16-23 drive the ULN arrays directly from the 3.3 V 595.
    uln_contracts = {
        16: ("U12", "1", "U26", "4", "13"),
        17: ("U12", "2", "U26", "3", "14"),
        18: ("U12", "3", "U26", "2", "15"),
        19: ("U12", "4", "U26", "1", "16"),
        20: ("U12", "5", "U27", "4", "13"),
        21: ("U12", "6", "U27", "3", "14"),
        22: ("U12", "7", "U27", "2", "15"),
        23: ("U12", "15", "U27", "1", "16"),
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

    tpd_refs = {
        component.get("ref")
        for component in components
        if (component.findtext("value") or "").strip() == "TPD4E05U06DQA"
    }
    if len(tpd_refs) != 3:
        failures.append(f"Expected three HDMI ESD arrays, found {len(tpd_refs)}")
    for net, endpoints in nets.items():
        if (
            any(ref in tpd_refs for ref, _ in endpoints)
            and net != "GND"
            and not net.startswith("HDMI_")
        ):
            failures.append(f"Non-HDMI ESD connection remains on {net}")

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
    if solder_jumpers:
        failures.append(f"Unexpected solder jumpers: {solder_jumpers}")
    mode_headers = [
        component.get("ref")
        for component in components
        if component.get("ref", "").startswith("JP")
        and "PinHeader_1x03" in (component.findtext("footprint") or "")
    ]
    if set(mode_headers) != {"JP2", "JP3", "JP4"}:
        failures.append(f"Unexpected input mode headers: {mode_headers}")
    if any(name.startswith(("BL_", "BLV")) for name in nets if name != "BL_PWM"):
        failures.append("Removed backlight power-switching nets remain")
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
    for reference in ("RN16", "RN17", "RN18", "RN19", "RN20", "RN21"):
        if reference not in references:
            failures.append(f"Missing 100 ohm series array {reference}")
    motion_array_maps = {
        "RN16": {1: (2, 3), 2: (3, 2), 3: (0, 1), 4: (1, 0)},
        "RN17": {1: (6, 7), 2: (7, 6), 3: (4, 5), 4: (5, 4)},
        "RN18": {1: (11, 11), 2: (10, 10), 3: (8, 9), 4: (9, 8)},
        "RN19": {1: (15, 15), 2: (14, 14), 3: (13, 13), 4: (12, 12)},
    }
    for reference, channel_bits in motion_array_maps.items():
        for channel, (source_bit, output_bit) in channel_bits.items():
            source_pin = str(channel)
            connector_pin = str(9 - channel)
            if (reference, source_pin) not in nets.get(f"BUFY{source_bit}", set()):
                failures.append(
                    f"{reference} source channel {channel} is not BUFY{source_bit}"
                )
            if (reference, connector_pin) not in nets.get(f"MOTION{output_bit}", set()):
                failures.append(
                    f"{reference} output channel {channel} is not MOTION{output_bit}"
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
    if ("MOD1", "49") not in nets.get("BL_PWM", set()):
        failures.append("BL_PWM is not driven directly by MOD1 GPIO1")
    if ("J22", "6") not in nets.get("BL_PWM", set()):
        failures.append("BL_PWM is not exposed on LCD connector J22 pin 6")
    for legacy in ("BL_EN", "BL_EN_REQ", "BL_VIN", "BL_RAW", "BL_GATE", "BL_GATE_NPN"):
        if legacy in nets:
            failures.append(f"Legacy backlight net {legacy} remains")
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
        "J10": {1: "MOTION3", 2: "MOTION1", 3: "MOTION0", 4: "GND"},
        "J11": {1: "MOTION4", 2: "MOTION2", 3: "MOTION5", 4: "GND"},
        "J28": {1: "MOTION9", 2: "MOTION7", 3: "MOTION6", 4: "GND"},
        "J29": {1: "MOTION10", 2: "MOTION8", 3: "MOTION11", 4: "GND"},
        "J30": {1: "MOTION15", 2: "MOTION13", 3: "MOTION12", 4: "GND"},
        "J31": {1: "AUX_OUT", 2: "GND"},
    }
    for reference, pins in motion_connectors.items():
        for pin, expected_net in pins.items():
            if (reference, str(pin)) not in nets.get(expected_net, set()):
                failures.append(
                    f"{reference} pin {pin} is not on expected net {expected_net}"
                )
    aux_mosfet = {
        ("R112", "1", "MOTION14"),
        ("R112", "2", "AUX_GATE"),
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
    # The physical connector order is chosen for the shortest, crossing-free
    # PCB fanout. Firmware maps these positions to logical PLC channels.
    for block, reference in ((0, "J7"), (1, "J8")):
        for local in range(8):
            number = (9 + local) if block == 0 else (1 + local)
            signal_pin = str(2 * local + 1)
            common_pin = str(2 * local + 2)
            if (reference, signal_pin) not in nets.get(f"FIELD_IN{number}", set()):
                failures.append(
                    f"{reference} pin {signal_pin} is not FIELD_IN{number}"
                )
            if (reference, common_pin) not in nets.get(f"FIELD_COM{block}", set()):
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
        ("RN20", "1", "KOUT0"), ("RN20", "8", "OUT24"),
        ("RN20", "2", "OUT25"), ("RN20", "7", "KOUT1"),
        ("RN20", "3", "KOUT2"), ("RN20", "6", "OUT26"),
        ("RN20", "4", "OUT27"), ("RN20", "5", "KOUT3"),
        ("RN21", "1", "KOUT4"), ("RN21", "8", "OUT28"),
        ("RN21", "2", "KOUT5"), ("RN21", "7", "OUT29"),
        ("RN21", "3", "KOUT6"), ("RN21", "6", "OUT30"),
        ("RN21", "4", "KOUT7"), ("RN21", "5", "OUT31"),
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
    decoupling_required = {
        "U1", "U2", "U37", "U38",
        "U6", "U7", "U8", "U9", "U10", "U11", "U12", "U13",
        "U24", "U25", "U28", "U34",
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
        "RN28", "RN29",
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
        ("RN26", "1", "HSTX_D1_P"),
        ("RN26", "8", "LVDS_D1_P"),
        ("RN26", "2", "HSTX_D1_N"),
        ("RN26", "7", "LVDS_D1_N"),
        ("RN26", "3", "HSTX_D0_P"),
        ("RN26", "6", "LVDS_D0_P"),
        ("RN26", "4", "HSTX_D0_N"),
        ("RN26", "5", "LVDS_D0_N"),
        ("RN27", "1", "HSTX_CLK_P"),
        ("RN27", "8", "LVDS_CLK_P"),
        ("RN27", "2", "HSTX_CLK_N"),
        ("RN27", "7", "LVDS_CLK_N"),
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
    hdmi_required = {
        ("RN28", "1", "HSTX_D2_P"), ("RN28", "8", "HDMI_D2_P"),
        ("RN28", "2", "HSTX_D2_N"), ("RN28", "7", "HDMI_D2_N"),
        ("RN28", "3", "HSTX_D1_P"), ("RN28", "6", "HDMI_D1_P"),
        ("RN28", "4", "HSTX_D1_N"), ("RN28", "5", "HDMI_D1_N"),
        ("RN29", "1", "HSTX_D0_P"), ("RN29", "8", "HDMI_D0_P"),
        ("RN29", "2", "HSTX_D0_N"), ("RN29", "7", "HDMI_D0_N"),
        ("RN29", "3", "HSTX_CLK_P"), ("RN29", "6", "HDMI_CLK_P"),
        ("RN29", "4", "HSTX_CLK_N"), ("RN29", "5", "HDMI_CLK_N"),
    }
    for reference, pin, expected_net in hdmi_required:
        if (reference, pin) not in nets.get(expected_net, set()):
            failures.append(
                f"{reference} pin {pin} is not on expected HDMI net {expected_net}"
            )

    removed = {
        "C9", "C12", "C18", "C19", "C20", "C21", "C78", "C81", "C82", "C83",
        "C84", "C85", "D3", "D6", "D7", "D8", "FB3", "J2", "JP1", "L2",
        "Q2", "Q3", "Q4", "R2", "R3", "R6", "R7", "R8", "R14", "R15",
        "R42", "R43", "SW1", "U3", "U4", "U14", "U15", "U16", "U17", "U22", "U23",
        "RN1", "RN2", "RN3", "RN4", "RN5", "RN23", "RN25",
        "RN30", "RN31", "RN32", "RN33",
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

    expected_pullups = {"R74", "R75", "R109"} | {
        f"R{index}" for index in range(76, 92)
    }
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
                "RV": (f"R{76 + bit}", "4.7k", {f"PLC_IN{number}_N", "+3V3"}),
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
    for reference, bank in (("U18", 0), ("U19", 0), ("U20", 1), ("U21", 1)):
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
    if component_values.get("U34") != "AMS1117-3.3":
        failures.append("ESP8266 does not have its dedicated 3.3 V regulator")
    if ("U34", "2") not in nets.get("+3V3_WIFI", set()):
        failures.append("ESP8266 regulator is not connected to +3V3_WIFI")

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
