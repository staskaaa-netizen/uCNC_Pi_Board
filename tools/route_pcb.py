"""Export Specctra DSN, run Freerouting, and import the routed SES."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
HARDWARE = ROOT / "hardware"
PCB = HARDWARE / "motherboard.kicad_pcb"
DSN = HARDWARE / "motherboard.dsn"
SES = HARDWARE / "motherboard.ses"
JAVA = (
    ROOT.parent
    / "tmp"
    / "leancam-sources"
    / "temurin25-jre"
    / "jdk-25.0.4.1+1-jre"
    / "bin"
    / "java.exe"
)
FREEROUTING_JAR = ROOT.parent / "tmp" / "leancam-sources" / "freerouting-2.5.0.jar"
KICAD_PYTHON = Path(
    r"C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe"
)


def main() -> None:
    board = pcbnew.LoadBoard(str(PCB))
    board.BuildConnectivity()
    # GND is completed by copper zones after routing. Removing it from the DSN
    # avoids asking the maze router to fan out hundreds of plane-connected pads.
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() == "GND":
                pad.SetNetCode(0)
    for zone in list(board.Zones()):
        board.Remove(zone)
    board.BuildConnectivity()
    if not pcbnew.ExportSpecctraDSN(board, str(DSN)):
        raise RuntimeError("KiCad failed to export Specctra DSN")

    env = os.environ.copy()
    env["FREEROUTING_USER_DATA_DIR"] = str(ROOT / ".freerouting")
    Path(env["FREEROUTING_USER_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
    command = [
        str(JAVA),
        "-jar",
        str(FREEROUTING_JAR),
        "-de",
        str(DSN),
        "-do",
        str(SES),
        "-mp",
        "5",
        "-mt",
        "12",
        "-us",
        "greedy",
        "-is",
        "sequential",
    ]
    print(" ".join(command))
    subprocess.run(command, check=True, cwd=ROOT, env=env)
    if not SES.exists():
        raise RuntimeError("Freerouting did not produce a session file")

    # KiCad's SWIG session can be invalidated if DSN export and SES import share
    # one Python process. Import in a clean process.
    subprocess.run(
        [str(KICAD_PYTHON), str(ROOT / "tools" / "import_ses.py")],
        check=True,
        cwd=ROOT,
    )


if __name__ == "__main__":
    main()
