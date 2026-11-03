# RP2350 GPIO and WeAct socket map

## Module identity

- Module: WeAct Studio RP2350B Core Board, 48 GPIO, 16 MiB flash.
- Body: 41.402 mm x 41.148 mm.
- Socket: two staggered 2.54 mm perimeter rows plus four internal debug pads.
- Board reference: MOD1.
- The socket footprint uses `MOD1.<n>` pin numbers from the official published
  pad coordinates. Use this table rather than visual pad proximity.

The WeAct `5V` pin is supplied from the motherboard `+5V` rail. The module's
onboard regulator powers the RP2350 and its own 3.3 V pins; those pins are not
connected to the separate motherboard `+3V3` rail.

The module's reset button, POR/BOR, watchdog and USB interface are used. MOD1
`RUN` is not connected to the motherboard.

## GPIO allocation

| GPIO | MOD1 pin | Signal | Direction | Function | Firmware note |
|---:|---:|---|---|---|---|
| 0 | 33 | - | Reserved | Module PSRAM CS | Leave free for module PSRAM |
| 1 | 49 | - | - | Not connected | Available |
| 2 | 34 | `SD_CD_MCU` | Input | SD card detect | Active low; close JP5 to enable |
| 3 | 50 | `PWR_GOOD_N` | Input | U1 power-good | Open-drain with R73 pull-up |
| 4 | 35 | `EXP_GPIO4` | Bidirectional | J51 pin 3 | Digital / PIO / PWM |
| 5 | 51 | `EXP_GPIO5` | Bidirectional | J51 pin 4 | Digital / PIO / PWM |
| 6 | 36 | `EXP_GPIO6` | Bidirectional | J51 pin 5 | Digital / PIO / PWM |
| 7 | 52 | `EXP_GPIO7` | Bidirectional | J51 pin 6 | Digital / PIO / PWM |
| 8 | 37 | `EXP_GPIO8` | Bidirectional | J51 pin 7 | Digital / PIO / PWM |
| 9 | 53 | `ESTOP_N` | Input | Dedicated isolated E-stop | Active low |
| 10 | 38 | `WIFI_TX` | Output | UART1 TX to ESP RX | 3.3 V |
| 11 | 54 | `WIFI_RX` | Input | UART1 RX from ESP TX | 3.3 V |
| 12 | 39 | `HSTX_D0_P` | Output | LCD D0+ | HSTX |
| 13 | 55 | `HSTX_D0_N` | Output | LCD D0- | HSTX |
| 14 | 40 | `HSTX_D1_P` | Output | LCD D1+ | HSTX |
| 15 | 56 | `HSTX_D1_N` | Output | LCD D1- | HSTX |
| 16 | 41 | `HSTX_D2_P` | Output | LCD D2+ | HSTX |
| 17 | 57 | `HSTX_D2_N` | Output | LCD D2- | HSTX |
| 18 | 42 | `HSTX_CLK_P` | Output | LCD clock+ | HSTX |
| 19 | 58 | `HSTX_CLK_N` | Output | LCD clock- | HSTX |
| 20 | 43 | `SR_OUT_SER` | Output | 74AHCT595 serial data | PIO DATA |
| 21 | 59 | `SR_SCK` | Output | Shared 74HC165/595 clock | PIO CLK |
| 22 | 44 | `SR_LATCH` | Output | 74AHCT595 latch | PIO LATCH |
| 23 | 60 | `SR_IN_Q7` | Input | 74HC165 return | Remove module R16 before use |
| 24 | 45 | `SR_PL_N` | Output | 74HC165 parallel load | Active low |
| 25 | 30 | `ENC2_Z_3V3` | Input | Encoder 2 index | R110/R111 divider; module LED |
| 26 | 15 | `ENC2_B_3V3` | Input | Encoder 2 B | U28 pin 11 |
| 27 | 29 | `ENC2_A_3V3` | Input | Encoder 2 A | U28 pin 12 |
| 28 | 14 | `ENC1_Z_3V3` | Input | Encoder 1 index | U28 pin 13 |
| 29 | 28 | `ENC1_B_3V3` | Input | Encoder 1 B | U28 pin 14 |
| 30 | 13 | `ENC1_A_3V3` | Input | Encoder 1 A | U28 pin 15 |
| 31 | 27 | `ENC0_Z_3V3` | Input | Encoder 0 index | U28 pin 16 |
| 32 | 12 | `ENC0_B_3V3` | Input | Encoder 0 B | U28 pin 17 |
| 33 | 26 | `ENC0_A_3V3` | Input | Encoder 0 A | U28 pin 18 |
| 34 | 11 | `SD_SCK_MCU` | Output | SPI SCK | U28 side is unrelated |
| 35 | 25 | `SD_MOSI_MCU` | Output | SPI MOSI | RN44 pin 2 |
| 36 | 10 | `SD_MISO_MCU` | Input | SPI MISO | RN44 pin 4 |
| 37 | 24 | `SD_CS_MCU` | Output | SPI CS | RN44 pin 1 |
| 38 | 9 | `I2C_SDA` | Bidirectional | I2C SDA | External pull-up required |
| 39 | 23 | `I2C_SCL` | Bidirectional | I2C SCL | External pull-up required |
| 40 | 8 | `AI0_ADC` | Input | ADC input 0 | 100 k / 33 k at J24 |
| 41 | 22 | `AI2_ADC` | Input | ADC input 2 | 100 k / 33 k at J24 |
| 42 | 7 | `AI1_ADC` | Input | ADC input 1 | 100 k / 33 k at J24 |
| 43 | 21 | `AI3_ADC` | Input | ADC input 3 | 100 k / 33 k at J24 |
| 44 | 6 | `AOUT1_PWM` | Output | Analog output 1 PWM | U38 channel 1 |
| 45 | 20 | `AOUT2_PWM` | Output | Analog output 2 PWM | U38 channel 2 |
| 46 | 5 | `AOUT0_PWM` | Output | Analog output 0 PWM | U38 channel 0 |
| 47 | 19 | `AOUT3_PWM` | Output | Analog output 3 PWM | U38 channel 3 |

