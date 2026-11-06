"""Set every PCB text object to 0.8 x 0.8 mm with a 0.12 mm stroke."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
TEXT_SIZE = pcbnew.VECTOR2I_MM(0.8, 0.8)
TEXT_THICKNESS = pcbnew.FromMM(0.12)


def text_items(board):
    for footprint in board.GetFootprints():
        yield from footprint.GetFields()
        for item in footprint.GraphicalItems():
            if type(item).__name__ == "PCB_TEXT":
                yield item
    for item in board.GetDrawings():
        if type(item).__name__ == "PCB_TEXT":
            yield item


def geometry(item):
    position = item.GetPosition()
    return (
        position.x,
        position.y,
        item.GetTextAngleDegrees(),
        item.GetLayer(),
        item.IsVisible(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    items = list(text_items(board))
    changes = []
    for item in items:
        size = item.GetTextSize()
        thickness = item.GetTextThickness()
        if (
            size.x != TEXT_SIZE.x
            or size.y != TEXT_SIZE.y
            or thickness != TEXT_THICKNESS
        ):
            changes.append(item)

    print(
        {
            "text_objects": len(items),
            "size_thickness_changes": len(changes),
            "target_size_mm": [0.8, 0.8],
            "target_thickness_mm": 0.12,
            "apply": args.apply,
        }
    )
    if not args.apply:
        return

    before = {id(item): geometry(item) for item in items}
    for item in items:
        item.SetTextSize(TEXT_SIZE)
        item.SetTextThickness(TEXT_THICKNESS)
    moved = [
        item
        for item in items
        if geometry(item) != before[id(item)]
    ]
    if moved:
        raise RuntimeError(f"Text geometry changed for {len(moved)} objects")

    board.BuildConnectivity()
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"Saved {BOARD}")


if __name__ == "__main__":
    main()
