"""Short, stable names shared by the schematic, PCB and verification tools."""

from __future__ import annotations

import re


AXIS_REMAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 6, 5: 5, 6: 4}

STATIC_NAMES = {
    "+24V_FIELD": "PLC_24V",
    "ISO_GND": "PLC_0V",
    "+12V_BL": "BL_12V",
    "+12V_AO": "AO_12V",
    "+5V": "5V",
    "+3V3": "3V3",
    "+3V3_A": "ADC_3V3",
    "+3V3_SD": "SD_3V3",
    "+3V3_WIFI": "WIFI_3V3",
    "+5V_ENC": "ENC_5V",
    "VIN_RAW": "VIN",
    "VIN_FUSED": "VIN_F",
    "VIN_PROT": "VIN_P",
    "VIN_BL_PROT": "BL_VIN",
    "VCC5": "B5_VCC",
    "VCC12": "B12_VCC",
    "BUCK5_BST": "B5_BST",
    "BUCK5_SW": "B5_SW",
    "BUCK12_BST": "B12_BST",
    "BUCK12_SW": "B12_SW",
    "FB5_TOP": "FB5_T",
    "PWR_GOOD_N": "PG_N",
    "PWR5_LEDA": "P5V_LED",
    "PWR3_LEDA": "P3V3_LED",
    "ESTOP_FIELD": "ESTOP_IN",
    "ESTOP_LED_A": "ESTOP_L",
    "ESTOP_OPTO_A": "ESTOP_O",
    "ESTOP_N": "ESTOP",
    "EN_3AX": "EN3",
    "EN_4AX": "EN4",
    "SR_IN_DS0": "IN0",
    "SR_IN_CHAIN1": "IN1",
    "SR_IN_CHAIN2": "IN2",
    "SR_IN_CHAIN3": "IN3",
    "SR_IN_Q7": "Q7",
    "SR_OUT_SER": "SER0",
    "SR_OUT_CHAIN1": "SER1",
    "SR_OUT_CHAIN2": "SER2",
    "SR_OUT_CHAIN3": "SER3",
    "SR_SCK": "SCK",
    "SR_LATCH": "LAT",
    "SR_PL_N": "PL",
    "SD_MISO_MCU": "SPI_SO",
    "SD_MISO": "SD_SO",
    "SD_MOSI_MCU": "SPI_SI",
    "SD_MOSI": "SD_SI",
    "SD_SCK_MCU": "SPI_CK",
    "SD_SCK": "SD_CK",
    "SD_CS_MCU": "SPI_CS",
    "SD_CS_N": "SD_CS",
    "SD_CD_MCU": "CD",
    "WIFI_GPIO0": "ESP_IO0",
    "WIFI_GPIO2": "ESP_IO2",
    "WIFI_EN": "ESP_EN",
    "WIFI_RST": "ESP_RST",
    "WIFI_RX": "UART_RX",
    "WIFI_TX": "UART_TX",
}

CONNECTOR_LABEL_NAMES = {
    "24+ -": "24+ GND",
    "BL12+ PLC-": "BL12+ PLC_0V",
    "ESTOP PLC-": "ESTOP PLC_0V",
    "PLC24+ PLC-": "PLC24+ PLC_0V",
    "5V A B Z -": "5V A B Z GND",
    "SDA SCL 3V3 5V -": "SDA SCL 3V3 5V GND",
    "3V3 - IO4 IO5 IO6 IO7 IO8": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "- AI0 AI1 AI2 AI3": "GND AI0 AI1 AI2 AI3",
    "- AO0 AO1 AO2 AO3": "GND AO0 AO1 AO2 AO3",
    **{f"- ERR{number} Z{number}": f"GND ERR{number} Z{number}" for number in range(7)},
    "24+ GND": "24+ GND",
    "BL12+ PLC_0V": "BL12+ PLC_0V",
    "ESTOP PLC_0V": "ESTOP PLC_0V",
    "PLC24+ PLC_0V": "PLC24+ PLC_0V",
    "5V A B Z GND": "5V A B Z GND",
    "+5V A0 B0 Z0 GND": "+5V A0 B0 Z0 GND",
    "+5V A1 B1 Z1 GND": "+5V A1 B1 Z1 GND",
    "+5V A2 B2 Z2 GND": "+5V A2 B2 Z2 GND",
    "SDA SCL 3V3 5V GND": "SDA SCL 3V3 5V GND",
    "3V3 GND IO4 IO5 IO6 IO7 IO8": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "GND AI0 AI1 AI2 AI3": "GND AI0 AI1 AI2 AI3",
    "GND AO0 AO1 AO2 AO3": "GND AO0 AO1 AO2 AO3",
    **{f"GND ERR{number} Z{number}": f"GND ERR{number} Z{number}" for number in range(7)},
    "GND 24+": "GND 24+",
    "PLC_0V BL12+": "PLC_0V BL12+",
    "PLC_0V PLC24+": "PLC_0V PLC24+",
}

