"""Generate the project-local verified symbols and WeAct socket footprint."""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
HARDWARE = PROJECT / "hardware"
LIBRARIES = HARDWARE / "libraries"
SOURCE_ROOT = PROJECT.parent / "tmp" / "leancam-sources"
WEACT_SOURCE = SOURCE_ROOT / "WeActStudio.RP2350B.footprint" / "WeAct2550B.kicad_mod"
WEACT_STEP = SOURCE_ROOT / "WeActStudio.RP2350BCoreBoard" / "HDK" / "3D_RP350B.step"


def fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def symbol_property(name: str, value: str, x: float, y: float) -> str:
    return f"""\t\t(property "{name}" "{value}"
\t\t\t(at {fmt(x)} {fmt(y)} 0)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
"""


def make_symbol(
    name: str,
    pins: list[tuple[str, str]],
    *,
    width: float = 15.24,
    description: str = "",
    footprint_filter: str = "*",
    pin_type: str = "passive",
) -> str:
    rows = (len(pins) + 1) // 2
    top = (rows - 1) * 1.27
    bottom = -top
    lines = [
        f'\t(symbol "{name}"',
        "\t\t(pin_numbers\n\t\t\t(hide yes)\n\t\t)",
        "\t\t(pin_names\n\t\t\t(offset 1.016)\n\t\t)",
        "\t\t(exclude_from_sim no)",
        "\t\t(in_bom yes)",
        "\t\t(on_board yes)",
        symbol_property("Reference", "U", -width - 2.54, top + 3.81),
        symbol_property("Value", name, -width - 2.54, top + 1.27),
        symbol_property("Footprint", "", 0, 0),
        symbol_property("Datasheet", "~", 0, -2.54),
        symbol_property("Description", description, 0, -5.08),
    ]
    lines.extend(
        [
            f'\t\t(symbol "{name}_0_1"',
            "\t\t\t(rectangle",
            f"\t\t\t\t(start {fmt(-width)} {fmt(top + 2.54)})",
            f"\t\t\t\t(end {fmt(width)} {fmt(bottom - 2.54)})",
            "\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)",
            "\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)",
            "\t\t\t)",
            "\t\t)",
            f'\t\t(symbol "{name}_1_1"',
        ]
    )
    for index, (number, pin_name) in enumerate(pins):
        if index < rows:
            x = -width
            y = top - index * 2.54
            angle = 0
        else:
            x = width
            y = bottom + (index - rows) * 2.54
            angle = 180
        safe_name = pin_name.replace('"', '\\"')
        effective_pin_type = pin_type
        if pin_type == "bidirectional" and pin_name in {
            "GND", "3V3", "3V3_DEBUG", "5V", "VBUS", "REF"
        }:
            effective_pin_type = "passive"
        lines.extend(
            [
                f"\t\t\t(pin {effective_pin_type} line",
                f"\t\t\t\t(at {fmt(x)} {fmt(y)} {angle})",
                "\t\t\t\t(length 2.54)",
                f'\t\t\t\t(name "{safe_name}"',
                "\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.016 1.016)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)",
                f'\t\t\t\t(number "{number}"',
                "\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.016 1.016)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)",
                "\t\t\t)",
            ]
        )
    lines.extend(
        [
            "\t\t)",
            f'\t\t(property "ki_fp_filters" "{footprint_filter}"',
            "\t\t\t(at 0 0 0)",
            "\t\t\t(show_name no)",
            "\t\t\t(do_not_autoplace no)",
            "\t\t\t(hide yes)",
            "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)",
            "\t\t)",
            "\t\t(embedded_fonts no)",
            "\t)",
        ]
    )
    return "\n".join(lines)


