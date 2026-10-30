# WeAct RP2350B pin allocation

This allocation was checked against the vendor `RP2350B_PINOUT.png`, the
official 64-pad footprint labels, and the generated `MOD1` pin numbers.

## Control and safety

| GPIO | MOD1 pin | Signal | Direction | Notes |
|---:|---:|---|---|---|
| 10 | 38 | WIFI_TX | Output | UART1 TX to ESP RX |
| 11 | 54 | WIFI_RX | Input | UART1 RX from ESP TX |
| 20 | 43 | SR_OUT_SER | Output | 595 serial data / PIO DATA |
| 21 | 59 | SR_SCK | Output | Shared 165/595 clock / PIO CLK |
| 22 | 44 | SR_LATCH | Output | 595 storage clock / PIO LATCH |
| 24 | 45 | SR_PL_N | Output | 165 parallel load |
| 23 | 60 | SR_IN_Q7 | Input | Shift-chain return; remove WeAct R16 (0R) and do not use USER key |
| 35 | 25 | `BL_PWM_MCU` | Output | Series-protected J2 PWM and Q8 gate drive |
| 36 | 10 | — | Reserved | Local output-enable gate removed |
| 37 | 24 | ESTOP_N | Input | Dedicated E-stop, active low |
| 38 | 9 | HOLD_N | Input | Dedicated HOLD, active low |
| 39 | 23 | START_N | Input | Dedicated START, active low |
| 43 | 21 | PWR_GOOD_N | Input | LMR36510 power-good |

## Encoders

| GPIO | MOD1 pin | Signal |
|---:|---:|---|
| 26 | 15 | ENC0_A_3V3 |
| 27 | 29 | ENC0_B_3V3 |
| 28 | 14 | ENC0_Z_3V3 |
| 29 | 28 | ENC1_A_3V3 |
| 30 | 13 | ENC1_B_3V3 |
| 31 | 27 | ENC1_Z_3V3 |
| 32 | 12 | ENC2_A_3V3 |
| 33 | 26 | ENC2_B_3V3 |
| 34 | 11 | ENC2_Z_3V3 |

## Display

| GPIO | MOD1 pin | Signal |
|---:|---:|---|
| 12 | 39 | HSTX_D0_P |
| 13 | 55 | HSTX_D0_N |
| 14 | 40 | HSTX_D1_P |
| 15 | 56 | HSTX_D1_N |
| 16 | 41 | HSTX_D2_P |
| 17 | 57 | HSTX_D2_N |
| 18 | 42 | HSTX_CLK_P |
| 19 | 58 | HSTX_CLK_N |

## Storage, UI and analog

| GPIO | MOD1 pin | Signal | Notes |
|---:|---:|---|---|
| 0 | 33 | — | Reserved for the module's optional PSRAM CS |
| 1 | 49 | — | Released spare output |
| 2 | 34 | SD_CD_MCU | SD-card detect |
| 3 | 50 | — | Reserved; on-board backlight switch removed |
| 4 | 35 | SD_MISO_MCU | SPI0 MISO |
| 5 | 51 | SD_CS_MCU | SPI0 chip select |
| 6 | 36 | SD_SCK_MCU | SPI0 clock |
| 7 | 52 | SD_MOSI_MCU | SPI0 MOSI |
| 8 | 37 | I2C_SDA | I2C0 SDA |
| 9 | 53 | I2C_SCL | I2C0 SCL |
| 40 | 8 | AI0_ADC | ADC input |
| 41 | 22 | AI1_ADC | ADC input |
| 42 | 7 | AI2_ADC | ADC input |
| 44 | 6 | AOUT1_PWM | 0-10 V analog output 1 |
| 45 | 20 | AOUT2_PWM | 0-10 V analog output 2 |
| 46 | 5 | AOUT3_PWM | 0-10 V analog output 3 |
| 47 | 19 | AOUT0_PWM | 0-10 V analog output 0 |

## Spare and reserved GPIO

| GPIO | MOD1 pin | Status |
|---:|---:|---|
| 1 | 49 | Spare output on the former backlight control pin |
| 3 | 50 | Spare output; same module edge as GPIO1 |
| 35 | 25 | Backlight PWM, series-protected by R131 |
| 36 | 10 | Spare general-purpose output on the opposite module edge |
| 25 | 30 | Module LED |

## Module power and debug pads

| MOD1 pins | Signal | Motherboard use |
|---:|---|---|
| 1, 2, 16, 32, 47, 61 | GND | Digital ground |
| 31 | 5V | LMR36510 5 V supply |
| 48 | REF | Filtered ADC reference |
| 62 | CLK | SWCLK |
| 63 | DIO | SWDIO |
| 4 | RUN | Not connected; use the WeAct module's onboard reset button |
| 3, 18, 64 | 3V3 | Module-local regulator output; not connected |
| 17 | EN | Not connected |
| 46 | VBUS | Not connected |

Hardware sanity checks pass for pin numbering and duplicate GPIO use. GPIO0 is
reserved exclusively for the module's optional PSRAM chip select.

uCNC requires a project-specific board map. The GP26-GP34 A/B/Z pins are
compatible with the generic interrupt encoder and with the adjacent A/B
requirement of the single-channel RP2350 PIO encoder module. That module still
needs extension before ENC1/ENC2 can use PIO. The standard shift-register
driver can bit-bang all 165/595 pins. GPIO20/21/22 are now ordered
DATA/CLK/LATCH for the optional stock 595 PIO implementation; scanning the
74HC165 inputs still requires separate or custom PIO code. See
[uCNC RP2350 pin compatibility](ucnc-rp2350.md).