TEXT_RENAMES = {
    "24 V DC input": "24+ GND",
    "Backlight: +12V_BL, ISO_GND": "BL12+ PLC_0V",
    "Dedicated E-stop loop": "ESTOP PLC_0V",
    "External isolated field 24 V supply / relay common A": "PLC24+ PLC_0V",
    "External isolated field 24 V supply / relay common B": "PLC24+ PLC_0V",
    "External isolated field 24 V supply / relay common": "PLC24+ PLC_0V",
    "PLC 24V / 0V A": "PLC24+ PLC_0V",
    "PLC 24V / 0V B": "PLC24+ PLC_0V",
    "PLC 24V / 0V": "PLC24+ PLC_0V",
    "24V IN": "24+ GND",
    "24V + / -": "24+ GND",
    "BL 12V / 0V": "BL12+ PLC_0V",
    "BL 12+ / PLC -": "BL12+ PLC_0V",
    "ESTOP / 0V": "ESTOP PLC_0V",
    "ESTOP / PLC -": "ESTOP PLC_0V",
    "PLC 24+ / PLC -": "PLC24+ PLC_0V",
    "PLC positions 1-8 signals": "I01 I02 I03 I04 I05 I06 I07 I08",
    "PLC positions 9-16 signals": "I09 I10 I11 I12 I13 I14 I15 I16",
    "PLC IN 1-8": "I01 I02 I03 I04 I05 I06 I07 I08",
    "PLC IN 9-16": "I09 I10 I11 I12 I13 I14 I15 I16",
    "General outputs 0-7": "D01 D02 D03 D04 D05 D06 D07 D08",
    "General outputs 8-15": "D09 D10 D11 D12 D13 D14 D15 D16",
    "OUT 0-7": "D01 D02 D03 D04 D05 D06 D07 D08",
    "OUT 8-15": "D09 D10 D11 D12 D13 D14 D15 D16",
    "0-10 V outputs 0-3; pin 1 = common GND": "GND AO0 AO1 AO2 AO3",
    "GND/AI0/AI1/AI2/AI3": "GND AI0 AI1 AI2 AI3",
    "I2C0: SDA, SCL, 3.3 V, 5 V, GND": "SDA SCL 3V3 5V GND",
    "LCD LVDS 2x10, 2.00 mm": "LVDS 2x10",
    "Expansion socket: +3V3, GND, GPIO4-GPIO8": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "Expansion: 3V3, GND, GPIO4-GPIO8": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "SOFNG TF-15x15 microSD socket (C111196)": "microSD TF15",
    "Open-Smart TF Card Breakout": "microSD header",
    "ESP-01/ESP-01S socket": "ESP-01",
    "ESP-01S socket": "ESP-01",
    "AI0/GND/AI1/GND/AI2/GND": "AI0-3 / -",
    "AO 0-3 / 0V": "GND AO0 AO1 AO2 AO3",
    "AI0-3 / 0V": "GND AI0 AI1 AI2 AI3",
    "I2C / 3V3 / 5V / 0V": "SDA SCL 3V3 5V GND",
    "IO4-8 / 3V3 / 0V": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "AO0-3 / -": "GND AO0 AO1 AO2 AO3",
    "AI0-3 / -": "GND AI0 AI1 AI2 AI3",
    "I2C: 3V3 5V -": "SDA SCL 3V3 5V GND",
    "IO4-8: 3V3 -": "3V3 GND IO4 IO5 IO6 IO7 IO8",
    "3V3_PWR": "3V3 LED",
    "5V_PWR": "5V LED",
    "WeAct RP2350B Core Board (socketed)": "WeAct RP2350B",
    "16 PLC inputs": "16 PLC IN",
    "24 PLC outputs": "PLC OUT",
    "Power and supervision": "Power",
    "MCU, shift chains and safety": "MCU / SHIFT",
    "Storage, Wi-Fi and UI": "SD / Wi-Fi",
    "J22 LCD LVDS 2.00 mm": "J22 LVDS",
    "J22 LCD LVDS 2x10": "J22 LVDS",
    "J5 E-STOP": "J5 ESTOP",
}


