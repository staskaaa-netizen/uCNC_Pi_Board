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
`U9 Q7 -> MOD1 GPIO23 (SR_IN_Q7)`.

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
| 5 | J34.1 | FIELD_IN13 | 8 |
| 6 | J34.3 | FIELD_IN14 | 9 |
| 7 | J34.5 | FIELD_IN15 | 10 |
| 8 | J34.7 | FIELD_IN16 | 11 |
| 9 | J8.1 | FIELD_IN1 | 7 |
| 10 | J8.3 | FIELD_IN2 | 6 |
| 11 | J8.5 | FIELD_IN3 | 5 |
| 12 | J8.7 | FIELD_IN4 | 4 |
| 13 | J35.1 | FIELD_IN5 | 0 |
| 14 | J35.3 | FIELD_IN6 | 1 |
| 15 | J35.5 | FIELD_IN7 | 2 |
| 16 | J35.7 | FIELD_IN8 | 3 |

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

`MOD1 GPIO20 (SR_OUT_SER) -> U10 SER`, `U10 QH' -> U11 SER`,
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
| 0 | AUX | J31.1 |
| 1 | MOTION0 / AX0_EN | J10.1 |
| 2 | MOTION2 / AX0_DIR | J10.3 |
| 3 | MOTION1 / AX0_STEP | J10.2 |
| 4 | MOTION4 / AX1_STEP | J11.2 |
| 5 | MOTION3 / AX1_EN | J11.1 |
| 6 | MOTION6 / AX2_EN | J28.1 |
| 7 | MOTION5 / AX1_DIR | J11.3 |
| 8 | MOTION8 / AX2_DIR | J28.3 |
| 9 | MOTION7 / AX2_STEP | J28.2 |
| 10 | MOTION9 / AX3_EN | J29.1 |
| 11 | MOTION10 / AX3_STEP | J29.2 |
| 12 | MOTION11 / AX3_DIR | J29.3 |
| 13 | MOTION12 / AX4_EN | J30.1 |
| 14 | MOTION13 / AX4_STEP | J30.2 |
| 15 | MOTION14 / AX4_DIR | J30.3 |
| 16-29 | DO0-DO13 | J12 pins1-8 and J32 pins1-6 through both ULN2003A arrays |
| 30-31 | DO14-DO15 | J32 pins7-8 through BSS138 low-side MOSFETs |
| 24-31 | KOUT0-KOUT7 | J16 even pins 2-16; OUT24-OUT31 fan out to the ULNs/MOSFETs where used |

Bit 0 enters U24 pin 8 and its U24 pin 12 (`BUFY0`) output drives RN16 element
3. RN16 pin 6 then drives the AUX low-side MOSFET gate; the 100 k pulldown at
R113 remains. Bits 1-15 use the remaining U24/U25 channels and 100 ohm series
resistors as MOTION0-MOTION14.
Bits 16-29 drive all fourteen ULN2003A inputs
directly from the 3.3 V 74HC595 outputs, with 10 k pulldowns wherever required
by the output bank. Bits 30-31 use BSS138 low-side MOSFETs with the same
100 ohm gate resistor and 100 k gate pulldown as the auxiliary output.
OUT24-29 additionally drive the keyboard through 100 ohm series resistors;
OUT30-31 do likewise while also driving the two MOSFET gates.

The first two 595/541 pairs use optimized, non-sequential physical pin maps.
Each logical OUTn still connects to U24/U25 input n and produces BUFYn; the
resistor arrays then offset BUFY1-15 to MOTION0-14. The package mapping is:

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

The four 100 ohm motion arrays form one monotonic physical sequence from the
buffer outputs on the upper RN row to the connector field from the lower RN
row. RN16 element 3 is the AUX gate-drive element, so all sixteen RN16-RN19
elements are active.

| Array | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN16 | BUFY2/MOTION2 | BUFY3/MOTION1 | BUFY0/AUX_GATE | BUFY1/MOTION0 |
| RN17 | BUFY6/MOTION6 | BUFY7/MOTION5 | BUFY4/MOTION4 | BUFY5/MOTION3 |
| RN18 | BUFY11/MOTION10 | BUFY10/MOTION9 | BUFY8/MOTION8 | BUFY9/MOTION7 |
| RN19 | BUFY15/MOTION14 | BUFY14/MOTION13 | BUFY13/MOTION12 | BUFY12/MOTION11 |

The first/second net listed for each element connects to the buffer-side and
connector-side pins respectively. Sorting the physical connector pins from
left to right gives BUFY15, 14, 13, 12, 11, 10, 8, 9, 6, 7, 4, 5, 2, 3, 1;
the corresponding series elements maintain monotonic pad order.

The updated output mapping in firmware is:
`OUT0 -> U24 -> RN16 -> AUX` and the explicit bit-to-motion permutation in the
table above. All fifteen motion channels plus AUX use all sixteen 541 outputs.

