# Digital chain and bit map

## Electrical protocol

Both chains use the same `SR_SCK` rising edge. The sequence is:

1. Pulse `SR_PL_N` low and release it to sample the 16 PLC inputs, eight expansion
   inputs and eight keyboard inputs into the four 74HC165 registers.
2. Transfer exactly 32 bits MSB-first. Received data is the input word; transmitted
   data is the next output word.
3. Pulse `SR_LATCH` high to update all 32 74HC595 outputs simultaneously, then
   return it low.

The 74HC595 and SN74AHCT541 output-enable pins are tied active on this board.
Hard output blocking and safe-state enforcement are external machine-interface
functions. Firmware should still initialize the shift word to the safe value
before enabling external power.

## Input chain

The physical chain runs from the far keyboard register toward the MCU:

`74HC165 U6 Q7 -> U7 DS`, `U7 Q7 -> U8 DS`, `U8 Q7 -> U9 DS`,
`U9 Q7 -> MOD1 GPIO22 (SR_IN_Q7)`.

| Logical bits | Register | Device | Parallel inputs | Field meaning |
|---:|---|---|---|---|
| 0-7 | U9 (nearest MCU) | 74HC165 | D0-D7 = PLC_IN5_N, PLC_IN6_N, PLC_IN7_N, PLC_IN8_N, PLC_IN4_N, PLC_IN3_N, PLC_IN2_N, PLC_IN1_N | PLC logical channels, firmware-permuted |
| 8-15 | U8 | 74HC165 | D0-D7 = PLC_IN13_N, PLC_IN14_N, PLC_IN15_N, PLC_IN16_N, PLC_IN12_N, PLC_IN11_N, PLC_IN10_N, PLC_IN9_N | PLC logical channels, firmware-permuted |
| 16-23 | U7 | 74HC165 | D0-D7 = EXP_IN0-EXP_IN7 | J9 direct 3.3 V expansion |
| 24-31 | U6 (far end) | 74HC165 | D0-D7 = KIN0_FILT-KIN7_FILT | Keyboard inputs KIN0-7 |

The 32-bit SPI received word is reconstructed from its four bytes as:

```c
uint32_t input_word = (uint32_t)byte0
                    | ((uint32_t)byte1 << 8)
                    | ((uint32_t)byte2 << 16)
                    | ((uint32_t)byte3 << 24);
```

`byte0` is the first byte shifted out of U9, and `byte1` is shifted out of U8.
The physical connector positions and 74HC165 data pins were selected for a
crossing-free PCB fanout, so firmware must apply the fixed input permutation
below:

| Field position | Connector pin | PCB field net | Firmware bit |
|---:|---|---|---:|
| 1 | J7.1 | FIELD_IN9 | 15 |
| 2 | J7.3 | FIELD_IN10 | 14 |
| 3 | J7.5 | FIELD_IN11 | 13 |
| 4 | J7.7 | FIELD_IN12 | 12 |
| 5 | J7.9 | FIELD_IN13 | 8 |
| 6 | J7.11 | FIELD_IN14 | 9 |
| 7 | J7.13 | FIELD_IN15 | 10 |
| 8 | J7.15 | FIELD_IN16 | 11 |
| 9 | J8.1 | FIELD_IN1 | 7 |
| 10 | J8.3 | FIELD_IN2 | 6 |
| 11 | J8.5 | FIELD_IN3 | 5 |
| 12 | J8.7 | FIELD_IN4 | 4 |
| 13 | J8.9 | FIELD_IN5 | 0 |
| 14 | J8.11 | FIELD_IN6 | 1 |
| 15 | J8.13 | FIELD_IN7 | 2 |
| 16 | J8.15 | FIELD_IN8 | 3 |

The connector even pins remain the isolated `FIELD_COM0`/`FIELD_COM1`
returns. `(input_word >> 16) & 0xff` remains J9/J27 expansion inputs 0-7,
and `(input_word >> 24) & 0xff` remains `KIN0-7`.
- Optical input off/disconnected reads `1`; an energized input with correct
  field polarity reads `0` at the optocoupler collector node.

