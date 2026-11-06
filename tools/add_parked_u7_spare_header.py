"""Park the J55 U7 spare-input header outside the PCB for manual placement."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew

from generate_pcb import load_footprint


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
PARK_X_MM = 175.0


def net(board, name: str):
    item = board.FindNet(name)
    if item is None:
        item = pcbnew.NETINFO_ITEM(board, name)
        board.Add(item)
    return item


def add_footprint(
    board,
    library_id: str,
    reference: str,
    value: str,
    position: tuple[float, float],
    pad_nets: dict[str, str],
):
    footprint = load_footprint(library_id)
    footprint.SetReference(reference)
    footprint.SetValue(value)
    footprint.SetPosition(pcbnew.VECTOR2I_MM(*position))
    footprint.SetOrientationDegrees(0)
    footprint.SetLayer(pcbnew.F_Cu)
    for pad_number, net_name in pad_nets.items():
        pad = footprint.FindPadByNumber(pad_number)
        if pad is None:
            raise RuntimeError(f"Missing pad {reference}.{pad_number}")
        pad.SetNet(net(board, net_name))
    board.Add(footprint)
    return footprint


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(BOARD))
    for reference in ("J55", "JP6", "JP7"):
        existing = board.FindFootprintByReference(reference)
        if existing is not None:
            board.Remove(existing)

    u7 = board.FindFootprintByReference("U7")
    if u7 is None:
        raise RuntimeError("U7 not found")
    u7.FindPadByNumber("13").SetNet(net(board, "U7_IN13"))
    u7.FindPadByNumber("14").SetNet(net(board, "U7_IN14"))

    add_footprint(
        board,
        "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "J55",
        "U7 spare inputs: GND, IN13, IN14",
        (PARK_X_MM, 10.0),
        {"1": "GND", "2": "U7_IN13", "3": "U7_IN14"},
    )
    board.BuildConnectivity()
    if args.apply:
        pcbnew.SaveBoard(str(BOARD), board)
        print(f"Saved {BOARD}")
    print(
        {
            "parked": ["J55"],
            "u7_pins_changed": {"13": "U7_IN13", "14": "U7_IN14"},
            "pin15": "GND / CLK INH unchanged",
            "apply": args.apply,
        }
    )


if __name__ == "__main__":
    main()