The ULN output byte is also wired to the current IC positions:

| Logical bit | 595 Q pin | ULN input | ULN output | Field output |
|---:|---:|---|---|---|
| 16 | 1 | U26.7 | U26.10 | DO0 |
| 17 | 2 | U26.6 | U26.11 | DO1 |
| 18 | 3 | U26.5 | U26.12 | DO2 |
| 19 | 4 | U26.4 | U26.13 | DO3 |
| 20 | 5 | U26.3 | U26.14 | DO4 |
| 21 | 6 | U26.2 | U26.15 | DO5 |
| 22 | 7 | U26.1 | U26.16 | DO6 |
| 23 | 15 | U27.7 | U27.10 | DO7 |
| 24 | U13.15 | U27.6 | U27.11 | DO8 |
| 25 | U13.1 | U27.5 | U27.12 | DO9 |
| 26 | U13.2 | U27.4 | U27.13 | DO10 |
| 27 | U13.3 | U27.3 | U27.14 | DO11 |
| 28 | U13.4 | U27.2 | U27.15 | DO12 |
| 29 | U13.5 | U27.1 | U27.16 | DO13 |
| 30 | U13.6 | BSS138 Q6 gate | Q6 drain | DO14 |
| 31 | U13.7 | BSS138 Q7 gate | Q7 drain | DO15 |

J12 exposes DO0-DO7. J32 exposes DO8-DO15. J33 provides their shared
`DO_COM` and GND terminals.

## Pull-down and keyboard resistor-network pin map

RN8-RN11 use equivalent element and terminal permutations selected from the
fixed footprint geometries:

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN8 | GND/BUFY2 | GND/BUFY3 | GND/BUFY0 | GND/BUFY1 |
| RN9 | BUFY5/GND | BUFY4/GND | BUFY7/GND | BUFY6/GND |
| RN10 | BUFY9/GND | BUFY8/GND | BUFY10/GND | BUFY11/GND |
| RN11 | GND/BUFY15 | GND/BUFY14 | GND/BUFY13 | GND/BUFY12 |

RN12, RN13, RN30 and RN31 use equivalent element/terminal swaps to meet the
U12/U13-to-U26/U27 fanout while preserving every `OUTn` logical assignment:

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN12 | OUT19/GND | OUT18/GND | OUT17/GND | OUT16/GND |
| RN13 | spare | OUT22/GND | OUT21/GND | OUT20/GND |
| RN30 | OUT26/GND | OUT24/GND | OUT25/GND | OUT23/GND |
| RN31 | OUT29/GND | OUT28/GND | OUT27/GND | spare |

RN20/RN21 and RN22/RN24 use equivalent isolated-element and terminal swaps to
minimize the local ratline crossings. All four networks remain on F.Cu.

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN20 | KOUT0/OUT24 | KOUT1/OUT25 | KOUT2/OUT26 | KOUT3/OUT27 |
| RN21 | KOUT4/OUT28 | KOUT5/OUT29 | KOUT6/OUT30 | KOUT7/OUT31 |
| RN22 | KIN0_FILT/KIN0 | KIN1_FILT/KIN1 | KIN2_FILT/KIN2 | KIN3_FILT/KIN3 |
| RN24 | KIN4_FILT/KIN4 | KIN5_FILT/KIN5 | KIN6_FILT/KIN6 | KIN7_FILT/KIN7 |

These swaps do not change the logical KIN0-7 or KOUT0-7 assignments.

## Passive LVDS physical mapping

RN26 and RN27 are placed rotation 90 degrees with their isolated element order
reversed so the outputs fan directly into J22:

| Network | Element 1 pins 1/8 | Element 2 pins 2/7 | Element 3 pins 3/6 | Element 4 pins 4/5 |
|---|---|---|---|---|
| RN26 | HSTX_D1_N -> LVDS_D1_N | HSTX_D1_P -> LVDS_D1_P | HSTX_D0_P -> LVDS_D0_P | HSTX_D0_N -> LVDS_D0_N |
| RN27 | HSTX_CLK_N -> LVDS_CLK_N | HSTX_CLK_P -> LVDS_CLK_P | HSTX_D2_P -> LVDS_D2_P | HSTX_D2_N -> LVDS_D2_N |

The RP2350 lane definitions are unchanged. J22 now follows the verified panel
pinout, with D0 on pins 7/8, D1 on 9/10, D2 on 11/12 and clock on 15/16.

## Legacy firmware status

The requested existing LeanCam/NCC firmware and prior board files were not
present in the supplied workspace. The physical chain order above is explicit and
verified against the 74HC165/74HC595 shift direction. The mapping of axis names
to STEP/DIR/EN is the proposed NCC contract and must be checked against the
production firmware before commissioning.
