"""Apply width rules to the isolated backlight power nets."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
WIDTHS_MM = {
    "+12V_BL": 0.8,
    "+24V_FIELD": 0.8,
    "ISO_GND": 0.8,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    changes = []
    for track in board.GetTracks():
        if track.GetClass() != "PCB_TRACK":
            continue
        netclass_name, width_mm = next(
            (
                (net, width)
                for net, width in WIDTHS_MM.items()
                if track.GetNetname() == net
            ),
            (None, None),
        )
        if netclass_name is None:
            continue
        desired = pcbnew.FromMM(width_mm)
        if track.GetWidth() != desired:
            changes.append(
                (
                    netclass_name,
                    round(pcbnew.ToMM(track.GetWidth()), 3),
                    width_mm,
                )
            )
            if args.apply:
                track.SetWidth(desired)

    if args.apply:
        board.BuildConnectivity()
        pcbnew.SaveBoard(str(args.board), board)
    print(f"width_changes={len(changes)} apply={args.apply}")
    for net, old_width, new_width in changes:
        print(f"{net}: {old_width:.3f} mm -> {new_width:.3f} mm")


if __name__ == "__main__":
    main()
