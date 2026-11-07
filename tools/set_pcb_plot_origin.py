"""Set the shared drill/place origin to the PCB lower-left corner."""

from __future__ import annotations

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    board = pcbnew.LoadBoard(str(BOARD))
    bbox = board.GetBoardEdgesBoundingBox()
    origin = pcbnew.VECTOR2I_MM(
        pcbnew.ToMM(bbox.GetLeft()),
        pcbnew.ToMM(bbox.GetBottom()),
    )
    board.GetDesignSettings().SetAuxOrigin(origin)
    pcbnew.SaveBoard(str(BOARD), board)
    print(
        {
            "aux_origin_mm": [
                pcbnew.ToMM(origin.x),
                pcbnew.ToMM(origin.y),
            ]
        }
    )


if __name__ == "__main__":
    main()
