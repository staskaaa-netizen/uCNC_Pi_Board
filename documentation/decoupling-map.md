# Decoupling capacitor map

This map separates digital/interface bypass capacitors from regulator input,
output, compensation and bulk capacitors. Reference assignments come from the
regenerated netlist. Placement status comes from checkpoint 55.

## Logic and interface ICs

| IC | Device | Supply | Local decoupling |
|---|---|---|---|
| U6 | 74HC165D input shift register | +3V3 | C22, 100 nF |
| U7 | 74HC165D input shift register | +3V3 | C23, 100 nF |
| U8 | 74HC165D input shift register | +3V3 | C24, 100 nF |
| U9 | 74HC165D input shift register | +3V3 | C25, 100 nF |
| U10 | 74HC595D output shift register | +3V3 | C26, 100 nF |
| U11 | 74HC595D output shift register | +3V3 | C27, 100 nF |
| U12 | 74HC595D output shift register | +3V3 | C28, 100 nF |
| U13 | 74HC595D output shift register | +3V3 | C29, 100 nF |
| U24 | SN74AHCT541DW motion buffer | +5V | C53, 100 nF |
| U25 | SN74AHCT541DW motion buffer | +5V | C54, 100 nF |
| U28 | SN74AHCT541DW encoder buffer | +3V3 | C57, 100 nF |
| MOD1 | WeAct RP2350B module | +5V input | On-module decoupling; no separate motherboard bypass assigned |

U26 and U27 are ULN2003A open-collector arrays and have no logic supply pin.
C55 and C56 (100 nF) are fitted between their `DO_COM` clamp rail and GND.
They are field-output rail clamps, not IC VCC bypass capacitors.

U18-U21 are LTV-847S four-channel phototransistor optocouplers; U35/U36 are
individual EL3H7 DIP-4 safety optocouplers. They have no VCC pin. Each used
output collector has one individual 4.7 k pull-up to `+3V3`. The former input
filter capacitors and pull-up arrays are removed; firmware provides debounce
timing.

U30-U32 are TPD4E05U06 ESD clamp arrays and have no supply pin, so they require
no VCC decoupling capacitor.

## Voltage regulators

| Regulator | Rail and role | Input capacitors | Output/VCC capacitors | Other |
|---|---|---|---|---|
| U1 LMR36510ADDAR | VIN_PROT to +5V, 1 A buck | C3 10 uF/50 V, C4 100 nF/100 V, C5 22 uF/50 V | C6 22 uF/10 V, C7 100 nF, C8 10 uF, C11 22 uF/10 V | C86 100 nF BOOT-to-SW; C91 1 uF VCC-to-GND |
| U2 AMS1117-3.3 | +5V to peripheral +3V3 | C10 10 uF, C76 100 nF | C13 100 nF, C90 22 uF | Supplies logic, SD, J22 LCD logic and analog prefilter |
| U34 AMS1117-3.3 | +5V to ESP +3V3_WIFI | C88 10 uF at `(202.80, 37.00)`, C89 100 nF at `(197.80, 37.00)` | C69 10 uF at `(195.00, 49.00)`, C70 100 nF at `(190.20, 41.20)` | Dedicated ESP-01S rail |
| U40 TBA2-0512 | +5V to isolated +12V_FIELD | C103 10 uF at `(30.50, 54.00)` on F.Cu | C105 10 uF/100 V at `(20.50, 54.00)` on F.Cu, after D56 | Dry-contact wetting supply |
| U37 L78L12 | VIN_PROT to +12V_AO | C100 1 uF/50 V | C101 10 uF/25 V | Supplies U38 only |

U38 TLV2374 uses C102 (100 nF) from `+12V_AO` to GND directly at the package.
C92/C94/C96/C98 are the 1 uF first-stage PWM filter capacitors, while
C93/C95/C97/C99 are the 100 nF second-stage filter capacitors. They are signal
filter parts, not power-rail decoupling.

For U1, C3-C5 form the input loop, C6/C7/C8/C11 form the output filter, C86 is
the bootstrap capacitor and C91 is the internal VCC bypass. The 0.3 mm thermal
vias under the PowerPAD tie the exposed pad to the B.Cu GND plane.

## Module and connector-local rail capacitors

| Load | Rail | Capacitors |
|---|---|---|
| ESP-01S at J20 | +3V3_WIFI | C69 10 uF, C70 100 nF |
| SD card at J19 | +3V3_SD | C67 10 uF at `(166.80, 75.70)`, C68 100 nF at `(166.80, 70.80)`; FB2 at `(166.80, 67.62)` |
| HDMI at J23 | +5V_HDMI | C71 10 uF, C72 100 nF |

These are local load or connector bypasses, not IC decoupling.

## Current placement qualification

Checkpoint 55 has zero placement DRC violations. U2 remains at the user-selected
front-side location `(198.12, 94.00)`, beside the main 5 V power stage. Its four
local capacitors are grouped around it:

| Capacitor | Role | Position (mm) | Rotation |
|---|---|---:|---:|
| C76 | 100 nF input bypass | 191.135, 94.000 | 90 deg |
| C13 | 100 nF output bypass | 191.135, 89.555 | 90 deg |
| C10 | 10 uF input bulk | 191.135, 99.080 | 90 deg |
| C90 | 22 uF output bulk | 195.580, 87.015 | 0 deg |

The measured supply-and-ground pad path scores are 8.13 mm for C76, 10.12 mm
for C13, 12.77 mm for C10 and 12.17 mm for C90. These are aggregate
two-terminal distances to U2, not routed track lengths.

The remaining general +5 V decoupling was grouped at the U1 output:
C7, C8, C16, C17 and C77 occupy the free space immediately left of C6/C11.
FB1, C15 and C14 form the `+3V3_A` reference filter beside MOD1 pin 48. R73 is
the 100 k `PWR_GOOD_N` pull-up between U1 and GPIO43.

The 5 V and 3.3 V indicators are D4/R4 and D5/R5, respectively. Both indicator
pairs are on F.Cu in the open area between MOD1 and the two regulators.

The former U29 encoder buffer and its C58 bypass are no longer fitted. U28
handles the first eight encoder signals; the single remaining `ENC2_Z` channel
uses R110 (5.1 k series) and R111 (10 k to GND), both 0805.

The eight shift-register bypass capacitors are now local to their ICs:
C22-C25 sit beside the U6-U9 VCC pins and C26-C29 beside U10-U13. Each 0805
capacitor is to the right of its SOIC-16 body, with the +3V3 pad toward the IC
and the GND pad toward a bottom-plane via. The input-register pad loops measure
7.38 mm and the output-register loops 9.92 mm.

The board remains incomplete: optional or unplaced modules are parked outside
the outline and 499 connections remain intentionally unrouted. Local
capacitor-to-IC placement must still be reviewed whenever one of those modules
enters the board.
