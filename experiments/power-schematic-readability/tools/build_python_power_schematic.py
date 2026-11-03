"""Method B: re-layout the current power sheet with functional blocks.

The source schematic remains authoritative. This builder reads the extracted
pin contract, places every current power-sheet symbol in a conventional
power-flow order, wires short local nets, and falls back to named labels for
cross-block and high-fanout rails.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_python_hierarchy import Block, Sheet, build_sheet


ROOT = Path(__file__).resolve().parents[3]
METHOD_B = ROOT / "experiments" / "power-schematic-readability" / "method-b"

POWER_SHEET = Sheet(
    stem="power",
    source="power.kicad_sch",
    title="Power distribution, protection and local regulation",
    paper="A1",
    blocks=(
        Block(
            "24 V INPUT, FUSE, CLAMP AND REVERSE-POLARITY PROTECTION",
            ("J1", "F1", "D1", "D2", "C2", "C3", "C4", "C5"),
            columns=8,
        ),
        Block(
            "5 V BUCK CONVERTER, FEEDBACK AND OUTPUT CAPACITORS",
            (
                "U1", "L1", "C86", "C91",
                "C6", "C7", "C10", "C11", "C76",
                "R70", "R71", "R72", "R73",
            ),
            columns=8,
        ),
        Block(
            "3V3 POINT-OF-LOAD REGULATOR AND ANALOG FILTER",
            ("U2", "C13", "C90", "FB1", "C15"),
            columns=5,
        ),
        Block(
            "5 V AND 3V3 STATUS INDICATORS",
            ("R4", "D4", "R5", "D5"),
            columns=4,
        ),
        Block(
            "ISOLATED PLC-24 V TO 12 V BACKLIGHT CONVERTER",
            (
                "J2", "D3", "U3", "L2",
                "C107", "C108", "C109", "C110", "C111", "C112",
                "C113", "C114", "R126", "R127", "R128",
                "FLG9", "FLG10",
            ),
            columns=9,
        ),
        Block(
            "OFF-SHEET POWER AND GROUND REFERENCES",
            tuple(f"FLG{index}" for index in range(1, 9)),
            columns=8,
        ),
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    result = build_sheet(
        POWER_SHEET,
        force=args.force,
        output_dir=METHOD_B,
        output_name="lean-power-b.kicad_sch",
        company="LeanCam / uCNC schematic readability experiment",
        comment="Method B: authoritative KiCad symbols grouped by power flow",
        labels_global=False,
    )
    report_path = METHOD_B / "generation-report.json"
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
