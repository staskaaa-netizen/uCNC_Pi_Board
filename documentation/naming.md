# Signal naming

The schematic and PCB use short, direct names. Prefixes identify the connector
or circuit side; they do not repeat physical explanations.

## Power and field

| Name | Meaning |
|---|---|
| `VIN` | Raw machine input |
| `VIN_F` | Fused input |
| `VIN_P` | Protected 5 V converter input |
| `5V` | Main 5 V rail |
| `3V3` | Peripheral logic rail |
| `WIFI_3V3` | ESP module rail |
| `SD_3V3` | Filtered microSD rail |
| `ADC_3V3` | ADC reference filter rail |
| `ENC_5V` | Fused encoder 5 V rail |
| `PLC_24V` | PLC 24+ terminal |
| `PLC_0V` | PLC - return |
| `BL_VIN` | Protected backlight converter input |
| `BL_12V` | Isolated backlight 12 V output |
| `AO_12V` | Analog-output regulator rail |

J1 lists `24+ -` in pin order. J33 and J45 list `PLC24+ PLC-` in pin order.
These assignments come from the PCB pad nets, not from connector-body
orientation.

## PLC inputs

| Pattern | Meaning |
|---|---|
| `I01-I16` | External PLC inputs and connector nets |
| `I01_N-I16_N` | Isolated logic-side inputs |
| `LI01-LI16` | Indicator LED nodes |
| `OI01-OI16` | Optocoupler input nodes |

The PLC range is `n=1..16`.

## Motion axes

Axis numbers follow the physical top-to-bottom connector order:

| Axis | Output | Input |
|---|---|---|
| A0 | J10 | J40 |
| A1 | J11 | J41 |
| A2 | J28 | J42 |
| A3 | J29 | J43 |
| A4 | J47 | J50 |
| A5 | J46 | J49 |
| A6 | J30 | J48 |

Motion nets are `STPn`, `DIRn`, `ERRn`, and `Zn`. Shared enables are `EN3`
and `EN4`. The output shift-register bits are deliberately non-sequential:

- Bits 8-9 drive A6.
- Bits 12-13 drive A4.

Each motion output connector is `ENx STPx DIRx`. Each status connector is
`GND ERRx Zx`.
The PCB-facing motion labels are presented in physical reading order as
`DIRx STPx ENx`; the electrical pin order remains `EN/STEP/DIR`.

## Digital chains

| Pattern | Meaning |
|---|---|
| `SER0-SER3` | 74AHCT595 serial chain |
| `IN0-IN3` | 74HC165 serial chain |
| `Q7` | Input-chain return to GPIO23 |
| `SCK` | Shared shift clock |
| `LAT` | Output latch |
| `PL` | Input parallel load |

## SPI, expansion and analog

| Pattern | Meaning |
|---|---|
| `SPI_CK/SI/SO/CS` | RP2350-side SPI |
| `SD_CK/SI/SO/CS` | SD-card side |
| `CD` | Card detect |
| `IO4-IO8` | Expansion GPIO |
| `ADC0-ADC3` | ADC divider nodes |
| `PWM0-PWM3` | Analog-output PWM sources |
| `AO0-AO3` | Analog outputs |
