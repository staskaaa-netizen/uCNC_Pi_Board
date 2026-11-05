"""Build PCB-fabrication and SMT-assembly archives from the current board."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
MANUFACTURING = ROOT / "manufacturing"
PACKAGES = MANUFACTURING / "packages"
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
DEFAULT_KICAD_CLI = (
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe"
)

FAB_LAYERS = (
    "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
)
SMT_LAYERS = (
    "F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,"
    "F.Mask,B.Mask,Edge.Cuts"
)


def run(command: list[str]) -> None:
    result = subprocess.run(command, check=False, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.returncode:
        raise SystemExit(result.stderr.strip() or f"command failed: {command}")
    if result.stderr.strip():
        print(result.stderr.strip())


def reset_directory(path: Path) -> None:
    resolved = path.resolve()
    if PACKAGES.resolve() not in resolved.parents:
        raise RuntimeError(f"Unsafe package output path: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def export_fabrication(kicad_cli: Path, output: Path) -> None:
    gerbers = output / "gerbers"
    drill = output / "drill"
    gerbers.mkdir()
    drill.mkdir()
    run(
        [
            str(kicad_cli),
            "pcb",
            "export",
            "gerbers",
            "--output",
            str(gerbers),
            "--layers",
            FAB_LAYERS,
            str(BOARD),
        ]
    )
    run(
        [
            str(kicad_cli),
            "pcb",
            "export",
            "drill",
            "--output",
            str(drill),
            "--format",
            "excellon",
            "--excellon-units",
            "mm",
            "--excellon-separate-th",
            "--generate-map",
            "--map-format",
            "pdf",
            "--generate-report",
            "--report-path",
            str(drill / "drill-report.rpt"),
            str(BOARD),
        ]
    )


def export_smt_layers(kicad_cli: Path, output: Path) -> Path:
    gerbers = output / "gerbers"
    drill = output / "drill"
    gerbers.mkdir()
    drill.mkdir()
    run(
        [
            str(kicad_cli),
            "pcb",
            "export",
            "gerbers",
            "--output",
            str(gerbers),
            "--layers",
            SMT_LAYERS,
            str(BOARD),
        ]
    )
    run(
        [
            str(kicad_cli),
            "pcb",
            "export",
            "drill",
            "--output",
            str(drill),
            "--format",
            "excellon",
            "--excellon-units",
            "mm",
            "--excellon-separate-th",
            "--generate-map",
            "--map-format",
            "pdf",
            "--generate-report",
            "--report-path",
            str(drill / "drill-report.rpt"),
            str(BOARD),
        ]
    )
    raw_position = output / "kicad-position-raw.csv"
    run(
        [
            str(kicad_cli),
            "pcb",
            "export",
            "pos",
            "--output",
            str(raw_position),
            "--side",
            "front",
            "--format",
            "csv",
            "--units",
            "mm",
            "--smd-only",
            "--exclude-dnp",
            str(BOARD),
        ]
    )
    return raw_position


def write_assembly_placement(output: Path, raw_position: Path) -> dict:
    bom_rows = list(
        csv.DictReader(
            (MANUFACTURING / "bom-smt-refs.csv").open(
                newline="", encoding="utf-8"
            )
        )
    )
    bom_refs = {row["Reference"] for row in bom_rows}
    raw_rows = {
        row["Ref"]: row
        for row in csv.DictReader(
            raw_position.open(newline="", encoding="utf-8")
        )
    }
    missing = sorted(bom_refs - set(raw_rows), key=natural_key)
    extra = sorted(set(raw_rows) - bom_refs, key=natural_key)
    if missing:
        raise RuntimeError(f"SMT positions missing for: {missing}")

    board = pcbnew.LoadBoard(str(BOARD))
    bbox = board.GetBoardEdgesBoundingBox()
    left = pcbnew.ToMM(bbox.GetLeft())
    bottom = pcbnew.ToMM(bbox.GetBottom())
    placements = []
    for reference in sorted(bom_refs, key=natural_key):
        row = raw_rows[reference]
        placements.append(
            {
                "Designator": reference,
                "Val": row["Val"],
                "Package": row["Package"],
                "PosX": f"{float(row['PosX']) - left:.3f}",
                "PosY": f"{bottom + float(row['PosY']):.3f}",
                "Rot": row["Rot"],
                "Side": row["Side"].title(),
            }
        )

    cpl_path = output / "cpl.csv"
    with cpl_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Designator",
                "Val",
                "Package",
                "PosX",
                "PosY",
                "Rot",
                "Side",
            ],
        )
        writer.writeheader()
        writer.writerows(placements)
    raw_position.unlink()
    return {
        "placements": len(placements),
        "excluded_from_raw_position": extra,
        "origin": "board lower-left",
        "units": "mm",
    }


def write_jlcpcb_files(
    cpl_path: Path,
    bom_path: Path,
    output_dir: Path,
) -> dict:
    cpl_rows = list(
        csv.DictReader(cpl_path.open(newline="", encoding="utf-8"))
    )
    jlc_cpl_rows = [
        {
            "Designator": row["Designator"],
            "Mid X": row["PosX"],
            "Mid Y": row["PosY"],
            "Layer": row["Side"],
            "Rotation": format_rotation(row["Rot"]),
        }
        for row in cpl_rows
    ]

    bom_rows = list(
        csv.DictReader(bom_path.open(newline="", encoding="utf-8"))
    )
    jlc_bom_rows = []
    bom_references = []
    for row in bom_rows:
        references = [
            reference
            for reference in re.split(r"[\s,]+", row["References"].strip())
            if reference
        ]
        bom_references.extend(references)
        footprint = row["Footprint"].split(":", 1)[-1]
        jlc_bom_rows.append(
            {
                "Comment": row["Design Values"],
                "Designator": ",".join(references),
                "Footprint": footprint,
                "JLCPCB Part #": "",
            }
        )

    cpl_references = [row["Designator"] for row in cpl_rows]
    if len(bom_references) != len(set(bom_references)):
        raise RuntimeError("Duplicate designators in SMT BOM")
    if len(cpl_references) != len(set(cpl_references)):
        raise RuntimeError("Duplicate designators in CPL")
    if set(bom_references) != set(cpl_references):
        missing_from_bom = sorted(set(cpl_references) - set(bom_references))
        missing_from_cpl = sorted(set(bom_references) - set(cpl_references))
        raise RuntimeError(
            "SMT BOM/CPL reference mismatch: "
            f"missing from BOM={missing_from_bom}, "
            f"missing from CPL={missing_from_cpl}"
        )

    jlc_cpl_path = output_dir / "cpl-jlcpcb.csv"
    with jlc_cpl_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation"],
        )
        writer.writeheader()
        writer.writerows(jlc_cpl_rows)

    jlc_bom_path = output_dir / "bom-jlcpcb.csv"
    with jlc_bom_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "Comment",
                "Designator",
                "Footprint",
                "JLCPCB Part #",
            ],
        )
        writer.writeheader()
        writer.writerows(jlc_bom_rows)

    report = {
        "cpl": str(cpl_path),
        "bom": str(bom_path),
        "jlc_cpl": str(jlc_cpl_path),
        "jlc_bom": str(jlc_bom_path),
        "smt_references": len(cpl_references),
        "bom_groups": len(jlc_bom_rows),
        "references_match": True,
        "jlcpartnumber_blank_groups": len(jlc_bom_rows),
        "units": "mm",
        "coordinate_origin": "board lower-left",
    }
    (output_dir / "jlcpcb-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def format_rotation(value: str) -> str:
    rotation = float(value) % 360.0
    if rotation.is_integer():
        return str(int(rotation))
    return f"{rotation:.6f}"


def natural_key(value: str) -> list[str | int]:
    import re

    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", value)
    ]


def write_readme(output: Path, title: str, text: str) -> None:
    (output / "README.txt").write_text(f"{title}\n\n{text}\n", encoding="utf-8")


def create_zip(directory: Path, archive: Path) -> None:
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                bundle.write(path, path.name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kicad-cli", type=Path, default=Path(DEFAULT_KICAD_CLI))
    args = parser.parse_args()

    PACKAGES.mkdir(parents=True, exist_ok=True)
    fabrication = PACKAGES / "uCNC_Pi_Board_PCB_Fabrication"
    assembly = PACKAGES / "uCNC_Pi_Board_SMT_Assembly"
    reset_directory(fabrication)
    reset_directory(assembly)

    export_fabrication(args.kicad_cli, fabrication)
    export_fabrication_readme = """\
