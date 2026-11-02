# Assembly and population options

## Fabrication

- `manufacturing/bom.csv` is grouped at part level by footprint, manufacturer,
  MPN and assembly status. The `Design Values` column records every schematic
  value represented by that physical part, and DNP alternates are included.
- Two-layer PCB, nominal 1.6 mm FR-4.
- The main assembly is front-side. J22 is on the back.
- External field wiring uses Phoenix `MCV 1,5` vertical 3.5 mm connectors.
- One SS16 input diode feeds the logic-side LMR36510 and one protects the
  isolated backlight-converter feed. U3 converts the PLC 24 V field rail to
  isolated +12 V.
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
  on 24 V-side nodes. Both 10 uF capacitors use the same 25 V X7R part.
- `BL_PWM_MCU` and `BL_PWM` use a dedicated 0.2 mm control netclass.
  `+24V_FIELD` and `ISO_GND` use the field-power class.
- Four M3 mounting positions.
- The seven 3-pin axis outputs, seven paired 3-pin ZERO/ERROR inputs, J18,
  and the U3 backlight-converter group are currently parked outside the
  board outline for manual placement.
- All logic is powered at 3.3 V except the two `TC74AC541F` motion buffers
  and their 5 V rail. One encoder `SN74AHCT541DW` buffer runs at 3.3 V and
  translates the first eight encoder outputs; the remaining `ENC2_Z` input uses
  a 5.1 k / 10 k divider. The TBD62083 output channels are driven directly by
  the 3.3 V 74HC595 outputs.

## Default build

The default build uses passive LCD LVDS and no Wi-Fi module:

- Fit the WeAct RP2350B socket, all input/output logic, power supply and standard
  decoupling.
- Fit RN26 and RN27 for the passive LVDS series path. U41 and C106 are removed.
- Do not insert the ESP-01/ESP-01S module unless Wi-Fi is required.
- The module and RP2350B board are supplied separately.

## Alternate populations

| Option | Fit | Do not fit |
|---|---|---|
| LCD LVDS | RN26/RN27, J22 | U41 |
| Wi-Fi | ESP-01 or ESP-01S in J20 | None |
| Backlight/CCFL | U3, its isolated buck passives, and J2 | None |
| Storage | J36 Open-Smart 3.3 V TF breakout | J19 |


The passive LVDS path is the only fitted path. No HDMI connector or HDMI signal path is fitted.
No solder jumper is required for backlight selection.
Fit the Open-Smart 3.3 V TF Card Breakout to J36; the full-size SD socket is
removed. The breakout is passive and must not contain a 5 V regulator or level
shifter.

The verified J22 pinout contains the LCD LVDS signals and logic supply only.
J2 is the separate backlight/CCFL connector: isolated `+12V_BL`, `ISO_GND`,
and 3.3 V `BL_PWM`. U3 derives 12 V from the PLC 24 V field rail. GPIO35/MOD1
pin 25 drives PWM through R131. The external driver must provide current
switching and PWM isolation. LCD-panel logic is powered from J22.

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

- RN41: 10 k state definitions for the shared shift-register controls.
- RN42/RN43: 10 k microSD pull-ups; RN43 has two spare elements.
- RN44: four isolated 22 ohm microSD series resistors for CS, MOSI, SCK and
  MISO.
- RN8-RN13 and RN30/RN31: 10 k pull-downs for output-register states.
- R114-R117: 100 ohm gate resistors and 100 k pull-downs for the two extra
  low-side BSS138 outputs.
- RN26/RN27: 4 x 330 ohm passive LVDS series resistors.
- R92-R99: individual 0805 10 k resistors for the two PWM filter stages.
- R100-R103: individual 0805 22 k feedback resistors.
- R104-R107: individual 0805 10 k gain-setting resistors to GND.

The 2.2 k 24 V input and output-LED resistors remain individual 1206 parts
because each can dissipate about 0.2 W. The three analog-input dividers remain
individual for tolerance. The 0-10 V signal resistors are individual 0805
parts, as requested, rather than resistor networks.