WEACT_MAP = {
    "1": "GND",
    "2": "GND",
    "3": "3V3",
    "4": "RUN",
    "5": "GP46",
    "6": "GP44",
    "7": "GP42",
    "8": "GP40",
    "9": "GP38",
    "10": "GP36",
    "11": "GP34",
    "12": "GP32",
    "13": "GP30",
    "14": "GP28",
    "15": "GP26",
    "16": "GND",
    "17": "EN",
    "18": "3V3",
    "19": "GP47",
    "20": "GP45",
    "21": "GP43",
    "22": "GP41",
    "23": "GP39",
    "24": "GP37",
    "25": "GP35",
    "26": "GP33",
    "27": "GP31",
    "28": "GP29",
    "29": "GP27",
    "30": "GP25",
    "31": "5V",
    "32": "GND",
    "33": "GP0",
    "34": "GP2",
    "35": "GP4",
    "36": "GP6",
    "37": "GP8",
    "38": "GP10",
    "39": "GP12",
    "40": "GP14",
    "41": "GP16",
    "42": "GP18",
    "43": "GP20",
    "44": "GP22",
    "45": "GP24",
    "46": "VBUS",
    "47": "GND",
    "48": "REF",
    "49": "GP1",
    "50": "GP3",
    "51": "GP5",
    "52": "GP7",
    "53": "GP9",
    "54": "GP11",
    "55": "GP13",
    "56": "GP15",
    "57": "GP17",
    "58": "GP19",
    "59": "GP21",
    "60": "GP23",
    "61": "GND",
    "62": "SWCLK",
    "63": "SWDIO",
    "64": "3V3_DEBUG",
}

QUAD_OPTO_PINS = [
    ("1", "CH1_ANODE"),
    ("2", "CH1_CATHODE"),
    ("3", "CH2_ANODE"),
    ("4", "CH2_CATHODE"),
    ("5", "CH3_ANODE"),
    ("6", "CH3_CATHODE"),
    ("7", "CH4_ANODE"),
    ("8", "CH4_CATHODE"),
    ("9", "CH4_EMITTER"),
    ("10", "CH4_COLLECTOR"),
    ("11", "CH3_EMITTER"),
    ("12", "CH3_COLLECTOR"),
    ("13", "CH2_EMITTER"),
    ("14", "CH2_COLLECTOR"),
    ("15", "CH1_EMITTER"),
    ("16", "CH1_COLLECTOR"),
]

QUAD_OPAMP_PINS = [
    ("1", "1OUT"),
    ("2", "1IN_N"),
    ("3", "1IN_P"),
    ("4", "VPLUS"),
    ("5", "2IN_P"),
    ("6", "2IN_N"),
    ("7", "2OUT"),
    ("8", "3OUT"),
    ("9", "3IN_N"),
    ("10", "3IN_P"),
    ("11", "VMINUS"),
    ("12", "4IN_P"),
    ("13", "4IN_N"),
    ("14", "4OUT"),
]

OCTAL_BUFFER_PINS = [
    ("1", "OE1_N"),
    ("2", "A0"),
    ("3", "Y0"),
    ("4", "A1"),
    ("5", "Y1"),
    ("6", "A2"),
    ("7", "Y2"),
    ("8", "A3"),
    ("9", "Y3"),
    ("10", "GND"),
    ("11", "A4"),
    ("12", "Y4"),
    ("13", "A5"),
    ("14", "Y5"),
    ("15", "A6"),
    ("16", "Y6"),
    ("17", "A7"),
    ("18", "Y7"),
    ("19", "OE2_N"),
    ("20", "VCC"),
]

HEX_SCHMITT_PINS = [
    ("1", "1A"),
    ("2", "1Y"),
    ("3", "2A"),
    ("4", "2Y"),
    ("5", "3A"),
    ("6", "3Y"),
    ("7", "GND"),
    ("8", "4Y"),
    ("9", "4A"),
    ("10", "5Y"),
    ("11", "5A"),
    ("12", "6Y"),
    ("13", "6A"),
    ("14", "VCC"),
]

RESISTOR_PACK04_PINS = [
    ("1", "R1A"),
    ("2", "R2A"),
    ("3", "R3A"),
    ("4", "R4A"),
    ("5", "R4B"),
    ("6", "R3B"),
    ("7", "R2B"),
    ("8", "R1B"),
]


