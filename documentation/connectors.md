# Connector map

All field-side 3.5 mm positions use the Phoenix `MCV 1,5` vertical land pattern.
This keeps the mating plugs perpendicular to the PCB and reduces edge clearance
problems compared with the previous horizontal `MC 1,5` footprints. A supplier
KF2EDG-specific mechanical drawing was not available in the source set; clones
must not be substituted without comparing their body, keying and vertical entry
height to the Phoenix footprint.

| Ref | Type | Pinout / function |
|---|---|---|
| J1 | 2-pin 3.5 mm | 1=VIN 12-24 V, 2=GND |
| J4 | 1x5 2.54 mm SWD | 1=3.3 V, 2=SWDIO, 3=SWCLK, 4=GND, 5=RESET_N |
| J5 | 2-pin 3.5 mm | 1=dedicated E-stop loop, 2=isolated safety common |
| J6 | 2-pin 3.5 mm | 1=HOLD button loop, 2=isolated control common |
| J7 | 1x16 3.5 mm paired | Signal pins=FIELD_IN9-16 in physical positions 1-8, even pins=isolated common 0 |
| J8 | 1x16 3.5 mm paired | Signal pins=FIELD_IN1-8 in physical positions 1-8, even pins=isolated common 1 |
| J9 | 1x6 2.54 mm | 1=GND, 2=+3.3 V, 3-6=`EXP_IN0`-`EXP_IN3` |
| J10 | 1x4 3.5 mm | 1=AX0_EN, 2=AX0_STEP, 3=AX0_DIR, 4=GND |
| J11 | 1x4 3.5 mm | 1=AX1_EN, 2=AX1_STEP, 3=AX1_DIR, 4=GND |
| J12 | 10-pin 3.5 mm | 1-8=DO0-DO7 open-collector, 9=DO_COM field +V, 10=GND |
| J13 | 5-pin 3.5 mm encoder 0 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J14 | 5-pin 3.5 mm encoder 1 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J15 | 5-pin 3.5 mm encoder 2 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J16 | 2x8 2.54 mm | Odd pins=KIN0-KIN7, even pins=KOUT0-KOUT7 |
| J17 | 1x3 2.54 mm | 1=+5 V, 2=GND, 3=GND |
| J18 | 1x4 2.54 mm I2C | 1=SDA, 2=SCL, 3=+3.3 V, 4=GND |
| J19 | Full-size SD | SPI mode, push-pull 3.3 V card interface, card detect |
| J20 | 2x4 2.54 mm socket | ESP-01S: 1=GND, 2=3V3, 3=GPIO2, 4=GPIO0, 5=RX, 6=TX, 7=EN/CH_PD, 8=RST |
| J22 | 2x10 2.00 mm LCD | 1=GND, 2-4=3.3 V, 6=BL_PWM, 7=NC, 8/9=D0-/+, 11/12=D1-/+, 14/15=D2-/+, 17/18=CLK-/+, 10/13/16/19=GND |
| J23 | HDMI Type A | Standard TMDS pinout; DDC pulled to HDMI +5 V |
| J24 | 6-pin 3.5 mm analog in | 1=AI0, 2=GND, 3=AI1, 4=GND, 5=AI2, 6=GND |
| J25 | 5-pin 3.5 mm analog out | 1=GND, 2=AOUT0, 3=AOUT1, 4=AOUT2, 5=AOUT3 |
| J26 | 2-pin 3.5 mm | 1=START button loop, 2=isolated control common |
| J27 | 1x6 2.54 mm | 1=GND, 2=+3.3 V, 3-6=`EXP_IN4`-`EXP_IN7` |
| J28 | 1x4 3.5 mm | 1=AX2_EN, 2=AX2_STEP, 3=AX2_DIR, 4=GND |
| J29 | 1x4 3.5 mm | 1=AX3_EN, 2=AX3_STEP, 3=AX3_DIR, 4=GND |
| J30 | 1x4 3.5 mm | 1=AX4_EN, 2=AX4_STEP, 3=AX4_DIR, 4=GND |
| J31 | 2-pin 3.5 mm | 1=MOTION14/AUX, 2=GND |

The encoder A/B/Z inputs require 5 V push-pull outputs. They drive
`SN74AHCT541DW` inputs powered at 3.3 V through no series resistor, filter
capacitor or board-level ESD array. Encoders with open-collector outputs need
external pull-up resistors.

J5-J8 can operate as dry-contact inputs. U40 provides an isolated 12 V wetting
rail for direct pair closure, while bottom-side three-pin header selectors can instead
leave each bank configured for an external 24 V wetting supply. The isolated
output is not connected to motherboard GND. See
`documentation/input-wetting.md` for the exact JP2-JP4 bridge table.

J7/J8 are arranged by shortest PCB fanout, not logical numbering. Firmware
must use the position-to-bit permutation in `documentation/io-bit-map.md`.

Each group of four PLC inputs uses one LTV-847S SOIC-16W optocoupler. The
dedicated E-stop, HOLD and START channels use separate EL3H7 DIP-4 optocouplers.
Every used output has one individual 4.7 k pull-up to `+3V3`. No input-node
capacitors or pull-up arrays are fitted. Firmware must debounce the sampled
contacts.

J5 is a dedicated E-stop connector and drives GPIO37 directly. J6 is the HOLD
input on GPIO38; J26 is the START input on GPIO39. They are not input-chain
bits. Output blocking is external.
J9 and J27 expose the spare 74HC165 byte as two direct 3.3 V logic groups with
10 k pulldowns. Each carries GND, +3.3 V and four inputs; do not connect field
voltage to either connector.

The local backlight power switch, J2 and JP1 are removed. J22 pin 6 exposes
`BL_PWM` directly; the external display/backlight module owns power switching.

J9 and J27 flank U7 on the front side. J16 remains on the front side above the
mid-board area, with KOUT arrays above it and KIN arrays below it.

J24 is the 0-10 V analog input connector. J25 provides four ground-referenced
0-10 V outputs sharing pin 1 as the return. The outputs are functional signals,
not isolated outputs.
