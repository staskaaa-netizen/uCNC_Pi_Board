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
| J2 | 2-pin 3.5 mm | 1=`+12V_BL`, 2=`ISO_GND` |
| J5 | 2-pin 3.5 mm | 1=dedicated E-stop loop, 2=`ISO_GND` |
| J7 | 1x8 3.5 mm | `FIELD_IN1`-`FIELD_IN8` |
| J8 | 1x8 3.5 mm | `FIELD_IN9`-`FIELD_IN16` |
| J10 | 1x3 3.5 mm | 1=`EN_3AX`, 2=AX0_STEP, 3=AX0_DIR |
| J11 | 1x3 3.5 mm | 1=`EN_3AX`, 2=AX1_STEP, 3=AX1_DIR |
| J12 | 1x8 3.5 mm | 1-8=DO0-DO7 |
| J13 | 1x5 3.5 mm encoder 0 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J14 | 1x5 3.5 mm encoder 1 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J15 | 1x5 3.5 mm encoder 2 | 1=+5 V, 2=A, 3=B, 4=Z, 5=GND |
| J17 | 1x3 2.54 mm | 1=+5 V, 2=GND, 3=GND |
| J18 | 1x5 3.5 mm I2C1 | 1=SDA, 2=SCL, 3=+3.3 V, 4=+5 V, 5=GND |
| J20 | 2x4 2.54 mm socket | ESP-01/ESP-01S: 1=GND, 2=3V3, 3=GPIO2, 4=GPIO0, 5=RX, 6=TX, 7=EN/CH_PD, 8=RST |
| J22 | 2x10 2.00 mm LCD | 1-3=3.3 V, 4-6=GND, 7/8=D0-/+, 9/10=D1-/+, 11/12=D2-/+, 13/14=GND, 15/16=CLK-/+, 17-20=NC |
| J24 | 5-pin 3.5 mm analog in | 1=GND, 2=AI0, 3=AI1, 4=AI2, 5=AI3 |
| J25 | 5-pin 3.5 mm analog out | 1=GND, 2=AOUT0, 3=AOUT1, 4=AOUT2, 5=AOUT3 |
| J28 | 1x3 3.5 mm | 1=`EN_3AX`, 2=AX2_STEP, 3=AX2_DIR |
| J29 | 1x3 3.5 mm | 1=`EN_4AX`, 2=AX3_STEP, 3=AX3_DIR |
| J30 | 1x3 3.5 mm | 1=`EN_4AX`, 2=AX4_STEP, 3=AX4_DIR |
| J46 | 1x3 3.5 mm | 1=`EN_4AX`, 2=AX5_STEP, 3=AX5_DIR |
| J47 | 1x3 3.5 mm | 1=`EN_4AX`, 2=AX6_STEP, 3=AX6_DIR |
| J32 | 1x8 3.5 mm | 1-8=DO8-DO15 |
| J33 | 2-pin 3.5 mm | 1=external isolated field +24 V, 2=`ISO_GND` |
| J40 | 1x3 3.5 mm | 1=AX0_ZERO, 2=AX0_ERROR_N, 3=GND |
| J41 | 1x3 3.5 mm | 1=AX1_ZERO, 2=AX1_ERROR_N, 3=GND |
| J42 | 1x3 3.5 mm | 1=AX2_ZERO, 2=AX2_ERROR_N, 3=GND |
| J43 | 1x3 3.5 mm | 1=AX3_ZERO, 2=AX3_ERROR_N, 3=GND |
| J48 | 1x3 3.5 mm | 1=AX4_ZERO, 2=AX4_ERROR_N, 3=GND |
| J49 | 1x3 3.5 mm | 1=AX5_ZERO, 2=AX5_ERROR_N, 3=GND |
| J50 | 1x3 3.5 mm | 1=AX6_ZERO, 2=AX6_ERROR_N, 3=GND |
| J45 | 2-pin 3.5 mm | Parallel field +24 V / `ISO_GND` input, identical to J33 |
| J36 | 1x9 2.54 mm | Open-Smart TF Card Breakout: CDN, DAT1, DO, GND, SCLK, VCC=3.3 V, DI, CS, DAT2 |