E-stop, HOLD and START are deliberately outside this chain. Their isolated loops
on J5/J6/J26 drive `ESTOP_N` on GPIO37, `HOLD_N` on GPIO38 and `START_N` on
GPIO39 directly. Each is active-low. uCNC maps these to `ESTOP`, `FHOLD` and
`CS_RES`; configure the corresponding input polarity in its board map.

## Output chain

The physical chain runs from the register nearest the MCU outward:

`MOD1 GPIO24 (SR_OUT_SER) -> U10 SER`, `U10 QH' -> U11 SER`,
`U11 QH' -> U12 SER`, `U12 QH' -> U13 SER`.

The software writes a 32-bit word using normal SPI mode 0, MSB-first:

```c
spi_write32(output_word);
gpio_put(SR_LATCH, 1);
gpio_put(SR_LATCH, 0);
```

Because the final bit sent after 32 clocks is least significant bit 0, the
logical output assignment is:

| Logical bits | Register | Logical outputs |
|---:|---|---|
| 0-7 | U10 (nearest MCU) | OUT0-OUT7 |
| 8-15 | U11 | OUT8-OUT15 |
| 16-23 | U12 | OUT16-OUT23 |
| 24-31 | U13 (far end) | OUT24-OUT31 |

| Bit | Signal | Destination |
|---:|---|---|
| 0 | AX0_STEP | J10.2 |
| 1 | AX0_DIR | J10.3 |
| 2 | AX0_EN | J10.1 |
| 3 | AX1_STEP | J11.2 |
| 4 | AX1_DIR | J11.3 |
| 5 | AX1_EN | J11.1 |
| 6 | AX2_STEP | J28.2 |
| 7 | AX2_DIR | J28.3 |
| 8 | AX2_EN | J28.1 |
| 9 | AX3_STEP | J29.2 |
| 10 | AX3_DIR | J29.3 |
| 11 | AX3_EN | J29.1 |
| 12 | AX4_STEP | J30.2 |
| 13 | AX4_DIR | J30.3 |
| 14 | AX4_EN | J30.1 |
| 15 | MOTION14/AUX | J31.1 |
| 16-23 | DO0-DO7 | J10.1-J10.8 through two ULN2003A arrays |
| 24-31 | KOUT0-KOUT7 | J14 even pins 2-16 |

The first 16 motion bits are driven through two `SN74AHCT541DW` buffers and
100 ohm series resistors. Bits 16-23 drive the ULN2003A inputs directly from the
3.3 V 74HC595 outputs, with 10 k pulldowns defining the off state while the 595
is disabled. Bits 24-31 drive the keyboard through 100 ohm series resistors
without pulldown arrays, because keyboard reads are not required while the 595
outputs are tri-stated.

The first two 595/541 pairs use optimized, non-sequential physical pin maps.
Each logical OUTn still connects to BUFYn and then to the same MOTIONn function;
only equivalent package channels changed. The mapping is:

| Logical bit | U10 or U11 Q pin into U24 or U25 | U24 or U25 output pin |
|---:|---|---|
| 0 | U10 pin 1 | U24 pin 12 |
| 1 | U10 pin 15 | U24 pin 11 |
| 2 | U10 pin 3 | U24 pin 14 |
| 3 | U10 pin 2 | U24 pin 13 |
| 4 | U10 pin 5 | U24 pin 16 |
| 5 | U10 pin 4 | U24 pin 15 |
| 6 | U10 pin 7 | U24 pin 18 |
| 7 | U10 pin 6 | U24 pin 17 |
| 8 | U11 pin 2 | U25 pin 12 |
| 9 | U11 pin 1 | U25 pin 11 |
| 10 | U11 pin 15 | U25 pin 13 |
| 11 | U11 pin 3 | U25 pin 14 |
| 12 | U11 pin 4 | U25 pin 15 |
| 13 | U11 pin 5 | U25 pin 16 |
| 14 | U11 pin 6 | U25 pin 17 |
| 15 | U11 pin 7 | U25 pin 18 |

On the U24/U25 side, input pins 2-9 are mapped to
OUT6/OUT7/OUT4/OUT5/OUT2/OUT3/OUT0/OUT1 for U24 and
OUT15/OUT14/OUT13/OUT12/OUT11/OUT10/OUT8/OUT9 for U25. This removes the
remaining 17 analyzed ratline crossings in the two register/buffer pairs for
the current placement.

