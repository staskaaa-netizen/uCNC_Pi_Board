# uCNC RP2350B Motherboard

KiCad 10 carrier for a socketed WeAct Studio RP2350B Core Board. The board
provides isolated machine I/O, motion and encoder interfaces, LCD power,
storage, optional Wi-Fi and analog I/O on a 200 mm x 150 mm two-layer PCB.

## Board features

- 16 isolated 24 V PLC inputs with TLP291-4 optocouplers.
- One dedicated isolated E-stop input on GPIO9, outside the shift-register
  chain.
- Four cascaded 74HC165 inputs and four cascaded SN74AHCT595 outputs.
- Seven STEP/DIR axes with grouped 3-axis and 4-axis enables.
- Seven paired servo ZERO/ERROR inputs with individual 3-pin connectors.
- Two TC74AC541F 5 V motion buffers.
- Sixteen general low-side outputs driven by two TBD62083AFG arrays.
- Sixteen optically isolated general-output channels.
- Three 5 V encoder interfaces with a 3.3 V logic-side buffer.
- Four 0-10 V analog inputs and four ground-referenced 0-10 V analog outputs.
- MicroSD through J36 or the on-board SOFNG TF-15x15 socket J54.
- Passive HSTX-to-LVDS interface on J22 using 4 x 330 ohm arrays.
- Optional ESP-01/ESP-01S socket with a dedicated 3.3 V regulator.
- Isolated 24 V to 12 V backlight supply.

## Open the project

Open `hardware/motherboard.kicad_pro` in KiCad 10.0 or newer.

- Root schematic: `hardware/motherboard.kicad_sch`
- PCB: `hardware/motherboard.kicad_pcb`
- Local symbols, footprints and 3D models: `hardware/libraries/`
- Manufacturing data: `manufacturing/`
- Design notes: `documentation/`

The checked-in KiCad board is authoritative. It contains the approved manual
placement and routing. Do not run a full PCB regeneration over that file.

## Design documentation

- [Board specification](documentation/board-specification.md)
- [GPIO map](documentation/gpio-map.md)
- [WeAct RP2350B pin allocation](documentation/rp2350-pinout.md)
- [Input and output bit map](documentation/io-bit-map.md)
- [Connector pinouts](documentation/connectors.md)
- [Power budget](documentation/power-budget.md)
- [Isolated PLC inputs](documentation/input-wetting.md)
- [Decoupling map](documentation/decoupling-map.md)
- [Component placement classes](documentation/component-placement-classes.md)
- [LCD LVDS interface](documentation/display-population.md)
- [Wi-Fi module](documentation/wifi-module.md)
- [Analog calibration](documentation/analog-calibration.md)
- [Four-channel 0-10 V outputs](documentation/analog-outputs.md)
- [uCNC RP2350 compatibility](documentation/ucnc-rp2350.md)
- [Mechanical notes](documentation/mechanical.md)
- [Assembly notes](documentation/assembly-options.md)
- [Release checklist](TODO.md)

## Manufacturing review files

- [Combined board review](manufacturing/board-review.pdf)
- [Board specification PDF](manufacturing/board-specification.pdf)
- [Front artwork and assembly layer](manufacturing/board-front.pdf)
- [Mirrored rear artwork](manufacturing/board-back.pdf)
- [Current top 3D render](manufacturing/board-3d-top-current.png)
- [Current bottom 3D render](manufacturing/board-3d-bottom-current.png)
- [Grouped BOM](manufacturing/bom.csv)

## Verification status

The current netlist contains 281 schematic components in 320 nets. The PCB has
275 footprints, 2,262 routed track segments and 189 vias. DRC reports zero
unconnected items. It still reports 55 error-severity and 183
warning-severity geometry or documentation findings, primarily clearance,
starved thermals and silkscreen checks. ERC has no electrical errors and 35
library-symbol cache warnings.

This is a routed prototype. It is not a fabrication release and is not a
safety-rated controller. Hazardous energy removal must remain an independent
hard-wired safety function.
