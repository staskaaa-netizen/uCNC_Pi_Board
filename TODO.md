# Release and validation checklist

## Prototype manufacturing order

The current PCB fabrication and SMT assembly packages are ready to send. The
remaining six silkscreen warnings are accepted as non-blocking for the
prototype: two microSD outline/edge conflicts, two microSD outline/pad
conflicts and two dense LVDS legend text-height warnings.

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

- Create the LeanCam-specific uCNC board map from
  `documentation/gpio-map.md` and `documentation/io-bit-map.md`.
- Keep GPIO20/21/22 contiguous for the optional four-register 74AHCT595 PIO
  output path.
- Implement or configure separate input scanning for the four 74HC165
  registers.
- Generalize the RP2350 PIO encoder backend if ENC1 and ENC2 are needed.
- Preserve active-low E-stop polarity on GPIO9.
- Implement the non-sequential A4/A6 motion-bit remap.
- Calibrate all four 0-10 V outputs against J25 after assembly.
- Remove WeAct module resistor R16 when GPIO23 is used as the shift-register
  input return.

## Manufacturing release

- Rerun and archive ERC and DRC after any further copper or placement edit.
- Regenerate every dependent manufacturing artifact after any board change.
- Keep the board marked as a prototype until the external hard-wired safety
  circuit and machine integration have been validated.
