"""Place all PLC-input pull-ups beside their optocoupler output pins."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

# References R76-R91 correspond to PLC inputs 1-16. Each resistor is placed
# immediately to the RP2350 side of its optocoupler collector, in the same
# orientation as the hand-approved input-0 template.
PULLUP_POSITIONS = (
    (45.922, 103.12), (45.922, 105.71), (45.922, 108.25), (45.922, 110.79),
    (46.422, 119.17), (46.422, 121.71), (46.422, 124.25), (46.422, 126.79),
    (46.642, 67.54), (46.642, 70.08), (46.642, 72.62), (46.642, 75.16),
    (47.142, 85.04), (47.142, 87.58), (47.142, 90.12), (47.142, 92.66),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    for bit, (x, y) in enumerate(PULLUP_POSITIONS):
        reference = f"R{76 + bit}"
        footprint = footprints[reference]
        put_on_side(footprint, back=False)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.SetOrientationDegrees(0.0)
        print(f"PLC input {bit + 1:2d}: {reference} -> ({x:.3f}, {y:.3f}) F.Cu")

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
