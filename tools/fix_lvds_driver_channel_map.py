"""Correct the U41 and passive-resistor LVDS channel pairing."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

DRIVER_NETS = {
    "1": "+3V3",
    "2": "HSTX_CLK_P",   # DIN1
    "3": "HSTX_D2_P",    # DIN2
    "4": "+3V3",
    "5": "GND",
    "6": "HSTX_D1_P",    # DIN3
    "7": "HSTX_D0_P",    # DIN4
    "8": "GND",
    "9": "LVDS_D0_N",    # DOUT4-
    "10": "LVDS_D0_P",   # DOUT4+
    "11": "LVDS_D1_P",   # DOUT3+
    "12": "LVDS_D1_N",   # DOUT3-
    "13": "LVDS_D2_N",   # DOUT2-
    "14": "LVDS_D2_P",   # DOUT2+
    "15": "LVDS_CLK_P",  # DOUT1+
    "16": "LVDS_CLK_N",  # DOUT1-
}

RESISTOR_NETS = {
    "RN26": {
        "1": "HSTX_D1_N",
        "2": "HSTX_D1_P",
        "3": "HSTX_D0_P",
        "4": "HSTX_D0_N",
        "5": "LVDS_D0_N",
        "6": "LVDS_D0_P",
        "7": "LVDS_D1_P",
        "8": "LVDS_D1_N",
    },
    "RN27": {
        "1": "HSTX_CLK_N",
        "2": "HSTX_CLK_P",
        "3": "HSTX_D2_P",
        "4": "HSTX_D2_N",
        "5": "LVDS_D2_N",
        "6": "LVDS_D2_P",
        "7": "LVDS_CLK_P",
        "8": "LVDS_CLK_N",
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.board))
    footprints = {footprint.GetReference(): footprint for footprint in board.GetFootprints()}
    expected = {"U41": DRIVER_NETS, **RESISTOR_NETS}
    missing = sorted(set(expected) - set(footprints))
    if missing:
        raise SystemExit(f"Missing footprints: {', '.join(missing)}")
    changes = []
    for reference, pin_nets in expected.items():
        for pad in footprints[reference].Pads():
            target = pin_nets[pad.GetNumber()]
            if pad.GetNetname() != target:
                changes.append(
                    (reference, pad.GetNumber(), pad.GetNetname(), target)
                )
    for reference, pin, old_net, new_net in changes:
        print(f"{reference} pin {pin}: {old_net} -> {new_net}")
    if not args.apply:
        return
    for reference, pin_nets in expected.items():
        for pad in footprints[reference].Pads():
            target = pin_nets[pad.GetNumber()]
            net = board.FindNet(target)
            if net is None:
                raise SystemExit(f"Missing net {target}")
            pad.SetNet(net)
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(args.board), board)
    print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
