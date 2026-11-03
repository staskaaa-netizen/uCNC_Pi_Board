# Digital chain and bit map

## Input register chain

The physical chain is:

`U6 Q7 -> U7 DS -> U8 DS -> U9 DS -> MOD1 GPIO23`

Clock all four 74HC165D registers from GPIO21. Pulse GPIO24 (`SR_PL_N`) low and
release it to sample all inputs, shift 32 bits, then pulse GPIO22 to update the
74AHCT595 outputs.

Because U9 is nearest the RP2350 serial input, its pin 6 data appears first in
the shifted stream. U6 data appears last.

### PLC inputs

| Register | Data bits | Logical inputs |
|---|---|---|
| U8 | Pin 11 -> pin 6 | PLC 1 -> PLC 8 |
| U9 | Pin 11 -> pin 6 | PLC 9 -> PLC 16 |

| Inputs | Connector pins | Optocoupler | Pull-up |
|---|---|---|---|
| 1-4 | J7.1-J7.4 | U21 | RN35 |
| 5-8 | J7.5-J7.8 | U20 | RN34 |
| 9-12 | J8.1-J8.4 | U19 | RN33 |
| 13-16 | J8.5-J8.8 | U18 | RN32 |

The RN32-RN35 signal pins are mirrored relative to the connector groups. Use
the register and connector tables above, not visual pin order, in firmware.

### Servo status input mapping

| Register | Pins | Signals |
|---|---|---|
| U6 | 11, 12 | AX0_ZERO, AX0_ERROR_N |
| U6 | 13, 14 | AX6_ZERO, AX6_ERROR_N |
| U6 | 3, 4 | AX4_ERROR_N, AX4_ZERO |
| U6 | 5, 6 | AX5_ERROR_N, AX5_ZERO |
| U7 | 11, 12 | AX3_ZERO, AX3_ERROR_N |
| U7 | 13, 14 | GND, GND |
| U7 | 3, 4 | AX1_ZERO, AX1_ERROR_N |
| U7 | 5, 6 | AX2_ZERO, AX2_ERROR_N |

| Axis | Output connector | Input connector |
|---|---|---|
| AX0 | J10: EN_3AX, STEP, DIR | J40: GND, ERROR, ZERO |
| AX1 | J11: EN_3AX, STEP, DIR | J41: GND, ERROR, ZERO |
| AX2 | J28: EN_3AX, STEP, DIR | J42: GND, ERROR, ZERO |
| AX3 | J29: EN_4AX, STEP, DIR | J43: GND, ERROR, ZERO |
| AX4 | J30: EN_4AX, STEP, DIR | J48: GND, ERROR, ZERO |
| AX5 | J46: EN_4AX, STEP, DIR | J49: GND, ERROR, ZERO |
| AX6 | J47: EN_4AX, STEP, DIR | J50: GND, ERROR, ZERO |

## Output register chain

The physical chain is:

`MOD1 GPIO20 -> U13 -> U12 -> U11 -> U10`

| Logical outputs | Register | Destination |
|---|---|---|
| OUT0-OUT7 | U10 | Motion buffer U42 |
| OUT8-OUT15 | U11 | Motion buffer U43 |
| OUT16-OUT23 | U12 | General outputs DO0-DO7 |
| OUT24-OUT31 | U13 | General outputs DO8-DO15 |

### Motion outputs

| Bit | Signal | Connector |
|---:|---|---|
| 0 | AX0_STEP | J10.2 |
| 1 | AX0_DIR | J10.3 |
| 2 | AX1_STEP | J11.2 |
| 3 | AX1_DIR | J11.3 |
| 4 | AX2_STEP | J28.2 |
| 5 | AX2_DIR | J28.3 |
| 6 | AX3_STEP | J29.2 |
| 7 | AX3_DIR | J29.3 |
| 8 | AX4_STEP | J30.2 |
| 9 | AX4_DIR | J30.3 |
| 10 | AX5_STEP | J46.2 |
| 11 | AX5_DIR | J46.3 |
| 12 | AX6_STEP | J47.2 |
| 13 | AX6_DIR | J47.3 |
| 14 | EN_3AX | J10.1, J11.1, J28.1 |
| 15 | EN_4AX | J29.1, J30.1, J46.1, J47.1 |

### General outputs

| Logical outputs | Register | Opto drive | Driver | Connector |
|---|---|---|---|---|
| DO0-DO3 | OUT16-OUT19 | RN37, U61 | U26 | J12.1-4 |
| DO4-DO7 | OUT20-OUT23 | RN38, U62 | U26 | J12.5-8 |
| DO8-DO11 | OUT24-OUT27 | RN39, U63 | U27 | J32.1-4 |
| DO12-DO15 | OUT28-OUT31 | RN40, U64 | U27 | J32.5-8 |

The TBD62083AFG arrays are low-side switches. Their outputs are not isolated
motor-supply rails and must remain within the package current and thermal
limits documented in the power budget.

## Control pins

| Function | GPIO | MOD1 pin |
|---|---:|---:|
| Shift serial data | 20 | 43 |
| Shift clock | 21 | 59 |
| 74AHCT595 latch | 22 | 44 |
| 74HC165 serial return | 23 | 60 |
| 74HC165 parallel load | 24 | 45 |
