# LeanCam NCC RP2350B HAL Pin Contract

Status: **normative hardware contract**. Update this file, the companion CSV,
the schematic, and the PCB together. Do not silently remap pins in firmware.

- Board: LeanCam NCC / uCNC RP2350B motherboard
- MCU module: WeAct Studio RP2350B Core Board (`MOD1`)
- PCB revision: `da42d9de`
- Machine-readable pin table:
  [`hardware/rp2350-hal-pin-contract.csv`](../hardware/rp2350-hal-pin-contract.csv)
- Contract verifier:
  [`tools/verify_hal_pin_contract.py`](../tools/verify_hal_pin_contract.py)

The PCB netlist and verified PCB pads are authoritative. GPIO numbers alone are
not enough: use the `GPIO`, `MOD1 pin`, net, electrical domain and function
together.

## Electrical rules

- RP2350-side logic is 3.3 V.
- Encoder inputs reach the RP2350 through U28 level translation.
- The four 74AHCT595 outputs run at 5 V and accept 3.3 V RP2350 inputs.
- The 74HC165 registers run at 3.3 V.
- `PLC_0V` is the isolated field return. It is not `GND`.
- E-stop is a controller indication only. It is not a safety-rated energy
  removal path.
- GPIO0 is reserved for optional WeAct PSRAM and must never be reassigned.
- GPIO23 requires removal of WeAct module resistor R16 to isolate the onboard
  USER key.
- GPIO25 also drives the WeAct onboard LED. Do not rely on it being visually
  dark while configured as encoder 2 Z.

## Direct RP2350 pin map

