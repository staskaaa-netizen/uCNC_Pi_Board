# WEACT RP2350B PSRAM bench test

Use this test after soldering the optional 8 MiB PSRAM on the WEACT RP2350B
Core Board and before building machine firmware. It tests the module, not the
LVDS scanout: the chip is initialized through QMI CS1 on GPIO0, its identity
is read by the Arduino-Pico core, and every 32-bit word of the detected 8 MiB
region is checked with data and address-dependent patterns.

```powershell
pio run -e RP2350-WEACT-PSRAM-TEST
pio run -e RP2350-WEACT-PSRAM-TEST -t upload
pio device monitor
```

The successful result is:

```text
detected bytes=8388608
PSRAM pattern 00: PASS
PSRAM pattern FF: PASS
PSRAM pattern 55: PASS
PSRAM pattern AA: PASS
PSRAM pattern address: PASS
PSRAM pattern address-inverse: PASS
PSRAM TEST: PASS 8 MiB
```

Bench result, 2026-11-16: the soldered WEACT PSRAM was detected as 8 MiB and
all six patterns passed over the complete range.

`detected bytes=0` means the chip was not identified. Check its orientation,
all package solder joints, the 3.3 V supply, and the GPIO0 chip-select path.
A data or address pattern failure reports the first failing byte. That is a
hardware fault; do not enable the PSRAM draw buffer in machine firmware until
the full test passes.

This target is hardware bring-up only. It excludes `uCNC.ino` and all machine
modules and must never be used as the machine firmware.