def write_symbol_library() -> Path:
    output = LIBRARIES / "LeanCam.kicad_sym"
    symbols = [
        make_symbol(
            "WeAct_RP2350B",
            [(number, WEACT_MAP[number]) for number in WEACT_MAP],
            width=22.86,
            description=(
                "WeAct Studio RP2350B Core Board on 2x15 perimeter socket rows plus "
                "four internal programming pads"
            ),
            footprint_filter="WeAct_RP2350B_Socket",
            pin_type="bidirectional",
        ),
        make_symbol(
            "QuadOpto",
            QUAD_OPTO_PINS,
            description="Four-channel optocoupler, LTV-847S pinout",
            footprint_filter="SOIC-16W*",
        ),
        make_symbol(
            "EL3H7",
            [
                ("1", "ANODE"),
                ("2", "CATHODE"),
                ("3", "EMITTER"),
                ("4", "COLLECTOR"),
            ],
            width=5.08,
            description="Everlight EL3H7 single-channel phototransistor optocoupler, DIP-4",
            footprint_filter="DIP-4*W7.62mm*",
        ),
        make_symbol(
            "OctalBuffer3V3",
            OCTAL_BUFFER_PINS,
            description="Octal non-inverting 3-state buffer, 74LVC244A pinout",
            footprint_filter="SOIC-20W*",
        ),
        make_symbol(
            "OctalBuffer5V",
            OCTAL_BUFFER_PINS,
            description="Octal non-inverting 3-state buffer, SN74AHCT541DW pinout",
            footprint_filter="SOIC-20W*",
        ),
        make_symbol(
            "OctalBufferAHCT",
            OCTAL_BUFFER_PINS,
            description=(
                "Octal non-inverting 3-state 5 V-tolerant AHCT buffer, "
                "SN74AHCT541DW pinout"
            ),
            footprint_filter="SOIC-20W*",
        ),
        make_symbol(
            "HexSchmittInverter3V3",
            HEX_SCHMITT_PINS,
            description="Hex inverting Schmitt trigger, 74LVC14A pinout",
            footprint_filter="SOIC-14*",
        ),
        make_symbol(
            "ResistorPack04",
            RESISTOR_PACK04_PINS,
            description="Four isolated resistors in one SMD array",
            footprint_filter="R_Array_*4x*",
            pin_type="passive",
        ),
        make_symbol(
            "TLV2374",
            QUAD_OPAMP_PINS,
            width=15.24,
            description=(
                "TLV2374 quad rail-to-rail input/output operational amplifier, "
                "2.7 V to 16 V supply, SOIC-14 pinout"
            ),
            footprint_filter="SOIC-14*",
        ),
        make_symbol(
            "L78L12",
            [
                ("1", "OUT"),
                ("2", "GND"),
                ("3", "IN"),
            ],
            width=5.08,
            description=(
                "100 mA fixed 12 V positive linear regulator, SOT-89 pinout"
            ),
            footprint_filter="SOT-89*",
        ),
    ]
    content = (
        "(kicad_symbol_lib\n"
        "\t(version 20251024)\n"
        '\t(generator "kicad_symbol_editor")\n'
        '\t(generator_version "10.0")\n'
        + "\n".join(symbols)
        + "\n)\n"
    )
    output.write_text(content, encoding="utf-8")
    return output


def coordinate_rows(text: str) -> dict[tuple[str, str], list[str]]:
    pattern = re.compile(
        r'\(pad "(?P<label>[^"]+)" thru_hole[^\n]*\n\s*'
        r"\(at (?P<x>-?[0-9.]+) (?P<y>-?[0-9.]+)"
    )
    result: dict[tuple[str, str], list[str]] = {}
    for match in pattern.finditer(text):
        key = (match.group("x"), match.group("y"))
        result.setdefault(key, []).append(match.group("label"))
    return result