| GPIO | MOD1 | Net | Direction | Domain | Function | Rule |
|---:|---:|---|---|---|---|---|
| 0 | 33 | - | Reserved | 3.3 V | WeAct PSRAM CS | Never assign |
| 1 | 49 | - | NC | 3.3 V | Spare | No PCB connection |
| 2 | 34 | `CD` | Input | 3.3 V | SD detect | Active low; JP5 selects |
| 3 | 50 | `PG_N` | Input | 3.3 V | 5 V power-good | Active low |
| 4 | 35 | `IO4` | Bidir | 3.3 V | J51.3 | Generic I/O |
| 5 | 51 | `IO5` | Bidir | 3.3 V | J51.4 | Generic I/O |
| 6 | 36 | `IO6` | Bidir | 3.3 V | J51.5 | Generic I/O |
| 7 | 52 | `IO7` | Bidir | 3.3 V | J51.6 | Generic I/O |
| 8 | 37 | `IO8` | Bidir | 3.3 V | J51.7 | Generic I/O |
| 9 | 53 | `ESTOP` | Input | 3.3 V | Dedicated E-stop | Active low |
| 10 | 38 | `UART_TX` | Output | 3.3 V | ESP RX | UART1 TX |
| 11 | 54 | `UART_RX` | Input | 3.3 V | ESP TX | UART1 RX |
| 12 | 39 | `HSTX_D0_P` | Output | HSTX | LCD D0+ | Fixed HSTX group |
| 13 | 55 | `HSTX_D0_N` | Output | HSTX | LCD D0- | Fixed HSTX group |
| 14 | 40 | `HSTX_D1_P` | Output | HSTX | LCD D1+ | Fixed HSTX group |
| 15 | 56 | `HSTX_D1_N` | Output | HSTX | LCD D1- | Fixed HSTX group |
| 16 | 41 | `HSTX_D2_P` | Output | HSTX | LCD D2+ | Fixed HSTX group |
| 17 | 57 | `HSTX_D2_N` | Output | HSTX | LCD D2- | Fixed HSTX group |
| 18 | 42 | `HSTX_CLK_P` | Output | HSTX | LCD clock+ | Fixed HSTX group |
| 19 | 58 | `HSTX_CLK_N` | Output | HSTX | LCD clock- | Fixed HSTX group |
| 20 | 43 | `SER0` | Output | 3.3 V in / 5 V chain | 595 serial data | PIO DATA |
| 21 | 59 | `SCK` | Output | 3.3 V in / 5 V chain | Shared shift clock | PIO CLK |
| 22 | 44 | `LAT` | Output | 3.3 V in / 5 V chain | 595 latch | PIO LATCH |
| 23 | 60 | `Q7` | Input | 3.3 V | 165 serial return | Remove WeAct R16 |
| 24 | 45 | `PL` | Output | 3.3 V in / 5 V chain | 165 parallel load | Active low |
| 25 | 30 | `E2_Z3V3` | Input | 3.3 V | ENC2 Z | U28 / divider path |
| 26 | 15 | `E2_B3V3` | Input | 3.3 V | ENC2 B | U28.11 |
| 27 | 29 | `E2_A3V3` | Input | 3.3 V | ENC2 A | U28.12 |
| 28 | 14 | `E1_Z3V3` | Input | 3.3 V | ENC1 Z | U28.13 |
| 29 | 28 | `E1_B3V3` | Input | 3.3 V | ENC1 B | U28.14 |
| 30 | 13 | `E1_A3V3` | Input | 3.3 V | ENC1 A | U28.15 |
| 31 | 27 | `E0_Z3V3` | Input | 3.3 V | ENC0 Z | U28.16 |
| 32 | 12 | `E0_B3V3` | Input | 3.3 V | ENC0 B | U28.17 |
| 33 | 26 | `E0_A3V3` | Input | 3.3 V | ENC0 A | U28.18 |
| 34 | 11 | `SPI_CK` | Output | 3.3 V | SD clock | Storage bus |
| 35 | 25 | `SPI_SI` | Output | 3.3 V | SD MOSI | Storage bus |
| 36 | 10 | `SPI_SO` | Input | 3.3 V | SD MISO | Storage bus |
| 37 | 24 | `SPI_CS` | Output | 3.3 V | SD CS | Active low |
| 38 | 9 | `I2C_SDA` | Bidir | 3.3 V | J18 SDA | External pull-up |
| 39 | 23 | `I2C_SCL` | Bidir | 3.3 V | J18 SCL | External pull-up |
| 40 | 8 | `ADC0` | Analog input | 0-3.3 V | AI0 | J24.2 |
| 41 | 22 | `ADC2` | Analog input | 0-3.3 V | AI2 | J24.4 |
| 42 | 7 | `ADC1` | Analog input | 0-3.3 V | AI1 | J24.3 |
| 43 | 21 | `ADC3` | Analog input | 0-3.3 V | AI3 | J24.5 |
| 44 | 6 | `PWM1` | Output | 3.3 V PWM | AO1 | U38 channel 1 |
| 45 | 20 | `PWM2` | Output | 3.3 V PWM | AO2 | U38 channel 2 |
| 46 | 5 | `PWM0` | Output | 3.3 V PWM | AO0 | U38 channel 0 |
| 47 | 19 | `PWM3` | Output | 3.3 V PWM | AO3 | U38 channel 3 |

## Module power and debug pins

| MOD1 pins | Net/use | Contract |
|---:|---|---|
| 1, 2, 16, 32, 47 | `GND` | Logic ground |
| 31 | `5V` | Main 5 V module input |
| 48 | `ADC_3V3` | Filtered ADC reference |
| 3, 18 | Module-local 3.3 V | Must not connect to motherboard `3V3` |
| 4, 17 | RUN / EN | Not connected |
| 46 | VBUS | Not connected |
| 61-64 | Debug | Not connected on the motherboard |

## uCNC HAL constraints

The hardware requires a LeanCam-specific board map. The stock Pico 2 and
Waveshare PiZero maps are not compatible.

```c
#define MCU MCU_RP2350
#define AXIS_COUNT 7
#define TOOL_COUNT 1
#define BAUDRATE 115200

#define IC74HC595_COUNT 4
#define IC74HC165_COUNT 4

#define IC74HC595_PIO_DATA  20
#define IC74HC595_PIO_CLK   21
#define IC74HC595_PIO_LATCH 22

#define ESTOP_BIT 9
#define ESTOP_ACTIVE_LOW

#define SPI_CLK_BIT 34
#define SPI_SDO_BIT 35
#define SPI_SDI_BIT 36
#define SPI_CS_BIT  37

#define I2C_CLK_BIT  39
#define I2C_DATA_BIT 38
```

`IC74HC595_CUSTOM_SHIFT_IO` is optional and output-only. It does not read the
four 74HC165 registers. Until a combined PIO driver exists, use the uCNC
bit-banged shift-register path or allocate a second PIO program for inputs.