The four 100 ohm motion arrays use optimized channel permutations. RN16 and
RN17 intentionally swap output pairs `1↔2` and `3↔4`; RN18 and RN19 retain
identity output pairing:

| Array | Channel 1 pins 1/8 | Channel 2 pins 2/7 | Channel 3 pins 3/6 | Channel 4 pins 4/5 |
|---|---|---|---|---|
| RN16 | BUFY2/MOTION3 | BUFY3/MOTION2 | BUFY0/MOTION1 | BUFY1/MOTION0 |
| RN17 | BUFY6/MOTION7 | BUFY7/MOTION6 | BUFY4/MOTION5 | BUFY5/MOTION4 |
| RN18 | BUFY11/MOTION11 | BUFY10/MOTION10 | BUFY8/MOTION9 | BUFY9/MOTION8 |
| RN19 | BUFY15/MOTION15 | BUFY14/MOTION14 | BUFY13/MOTION13 | BUFY12/MOTION12 |

Accordingly, the RN16/RN17 output mapping must be reflected in firmware:
`OUT0→MOTION1`, `OUT1→MOTION0`, `OUT2→MOTION3`, `OUT3→MOTION2`,
`OUT4→MOTION5`, `OUT5→MOTION4`, `OUT6→MOTION7`, and `OUT7→MOTION6`.
RN18/RN19 remain identity through bit 15.

The ULN output byte is also wired to the current IC positions:

| Logical bit | U12 Q pin | ULN input | ULN output | Field output |
|---:|---:|---|---|---|
| 16 | 1 | U26.4 | U26.13 | DO0 |
| 17 | 2 | U26.3 | U26.14 | DO1 |
| 18 | 3 | U26.2 | U26.15 | DO2 |
| 19 | 4 | U26.1 | U26.16 | DO3 |
| 20 | 5 | U27.4 | U27.13 | DO4 |
| 21 | 6 | U27.3 | U27.14 | DO5 |
| 22 | 7 | U27.2 | U27.15 | DO6 |
| 23 | 15 | U27.1 | U27.16 | DO7 |

## Keyboard resistor-network pin map

RN20/RN21 and RN22/RN24 use equivalent isolated-element and terminal swaps to
minimize the local ratline crossings. All four networks remain on F.Cu.

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN20 | KOUT0/OUT24 | OUT25/KOUT1 | KOUT2/OUT26 | OUT27/KOUT3 |
| RN21 | KOUT4/OUT28 | KOUT5/OUT29 | KOUT6/OUT30 | KOUT7/OUT31 |
| RN22 | KIN0_FILT/KIN0 | KIN1_FILT/KIN1 | KIN2_FILT/KIN2 | KIN3_FILT/KIN3 |
| RN24 | KIN4_FILT/KIN4 | KIN5_FILT/KIN5 | KIN6_FILT/KIN6 | KIN7_FILT/KIN7 |

These swaps do not change the logical KIN0-7 or KOUT0-7 assignments.

## Passive LVDS physical mapping

RN26 and RN27 are placed rotation 90 degrees with their isolated element order
reversed so the outputs fan directly into J22:

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN26 | HSTX_D1_P -> LVDS_D1_P | HSTX_D1_N -> LVDS_D1_N | HSTX_D0_P -> LVDS_D0_P | HSTX_D0_N -> LVDS_D0_N |
| RN27 | HSTX_CLK_P -> LVDS_CLK_P | HSTX_CLK_N -> LVDS_CLK_N | HSTX_D2_P -> LVDS_D2_P | HSTX_D2_N -> LVDS_D2_N |

The RP2350 lane definitions and J22 pin mapping remain unchanged.

## Legacy firmware status

The requested existing LeanCam/NCC firmware and prior board files were not
present in the supplied workspace. The physical chain order above is explicit and
verified against the 74HC165/74HC595 shift direction. The mapping of axis names
to STEP/DIR/EN is the proposed NCC contract and must be checked against the
production firmware before commissioning.
