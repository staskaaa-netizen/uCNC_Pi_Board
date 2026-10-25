# Assembly and population options

## Fabrication

- Two-layer PCB, nominal 1.6 mm FR-4.
- Components are fitted on both sides. Field connectors and the module socket
  are front-side; J9/J16/J17 and most input/output conditioning are back-side.
- External field wiring uses Phoenix `MCV 1,5` vertical 3.5 mm connectors.
- One LMR36510 24 V-to-5 V buck feeds the WeAct module and two local 3.3 V
  LDOs: one for peripheral logic/SD/LCD and one dedicated to the ESP-01S.
- U37, an L78L12 SOT-89 regulator, creates a separate `+12V_AO` rail for the
  four-channel TLV2374 0-10 V output amplifier.
- Minimum track/clearance: 0.25/0.20 mm; 0.30 mm drill with 0.60 mm via pad.
- General 100 nF IC decoupling uses 0805 to keep loop area small. High-voltage
  input ceramics, bulk components and most other passives remain 1206.
- Four M3 mounting positions.
- All logic is powered at 3.3 V except the two `SN74AHCT541DW` motion buffers
  and their 5 V rail. One encoder `SN74AHCT541DW` buffer runs at 3.3 V and
  translates the first eight encoder outputs; the remaining `ENC2_Z` input uses
  a 5.1 k / 10 k divider. The ULN and keyboard channels are driven directly by
  the 3.3 V 74HC595 outputs.

## Default build

The default build is the passive LCD LVDS configuration and no Wi-Fi module:

- Fit the WeAct RP2350B socket, all input/output logic, power supply and standard
  decoupling.
- Fit RN26/RN27 (two four-element 330 ohm LVDS arrays).
- Leave RN28/RN29 (HDMI selector arrays) unfitted.
- Do not insert ESP-01S unless Wi-Fi is required.
- The module and ESP-01S are supplied separately.

## Alternate populations

| Option | Fit | Do not fit |
|---|---|---|
| Passive LCD LVDS | RN26/RN27, J22 | RN28/RN29 |
| HDMI | RN28/RN29, J23 | RN26/RN27 |
| Wi-Fi | ESP-01S in J18 | None |
| External LCD/backlight driver | J22 pin 6 PWM to external driver | None |


Fit only one display path. The active-LVDS driver is not fitted. No solder
jumper is required for backlight selection.

J22 pin 6 carries `BL_PWM` directly. The local J2 backlight connector, JP1
supply selector and Q2/Q3 high-current switch are not fitted. Backlight power
switching and current limiting are the external display driver's responsibility.
LCD panel logic is powered directly from `+3V3`.

The WeAct module's own reset button, power-on reset, brownout detector and
watchdog are used. The external reset branch and TPS3839 supervisor have been
removed from the design. The ESP programming button remains because it is not
provided by the WeAct board.

## Repeated resistor arrays

The repeated low-power and digital-output resistors use isolated four-element
arrays:

- RN6/RN7: 10 k expansion-input pull-downs.
- RN8-RN13: 10 k pull-downs for motion and ULN output-register states.
- RN16-RN21: 100 ohm motion and keyboard output series resistors.
- RN22 and RN24: 1 k keyboard input series protection only.
- RN26/RN27: 4 x 330 ohm passive LVDS series resistors.
- RN28/RN29: 4 x 0 ohm HDMI selector links, DNP by default.
- R92-R99: individual 0805 10 k resistors for the two PWM filter stages.
- R100-R103: individual 0805 22 k feedback resistors.
- R104-R107: individual 0805 10 k gain-setting resistors to GND.

The 2.2 k 24 V input and output-LED resistors remain individual 1206 parts
because each can dissipate about 0.2 W. The three analog-input dividers remain
individual for tolerance. The 0-10 V signal resistors are individual 0805
parts, as requested, rather than resistor networks.

The 16 PLC inputs use four LTV-847S SOIC-16W quad optocouplers. The dedicated
E-stop, HOLD and START channels use individual EL3H7 DIP-4 optocouplers. Each
used channel has one 2.2 k field resistor, indicator LED, reverse diode and one
individual 4.7 k pull-up. The optocoupler collectors drive the RP2350 directly;
no receiver gates are fitted.

For dry contacts, U40 (Traco `TBA2-0512`) generates a protected isolated 12 V
field rail. One three-pad selector per bank chooses external 24 V or internal
12 V `CONTACT` mode. D56 blocks backfeed into the converter. See
`input-wetting.md`.

The four 0-10 V outputs share one TLV2374IDR rail-to-rail quad op-amp and the
U37 12 V regulator. They are ground-referenced, not isolated. J25 pin 1 is the
common return. The external status LED is omitted because GPIO46 now supplies
the fourth PWM channel; the WeAct board's onboard LED remains available.

The local output-enable safety gates, inverter and pull-up are removed. The
74HC595 and AHCT541 output-enable pins are tied active. Output power isolation
and hard blocking must be provided by the external machine interface.

## ESD protection

`TPD4E05U06DQA` is fitted only where its sub-picofarad capacitance and exposed
connector justify the fine-pitch USON-10 package. Three arrays remain:

- U30/U31 protect the four HDMI TMDS pairs.
- U32 protects HDMI DDC, HPD and CEC.

Encoder, keyboard and SD-card signals are internal or enclosed connections and
do not fit these arrays. The encoder interface requires 5 V push-pull A/B/Z
outputs; open-collector encoders need pull-ups added externally.

## Hand assembly

Solder the fine-pitch HDMI, USON-10 ESD, SOIC and 1206 packages in that order of
difficulty. Display selection uses populated resistor arrays rather than solder
jumpers. JP2-JP4 use standard 2.54 mm headers and removable shunts; fit one
shunt per field bank in the required position. Fit the WeAct module last.
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
- The PLC input loops do not include an onboard isolated wetting supply. Provide
  an external isolated 12-24 V field supply connected through the switched
  inputs and their corresponding `FIELD_COM` return.
- The board is not a safety-rated e-stop controller. Motor energy removal must
  remain an independent hard-wired safety function.
