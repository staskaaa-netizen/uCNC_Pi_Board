"""Place AI1/AI2 from the approved AI0 divider/filter template."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

CHANNELS = {
    1: ("R64", "R66", "C74"),
    2: ("R67", "R69", "C75"),
}
AI0_COMPONENTS = ("R61", "R63", "C73")
J24_AI_PINS = {0: "1", 1: "3", 2: "5"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--channel", type=int, choices=tuple(CHANNELS), required=True)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    j24 = footprints["J24"]
    anchor0 = j24.FindPadByNumber(J24_AI_PINS[0]).GetPosition()
    anchor = j24.FindPadByNumber(J24_AI_PINS[args.channel]).GetPosition()

    template = []
    for reference in AI0_COMPONENTS:
        footprint = footprints[reference]
        position = footprint.GetPosition()
        template.append(
            (
                position.x - anchor0.x,
                position.y - anchor0.y,
                footprint.GetOrientationDegrees(),
            )
        )

    for reference, (dx, dy, rotation) in zip(CHANNELS[args.channel], template):
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetPosition(pcbnew.VECTOR2I(anchor.x + dx, anchor.y + dy))
        footprint.SetOrientationDegrees(rotation)
        position = footprint.GetPosition()
        print(
            f"{reference}: ({pcbnew.ToMM(position.x):.3f}, "
            f"{pcbnew.ToMM(position.y):.3f}) rotation={rotation:.1f}"
        )

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
