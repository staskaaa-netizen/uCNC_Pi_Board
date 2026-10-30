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
| U28 | SN74AHCT541DW encoder buffer | +3V3 | C106, 100 nF |
| U41 | DS90LV047A LVDS driver | +3V3 | C57, 100 nF |
| MOD1 | WeAct RP2350B module | +5V input | On-module decoupling; no separate motherboard bypass assigned |

U26 and U27 are ULN2003A open-collector arrays and have no logic supply pin.
C55 and C56 (100 nF) are fitted between their `DO_COM` clamp rail and GND.
They are field-output rail clamps, not IC VCC bypass capacitors.

U18-U21 are LTV-847S four-channel PLC optocouplers; U35/U36/U39 are individual
EL3H7 DIP-4 safety optocouplers. They have no VCC pin. RN32-RN35 provide one
4x4.7 k isolated pull-up network per PLC bank; the E-stop, HOLD and START
collectors retain discrete 4.7 k pull-ups to `+3V3`. No input-node capacitors
are fitted; firmware provides debounce timing.

## Voltage regulators

| Regulator | Rail and role | Input capacitors | Output/VCC capacitors | Other |
|---|---|---|---|---|
| U1 LMR36510ADDAR | VIN_PROT to +5V, 1 A buck | C3 22 uF/50 V 1210, C4 100 nF/100 V 1206, C5 22 uF/50 V 1210 | C6 22 uF/25 V 1210, C7 100 nF 0805, C11 22 uF/25 V 1210 | C86 100 nF BOOT-to-SW; C91 1 uF VCC-to-GND |
| U3 LMR36510ADDAR | VIN_BL_PROT to +12V_BL, 1 A backlight buck | C107 22 uF/50 V 1210, C108 100 nF/100 V 1206 | C109-C111 3 x 22 uF/25 V 1210, C112 100 nF 0805 | C113 100 nF BOOT-to-SW; C114 1 uF VCC-to-GND |
| U2 AMS1117-3.3 | +5V to peripheral +3V3 | C10 22 uF/25 V 1210, C76 100 nF 0805 | C13 100 nF 0805, C90 22 uF/25 V 1210 | Supplies logic, SD, J22 LCD logic and analog prefilter |
| U34 AMS1117-3.3 | +5V to ESP +3V3_WIFI | C88 22 uF/25 V 1210, C89 100 nF 0805 | C69 22 uF/25 V 1210, C70 100 nF 0805 | Dedicated ESP-01/ESP-01S rail |
| U40 TBA2-0512 | +5V to isolated +12V_FIELD | C103 22 uF/25 V 1210 | C105 10 uF/100 V 1206, after D56 | Dry-contact wetting supply |
| U37 L78L12 | VIN_PROT to +12V_AO | C100 22 uF/50 V 1210 | C101 22 uF/25 V 1210 | Supplies U38 only |

RN36 provides the four 10 k pull-ups for `EN`, `RST`, `GPIO0` and `GPIO2` at
the ESP socket. Its supply side is referenced to `+3V3_WIFI`, not the
motherboard `+3V3` rail. This keeps those pins in the ESP supply domain and
avoids backfeeding an unpowered ESP rail.

U38 TLV2374 uses C102 (100 nF) from `+12V_AO` to GND directly at the package.
C92/C94/C96/C98 are the 1 uF first-stage PWM filter capacitors, while
C93/C95/C97/C99 are the 100 nF second-stage filter capacitors. They are signal
filter parts, not power-rail decoupling.

The latest placement audit confirms that every powered logic or analog IC has
at least one capacitor between its supply and ground. After the recent moves,
C106 is the local 100 nF bypass at U28 and C57 is the local 100 nF bypass at
U41.

One placement item remains worth reviewing:

- U34's `+3V3_WIFI` output capacitors C69/C70 are approximately 13.0 mm and
  17.6 mm from its supply pin. Move the 100 nF bypass closer to U34 or place an
  additional 100 nF beside the regulator.

