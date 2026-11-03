# LCD LVDS interface

J22 is the only display connector. It is a 2 x 10, 2.00 mm header on F.Cu. The
RP2350 HSTX pins drive four differential channels through two 4 x 330 ohm
resistor arrays:

| RP2350 function | GPIO | J22 pins |
|---|---:|---:|
| HSTX D0 P/N | 12 / 13 | 8 / 7 |
| HSTX D1 P/N | 14 / 15 | 10 / 9 |
| HSTX D2 P/N | 16 / 17 | 12 / 11 |
| HSTX clock P/N | 18 / 19 | 16 / 15 |

## J22 pinout

| Row | Left pin | Right pin | Required |
|---|---|---|---|
| 1 | 1=`3V3` | 2=`3V3` | Yes |
| 2 | 3=`3V3` | 4=`GND` | Yes |
| 3 | 5=`GND` | 6=`GND` | Yes |
| 4 | 7=D0- | 8=D0+ | Yes |
| 5 | 9=D1- | 10=D1+ | Yes |
| 6 | 11=D2- | 12=D2+ | Yes |
| 7 | 13=`GND` | 14=`GND` | Yes |
| 8 | 15=CLK- | 16=CLK+ | Yes |
| 9 | 17=NC | 18=NC | No |
| 10 | 19=NC | 20=NC | No |

## Series arrays

| Network | Pins | Connection |
|---|---|---|
| RN26 | 1-8 | HSTX_D0_P to LVDS_D0_P |
| RN26 | 2-7 | HSTX_D0_N to LVDS_D0_N |
| RN26 | 3-6 | HSTX_D1_P to LVDS_D1_P |
| RN26 | 4-5 | HSTX_D1_N to LVDS_D1_N |
| RN27 | 1-8 | HSTX_D2_P to LVDS_D2_P |
| RN27 | 2-7 | HSTX_D2_N to LVDS_D2_N |
| RN27 | 3-6 | HSTX_CLK_P to LVDS_CLK_P |
| RN27 | 4-5 | HSTX_CLK_N to LVDS_CLK_N |

The networks contain isolated 330 ohm elements. Verify the final value with the
target panel, cable length and PicoLVDS-compatible source configuration before
release.

The HSTX source pairs use the 0.20 mm `DigitalDiffPair` net class. The J22
fan-out uses the 0.12 mm `LVDSConnector` class so the tracks clear the 2.00 mm
connector pads. A compact legend on B.Silkscreen identifies supply, ground,
data, clock and no-connect pin groups.

## Backlight

J22 does not carry backlight power. J2 provides:

| Pin | Signal |
|---:|---|
| 1 | isolated `BL_12V` |
| 2 | `PLC_0V` |

U3 is an LMR36510 converter powered from PLC 24+ on J33/J45.
Its input, output and feedback networks all reference `PLC_0V`.

Backlight PWM, current limiting, CCFL inversion and high-current switching are
external. Do not connect `BL_12V` or `PLC_0V` to the logic-side GND domain.
