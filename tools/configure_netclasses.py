"""Install the LeanCam PCB netclass rules into the KiCad project."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "motherboard.kicad_pro"
RULES = ROOT / "hardware" / "motherboard.kicad_dru"
MIN_TRACK_WIDTH_MM = 0.12

RULE_TEXT = """(version 1)

(rule "LVDS connector geometry"
    (constraint track_width (min 0.12mm) (max 0.12mm) (opt 0.12mm))
    (constraint diff_pair_gap (min 0.12mm) (opt 0.12mm))
    (condition "A.NetName == 'LVDS_*'")
)

(rule "J22 LVDS connector clearance"
    (constraint clearance (min 0.12mm))
    (condition "(A.NetName == 'LVDS_*' && B.memberOfFootprint('J22')) || (B.NetName == 'LVDS_*' && A.memberOfFootprint('J22'))")
)
"""

TRANSPARENT = "rgba(0, 0, 0, 0.000)"


def make_class(
    name: str,
    track_width: float,
    clearance: float,
    via_diameter: float,
    via_drill: float,
    *,
    diff_pair_width: float = 0.2,
    diff_pair_gap: float = 0.2,
    priority: int = 0,
) -> dict:
    return {
        "bus_width": 12,
        "clearance": clearance,
        "diff_pair_gap": diff_pair_gap,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": diff_pair_width,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": name,
        "pcb_color": TRANSPARENT,
        "priority": priority,
        "schematic_color": TRANSPARENT,
        "track_width": track_width,
        "tuning_profile": "",
        "via_diameter": via_diameter,
        "via_drill": via_drill,
        "wire_width": 6,
    }


CLASSES = (
    make_class("Default", 0.2, 0.2, 0.6, 0.3, priority=2147483647),
    make_class("Power", 0.8, 0.3, 0.8, 0.4),
    make_class("FieldPower", 0.5, 0.5, 0.6, 0.3),
    make_class("AnalogPower", 0.3, 0.2, 0.6, 0.3),
    make_class("EncoderPower", 0.3, 0.2, 0.6, 0.3),
    make_class("BacklightControl", 0.2, 0.2, 0.6, 0.3),
    make_class("Ground", 0.5, 0.3, 0.6, 0.3),
    make_class("DigitalDiffPair", 0.2, 0.2, 0.6, 0.3),
    make_class(
        "LVDSConnector",
        0.12,
        0.12,
        0.6,
        0.3,
        diff_pair_width=0.12,
        diff_pair_gap=0.12,
    ),
    make_class("Analog", 0.25, 0.25, 0.6, 0.3),
)

PATTERNS = (
    # Field and isolated-domain power must win over the generic supply rules.
    ("FieldPower", "FIELD_COM*"),
    ("FieldPower", "FIELD_SAFETY_COM"),
    ("FieldPower", "ISO_GND"),
    ("FieldPower", "+5V_ISO_IN"),
    ("FieldPower", "+12V_FIELD"),
    ("FieldPower", "DO_COM"),
    ("AnalogPower", "+12V_AO"),
    ("AnalogPower", "+12V_RAW"),
    ("EncoderPower", "+5V_ENC"),
    ("BacklightControl", "BL_PWM*"),
    ("BacklightControl", "BL_SW_GATE"),
    ("Ground", "GND"),
    ("Power", "VIN_*"),
    ("Power", "+5V"),
    ("Power", "+5V_*"),
    ("Power", "+3V3*"),
    ("Power", "+12V_*"),
    ("Power", "BL_LED_N"),
    ("DigitalDiffPair", "HSTX_*"),
    ("LVDSConnector", "LVDS_*"),
    ("Analog", "AI*"),
    ("Analog", "AOUT*"),
)


def configure_netclasses(project: Path = PROJECT) -> dict:
    data = json.loads(project.read_text(encoding="utf-8"))
    data["board"]["design_settings"]["rules"]["min_track_width"] = MIN_TRACK_WIDTH_MM
    settings = data["net_settings"]
    defaults = settings["classes"][0]
    classes = []
    for class_data in CLASSES:
        merged = deepcopy(defaults)
        merged.update(class_data)
        classes.append(merged)
    settings["classes"] = classes
    settings["netclass_assignments"] = None
    settings["netclass_patterns"] = [
        {"netclass": netclass, "pattern": pattern}
        for netclass, pattern in PATTERNS
    ]
    project.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    RULES.write_text(RULE_TEXT, encoding="utf-8")
    return {
        "project": str(project),
        "rules": str(RULES),
        "classes": [item["name"] for item in classes],
        "patterns": len(PATTERNS),
    }


if __name__ == "__main__":
    print(json.dumps(configure_netclasses(), indent=2))
