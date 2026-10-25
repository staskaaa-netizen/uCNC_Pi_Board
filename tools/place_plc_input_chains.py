"""Place all isolated input field chains and their local optocoupler parts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import put_on_side


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    j7 = footprints["J7"]
    j8 = footprints["J8"]
    anchor0 = j7.FindPadByNumber("1").GetPosition()

    template_refs = ("R18", "D14", "D13")
    template = []
    for reference in template_refs:
        footprint = footprints[reference]
        position = footprint.GetPosition()
        template.append(
            (
                position.x - anchor0.x,
                position.y - anchor0.y,
                footprint.GetOrientationDegrees(),
            )
        )

    for bit in range(16):
        if bit < 8:
            anchor = j7.FindPadByNumber(str(bit + 1)).GetPosition()
        else:
            anchor = j8.FindPadByNumber(str(bit - 7)).GetPosition()

        references = (f"R{18 + bit}", f"D{14 + 2 * bit}", f"D{13 + 2 * bit}")
        for reference, (dx, dy, rotation) in zip(references, template):
            footprint = footprints[reference]
            put_on_side(footprint, back=False)
            footprint.SetPosition(pcbnew.VECTOR2I(anchor.x + dx, anchor.y + dy))
            footprint.SetOrientationDegrees(rotation)
            position = footprint.GetPosition()
            print(
                f"input {bit:2d}: {reference} -> "
                f"({pcbnew.ToMM(position.x):.2f}, {pcbnew.ToMM(position.y):.2f}) "
                f"rot={rotation:.1f}"
            )

    # U17 was a two-channel safety quad. Its channels are now individual EL3H7
    # parts U35 (E-stop) and U36 (HOLD). Keep the
    # complete field chain close to the dedicated connectors on B.Cu where the
    # top-right F.Cu area is occupied. The sequence and spacing match the PLC
    # chains: input limit, indicator LED, reverse diode, optocoupler and pull-up.
    safety_channels = (
        {
            "connector": "J5",
            "resistor": "R16",
            "led": "D9",
            "reverse_diode": "D10",
            "opto": "U35",
            "pullup": "R74",
        },
        {
            "connector": "J6",
            "resistor": "R17",
            "led": "D11",
            "reverse_diode": "D12",
            "opto": "U36",
            "pullup": "R75",
        },
    )
    safety_layout = (
        # reference key, dx, dy, rotation
        ("resistor", -7.25, 0.0, 180.0),
        ("led", -11.95, 0.0, 0.0),
        ("reverse_diode", -11.95, -3.0, 0.0),
        ("opto", -15.75, 0.0, 180.0),
        ("pullup", -27.85, 0.0, 180.0),
    )
    for channel in safety_channels:
        connector = footprints[channel["connector"]]
        anchor = connector.FindPadByNumber("1").GetPosition()
        for key, dx, dy, rotation in safety_layout:
            reference = channel[key]
            footprint = footprints[reference]
            put_on_side(footprint, back=True)
            footprint.SetPosition(
                pcbnew.VECTOR2I(round(anchor.x + pcbnew.FromMM(dx)), round(anchor.y + pcbnew.FromMM(dy)))
            )
            footprint.SetOrientationDegrees(rotation)
            position = footprint.GetPosition()
            print(
                f"{channel['connector']} safety: {reference} -> "
                f"({pcbnew.ToMM(position.x):.2f}, {pcbnew.ToMM(position.y):.2f}) "
                f"rot={rotation:.1f} B.Cu"
            )

    pcbnew.SaveBoard(str(args.board), board)


if __name__ == "__main__":
    main()
