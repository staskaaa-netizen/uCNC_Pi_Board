# Assembly and population options

## Fabrication

- `manufacturing/bom.csv` is grouped at part level by footprint, manufacturer,
  MPN and assembly status. The `Design Values` column records every schematic
  value represented by that physical part, and DNP alternates are included.
- Two-layer PCB, nominal 1.6 mm FR-4.
- The main assembly is front-side. J22, C57 and the JP2-JP4 field-mode
  selectors are on the back. The backlight-buck parts are user-placed on the
  board.
- External field wiring uses Phoenix `MCV 1,5` vertical 3.5 mm connectors.
- Two SS16 input diodes split the fused 24 V feed into separate logic and
  backlight branches. The first LMR36510 makes the 1 A +5 V rail; the second
  LMR36510 makes a separate 1 A +12 V backlight/CCFL rail.
- The 5 V rail feeds the WeAct module and two local 3.3 V LDOs: one for
  peripheral logic/SD/LCD and one dedicated to the ESP-01/ESP-01S.
- U37, an L78L12 SOT-89 regulator, creates a separate `+12V_AO` rail for the
  four-channel TLV2374 0-10 V output amplifier.
- General minimum track/clearance: 0.25/0.20 mm; 0.30 mm drill with 0.60 mm
  via pad. The eight LVDS connector signals use 0.12 mm tracks and 0.12 mm
  spacing to fan out between the 2.00 mm J22 pins.
- Low-voltage 100 nF decoupling and all 1 uF bypass/filter capacitors use
  0805. The 10 uF capacitors and 100 nF/100 V input ceramics use 1206.
- Regulator bulk capacitors are standardized to 22 uF/50 V in 1210 on both the
  regulated and 24 V-side rails. The 50 V rating retains margin above the
  SMBJ24CA input clamp; a 30 V part is not sufficient for a 24 V input.
  High-frequency bypasses are 100 nF in 0805, except 100 nF/100 V 1206 parts
  on 24 V-side nodes. C105 remains 10 uF/100 V for field-side backfeed
  exposure.
- `BL_PWM_MCU`, `BL_PWM`, and `BL_SW_GATE` use a dedicated 0.2 mm control
  netclass. The
  `+12V_BL` and switched `BL_LED_N` power path use the 0.8 mm Power class.
- Four M3 mounting positions.
- All logic is powered at 3.3 V except the two `SN74AHCT541DW` motion buffers
  and their 5 V rail. One encoder `SN74AHCT541DW` buffer runs at 3.3 V and
  translates the first eight encoder outputs; the remaining `ENC2_Z` input uses
  a 5.1 k / 10 k divider. The ULN and keyboard channels are driven directly by
  the 3.3 V 74HC595 outputs.

## Default build

The default build is the active LCD LVDS configuration and no Wi-Fi module:

- Fit the WeAct RP2350B socket, all input/output logic, power supply and standard
  decoupling.
- Fit U41 (DS90LV047A) and its C57 bypass. Leave the passive RN26/RN27 arrays unfitted.
- RN26 and RN27 are included in the BOM as optional DNP items.
- Do not insert the ESP-01/ESP-01S module unless Wi-Fi is required.
- The module and RP2350B board are supplied separately.

## Alternate populations

| Option | Fit | Do not fit |
|---|---|---|
| Active LCD LVDS | U41, C57, J22 | RN26/RN27 |
| Passive LCD LVDS | RN26/RN27, J22 | U41 |
| Wi-Fi | ESP-01 or ESP-01S in J20 | None |
| Backlight/CCFL | U3 and its buck passives, J2 | None |
| Storage | J19 full-size SD | J36 microSD |
| Storage alternative | J36 microSD | J19 full-size SD |


Fit only one LVDS driver path. No HDMI connector or HDMI signal path is fitted.
No solder jumper is required for backlight selection.
Fit exactly one storage socket: full-size J19 or alternate microSD J36.

The verified J22 pinout contains the LCD LVDS signals and logic supply only.
J2 is the separate backlight/CCFL connector: `+12V_BL`, GND, `BL_PWM`, and an
optional Q8-switched low-side return. GPIO35/MOD1 pin 25 drives both the direct
PWM pin and the Q8 gate path. Backlight current switching remains external.
LCD-panel logic is powered from J22.

JP5 is an open two-pad solder jumper in the SD-card-detect path. Bridge it to
enable card detection to GPIO2. With JP5 open, firmware should enable the
RP2350 internal pull-up or ignore the card-detect input.

The WeAct module's own reset button, power-on reset, brownout detector and
watchdog are used. The external reset branch and TPS3839 supervisor have been
removed from the design. The ESP programming button remains because it is not
provided by the WeAct board.

## Repeated resistor arrays

The repeated low-power and digital-output resistors use isolated four-element
arrays:

- RN6/RN7: 10 k expansion-input pull-downs.
- RN8-RN13 and RN30/RN31: 10 k pull-downs for output-register states.
- RN16-RN21: 100 ohm motion and keyboard output series resistors.
- R114-R117: 100 ohm gate resistors and 100 k pull-downs for the two extra
  low-side BSS138 outputs.
- RN22 and RN24: 1 k keyboard input series protection only.
- RN26/RN27: 4 x 330 ohm passive LVDS series resistors.
- R92-R99: individual 0805 10 k resistors for the two PWM filter stages.
- R100-R103: individual 0805 22 k feedback resistors.
- R104-R107: individual 0805 10 k gain-setting resistors to GND.

The 2.2 k 24 V input and output-LED resistors remain individual 1206 parts
because each can dissipate about 0.2 W. The three analog-input dividers remain
individual for tolerance. The 0-10 V signal resistors are individual 0805
parts, as requested, rather than resistor networks.

The 16 PLC inputs use four LTV-847S SOIC-16W quad optocouplers. The dedicated
E-stop, HOLD and START channels use individual EL3H7 DIP-4 optocouplers. The
PLC channels use four isolated 4x10 k pull-up networks, one per four-channel
group; the safety channels retain discrete 4.7 k pull-ups. Each input has one
2.2 k field resistor, indicator LED and reverse diode. The optocoupler
collectors drive the RP2350 directly; no receiver gates are fitted.

For dry contacts, U40 (Traco `TBA2-0512`) generates a protected isolated 12 V
field rail. One three-pad selector per bank chooses external 24 V or internal
12 V `CONTACT` mode. D56 blocks backfeed into the converter. See
`input-wetting.md`.

The four 0-10 V outputs share one TLV2374IDR rail-to-rail quad op-amp and the
U37 12 V regulator. They are ground-referenced, not isolated. J25 pin 1 is the
common return. The external status LED is omitted because GPIO46 now supplies
the fourth PWM channel; the WeAct board's onboard LED remains available.

The local output-enable safety gates, inverter and pull-up are removed. The
74HC595 `~OE` and AHCT541 output-enable pins are tied active, and all four
74HC595 `~SRCLR` pins are tied to `+3V3`. Output power isolation and hard
blocking must be provided by the external machine interface.

Both ULN2003A packages use all seven channels, providing DO0-DO13. DO14 and
DO15 use BSS138 MOSFETs with the same gate network as the auxiliary output.
J12 exposes DO0-DO7 with DO_COM and GND; the adjacent same-family 8-pin J32
exposes DO8-DO15 and shares `DO_COM`/`GND` through J12.

The first 595 output bit drives the AUX channel through Q5. The fifteen
motion channels therefore use shift bits 1-15 through the two
SN74AHCT541DW buffers. DO8-DO15 have the same resistor/LED indication chain
as DO0-DO7, fitted in a second row below J32.

RN12/RN13 define OUT16-OUT22 when the 595 chain is tri-stated. RN30 covers
OUT23-OUT26 and RN31 covers OUT27-OUT29; the remaining element in each array
is spare.

## ESD protection

The HDMI connector, HDMI-only ESD arrays and HDMI supply components are removed.
Encoder, keyboard and SD-card signals are internal or enclosed connections and
do not use TPD4E arrays. The encoder interface requires 5 V push-pull A/B/Z
outputs; open-collector encoders need pull-ups added externally.

## Hand assembly

Solder the fine-pitch SOIC and 1206 packages in that order of difficulty.
Display selection uses the active or passive LVDS population rather than solder
jumpers. JP2-JP4 use standard 2.54 mm headers and removable shunts; fit one
shunt per field bank in the required position. Fit the WeAct module last.
Before fitting it, remove **R16 (0R)** from the WeAct module to disconnect
GPIO23 from the onboard USER-key and WeAct C27 capacitor network used by the
74HC165 return. Motherboard C27 at U11 is unrelated and remains fitted.
Inspect the isolated input side before energising field wiring. The input
`FIELD_COMx` returns are
deliberately separate from logic ground.

No test points are fitted. Use the application connectors or probe accessible
component pads when debugging.

## Known release caveats

- The exact production LeanCam firmware and its original axis-bit names were not
  supplied. The generic AX0-AX4 mapping is documented and must be matched to the
  installed firmware before machine commissioning.
- The 3.5 mm connector land uses the verified Phoenix MC 1.5 footprint. KF2EDG
  clones differ in housing/keying; verify mechanical compatibility before ordering
  a KF2EDG-specific plug.
- The passive LVDS 330 ohm value follows this specification. The existing PicoLVDS
  prototype uses 270 ohm; validate the target LCD/cable before production.
- PLC input banks can use an external 24 V wetting source or the onboard
  isolated 12 V contact supply selected by JP2-JP4. Preserve the isolated
  `FIELD_COM` return and never connect it to logic GND.
- The board is not a safety-rated e-stop controller. Motor energy removal must
  remain an independent hard-wired safety function.