PCB fabrication only.

- Board: uCNC Pi Board, LeanCam NCC RP2350B
- Outline: 160 x 120 mm
- Copper layers: 2
- Gerbers: copper, solder mask, silkscreen and board edge
- Drill: PTH and NPTH, Excellon, millimetres
- No SMT BOM or placement file is included in this archive.
"""
    write_readme(
        fabrication,
        "uCNC Pi Board - PCB Fabrication Package",
        export_fabrication_readme,
    )

    raw_position = export_smt_layers(args.kicad_cli, assembly)
    placement_report = write_assembly_placement(assembly, raw_position)
    shutil.copy2(assembly / "cpl.csv", MANUFACTURING / "cpl.csv")
    jlc_report = write_jlcpcb_files(
        MANUFACTURING / "cpl.csv",
        MANUFACTURING / "bom-smt.csv",
        MANUFACTURING,
    )
    for source, destination in (
        (MANUFACTURING / "bom-smt.csv", assembly / "bom-smt.csv"),
        (MANUFACTURING / "bom-smt-refs.csv", assembly / "bom-smt-refs.csv"),
        (MANUFACTURING / "bom.csv", assembly / "bom-full.csv"),
        (MANUFACTURING / "bom-report.json", assembly / "bom-report.json"),
        (MANUFACTURING / "bom-jlcpcb.csv", assembly / "bom-jlcpcb.csv"),
        (MANUFACTURING / "cpl.csv", assembly / "cpl.csv"),
        (MANUFACTURING / "cpl-jlcpcb.csv", assembly / "cpl-jlcpcb.csv"),
        (MANUFACTURING / "jlcpcb-report.json", assembly / "jlcpcb-report.json"),
        (MANUFACTURING / "board-front.pdf", assembly / "assembly-front.pdf"),
        (MANUFACTURING / "board-back.pdf", assembly / "assembly-back.pdf"),
        (
            MANUFACTURING / "connector-label-check.png",
            assembly / "connector-label-check.png",
        ),
    ):
        shutil.copy2(source, destination)

    bom_report = json.loads(
        (MANUFACTURING / "bom-report.json").read_text(encoding="utf-8")
    )
    assembly_readme = f"""\