def _dynamic_name(name: str) -> str:
    axis = re.fullmatch(r"AX([0-6])_(STEP|DIR|ERROR_N|ZERO)", name)
    if axis:
        number = AXIS_REMAP[int(axis.group(1))]
        suffix = {"STEP": "STP", "DIR": "DIR", "ERROR_N": "ERR", "ZERO": "Z"}[
            axis.group(2)
        ]
        return f"{suffix}{number}"

    field_input = re.fullmatch(r"FIELD_IN(\d+)", name)
    if field_input:
        return f"I{int(field_input.group(1)):02d}"
    logic_input = re.fullmatch(r"PLC_IN(\d+)_N", name)
    if logic_input:
        return f"I{int(logic_input.group(1)):02d}_N"
    input_led = re.fullmatch(r"FLD_LED(\d+)_A", name)
    if input_led:
        return f"LI{int(input_led.group(1)):02d}"
    input_opto = re.fullmatch(r"FLD_OPTO(\d+)_A", name)
    if input_opto:
        return f"OI{int(input_opto.group(1)):02d}"

    output_led = re.fullmatch(r"DO_LED(\d+)_A", name)
    if output_led:
        return f"DL{int(output_led.group(1)) + 1:02d}"
    output_opto = re.fullmatch(r"DO_OPTO_LED(\d+)_A", name)
    if output_opto:
        return f"OD{int(output_opto.group(1)) + 1:02d}"
    output_driver = re.fullmatch(r"DO_DRV(\d+)", name)
    if output_driver:
        return f"TD{int(output_driver.group(1)) + 1:02d}"
    output = re.fullmatch(r"DO(\d+)", name)
    if output and 0 <= int(output.group(1)) <= 15:
        return f"D{int(output.group(1)) + 1:02d}"

    encoder = re.fullmatch(r"ENC([0-2])_([ABZ])_(5V|3V3)", name)
    if encoder:
        return f"E{encoder.group(1)}_{encoder.group(2)}{encoder.group(3)}"

    expansion = re.fullmatch(r"EXP_GPIO([4-8])", name)
    if expansion:
        return f"IO{expansion.group(1)}"

    adc = re.fullmatch(r"AI([0-3])_ADC", name)
    if adc:
        return f"ADC{adc.group(1)}"

    analog = re.fullmatch(r"AOUT([0-3])(?:_(PWM|F1|F2|FB))?", name)
    if analog:
        number, suffix = analog.groups()
        return {
            None: f"AO{number}",
            "PWM": f"PWM{number}",
            "F1": f"AO{number}_1",
            "F2": f"AO{number}_2",
            "FB": f"AO{number}_FB",
        }[suffix]
    return name