The TBA2-0512 datasheet does not require an external output capacitor. During
normal `CONTACT` operation D56 is forward-biased, so C105 on `+12V_FIELD`
serves as the converter's bulk output reservoir. The manufacturer's optional
22 uF input-capacitor recommendation applies to long input lines or hot-plug
events; C103 provides the local input bypass on this fused board supply.

For U1, C3-C5 form the input loop, C6/C7/C11 form the output filter, C86 is
the bootstrap capacitor and C91 is the internal VCC bypass. The 0.3 mm thermal
vias under the PowerPAD tie the exposed pad to the B.Cu GND plane. U3 uses the
TI 12 V reference capacitor set and is user-placed on the board with its
passives.

## Module and connector-local rail capacitors

| Load | Rail | Capacitors |
|---|---|---|
| ESP-01/ESP-01S at J20 | +3V3_WIFI | C69 10 uF, C70 100 nF |
| SD card at J19 | +3V3_SD | C67 10 uF at `(166.80, 75.70)`, C68 100 nF at `(166.80, 70.80)`; FB2 at `(166.80, 67.62)` |
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

The 5 V output rail uses C6/C11 as the two 22 uF bulk capacitors and C7 as
the local high-frequency bypass. Redundant C8, C16, C17 and C77 are removed.
FB1 and C15 form the `+3V3_A` reference filter beside MOD1 pin 48. The 10 uF
C14 bulk capacitor is removed because C15 provides the required local bypass. R73
is the 100 k `PWR_GOOD_N` pull-up between U1 and GPIO43.

The 5 V and 3.3 V indicators are D4/R4 and D5/R5, respectively. Both indicator
pairs are on F.Cu in the open area between MOD1 and the two regulators.

The former U29 encoder buffer and its C58 bypass are no longer fitted. U28
handles the first eight encoder signals with the nearby C106 bypass; the single
remaining `ENC2_Z` channel uses R110 (5.1 k series) and R111 (10 k to GND),
both 0805.

The eight shift-register bypass capacitors are now local to their ICs:
C22-C25 sit beside the U6-U9 VCC pins and C26-C29 beside U10-U13. Each 0805
capacitor is to the right of its SOIC-16 body, with the +3V3 pad toward the IC
and the GND pad toward a bottom-plane via. The input-register pad loops measure
7.38 mm and the output-register loops 9.92 mm.

Every fitted 100 nF capacitor with a GND terminal now has its own 0.6 mm /
0.3 mm through-via placed beyond the GND pad, away from the supply pad. A
0.5 mm F.Cu stub joins the capacitor pad to that via. Thirty decoupling
capacitors are covered after removing C17/C77 and adding C106; C86 is excluded
because it is the buck bootstrap capacitor connected between BOOT and SW rather
than GND.

The PCB uses these project netclasses:

| Class | Track | Clearance | Via diameter/drill | Assignment |
|---|---:|---:|---:|---|
| Default | 0.20 mm | 0.20 mm | 0.60/0.30 mm | Logic and general signals |
| Power | 0.80 mm | 0.30 mm | 0.80/0.40 mm | VIN, +5 V, +3.3 V and +12 V rails |
| FieldPower | 0.50 mm | 0.50 mm | 0.60/0.30 mm | Isolated commons, field commons and DO_COM |
| AnalogPower | 0.30 mm | 0.20 mm | 0.60/0.30 mm | Low-current +12 V analog rails |
| EncoderPower | 0.30 mm | 0.20 mm | 0.60/0.30 mm | Shared encoder +5 V feeder |
| Ground | 0.50 mm | 0.30 mm | 0.60/0.30 mm | GND and decoupling-via stubs |
| DigitalDiffPair | 0.20 mm | 0.20 mm | 0.60/0.30 mm | HSTX source pairs |
| LVDSConnector | 0.12 mm | 0.12 mm | 0.60/0.30 mm | J22 LVDS pair fanout |
| Analog | 0.25 mm | 0.25 mm | 0.60/0.30 mm | AI and AOUT nets |

The board remains incomplete: all footprints are inside the outline and two
connections remain intentionally unrouted. Local capacitor-to-IC placement must
still be reviewed whenever the footprint placement changes.
