# Display population options

The board provides one LCD output configuration. The verified PicoLVDS HSTX
order is used: `GPIO12-13 = D0`, `GPIO14-15 = D1`,
`GPIO16-17 = D2`, `GPIO18-19 = clock`. In each pair, the lower-numbered
GPIO is P and the higher-numbered GPIO is N.

The HDMI receptacle and all HDMI-only circuitry are removed. There is no HDMI
video, CEC, DDC, HPD, +5 V HDMI fuse or HDMI ESD/termination path on the board.
J22 is the only display connector.

## Default: active LCD LVDS

- Fit U41, a DS90LV047A quad CMOS-to-LVDS driver in SOIC-16.
- Leave RN26 and RN27 unfitted.
- RN26 and RN27 are included in the BOM as optional DNP items.
- J22 is the 2.00 mm, 2x10 LCD connector and is mounted on B.Cu.
- Odd pins are the left column and even pins are the right column. Rows 1-8
  are used; rows 9-10 and pins 17-20 are no-connect.
- J22 is placed on the back at `(148.85, 29.05)`, rotation 90 degrees.
- RN27 and RN26 are placed below it at `(135.80, 34.40)` and
  `(141.50, 34.40)`, both rotation 90 degrees. U41 is placed over the resistor
  networks at `(138.65, 36.30)`, rotation 90 degrees. The driver and resistor
  networks are alternate populations.

| Row | Left pin | Right pin |
|---:|---|---|
| 1 | 1 = +3V3 | 2 = +3V3 |
| 2 | 3 = +3V3 | 4 = GND |
| 3 | 5 = GND | 6 = GND |
| 4 | 7 = D0- | 8 = D0+ |
| 5 | 9 = D1- | 10 = D1+ |
| 6 | 11 = D2- | 12 = D2+ |
| 7 | 13 = GND | 14 = GND |
| 8 | 15 = CLK- | 16 = CLK+ |
| 9 | 17 = NC | 18 = NC |
| 10 | 19 = NC | 20 = NC |

U41 accepts four single-ended 3.3 V HSTX signals and drives the four LVDS pairs:

| Driver input | Driver output pins | LVDS net pair | J22 pair |
|---|---|---|---|
| `HSTX_CLK_P`, pin 2 (`DIN1`) | 15 (`DOUT1+`), 16 (`DOUT1-`) | `LVDS_CLK_P/N` | pins 16/15 |
| `HSTX_D2_P`, pin 3 (`DIN2`) | 14 (`DOUT2+`), 13 (`DOUT2-`) | `LVDS_D2_P/N` | pins 12/11 |
| `HSTX_D1_P`, pin 6 (`DIN3`) | 11 (`DOUT3+`), 12 (`DOUT3-`) | `LVDS_D1_P/N` | pins 10/9 |
| `HSTX_D0_P`, pin 7 (`DIN4`) | 10 (`DOUT4+`), 9 (`DOUT4-`) | `LVDS_D0_P/N` | pins 8/7 |

`EN` is tied to `+3V3`, `EN*` to GND, and C57 provides local 100 nF
decoupling at the driver. LVDS connector tracks use a dedicated
0.12 mm track/gap/clearance netclass; the HSTX source nets remain 0.20 mm.

## Alternate: passive LCD LVDS

RN26 and RN27 are retained as an unfitted passive alternative. Their isolated
network pairs are physically ordered to fan into J22 without reversing the
logical lanes:

| Network | Pair 1 pins 1/8 | Pair 2 pins 2/7 | Pair 3 pins 3/6 | Pair 4 pins 4/5 |
|---|---|---|---|---|
| RN26 | HSTX_D1_N -> LVDS_D1_N | HSTX_D1_P -> LVDS_D1_P | HSTX_D0_P -> LVDS_D0_P | HSTX_D0_N -> LVDS_D0_N |
| RN27 | HSTX_CLK_N -> LVDS_CLK_N | HSTX_CLK_P -> LVDS_CLK_P | HSTX_D2_P -> LVDS_D2_P | HSTX_D2_N -> LVDS_D2_N |

The physical output polarity order of both the driver outputs and the two
resistor networks is `N, P, P, N, N, P, P, N`.

This is an equivalent package-pin permutation; the RP2350 pin functions and J22
net names are unchanged.

This follows the established PicoLVDS lane order. The requested nominal value is
330 ohm; the reference prototype used 270 ohm. Verify the target panel and cable
with the selected value before release.

The B.Silkscreen includes a compact J22 legend for supply, ground, D0-D2,
clock, and no-connect pin groups.

RN26/RN27 and U41 are mutually exclusive populations. Do not fit both.

## Backlight

The verified J22 pinout contains no backlight contact. J2 is the separate
4-position backlight/CCFL connector:

| Pin | Signal |
|---:|---|
| 1 | `+12V_BL` |
| 2 | GND |
| 3 | `BL_PWM`, 3.3 V from GPIO35 |
| 4 | `BL_LED_N`, low-side switched return through Q8 |

U3 is a second TI LMR36510 buck using the datasheet's 12 V, 400 kHz reference
network: 47 uH, 100 k / 9.09 k feedback, 3 x 10 uF output and 2.2 uF + 220 nF
local input capacitance. The existing U37 `+12V_AO` supply for the 0-10 V
output stage remains separate and is not shared with the backlight rail.

GPIO35/MOD1 pin 25 drives `BL_PWM_MCU`. R131 (100 ohm) feeds only J2 pin 3;
R129 (100 ohm) branches from the same MCU-side node to the Q8 gate. Use the
direct PWM input for a CCFL inverter or display controller, or the Q8-switched
low-side return for a small LED-backlight load. Any CCFL inverter stage,
high-current switching and current limiting remain external.

`BL_PWM_MCU`, `BL_PWM`, and `BL_SW_GATE` use 0.2 mm copper. The 12 V and
switched-return paths use the 0.8 mm Power class.