JP5 is an open two-pad solder jumper between `SD_CD` and `SD_CD_MCU`. Bridge
it to connect the SD-card detect switch to GPIO2/MOD1 pin 34. The jumper uses the original
1206 pad spacing for easy hand soldering and is excluded from the BOM.

J36 is a 1x9 header for the passive Open-Smart TF Card Breakout. Its exact pin
order from pin 1 is `CDN`, `DAT1`, `DO`, `GND`, `SCLK`, `VCC`, `DI`, `CS`,
`DAT2`; `VCC` is 3.3 V only. The breakout must not include a 5 V regulator or
level shifter. The former full-size J19 and motherboard microSD sockets are
removed.

## Field-connector standardization

The board-side field-connector family uses the existing Phoenix `MCV 1,5`
3.5 mm vertical terminal blocks. Wider functions are split across stackable
single-row connectors:

| Positions | Intended use |
|---:|---|
| 2 | Power input, E-stop and field supply |
| 5 | I2C, one encoder or the analog-output group |
| 8 | One PLC signal half-bank |

The former larger field connectors are converted as follows:

- J7/J8 carry the eight PLC signals per bank; their return is the shared
  `ISO_GND` on J33/J45.
- J12/J32 carry the eight output signals; their field supply and return are
  shared on J33/J45.
- J33 and J45 provide parallel `+24V_FIELD` / `ISO_GND` field connections.
- J24 uses one shared ground on pin 1 followed by four analog-input channels.
The former 2x10 expansion-input connector J37 is removed. U8 carries PLC
inputs 1-8 and U9 carries PLC inputs 9-16. U6/U7 carry paired servo
ZERO/ERROR inputs.
SD, LCD, ESP and other logic-level headers remain purpose-specific
and are excluded from the field-terminal inventory.

The encoder A/B/Z inputs require 5 V push-pull outputs. They drive
`SN74AHCT541DW` inputs powered at 3.3 V through no series resistor, filter
capacitor or board-level ESD array. Encoders with open-collector outputs need
external pull-up resistors.

J5-J8 form dry-contact input loops. J33 and J45 provide parallel access to the
external isolated 24 V field rail and its single `ISO_GND` return. The isolated
field domain is not connected to motherboard GND. See
`documentation/input-wetting.md` for the field-wiring rules.

J7/J8 follow physical left-to-right channel numbering. Firmware must still use
the register bit permutation in `documentation/io-bit-map.md`.

Each group of four PLC inputs uses one TLP291-4 SOIC-16 optocoupler. Four
isolated 4x10 k networks provide the PLC pull-ups. The dedicated E-stop uses
one TLP291 SOP-4 optocoupler and a 4.7 k pull-up to `+3V3`. No input-node
capacitors are fitted. Firmware must debounce the sampled contacts.

J5 is the dedicated E-stop connector and drives GPIO9/MOD1 pin 53 directly. It is not an
input-chain bit. Output blocking is external.
Each axis has a 3-pin output connector (`EN, STEP, DIR`) and a paired 3-pin
input connector (`ZERO, ERROR, GND`). `EN_3AX` is shared by AX0-AX2;
`EN_4AX` is shared by AX3-AX6. J51 and the former AUX connector J31 are removed.

The verified J22 pinout has no backlight contact. U3 converts the J33/J45 PLC
24 V field supply to isolated `+12V_BL`; J2 carries only `+12V_BL` and
`ISO_GND`. Backlight PWM, current switching, CCFL inversion and PWM isolation
remain external.

J9 and J27 flank U7 on the front side. J16 remains on the front side above the
mid-board area, with KOUT arrays above it and KIN arrays below it.

J24 is the four-channel 0-10 V analog input connector with a shared ground on
pin 1. J25 provides four ground-referenced 0-10 V outputs sharing pin 1 as the
return. The outputs are functional signals, not isolated outputs.
