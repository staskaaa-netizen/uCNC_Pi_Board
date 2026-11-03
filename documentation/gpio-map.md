# RP2350 GPIO and WeAct socket map

## Module identity

- Module: WeAct Studio RP2350B Core Board, 48 GPIO, 16 MiB flash.
- Official body size: 41.402 mm x 41.148 mm.
- Socket: two staggered 2.54 mm perimeter rows plus four internal debug pads.
- Board reference: `MOD1`.
- The socket footprint uses `MOD1.<n>` pin numbers generated from the official
  published pad coordinates. Use the identifying signal and GPIO in the table,
  not visual proximity, when replacing the module.

The WeAct `5V` pin is supplied from the motherboard 5 V rail and feeds the
module's onboard 3.3 V regulator. The module `3V3` output pins remain local to
the module; the separately regulated peripheral `+3V3` rail is not tied to them.
VBUS and regulator-enable are not connected to motherboard peripherals. GPIO25
is connected to the module's onboard LED and is also allocated to `ENC2_Z`;
remove the module-side LED series resistor when a clean digital input is
required. GPIO23 is repurposed as the 74HC165 return, so the module's onboard
USER key must not be used. The module's reset button, POR/BOR and watchdog are
used; MOD1 `RUN` is not connected, and no duplicate reset button or external
supervisor is fitted. The four 74HC595 `~SRCLR` pins are tied to `+3V3`.

## Allocation

| GPIO | MOD1 pin | Signal | Direction | Peripheral / function | Voltage | Firmware note |
|---:|---:|---|---|---|---|---|
| 0 | 33 | — | Reserved | Module PSRAM chip select | 3.3 V | Left free for the module's solderable PSRAM |
| 1 | 49 | — | Reserved | Not connected | — | Available GPIO |
| 2 | 34 | SD_CD_MCU | Input | SD-card detect | 3.3 V | Active low; bridge JP5 to enable |
| 3 | 50 | PWR_GOOD_N | Input | LMR36510 power-good | 3.3 V | Open-drain, pulled up to +3V3 |
| 4 | 35 | — | Reserved | Not connected | — | Available GPIO |
| 5 | 51 | — | Reserved | Not connected | — | Available GPIO |
| 6 | 36 | — | Reserved | Not connected | — | Available GPIO |
| 7 | 52 | — | Reserved | Not connected | — | Available GPIO |
| 8 | 37 | — | Reserved | Not connected | — | Released from I2C0 |
| 9 | 53 | ESTOP_N | Input | Dedicated isolated E-stop | 3.3 V | Active low; external hardware blocks outputs |
| 10 | 38 | WIFI_TX | Output | UART1 TX | 3.3 V | Direct to ESP-01/ESP-01S RX |
| 11 | 54 | WIFI_RX | Input | UART1 RX | 3.3 V | Direct from ESP-01/ESP-01S TX |
| 12 | 39 | HSTX_D0_P | Output | HSTX lane 0 positive | 3.3 V differential | LCD LVDS D0+ driver input |
| 13 | 55 | HSTX_D0_N | Output | HSTX lane 0 negative | 3.3 V differential | Alternate passive LVDS D0- |
| 14 | 40 | HSTX_D1_P | Output | HSTX lane 1 positive | 3.3 V differential | LCD LVDS D1+ driver input |
| 15 | 56 | HSTX_D1_N | Output | HSTX lane 1 negative | 3.3 V differential | Alternate passive LVDS D1- |
| 16 | 41 | HSTX_D2_P | Output | HSTX lane 2 positive | 3.3 V differential | LCD LVDS D2+ driver input |
| 17 | 57 | HSTX_D2_N | Output | HSTX lane 2 negative | 3.3 V differential | Alternate passive LVDS D2- |
| 18 | 42 | HSTX_CLK_P | Output | HSTX clock positive | 3.3 V differential | LCD LVDS clock+ driver input |
| 19 | 58 | HSTX_CLK_N | Output | HSTX clock negative | 3.3 V differential | Alternate passive LVDS clock- |
| 20 | 43 | SR_OUT_SER | Output | 74HC595 serial input | 3.3 V | PIO DATA; GPIO20/21/22 are consecutive |
| 21 | 59 | SR_SCK | Output | Shared shift clock | 3.3 V | PIO CLK; 74HC165 CP and 74HC595 SRCLK |
| 22 | 44 | SR_LATCH | Output | 74HC595 storage-register clock | 3.3 V | PIO LATCH; rising edge updates all 32 outputs |
| 23 | 60 | SR_IN_Q7 | Input | 74HC165 serial return | 3.3 V | Remove WeAct R16 (0R) to isolate the onboard key network |
| 24 | 45 | SR_PL_N | Output | 74HC165 parallel load | 3.3 V | Active-low pulse before read |
| 25 | 30 | ENC2_Z_3V3 | Input | Encoder 2 Z | 3.3 V | Also connected to the module's onboard LED |
| 26 | 15 | ENC2_B_3V3 | Input | Provisional encoder channel 2 B | 3.3 V | U28 pin 15; connector naming to be revised |
| 27 | 29 | ENC2_A_3V3 | Input | Provisional encoder channel 2 A | 3.3 V | U28 pin 12; connector naming to be revised |
| 28 | 14 | ENC1_Z_3V3 | Input | Provisional encoder channel 1 Z | 3.3 V | U28 pin 13; connector naming to be revised |
| 29 | 28 | ENC1_B_3V3 | Input | Provisional encoder channel 1 B | 3.3 V | U28 pin 14; connector naming to be revised |
| 30 | 13 | ENC1_A_3V3 | Input | Provisional encoder channel 1 A | 3.3 V | U28 pin 15; connector naming to be revised |
| 31 | 27 | ENC0_Z_3V3 | Input | Provisional encoder channel 0 Z | 3.3 V | U28 pin 16; connector naming to be revised |
| 32 | 12 | ENC0_B_3V3 | Input | Provisional encoder channel 0 B | 3.3 V | U28 pin 17; connector naming to be revised |
| 33 | 26 | ENC0_A_3V3 | Input | Provisional encoder channel 0 A | 3.3 V | U28 pin 18; connector naming to be revised |
| 34 | 11 | SD_SCK_MCU | Output | SPI0 SCK | 3.3 V | Located on the side-1 header |
| 35 | 25 | SD_MOSI_MCU | Output | SPI0 MOSI | 3.3 V | Located on the side-1 header |
| 36 | 10 | SD_MISO_MCU | Input | SPI0 MISO | 3.3 V | Located on the side-1 header |
| 37 | 24 | SD_CS_MCU | Output | SPI0 CS | 3.3 V | Active low |
| 38 | 9 | I2C_SDA | Bidirectional | Hardware I2C1 SDA | 3.3 V | External pull-up required |
| 39 | 23 | I2C_SCL | Bidirectional | Hardware I2C1 SCL | 3.3 V | External pull-up required |
| 40 | 8 | AI0_ADC | Input | ADC channel 0 | 0-2.48 V | 0-10 V through 100 k/33 k divider at J24 |
| 41 | 22 | AI2_ADC | Input | ADC channel 2 | 0-2.48 V | 0-10 V through 100 k/33 k divider at J24 |
| 42 | 7 | AI1_ADC | Input | ADC channel 1 | 0-2.48 V | 0-10 V through 100 k/33 k divider at J24 |
| 43 | 21 | AI3_ADC | Input | ADC channel 3 | 0-2.48 V | 0-10 V through 100 k/33 k divider at J24 |
| 44 | 6 | AOUT1_PWM | Output | 0-10 V analog output 1 | 3.3 V PWM | Two-stage RC filter into U38B |
| 45 | 20 | AOUT2_PWM | Output | 0-10 V analog output 2 | 3.3 V PWM | Two-stage RC filter into U38C |
| 46 | 5 | AOUT0_PWM | Output | 0-10 V analog output 0 | 3.3 V PWM | Two-stage RC filter into U38A; 20 kHz recommended |
| 47 | 19 | AOUT3_PWM | Output | 0-10 V analog output 3 | 3.3 V PWM | Two-stage RC filter into U38D |

