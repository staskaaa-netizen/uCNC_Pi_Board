# LeanCam motherboard follow-up work

## Component placement, one element at a time

- Component classification is complete in
  `hardware/component-placement-manifest.csv`.
- AI0, AI1 and AI2 are all placed beside J24 using the same three-part template.
- PLC input groups use four-channel LTV-847S SOIC-16W optocouplers. The
  dedicated controls use individual EL3H7 DIP-4 parts: U35 (E-stop),
  U36 (HOLD) and U39 (START). Every used channel has one individual 4.7 k
  pull-up and firmware debouncing.
- All 16 PLC field-side resistor/LED/reverse-diode chains are placed at J7/J8.
- The E-stop and HOLD chains, U35/U36 and their R74/R75 pull-ups remain grouped
  beside J5/J6. START/J26/U39/R108/R109/D54/D55 are added and await manual
  placement.
- Analog channels now use one 100 k upper and one 33 k lower resistor; keep
  each divider/filter group next to J24, not beside the RP2350.
- Four 0-10 V outputs are implemented through one TLV2374 quad op-amp and
  sixteen individual 0805 resistors for the filters and feedback. They use
  GPIO47 and GPIO44-GPIO46 and the new J25 connector. SD-card detect moved to
  GPIO2 by swapping MOD1 pins 34 and 19.
- Add one input channel first: field connector pin, reverse diode, LED, series
  resistor, optocoupler channel, pull-up and ADC-side filter.
- Measure placement DRC, local airwire length and crossings after that single
  channel before adding another.
- Repeat for each remaining input channel only after the first channel matches
  the intended reference geometry.
- Place passives one at a time around their actual IC pins. Do not run a bulk
  automatic placement pass over already approved modules.
- Place decoupling capacitors and other passive networks individually after
  their associated channel is fixed; verify each before continuing.
- Add motion and ULN output channels one at a time in the same way.
- Keep all ICs fixed unless a separate approved placement change explicitly
  allows movement.
- Do not start Freerouting before the completed placement is approved.
- Route and validate the four analog output channels after their placement is
  approved; bench-calibrate maximum PWM duty against J25.

## uCNC and RP2350 programmability audit

- The stock uCNC RP2350/Pico 2 board map does not match this board; a
  LeanCam-specific board map is required.
- The normal uCNC `shift_register` driver supports both 74HC165 and 74HC595 on
  arbitrary GPIOs and remains the complete bit-banged runtime path.
- The optional uCNC 595 PIO path uses GPIO20/21/22 in the required
  DATA/CLK/LATCH order. It drives only the four 595 outputs; add separate or
  custom PIO input scanning before selecting that path for the complete board.
- Stock uCNC encoders use GPIO interrupts rather than PIO. All nine A/B/Z pins
  GP26-GP34 are compatible as PULSE/DIR/INDEX. A custom PIO quadrature decoder
  remains optional firmware work.
- Confirm direct `ESTOP_N`, `HOLD_N` and `START_N` polarity against uCNC.
- Check for conflicts between PIO pin groups, ADC pins, UART, SPI, HSTX,
  SWD and the onboard PSRAM chip select.
- Produce a firmware-facing pin and bit map that includes the RN16/RN17 output
  pair swaps and physical shift-register Q-pin assignments.
- Implement the checkpoint-57 connector-position and 74HC165 PLC input
  permutation from `documentation/io-bit-map.md` in the LeanCam board map.
- Bench-check the calculated 24 V/12 V input currents and LTV-847S saturation
  at temperature; each three-pad selector must use only one bridge position.
- Validate the resulting assumptions against the actual uCNC source before
  routing or manufacturing release.
- Re-evaluate the DTU autoplacer only with a restricted movable set or after
  correcting its footprint-clearance handling; its first full-board run produced
  502 DRC violations and substantially worse connectivity.

## Display alternatives

- Add a DS90LV047A active-LVDS driver as an alternate population to the two
  4x330R passive LVDS arrays.
- Feed it only the four single-ended HSTX signals: D0, D1, D2 and clock.
- Tie `EN` active-high and complementary `~EN` active-low so the driver is
  permanently enabled; add local +3V3 decoupling.
- Make the driver and RN26/RN27 mutually exclusive, using the verified display
  connector pinout in `documentation/display-population.md`.
- Do not fit this option in the current passive-LCD build.

## Connector standardization

- Limit board-side pluggable field terminals to Phoenix `MCV 1,5` 3.5 mm
  connectors in 2-, 4-, 5- and 8-position variants.
- Split each 16-position PLC bank into two 8-position connectors.
- Split J12 into one 8-position output connector plus one 2-position
  `DO_COM`/GND connector.
- Keep J24 on the 5-position standard as `AI0/GND/AI1/GND/AI2`; three
  analog inputs need only two shared ground terminals.
- Do not convert 8-position groups to two 2x4 connectors; this adds a fourth
  physical format without reducing useful pin count.

## Incremental routing

- Routed first channel: `OUT9`, U11 pin 1 to U25 pin 9, F.Cu, 0.25 mm.
- Completed first motion output path: OUT0/BUFY0/MOTION1 through U10, U24,
  RN8, RN16 and J10.
- Completed first isolated PLC input path for input 0 through R18, D13, D14,
  U18, C33, RN2 and U9.
- Continue one short channel or functional group at a time and run DRC after
  each group.
- Do not run Freerouting until incremental manual routing has been reviewed.
