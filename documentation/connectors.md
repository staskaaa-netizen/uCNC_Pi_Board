# Connector map

Field-side 3.5 mm connectors use Phoenix `MCV 1,5` vertical footprints.
Verify connector body, keying and vertical entry height before substituting a
different supplier.

## Field connectors

| Ref | Size | Pinout / function |
|---|---|---|
| J1 | 2-pin 3.5 mm | 1=`VIN` 12-24 V, 2=`GND` |
| J2 | 2-pin 3.5 mm | 1=`+12V_BL`, 2=`ISO_GND` |
| J5 | 2-pin 3.5 mm | 1=E-stop loop, 2=`ISO_GND` |
| J7 | 1 x 8, 3.5 mm | 1-8=PLC inputs 1-8 |
| J8 | 1 x 8, 3.5 mm | 1-8=PLC inputs 9-16 |
| J10 | 1 x 3, 3.5 mm | 1=`EN_3AX`, 2=AX0_STEP, 3=AX0_DIR |
| J11 | 1 x 3, 3.5 mm | 1=`EN_3AX`, 2=AX1_STEP, 3=AX1_DIR |
| J12 | 1 x 8, 3.5 mm | 1-8=DO0-DO7 |
| J13 | 1 x 5, 3.5 mm | 1=+5 V, 2=ENC0_A, 3=ENC0_B, 4=ENC0_Z, 5=GND |
| J14 | 1 x 5, 3.5 mm | 1=+5 V, 2=ENC1_A, 3=ENC1_B, 4=ENC1_Z, 5=GND |
| J15 | 1 x 5, 3.5 mm | 1=+5 V, 2=ENC2_A, 3=ENC2_B, 4=ENC2_Z, 5=GND |
| J28 | 1 x 3, 3.5 mm | 1=`EN_3AX`, 2=AX2_STEP, 3=AX2_DIR |
| J29 | 1 x 3, 3.5 mm | 1=`EN_4AX`, 2=AX3_STEP, 3=AX3_DIR |
| J30 | 1 x 3, 3.5 mm | 1=`EN_4AX`, 2=AX4_STEP, 3=AX4_DIR |
| J32 | 1 x 8, 3.5 mm | 1-8=DO8-DO15 |
| J33 | 2-pin 3.5 mm | 1=`+24V_FIELD`, 2=`ISO_GND` |
| J40 | 1 x 3, 3.5 mm | 1=GND, 2=AX0_ERROR_N, 3=AX0_ZERO |
| J41 | 1 x 3, 3.5 mm | 1=GND, 2=AX1_ERROR_N, 3=AX1_ZERO |
| J42 | 1 x 3, 3.5 mm | 1=GND, 2=AX2_ERROR_N, 3=AX2_ZERO |
| J43 | 1 x 3, 3.5 mm | 1=GND, 2=AX3_ERROR_N, 3=AX3_ZERO |
| J45 | 2-pin 3.5 mm | 1=`+24V_FIELD`, 2=`ISO_GND` |
| J46 | 1 x 3, 3.5 mm | 1=`EN_4AX`, 2=AX5_STEP, 3=AX5_DIR |
| J47 | 1 x 3, 3.5 mm | 1=`EN_4AX`, 2=AX6_STEP, 3=AX6_DIR |
| J48 | 1 x 3, 3.5 mm | 1=GND, 2=AX4_ERROR_N, 3=AX4_ZERO |
| J49 | 1 x 3, 3.5 mm | 1=GND, 2=AX5_ERROR_N, 3=AX5_ZERO |
| J50 | 1 x 3, 3.5 mm | 1=GND, 2=AX6_ERROR_N, 3=AX6_ZERO |

J33 and J45 provide parallel access to the external isolated 24 V field rail
and its single `ISO_GND` return. The field domain supplies PLC contact wetting,
the output optocoupler side and the isolated backlight converter input. It is
not connected to motherboard GND.