def shorten_name(name: str) -> str:
    """Return the current short name for a net or connector value."""
    if name in CONNECTOR_LABEL_NAMES:
        return CONNECTOR_LABEL_NAMES[name]
    if name in STATIC_NAMES:
        return STATIC_NAMES[name]
    if name in TEXT_RENAMES:
        return TEXT_RENAMES[name]
    current_axis_value = re.fullmatch(r"A([0-6]): (?:0V|-), ERR, Z", name)
    if current_axis_value:
        number = current_axis_value.group(1)
        return f"GND ERR{number} Z{number}"
    current_encoder_value = re.fullmatch(r"ENC([0-2]) 5V A B Z (?:0V|-)", name)
    if current_encoder_value:
        number = current_encoder_value.group(1)
        return f"+5V A{number} B{number} Z{number} GND"
    current_output_axis = re.fullmatch(
        r"A([0-6]): EN(3|4), ST, DIR",
        name,
    )
    if current_output_axis:
        number = current_output_axis.group(1)
        return f"EN{current_output_axis.group(2)} STP{number} DIR{number}"

    current_pin_axis_output = re.fullmatch(
        r"1=EN(3|4) 2=A([0-6])_ST 3=A\2_DIR",
        name,
    )
    if current_pin_axis_output:
        number = current_pin_axis_output.group(2)
        return f"EN{current_pin_axis_output.group(1)} STP{number} DIR{number}"

    current_pin_axis_status = re.fullmatch(
        r"1=- 2=A([0-6])_ERR 3=A\1_Z",
        name,
    )
    if current_pin_axis_status:
        number = current_pin_axis_status.group(1)
        return f"GND ERR{number} Z{number}"

    compact_axis_net = re.fullmatch(r"A([0-6])_(ST|DIR|ERR|Z)", name)
    if compact_axis_net:
        number, signal = compact_axis_net.groups()
        suffix = {"ST": "STP", "DIR": "DIR", "ERR": "ERR", "Z": "Z"}[signal]
        return f"{suffix}{number}"

    axis_value = re.fullmatch(r"AX([0-6]):\s*(.*)", name)
    if axis_value:
        number = AXIS_REMAP[int(axis_value.group(1))]
        tail = axis_value.group(2)
        for old, new in (
            ("EN_3AX", "EN3"),
            ("EN_4AX", "EN4"),
            ("STEP", "ST"),
            ("shared alarm", "ERR"),
            ("ERROR", "ERR"),
            ("ZERO", "Z"),
            ("GND", "-"),
        ):
            tail = tail.replace(old, new)
        if "ERR" in tail or "ZERO" in tail:
            return f"GND ERR{number} Z{number}"
        enable = "EN3" if number <= 2 else "EN4"
        return f"{enable} STP{number} DIR{number}"

    encoder_value = re.fullmatch(
        r"Encoder ([0-2]): \+5,A,B,Z,GND",
        name,
    )
    if encoder_value:
        number = encoder_value.group(1)
        return f"+5V A{number} B{number} Z{number} GND"
    return _dynamic_name(name)


def _all_old_names() -> set[str]:
    names = set(STATIC_NAMES) | set(TEXT_RENAMES)
    for number in range(1, 17):
        names.update(
            {
                f"FIELD_IN{number}",
                f"PLC_IN{number}_N",
                f"FLD_LED{number}_A",
                f"FLD_OPTO{number}_A",
            }
        )
    for number in range(16):
        names.update(
            {
                f"DO{number}",
                f"DO_LED{number}_A",
                f"DO_OPTO_LED{number}_A",
                f"DO_DRV{number}",
            }
        )
    for axis in range(7):
        names.update(
            {
                f"AX{axis}_STEP",
                f"AX{axis}_DIR",
                f"AX{axis}_ERROR_N",
                f"AX{axis}_ZERO",
                f"A{axis}_STEP",
                f"A{axis}_DIR",
                f"A{axis}_ERROR_N",
                f"A{axis}_ZERO",
                f"A{axis}_ST",
                f"A{axis}_ERR",
                f"A{axis}_Z",
                *(f"P{number}" for number in range(1, 17)),
                f"AX{axis}: EN_3AX, STEP, DIR",
                f"AX{axis}: EN_4AX, STEP, DIR",
                f"AX{axis}: GND, ERROR, ZERO",
                f"AX{axis}: ZERO, shared alarm, GND",
            }
        )
    for encoder in range(3):
        for signal in "ABZ":
            names.add(f"ENC{encoder}_{signal}_5V")
            names.add(f"ENC{encoder}_{signal}_3V3")
        names.add(f"Encoder {encoder}: +5,A,B,Z,GND")
    for number in range(4, 9):
        names.add(f"EXP_GPIO{number}")
    for number in range(4):
        names.add(f"AI{number}_ADC")
        names.add(f"AOUT{number}")
        names.add(f"AOUT{number}_PWM")
        names.add(f"AOUT{number}_F1")
        names.add(f"AOUT{number}_F2")
        names.add(f"AOUT{number}_FB")
    return names


