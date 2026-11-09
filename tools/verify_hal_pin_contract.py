"""Verify the normative RP2350 HAL pin contract against the PCB."""

from __future__ import annotations

import csv
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "hardware" / "motherboard.kicad_pcb"
CONTRACT = ROOT / "hardware" / "rp2350-hal-pin-contract.csv"


def main() -> None:
    rows = list(csv.DictReader(CONTRACT.open(newline="", encoding="utf-8")))
    board = pcbnew.LoadBoard(str(BOARD))
    module = next(
        footprint
        for footprint in board.GetFootprints()
        if footprint.GetReference() == "MOD1"
    )
    pads = {pad.GetNumber(): pad for pad in module.Pads()}

    failures: list[str] = []
    seen_pins: set[str] = set()
    gpio_rows = [row for row in rows if row["gpio"]]
    if len(gpio_rows) != 48:
        failures.append(f"Expected 48 GPIO rows, found {len(gpio_rows)}")
    if {int(row["gpio"]) for row in gpio_rows} != set(range(48)):
        failures.append("GPIO contract does not contain exactly GPIO0-GPIO47")

    for row in rows:
        pin = row["mod1_pin"]
        if pin in seen_pins:
            failures.append(f"Duplicate MOD1 pin {pin}")
        seen_pins.add(pin)
        pad = pads.get(pin)
        if pad is None:
            if row["board_net"] == "-" and row["resource"].startswith("MOD1_DEBUG_"):
                continue
            failures.append(f"{row['resource']}: MOD1 pin {pin} does not exist")
            continue
        expected = row["board_net"]
        actual = pad.GetNetname()
        if expected == "-":
            if actual:
                failures.append(
                    f"{row['resource']}: pin {pin} is unconnected in the "
                    f"contract but is on net {actual}"
                )
        elif actual != expected:
            failures.append(
                f"{row['resource']}: MOD1 pin {pin} expected {expected}, "
                f"found {actual or '<no net>'}"
            )

    if failures:
        print("HAL pin contract verification FAILED")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print(
        "HAL pin contract verification PASSED: "
        f"{len(gpio_rows)} GPIOs, {len(rows)} module pins"
    )


if __name__ == "__main__":
    main()
