# Power budget and protection

## Input and regulators

The main machine input is 12-24 V DC. F1 is a 2 A fuse, D1 is an SMBJ24CA
clamp and D2 is an SS16 reverse-polarity diode. C2 provides a local 100 nF
bypass on the fused node.

| Rail | Source | Input | Output | Intended load |
|---|---|---|---|---|
| `5V` | U1 LMR36510, 1 A | `VIN_P` | 22 uH, 2 x 22 uF plus 100 nF | MOD1, U2, U34, U28, encoders |
| `3V3` | U2 AMS1117-3.3 | `5V` | 22 uF plus 100 nF each side | Input logic, 74AHCT595 control, SD, LCD |
| `WIFI_3V3` | U34 AMS1117-3.3 | `5V` | 22 uF plus 100 nF each side | ESP-01/ESP-01S |
| `AO_12V` | U37 L78L12 | `VIN_P` | 22 uF plus 100 nF | U38 and 0-10 V outputs |
| `BL_12V` | U3 isolated LMR36510, 1 A | isolated `PLC_24V` | 47 uH, 3 x 22 uF plus 100 nF | Backlight/CCFL input |

U1 feedback uses R70 and R71 in the upper leg and R72 in the lower leg. U3
feedback uses R126 in the upper leg and R127/R128 in the lower leg. U1 and U3
each have six 0.3 mm thermal vias in their PowerPAD land; U3's array is tied to
`PLC_0V`.

Thermal-relief zone connections are intentionally limited to the two switching
regulators. Other `GND` and `PLC_0V` pads use solid zone connections so the
two-spoke rule does not create unrelated starved-thermal warnings.

The WeAct module receives `5V` and uses its own onboard 3.3 V regulator.
Do not connect that regulator output to the motherboard `3V3` rail.

## Estimated loads

| Load | Typical | Peak | Source |
|---|---:|---:|---|
| WeAct RP2350B module | 90 mA | 150 mA | `5V` |
| 74HC logic and indicators | 60 mA | 130 mA | `3V3` / `5V` |
| MicroSD | 30 mA | 120 mA | `SD_3V3` |
| ESP-01/ESP-01S | 80 mA | 500 mA | `WIFI_3V3` |
| Encoders | 30 mA | 150 mA | `ENC_5V` |
| Four analog outputs | 3 mA | 12 mA | `AO_12V` |
| PLC contact current | 110 mA | 167 mA | external `PLC_24V` |
| Backlight input | load dependent | 1 A | `BL_12V` |

U1 is sized for the expected 100-200 mA motherboard load with substantial
margin. The ESP peak current is the reason for its dedicated U34 regulator and
local reservoir. Keep U2's continuous output below 500 mA and use copper area
for thermal margin.

Do not operate the ESP at peak transmit while all other 3.3 V logic and a
high-current backlight are simultaneously loaded without measuring the 5 V
converter input current and temperature.

F2 is a separate 500 mA encoder-branch fuse and D53 is an SMAJ5.0A clamp. This
branch is not part of the main field-isolated domain.

## Field power

J33 and J45 are parallel 1=PLC24+ 2=PLC- inputs. The PLC domain supplies:

- PLC contact loops through U18-U21.
- The E-stop loop through U35.
- General-output optocoupler collectors through U61-U64.
- TBD62083AFG clamp and reference pins.
- The isolated backlight converter U3.

The isolated domain must not connect to the logic GND plane. D3 protects U3
from reverse connection to J33/J45.

Each PLC input uses a 2.2 k field-side series resistor. With approximately 3 V
total LED drop at 24 V, the nominal loop current is about 9.5 mA. Each general
output has a 4 x 1 k optocoupler drive network and a TBD62083AFG low-side output.
External loads must be powered from the isolated field rail and must respect
the TBD62083AFG channel, package and temperature limits.

## Analog-output rail

U37 is a 100 mA linear regulator from `VIN_P`. Its expected load is the
TLV2374 quiescent current, feedback dividers and high-impedance analog inputs.
At 24 V input and a few milliamps, the regulator dissipation is small. Do not
use `AO_12V` for solenoids, lamps or other high-current field loads.

The ideal 0-10 V output full scale is about 10.56 V with 3.3 V PWM and the
3.2x gain stage. Firmware must clamp the calibrated maximum duty below 100%.

## Safety boundary

The 74AHCT595 output enables and TC74AC541F buffers are always active. The
board does not provide a local safety-rated output interlock. Motor power,
hazardous output supplies and energy removal must be handled by an independent
hard-wired safety circuit.

The E-stop optocoupler provides an isolated controller indication only. It does
not remove motor or field power.
