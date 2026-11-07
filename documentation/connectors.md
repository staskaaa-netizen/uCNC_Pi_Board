# Connector map

Field-side 3.5 mm connectors use Phoenix `MCV 1,5` vertical footprints.
Verify connector body, keying and vertical entry height before substituting a
different supplier.

## Field connectors

| Ref | Size | Pinout / function |
|---|---|---|
| J1 | 2-pin 3.5 mm | GND, 24+ (PCB label order) |
| J2 | 2-pin 3.5 mm | PLC_0V, BL12+ (PCB label order) |
| J5 | 2-pin 3.5 mm | ESTOP, PLC - |
| J7 | 1 x 8, 3.5 mm | I01, I02, I03, I04, I05, I06, I07, I08 |
| J8 | 1 x 8, 3.5 mm | I09, I10, I11, I12, I13, I14, I15, I16 |
| J10 | 1 x 3, 3.5 mm | `EN3`, STP0, DIR0 |
| J11 | 1 x 3, 3.5 mm | `EN3`, STP1, DIR1 |
| J12 | 1 x 8, 3.5 mm | D01, D02, D03, D04, D05, D06, D07, D08 |
| J13 | 1 x 5, 3.5 mm | +5V, A0, B0, Z0, GND |
| J14 | 1 x 5, 3.5 mm | +5V, A1, B1, Z1, GND |
| J15 | 1 x 5, 3.5 mm | +5V, A2, B2, Z2, GND |
| J28 | 1 x 3, 3.5 mm | `EN3`, STP2, DIR2 |
| J29 | 1 x 3, 3.5 mm | `EN4`, STP3, DIR3 |
| J30 | 1 x 3, 3.5 mm | `EN4`, STP6, DIR6 |
| J32 | 1 x 8, 3.5 mm | D09, D10, D11, D12, D13, D14, D15, D16 |
| J33 | 2-pin 3.5 mm | PLC24+, PLC_0V |
| J40 | 1 x 3, 3.5 mm | GND, ERR0, Z0 |
| J41 | 1 x 3, 3.5 mm | GND, ERR1, Z1 |
| J42 | 1 x 3, 3.5 mm | GND, ERR2, Z2 |
| J43 | 1 x 3, 3.5 mm | GND, ERR3, Z3 |
| J45 | 2-pin 3.5 mm | PLC_0V, PLC24+ (PCB label order) |
| J46 | 1 x 3, 3.5 mm | `EN4`, STP5, DIR5 |
| J47 | 1 x 3, 3.5 mm | `EN4`, STP4, DIR4 |
| J48 | 1 x 3, 3.5 mm | GND, ERR6, Z6 |
| J49 | 1 x 3, 3.5 mm | GND, ERR5, Z5 |
| J50 | 1 x 3, 3.5 mm | GND, ERR4, Z4 |

Verified main-input polarity: J1 pin 1 is `VIN` and pin 2 is `GND`.
The fuse and D1/D2 protection are on the pin-1 branch.

J1, J2 and J45 are rotated 180 degrees on the PCB. Their visible labels are
deliberately written in physical left-to-right order:

- J1: `GND 24+`, while pad 1 is still `24+` and pad 2 is `GND`.
- J2: `PLC_0V BL12+`, while pad 1 is still `BL12+` and pad 2 is `PLC_0V`.
- J45: `PLC_0V PLC24+`, while pad 1 is still `PLC24+` and pad 2 is `PLC_0V`.

J33 has the opposite footprint orientation and therefore remains visibly
`PLC24+ PLC_0V`.

The motion output map is physically consistent across all seven connectors:
pin 1 is the grouped enable, pin 2 is STEP and pin 3 is DIR. The matching
status connector uses pin 1 for `GND`, pin 2 for ERROR and pin 3 for ZERO.
Because the motion connectors face the opposite direction, their PCB value
labels read `DIRn STPn ENx` from the physical connector edge. This changes
only the visible word order; the pin-to-net table above remains authoritative.

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
| J18 | 1 x 5, 3.5 mm | SDA, SCL, 3V3, 5V, - |
| J20 | 2 x 4, 2.54 mm socket | ESP-01/ESP-01S module socket |
| J22 | 2 x 10, 2.00 mm | LCD LVDS and logic supply |
| J24 | 1 x 5, 3.5 mm | -, AI0, AI1, AI2, AI3 |
| J25 | 1 x 5, 3.5 mm | -, AO0, AO1, AO2, AO3 |
| J36 | 1 x 9, 2.54 mm | microSD header |
| J51 | 1 x 7, 2.54 mm socket | 3V3, -, IO4-IO8 |
| J54 | SOFNG TF-15x15 | On-board microSD socket, LCSC `C111196` |

## J20 ESP socket

| Pin | Signal |
|---:|---|
| 1 | GND |
| 2 | RP2350 GPIO11 `UART_RX` to ESP TX |
| 3 | ESP GPIO2 |
| 4 | EN/CH_PD |
| 5 | ESP GPIO0 |
| 6 | RST |
| 7 | RP2350 GPIO10 `UART_TX` to ESP RX |
| 8 | `WIFI_3V3` |

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
