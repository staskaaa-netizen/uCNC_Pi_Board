"""Import a routed Specctra session into the KiCad PCB in a fresh process."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "hardware" / "motherboard.kicad_pcb"
SES = ROOT / "hardware" / "motherboard.ses"


def main() -> None:
    board = pcbnew.LoadBoard(str(PCB))
    if not pcbnew.ImportSpecctraSES(board, str(SES)):
        raise RuntimeError("KiCad failed to import routed SES")
    board.BuildConnectivity()
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(PCB), board)
    print(f"Imported {len(board.GetTracks())} track/via items and filled GND zones")


if __name__ == "__main__":
    main()
