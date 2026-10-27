"""Apply the verified 3D transform to the WeAct module instance."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
OFFSET_MM = (-20.7, 20.6, 0.0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprint = next(
        (item for item in board.GetFootprints() if item.GetReference() == "MOD1"),
        None,
    )
    if footprint is None:
        raise SystemExit("MOD1 not found")
    models = footprint.Models()
    if len(models) != 1:
        raise SystemExit(f"Expected one MOD1 3D model, found {len(models)}")
    model = models[0]
    print(
        "before:",
        model.m_Filename,
        model.m_Offset.x,
        model.m_Offset.y,
        model.m_Offset.z,
    )
    model.m_Offset.x, model.m_Offset.y, model.m_Offset.z = OFFSET_MM
    print("after:", model.m_Offset.x, model.m_Offset.y, model.m_Offset.z)
    if not args.apply:
        return
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
