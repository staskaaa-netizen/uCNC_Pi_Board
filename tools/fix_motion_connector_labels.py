"""Verify motion and servo-status connector pad polarity and order."""

from __future__ import annotations

import argparse
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"

EXPECTED_PADS = {
    "J10": {1: "EN3", 2: "STP0", 3: "DIR0"},
    "J11": {1: "EN3", 2: "STP1", 3: "DIR1"},
    "J28": {1: "EN3", 2: "STP2", 3: "DIR2"},
    "J29": {1: "EN4", 2: "STP3", 3: "DIR3"},
    "J47": {1: "EN4", 2: "STP4", 3: "DIR4"},
    "J46": {1: "EN4", 2: "STP5", 3: "DIR5"},
    "J30": {1: "EN4", 2: "STP6", 3: "DIR6"},
    "J40": {1: "GND", 2: "ERR0", 3: "Z0"},
    "J41": {1: "GND", 2: "ERR1", 3: "Z1"},
    "J42": {1: "GND", 2: "ERR2", 3: "Z2"},
    "J43": {1: "GND", 2: "ERR3", 3: "Z3"},
    "J50": {1: "GND", 2: "ERR4", 3: "Z4"},
    "J49": {1: "GND", 2: "ERR5", 3: "Z5"},
    "J48": {1: "GND", 2: "ERR6", 3: "Z6"},
}

EXPECTED_DISPLAY = {
    "J10": "DIR0 STP0 EN3",
    "J11": "DIR1 STP1 EN3",
    "J28": "DIR2 STP2 EN3",
    "J29": "DIR3 STP3 EN4",
    "J47": "DIR4 STP4 EN4",
    "J46": "DIR5 STP5 EN4",
    "J30": "DIR6 STP6 EN4",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--board", type=Path, default=DEFAULT_BOARD)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    board = pcbnew.LoadBoard(str(args.board))
    footprints = {item.GetReference(): item for item in board.GetFootprints()}
    failures = []
    for reference, expected in EXPECTED_PADS.items():
        footprint = footprints.get(reference)
        if footprint is None:
            failures.append(f"{reference}: missing")
            continue
        actual = {
            int(pad.GetNumber()): pad.GetNetname()
            for pad in footprint.Pads()
            if pad.GetNumber().isdigit()
        }
        for pin, net_name in expected.items():
            if actual.get(pin) != net_name:
                failures.append(
                    f"{reference}.{pin}: expected {net_name}, found {actual.get(pin)}"
                )
        if reference in EXPECTED_DISPLAY and footprint.GetValue() != EXPECTED_DISPLAY[reference]:
            failures.append(
                f"{reference}: visible value must be {EXPECTED_DISPLAY[reference]}, "
                f"found {footprint.GetValue()}"
            )
        print(
            f"{reference}: "
            + ", ".join(f"{pin}={expected[pin]}" for pin in sorted(expected))
        )

    if failures:
        raise SystemExit("\n".join(failures))
    if args.apply:
        pcbnew.SaveBoard(str(args.board), board)
        print(f"Saved {args.board}")


if __name__ == "__main__":
    main()
