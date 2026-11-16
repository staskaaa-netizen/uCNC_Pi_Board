# Batch 1 bench status

Bench record for the assembled Batch 1 RP2350B carriers, 2026-11-16.

## Working

| Function | Bench evidence |
| --- | --- |
| WeAct module boot and USB serial | Boots uCNC and enumerates as a USB CDC serial port (`COM12` on the bench host). |
| Activity heartbeat | GPIO25 drives the WeAct onboard LED through uCNC's `ACTIVITY_LED` output. |
| Soldered PSRAM | 8 MiB detected; data, inverse-data and address patterns passed over the complete range. |
| LVDS/HSTX video | NCC boot picture and work screen visible and stable on the panel. |
| Isolated E-stop | Dedicated GPIO9 input is active-low and releases to `Idle` when the loop is closed. |
| SD card | SPI card mounts as `/D` and directory listing works with the main PSU enabled. |
| Three-axis motion path | A0-A2 interpolation and STEP/DIR/shared-enable signals observed through the shift-register output path. |
| General outputs | D01-D16 static patterns and individual shift-register bits verified. |
| Input shift chain | The 32-bit 74HC165 value is read and displayed on the NCC diagnostic row. |
| Spindle analog path | AO0 spindle PWM tested: `M3 S450` produced 4.68 V on J25 with `$30=1000`. |
| Defaults and settings reset | `$RST=*` restores defaults and is accepted by the controller. |
| I2C | The board I2C path communicates. |

## Bench configuration

- Firmware target: `RP2350-LEANCAM-LVDS-NCC`.
- Controller: three axes, A0-A2.
- PSRAM chip select: GPIO0, 8 MiB.
- NC panel: `ncc`, portrait 600x800.
- During motion testing, D01-D07 stood in for A0-A2 STEP, DIR and shared enable.

## Still open

- The physical-to-logical mapping of the general outputs and complete input
  chain is not final; the electrical paths work, but the reported labels and
  bit positions need to be reconciled.
- Real motor buffers and field connectors have not replaced the bench LED
  indicators for A0-A2.
- A3-A6 are documented by the carrier but are not configured in the current
  three-axis firmware.
- AI0-AI3 and AO1-AO3 have not been calibrated. AO0 has only the rough spindle
  voltage check above.
- SD cold-start behaviour with every PSU state, file write durability and the
  removable card socket still need the full machine checklist.
- Encoder channels, Wi-Fi, the remaining isolated inputs and the full 24 V
  field I/O matrix still need dedicated bench passes.
- The board remains a prototype. Independent hard-wired safety energy removal
  is required and has not been certified by this firmware bring-up.
