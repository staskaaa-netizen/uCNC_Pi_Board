"""Promote connector reference and value fields to the physical silkscreen."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
SKIP_REFERENCES = {"J22"}  # J22 has purpose-built row legends.


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    promoted = []
    for footprint in board.GetFootprints():
        reference = footprint.GetReference()
        if not reference.startswith("J") or reference in SKIP_REFERENCES:
            continue
        layer = pcbnew.B_SilkS if footprint.GetLayer() == pcbnew.B_Cu else pcbnew.F_SilkS
        footprint.Reference().SetLayer(layer)
        footprint.Reference().SetVisible(True)
        footprint.Reference().SetMirrored(layer == pcbnew.B_SilkS)
        footprint.Value().SetLayer(layer)
        footprint.Value().SetVisible(True)
        footprint.Value().SetMirrored(layer == pcbnew.B_SilkS)
        footprint.Value().SetTextSize(pcbnew.VECTOR2I_MM(0.8, 0.8))
        footprint.Value().SetTextThickness(pcbnew.FromMM(0.12))
        promoted.append(reference)

    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")
    print(f"Promoted {len(promoted)} connector labels: {', '.join(sorted(promoted))}")


if __name__ == "__main__":
    main()
