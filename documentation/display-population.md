# Display population options

Only one output configuration is populated at a time. The verified PicoLVDS
HSTX order is used: `GPIO12-13 = D0`, `GPIO14-15 = D1`,
`GPIO16-17 = D2`, `GPIO18-19 = clock`. In each pair, the lower-numbered
GPIO is P and the higher-numbered GPIO is N.

## Default: passive LCD LVDS

- Fit RN26 and RN27: two four-element 330 ohm resistor arrays.
- Leave RN28 and RN29 unfitted.
- J22 is the 2.00 mm, 2x10 LCD connector.
- The chain is `HSTX_D2_N/P`, `HSTX_CLK_N/P`, `HSTX_D1_N/P`,
  `HSTX_D0_N/P` to J22 pins 14/15, 17/18, 11/12, 8/9.
- J22 is placed on the front at `(145.50, 34.00)`, rotation 270 degrees.
- RN27 and RN26 are placed below it at `(135.50, 40.00)` and
  `(143.00, 40.00)`, both rotation 90 degrees.

The isolated network pairs are physically ordered to fan into J22 without
reversing the logical lanes:

| Network | Pair 1 pins 1/8 | Pair 2 pins 2/7 | Pair 3 pins 3/6 | Pair 4 pins 4/5 |
|---|---|---|---|---|
| RN26 | HSTX_D1_P -> LVDS_D1_P | HSTX_D1_N -> LVDS_D1_N | HSTX_D0_P -> LVDS_D0_P | HSTX_D0_N -> LVDS_D0_N |
| RN27 | HSTX_CLK_P -> LVDS_CLK_P | HSTX_CLK_N -> LVDS_CLK_N | HSTX_D2_P -> LVDS_D2_P | HSTX_D2_N -> LVDS_D2_N |

This is an equivalent package-pin permutation; the RP2350 pin functions and J22
net names are unchanged.

This follows the established PicoLVDS lane order. The requested nominal value is
330 ohm; the reference prototype used 270 ohm. Verify the target panel and cable
with the selected value before release.

## Planned alternative: active LCD LVDS driver

Add a DS90LV047A later as an alternate population to RN26/RN27; it is not fitted
in the current passive configuration.

- The DS90LV047A is a quad CMOS-to-LVDS driver and needs only four
  single-ended RP2350 HSTX inputs: D0, D1, D2 and clock.
- Its four differential outputs drive the same LVDS lane order at J22.
- Tie the enable pins to their active states so the driver is permanently
  enabled: `EN` to `+3V3` and complementary `~EN` to GND, according to the
  selected package and datasheet pinout.
- Fit a local 100 nF supply bypass at the driver.
- RN26/RN27 and the active driver are mutually exclusive populations.
- Leave RN28/RN29 and the HDMI path unfitted for this LCD option.

The RP2350 does not provide differential HSTX outputs to this part. Four
single-ended CMOS inputs are the intended interface.

## HDMI option

- Leave RN26 and RN27 unfitted.
- Fit RN28 and RN29: two four-element 0 ohm resistor arrays.
- J23 is a full-size HDMI Type A connector.
- RN28 and RN29 are placed at `(173.50, 19.00)` and `(173.50, 25.00)`.
- C71, C72, R59 and R60 are grouped near the HDMI connector and its +5 V rail.
- U30/U31 provide TPD4E05U06 ESD protection on all four TMDS pairs;
  U32 protects DDC, HPD and CEC.
- DDC SCL/SDA have 4.7 k pull-ups to the
  HDMI +5 V rail and are not connected to the RP2350 because the established
  output uses fixed timing and does not require an MCU-side EDID exchange.

## Backlight

J22 pin 6 carries the 3.3 V `BL_PWM` signal directly to the LCD/backlight
assembly. The motherboard no longer switches or selects a backlight voltage
rail. J2, JP1 and the Q2/Q3 MOSFET stage are removed. The external display
module or a separate backlight driver must own high-current switching,
current limiting and any required enable logic.