The 16 PLC inputs use four TLP291-4 SOIC-16 quad optocouplers. U36/U39 and the
isolated servo diagnostics are removed. The dedicated E-stop uses one TLP291
SOP-4 optocoupler. The
PLC channels use four isolated 4x10 k pull-up networks, one per four-channel
group; the E-stop retains one discrete 4.7 k pull-up. Each input has a
connector-side indicator LED, 2.2 k field resistor and reverse diode. The optocoupler
collectors drive the RP2350 directly; no receiver gates are fitted.

J33 and J45 are parallel two-pin connections for the external isolated 24 V
field rail and its single `ISO_GND` return. They supply both dry-contact
wetting and the output side. No separate return blocks or mode selectors are
fitted. See `input-wetting.md`.

The four 0-10 V outputs share one TLV2374IDR rail-to-rail quad op-amp and the
U37 12 V regulator. They are ground-referenced, not isolated. J25 pin 1 is the
common return. The external status LED is omitted because GPIO46 now supplies
the fourth PWM channel; the WeAct board's onboard LED remains available.

The local output-enable safety gates, inverter and pull-up are removed. The
74HC595 `~OE` and AHCT541 output-enable pins are tied active, and all four
74HC595 `~SRCLR` pins are tied to `+3V3`. Output power isolation and hard
blocking must be provided by the external machine interface.

Two TBD62083AFG packages provide all sixteen general outputs. J12 exposes
DO0-DO7 and J32 exposes DO8-DO15. Field power and return are connected through
the parallel J33/J45 pair.

Output bits 0-13 drive seven STEP/DIR axes through the two TC74AC541F buffers.
Bit 14 is the shared `EN_3AX` output and bit 15 is the shared `EN_4AX` output.
There is no AUX output. DO8-DO15 have the same resistor/LED indication chain as
DO0-DO7, fitted in a second row below J32.

RN12/RN13 define OUT16-OUT22 when the 595 chain is tri-stated. RN30 covers
OUT23-OUT26 and RN31 covers OUT27-OUT29; the remaining element in each array
is spare.

## ESD protection

The HDMI connector, HDMI-only ESD arrays and HDMI supply components are removed.
Encoder and SD-card signals are internal or enclosed connections and
do not use TPD4E arrays. The encoder interface requires 5 V push-pull A/B/Z
outputs; open-collector encoders need pull-ups added externally.

## Hand assembly

Solder the fine-pitch SOIC and 1206 packages in that order of difficulty.
The passive LVDS resistor path is fitted rather than using solder jumpers.
Fit the WeAct module last.
Before fitting it, remove **R16 (0R)** from the WeAct module to disconnect
GPIO23 from the onboard USER-key and WeAct C27 capacitor network used by the
74HC165 return. Motherboard C27 at U11 is unrelated and remains fitted.
Inspect the isolated input side before energising field wiring. The input
return is the single `ISO_GND` pin on J33 or J45 and is deliberately separate
from logic ground.

No test points are fitted. Use the application connectors or probe accessible
component pads when debugging.

## Known release caveats

- The exact production LeanCam firmware and its original axis-bit names were not
  supplied. The AX0-AX6 mapping is documented and must be matched to the
  installed firmware before machine commissioning.
- The 3.5 mm connector land uses the verified Phoenix MC 1.5 footprint. KF2EDG
  clones differ in housing/keying; verify mechanical compatibility before ordering
  a KF2EDG-specific plug.
- The passive LVDS 330 ohm value follows this specification. The existing PicoLVDS
  prototype uses 270 ohm; validate the target LCD/cable before production.
- PLC input banks use the external isolated 24 V wetting source connected
  through J33 or J45. Preserve the single isolated `ISO_GND` return and never
  connect it to logic GND.
- The board is not a safety-rated e-stop controller. Motor energy removal must
  remain an independent hard-wired safety function.
