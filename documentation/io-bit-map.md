# Digital chain and bit map

## Input chain

The physical chain is:

`U6 Q7 -> U7 DS`, `U7 Q7 -> U8 DS`, `U8 Q7 -> U9 DS`,
`U9 Q7 -> MOD1 GPIO23`.

Both chains use `SR_SCK` rising edges. Pulse `SR_PL_N` low and release it to
sample the inputs, transfer exactly 32 bits, then pulse `SR_LATCH` to update
the 74HC595 outputs.

### PLC inputs

| Register | Data pins |
|---|---|
| U8 | Pin 11 = input 1 through pin 6 = input 8 |
| U9 | Pin 11 = input 9 through pin 6 = input 16 |

The PLC field groups are:

| Inputs | Connector | Optocoupler | Pull-up |
|---:|---|---|---|
| 1-4 | J7.1-4 | U21 | RN35 |
| 5-8 | J7.5-8 | U20 | RN34 |
| 9-12 | J8.1-4 | U19 | RN33 |
| 13-16 | J8.5-8 | U18 | RN32 |

Each RN signal order is mirrored `4-3-2-1`. The isolated field return is
`ISO_GND` on J33/J45.

### Servo status inputs

| Register | Data-pin assignment |
|---|---|
| U6 | AX0 and AX4-AX6 ZERO/ERROR pairs |
| U7 | AX1-AX3 ZERO/ERROR pairs; pins 13/14 grounded |

U6 exact mapping:

| Pin | Signal |
|---:|---|
| 11 | `AX0_ZERO` |
| 12 | `AX0_ERROR_N` |
| 13 | `AX6_ZERO` |
| 14 | `AX6_ERROR_N` |
| 3 | `AX4_ERROR_N` |
| 4 | `AX4_ZERO` |
| 5 | `AX5_ERROR_N` |
| 6 | `AX5_ZERO` |

U7 exact mapping:

| Pin | Signal |
|---:|---|
| 11 | `AX3_ZERO` |
| 12 | `AX3_ERROR_N` |
| 13 | GND |
| 14 | GND |
| 3 | `AX1_ZERO` |
| 4 | `AX1_ERROR_N` |
| 5 | `AX2_ZERO` |
| 6 | `AX2_ERROR_N` |

Each axis has a paired 3-pin connector:

| Axis | Output connector | Input connector |
|---|---|---|
| AX0 | J10: EN, STEP, DIR | J40: ZERO, ERROR, GND |
| AX1 | J11: EN, STEP, DIR | J41: ZERO, ERROR, GND |
| AX2 | J28: EN, STEP, DIR | J42: ZERO, ERROR, GND |
| AX3 | J29: EN, STEP, DIR | J43: ZERO, ERROR, GND |
| AX4 | J30: EN, STEP, DIR | J48: ZERO, ERROR, GND |
| AX5 | J46: EN, STEP, DIR | J49: ZERO, ERROR, GND |
| AX6 | J47: EN, STEP, DIR | J50: ZERO, ERROR, GND |

There is no shared servo alarm input.

## Output chain

The physical serial chain is:

`MCU GPIO20 -> U13 -> U12 -> U11 -> U10`

| Logical bits | Register | Load |
|---:|---|---|
| 0-7 | U10 | Motion |
| 8-15 | U11 | Motion and enables |
| 16-23 | U12 | General outputs DO0-DO7 |
| 24-31 | U13 | General outputs DO8-DO15 |

| Bit | Signal | Destination |
|---:|---|---|
| 0 | `AX0_STEP` | J10.2 |
| 1 | `AX0_DIR` | J10.3 |
| 2 | `AX1_STEP` | J11.2 |
| 3 | `AX1_DIR` | J11.3 |
| 4 | `AX2_STEP` | J28.2 |
| 5 | `AX2_DIR` | J28.3 |
| 6 | `AX3_STEP` | J29.2 |
| 7 | `AX3_DIR` | J29.3 |
| 8 | `AX4_STEP` | J30.2 |
| 9 | `AX4_DIR` | J30.3 |
| 10 | `AX5_STEP` | J46.2 |
| 11 | `AX5_DIR` | J46.3 |
| 12 | `AX6_STEP` | J47.2 |
| 13 | `AX6_DIR` | J47.3 |
| 14 | `EN_3AX` | J10.1, J11.1, J28.1 |
| 15 | `EN_4AX` | J29.1, J30.1, J46.1, J47.1 |

General outputs are opto-isolated and driven by U26/U27 TBD62083AFG arrays.
J12 exposes DO0-DO7 and J32 exposes DO8-DO15. U26/U27 pin 9 is `ISO_GND` and
pin 10 is `+24V_FIELD`.
