"""Add the physical J22 row labels on the front silkscreen."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
LABELS = (
    ("J22 LVDS", -13.593, -2.034, 0.8),
    ("NC NC CLK_P GND D2_P D1_P D0_P GND GND 3V3", -21.721, 4.443, 0.62),
    ("NC NC CLK_N GND D2_N D1_N D0_N GND 3V3 3V3", -21.594, 6.221, 0.62),
)
LEGACY_LABELS = {
    "LCD LVDS 2x10",
    "J22 LVDS",
    "PWR 1-3   GND 4-6,13-14",
    "D0- 7  D0+ 8   D1- 9  D1+ 10",
    "D2- 11 D2+ 12  CLK- 15 CLK+ 16",
    "NC 17-20",
    "NC NC CLK_N GND D2_N D1_N D0_N GND GND 3V3",
    "NC NC CLK_P GND D2_P D1_P D0_P GND GND 3V3",
}


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
    item.SetLayer(pcbnew.F_SilkS)
    item.SetTextSize(pcbnew.VECTOR2I_MM(size_mm, size_mm))
    item.SetTextThickness(pcbnew.FromMM(thickness_mm))
    item.SetTextPos(pcbnew.VECTOR2I_MM(x_mm, y_mm))
    item.SetTextAngleDegrees(0)
    item.SetMirrored(False)
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
    origin_x = pcbnew.ToMM(position.x)
    origin_y = pcbnew.ToMM(position.y)
    existing = {
        item.GetText(): item
        for item in board.GetDrawings()
        if isinstance(item, pcbnew.PCB_TEXT)
        and item.GetLayer() in {pcbnew.B_SilkS, pcbnew.F_SilkS}
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