SPI peripheral selection, PIO state-machine allocation and shared-enable
semantics must be verified against the exact uCNC RP2350 backend before this
block is made compile-ready.

## Output shift-register contract

Serial order is `GPIO20 -> U13 -> U12 -> U11 -> U10`. Latch with GPIO22 after
all 32 bits are shifted.

| Bit | uCNC offset | Signal | Physical destination |
|---:|---|---|---|
| 0 | `STEP0_IO_OFFSET = 0` | `STP0` | J10.2 |
| 1 | `DIR0_IO_OFFSET = 1` | `DIR0` | J10.3 |
| 2 | `STEP1_IO_OFFSET = 2` | `STP1` | J11.2 |
| 3 | `DIR1_IO_OFFSET = 3` | `DIR1` | J11.3 |
| 4 | `STEP2_IO_OFFSET = 4` | `STP2` | J28.2 |
| 5 | `DIR2_IO_OFFSET = 5` | `DIR2` | J28.3 |
| 6 | `STEP3_IO_OFFSET = 6` | `STP3` | J29.2 |
| 7 | `DIR3_IO_OFFSET = 7` | `DIR3` | J29.3 |
| 8 | `STEP6_IO_OFFSET = 8` | `STP6` | J30.2 |
| 9 | `DIR6_IO_OFFSET = 9` | `DIR6` | J30.3 |
| 10 | `STEP5_IO_OFFSET = 10` | `STP5` | J46.2 |
| 11 | `DIR5_IO_OFFSET = 11` | `DIR5` | J46.3 |
| 12 | `STEP4_IO_OFFSET = 12` | `STP4` | J47.2 |
| 13 | `DIR4_IO_OFFSET = 13` | `DIR4` | J47.3 |
| 14 | shared enable | `EN3` | J10.1, J11.1, J28.1 |
| 15 | shared enable | `EN4` | J29.1, J30.1, J46.1, J47.1 |
| 16 | `DOUT0_IO_OFFSET = 16` | `D01` | J12.1 |
| 17 | `DOUT1_IO_OFFSET = 17` | `D02` | J12.2 |
| 18 | `DOUT2_IO_OFFSET = 18` | `D03` | J12.3 |
| 19 | `DOUT3_IO_OFFSET = 19` | `D04` | J12.4 |
| 20 | `DOUT4_IO_OFFSET = 20` | `D05` | J12.5 |
| 21 | `DOUT5_IO_OFFSET = 21` | `D06` | J12.6 |
| 22 | `DOUT6_IO_OFFSET = 22` | `D07` | J12.7 |
| 23 | `DOUT7_IO_OFFSET = 23` | `D08` | J12.8 |
| 24 | `DOUT8_IO_OFFSET = 24` | `D09` | J32.1 |
| 25 | `DOUT9_IO_OFFSET = 25` | `D10` | J32.2 |
| 26 | `DOUT10_IO_OFFSET = 26` | `D11` | J32.3 |
| 27 | `DOUT11_IO_OFFSET = 27` | `D12` | J32.4 |
| 28 | `DOUT12_IO_OFFSET = 28` | `D13` | J32.5 |
| 29 | `DOUT13_IO_OFFSET = 29` | `D14` | J32.6 |
| 30 | `DOUT14_IO_OFFSET = 30` | `D15` | J32.7 |
| 31 | `DOUT15_IO_OFFSET = 31` | `D16` | J32.8 |

The two enable bits are shared across axes. Do not toggle one axis enable while
assuming the other axes sharing that bit are independent.

## Axis contract

Axes follow the physical connector order, not shift-bit order.

| Axis | STEP bit | DIR bit | Enable | Output connector | Status connector |
|---|---:|---:|---|---|---|
| A0 | 0 | 1 | `EN3`, bit 14 | J10 | J40 |
| A1 | 2 | 3 | `EN3`, bit 14 | J11 | J41 |
| A2 | 4 | 5 | `EN3`, bit 14 | J28 | J42 |
| A3 | 6 | 7 | `EN4`, bit 15 | J29 | J43 |
| A4 | 12 | 13 | `EN4`, bit 15 | J47 | J50 |
| A5 | 10 | 11 | `EN4`, bit 15 | J46 | J49 |
| A6 | 8 | 9 | `EN4`, bit 15 | J30 | J48 |

