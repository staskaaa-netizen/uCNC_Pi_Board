# WeAct RP2350B pin allocation

This allocation uses the vendor 64-pad footprint numbering and the generated
`MOD1` pin numbers.

## Control, buses and safety

| GPIO | MOD1 pin | Signal | Direction | Notes |
|---:|---:|---|---|---|
| 9 | 53 | `ESTOP_N` | Input | Dedicated isolated E-stop, active low |
| 10 | 38 | `WIFI_TX` | Output | UART1 TX to ESP RX |
| 11 | 54 | `WIFI_RX` | Input | UART1 RX from ESP TX |
| 20 | 43 | `SR_OUT_SER` | Output | 74HC595 serial data |
| 21 | 59 | `SR_SCK` | Output | Shared 74HC165/595 clock |
| 22 | 44 | `SR_LATCH` | Output | 74HC595 latch |
| 23 | 60 | `SR_IN_Q7` | Input | 74HC165 return |
| 24 | 45 | `SR_PL_N` | Output | 74HC165 parallel load |
| 1 | 49 | `SD_CS_MCU` | Output | SPI0 CS |
| 3 | 50 | `PWR_GOOD_N` | Input | LMR36510 power-good |
| 38 | 9 | `I2C_SDA` | Bidirectional | Hardware I2C1 SDA |
| 39 | 23 | `I2C_SCL` | Bidirectional | Hardware I2C1 SCL |
| 43 | 21 | `AI3_ADC` | Input | Analog input 3 |

## Encoders

| GPIO | MOD1 pin | Signal |
|---:|---:|---|
| 26 | 15 | `ENC2_B_3V3` |
| 27 | 29 | `ENC2_A_3V3` |
| 28 | 14 | `ENC1_Z_3V3` |
| 29 | 28 | `ENC1_B_3V3` |
| 30 | 13 | `ENC1_A_3V3` |
| 31 | 27 | `ENC0_Z_3V3` |
| 32 | 12 | `ENC0_B_3V3` |
| 33 | 26 | `ENC0_A_3V3` |
| 25 | 30 | `ENC2_Z_3V3` |

## Display

| GPIO | MOD1 pin | Signal |
|---:|---:|---|
| 12 | 39 | `HSTX_D0_P` |
| 13 | 55 | `HSTX_D0_N` |
| 14 | 40 | `HSTX_D1_P` |
| 15 | 56 | `HSTX_D1_N` |
| 16 | 41 | `HSTX_D2_P` |
| 17 | 57 | `HSTX_D2_N` |
| 18 | 42 | `HSTX_CLK_P` |
| 19 | 58 | `HSTX_CLK_N` |

## Storage and analog

| GPIO | MOD1 pin | Signal | Notes |
|---:|---:|---|---|
| 0 | 33 | — | Reserved for module PSRAM CS |
| 1 | 49 | — | Available GPIO |
| 2 | 34 | `SD_CD_MCU` | SD-card detect |
| 3 | 50 | `PWR_GOOD_N` | LMR36510 power-good |
| 34 | 11 | `SD_SCK_MCU` | SPI0 SCK |
| 35 | 25 | `SD_MOSI_MCU` | SPI0 MOSI |
| 36 | 10 | `SD_MISO_MCU` | SPI0 MISO |
| 37 | 24 | `SD_CS_MCU` | SPI0 CS |
| 40 | 8 | `AI0_ADC` | ADC input 0 |
| 41 | 22 | `AI2_ADC` | ADC input 2 |
| 42 | 7 | `AI1_ADC` | ADC input 1 |
| 43 | 21 | `AI3_ADC` | ADC input 3 |
| 44 | 6 | `AOUT1_PWM` | Analog output 1 |
| 45 | 20 | `AOUT2_PWM` | Analog output 2 |
| 46 | 5 | `AOUT0_PWM` | Analog output 0 |
| 47 | 19 | `AOUT3_PWM` | Analog output 3 |

## Power and debug pads

| MOD1 pins | Signal | Motherboard use |
|---:|---|---|
| 1, 2, 16, 32, 47 | GND | Digital ground |
| 31 | 5V | LMR36510 5 V input |
| 48 | REF | Filtered ADC reference |
| 61-64 | DEBUG | Intentionally unconnected |
| 4 | RUN | Not connected |
| 3, 18 | 3V3 | Module-local regulator output |
| 17 | EN | Not connected |
| 46 | VBUS | Not connected |
