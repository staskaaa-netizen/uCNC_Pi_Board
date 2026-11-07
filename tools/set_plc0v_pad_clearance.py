"""Set a 0.25 mm local clearance override on every PLC_0V pad."""

from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
NET_NAME = "PLC_0V"
CLEARANCE_MM = 0.25


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    pads = [
        pad
        for footprint in board.GetFootprints()
        for pad in footprint.Pads()
        if pad.GetNetname() == NET_NAME
    ]
    for pad in pads:
        pad.SetLocalClearance(pcbnew.FromMM(CLEARANCE_MM))
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(
        {
            "net": NET_NAME,
            "clearance_mm": CLEARANCE_MM,
            "pads_updated": len(pads),
        }
    )


if __name__ == "__main__":
    main()
