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
| J2 | 4-pin 3.5 mm | 1=`+12V_BL`, 2=GND, 3=`BL_PWM`, 4=switched `BL_LED_N` |
| J4 | 1x4 2.54 mm SWD | 1=3.3 V, 2=SWDIO, 3=SWCLK, 4=GND |
| J5 | 2-pin 3.5 mm | 1=dedicated E-stop loop, 2=isolated safety common |
| J6 | 2-pin 3.5 mm | 1=HOLD button loop, 2=isolated control common |
| J7 | 8-pin 3.5 mm paired | FIELD_IN9-12 plus alternating isolated common 0 |
| J8 | 8-pin 3.5 mm paired | FIELD_IN1-4 plus alternating isolated common 1 |
| J9 | 1x6 2.54 mm | 1=GND, 2=+3.3 V, 3-6=`EXP_IN0`-`EXP_IN3` |
| J10 | 1x4 3.5 mm | 1=AX0_EN, 2=AX0_STEP, 3=AX0_DIR, 4=GND |
| J11 | 1x4 3.5 mm | 1=AX1_EN, 2=AX1_STEP, 3=AX1_DIR, 4=GND |
| J12 | 8-pin 3.5 mm | 1-8=DO0-DO7 open-collector |
| J13 | 5-pin 3.5 mm encoder 0 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J14 | 5-pin 3.5 mm encoder 1 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J15 | 5-pin 3.5 mm encoder 2 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J16 | 2x8 2.54 mm | Odd pins=KIN0-KIN7, even pins=KOUT0-KOUT7 |
| J17 | 1x3 2.54 mm | 1=+5 V, 2=GND, 3=GND |
| J18 | 4-pin 3.5 mm I2C | 1=SDA, 2=SCL, 3=+3.3 V, 4=GND |
| J19 | Full-size SD | SPI mode, push-pull 3.3 V card interface, card detect |
| J20 | 2x4 2.54 mm socket | ESP-01/ESP-01S: 1=GND, 2=3V3, 3=GPIO2, 4=GPIO0, 5=RX, 6=TX, 7=EN/CH_PD, 8=RST |
| J22 | 2x10 2.00 mm LCD | 1-3=3.3 V, 4-6=GND, 7/8=D0-/+, 9/10=D1-/+, 11/12=D2-/+, 13/14=GND, 15/16=CLK-/+, 17-20=NC |
| J24 | 5-pin 3.5 mm analog in | 1=AI0, 2=GND, 3=AI1, 4=GND, 5=AI2 |
| J25 | 5-pin 3.5 mm analog out | 1=GND, 2=AOUT0, 3=AOUT1, 4=AOUT2, 5=AOUT3 |
| J26 | 2-pin 3.5 mm | 1=START button loop, 2=isolated control common |
| J27 | 1x6 2.54 mm | 1=GND, 2=+3.3 V, 3-6=`EXP_IN4`-`EXP_IN7` |
| J28 | 1x4 3.5 mm | 1=AX2_EN, 2=AX2_STEP, 3=AX2_DIR, 4=GND |
| J29 | 1x4 3.5 mm | 1=AX3_EN, 2=AX3_STEP, 3=AX3_DIR, 4=GND |
| J30 | 1x4 3.5 mm | 1=AX4_EN, 2=AX4_STEP, 3=AX4_DIR, 4=GND |
| J31 | 2-pin 3.5 mm | 1=AUX, 2=GND |
| J32 | 8-pin 3.5 mm | 1-8=DO8-DO15 open-collector/low-side; DO_COM and GND are shared through J12 |
| J33 | 2-pin 3.5 mm | 1=DO_COM field +V, 2=GND |
| J34 | 8-pin 3.5 mm paired | FIELD_IN13-16 plus alternating isolated common 0 |
| J35 | 8-pin 3.5 mm paired | FIELD_IN5-8 plus alternating isolated common 1 |
| J36 | Molex 104031-0811 microSD | Alternate for J19; shares SPI, power and detect nets |

JP5 is an open two-pad solder jumper between `SD_CD` and `SD_CD_MCU`. Bridge
it to connect the SD-card detect switch to GPIO2. The jumper uses the original
1206 pad spacing for easy hand soldering and is excluded from the BOM.

J36 is an off-board DNP microSD alternative sharing the J19 SPI, power,
ground and card-detect nets. Populate exactly one of J19 or J36.

J4 intentionally omits debugger reset. The WeAct module's onboard reset button
controls the RP2350. All four 74HC595 `~SRCLR` pins are tied to `+3V3`, so a
processor reset does not clear their shift registers; firmware must shift and
latch a safe output word after reset, while machine-safe output blocking remains
external.

## Field-connector standardization

The board-side pluggable field-connector family is the Phoenix `MCV 1,5`
3.5 mm vertical series. The implemented inventory is limited to four position
counts:

| Positions | Intended use |
|---:|---|
| 2 | Power input, buttons and auxiliary output |
| 4 | One motion-axis connector |
| 5 | One encoder or the analog-output group |
| 8 | One PLC input/output bank |

The former larger field connectors are converted as follows:

- J7/J8: each 16-position input bank becomes two 8-position connectors.
- J12: DO0-DO7 use one 8-position connector; DO_COM/GND use J33, a 2-position
  connector.
- J24 uses the 5-position standard because three analog inputs need only two
  shared ground terminals.
- J32 uses the 8-position standard.

Splitting every 8-position connector into two 2x4 boards is not part of the
preferred plan. It keeps the same eight electrical positions while introducing
another physical connector format, more board area and more mating operations.
SD, LCD, SWD, ESP and other logic-level headers remain purpose-specific
and are excluded from the field-terminal inventory.

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

Each group of four PLC inputs uses one LTV-847S SOIC-16W optocoupler. Four
isolated 4x10 k networks provide the PLC pull-ups, while the dedicated E-stop,
HOLD and START channels use individual EL3H7 DIP-4 optocouplers and retain
discrete 4.7 k pull-ups to `+3V3`. No input-node capacitors are fitted.
Firmware must debounce the sampled contacts.

J5 is a dedicated E-stop connector and drives GPIO37 directly. J6 is the HOLD
input on GPIO38; J26 is the START input on GPIO39. They are not input-chain
bits. Output blocking is external.
J9 and J27 expose the spare 74HC165 byte as two direct 3.3 V logic groups with
10 k pulldowns. Each carries GND, +3.3 V and four inputs; do not connect field
voltage to either connector.

The verified J22 pinout has no backlight contact. MOD1 GPIO35 drives `BL_PWM`
on the separate J2 backlight connector at 3.3 V logic level. J2 pin 1 supplies
the U3-derived `+12V_BL` rail to the backlight/CCFL assembly. Backlight current
switching and any CCFL inverter remain external. GPIO35/MOD1 pin 25 drives
`BL_PWM_MCU`; R131 provides 100 ohm series protection to J2 pin 3, while R129
branches from the same MCU-side node to the Q8 gate. Q8 provides the optional
switched LED return on pin 4.

J9 and J27 flank U7 on the front side. J16 remains on the front side above the
mid-board area, with KOUT arrays above it and KIN arrays below it.

J24 is the 0-10 V analog input connector. J25 provides four ground-referenced
0-10 V outputs sharing pin 1 as the return. The outputs are functional signals,
not isolated outputs.