## Module power pins

| MOD1 pins | Signal | Motherboard connection |
|---:|---|---|
| 1, 2, 16, 32, 47 | GND/G | Digital ground |
| 31 | 5V | LMR36510 +5 V input to the module regulator |
| 48 | REF | Locally filtered `+3V3_A` ADC reference |
| 61-64 | DEBUG | Module pads intentionally unconnected |
| 3, 18, 64 | 3V3 | Module-local regulator output; not connected on motherboard |
| 17 | EN | No connect; module's onboard regulator network controls it |
| 46 | VBUS | No connect |

## Firmware hazards

- GPIO0 is reserved for the module's optional PSRAM chip select and is not used
  by the motherboard.
- GPIO23 carries `SR_IN_Q7`. Before fitting the WeAct module, remove its R16
  (0R) series resistor, which isolates the SW3 USER-key network and the WeAct
  C27 capacitor position from this pin. This is separate from motherboard C27
  (U11 decoupling). Do not press or use the key as a machine control.
- GPIO25 remains attached to the module's onboard LED.
- GPIO12-19 must be assigned to HSTX before driving video.
- The first eight encoder A/B/Z signals feed one non-inverting
  `SN74AHCT541DW` channel powered at 3.3 V. The single `ENC2_Z` input uses R110
  (5.1 k series) and R111 (10 k to GND), producing about 3.31 V from a 5 V
  push-pull output.
- Backlight PWM is not routed on the motherboard; J2 provides isolated 12 V
  power only.
- GPIO47 and GPIO44-GPIO46 are dedicated to the four 0-10 V outputs. Drive them at
  a common PWM frequency and calibrate the maximum duty because the output
  stage has approximately 3.2x gain.
