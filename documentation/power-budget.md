# Power budget and protective design

## Input

- PLC inputs support external 24 V wetting or an internal isolated 12 V
  short-pair mode.
- Main input protection: 2 A fuse, one 24 V bidirectional TVS and a
  reverse-polarity P-channel MOSFET.
- 5 V rail: TI LMR36510ADDAR, 1 A synchronous buck at 400 kHz. The reference
  network uses 22 uH, 2 x 22 uF output capacitance, 34 k + 46.4 k / 20 k
  feedback divider, 1 uF VCC bypass and a 100 nF bootstrap capacitor. No catch
  diode is fitted.
- The WeAct `5V` pin is supplied directly from the motherboard 5 V rail. Its
  onboard 3.3 V regulator powers only the module.
- A separate AMS1117-3.3 LDO supplies the motherboard peripheral `+3V3` rail,
  so the MCU's onboard regulator is not duplicated or externally loaded.
- The module's onboard reset button, POR/BOR and watchdog are used. There is no
  motherboard reset button or external MCU supervisor.
- The optional ESP-01S has a dedicated AMS1117-3.3 regulator from 5 V; its
  transmit peaks do not load the WeAct regulator.
- A local L78L12 SOT-89 regulator, U37, derives `+12V_AO` from `VIN_PROT` for
  the TLV2374 quad analog-output amplifier. It is not used by logic or field I/O.
- Logic, analog and switching returns share one continuous GND plane. The
  isolated PLC/field returns remain separate as `FIELD_COM0/1`.
- Every supply-bearing IC has a local 100 nF capacitor to GND. General logic
  decoupling uses 0805 packages so the capacitor can sit beside its IC pins;
  high-voltage input ceramics remain 1206.

## Estimated loads

| Load | Typical | Peak | Source |
|---|---:|---:|---|
| WeAct RP2350B module | 90 mA | 150 mA | +5V |
| 74HC logic and LEDs | 60 mA | 130 mA | +3V3 / +5V |
| Full-size SD card | 30 mA | 120 mA | +3V3_SD |
| ESP-01S | 80 mA | 500 mA | +3V3_WIFI, dedicated U34 |
| Encoders | 30 mA | 150 mA | +5V_ENC |
| HDMI +5 V | 20 mA | 100 mA | +5V_HDMI |
| Four 0-10 V outputs | 3 mA | 12 mA | +12V_AO, U37 from VIN_PROT |
| Isolated field wetting | 110 mA | 167 mA | +5V_ISO_IN via U40 |

The LMR36510 is rated to 1 A and is sized for the expected 100-200 mA
motherboard load. The two 3.3 V LDOs are powered from its 5 V output:

- U2 AMS1117-3.3 feeds logic, SD and the unswitched LCD panel logic rail. Keep continuous
  current below 500 mA and use copper area for thermal margin.
- U34 AMS1117-3.3 feeds only the optional ESP-01S. Its 500 mA transmit peak is
  locally reservoir-supported by 10 uF plus 100 nF.

The 1 A buck limit must include both LDO input currents plus the direct 5 V
encoder and HDMI loads. Do not operate the ESP at peak transmit and all other
loads simultaneously. The 2 A input fuse remains the hard assembly limit.
Backlight power is not supplied by this board; J22 pin 6 carries only the
3.3 V logic-level `BL_PWM` signal to an external backlight driver.

A linear 5 V regulator is not acceptable from the specified 12-24 V input. At
24 V and only 200 mA it would dissipate approximately 3.8 W.

The separate 12 V analog rail is deliberately linear because its expected load
is only a few milliamps. U37's 100 mA rating includes margin for the op-amp
quiescent current, feedback dividers and high-impedance analog loads. At 24 V
input and 12 mA, its dissipation is approximately 0.14 W. Do not use this rail
to power solenoids, lamps or other high-current loads.

The LMR36510 loop uses a continuous ground plane. Input capacitors sit at the
VIN/GND pins, the 22 uH inductor is next to SW, the bootstrap capacitor bridges
BOOT/SW, and the feedback divider sits at FB. The SOIC PowerPAD uses a stitched
ground pad.

PLC output load current is supplied from the external `DO_COM` field supply, not
from the motherboard 5 V or 3.3 V rails. ULN2003A channels are limited in
firmware/application to 150 mA per channel and 500 mA per package for thermal
margin. Motion outputs are 5 V CMOS logic, not motor power.

Each PLC channel has a 2.2 k series resistor, indicator LED,
reverse-protection diode and optocoupler channel. The board can either use an
external 24 V wetting source or generate its own isolated 12 V wetting source
with U40, a Traco `TBA2-0512`, rated at 2 W and approximately 167 mA. F4 limits
the converter input to 750 mA, and D56 prevents field-side backfeed into U40.
One bottom-side selector per input bank chooses 24 V or `CONTACT`; see
`documentation/input-wetting.md`.

## Safe state

The local output-enable safety chain is removed, and the 595/541 output-enable
pins are tied active. Motor power and other hazardous output supplies must be
removed by an independent external hard-wired safety circuit. The U24/U25
outputs are not safety-rated.
