# Display population options

The board provides one LCD output configuration. The verified PicoLVDS HSTX
order is used: `GPIO12-13 = D0`, `GPIO14-15 = D1`,
`GPIO16-17 = D2`, `GPIO18-19 = clock`. In each pair, the lower-numbered
GPIO is P and the higher-numbered GPIO is N.

The HDMI receptacle and all HDMI-only circuitry are removed. There is no HDMI
video, CEC, DDC, HPD, +5 V HDMI fuse or HDMI ESD/termination path on the board.
J22 is the only display connector.

## LCD LVDS

- Fit RN26 and RN27, the 4 x 330 ohm passive LVDS series arrays.
- U41 (DS90LV047A) and its C106 bypass are removed.
- J22 is the 2.00 mm, 2x10 LCD connector and is mounted on F.Cu.
- Odd pins are the left column and even pins are the right column. Rows 1-8
  are used; rows 9-10 and pins 17-20 are no-connect.
- J22 is placed at approximately `(106.82, 103.11)`, rotation 90 degrees.
- RN26 and RN27 are placed at approximately `(112.63, 96.64)` and
  `(118.33, 96.64)`, both rotation 270 degrees.

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

RN26 and RN27 form the passive signal path. Their isolated
network pairs are physically ordered to fan into J22 without reversing the
logical lanes:

| Network | Pair 1 pins 1/8 | Pair 2 pins 2/7 | Pair 3 pins 3/6 | Pair 4 pins 4/5 |
|---|---|---|---|---|
| RN26 | HSTX_D1_N -> LVDS_D1_N | HSTX_D1_P -> LVDS_D1_P | HSTX_D0_P -> LVDS_D0_P | HSTX_D0_N -> LVDS_D0_N |
| RN27 | HSTX_CLK_N -> LVDS_CLK_N | HSTX_CLK_P -> LVDS_CLK_P | HSTX_D2_P -> LVDS_D2_P | HSTX_D2_N -> LVDS_D2_N |

The physical output polarity order of the two resistor networks is
`N, P, P, N, N, P, P, N`.

This is an equivalent package-pin permutation; the RP2350 pin functions and J22
net names are unchanged.

This follows the established PicoLVDS lane order. The requested nominal value is
330 ohm; the reference prototype used 270 ohm. Verify the target panel and cable
with the selected value before release.

The B.Silkscreen includes a compact J22 legend for supply, ground, D0-D2,
clock, and no-connect pin groups.

LVDS connector tracks use a dedicated 0.12 mm track/gap/clearance netclass;
the HSTX source nets remain 0.20 mm.

## Backlight

The verified J22 pinout contains no backlight contact. J2 is the separate
3-position backlight/CCFL connector:

| Pin | Signal |
|---:|---|
| 1 | isolated `+12V_BL` from U3 |
| 2 | `ISO_GND` |
| 3 | `BL_PWM`, 3.3 V from GPIO35 |

U3 is an LMR36510 buck powered from the isolated PLC 24 V rail on J33/J45. Its
input, output and feedback network all reference `ISO_GND`. The existing U37
`+12V_AO` supply remains dedicated to the 0-10 V output stage.

GPIO35/MOD1 pin 25 drives `BL_PWM_MCU`; R131 (100 ohm) feeds J2 pin 3. Any
CCFL inverter stage, high-current switching, current limiting and PWM isolation
remain external.

`BL_PWM_MCU` and `BL_PWM` use 0.2 mm copper. `+24V_FIELD` and `ISO_GND` use
the field-power class.
