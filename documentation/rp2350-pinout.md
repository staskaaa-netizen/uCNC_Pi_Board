# WeAct RP2350B pin allocation

This is a grouped view of the generated `MOD1` socket mapping. The complete
GPIO table is in [GPIO map](gpio-map.md).

## Control, storage and safety

| Function | GPIO | MOD1 pin | Notes |
|---|---:|---:|---|
| E-stop | 9 | 53 | Active-low, dedicated input |
| Wi-Fi TX | 10 | 38 | To ESP RX |
| Wi-Fi RX | 11 | 54 | From ESP TX |
| Shift data | 20 | 43 | 74AHCT595 serial input |
| Shift clock | 21 | 59 | 74HC165 and 74AHCT595 clock |
| Shift latch | 22 | 44 | 74AHCT595 latch |
| Shift input return | 23 | 60 | 74HC165 Q7 |
| Shift parallel load | 24 | 45 | Active-low input load |
| SD clock | 34 | 11 | SPI0 SCK |
| SD MOSI | 35 | 25 | SPI0 MOSI |
| SD MISO | 36 | 10 | SPI0 MISO |
| SD chip select | 37 | 24 | Active low |
| SD card detect | 2 | 34 | Enabled by JP5 |
| Power-good | 3 | 50 | U1 open-drain output |
| I2C SDA | 38 | 9 | External pull-up |
| I2C SCL | 39 | 23 | External pull-up |

GPIO1 on MOD1 pin 49 is not connected.

## Encoders

| Encoder | A | B | Z |
|---|---|---|---|
| ENC0 | GPIO33 / pin 26 | GPIO32 / pin 12 | GPIO31 / pin 27 |
| ENC1 | GPIO30 / pin 13 | GPIO29 / pin 28 | GPIO28 / pin 14 |
| ENC2 | GPIO27 / pin 29 | GPIO26 / pin 15 | GPIO25 / pin 30 |

U28 converts the A/B/Z signals from J13-J15 to 3.3 V logic. ENC2_Z instead uses
the R110/R111 divider at J15.

## LCD

| Pair | Positive | Negative | J22 row |
|---|---|---|---|
| D0 | GPIO12 / pin 39 | GPIO13 / pin 55 | Row 4 |
| D1 | GPIO14 / pin 40 | GPIO15 / pin 56 | Row 5 |
| D2 | GPIO16 / pin 41 | GPIO17 / pin 57 | Row 6 |
| Clock | GPIO18 / pin 42 | GPIO19 / pin 58 | Row 8 |

## Analog

| Channel | GPIO | MOD1 pin | Connector |
|---|---:|---:|---|
| AI0 | 40 | 8 | J24 pin 2 |
| AI1 | 42 | 7 | J24 pin 3 |
| AI2 | 41 | 22 | J24 pin 4 |
| AI3 | 43 | 21 | J24 pin 5 |
| AOUT0 | 46 | 5 | J25 pin 2 |
| AOUT1 | 44 | 6 | J25 pin 3 |
| AOUT2 | 45 | 20 | J25 pin 4 |
| AOUT3 | 47 | 19 | J25 pin 5 |

## Expansion

| Signal | GPIO | MOD1 pin | J51 pin |
|---|---:|---:|---:|
| `EXP_GPIO4` | 4 | 35 | 3 |
| `EXP_GPIO5` | 5 | 51 | 4 |
| `EXP_GPIO6` | 6 | 36 | 5 |
| `EXP_GPIO7` | 7 | 52 | 6 |
| `EXP_GPIO8` | 8 | 37 | 7 |

## Module power and debug

| MOD1 pins | Signal | Motherboard use |
|---:|---|---|
| 1, 2, 16, 32, 47 | GND | Logic ground |
| 31 | 5V | `+5V` input |
| 48 | REF | `+3V3_A` ADC reference |
| 3, 18 | 3V3 | Module-local output, unconnected |
| 4 | RUN | Unconnected |
| 17 | EN | Unconnected |
| 46 | VBUS | Unconnected |
| 61-64 | DEBUG | Unconnected |

GPIO0 on MOD1 pin 33 is reserved for the optional PSRAM on the WeAct module.