def write_weact_footprint() -> Path:
    text = WEACT_SOURCE.read_text(encoding="utf-8")
    rows = coordinate_rows(text)
    ordered: list[tuple[float, float, str]] = []

    for y in (-19.47, -16.93, 16.09, 18.63):
        entries = []
        for (x_text, y_text), labels in rows.items():
            if float(y_text) == y:
                for label in labels:
                    entries.append((float(x_text), y, label))
        ordered.extend(sorted(entries))

    for y in (3.89, 6.43, 8.97, 11.51):
        entries = []
        for (x_text, y_text), labels in rows.items():
            if float(y_text) == y:
                for label in labels:
                    entries.append((float(x_text), y, label))
        ordered.extend(sorted(entries))

    if len(ordered) != 64:
        raise RuntimeError(f"Expected 64 official WeAct pads, found {len(ordered)}")

    label_to_number = {label: str(index) for index, (_, _, label) in enumerate(ordered, 1)}
    expected = set()
    for index in range(1, 65):
        value = WEACT_MAP[str(index)]
        if value == "GND":
            expected.add("GND" if index == 61 else "G")
        elif value == "SWCLK":
            expected.add("CLK")
        elif value == "SWDIO":
            expected.add("DIO")
        elif value == "3V3_DEBUG":
            expected.add("3V3")
        elif value.startswith("GP"):
            expected.add(value[2:])
        else:
            expected.add(value)
    actual = set(label_to_number)
    if actual != expected:
        raise RuntimeError(f"Official footprint label mismatch: {actual ^ expected}")

    pad_pattern = re.compile(
        r'(?P<head>\(pad ")(?P<label>[^"]+)(?P<tail>" thru_hole)'
    )
    number_by_label: dict[str, list[str]] = {}
    for (_, _, label), number in zip(ordered, map(str, range(1, 65)), strict=True):
        number_by_label.setdefault(label, []).append(number)

    used: dict[str, int] = {}

    def replace_pad(match: re.Match[str]) -> str:
        label = match.group("label")
        position = used.get(label, 0)
        number = number_by_label[label][position]
        used[label] = position + 1
        return f'{match.group("head")}{number}{match.group("tail")}'

    text = pad_pattern.sub(replace_pad, text)
    text = text.replace('(footprint "WeAct2550B"', '(footprint "WeAct_RP2350B_Socket"', 1)
    text = re.sub(
        r'\(descr "[^"]*"\)',
        '(descr "WeAct Studio RP2350B Core Board, 41.402 x 41.148 mm body, 2.54 mm perimeter socket")',
        text,
        count=1,
    )
    text = re.sub(
        r'\(tags "[^"]*"\)',
        '(tags "WeAct RP2350B RP2350 socket 2.54mm")',
        text,
        count=1,
    )
    text = re.sub(
        r'\(model "[^"]*"',
        '(model "${KIPRJMOD}/libraries/3d/WeAct_RP2350B.step"',
        text,
        count=1,
    )
    output = LIBRARIES / "LeanCam.pretty" / "WeAct_RP2350B_Socket.kicad_mod"
    output.write_text(text, encoding="utf-8")
    return output


def write_tables() -> None:
    (HARDWARE / "sym-lib-table").write_text(
        '(sym_lib_table\n'
        '\t(version 7)\n'
        '\t(lib (name "LeanCam")(type "KiCad")'
        '(uri "${KIPRJMOD}/libraries/LeanCam.kicad_sym")'
        '(options "")(descr "LeanCam project symbols"))\n'
        ')\n',
        encoding="utf-8",
    )
    (HARDWARE / "fp-lib-table").write_text(
        '(fp_lib_table\n'
        '\t(version 7)\n'
        '\t(lib (name "LeanCam")(type "KiCad")'
        '(uri "${KIPRJMOD}/libraries/LeanCam.pretty")'
        '(options "")(descr "LeanCam project footprints"))\n'
        ')\n',
        encoding="utf-8",
    )


def main() -> None:
    LIBRARIES.mkdir(parents=True, exist_ok=True)
    (LIBRARIES / "LeanCam.pretty").mkdir(parents=True, exist_ok=True)
    (LIBRARIES / "3d").mkdir(parents=True, exist_ok=True)
    write_tables()
    sym = write_symbol_library()
    fp = write_weact_footprint()
    shutil.copy2(WEACT_STEP, LIBRARIES / "3d" / "WeAct_RP2350B.step")
    shutil.copy2(
        SOURCE_ROOT / "WeActStudio.RP2350BCoreBoard" / "HDK" / "RP2350B_PINOUT.png",
        LIBRARIES / "WeAct_RP2350B_PINOUT.png",
    )
    shutil.copy2(
        SOURCE_ROOT / "WeActStudio.RP2350BCoreBoard" / "HDK" / "尺寸图.pdf",
        LIBRARIES / "WeAct_RP2350B_dimensions.pdf",
    )
    generated_uuid = uuid.uuid4()
    (LIBRARIES / "SOURCES.md").write_text(
        "# Vendor sources\n\n"
        "- WeAct Studio RP2350B Core Board official hardware repository: "
        "https://github.com/WeActStudio/WeActStudio.RP2350BCoreBoard\n"
        "- Official body drawing: `WeAct_RP2350B_dimensions.pdf` "
        "(41.402 mm x 41.148 mm).\n"
        "- Official pinout image: `WeAct_RP2350B_PINOUT.png`.\n"
        "- Official 3D STEP: `3d/WeAct_RP2350B.step`.\n"
        "- Socket land pattern: generated from the published "
        "`WeActStudio.RP2350B.footprint` coordinate data, with the manufacturer "
        "pad labels mapped deterministically to module pins 1-64 so the schematic "
        "and PCB agree.\n"
        f"- Local footprint generation identifier: `{generated_uuid}`.\n",
        encoding="utf-8",
    )
    print(f"symbols: {sym}")
    print(f"footprint: {fp}")


if __name__ == "__main__":
    main()