_OLD_TO_NEW = {name: shorten_name(name) for name in _all_old_names()}
_NEW_TO_OLD = {new: old for old, new in _OLD_TO_NEW.items()}
_OLD_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    + "|".join(
        re.escape(name)
        for name in sorted(_OLD_TO_NEW, key=len, reverse=True)
    )
    + r")(?![A-Za-z0-9_])"
)
_QUOTED_RE = re.compile(r'"([^"\r\n]*)"')
_SIM_PINS_RE = re.compile(r'(\(property "Sim\.Pins" ")([^"]*)(")')
_PIN_MAPPING_RE = re.compile(r"(?<!\S)[1-9]\d*=")


def shorten_text(text: str) -> str:
    """Shorten known net names embedded in a quoted KiCad field."""
    direct = shorten_name(text)
    if direct != text:
        return direct
    text = _PIN_MAPPING_RE.sub("", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return shorten_embedded_text(text)


def shorten_embedded_text(text: str) -> str:
    """Shorten known net names inside prose or a longer value."""
    text = _OLD_TOKEN_RE.sub(lambda match: _OLD_TO_NEW[match.group(0)], text)
    return _PIN_MAPPING_RE.sub("", text)


def shorten_quoted_tokens(text: str) -> str:
    """Rewrite quoted strings in a KiCad S-expression without touching layout."""
    protected: list[str] = []

    def protect_sim_pins(match: re.Match[str]) -> str:
        protected.append(match.group(2))
        return f"{match.group(1)}__SIM_PINS_{len(protected) - 1}__{match.group(3)}"

    text = _SIM_PINS_RE.sub(protect_sim_pins, text)
    text = _QUOTED_RE.sub(lambda match: f'"{shorten_text(match.group(1))}"', text)
    for index, value in enumerate(protected):
        text = text.replace(f"__SIM_PINS_{index}__", value)
    return text


def canonical_name(name: str) -> str:
    """Map a short name back to the established verification vocabulary."""
    logic_input = re.fullmatch(r"I(\d{2})_N", name)
    if logic_input:
        return f"PLC_IN{int(logic_input.group(1))}_N"
    field_input = re.fullmatch(r"I(\d{2})", name)
    if field_input:
        return f"FIELD_IN{int(field_input.group(1))}"
    input_led = re.fullmatch(r"LI(\d{2})", name)
    if input_led:
        return f"FLD_LED{int(input_led.group(1))}_A"
    input_opto = re.fullmatch(r"OI(\d{2})", name)
    if input_opto:
        return f"FLD_OPTO{int(input_opto.group(1))}_A"
    output = re.fullmatch(r"D(\d{2})", name)
    if output:
        return f"DO{int(output.group(1)) - 1}"
    output_led = re.fullmatch(r"DL(\d{2})", name)
    if output_led:
        return f"DO_LED{int(output_led.group(1)) - 1}_A"
    output_opto = re.fullmatch(r"OD(\d{2})", name)
    if output_opto:
        return f"DO_OPTO_LED{int(output_opto.group(1)) - 1}_A"
    output_driver = re.fullmatch(r"TD(\d{2})", name)
    if output_driver:
        return f"DO_DRV{int(output_driver.group(1)) - 1}"
    axis_net = re.fullmatch(r"(STP|DIR|ERR|Z)([0-6])", name)
    if axis_net:
        prefix, physical_axis = axis_net.groups()
        logical_axis = next(
            old for old, new in AXIS_REMAP.items() if new == int(physical_axis)
        )
        suffix = {
            "STP": "STEP",
            "DIR": "DIR",
            "ERR": "ERROR_N",
            "Z": "ZERO",
        }[prefix]
        return f"AX{logical_axis}_{suffix}"
    return _NEW_TO_OLD.get(name, name)
