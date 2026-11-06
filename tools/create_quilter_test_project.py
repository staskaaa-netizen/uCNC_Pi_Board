"""Create a standalone Quilter test copy of the current KiCad project."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "hardware"
DEFAULT_OUTPUT = ROOT / "experiments" / "quilter-ai-test"
PROJECT_FILES = {
    "motherboard.kicad_pro",
    "motherboard.kicad_prl",
    "motherboard.kicad_dru",
    "fp-lib-table",
    "sym-lib-table",
}
def reset_directory(path: Path) -> None:
    resolved = path.resolve()
    experiments = (ROOT / "experiments").resolve()
    if resolved != experiments and experiments not in resolved.parents:
        raise RuntimeError(f"Unsafe output directory: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True)


def copy_project(source: Path, output: Path) -> None:
    for path in source.iterdir():
        if not path.is_file():
            continue
        if path.name in PROJECT_FILES or path.suffix == ".kicad_sch":
            shutil.copy2(path, output / path.name)
    shutil.copytree(source / "libraries", output / "libraries")


def remove_copper(board) -> None:
    board.Tracks().clear()
    for zone in list(board.Zones()):
        board.Remove(zone)


def create_unrouted(source_board: Path, output_board: Path) -> dict:
    board = pcbnew.LoadBoard(str(source_board))
    footprints = len(board.GetFootprints())
    zones = len(list(board.Zones()))
    remove_copper(board)
    pcbnew.SaveBoard(str(output_board), board)
    return {
        "path": output_board,
        "footprints": footprints,
        "tracks": 0,
        "vias": 0,
        "zones": 0,
        "source_zones_removed": zones,
    }


def create_mechanical_outline(
    source_board: Path,
    output_board: Path,
) -> dict:
    source = pcbnew.LoadBoard(str(source_board))
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    for drawing in source.GetDrawings():
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            board.Add(drawing.Duplicate())
    pcbnew.SaveBoard(str(output_board), board)
    return {
        "path": output_board,
        "footprints": len(board.GetFootprints()),
        "tracks": 0,
        "vias": 0,
        "zones": len(list(board.Zones())),
    }


def board_size_mm(board_path: Path) -> tuple[float, float]:
    board = pcbnew.LoadBoard(str(board_path))
    box = board.GetBoardEdgesBoundingBox()
    return pcbnew.ToMM(box.GetWidth()), pcbnew.ToMM(box.GetHeight())


def board_counts(board_path: Path) -> dict:
    board = pcbnew.LoadBoard(str(board_path))
    return {
        "footprints": len(board.GetFootprints()),
        "tracks": sum(
            isinstance(item, pcbnew.PCB_TRACK)
            and not isinstance(item, pcbnew.PCB_VIA)
            for item in board.GetTracks()
        ),
        "vias": sum(
            isinstance(item, pcbnew.PCB_VIA)
            for item in board.GetTracks()
        ),
        "zones": len(list(board.Zones())),
    }


def run_board_stage(stage: str, source: Path, output: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--stage",
            stage,
            "--source-board",
            str(source),
            "--output-board",
            str(output),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr.strip()
            or result.stdout.strip()
            or f"KiCad board stage failed: {stage}"
        )


def zip_board(board_path: Path, output: Path) -> None:
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(board_path, board_path.name)


def zip_project(project_dir: Path, output: Path) -> None:
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(project_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(project_dir))


def write_readme(
    output: Path,
    unrouted: dict,
    outline: dict,
    size: tuple[float, float],
) -> None:
    text = f"""\
# Quilter AI Test Project

This is a separate copy of the uCNC RP2350B board for Quilter experiments.
The released manufacturing PCB is untouched.

## Upload for routing

Use:

`hardware/motherboard.kicad_pcb`

It preserves:

- the exact board outline: {size[0]:.3f} x {size[1]:.3f} mm
- {unrouted['footprints']} placed footprints
- component references, values and net names
- pad net assignments, net classes and board rules
- two-layer stackup, mechanical holes and silkscreen

It deliberately contains:

- {unrouted['tracks']} copper tracks
- {unrouted['vias']} vias
- {unrouted['zones']} copper zones

Unconnected-item DRC results are expected because this board is entirely
unrouted.

Two convenience archives are outside this directory:

- `../quilter-ai-test-unrouted-board.zip`
- `../quilter-ai-test-outline-only.zip`
- `../quilter-ai-test-project.zip`

## Upload for placement only

Use:

`hardware/motherboard-outline-only.kicad_pcb`

This contains only the exact board edge, with no footprints, electrical
components, tracks, vias or zones.

## Opening the project

Open `hardware/motherboard.kicad_pro`. Schematics, local symbols, footprints,
3D models and design rules are included so the project remains editable in
KiCad 10.

This experiment is not a released manufacturing package.
"""
    (output / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--stage",
        choices=("unrouted", "outline"),
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--source-board", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--output-board", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.stage:
        if not args.source_board or not args.output_board:
            raise SystemExit("stage generation requires board paths")
        if args.stage == "unrouted":
            create_unrouted(args.source_board, args.output_board)
        else:
            create_mechanical_outline(args.source_board, args.output_board)
        # KiCad 10 can crash in SWIG destructors after large object deletion.
        # The files are already closed and saved at this point.
        os._exit(0)

    source = args.source_dir.resolve()
    output = args.output_dir.resolve()
    reset_directory(output)
    hardware = output / "hardware"
    hardware.mkdir()
    copy_project(source, hardware)

    source_board = source / "motherboard.kicad_pcb"
    unrouted_path = hardware / "motherboard.kicad_pcb"
    outline_path = hardware / "motherboard-outline-only.kicad_pcb"
    run_board_stage("unrouted", source_board, unrouted_path)
    run_board_stage("outline", source_board, outline_path)
    unrouted = board_counts(unrouted_path)
    outline = board_counts(outline_path)
    size = board_size_mm(unrouted_path)
    write_readme(output, unrouted, outline, size)

    zip_board(
        unrouted_path,
        ROOT / "experiments" / "quilter-ai-test-unrouted-board.zip",
    )
    zip_board(
        outline_path,
        ROOT / "experiments" / "quilter-ai-test-outline-only.zip",
    )
    zip_project(
        hardware,
        ROOT / "experiments" / "quilter-ai-test-project.zip",
    )
    print(
        {
            "project": str(output),
            "board_size_mm": [round(size[0], 3), round(size[1], 3)],
            "unrouted": {
                key: unrouted[key]
                for key in ("footprints", "tracks", "vias", "zones")
            },
            "outline_only": {
                key: outline[key]
                for key in ("footprints", "tracks", "vias", "zones")
            },
        }
    )


if __name__ == "__main__":
    main()