Motion connector electrical order is always pin 1 `EN`, pin 2 `STEP`, pin 3
`DIR`. Status connector order is pin 1 `GND`, pin 2 `ERROR`, pin 3 `ZERO`.

## Input shift-register contract

Chain: `U6 -> U7 -> U8 -> U9 -> GPIO23`. Clock GPIO21. Pulse GPIO24 low to
load, then shift 32 bits. Bit 0 below is the first bit returned after `PL` is
released.

| Stream bit | Register pin | Logical signal | Function |
|---:|---:|---|---|
| 0 | U9.6 | `I16` | PLC input 16 |
| 1 | U9.5 | `I15` | PLC input 15 |
| 2 | U9.4 | `I14` | PLC input 14 |
| 3 | U9.3 | `I13` | PLC input 13 |
| 4 | U9.14 | `I12` | PLC input 12 |
| 5 | U9.13 | `I11` | PLC input 11 |
| 6 | U9.12 | `I10` | PLC input 10 |
| 7 | U9.11 | `I09` | PLC input 9 |
| 8 | U8.6 | `I08` | PLC input 8 |
| 9 | U8.5 | `I07` | PLC input 7 |
| 10 | U8.4 | `I06` | PLC input 6 |
| 11 | U8.3 | `I05` | PLC input 5 |
| 12 | U8.14 | `I04` | PLC input 4 |
| 13 | U8.13 | `I03` | PLC input 3 |
| 14 | U8.12 | `I02` | PLC input 2 |
| 15 | U8.11 | `I01` | PLC input 1 |
| 16 | U7.6 | `ERR2` | A2 error |
| 17 | U7.5 | `Z2` | A2 zero |
| 18 | U7.4 | `ERR1` | A1 error |
| 19 | U7.3 | `Z1` | A1 zero |
| 20 | U7.14 | `U7_IN14` | Spare J55.3 |
| 21 | U7.13 | `U7_IN13` | Spare J55.2 |
| 22 | U7.12 | `ERR3` | A3 error |
| 23 | U7.11 | `Z3` | A3 zero |
| 24 | U6.6 | `Z5` | A5 zero |
| 25 | U6.5 | `ERR5` | A5 error |
| 26 | U6.4 | `Z6` | A6 zero |
| 27 | U6.3 | `ERR6` | A6 error |
| 28 | U6.14 | `ERR4` | A4 error |
| 29 | U6.13 | `Z4` | A4 zero |
| 30 | U6.12 | `ERR0` | A0 error |
| 31 | U6.11 | `Z0` | A0 zero |

If uCNC logical input names must remain monotonic (`I01` first), the board map
must remap `DIN*_IO_OFFSET`; do not rewrite the physical stream table.

## Fixed connector contracts

| Connector | Pin order |
|---|---|
| J7 | `I01, I02, I03, I04, I05, I06, I07, I08` |
| J8 | `I09, I10, I11, I12, I13, I14, I15, I16` |
| J12 | `D01, D02, D03, D04, D05, D06, D07, D08` |
| J32 | `D09, D10, D11, D12, D13, D14, D15, D16` |
| J13 | `+5V, A0, B0, Z0, GND` |
| J14 | `+5V, A1, B1, Z1, GND` |
| J15 | `+5V, A2, B2, Z2, GND` |
| J18 | `SDA, SCL, 3V3, 5V, GND` |
| J24 | `GND, AI0, AI1, AI2, AI3` |
| J25 | `GND, AO0, AO1, AO2, AO3` |
| J51 | `3V3, GND, GPIO4, GPIO5, GPIO6, GPIO7, GPIO8` |
| J55 | `GND, U7_IN13, U7_IN14` |

## HAL implementation gates

Before changing uCNC firmware:

1. Run `verify_hal_pin_contract.py` against the PCB.
2. Confirm the selected encoder backend and polarity for A/B and Z.
3. Confirm PIO allocation for encoder, 595 output and any 165 input scanner.
4. Preserve the shared `EN3`/`EN4` behavior in the motion abstraction.
5. Keep analog outputs at zero whenever motion is disabled.
6. Treat E-stop as an input signal, not as a hard-wired safety output.
