# Connector map

Field-side 3.5 mm connectors use Phoenix `MCV 1,5` vertical footprints.
Verify connector body, keying and vertical entry height before substituting a
different supplier.

## Field connectors

| Ref | Size | Pinout / function |
|---|---|---|
| J1 | 2-pin 3.5 mm | 1=24V +, 2=24V - |
| J2 | 2-pin 3.5 mm | 1=BL 12+, 2=PLC - |
| J5 | 2-pin 3.5 mm | 1=ESTOP, 2=PLC - |
| J7 | 1 x 8, 3.5 mm | 1=I01, 2=I02, 3=I03, 4=I04, 5=I05, 6=I06, 7=I07, 8=I08 |
| J8 | 1 x 8, 3.5 mm | 1=I09, 2=I10, 3=I11, 4=I12, 5=I13, 6=I14, 7=I15, 8=I16 |
| J10 | 1 x 3, 3.5 mm | 1=`EN3`, 2=STP0, 3=DIR0 |
| J11 | 1 x 3, 3.5 mm | 1=`EN3`, 2=STP1, 3=DIR1 |
| J12 | 1 x 8, 3.5 mm | 1=D01, 2=D02, 3=D03, 4=D04, 5=D05, 6=D06, 7=D07, 8=D08 |
| J13 | 1 x 5, 3.5 mm | 1=5V, 2=A, 3=B, 4=Z, 5=- |
| J14 | 1 x 5, 3.5 mm | 1=5V, 2=A, 3=B, 4=Z, 5=- |
| J15 | 1 x 5, 3.5 mm | 1=5V, 2=A, 3=B, 4=Z, 5=- |
| J28 | 1 x 3, 3.5 mm | 1=`EN3`, 2=STP2, 3=DIR2 |
| J29 | 1 x 3, 3.5 mm | 1=`EN4`, 2=STP3, 3=DIR3 |
| J30 | 1 x 3, 3.5 mm | 1=`EN4`, 2=STP6, 3=DIR6 |
| J32 | 1 x 8, 3.5 mm | 1=D09, 2=D10, 3=D11, 4=D12, 5=D13, 6=D14, 7=D15, 8=D16 |
| J33 | 2-pin 3.5 mm | 1=PLC 24+, 2=PLC - |
| J40 | 1 x 3, 3.5 mm | 1=-, 2=A0 ERR, 3=A0 Z |
| J41 | 1 x 3, 3.5 mm | 1=-, 2=A1 ERR, 3=A1 Z |
| J42 | 1 x 3, 3.5 mm | 1=-, 2=A2 ERR, 3=A2 Z |
| J43 | 1 x 3, 3.5 mm | 1=-, 2=A3 ERR, 3=A3 Z |
| J45 | 2-pin 3.5 mm | 1=PLC 24+, 2=PLC - |
| J46 | 1 x 3, 3.5 mm | 1=`EN4`, 2=STP5, 3=DIR5 |
| J47 | 1 x 3, 3.5 mm | 1=`EN4`, 2=STP4, 3=DIR4 |
| J48 | 1 x 3, 3.5 mm | 1=-, 2=A6 ERR, 3=A6 Z |
| J49 | 1 x 3, 3.5 mm | 1=-, 2=A5 ERR, 3=A5 Z |
| J50 | 1 x 3, 3.5 mm | 1=-, 2=A4 ERR, 3=A4 Z |

Verified main-input polarity: J1 pin 1 is `VIN` and pin 2 is `GND`.
The fuse and D1/D2 protection are on the pin-1 branch.

The motion output map is physically consistent across all seven connectors:
pin 1 is the grouped enable, pin 2 is STEP and pin 3 is DIR. The matching
status connector uses pin 1 for 0 V, pin 2 for ERROR and pin 3 for ZERO.

PLC input numbering is direct: J7 pin `n` is `I0n`, and J8 pin `n` is
`I(8+n)` using two digits. PLC output numbering is also one-based: J12 pin
`n` is `D0n`, and J32 pin `n` is `D(8+n)`.

J33 and J45 provide parallel access to PLC 24+ and PLC -. The PLC domain
supplies the contact loops, output optocoupler side and isolated backlight
converter input. It is not connected to motherboard GND.

J7/J8 carry PLC signals only. Use the `PLC_24V` terminal from J33 or J45 for
the other side of each dry-contact loop.

## Logic and mixed connectors

| Ref | Type | Pinout / function |
|---|---|---|
| J18 | 1 x 5, 3.5 mm | 1=SDA, 2=SCL, 3=3V3, 4=5V, 5=- |
| J20 | 2 x 4, 2.54 mm socket | ESP-01/ESP-01S module socket |
| J22 | 2 x 10, 2.00 mm | LCD LVDS and logic supply |
| J24 | 1 x 5, 3.5 mm | 1=-, 2=AI0, 3=AI1, 4=AI2, 5=AI3 |
| J25 | 1 x 5, 3.5 mm | 1=-, 2=AO0, 3=AO1, 4=AO2, 5=AO3 |
| J36 | 1 x 9, 2.54 mm | microSD header |
| J51 | 1 x 7, 2.54 mm socket | 3V3, -, IO4-IO8 |
| J54 | SOFNG TF-15x15 | On-board microSD socket, LCSC `C111196` |

## J20 ESP socket

| Pin | Signal |
|---:|---|
| 1 | GND |
| 2 | `WIFI_3V3` |
| 3 | ESP GPIO2 with 10 k pull-up |
| 4 | ESP GPIO0 with 10 k pull-up |
| 5 | RP2350 GPIO11 `UART_RX` |
| 6 | RP2350 GPIO10 `UART_TX` |
| 7 | EN/CH_PD with 10 k pull-up |
| 8 | RST with 10 k pull-up |

## J22 LCD LVDS

| Row | Left pin | Right pin | Signal |
|---:|---|---|---|
| 1 | 1 | 2 | `3V3` |
| 2 | 3 | 4 | `3V3` / `GND` |
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
| 4 | `SD_3V3` |
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
| 1 | `3V3` |
| 2 | GND |
| 3 | GPIO4 |
| 4 | GPIO5 |
| 5 | GPIO6 |
| 6 | GPIO7 |
| 7 | GPIO8 |

GPIO4/6/8 are on MOD1 pins 35/36/37. GPIO5/7 are on MOD1 pins 51/52.
