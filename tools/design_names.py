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

TEXT_RENAMES = {
    "24 V DC input": "1=24+ 2=-",
    "Backlight: +12V_BL, ISO_GND": "1=BL12+ 2=PLC-",
    "Dedicated E-stop loop": "1=ESTOP 2=PLC-",
    "External isolated field 24 V supply / relay common A": "1=PLC24+ 2=PLC-",
    "External isolated field 24 V supply / relay common B": "1=PLC24+ 2=PLC-",
    "External isolated field 24 V supply / relay common": "1=PLC24+ 2=PLC-",
    "PLC 24V / 0V A": "1=PLC24+ 2=PLC-",
    "PLC 24V / 0V B": "1=PLC24+ 2=PLC-",
    "PLC 24V / 0V": "1=PLC24+ 2=PLC-",
    "24V IN": "1=24+ 2=-",
    "24V + / -": "1=24+ 2=-",
    "BL 12V / 0V": "1=BL12+ 2=PLC-",
    "BL 12+ / PLC -": "1=BL12+ 2=PLC-",
    "ESTOP / 0V": "1=ESTOP 2=PLC-",
    "ESTOP / PLC -": "1=ESTOP 2=PLC-",
    "PLC 24+ / PLC -": "1=PLC24+ 2=PLC-",
    "PLC positions 1-8 signals": "1=I01 2=I02 3=I03 4=I04 5=I05 6=I06 7=I07 8=I08",
    "PLC positions 9-16 signals": "1=I09 2=I10 3=I11 4=I12 5=I13 6=I14 7=I15 8=I16",
    "PLC IN 1-8": "1=I01 2=I02 3=I03 4=I04 5=I05 6=I06 7=I07 8=I08",
    "PLC IN 9-16": "1=I09 2=I10 3=I11 4=I12 5=I13 6=I14 7=I15 8=I16",
    "General outputs 0-7": "1=D01 2=D02 3=D03 4=D04 5=D05 6=D06 7=D07 8=D08",
    "General outputs 8-15": "1=D09 2=D10 3=D11 4=D12 5=D13 6=D14 7=D15 8=D16",
    "OUT 0-7": "1=D01 2=D02 3=D03 4=D04 5=D05 6=D06 7=D07 8=D08",
    "OUT 8-15": "1=D09 2=D10 3=D11 4=D12 5=D13 6=D14 7=D15 8=D16",
    "0-10 V outputs 0-3; pin 1 = common GND": "1=- 2=AO0 3=AO1 4=AO2 5=AO3",
    "GND/AI0/AI1/AI2/AI3": "1=- 2=AI0 3=AI1 4=AI2 5=AI3",
    "I2C0: SDA, SCL, 3.3 V, 5 V, GND": "1=SDA 2=SCL 3=3V3 4=5V 5=-",
    "LCD LVDS 2x10, 2.00 mm": "LVDS 2x10",
    "Expansion socket: +3V3, GND, GPIO4-GPIO8": "1=3V3 2=- 3=IO4 4=IO5 5=IO6 6=IO7 7=IO8",
    "Expansion: 3V3, GND, GPIO4-GPIO8": "1=3V3 2=- 3=IO4 4=IO5 5=IO6 6=IO7 7=IO8",
    "SOFNG TF-15x15 microSD socket (C111196)": "microSD TF15",
    "Open-Smart TF Card Breakout": "microSD header",
    "ESP-01/ESP-01S socket": "ESP-01",
    "ESP-01S socket": "ESP-01",
    "AI0/GND/AI1/GND/AI2/GND": "AI0-3 / -",
    "AO 0-3 / 0V": "1=- 2=AO0 3=AO1 4=AO2 5=AO3",
    "AI0-3 / 0V": "1=- 2=AI0 3=AI1 4=AI2 5=AI3",
    "I2C / 3V3 / 5V / 0V": "1=SDA 2=SCL 3=3V3 4=5V 5=-",
    "IO4-8 / 3V3 / 0V": "1=3V3 2=- 3=IO4 4=IO5 5=IO6 6=IO7 7=IO8",
    "AO0-3 / -": "1=- 2=AO0 3=AO1 4=AO2 5=AO3",
    "AI0-3 / -": "1=- 2=AI0 3=AI1 4=AI2 5=AI3",
    "I2C: 3V3 5V -": "1=SDA 2=SCL 3=3V3 4=5V 5=-",
    "IO4-8: 3V3 -": "1=3V3 2=- 3=IO4 4=IO5 5=IO6 6=IO7 7=IO8",
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
    if name in STATIC_NAMES:
        return STATIC_NAMES[name]
    if name in TEXT_RENAMES:
        return TEXT_RENAMES[name]
    current_axis_value = re.fullmatch(r"A([0-6]): (?:0V|-), ERR, Z", name)
    if current_axis_value:
        number = current_axis_value.group(1)
        return f"- ERR{number} Z{number}"
    current_encoder_value = re.fullmatch(r"ENC([0-2]) 5V A B Z (?:0V|-)", name)
    if current_encoder_value:
        return "1=5V 2=A 3=B 4=Z 5=-"
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
        return f"- ERR{number} Z{number}"

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
            return f"- ERR{number} Z{number}"
        enable = "EN3" if number <= 2 else "EN4"
        return f"{enable} STP{number} DIR{number}"

    encoder_value = re.fullmatch(
        r"Encoder ([0-2]): \+5,A,B,Z,GND",
        name,
    )
    if encoder_value:
        return "1=5V 2=A 3=B 4=Z 5=-"
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


def shorten_text(text: str) -> str:
    """Shorten known net names embedded in a quoted KiCad field."""
    direct = shorten_name(text)
    if direct != text:
        return direct
    return shorten_embedded_text(text)


def shorten_embedded_text(text: str) -> str:
    """Shorten known net names inside prose or a longer value."""
    return _OLD_TOKEN_RE.sub(lambda match: _OLD_TO_NEW[match.group(0)], text)


def shorten_quoted_tokens(text: str) -> str:
    """Rewrite quoted strings in a KiCad S-expression without touching layout."""
    return _QUOTED_RE.sub(lambda match: f'"{shorten_text(match.group(1))}"', text)


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