PCB fabrication plus SMT assembly data.

- SMT references: {placement_report['placements']}
- SMT BOM groups: {bom_report['smt_bom_groups']}
- Placement origin: board lower-left
- Units: millimetres, Y positive upward
- Gerbers include front/back copper, paste, mask, silkscreen and board edge

Use `bom-smt.csv` for purchasing/grouped review and `cpl.csv` for placement.
`bom-smt-refs.csv` provides a one-row-per-reference cross-check.
`bom-jlcpcb.csv` and `cpl-jlcpcb.csv` use the column names commonly requested
by JLCPCB. The JLCPCB part-number column is present but blank because this
repository does not contain verified LCSC part numbers.

Mixed-footprint J54 and all through-hole parts are excluded from the SMT BOM
and CPL. `bom-full.csv` lists the complete assembly for manual or separate
through-hole work.

LCSC part numbers are not present. The BOM is suitable for an assembly house
that sources by manufacturer/MPN; direct JLCPCB upload requires LCSC numbers.
"""
    write_readme(
        assembly,
        "uCNC Pi Board - SMT Assembly Package",
        assembly_readme,
    )

    fabrication_zip = MANUFACTURING / "uCNC_Pi_Board_PCB_Fabrication.zip"
    assembly_zip = MANUFACTURING / "uCNC_Pi_Board_SMT_Assembly.zip"
    create_zip(fabrication, fabrication_zip)
    create_zip(assembly, assembly_zip)
    print(
        json.dumps(
            {
                "pcb_fabrication_zip": str(fabrication_zip),
                "smt_assembly_zip": str(assembly_zip),
                "smt_placements": placement_report["placements"],
                "jlc_references": jlc_report["smt_references"],
                "jlc_references_match": jlc_report["references_match"],
                "cpl_origin": placement_report["origin"],
                "raw_position_excluded": placement_report[
                    "excluded_from_raw_position"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