## Power, reference and debug pads

| MOD1 pins | Signal | Motherboard connection |
|---:|---|---|
| 1, 2, 16, 32, 47 | GND | Logic ground |
| 31 | 5V | LMR36510 `+5V` input |
| 48 | REF | FB1/C15-filtered `+3V3_A` |
| 61-64 | DEBUG | Intentionally unconnected |
| 3, 18 | 3V3 | Module-local regulator output, not connected |
| 4 | RUN | Not connected |
| 17 | EN | Not connected |
| 46 | VBUS | Not connected |

## Pin grouping

- GPIO12-19 are the eight HSTX differential source pins.
- GPIO20-22 are contiguous for the optional 74AHCT595 output-only PIO path.
- GPIO25-33 contain adjacent encoder pairs and three index inputs.
- GPIO34-37 are the SPI0 storage pins.
- GPIO38/39 are the I2C pins adjacent to the side-1 header.
- GPIO40-43 are the four ADC inputs.
- GPIO44-47 are the four analog-output PWM sources.

## Firmware hazards

- Remove WeAct module resistor R16 to isolate GPIO23 from the onboard USER-key
  network. Do not use that key as a machine control.
- GPIO25 also drives the module's onboard LED.
- Open-collector encoders require external pull-ups.
- Keep GPIO20/21/22 as DATA/CLK/LATCH if the uCNC output-only PIO driver is
  selected.
- The stock bit-banged uCNC shift-register driver is required until a combined
  74HC165/74AHCT595 PIO implementation is available.
- The four analog outputs are not safety outputs. Force PWM to zero in firmware
  when machine motion is disabled.
