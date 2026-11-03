# Decoupling and power-component map

This page separates local IC bypasses, regulator loops, signal filters and load
reservoirs. Reference designators come from the current KiCad netlist.

## Logic and interface ICs

| IC | Device | Supply | Local bypass |
|---|---|---|---|
| U6 | 74HC165D | `3V3` | C22, 100 nF |
| U7 | 74HC165D | `3V3` | C23, 100 nF |
| U8 | 74HC165D | `3V3` | C24, 100 nF |
| U9 | 74HC165D | `3V3` | C25, 100 nF |
| U10 | SN74AHCT595DR | `5V` | C29, 100 nF |
| U11 | SN74AHCT595DR | `5V` | C28, 100 nF |
| U12 | SN74AHCT595DR | `5V` | C27, 100 nF |
| U13 | SN74AHCT595DR | `5V` | C26, 100 nF |
| U28 | SN74AHCT541DW encoder receiver | `3V3` | C119, 100 nF |
| U38 | TLV2374IDR | `AO_12V` | C102, 100 nF |
| U42 | TC74AC541F motion buffer | `5V` | C115, 100 nF |
| U43 | TC74AC541F motion buffer | `5V` | C116, 100 nF |
| MOD1 | WeAct RP2350B module | `5V` input | Module-local capacitors |

U18-U21 are PLC input optocouplers, U35 is the E-stop optocoupler and U61-U64
are general-output optocouplers. These parts have no logic supply pin. U26/U27
are TBD62083AFG arrays and also have no logic-supply bypass requirement.

Each 74HC165/595 and U28/U42/U43 bypass capacitor sits beside its package supply
or ground pin and has a dedicated ground via to the B.Cu plane. The bypass is a
power-rail part; signal filters below are separate.

## Switching regulators

| Regulator | Conversion | Input side | Output side | Compensation and support |
|---|---|---|---|---|
| U1 LMR36510 | `VIN_P` to `5V`, 1 A | C3 22 uF/50 V, C4 100 nF/100 V, C5 22 uF/50 V | C6/C11 22 uF/50 V, C7 100 nF | C86 100 nF BOOT-SW, C91 1 uF VCC-GND, L1 22 uH, R70/R71 upper and R72 lower feedback |
| U3 LMR36510 | isolated 24 V to `BL_12V`, 1 A | C107 22 uF/50 V, C108 100 nF/100 V | C109-C111 22 uF/50 V, C112 100 nF | C113 100 nF BOOT-SW, C114 1 uF VCC-PLC_0V, L2 47 uH, R126/R127/R128 feedback |

U1 and U3 each use six 0.3 mm ground vias under the exposed PowerPAD. Keep the
input capacitors on the VIN/GND side, the inductor at SW and the bootstrap
capacitor between BOOT and SW.

## Linear regulators

| Regulator | Conversion | Input capacitors | Output capacitors | Load |
|---|---|---|---|---|
| U2 AMS1117-3.3 | `5V` to `3V3` | C10 22 uF, C76 100 nF | C13 100 nF, C90 22 uF | Logic, encoders, SD and LCD logic |
| U34 AMS1117-3.3 | `5V` to `WIFI_3V3` | C88 22 uF, C89 100 nF | C69 22 uF, C70 100 nF | ESP-01/ESP-01S only |
| U37 L78L12 | `VIN_P` to `AO_12V` | C100 22 uF | C101 22 uF | U38 and 0-10 V outputs |

U34 has its own regulator because the ESP8266 transmit pulse is independent of
the main peripheral 3.3 V load. U37 is a low-current analog rail and must not be
used for field loads.

## Load and filter capacitors

| Function | Rail or node | Capacitors |
|---|---|---|
| SD power filter at J36/J54 | `SD_3V3` | FB2, C67 10 uF, C68 100 nF |
| ADC reference filter at MOD1 | `ADC_3V3` | FB1, C15 100 nF |
| Encoder 5 V branch | `ENC_5V` | F2 and D53 protection; module-side load bypass |
| 0-10 V output filters | AO0-AO3 | C92/C94/C96/C98 1 uF and C93/C95/C97/C99 100 nF |
| Analog divider filters | AI0-AI3 ADC nodes | C73, C74, C75 and C118, 100 nF each |

C92-C99 are signal-filter capacitors, not supply decoupling. C86 and C113 are
bootstrap capacitors and intentionally do not connect to ground.

The ESP socket uses RN36, a 4 x 10 k array referenced to `WIFI_3V3`, for GPIO2,
GPIO0, EN and RST.

## SD series and pull-up networks

RN43 provides 10 k pull-ups for CS, MOSI, MISO and card detect. Its common side
is `SD_3V3`. RN44 provides 22 ohm series resistors for CS, MOSI, MISO and SCK.
DAT1 and DAT2 remain unconnected in SPI mode.

## Net classes

| Class | Track | Clearance | Assignments |
|---|---:|---:|---|
| Default | 0.20 mm | 0.20 mm | Logic and general signals |
| Power | 0.80 mm | 0.30 mm | Main 5 V, 3.3 V and 12 V rails |
| FieldPower | 0.50 mm | 0.50 mm | `PLC_24V`, isolated commons |
| AnalogPower | 0.30 mm | 0.20 mm | `AO_12V` |
| EncoderPower | 0.30 mm | 0.20 mm | Encoder +5 V branch |
| Ground | 0.50 mm | 0.30 mm | GND and ground-via stubs |
| DigitalDiffPair | 0.20 mm | 0.20 mm | HSTX source pairs |
| LVDSConnector | 0.12 mm | 0.12 mm | J22 fan-out |
| Analog | 0.25 mm | 0.25 mm | AI/AOUT signals |

The PCB currently has no unconnected nets. Local bypass placement must be
rechecked after any footprint movement.
