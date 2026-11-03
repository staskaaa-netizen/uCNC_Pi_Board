# Digital chain and bit map

## Input register chain

The physical chain is:

`U6 Q7 -> U7 DS -> U8 DS -> U9 DS -> MOD1 GPIO23`

Clock all four 74HC165D registers from GPIO21. Pulse GPIO24 (`PL`) low and
release it to sample all inputs, shift 32 bits, then pulse GPIO22 to update the
74AHCT595 outputs.

Because U9 is nearest the RP2350 serial input, its pin 6 data appears first in
the shifted stream. U6 data appears last.

### PLC inputs

| Register | Data bits | Logical inputs |
|---|---|---|
| U8 | Pin 11 -> pin 6 | I01 -> I08 |
| U9 | Pin 11 -> pin 6 | I09 -> I16 |

| Input | Connector pin | Optocoupler output | Shift-register pin |
|---:|---|---|---:|
| I01-I04 | J7.1-J7.4 | U21.16/U21.14/U21.12/U21.10 | U8.11/U8.12/U8.13/U8.14 |
| I05-I08 | J7.5-J7.8 | U20.16/U20.14/U20.12/U20.10 | U8.3/U8.4/U8.5/U8.6 |
| I09-I12 | J8.1-J8.4 | U19.16/U19.14/U19.12/U19.10 | U9.11/U9.12/U9.13/U9.14 |
| I13-I16 | J8.5-J8.8 | U18.16/U18.14/U18.12/U18.10 | U9.3/U9.4/U9.5/U9.6 |

| Inputs | Connector pins | Optocoupler | Pull-up |
|---|---|---|---|
| I01-I04 | J7.1-J7.4 | U21 | RN35 |
| I05-I08 | J7.5-J7.8 | U20 | RN34 |
| I09-I12 | J8.1-J8.4 | U19 | RN33 |
| I13-I16 | J8.5-J8.8 | U18 | RN32 |

The RN32-RN35 signal pins are mirrored relative to the connector groups. Use
the register and connector tables above, not visual pin order, in firmware.

### Servo status input mapping

| Register | Pins | Signals |
|---|---|---|
| U6 | 11, 12 | Z0, ERR0 |
| U6 | 13, 14 | Z4, ERR4 |
| U6 | 3, 4 | ERR6, Z6 |
| U6 | 5, 6 | ERR5, Z5 |
| U7 | 11, 12 | Z3, ERR3 |
| U7 | 13, 14 | GND, GND |
| U7 | 3, 4 | Z1, ERR1 |
| U7 | 5, 6 | Z2, ERR2 |

The status chain uses A4 before A6 in the physical register order. Firmware
must use this table rather than assume A0-A6 are consecutive.

| Axis | Output connector | Input connector |
|---|---|---|
| A0 | J10: EN3 STP0 DIR0 | J40: GND ERR0 Z0 |
| A1 | J11: EN3 STP1 DIR1 | J41: GND ERR1 Z1 |
| A2 | J28: EN3 STP2 DIR2 | J42: GND ERR2 Z2 |
| A3 | J29: EN4 STP3 DIR3 | J43: GND ERR3 Z3 |
| A4 | J47: EN4 STP4 DIR4 | J50: GND ERR4 Z4 |
| A5 | J46: EN4 STP5 DIR5 | J49: GND ERR5 Z5 |
| A6 | J30: EN4 STP6 DIR6 | J48: GND ERR6 Z6 |

Axis numbers follow the physical top-to-bottom connector order. A4 is
J47/J50 and A6 is J30/J48; they are not sequential with the output bit order.

## Output register chain

The physical chain is:

`MOD1 GPIO20 -> U13 -> U12 -> U11 -> U10`

| Logical outputs | Register | Destination |
|---|---|---|
| OUT0-OUT7 | U10 | Motion buffer U42 |
| OUT8-OUT15 | U11 | Motion buffer U43 |
| OUT16-OUT23 | U12 | General outputs D01-D08 |
| OUT24-OUT31 | U13 | General outputs D09-D16 |

### Motion outputs

| Bit | Signal | Buffer input | Buffer output | Connector |
|---:|---|---:|---:|---|
| 0 | STP0 | U42.9 | U42.11 | J10.2 |
| 1 | DIR0 | U42.8 | U42.12 | J10.3 |
| 2 | STP1 | U42.7 | U42.13 | J11.2 |
| 3 | DIR1 | U42.6 | U42.14 | J11.3 |
| 4 | STP2 | U42.5 | U42.15 | J28.2 |
| 5 | DIR2 | U42.4 | U42.16 | J28.3 |
| 6 | STP3 | U42.3 | U42.17 | J29.2 |
| 7 | DIR3 | U42.2 | U42.18 | J29.3 |
| 8 | STP6 | U43.9 | U43.11 | J30.2 |
| 9 | DIR6 | U43.8 | U43.12 | J30.3 |
| 10 | STP5 | U43.7 | U43.13 | J46.2 |
| 11 | DIR5 | U43.6 | U43.14 | J46.3 |
| 12 | STP4 | U43.5 | U43.15 | J47.2 |
| 13 | DIR4 | U43.4 | U43.16 | J47.3 |
| 14 | EN3 | U43.3 | U43.17 | J10.1, J11.1, J28.1 |
| 15 | EN4 | U43.2 | U43.18 | J29.1, J30.1, J46.1, J47.1 |

Motion bits 8-9 therefore drive A6 and bits 12-13 drive A4. Firmware must use
this bit map rather than assume sequential axis order.

### General outputs

| Output | Connector pin | Shift bit | Optocoupler output | Driver output |
|---|---:|---:|---|---:|
| D01 | J12.1 | OUT16 | U61.9 | U26.11 |
| D02 | J12.2 | OUT17 | U61.11 | U26.12 |
| D03 | J12.3 | OUT18 | U61.13 | U26.13 |
| D04 | J12.4 | OUT19 | U61.15 | U26.14 |
| D05 | J12.5 | OUT20 | U62.9 | U26.15 |
| D06 | J12.6 | OUT21 | U62.11 | U26.16 |
| D07 | J12.7 | OUT22 | U62.13 | U26.17 |
| D08 | J12.8 | OUT23 | U62.15 | U26.18 |
| D09 | J32.1 | OUT24 | U63.9 | U27.11 |
| D10 | J32.2 | OUT25 | U63.11 | U27.12 |
| D11 | J32.3 | OUT26 | U63.13 | U27.13 |
| D12 | J32.4 | OUT27 | U63.15 | U27.14 |
| D13 | J32.5 | OUT28 | U64.9 | U27.15 |
| D14 | J32.6 | OUT29 | U64.11 | U27.16 |
| D15 | J32.7 | OUT30 | U64.13 | U27.17 |
| D16 | J32.8 | OUT31 | U64.15 | U27.18 |

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