J7/J8 carry PLC signals only. Use the `+24V_FIELD` terminal from J33 or J45 for
the other side of each dry-contact loop.

## Logic and mixed connectors

| Ref | Type | Pinout / function |
|---|---|---|
| J18 | 1 x 5, 3.5 mm | 1=SDA, 2=SCL, 3=+3.3 V, 4=+5 V, 5=GND |
| J20 | 2 x 4, 2.54 mm socket | ESP-01/ESP-01S module socket |
| J22 | 2 x 10, 2.00 mm | LCD LVDS and logic supply |
| J24 | 1 x 5, 3.5 mm | 1=GND, 2=AI0, 3=AI1, 4=AI2, 5=AI3 |
| J25 | 1 x 5, 3.5 mm | 1=GND, 2=AOUT0, 3=AOUT1, 4=AOUT2, 5=AOUT3 |
| J36 | 1 x 9, 2.54 mm | Open-Smart TF Card Breakout |
| J51 | 1 x 7, 2.54 mm socket | +3.3 V, GND, GPIO4-GPIO8 |
| J54 | SOFNG TF-15x15 | On-board microSD socket, LCSC `C111196` |

## J20 ESP socket

| Pin | Signal |
|---:|---|
| 1 | GND |
| 2 | `+3V3_WIFI` |
| 3 | ESP GPIO2 with 10 k pull-up |
| 4 | ESP GPIO0 with 10 k pull-up |
| 5 | RP2350 GPIO11 `WIFI_RX` |
| 6 | RP2350 GPIO10 `WIFI_TX` |
| 7 | EN/CH_PD with 10 k pull-up |
| 8 | RST with 10 k pull-up |

## J22 LCD LVDS

| Row | Left pin | Right pin | Signal |
|---:|---|---|---|
| 1 | 1 | 2 | `+3V3` |
| 2 | 3 | 4 | `+3V3` / `GND` |
| 3 | 5 | 6 | `GND` |
| 4 | 7 | 8 | D0- / D0+ |
| 5 | 9 | 10 | D1- / D1+ |
| 6 | 11 | 12 | D2- / D2+ |
| 7 | 13 | 14 | `GND` |
| 8 | 15 | 16 | CLK- / CLK+ |
| 9 | 17 | 18 | NC |
| 10 | 19 | 20 | NC |

Odd pins are the left column and even pins are the right column. J22 is mounted
on F.Cu.

## J36 TF-card breakout

| Pin | Signal |
|---:|---|
| 1 | CDN |
| 2 | DAT1 |
| 3 | DO / MISO |
| 4 | GND |
| 5 | SCLK |
| 6 | 3.3 V |
| 7 | DI / MOSI |
| 8 | CS |
| 9 | DAT2 |

Use the passive 3.3 V breakout. It must not contain a regulator or level
shifter.

## J54 SOFNG TF-15x15

| Pad | Signal |
|---:|---|
| 1 | DAT2 |
| 2 | CS |
| 3 | MOSI |
| 4 | `+3V3_SD` |
| 5 | SCK |
| 6 | GND |
| 7 | MISO |
| 8 | DAT1 |
| 9 | Card detect |
| 10-13 | Ground tabs |

The footprint was converted from the JLCEDA/EasyEDA Official Library and its
STEP/WRL models are stored under `hardware/libraries/3d/`.

J36 and J54 are electrically parallel. Both connectors may be fitted, but use
one card source at a time. JP5 is a standard open two-pad solder jumper in the
card-detect path; close it to connect detection to GPIO2.

## J51 expansion

| Pin | Signal |
|---:|---|
| 1 | `+3V3` |
| 2 | GND |
| 3 | GPIO4 |
| 4 | GPIO5 |
| 5 | GPIO6 |
| 6 | GPIO7 |
| 7 | GPIO8 |

GPIO4/6/8 are on MOD1 pins 35/36/37. GPIO5/7 are on MOD1 pins 51/52.
