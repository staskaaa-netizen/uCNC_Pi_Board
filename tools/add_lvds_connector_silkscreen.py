"""Add an assembly legend beside J22 on the back silkscreen."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
LABELS = (
    ("J22 LCD LVDS 2x10", 0.0, 0.0, 1.2),
    ("1-3: 3V3", 0.0, 1.7, 0.9),
    ("4-6,13-14: GND", 0.0, 3.0, 0.9),
    ("7/8: D0- / D0+", 0.0, 4.3, 0.9),
    ("9/10: D1- / D1+", 0.0, 5.6, 0.9),
    ("11/12: D2- / D2+", 0.0, 6.9, 0.9),
    ("15/16: CLK- / CLK+", 0.0, 8.2, 0.9),
    ("17-20: NC", 0.0, 9.5, 0.9),
)
LEGACY_LABELS = {"LCD LVDS 2x10"}


def add_text(
    board,
    text: str,
    x_mm: float,
    y_mm: float,
    size_mm: float,
    thickness_mm: float = 0.16,
) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetLayer(pcbnew.B_SilkS)
    item.SetTextSize(pcbnew.VECTOR2I_MM(size_mm, size_mm))
    item.SetTextThickness(pcbnew.FromMM(thickness_mm))
    item.SetTextPos(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetTextAngleDegrees(0)
    item.SetMirrored(True)
    item.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(item)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    connector = next(
        (
            footprint
            for footprint in board.GetFootprints()
            if footprint.GetReference() == "J22"
        ),
        None,
    )
    if connector is None:
        raise SystemExit("J22 not found")
    position = connector.GetPosition()
    origin_x = pcbnew.ToMM(position.x) - 28.0
    origin_y = pcbnew.ToMM(position.y) - 16.0
    existing = {
        item.GetText(): item
        for item in board.GetDrawings()
        if isinstance(item, pcbnew.PCB_TEXT) and item.GetLayer() == pcbnew.B_SilkS
    }
    for text in LEGACY_LABELS | {entry[0] for entry in LABELS}:
        if text in existing:
            board.Remove(existing[text])
    additions = list(LABELS)
    for text, dx, dy, size in additions:
        print(
            f"add B.Silkscreen {text!r} at "
            f"({origin_x + dx:.2f},{origin_y + dy:.2f}) size {size:.2f}"
        )
    if not args.apply:
        return
    for text, dx, dy, size in additions:
        add_text(board, text, origin_x + dx, origin_y + dy, size)
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
