# First-board NCC firmware

`uCNC-NCC-RP2350B-first-board-working-20261117.uf2` is the validated
RP2350B NCC image for Batch 1 boards.

## Flash

1. Disconnect the board.
2. Hold `BOOTSEL` while reconnecting USB.
3. Copy the UF2 to the mounted `RP2350` drive.
4. The board reboots automatically into uCNC.

## Source

- uCNC source snapshot: `a36bbfda`
- Target: `RP2350-LEANCAM-LVDS-NCC`
- Hardware: WeAct RP2350B core on the LeanCam NCC motherboard

The image was bench-validated on the assembled Batch 1 board. Preserve an
independent hardware safety path; this firmware is not a safety-rated
controller.

## Checksum

```text
SHA256 AEFEAC3D6C135B12C48A9DA5048C751CEC3450307540928A487BD3381A2E7430
```
