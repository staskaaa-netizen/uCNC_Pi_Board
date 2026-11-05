# Assembly notes

## PCB

- Two-layer, 160 mm x 120 mm FR-4 board, 1.6 mm nominal thickness.
- Four M3 mounting holes.
- Main assembly and J22 are on F.Cu.
- MOD1 uses four 1 x 15, 2.54 mm female sockets on the carrier and matching male
  pin headers on the WeAct module. These headers are assembly hardware rather
  than electrical BOM lines.
- B.Cu is used for routing and the continuous GND region.
- No test points are fitted; use connector pins or accessible component pads.
- Manufacturing files are in `manufacturing/`.

## Power build

- U1 is the LMR36510 5 V, 1 A synchronous buck for the WeAct module, logic
  regulators, encoders and other 5 V loads.
- U2 is the peripheral AMS1117-3.3 regulator for logic, SD, encoder translation
  and the LCD 3.3 V rail.
- U34 is a separate AMS1117-3.3 regulator for the optional ESP module.
- U3 is the isolated LMR36510 24 V to 12 V backlight supply.
- U37 is the L78L12 regulator for the four-channel analog-output amplifier.
- D1 clamps the 12-24 V main input, F1 limits the main input branch and D2
  provides reverse-polarity protection.
- F2 limits the encoder 5 V branch. D53 clamps that branch.
- D3 protects the isolated backlight-converter input from the field rail.

The WeAct module's onboard reset button, power-on reset, brownout detector and
3.3 V regulator are used. Do not add a second motherboard reset or MCU
supervisor.

## Logic population

- U6-U9 are 74HC165D input registers at `3V3`.
- U10-U13 are SN74AHCT595DR output registers at `5V`.
- U28 is an SN74AHCT541DW encoder receiver at `3V3`.
- U42/U43 are onsemi MC74AC541DWR2G wide-body SOIC-20 motion buffers at `5V`,
  using the `SOIC-20W_7.5x12.8mm_P1.27mm` footprint.
- U26/U27 are TBD62083AFG low-side output arrays.
- U18-U21 are TLP291-4 PLC input optocouplers.
- U35 is the dedicated E-stop TLP291.
- U61-U64 are TLP291-4 general-output optocouplers.
- U38 is the TLV2374 quad analog-output amplifier.

The 74AHCT595 inputs accept the RP2350 3.3 V control levels at 5 V supply. Tie
their `~OE` and `~SRCLR` pins to their supply as implemented in the schematic.

## Passive standards

- General 100 nF and 1 uF bypasses: 0805.
- 10 uF capacitors: 1206, 25 V X7R.
- 100 nF / 100 V input bypasses: 1206.
- 22 uF bulk capacitors: 1210, 10 V on 5 V/3.3 V rails, 25 V on 12 V rails
  and an approved 35 V X5R substitution on the nominal 24 V input rails.
- Switching inductors: L1/L2 are SXN SMNR5040 5 x 5 x 4 mm parts.
- Analog divider resistors: 1206, 1%.
- Analog signal and feedback resistors: 0805, 1%.
- Field 2.2 k LED/input resistors: 1206.
- PLC pull-ups: RN32-RN35, 4 x 10 k, 4 x 0603.
- Output-register pull-downs: RN8-RN13, RN30 and RN31, 4 x 10 k.
- Output-opto drive networks: RN37-RN40, 4 x 1 k, 4 x 1206.
- All indicators: Lite-On `LTST-C150KGKT`, green 1206 LED.
- SD pull-ups: RN43, 4 x 10 k.
- SD series resistors: RN44, 4 x 22 ohm.
- LVDS series resistors: RN26/RN27, 4 x 330 ohm, 4 x 0603.

The 5 V and 3.3 V 22 uF bulk capacitors use 10 V parts, the 12 V rails use
25 V parts, and the 24 V-side input capacitors use 50 V or 100 V ratings as
listed in the BOM.

## SD-card population

J36 is a 1 x 9 header for the passive Open-Smart 3.3 V TF Card Breakout. J54 is
the on-board SOFNG TF-15x15 `C111196` socket. Both are wired to the same SPI
signals and can be populated together, but only one card source may be used at
a time.

The selected breakout or socket must use 3.3 V only and must not contain a 5 V
regulator or level shifter. RN43 pulls up CS, MOSI, MISO and card detect. RN44
provides 22 ohm series resistors on CS, MOSI, MISO and SCK. Close JP5 to enable
the card-detect switch to GPIO2.

## WeAct module preparation

The socket accepts a WeAct Studio RP2350B Core Board. Before fitting the module:

- Remove module resistor R16 to isolate GPIO23 from the onboard USER-key
  network. GPIO23 is the 74HC165 serial input return.
- Do not use the onboard USER key as a machine control or override its attached
  network.
- GPIO25 also drives the module's onboard LED.
- Leave module PSRAM chip-select GPIO0 free for the module's solderable PSRAM.
- GPIO61-GPIO64 debug pads are not connected to the motherboard.

The module's USB connector is oriented toward the accessible board edge.

## ESP-01 / ESP-01S

J20 accepts the original ESP-01 or ESP-01S. The module is optional; the
motherboard operates without it. GPIO2, GPIO0, EN and RST have 10 k pull-ups in
the `WIFI_3V3` domain.

For UART programming, ground ESP GPIO0 externally, reset the module, release
GPIO0 and program it through the socket. Keep the antenna end toward the board
perimeter with at least 15 mm of copper- and component-free clearance.

## First power-up

1. Inspect the isolated input side and confirm that `PLC_0V` is not connected
   to logic GND.
2. Verify the +5 V, +3.3 V, AO_12V and isolated BL_12V rails on current-limited
   bench supplies before fitting MOD1, an ESP module or a card.
3. Set the machine input to 24 V after the low-voltage rails are verified.
4. Confirm the main converter and analog regulator temperatures under load.
5. Calibrate all four 0-10 V outputs against J25.
6. Validate E-stop response and external hard-wired energy removal separately.

## Safety

The E-stop is a controller input and does not locally remove motor or output
power. Motor power, hazardous output supplies and any certified safety function
must be handled by external hard-wired safety hardware.
