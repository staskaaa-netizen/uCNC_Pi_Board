"""Generate the LeanCam NCC RP2350B hierarchical schematic from verified parts."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import kicad_sch_api.library.cache as cache_module
from kicad_sch_api import Schematic
from kicad_sch_api.core.types import Point


PROJECT = Path(__file__).resolve().parents[1]
HARDWARE = PROJECT / "hardware"
CACHE_DIR = PROJECT / ".kicad-cache"
KICAD_SYMBOLS = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\share\kicad\symbols"
)
CUSTOM_SYMBOLS = HARDWARE / "libraries" / "LeanCam.kicad_sym"

FP = {
    "R1206": "Resistor_SMD:R_1206_3216Metric",
    "R0805": "Resistor_SMD:R_0805_2012Metric",
    "R_Array_4x0603": "Resistor_SMD:R_Array_Convex_4x0603",
    "R_Array_4x1206": "Resistor_SMD:R_Array_Convex_4x1206",
    "C0805": "Capacitor_SMD:C_0805_2012Metric",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "C1210": "Capacitor_SMD:C_1210_3225Metric",
    "C1206_100V": "Capacitor_SMD:C_1206_3216Metric",
    "LED1206": "LED_SMD:LED_1206_3216Metric",
    "D_SOD323": "Diode_SMD:D_SOD-323",
    "D_SMA": "Diode_SMD:D_SMA",
    "D_SMB": "Diode_SMD:D_SMB",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SOT23_5": "Package_TO_SOT_SMD:SOT-23-5",
    "SOT23_6": "Package_TO_SOT_SMD:SOT-23-6",
    "SOT223": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    "SOT89": "Package_TO_SOT_SMD:SOT-89-3_Handsoldering",
    "SOT363": "Package_TO_SOT_SMD:SOT-363_SC-70-6",
    "TSOT23_6": "Package_TO_SOT_SMD:TSOT-23-6",
    "SOIC8": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
    "SOIC8_POWERPAD": "Package_SO:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.41x3.3mm",
    "SOIC14": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
    "SOIC16": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
    "SOIC16W": "Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm",
    "SOIC20W": "Package_SO:SOIC-20W_7.5x12.8mm_P1.27mm",
    "DIP4": "Package_DIP:DIP-4_W7.62mm",
    "TO263_5": "Package_TO_SOT_SMD:TO-263-5_TabPin3",
    "USON10": "Package_SON:USON-10_2.5x1.0mm_P0.5mm",
    "SD": "Connector_Card:SD_TE_2041021",
    "MICROSD": "Connector_Card:microSD_HC_Molex_104031-0811",
    "PH2": "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "SWITCH": "Button_Switch_THT:SW_PUSH_6mm",
    "WEACT": "LeanCam:WeAct_RP2350B_Socket",
    "NETTIE": "NetTie:NetTie-2_SMD_Pad2.0mm",
    "L_SRR1260": "Inductor_SMD:L_Bourns_SRR1260",
    "L_SRN6045": "Inductor_SMD:L_Bourns_SRN6045TA",
    "DCDC_TMA0505": "Converter_DCDC:Converter_DCDC_TRACO_TMA-05xxS_12xxS_Single_THT",
    "DCDC_TBA2": "Converter_DCDC:Converter_DCDC_TRACO_TBA2-xxxx_Single_THT",
    "SJ2": "LeanCam:SolderJumper_2_Open_1206Gap",
    "SJ3": "Jumper:SolderJumper-3_P1.3mm_Open_Pad1.0x1.5mm",
}

for count in range(2, 17):
    FP[f"TERM{count}"] = (
        "Connector_Phoenix_MC:"
        f"PhoenixContact_MCV_1,5_{count}-G-3.5_1x{count:02d}_P3.50mm_Vertical"
    )

for count in (2, 3, 4, 5, 6, 8, 10):
    FP[f"HDR1X{count}"] = (
        f"Connector_PinHeader_2.54mm:PinHeader_1x{count:02d}_P2.54mm_Vertical"
    )
FP["HDR2X4"] = "Connector_PinSocket_2.54mm:PinSocket_2x04_P2.54mm_Vertical"
FP["HDR2X5"] = "Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical"
FP["HDR2X8"] = "Connector_PinHeader_2.54mm:PinHeader_2x08_P2.54mm_Vertical"
FP["HDR2X10_2MM"] = "Connector_PinHeader_2.00mm:PinHeader_2x10_P2.00mm_Vertical"

MPN = {
    "R1206": ("Yageo", "RC1206 series 1%"),
    "R0805": ("Yageo", "RC0805 series 1%"),
    "R_Array_4x0603": ("Yageo", "YC164-FR-07 series 1%"),
    "R_Array_4x1206": ("Yageo", "YC324-FR-07 series 1%"),
    "C0805": ("Samsung Electro-Mechanics", "CL21 series 0805 X7R"),
    "C1206": ("Samsung Electro-Mechanics", "CL31 series 1206 X7R"),
    "C1210": ("Samsung Electro-Mechanics", "CL32 series 1210 X7R"),
    "C1206_100V": ("Murata", "GRM31 series 1206 C0G/X7R"),
    "LED1206": ("Lite-On", "LTST-C150 series"),
    "D_SOD323": ("Diodes Incorporated", "1N4148WS"),
    "D_SMA": ("Diodes Incorporated", "SS54"),
    "D_SMB": ("Bourns", "SMBJ24CA"),
    "SOT23": ("Texas Instruments", "generic SOT-23"),
    "SOT23_5": ("Texas Instruments", "generic SOT-23-5"),
    "SOT23_6": ("Texas Instruments", "generic SOT-23-6"),
    "SOT223": ("Advanced Monolithic Systems", "AMS1117-3.3"),
    "SOT89": ("Texas Instruments", "L78L12ACUTR"),
    "SOT363": ("Texas Instruments", "LM66100DCKR"),
    "TSOT23_6": ("Diodes Incorporated", "AP63203WU-7"),
    "SOIC8": ("Texas Instruments", "generic SOIC-8"),
    "SOIC8_POWERPAD": ("Texas Instruments", "LMR36510ADDAR"),
    "SOIC14": ("Texas Instruments", "generic SOIC-14"),
    "SOIC16": ("Texas Instruments", "generic SOIC-16"),
    "SOIC16W": ("Lite-On", "LTV-847S"),
    "SOIC20W": ("Texas Instruments", "SN74AHCT541DW"),
    "DIP4": ("Everlight", "EL3H7"),
    "TO263_5": ("Texas Instruments", "LM2596S-5.0/NOPB"),
    "USON10": ("Texas Instruments", "TPD4E05U06DQA"),
    "SD": ("TE Connectivity", "2041021-4"),
    "MICROSD": ("Molex", "104031-0811"),
    "PH2": ("Nichicon", "UWT1H101MNL1GS"),
    "SWITCH": ("C&K", "PTS645"),
    "HDR2X4": ("Wurth Elektronik", "61300821121"),
    "SJ2": ("PCB fabrication", "2-pad solder jumper"),
    "L_SRR1260": ("Bourns", "SRR1260 series"),
    "L_SRN6045": ("Bourns", "SRN6045TA series"),
    "SJ3": ("PCB fabrication", "3-pad solder jumper"),
}

cache_module._global_cache = cache_module.SymbolLibraryCache(CACHE_DIR)
cache_module._global_cache.discover_libraries([KICAD_SYMBOLS])
cache_module._global_cache.add_library_path(CUSTOM_SYMBOLS)


@dataclass
class Part:
    reference: str
    value: str
    footprint: str
    lib_id: str
    dnp: bool
    mpn: str


PARTS: list[Part] = []
REF_COUNTERS: defaultdict[str, int] = defaultdict(int)


class SheetBuilder:
    def __init__(self, name: str, filename: str, paper: str = "A2") -> None:
        self.name = name
        self.filename = filename
        self.sch = Schematic.create(name, paper=paper)
        self.counters = REF_COUNTERS
        self.dnp_uuids: set[str] = set()
        self.pin_owners: dict[tuple[float, float], dict[tuple[str, str], str | None]] = defaultdict(dict)

    def next_ref(self, prefix: str) -> str:
        self.counters[prefix] += 1
        return f"{prefix}{self.counters[prefix]}"

    def note(self, text: str, x: float, y: float, width: float = 80, height: float = 20) -> None:
        self.sch.add_text_box(
            text=text,
            position=(x, y),
            size=(width, height),
            font_size=1.27,
            stroke_width=0.127,
            fill_type="none",
        )

    def _symbol_pins(self, lib_id: str):
        symbol = cache_module._global_cache.get_symbol(lib_id)
        if symbol is None:
            raise RuntimeError(f"Symbol not found: {lib_id}")
        return symbol.pins

    def _pin_world(self, component, pin_number: str):
        pin = next((item for item in self._symbol_pins(component.lib_id) if item.number == pin_number), None)
        if pin is None:
            raise RuntimeError(f"Pin {pin_number} not found on {component.reference}")
        return (
            component.position.x + pin.position.x,
            component.position.y - pin.position.y,
            pin.rotation,
        )

    def _stub_end(self, x: float, y: float, rotation: float) -> tuple[float, float]:
        if rotation == 0:
            return x - 2.54, y
        if rotation == 180:
            return x + 2.54, y
        if rotation == 90:
            return x, y + 2.54
        return x, y - 2.54

    def connect_pin(self, component, pin_number: str, net: str | None) -> None:
        x, y, rotation = self._pin_world(component, pin_number)
        key = (round(x, 4), round(y, 4))
        owner = (component.reference, pin_number)
        other_owners = {
            item: value for item, value in self.pin_owners[key].items() if item != owner
        }
        if other_owners and any(value != net for value in other_owners.values()):
            raise RuntimeError(
                f"Pin coordinate collision at {key} in {self.name}: "
                f"{owner}:{net!r} with {other_owners}"
            )
        self.pin_owners[key][owner] = net
        if net is None:
            self.sch.no_connects.add((x, y))
            return
        self.sch.labels.add(net, (x, y))

    def add(
        self,
        *,
        lib_id: str,
        value: str,
        footprint_key: str | None,
        nets: dict[str, str | None],
        position: tuple[float, float] = (50.8, 50.8),
        prefix: str = "U",
        mpn: str | None = None,
        manufacturer: str | None = None,
        dnp: bool = False,
        reference: str | None = None,
        rotation: float = 0,
    ):
        footprint = FP[footprint_key] if footprint_key else None
        if reference is None:
            reference = self.next_ref(prefix)
        else:
            match = re.fullmatch(r"([A-Za-z]+)([0-9]+)", reference)
            if match:
                self.counters[match.group(1)] = max(
                    self.counters[match.group(1)], int(match.group(2))
                )
        component = self.sch.components.add(
            lib_id,
            reference=reference,
            value=value,
            footprint=footprint,
            position=position,
            rotation=rotation,
        )
        component.set_property("MPN", mpn or value)
        component.set_property("Manufacturer", manufacturer or "generic")
        if dnp:
            component.set_property("Assembly", "DNP")
            self.dnp_uuids.add(component.uuid)
        defined = {pin.number: pin.name for pin in self._symbol_pins(lib_id)}
        normalized = {}
        for selector, net in nets.items():
            matches = [number for number, pin_name in defined.items() if selector in (number, pin_name)]
            if not matches:
                raise RuntimeError(f"No pin selector {selector!r} on {reference} ({lib_id})")
            for pin_number in matches:
                normalized[pin_number] = net
        missing = sorted(set(defined) - set(normalized))
        if missing:
            raise RuntimeError(
                f"{reference} ({lib_id}) has unmapped pins: "
                + ", ".join(f"{number}:{defined[number]}" for number in missing)
            )
        for pin_number, net in normalized.items():
            self.connect_pin(component, pin_number, net)
        PARTS.append(
            Part(
                reference=reference,
                value=value,
                footprint=footprint or "",
                lib_id=lib_id,
                dnp=dnp,
                mpn=mpn or value,
            )
        )
        return component

    def two_pin(
        self,
        prefix: str,
        lib_id: str,
        value: str,
        footprint_key: str,
        net1: str,
        net2: str,
        position: tuple[float, float],
        *,
        mpn: str | None = None,
        manufacturer: str | None = None,
        dnp: bool = False,
        reference: str | None = None,
    ):
        return self.add(
            lib_id=lib_id,
            value=value,
            footprint_key=footprint_key,
            nets={"1": net1, "2": net2},
            position=position,
            prefix=prefix,
            mpn=mpn,
            manufacturer=manufacturer,
            dnp=dnp,
            reference=reference,
        )

    def resistor(
        self,
        net1: str,
        net2: str,
        value: str,
        position: tuple[float, float],
        *,
        dnp: bool = False,
        footprint_key: str = "R1206",
        reference: str | None = None,
    ):
        manufacturer, mpn = MPN[footprint_key]
        return self.two_pin(
            "R",
            "Device:R",
            value,
            footprint_key,
            net1,
            net2,
            position,
            mpn=f"{mpn} {value}" if footprint_key == "R0805" else f"RC1206FR-07 1% {value}",
            manufacturer=manufacturer,
            dnp=dnp,
            reference=reference,
        )

    def resistor_pack4(
        self,
        value: str,
        footprint_key: str,
        pairs: list[tuple[str | None, str | None]],
        position: tuple[float, float],
        *,
        dnp: bool = False,
        reference: str | None = None,
    ):
        if len(pairs) != 4:
            raise ValueError("A four-resistor pack requires four pairs")
        pins = [("1", "8"), ("2", "7"), ("3", "6"), ("4", "5")]
        nets = {}
        for (pin_a, pin_b), (net_a, net_b) in zip(pins, pairs):
            nets[pin_a] = net_a
            nets[pin_b] = net_b
        manufacturer, mpn = MPN[footprint_key]
        exact_mpns = {
            ("R_Array_4x0603", "1k"): "YC164-FR-071KL",
            ("R_Array_4x0603", "4.7k"): "YC164-FR-074K7L",
            ("R_Array_4x0603", "10k"): "YC164-FR-0710KL",
            ("R_Array_4x1206", "100R"): "YC324-FR-07100RL",
            ("R_Array_4x1206", "330R"): "YC324-FR-07330RL",
            ("R_Array_4x1206", "0R"): "YC324-JK-070RL",
        }
        mpn = exact_mpns.get((footprint_key, value), mpn)
        return self.add(
            lib_id="LeanCam:ResistorPack04",
            value=f"4x{value}",
            footprint_key=footprint_key,
            nets=nets,
            position=position,
            prefix="RN",
            mpn=mpn,
            manufacturer=manufacturer,
            dnp=dnp,
            reference=reference,
        )

    def capacitor(
        self,
        net1: str,
        net2: str,
        value: str,
        position: tuple[float, float],
        *,
        footprint_key: str | None = None,
        lib_id: str = "Device:C",
        dnp: bool = False,
        reference: str | None = None,
    ):
        if footprint_key is None:
            footprint_key = "C0805" if value in {"100nF", "1uF"} else "C1206"
        manufacturer, mpn = MPN[footprint_key]
        return self.two_pin(
            "C",
            lib_id,
            value,
            footprint_key,
            net1,
            net2,
            position,
            manufacturer=manufacturer,
            mpn=f"{mpn} {value}",
            dnp=dnp,
            reference=reference,
        )

    def diode(
        self,
        net_k: str,
        net_a: str,
        position: tuple[float, float],
        *,
        value: str = "1N4148WS",
        lib_id: str = "Device:D",
        footprint_key: str = "D_SOD323",
        dnp: bool = False,
        reference: str | None = None,
    ):
        manufacturer, mpn = MPN[footprint_key]
        return self.two_pin(
            "D",
            lib_id,
            value,
            footprint_key,
            net_k,
            net_a,
            position,
            mpn=mpn if value == "1N4148WS" else value,
            manufacturer=manufacturer,
            dnp=dnp,
            reference=reference,
        )

    def led(
        self,
        net_k: str,
        net_a: str,
        position: tuple[float, float],
        value: str = "indicator",
        *,
        reference: str | None = None,
    ):
        manufacturer, mpn = MPN["LED1206"]
        return self.two_pin(
            "D",
            "Device:LED",
            value,
            "LED1206",
            net_k,
            net_a,
            position,
            mpn=mpn,
            manufacturer=manufacturer,
            reference=reference,
        )

    def header(
        self,
        rows: int,
        count: int,
        nets: dict[str, str],
        position: tuple[float, float],
        value: str,
        *,
        dnp: bool = False,
        reference: str | None = None,
    ):
        if rows == 1:
            lib_id = f"Connector_Generic:Conn_01x{count:02d}"
            footprint_key = f"HDR1X{count}"
        else:
            lib_id = f"Connector_Generic:Conn_02x{count:02d}_Odd_Even"
            footprint_key = f"HDR{rows}X{count}" if rows != 2 or count != 10 else "HDR2X10_2MM"
        if footprint_key is None:
            raise RuntimeError(f"Connector footprint not configured: {rows}x{count}")
        manufacturer, mpn = MPN.get(footprint_key, ("generic", value))
        return self.add(
            lib_id=lib_id,
            value=value,
            footprint_key=footprint_key,
            nets=nets,
            position=position,
            prefix="J",
            mpn=mpn,
            manufacturer=manufacturer,
            dnp=dnp,
            reference=reference,
        )

    def terminal(
        self,
        count: int,
        nets: dict[str, str],
        position: tuple[float, float],
        value: str,
        *,
        reference: str | None = None,
    ):
        return self.add(
            lib_id=f"Connector_Generic:Conn_01x{count:02d}",
            value=value,
            footprint_key=f"TERM{count}",
            nets=nets,
            position=position,
            prefix="J",
            mpn=f"Phoenix Contact MCV 1,5/{count}-G-3.5",
            manufacturer="Phoenix Contact",
            reference=reference,
        )

    def save(self) -> Path:
        path = HARDWARE / self.filename
        self.sch.save(path)
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r'(?m)^\t\(label ("[^"]+")\n\t\t\(at ([^\)]+)\)\n\t\t\(effects',
            lambda m: (
                f"\t(global_label {m.group(1)}\n"
                "\t\t(shape passive)\n"
                f"\t\t(at {m.group(2)})\n"
                "\t\t(fields_autoplaced yes)\n"
                "\t\t(effects"
            ),
            text,
        )
        for component_uuid in self.dnp_uuids:
            marker = f'(uuid "{component_uuid}")'
            index = text.find(marker)
            if index < 0:
                raise RuntimeError(f"Could not locate DNP symbol {component_uuid}")
            block_start = text.rfind("\n\t(symbol\n", 0, index)
            block_end = text.find("\n\t(symbol\n", index)
            if block_end < 0:
                block_end = text.find("\n\t(sheet_instances", index)
            block = text[block_start:block_end]
            block = block.replace("\t\t(dnp no)", "\t\t(dnp yes)", 1)
            text = text[:block_start] + block + text[block_end:]
        path.write_text(text, encoding="utf-8")
        return path


def make_root() -> None:
    root = Schematic.create("LeanCam NCC RP2350B Motherboard", paper="A2")
    sheets = [
        ("Power and supervision", "power.kicad_sch", 20, 20, 120, 80, "2"),
        ("MCU, shift chains and safety", "mcu_io.kicad_sch", 20, 115, 180, 100, "3"),
        ("16 PLC inputs and expansion", "field_inputs.kicad_sch", 215, 20, 160, 120, "4"),
        ("24 PLC outputs", "field_outputs.kicad_sch", 390, 20, 160, 120, "5"),
        ("Encoders", "encoders.kicad_sch", 215, 155, 120, 85, "6"),
        ("Display", "display.kicad_sch", 350, 155, 200, 85, "7"),
        ("Storage, Wi-Fi and UI", "storage_wifi_ui.kicad_sch", 20, 230, 160, 100, "8"),
        ("Analog I/O", "analog_io.kicad_sch", 200, 255, 140, 90, "9"),
    ]
    for name, filename, x, y, width, height, page in sheets:
        root.add_sheet(
            name=name,
            filename=filename,
            position=(x, y),
            size=(width, height),
            page_number=page,
        )
    root.add_text_box(
        text=(
            "LeanCam NCC RP2350B motherboard\n"
            "This root sheet instantiates the functional hierarchy. Global net labels are "
            "the inter-sheet contract; see documentation/gpio-map.md and io-bit-map.md."
        ),
        position=(18, 270),
        size=(160, 30),
        font_size=1.6,
        stroke_width=0.2,
    )
    root.save(HARDWARE / "motherboard.kicad_sch")


def add_power(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "Power tree: fused 12-24 V input with a TVS and two independent 1 A "
        "series-diode feeds. One feed powers the 5 V logic buck and analog housekeeping; "
        "the other powers the nominal 11 V backlight buck. WeAct onboard 3.3 V "
        "regulation supplies only the module, and the ESP has its own 3.3 V LDO.",
        15,
        15,
        175,
        28,
    )

    b.terminal(2, {"1": "VIN_RAW", "2": "GND"}, (30, 60), "24 V DC input")
    b.two_pin("F", "Device:Fuse", "2 A", "R1206", "VIN_RAW", "VIN_FUSED", (55, 55), mpn="0ZCG0200FF2E", manufacturer="Bel Fuse")
    b.two_pin("D", "Device:D_TVS", "SMBJ24CA", "D_SMB", "VIN_FUSED", "GND", (72, 55), mpn="SMBJ24CA", manufacturer="Bourns")
    b.next_ref("C")  # retired common bulk capacitor C1
    b.capacitor("VIN_FUSED", "GND", "100nF 100V", (100, 55), footprint_key="C1206_100V")

    # Two independent 1 A series feeds provide reverse-polarity protection and
    # keep the logic converter and backlight converter on separate branches.
    b.diode(
        "VIN_PROT",
        "VIN_FUSED",
        (115, 65),
        value="SS16",
        footprint_key="D_SMA",
        reference="D2",
    )
    b.diode(
        "VIN_BL_PROT",
        "VIN_FUSED",
        (115, 80),
        value="SS16",
        footprint_key="D_SMA",
        reference="D3",
    )
    b.next_ref("Q")  # retired Q1 reverse-polarity MOSFET
    b.next_ref("R")  # retired R1 gate pull-down
    b.capacitor("VIN_PROT", "GND", "22uF 50V", (145, 65), footprint_key="C1210")
    b.capacitor("VIN_PROT", "GND", "100nF 100V", (157, 65), footprint_key="C1206_100V")

    # TI LMR36510 reference values for 5 V/1 A at 400 kHz:
    # L1=22 uH, COUT=2x22 uF, RFBT=33k+100k, RFBB=33k.
    b.add(
        lib_id="Regulator_Switching:LMR36510ADDA",
        value="LMR36510ADDAR",
        footprint_key="SOIC8_POWERPAD",
        nets={
            "1": "GND",
            "2": "VIN_PROT",
            "3": "VIN_PROT",
            "4": "PWR_GOOD_N",
            "5": "FB5",
            "6": "VCC5",
            "7": "BUCK5_BST",
            "8": "BUCK5_SW",
            "9": "GND",
        },
        position=(45, 100),
        prefix="U",
        mpn="LMR36510ADDAR",
        manufacturer="Texas Instruments",
    )
    b.two_pin("L", "Device:L", "22uH 1.5A", "L_SRN6045", "BUCK5_SW", "+5V", (75, 100), mpn="SRN6045TA-220M", manufacturer="Bourns")
    b.capacitor("VIN_PROT", "GND", "22uF 50V", (30, 120), footprint_key="C1210")
    b.capacitor("+5V", "GND", "22uF 50V", (115, 100), footprint_key="C1210")
    b.capacitor("+5V", "GND", "100nF", (127, 100))
    b.next_ref("C")  # retired C8: C6/C11 already provide 2x22uF output bulk

    # Peripheral 3.3 V LDO. The WeAct regulator supplies only the module; this
    # separate linear rail prevents the MCU regulator from carrying board loads.
    b.add(
        lib_id="Regulator_Linear:AMS1117-3.3",
        value="AMS1117-3.3",
        footprint_key="SOT223",
        nets={
            "1": "GND",
            "2": "+3V3",
            "3": "+5V",
        },
        position=(65, 145),
        prefix="U",
        reference="U2",
        mpn="AMS1117-3.3",
        manufacturer="Advanced Monolithic Systems",
    )
    b.next_ref("L")  # reserve L2 for the dedicated backlight buck
    b.next_ref("C")  # retired 3.3 V buck bootstrap C9
    b.capacitor("+5V", "GND", "22uF 50V", (52, 155), footprint_key="C1210")
    b.capacitor("+5V", "GND", "22uF 50V", (118, 145), footprint_key="C1210")
    b.next_ref("C")  # retired optional output capacitor C12
    b.capacitor("+3V3", "GND", "100nF", (142, 145))
    # Isolated 3.3 V analog rail.
    b.two_pin(
        "FB",
        "Device:FerriteBead",
        "600R@100MHz",
        "R1206",
        "+3V3",
        "+3V3_A",
        (160, 145),
        mpn="BLM18KG601SN1D",
        manufacturer="Murata",
    )
    b.next_ref("C")  # retired C14: C15 provides the required reference bypass
    b.capacitor("+3V3_A", "GND", "100nF", (187, 145))

    # WeAct USB/5 V backfeed handling is provided by the module. Retire the
    # former ideal-diode branch without renumbering the remaining parts.
    b.next_ref("U")  # retired U3
    b.next_ref("C")  # retired C16: redundant +5V bulk
    b.next_ref("C")  # retired C17: redundant +5V bypass
    b.next_ref("R")  # retired status pull-up R2

    # The WeAct module owns reset and supervision.
    b.next_ref("U")  # retired U4
    b.next_ref("R")  # retired reset pull-up R3

    b.led("GND", "PWR5_LEDA", (240, 90), "5V_PWR")
    b.resistor("+5V", "PWR5_LEDA", "1k", (253, 90))
    b.led("GND", "PWR3_LEDA", (240, 110), "3V3_PWR")
    b.resistor("+3V3", "PWR3_LEDA", "1k", (253, 110))

    power_flags = (
        "GND",
        "+5V",
        "+3V3_A",
        "VIN_PROT",
        "+5V_ENC",
        "+3V3_SD",
        "+5V_ISO_IN",
        "+12V_FIELD",
        "VIN_BL_PROT",
        "+12V_BL",
    )
    for index, net in enumerate(power_flags):
        b.add(
            lib_id="power:PWR_FLAG",
            value=net,
            footprint_key=None,
            nets={"1": net},
            position=(25 + index * 12, 185),
            prefix="FLG",
            mpn="",
            manufacturer="",
        )

    b.note(
        "Default: the LMR36510 generates +5V for the module and both peripheral LDOs. "
        "The WeAct onboard regulator supplies only the module, whose 3V3 outputs and "
        "VBUS remain local.",
        120,
        165,
        140,
        34,
    )


def add_mcu(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "Shift order (verified from the hardware chain): 74HC165 Q7 -> next DS, with "
        "the PLC input banks assigned to their nearest 74HC165 data pins; "
        "74HC595 SER enters the OUT0-7 register and QH' continues "
        "to the keyboard byte. Both 32-bit chains share one hardware clock. "
        "The 595 data/clock/latch controls use consecutive GPIO20/21/22 for "
        "uCNC RP2350 PIO compatibility. Latch is simultaneous.",
        15,
        15,
        190,
        32,
    )

    gpio_nets = {
        "1": "GND", "2": "GND", "3": None, "4": None, "5": "AOUT3_PWM",
        "6": "AOUT1_PWM", "7": "AI2_ADC", "8": "AI0_ADC", "9": "HOLD_N",
        "10": None, "11": "ENC2_Z_3V3", "12": "ENC2_A_3V3",
        "13": "ENC1_B_3V3", "14": "ENC0_Z_3V3", "15": "ENC0_A_3V3",
        "16": "GND", "17": None, "18": None, "19": "AOUT0_PWM",
        "20": "AOUT2_PWM", "21": "PWR_GOOD_N", "22": "AI1_ADC", "23": "START_N",
        "24": "ESTOP_N", "25": "BL_PWM_MCU", "26": "ENC2_B_3V3",
        "27": "ENC1_Z_3V3", "28": "ENC1_A_3V3", "29": "ENC0_B_3V3",
        "30": None, "31": "+5V", "32": "GND", "33": None,
        "34": "SD_CD_MCU", "35": "SD_MISO_MCU", "36": "SD_SCK_MCU",
        "37": "I2C_SDA", "38": "WIFI_TX", "39": "HSTX_D0_P",
        "40": "HSTX_D1_P", "41": "HSTX_D2_P", "42": "HSTX_CLK_P",
        "43": "SR_OUT_SER", "44": "SR_LATCH", "45": "SR_PL_N", "46": None,
        "47": "GND", "48": "+3V3_A", "49": None, "50": None,
        "51": "SD_CS_MCU", "52": "SD_MOSI_MCU", "53": "I2C_SCL", "54": "WIFI_RX",
        "55": "HSTX_D0_N", "56": "HSTX_D1_N", "57": "HSTX_D2_N",
        "58": "HSTX_CLK_N", "59": "SR_SCK", "60": "SR_IN_Q7", "61": "GND",
        "62": "SWCLK", "63": "SWDIO", "64": None,
    }
    b.add(
        lib_id="LeanCam:WeAct_RP2350B",
        value="WeAct RP2350B Core Board (socketed)",
        footprint_key="WEACT",
        nets=gpio_nets,
        position=(150, 95),
        prefix="MOD",
        mpn="WeAct Studio RP2350B Core Board",
        manufacturer="WeAct Studio",
        reference="MOD1",
    )

    # The WeAct board supplies RUN/reset, its reset button, POR/BOR and watchdog.
    # Keep the reserved references so the remaining hierarchy stays stable.
    b.next_ref("D")   # retired reset diode D7
    b.next_ref("SW")  # retired reset button SW1
    b.next_ref("C")   # retired reset capacitor C21

    b.header(
        1,
        4,
        {"1": "+3V3", "2": "SWDIO", "3": "SWCLK", "4": "GND"},
        (65, 155),
        "SWD",
    )
    # Use the WeAct board's onboard status LED so GPIO46 is available for the
    # fourth 0-10 V output. Reserve the old references to keep numbering stable.
    b.next_ref("D")  # removed external status LED D8
    b.next_ref("R")  # removed status LED resistor R8

    # Input chain: keyboard register is the far end; PLC inputs 1-8 are nearest MISO.
    in_u_order = [(11, 24), (10, 16), (9, 8), (8, 0)]
    positions = [(70, 195), (100, 195), (130, 195), (160, 195)]
    for offset, ((unit_index, base), pos) in enumerate(zip(in_u_order, positions)):
        next_ds = "SR_IN_DS0" if offset == 0 else f"SR_IN_CHAIN{offset}"
        if base < 16:
            # D0-D7 assignments are selected from the placed optocoupler and
            # shift-register pin geometry. This removes all local ratline
            # crossings at the cost of a documented firmware permutation.
            plc_pin_numbers = {
                0: (5, 6, 7, 8, 4, 3, 2, 1),
                8: (13, 14, 15, 16, 12, 11, 10, 9),
            }
            data_nets = [
                f"PLC_IN{number}_N" for number in plc_pin_numbers[base]
            ]
        elif base < 24:
            data_nets = [f"EXP_IN{index}" for index in range(8)]
        else:
            data_nets = [f"KIN{index}_FILT" for index in range(8)]
        nets = {
            "1": "SR_PL_N",
            "2": "SR_SCK",
            "3": data_nets[4],
            "4": data_nets[5],
            "5": data_nets[6],
            "6": data_nets[7],
            "7": None,
            "8": "GND",
            "9": f"SR_IN_CHAIN{offset + 1}" if offset < 3 else "SR_IN_Q7",
            "10": next_ds,
            "11": data_nets[0],
            "12": data_nets[1],
            "13": data_nets[2],
            "14": data_nets[3],
            "15": "GND",
            "16": "+3V3",
        }
        b.add(
            lib_id="74xx:74HC165",
            value="74HC165D",
            footprint_key="SOIC16",
            nets=nets,
            position=pos,
            prefix="U",
            mpn="74HC165D,653",
            manufacturer="Nexperia",
        )
        b.capacitor("+3V3", "GND", "100nF", (pos[0] + 16, pos[1]))
    b.resistor("SR_IN_DS0", "GND", "10k", (55, 210))
    b.resistor("SR_SCK", "GND", "10k", (40, 210))
    b.resistor("SR_PL_N", "+3V3", "10k", (40, 225))

    # Output chain: OUT0-7 enters the first register; keyboard is the farthest byte.
    out_positions = [(70, 245), (100, 245), (130, 245), (160, 245)]
    # The first two register bytes use non-sequential Q-pin maps selected from
    # the placed board. This lets the facing 595/541 pins connect without
    # ratline crossings while preserving OUTn -> BUFYn -> MOTIONn.
    output_register_pin_bits = (
        {15: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4, 6: 7, 7: 6},
        {15: 2, 1: 1, 2: 0, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},
        {15: 7, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6},
        {15: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7},
    )
    for offset, pos in enumerate(out_positions):
        base = offset * 8
        ser = "SR_OUT_SER" if offset == 0 else f"SR_OUT_CHAIN{offset}"
        q_next = f"SR_OUT_CHAIN{offset + 1}" if offset < 3 else "SR_OUT_QH_LAST"
        pin_bits = output_register_pin_bits[offset]
        nets = {
            str(pin): f"OUT{base + bit}" for pin, bit in pin_bits.items()
        }
        nets.update({
            "8": "GND",
            "9": q_next if offset < 3 else None,
            "10": "+3V3",
            "11": "SR_SCK",
            "12": "SR_LATCH",
            "13": "GND",
            "14": ser,
            "16": "+3V3",
        })
        b.add(
            lib_id="74xx:74HC595",
            value="74HC595D",
            footprint_key="SOIC16",
            nets=nets,
            position=pos,
            prefix="U",
            mpn="74HC595D,118",
            manufacturer="Nexperia",
        )
        b.capacitor("+3V3", "GND", "100nF", (pos[0] + 16, pos[1]))
    b.resistor("SR_OUT_SER", "GND", "10k", (55, 260))
    b.resistor("SR_LATCH", "GND", "10k", (55, 275))

    # Local output-gating circuitry is intentionally omitted. The external
    # machine interface owns hard output blocking; on this board the 595 and
    # 541 output-enable pins are tied active so the shift chain remains usable.
    for _ in range(3):
        b.next_ref("U")  # retired U14-U16 AND gates
    b.next_ref("Q")     # retired Q4 inverter
    b.next_ref("R")     # retired R14 base resistor
    b.next_ref("R")     # retired R15 pull-up

    b.note(
        "Output safety qualification is external. J5/J6/J26 are local control "
        "inputs only. 74HC595 and AHCT541 output-enable pins are tied active; "
        "the external machine interface must provide hard output blocking.",
        190,
        325,
        165,
        40,
    )


def add_field_inputs(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "16 isolated PLC field positions use software-remapped logical channels to minimize PCB crossings. "
        "Dedicated E-stop, HOLD and START "
        "optochannels are separate connectors, not shift-register bits. PLC and control channels "
        "keep the 2.2 k series limit, indicator LED and reverse diode. U17's two "
        "used control channels use individual EL3H7 DIP-4 optocouplers "
        "U35/U36; PLC inputs use four LTV-847S SOIC-16W packages. Four 4x4.7 k "
        "isolated networks provide the PLC pull-ups and no input-node capacitor "
        "is fitted. Expansion bits "
        "16-23 are split across two 1x6 headers.",
        15,
        15,
        190,
        45,
    )

    # E-stop and HOLD remain completely outside the input shift chain. START is
    # added with its opto channel later, after J25 has taken reference 25.
    b.terminal(
        2,
        {"1": "ESTOP_FIELD", "2": "FIELD_SAFETY_COM"},
        (25, 70),
        "Dedicated E-stop loop",
    )
    b.terminal(
        2,
        {"1": "HOLD_FIELD", "2": "FIELD_SAFETY_COM"},
        (25, 95),
        "Dedicated HOLD button input",
    )

    for block in range(2):
        # Each original 16-position bank is split into two 8-position
        # connectors. J7 therefore feeds channels 9-16 and J8 feeds 1-8;
        # firmware compensates for that physical bank order.
        logical_numbers = tuple(range(9, 17)) if block == 0 else tuple(range(1, 9))
        nets = {}
        for local in range(4):
            number = logical_numbers[local]
            nets[str(2 * local + 1)] = f"FIELD_IN{number}"
            nets[str(2 * local + 2)] = f"FIELD_COM{block}"
        b.terminal(
            8,
            nets,
            (25, 125 + block * 48),
            f"PLC positions {block * 8 + 1}-{block * 8 + 4}; software-mapped isolated inputs",
            reference=f"J{7 + block}",
        )

    for index, (field_net, led_net, opto_net, output_net) in enumerate(
        (
            ("ESTOP_FIELD", "ESTOP_LED_A", "ESTOP_OPTO_A", "ESTOP_N"),
            ("HOLD_FIELD", "HOLD_LED_A", "HOLD_OPTO_A", "HOLD_N"),
        )
    ):
        x = 100 + index * 35
        b.resistor(field_net, led_net, "2.2k", (x, 72))
        b.led(opto_net, led_net, (x, 87))
        b.diode(led_net, "ISO_GND", (x + 7, 72))
        b.next_ref("C")  # removed input filter C30/C31
    b.next_ref("RN")  # removed safety pull-up pack RN1
    b.next_ref("U")  # retired quad safety optocoupler U17
    b.next_ref("C")   # removed U17 pull-up rail bypass C32

    for group in range(4):
        x0 = 240 + (group % 2) * 100
        y0 = 65 + (group // 2) * 100
        for channel in range(4):
            bit = group * 4 + channel
            number = bit + 1

            x = x0 + channel * 17
            b.resistor(f"FIELD_IN{number}", f"FLD_LED{number}_A", "2.2k", (x, y0))
            b.led(f"FLD_OPTO{number}_A", f"FLD_LED{number}_A", (x, y0 + 15))
            b.diode(f"FLD_LED{number}_A", "ISO_GND", (x + 7, y0))
            b.next_ref("C")  # removed input filter capacitor
        opto_pins = {}
        for channel in range(4):
            number = group * 4 + channel + 1
            opto_pins[str(1 + channel * 2)] = f"FLD_OPTO{number}_A"
            opto_pins[str(2 + channel * 2)] = "ISO_GND"
            opto_pins[str(16 - channel * 2)] = f"PLC_IN{number}_N"
            opto_pins[str(15 - channel * 2)] = "GND"
        b.add(
            lib_id="LeanCam:QuadOpto",
            value="LTV-847S",
            footprint_key="SOIC16W",
            nets=opto_pins,
            position=(x0 + 27, y0 + 79),
            prefix="U",
            mpn="LTV-847S",
            manufacturer="Lite-On",
        )
        b.next_ref("RN")  # preserve the retired PLC pull-up pack refs
        b.next_ref("C")   # removed pull-up rail bypass C37-C52

    expansion_nets = {"1": "GND", "2": "+3V3"}
    for signal in range(4):
        expansion_nets[str(signal + 3)] = f"EXP_IN{signal}"
    b.header(
        1,
        6,
        expansion_nets,
        (45, 175),
        "Expansion inputs 0-3; 1=GND, 2=3.3 V",
        reference="J9",
    )
    for pack_index in range(2):
        b.resistor_pack4(
            "10k",
            "R_Array_4x0603",
            [(f"EXP_IN{pack_index * 4 + signal}", "GND") for signal in range(4)],
            (105 + pack_index * 50, 185),
        )

    b.next_ref("U")  # retired E-stop receiver U22
    b.next_ref("U")  # retired fault receiver U23

    b.note(
        "FIELD COM 0/1 are isolated returns and have no copper connection to GND. "
        "Each bank uses one selector: external 24 V wetting or the internal "
        "protected isolated 12 V contact supply.",
        390,
        200,
        140,
        35,
    )


def add_isolated_field_supply(builder: SheetBuilder) -> None:
    """Add the isolated dry-contact supply and field-mode solder selectors."""
    b = builder
    b.two_pin(
        "F",
        "Device:Fuse",
        "750mA",
        "R1206",
        "+5V",
        "+5V_ISO_IN",
        (470, 65),
        reference="F4",
        mpn="0ZCG0075FF2E",
        manufacturer="Bel Fuse",
    )
    b.capacitor(
        "+5V_ISO_IN",
        "GND",
        "22uF 50V",
        (485, 65),
        footprint_key="C1210",
        reference="C103",
    )
    b.add(
        lib_id="Converter_DCDC:TBA2-0512",
        value="TBA2-0512",
        footprint_key="DCDC_TBA2",
        nets={
            "1": "+5V_ISO_IN",
            "2": "GND",
            "4": "ISO_GND",
            "6": "+12V_RAW",
        },
        position=(485, 85),
        prefix="U",
        reference="U40",
        mpn="TBA2-0512",
        manufacturer="Traco Power",
    )
    b.diode(
        "+12V_FIELD",
        "+12V_RAW",
        (510, 85),
        value="SS54",
        footprint_key="D_SMA",
        reference="D56",
    )
    b.capacitor(
        "+12V_FIELD",
        "ISO_GND",
        "10uF 25V",
        (525, 85),
        footprint_key="C1206",
        reference="C105",
    )
    # One three-pin selector per field bank:
    # 1-2 = external 24 V, 2-3 = internal isolated 12 V contact mode.
    field_selectors = (
        ("JP2", "J7 24V/CONTACT", "FIELD_COM0", (485, 120)),
        ("JP3", "J8 24V/CONTACT", "FIELD_COM1", (510, 120)),
        ("JP4", "SAFETY 24V/CONTACT", "FIELD_SAFETY_COM", (535, 120)),
    )
    for reference, value, common_net, position in field_selectors:
        b.add(
            lib_id="Connector_Generic:Conn_01x03",
            value=value,
            footprint_key="HDR1X3",
            nets={"1": "ISO_GND", "2": common_net, "3": "+12V_FIELD"},
            position=position,
            prefix="JP",
            reference=reference,
        )

def add_field_outputs(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "32-bit output chain: bit0 drives the isolated AUX output; bits1-15 are "
        "buffered to the fifteen motion outputs; bits16-29 drive all fourteen "
        "ULN2003A low-side channels; bits30-31 use BSS138 low-side MOSFETs. "
        "Bits24-31 also drive the keyboard through series resistors. J12 exposes "
        "DO0-DO7 and J32 exposes DO8-DO15.",
        15,
        15,
        180,
        35,
    )

    motion_labels = [
        "AX0_STEP", "AX0_DIR", "AX0_EN",
        "AX1_STEP", "AX1_DIR", "AX1_EN",
        "AX2_STEP", "AX2_DIR", "AX2_EN",
        "AX3_STEP", "AX3_DIR", "AX3_EN",
        "AX4_STEP", "AX4_DIR", "AX4_EN",
    ]
    keyboard_labels = [f"KOUT{i}" for i in range(8)]

    buffer_specs = [
        (0, "MOTION_BUF0", (6, 7, 4, 5, 2, 3, 0, 1)),
        (1, "MOTION_BUF1", (15, 14, 13, 12, 11, 10, 8, 9)),
    ]
    for byte_index, value, channel_bits in buffer_specs:
        x = 50 + byte_index * 55
        input_pins = (2, 3, 4, 5, 6, 7, 8, 9)
        output_pins = (18, 17, 16, 15, 14, 13, 12, 11)
        nets = {"1": "GND", "10": "GND", "19": "GND", "20": "+5V"}
        nets.update(
            {
                str(pin): f"OUT{bit}"
                for pin, bit in zip(input_pins, channel_bits)
            }
        )
        nets.update(
            {
                str(pin): f"BUFY{bit}"
                for pin, bit in zip(output_pins, channel_bits)
            }
        )
        b.add(
            lib_id="LeanCam:OctalBuffer5V",
            value="SN74AHCT541DW",
            footprint_key="SOIC20W",
            nets=nets,
            position=(x, 80),
            prefix="U",
            mpn="SN74AHCT541DW",
            manufacturer="Texas Instruments",
        )
        b.capacitor("+5V", "GND", "100nF", (x, 100))

    # Four-channel arrays keep the repeated field I/O passives compact.
    output_pulldown_pairs = (
        (("GND", "BUFY2"), ("GND", "BUFY3"),
         ("GND", "BUFY0"), ("GND", "BUFY1")),
        (("BUFY5", "GND"), ("BUFY4", "GND"),
         ("BUFY7", "GND"), ("BUFY6", "GND")),
        (("BUFY9", "GND"), ("BUFY8", "GND"),
         ("BUFY10", "GND"), ("BUFY11", "GND")),
        (("GND", "BUFY15"), ("GND", "BUFY14"),
         ("GND", "BUFY13"), ("GND", "BUFY12")),
        (("OUT19", "GND"), ("OUT18", "GND"),
         ("OUT17", "GND"), ("OUT16", "GND")),
        ((None, None), ("OUT22", "GND"),
         ("OUT21", "GND"), ("OUT20", "GND")),
    )
    for pack_index, pairs in enumerate(output_pulldown_pairs):
        b.resistor_pack4(
            "10k",
            "R_Array_4x0603",
            list(pairs),
            (35 + (pack_index % 4) * 55, 280 + (pack_index // 4) * 50),
        )
    # Keyboard outputs are intentionally not pulled down while the 595 chain is
    # disabled. Keep the retired references reserved so later arrays stay stable.
    b.next_ref("RN")  # retired RN14
    b.next_ref("RN")  # retired RN15
    motion_output_pairs = (
        (("BUFY2", "MOTION2"), ("BUFY3", "MOTION1"),
         ("BUFY0", "AUX_GATE"), ("BUFY1", "MOTION0")),
        (("BUFY6", "MOTION6"), ("BUFY7", "MOTION5"),
         ("BUFY4", "MOTION4"), ("BUFY5", "MOTION3")),
        (("BUFY11", "MOTION10"), ("BUFY10", "MOTION9"),
         ("BUFY8", "MOTION8"), ("BUFY9", "MOTION7")),
        (("BUFY15", "MOTION14"), ("BUFY14", "MOTION13"),
         ("BUFY13", "MOTION12"), ("BUFY12", "MOTION11")),
    )
    for pack_index, pairs in enumerate(motion_output_pairs):
        b.resistor_pack4(
            "100R",
            "R_Array_4x1206",
            list(pairs),
            (35 + pack_index * 55, 225),
        )
    keyboard_output_pairs = (
        (
            ("KOUT0", "OUT24"), ("KOUT1", "OUT25"),
            ("KOUT2", "OUT26"), ("KOUT3", "OUT27"),
        ),
        (
            ("KOUT4", "OUT28"), ("KOUT5", "OUT29"),
            ("KOUT6", "OUT30"), ("KOUT7", "OUT31"),
        ),
    )
    for pack_index, pairs in enumerate(keyboard_output_pairs):
        b.resistor_pack4(
            "100R",
            "R_Array_4x1206",
            pairs,
            (255 + pack_index * 55, 225),
        )

    # Both ULN packages use all seven channels. The order follows the fixed
    # left-to-right package pads while preserving logical OUTn -> DOn mapping.
    uln_channel_bits = ((6, 5, 4, 3, 2, 1, 0), (13, 12, 11, 10, 9, 8, 7))
    for package, channel_bits in enumerate(uln_channel_bits):
        nets = {"8": "GND", "9": "DO_COM"}
        input_numbers = [1, 2, 3, 4, 5, 6, 7]
        output_numbers = [16, 15, 14, 13, 12, 11, 10]
        for channel in range(7):
            bit = channel_bits[channel]
            nets[str(input_numbers[channel])] = f"OUT{bit + 16}"
            nets[str(output_numbers[channel])] = f"DO{bit}"
        b.add(
            lib_id="Transistor_Array:ULN2003A",
            value="ULN2003ADR",
            footprint_key="SOIC16",
            nets=nets,
            position=(170 + package * 45, 195),
            prefix="U",
            mpn="ULN2003ADR",
            manufacturer="Texas Instruments",
        )
        b.capacitor("DO_COM", "GND", "100nF", (170 + package * 45, 210))

    # Output LEDs indicate low-side channel energisation.
    for bit in range(8):
        x = 250 + (bit % 4) * 18
        y = 150 + (bit // 4) * 28
        b.led(f"DO{bit}", f"DO_LED{bit}_A", (x, y), f"DO{bit}")
        b.resistor(f"DO_COM", f"DO_LED{bit}_A", "2.2k", (x + 8, y))

    b.terminal(
        4,
        {"1": "MOTION0", "2": "MOTION1", "3": "MOTION2", "4": "GND"},
        (300, 140),
        "AX0: EN, STEP, DIR, GND",
        reference="J10",
    )
    b.terminal(
        4,
        {"1": "MOTION3", "2": "MOTION4", "3": "MOTION5", "4": "GND"},
        (330, 140),
        "AX1: EN, STEP, DIR, GND",
        reference="J11",
    )
    b.terminal(
        8,
        {
            "1": "DO0", "2": "DO1", "3": "DO2", "4": "DO3",
            "5": "DO4", "6": "DO5", "7": "DO6", "8": "DO7",
        },
        (300, 210),
        "General outputs 0-7",
    )
def add_input_pullups(
    builder: SheetBuilder,
    storage_builder: SheetBuilder,
) -> None:
    """Add discrete safety pull-ups and grouped PLC pull-up networks."""
    b = builder
    b.note(
        "The dedicated E-stop, HOLD and START channels use individual EL3H7 "
        "DIP-4 optocouplers U35/U36/U39 and keep discrete 4.7 k pull-ups. PLC "
        "inputs use four LTV-847S packages with one isolated 4x4.7 k network per "
        "four-channel group. Every field input uses the same 2.2 k / indicator "
        "LED / reverse-diode chain. Firmware provides debouncing.",
        15,
        205,
        250,
        34,
    )

    b.terminal(
        2,
        {"1": "START_FIELD", "2": "FIELD_SAFETY_COM"},
        (480, 210),
        "Dedicated START button input",
    )
    b.resistor(
        "START_FIELD",
        "START_LED_A",
        "2.2k",
        (480, 225),
        reference="R108",
    )
    b.two_pin(
        "D",
        "Device:LED",
        "indicator",
        "LED1206",
        "START_OPTO_A",
        "START_LED_A",
        (480, 235),
        reference="D54",
        mpn="LTST-C150 series",
        manufacturer="Lite-On",
    )
    b.two_pin(
        "D",
        "Device:D",
        "1N4148WS",
        "D_SOD323",
        "START_LED_A",
        "ISO_GND",
        (490, 225),
        reference="D55",
        mpn="1N4148WS",
        manufacturer="Diodes Incorporated",
    )

    for opto_reference, anode_net, output_net, x in (
        ("U35", "ESTOP_OPTO_A", "ESTOP_N", 420),
        ("U36", "HOLD_OPTO_A", "HOLD_N", 440),
        ("U39", "START_OPTO_A", "START_N", 460),
    ):
        b.add(
            lib_id="LeanCam:EL3H7",
            value="EL3H7",
            footprint_key="DIP4",
            nets={
                "1": anode_net,
                "2": "ISO_GND",
                "3": "GND",
                "4": output_net,
            },
            position=(x, 250),
            prefix="U",
            reference=opto_reference,
            mpn="EL3H7",
            manufacturer="Everlight",
        )

    channels = [
        ("R74", "ESTOP_N"),
        ("R75", "HOLD_N"),
        ("R109", "START_N"),
    ]

    for index, (resistor_reference, output_net) in enumerate(channels):
        x = 55 + (index % 6) * 48
        y = 250 + (index // 6) * 45
        b.two_pin(
            "R",
            "Device:R",
            "4.7k",
            "R1206",
            output_net,
            "+3V3",
            (x, y),
            mpn="RC1206FR-07 4K7L",
            manufacturer="Yageo",
            reference=resistor_reference,
        )

    for group in range(4):
        numbers = tuple(range(group * 4 + 1, group * 4 + 5))
        b.resistor_pack4(
            "10k",
            "R_Array_4x0603",
            [(f"PLC_IN{number}_N", "+3V3") for number in numbers],
            (55 + group * 60, 340),
            reference=f"RN{32 + group}",
        )

    storage_builder.resistor_pack4(
        "10k",
        "R_Array_4x0603",
        [
            ("+3V3_WIFI", "WIFI_EN"),
            ("+3V3_WIFI", "WIFI_RST"),
            ("+3V3_WIFI", "WIFI_GPIO0"),
            ("+3V3_WIFI", "WIFI_GPIO2"),
        ],
        (20, 220),
        reference="RN36",
    )


def add_encoders(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "Three independent quadrature encoders. The first eight 5 V push-pull A/B/Z "
        "outputs feed U28, an SN74AHCT541 powered at 3.3 V. ENC2_Z uses only a "
        "5.1 k series / 10 k shunt divider, which is sufficient for this single "
        "input and avoids a second 20-pin buffer. No ESD array is fitted.",
        15,
        15,
        190,
        35,
    )
    for encoder in range(3):
        x0 = 50 + encoder * 80
        nets = {
            "1": "+5V_ENC",
            "2": f"ENC{encoder}_A_5V",
            "3": f"ENC{encoder}_B_5V",
            "4": f"ENC{encoder}_Z_5V",
            "5": "GND",
        }
        b.terminal(5, nets, (x0, 80), f"Encoder {encoder}: +5,A,B,Z,GND")

    encoder_inputs = [
        f"ENC{encoder}_{signal}_5V"
        for encoder in range(3)
        for signal in "ABZ"
    ]
    channels = encoder_inputs[:8]
    nets = {str(pin): "GND" for pin in range(2, 10)}
    nets.update({str(pin): None for pin in range(11, 19)})
    nets.update({"1": "GND", "10": "GND", "19": "GND", "20": "+3V3"})
    for input_pin, input_net in enumerate(channels, start=2):
        nets[str(input_pin)] = input_net
        nets[str(20 - input_pin)] = input_net.replace("_5V", "_3V3")
    b.add(
        lib_id="LeanCam:OctalBufferAHCT",
        value="SN74AHCT541DW",
        footprint_key="SOIC20W",
        nets=nets,
        position=(60, 125),
        prefix="U",
        mpn="SN74AHCT541DW",
        manufacturer="Texas Instruments",
    )
    b.capacitor("+3V3", "GND", "100nF", (60, 145))
    # Preserve later reference allocation: retired U29 and its C58 bypass.
    b.next_ref("U")
    b.next_ref("C")

    b.two_pin("F", "Device:Fuse", "500mA", "R1206", "+5V", "+5V_ENC", (30, 55), mpn="0ZCG0050FF2E", manufacturer="Bel Fuse")
    b.two_pin(
        "D",
        "Device:D_TVS",
        "SMAJ5.0A",
        "D_SMA",
        "+5V_ENC",
        "GND",
        (45, 55),
        mpn="SMAJ5.0A",
        manufacturer="Bourns",
    )


def add_encoder_z_divider(builder: SheetBuilder) -> None:
    b = builder
    b.resistor(
        "ENC2_Z_5V",
        "ENC2_Z_3V3",
        "5.1k",
        (180, 80),
        footprint_key="R0805",
        reference="R110",
    )
    b.resistor(
        "ENC2_Z_3V3",
        "GND",
        "10k",
        (194, 80),
        footprint_key="R0805",
        reference="R111",
    )
    b.note(
        "ENC2_Z level translation: 5.1 k series and 10 k to GND. "
        "5 V input produces approximately 3.31 V at the RP2350 pin.",
        170,
        95,
        70,
        25,
    )


def add_keyboard_storage_wifi(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "Full-size SD card, ESP-01/ESP-01S socket and combined 8x8 scan interface. "
        "Keyboard KIN0-7 feed the 74HC165 through one series resistor per line without "
        "pull-ups, capacitors or an active buffer; KOUT0-7 come directly from bits "
        "24-31 of the 74HC595 chain.",
        15,
        15,
        190,
        35,
    )

    scan_nets = {}
    for bit in range(8):
        scan_nets[str(2 * bit + 1)] = f"KIN{bit}"
        scan_nets[str(2 * bit + 2)] = f"KOUT{bit}"
    b.header(2, 8, scan_nets, (45, 75), "Keyboard KIN0-7 / KOUT0-7")
    b.header(1, 3, {"1": "+5V", "2": "GND", "3": "GND"}, (90, 75), "Keyboard power/reference")
    for pack_index in range(2):
        signals = range(pack_index * 4, pack_index * 4 + 4)
        b.resistor_pack4(
            "1k",
            "R_Array_4x0603",
            [(f"KIN{signal}_FILT", f"KIN{signal}") for signal in signals],
            (130 + pack_index * 60, 85),
        )
        b.next_ref("RN")  # removed keyboard pull-up RN23/RN25
        for _signal in signals:
            b.next_ref("C")  # removed keyboard filter C59-C66

    # I2C header with optional pull-up resistors.
    b.terminal(
        4,
        {"1": "I2C_SDA", "2": "I2C_SCL", "3": "+3V3", "4": "GND"},
        (35, 150),
        "I2C0",
        reference="J18",
    )
    b.next_ref("R")  # retired I2C SDA pull-up R42
    b.next_ref("R")  # retired I2C SCL pull-up R43

    # Full size SD, SPI mode.
    b.add(
        lib_id="Connector:SD_Card_Receptacle",
        value="Full-size SD, SPI",
        footprint_key="SD",
        nets={
            "1": "SD_CS_N", "2": "SD_MOSI", "3": "GND", "4": "+3V3_SD",
            "5": "SD_SCK", "6": "GND", "7": "SD_MISO", "8": "SD_DAT1",
            "9": "SD_DAT2", "10": "SD_CD", "11": None, "SH": "GND",
        },
        position=(155, 170),
        prefix="J",
        mpn="2041021-4",
        manufacturer="TE Connectivity",
    )
    for net, pos in [
        ("SD_CS_N", (100, 145)), ("SD_MOSI", (112, 145)), ("SD_MISO", (124, 145)),
        ("SD_CD", (136, 145)), ("SD_DAT1", (100, 158)), ("SD_DAT2", (112, 158)),
    ]:
        b.resistor("+3V3_SD", net, "10k", pos)
    for source, target, pos in [
        ("SD_SCK_MCU", "SD_SCK", (205, 145)),
        ("SD_MOSI_MCU", "SD_MOSI", (218, 145)),
        ("SD_MISO", "SD_MISO_MCU", (231, 145)),
        ("SD_CS_MCU", "SD_CS_N", (244, 145)),
    ]:
        b.resistor(source, target, "22R", pos)
    b.two_pin("FB", "Device:FerriteBead", "600R@100MHz", "R1206", "+3V3", "+3V3_SD", (75, 170), mpn="BLM18KG601SN1D", manufacturer="Murata")
    b.capacitor("+3V3_SD", "GND", "10uF 25V", (90, 170))
    b.capacitor("+3V3_SD", "GND", "100nF", (102, 170))
    b.next_ref("R")  # preserve the retired R54 card-detect resistor reference
    b.add(
        lib_id="Jumper:SolderJumper_2_Open",
        value="SD_CD_EN",
        footprint_key="SJ2",
        nets={"1": "SD_CD_MCU", "2": "SD_CD"},
        position=(300, 165),
        prefix="JP",
        reference="JP5",
        mpn="",
        manufacturer="PCB fabrication",
    )

    # ESP-01/ESP-01S socket and programming/test header.
    b.header(2, 4, {
        "1": "GND", "2": "+3V3_WIFI", "3": "WIFI_GPIO2", "4": "WIFI_GPIO0",
        "5": "WIFI_RX", "6": "WIFI_TX", "7": "WIFI_EN", "8": "WIFI_RST",
    }, (40, 205), "ESP-01/ESP-01S socket")
    b.next_ref("J")  # retired J21 external UART header
    for _ in range(4):
        b.next_ref("R")  # preserve the retired discrete ESP pull-up references
    b.add(
        lib_id="Switch:SW_Push",
        value="ESP_PROG",
        footprint_key="SWITCH",
        nets={"1": "WIFI_GPIO0", "2": "GND"},
        position=(65, 230),
        prefix="SW",
        mpn="PTS645SM43SMTR92LFS",
        manufacturer="C&K",
    )
    b.capacitor(
        "+3V3_WIFI",
        "GND",
        "22uF 50V",
        (105, 220),
        footprint_key="C1210",
    )
    b.capacitor("+3V3_WIFI", "GND", "100nF", (117, 220))
    b.next_ref("FB")  # retired local-LDO link FB3

def add_display(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "HSTX pair order from the verified PicoLVDS/reference firmware: "
        "D0=GP12(P)/13(N), D1=GP14(P)/15(N), D2=GP16(P)/17(N), "
        "CLK=GP18(P)/19(N). J22 uses the verified display pinout: odd pins "
        "on the left and even pins on the right. Only the first eight rows "
        "are used; pins 17-20 are no-connect.",
        15,
        15,
        190,
        38,
    )

    b.header(2, 10, {
        "1": "+3V3", "2": "+3V3", "3": "+3V3", "4": "GND",
        "5": "GND", "6": "GND", "7": "LVDS_D0_N", "8": "LVDS_D0_P",
        "9": "LVDS_D1_N", "10": "LVDS_D1_P",
        "11": "LVDS_D2_N", "12": "LVDS_D2_P",
        "13": "GND", "14": "GND",
        "15": "LVDS_CLK_N", "16": "LVDS_CLK_P",
        "17": None, "18": None, "19": None, "20": None,
    }, (50, 85), "LCD LVDS 2x10, 2.00 mm")

    # Passive LVDS. The isolated array pairs are ordered to follow J22 from
    # left to right when the networks are rotated 90 degrees on the PCB.
    passive = [
        ("HSTX_D1_N", "LVDS_D1_N"), ("HSTX_D1_P", "LVDS_D1_P"),
        ("HSTX_D0_P", "LVDS_D0_P"), ("HSTX_D0_N", "LVDS_D0_N"),
        ("HSTX_CLK_N", "LVDS_CLK_N"), ("HSTX_CLK_P", "LVDS_CLK_P"),
        ("HSTX_D2_P", "LVDS_D2_P"), ("HSTX_D2_N", "LVDS_D2_N"),
    ]
    for pack in range(2):
        b.resistor_pack4(
            "330R",
            "R_Array_4x1206",
            passive[pack * 4:(pack + 1) * 4],
            (90 + pack * 65, 85),
            dnp=True,
        )

    b.add(
        lib_id="LeanCam:DS90LV047A",
        value="DS90LV047A",
        footprint_key="SOIC16",
        nets={
            "1": "+3V3",
            "2": "HSTX_CLK_P",
            "3": "HSTX_D2_P",
            "4": "+3V3",
            "5": "GND",
            "6": "HSTX_D1_P",
            "7": "HSTX_D0_P",
            "8": "GND",
            "9": "LVDS_D0_N",
            "10": "LVDS_D0_P",
            "11": "LVDS_D1_P",
            "12": "LVDS_D1_N",
            "13": "LVDS_D2_N",
            "14": "LVDS_D2_P",
            "15": "LVDS_CLK_P",
            "16": "LVDS_CLK_N",
        },
        position=(125, 45),
        prefix="U",
        reference="U41",
        mpn="DS90LV047ATMTC/NOPB",
        manufacturer="Texas Instruments",
    )
    b.capacitor(
        "+3V3",
        "GND",
        "100nF",
        (145, 45),
        reference="C106",
    )

    # Preserve reference numbering after removal of the HDMI branch.
    b.next_ref("J")   # retired J23 HDMI connector
    b.next_ref("RN")  # retired RN28 HDMI link array
    b.next_ref("RN")  # retired RN29 HDMI link array
    b.next_ref("U")   # retired U42 HDMI ESD array
    b.next_ref("U")   # retired U43 HDMI ESD array
    b.next_ref("U")   # retired U44 HDMI ESD/DDC array
    b.next_ref("R")   # retired R59 HDMI DDC pull-up
    b.next_ref("R")   # retired R60 HDMI DDC pull-up
    b.next_ref("F")   # retired F3 HDMI fuse
    b.next_ref("C")   # retired C107 HDMI bulk capacitor
    b.next_ref("C")   # retired C108 HDMI bypass capacitor


def add_analog(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "Three 0-10 V ADC inputs use a 100 k over 33 k divider and one 100 nF ADC "
        "capacitor per channel. Place each divider/filter group at J24, not at the MCU. "
        "Four ground-referenced 0-10 V outputs use individual 0805 resistors for "
        "the approved two-stage 10 k / 1 uF and 10 k / 100 nF PWM filters. A "
        "TLV2374 is powered from a local 12 V rail and uses 22 k / 10 k feedback "
        "for a nominal gain of 3.2, leaving calibration headroom for exactly 10 V.",
        15,
        15,
        300,
        45,
    )

    analog_in_nets = {
        "1": "AI0",
        "2": "GND",
        "3": "AI1",
        "4": "GND",
        "5": "AI2",
    }
    b.terminal(5, analog_in_nets, (38, 75), "AI0/GND/AI1/GND/AI2")

    for bit in range(3):
        x = 100 + bit * 50
        b.resistor(f"AI{bit}", f"AI{bit}_ADC", "100k", (x, 70))
        b.next_ref("R")  # retired second upper resistor
        b.resistor(f"AI{bit}_ADC", "GND", "33k", (x, 100))
        b.capacitor(
            f"AI{bit}_ADC",
            "GND",
            "100nF",
            (x, 130),
            reference=f"C{73 + bit}",
        )

    b.terminal(
        5,
        {
            "1": "GND",
            "2": "AOUT0",
            "3": "AOUT1",
            "4": "AOUT2",
            "5": "AOUT3",
        },
        (38, 210),
        "0-10 V outputs 0-3; pin 1 = common GND",
    )

    for bit in range(4):
        x = 90 + bit * 25
        b.resistor(
            f"AOUT{bit}_PWM",
            f"AOUT{bit}_F1",
            "10k",
            (x, 200),
            footprint_key="R0805",
            reference=f"R{92 + bit}",
        )
        b.resistor(
            f"AOUT{bit}_F1",
            f"AOUT{bit}_F2",
            "10k",
            (x, 210),
            footprint_key="R0805",
            reference=f"R{96 + bit}",
        )
        b.resistor(
            f"AOUT{bit}_FB",
            f"AOUT{bit}",
            "22k",
            (x, 230),
            footprint_key="R0805",
            reference=f"R{100 + bit}",
        )
        b.resistor(
            f"AOUT{bit}_FB",
            "GND",
            "10k",
            (x, 240),
            footprint_key="R0805",
            reference=f"R{104 + bit}",
        )

    for bit in range(4):
        x = 255 + bit * 35
        b.capacitor(
            f"AOUT{bit}_F1",
            "GND",
            "1uF",
            (x, 205),
            reference=f"C{92 + bit * 2}",
        )
        b.capacitor(
            f"AOUT{bit}_F2",
            "GND",
            "100nF",
            (x, 225),
            reference=f"C{93 + bit * 2}",
        )

    b.add(
        lib_id="LeanCam:TLV2374",
        value="TLV2374IDR",
        footprint_key="SOIC14",
        nets={
            "1": "AOUT0",
            "2": "AOUT0_FB",
            "3": "AOUT0_F2",
            "4": "+12V_AO",
            "5": "AOUT1_F2",
            "6": "AOUT1_FB",
            "7": "AOUT1",
            "8": "AOUT2",
            "9": "AOUT2_FB",
            "10": "AOUT2_F2",
            "11": "GND",
            "12": "AOUT3_F2",
            "13": "AOUT3_FB",
            "14": "AOUT3",
        },
        position=(430, 210),
        prefix="U",
        reference="U38",
        mpn="TLV2374IDR",
        manufacturer="Texas Instruments",
    )

    b.add(
        lib_id="LeanCam:L78L12",
        value="L78L12ACUTR",
        footprint_key="SOT89",
        nets={"1": "+12V_AO", "2": "GND", "3": "VIN_PROT"},
        position=(350, 295),
        prefix="U",
        reference="U37",
        mpn="L78L12ACUTR",
        manufacturer="Texas Instruments",
    )
    b.capacitor(
        "VIN_PROT",
        "GND",
        "22uF 50V",
        (315, 295),
        footprint_key="C1210",
        reference="C100",
    )
    b.capacitor(
        "+12V_AO",
        "GND",
        "22uF 50V",
        (385, 295),
        footprint_key="C1210",
        reference="C101",
    )
    b.capacitor(
        "+12V_AO",
        "GND",
        "100nF",
        (465, 210),
        reference="C102",
    )


def add_backlight_power(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "U3 is a second LMR36510 buck set to 12 V for the LCD backlight/CCFL "
        "inverter supply. It uses 47 uH, 100 k / 10 k feedback, 3x22 uF/25 V "
        "output and 22 uF/50 V + 100 nF/100 V local input. The existing U37 "
        "+12V_AO supply remains separate.",
        250,
        250,
        210,
        42,
    )
    b.add(
        lib_id="Regulator_Switching:LMR36510ADDA",
        value="LMR36510ADDAR",
        footprint_key="SOIC8_POWERPAD",
        nets={
            "1": "GND",
            "2": "VIN_BL_PROT",
            "3": "VIN_BL_PROT",
            "4": None,
            "5": "FB12",
            "6": "VCC12",
            "7": "BUCK12_BST",
            "8": "BUCK12_SW",
            "9": "GND",
        },
        position=(250, 310),
        prefix="U",
        reference="U3",
        mpn="LMR36510ADDAR",
        manufacturer="Texas Instruments",
    )
    b.two_pin(
        "L",
        "Device:L",
        "47uH 1.5A",
        "L_SRN6045",
        "BUCK12_SW",
        "+12V_BL",
        (280, 310),
        mpn="SRN6045TA-470M",
        manufacturer="Bourns",
        reference="L2",
    )
    b.capacitor(
        "VIN_BL_PROT",
        "GND",
        "22uF 50V",
        (232, 305),
        footprint_key="C1210",
        reference="C107",
    )
    b.capacitor(
        "VIN_BL_PROT",
        "GND",
        "100nF 100V",
        (232, 318),
        footprint_key="C1206_100V",
        reference="C108",
    )
    for index, x in enumerate((300, 315, 330)):
        b.capacitor(
            "+12V_BL",
            "GND",
            "22uF 50V",
            (x, 310),
            footprint_key="C1210",
            reference=f"C{109 + index}",
        )
    b.capacitor(
        "+12V_BL",
        "GND",
        "100nF",
        (345, 310),
        footprint_key="C0805",
        reference="C112",
    )
    b.capacitor(
        "BUCK12_BST",
        "BUCK12_SW",
        "100nF",
        (257, 325),
        footprint_key="C0805",
        reference="C113",
    )
    b.capacitor(
        "VCC12",
        "GND",
        "1uF",
        (272, 325),
        footprint_key="C0805",
        reference="C114",
    )
    b.resistor(
        "+12V_BL",
        "FB12",
        "100k",
        (286, 325),
        reference="R126",
    )
    b.resistor(
        "FB12",
        "GND",
        "10k",
        (299, 325),
        reference="R127",
    )
    b.resistor(
        "FB12",
        "GND",
        "100k",
        (312, 325),
        reference="R128",
    )
    b.resistor(
        "BL_PWM_MCU",
        "BL_PWM",
        "100R",
        (302, 338),
        footprint_key="R0805",
        reference="R131",
    )
    b.resistor(
        "BL_PWM_MCU",
        "BL_SW_GATE",
        "100R",
        (315, 325),
        footprint_key="R0805",
        reference="R129",
    )
    b.resistor(
        "BL_SW_GATE",
        "GND",
        "100k",
        (328, 325),
        footprint_key="R0805",
        reference="R130",
    )
    b.add(
        lib_id="Transistor_FET:Q_NMOS_GSD",
        value="BSS138",
        footprint_key="SOT23",
        nets={"1": "BL_SW_GATE", "2": "GND", "3": "BL_LED_N"},
        position=(342, 325),
        prefix="Q",
        reference="Q8",
        mpn="BSS138",
        manufacturer="onsemi",
    )


def add_backlight(builder: SheetBuilder) -> None:
    b = builder
    b.note(
        "J2 carries the nominal 11 V backlight/CCFL supply on the legacy "
        "+12V_BL net, a 3.3 V PWM "
        "control signal from GPIO1, and ground. GPIO1 also drives the optional "
        "Q8 low-side return through a 100 ohm gate resistor. High-current "
        "switching remains on the external inverter or backlight driver.",
        15,
        240,
        180,
        30,
    )
    b.terminal(
        4,
        {"1": "+12V_BL", "2": "GND", "3": "BL_PWM", "4": "BL_LED_N"},
        (40, 260),
        "Backlight: +12V, GND, PWM, switched low-side",
        reference="J2",
    )
    # Preserve the reference sequence of the removed backlight circuit so the
    # remaining staged PCB references stay stable.
    b.next_ref("Q")  # retired Q2 high-side switch
    b.next_ref("R")  # retired R6 gate pull-up
    b.next_ref("D")  # retired D6 gate clamp
    b.next_ref("R")  # retired R7 base resistor
    b.next_ref("Q")  # retired Q3 enable transistor
    b.next_ref("C")  # retired C18 backlight bulk capacitor
    b.next_ref("JP") # retired JP1 supply selector
    b.next_ref("U")  # retired U5
    b.next_ref("C")  # retired C19
    b.next_ref("C")  # retired C20
    b.next_ref("J")  # retired J3


def main() -> None:
    HARDWARE.mkdir(parents=True, exist_ok=True)
    sheets = {
        "power": SheetBuilder("Power and supervision", "power.kicad_sch", "A2"),
        "mcu": SheetBuilder("MCU, shift chains and safety", "mcu_io.kicad_sch", "A1"),
        "inputs": SheetBuilder("16 PLC inputs and expansion", "field_inputs.kicad_sch", "A1"),
        "outputs": SheetBuilder("24 PLC outputs", "field_outputs.kicad_sch", "A1"),
        "encoders": SheetBuilder("Encoders", "encoders.kicad_sch", "A2"),
        "storage": SheetBuilder("Storage, Wi-Fi and UI", "storage_wifi_ui.kicad_sch", "A1"),
        "display": SheetBuilder("Display", "display.kicad_sch", "A1"),
        "analog": SheetBuilder("Analog I/O", "analog_io.kicad_sch", "A2"),
    }
    add_power(sheets["power"])
    add_backlight(sheets["power"])
    add_mcu(sheets["mcu"])
    add_field_inputs(sheets["inputs"])
    add_field_outputs(sheets["outputs"])
    add_encoders(sheets["encoders"])
    add_keyboard_storage_wifi(sheets["storage"])
    add_display(sheets["display"])
    add_analog(sheets["analog"])

    # U33 was the retired LCD-logic enable gate. Reserve the reference after
    # all automatically numbered MCU/peripheral gates have been created.
    sheets["power"].next_ref("U")

    # Explicit end-of-design references keep the existing capacitor references stable
    # staged PCB. One local 100 nF part is assigned to every supply-bearing IC
    # that did not already have a dedicated decoupling capacitor.
    local_decoupling = (
        ("power", "+5V", (285, 240), "C76"),       # U2 input
    )
    for sheet_name, rail, position, reference in local_decoupling:
        sheets[sheet_name].capacitor(
            rail,
            "GND",
            "100nF",
            position,
            reference=reference,
            dnp=reference == "C78",
        )
    sheets["power"].capacitor(
        "BUCK5_BST",
        "BUCK5_SW",
        "100nF",
        (345, 240),
        footprint_key="C0805",
        reference="C86",
    )
    sheets["power"].capacitor(
        "VCC5",
        "GND",
        "1uF",
        (369, 252),
        footprint_key="C0805",
        reference="C91",
    )
    sheets["storage"].add(
        lib_id="Regulator_Linear:AMS1117-3.3",
        value="AMS1117-3.3",
        footprint_key="SOT223",
        nets={"1": "GND", "2": "+3V3_WIFI", "3": "+5V"},
        position=(330, 260),
        prefix="U",
        reference="U34",
        mpn="AMS1117-3.3",
        manufacturer="Advanced Monolithic Systems",
    )
    sheets["storage"].capacitor(
        "+5V",
        "GND",
        "22uF 50V",
        (342, 260),
        footprint_key="C1210",
        reference="C88",
    )
    sheets["storage"].capacitor(
        "+5V",
        "GND",
        "100nF",
        (354, 260),
        reference="C89",
    )
    sheets["power"].capacitor(
        "+3V3",
        "GND",
        "22uF 50V",
        (417, 240),
        footprint_key="C1210",
        reference="C90",
    )
    for net_a, net_b, value, position, reference in (
        ("+5V", "FB5_TOP", "33k", (400, 240), "R70"),
        ("FB5_TOP", "FB5", "100k", (412, 240), "R71"),
        ("FB5", "GND", "33k", (424, 240), "R72"),
        ("PWR_GOOD_N", "+3V3", "100k", (436, 240), "R73"),
    ):
        sheets["power"].two_pin(
            "R",
            "Device:R",
            value,
            "R1206",
            net_a,
            net_b,
            position,
            mpn=f"RC1206FR-07 1% {value}",
            manufacturer="Yageo",
            reference=reference,
        )

    add_input_pullups(sheets["inputs"], sheets["storage"])
    add_encoder_z_divider(sheets["encoders"])

    expansion_4_7 = {"1": "GND", "2": "+3V3"}
    for signal in range(4, 8):
        expansion_4_7[str(signal - 1)] = f"EXP_IN{signal}"
    sheets["inputs"].header(
        1,
        6,
        expansion_4_7,
        (70, 175),
        "Expansion inputs 4-7; 1=GND, 2=3.3 V",
        reference="J27",
    )
    motion_connectors = (
        ("J28", "AX2: EN, STEP, DIR, GND", {"1": "MOTION6", "2": "MOTION7", "3": "MOTION8", "4": "GND"}, (360, 175)),
        ("J29", "AX3: EN, STEP, DIR, GND", {"1": "MOTION9", "2": "MOTION10", "3": "MOTION11", "4": "GND"}, (390, 175)),
        ("J30", "AX4: EN, STEP, DIR, GND", {"1": "MOTION12", "2": "MOTION13", "3": "MOTION14", "4": "GND"}, (330, 210)),
    )
    for reference, value, nets, position in motion_connectors:
        sheets["outputs"].terminal(
            4,
            nets,
            position,
            value,
            reference=reference,
        )
    sheets["outputs"].terminal(
        2,
        {"1": "AUX_OUT", "2": "GND"},
        (360, 210),
        "AUX open-drain output and GND",
        reference="J31",
    )
    sheets["outputs"].resistor(
        "AUX_GATE",
        "GND",
        "100k",
        (345, 240),
        footprint_key="R0805",
        reference="R113",
    )
    sheets["outputs"].add(
        lib_id="Transistor_FET:Q_NMOS_GSD",
        value="BSS138",
        footprint_key="SOT23",
        nets={"1": "AUX_GATE", "2": "GND", "3": "AUX_OUT"},
        position=(360, 240),
        prefix="Q",
        reference="Q5",
        mpn="BSS138",
        manufacturer="onsemi",
    )
    for index, bit in enumerate((14, 15)):
        gate_net = f"DO{bit}_GATE"
        sheets["outputs"].resistor(
            f"OUT{bit + 16}",
            gate_net,
            "100R",
            (330, 255 + index * 15),
            footprint_key="R0805",
            reference=f"R{114 + index * 2}",
        )
        sheets["outputs"].resistor(
            gate_net,
            "GND",
            "100k",
            (345, 255 + index * 15),
            footprint_key="R0805",
            reference=f"R{115 + index * 2}",
        )
        sheets["outputs"].add(
            lib_id="Transistor_FET:Q_NMOS_GSD",
            value="BSS138",
            footprint_key="SOT23",
            nets={"1": gate_net, "2": "GND", "3": f"DO{bit}"},
            position=(360, 255 + index * 15),
            prefix="Q",
            reference=f"Q{6 + index}",
            mpn="BSS138",
            manufacturer="onsemi",
        )

    # Add explicitly numbered field-supply parts only after all automatically
    # numbered references have been allocated, so existing board references do
    # not move.
    add_isolated_field_supply(sheets["inputs"])
    sheets["outputs"].terminal(
        8,
        {
            "1": "DO8", "2": "DO9", "3": "DO10", "4": "DO11",
            "5": "DO12", "6": "DO13", "7": "DO14", "8": "DO15",
        },
        (375, 210),
        "General outputs 8-15; DO_COM and GND are shared through J12",
        reference="J32",
    )
    sheets["outputs"].terminal(
        2,
        {"1": "DO_COM", "2": "GND"},
        (390, 210),
        "General outputs field +V and GND",
        reference="J33",
    )
    sheets["inputs"].terminal(
        8,
        {"1": "FIELD_IN13", "2": "FIELD_COM0",
         "3": "FIELD_IN14", "4": "FIELD_COM0",
         "5": "FIELD_IN15", "6": "FIELD_COM0",
         "7": "FIELD_IN16", "8": "FIELD_COM0"},
        (420, 125),
        "PLC positions 5-8 of J7 bank; software-mapped isolated inputs",
        reference="J34",
    )
    sheets["inputs"].terminal(
        8,
        {"1": "FIELD_IN5", "2": "FIELD_COM1",
         "3": "FIELD_IN6", "4": "FIELD_COM1",
         "5": "FIELD_IN7", "6": "FIELD_COM1",
         "7": "FIELD_IN8", "8": "FIELD_COM1"},
        (420, 173),
        "PLC positions 5-8 of J8 bank; software-mapped isolated inputs",
        reference="J35",
    )
    for bit in range(8, 16):
        led_reference = f"D{57 + bit - 8}"
        resistor_reference = f"R{118 + bit - 8}"
        x = 250 + ((bit - 8) % 4) * 18
        y = 205 + ((bit - 8) // 4) * 28
        sheets["outputs"].led(
            f"DO{bit}",
            f"DO_LED{bit}_A",
            (x, y),
            f"DO{bit}",
            reference=led_reference,
        )
        sheets["outputs"].resistor(
            "DO_COM",
            f"DO_LED{bit}_A",
            "2.2k",
            (x + 8, y),
            reference=resistor_reference,
        )
    sheets["outputs"].resistor_pack4(
        "10k",
        "R_Array_4x0603",
        [
            ("OUT26", "GND"),
            ("OUT24", "GND"),
            ("OUT25", "GND"),
            ("OUT23", "GND"),
        ],
        (420, 235),
        reference="RN30",
    )
    sheets["outputs"].resistor_pack4(
        "10k",
        "R_Array_4x0603",
        [
            ("OUT29", "GND"),
            ("OUT28", "GND"),
            ("OUT27", "GND"),
            (None, None),
        ],
        (440, 235),
        reference="RN31",
    )

    sheets["storage"].add(
        lib_id="Connector:Micro_SD_Card_Det2",
        value="MicroSD alternative, SPI",
        footprint_key="MICROSD",
        nets={
            "1": "SD_DAT2",
            "2": "SD_CS_N",
            "3": "SD_MOSI",
            "4": "+3V3_SD",
            "5": "SD_SCK",
            "6": "GND",
            "7": "SD_MISO",
            "8": "SD_DAT1",
            "9": "GND",
            "10": "SD_CD",
            "SH": "GND",
        },
        position=(380, 165),
        prefix="J",
        reference="J36",
        dnp=True,
        mpn="104031-0811",
        manufacturer="Molex",
    )

    add_backlight_power(sheets["power"])

    for sheet in sheets.values():
        sheet.save()
    make_root()

    # Deterministic reference check across the hierarchy.
    duplicates = sorted(ref for ref, count in defaultdict(
        int, {ref: sum(part.reference == ref for part in PARTS) for ref in {part.reference for part in PARTS}}
    ).items() if count > 1)
    if duplicates:
        raise RuntimeError(f"Duplicate references: {duplicates}")
    print(f"Generated {len(PARTS)} parts across {len(sheets)} hierarchical sheets")


if __name__ == "__main__":
    main()
