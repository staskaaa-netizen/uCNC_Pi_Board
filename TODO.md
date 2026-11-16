# Release and validation checklist

## Prototype manufacturing order

The current PCB fabrication and SMT assembly packages are ready to send. The
remaining four silkscreen warnings are accepted as non-blocking for the
prototype: two microSD outline/pad conflicts and two dense LVDS legend
text-height warnings.

- [x] Generate the BOM, CPL, Gerbers, drills, PDFs and 3D renders from the
  current committed board.
- [x] Confirm 235 SMT BOM and CPL references match.
- [x] Run final DRC with zero errors and zero unconnected items.
- [x] Inspect both 3D sides and the manufacturing views.

## Post-build validation and production hardening

These checks apply after the prototype arrives and before production or
machine integration:

- Recheck the isolated field creepage and clearance against the intended
  enclosure and pollution degree.
- Confirm the target LCD cable, panel lane polarity and 330 ohm series value.
- Confirm the selected Phoenix `MCV 1,5` connector family and mating plugs.
- Verify the SOFNG TF-15x15 `C111196` socket against the ordered part.
- Review the BOM substitutes and assembly notes with the manufacturer.
- Bench-test every supply rail before fitting MOD1, J54 or an ESP module.

## Firmware integration

- The LeanCam-specific uCNC board map is implemented from
  `documentation/gpio-map.md` and `documentation/io-bit-map.md`.
- GPIO20/21/22 remain contiguous for the optional four-register 74AHCT595 PIO
  output path.
- The combined four-register 74HC165/74AHCT595 scan path is configured and
  software-verified by a clean firmware build.
- [x] Bench-test the four-register scan and three-axis motion timing on Batch 1.
- Implement separate PIO input scanning for the four 74HC165 registers.
- Generalize the RP2350 PIO encoder backend if ENC1 and ENC2 are needed.
- Active-low E-stop polarity on GPIO9 is configured.
- The non-sequential A4/A6 motion-bit remap is implemented.
- The soldered WEACT 8 MiB PSRAM passed full-range data/address tests.
- [x] Bring up LVDS video, NCC, SD mounting, dedicated E-stop and GPIO25
  heartbeat on Batch 1.
- [x] Verify D01-D16 shift-register static output control and the 32-bit input
  chain read path.
- [x] Rough-test AO0 through the spindle path (`S450` gives 4.68 V).
- Calibrate all four 0-10 V outputs against J25 after assembly.
- Remove WeAct module resistor R16 when GPIO23 is used as the shift-register
  input return.

## Manufacturing release

- Rerun and archive ERC and DRC after any further copper or placement edit.
- Regenerate every dependent manufacturing artifact after any board change.
- Keep the board marked as a prototype until the external hard-wired safety
  circuit and machine integration have been validated.
