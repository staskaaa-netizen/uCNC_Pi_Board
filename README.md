# uCNC RP2350B Motherboard - MANUFACTURING-READY PROTOTYPE

KiCad 10 carrier for a socketed WeAct Studio RP2350B Core Board. The board
provides isolated machine I/O, motion and encoder interfaces, LCD power,
storage, optional Wi-Fi and analog I/O on a 160 mm x 120 mm two-layer PCB.

**Status: MANUFACTURING PACKAGE GENERATED; FINAL DRC REVIEW REQUIRED.** The
circuit, pin mapping, PCB and manufacturing archives are complete. The PCB
fabrication and SMT assembly ZIPs are generated from the current board.

The current BOM has 263 physical parts in 44 purchasing groups. SMT assembly
contains 227 references in 33 groups; D53 is hand-fit and excluded from the
CPL. The combined JLC BOM contains 262 references in 43 groups.

## Board features

- 16 isolated 24 V PLC inputs, `I01-I16`, with TLP291-4 optocouplers.
- One dedicated isolated E-stop input on GPIO9, outside the shift-register
  chain.
- Four cascaded 74HC165 inputs and four cascaded SN74AHCT595 outputs.
- All 32 input-register channels have 10 k pull-ups, including the direct
  servo ZERO/ERROR inputs.
- Seven STEP/DIR axes, A0-A6, with labels `EN3 STPn DIRn`.
- Seven paired servo ZERO/ERROR inputs with individual 3-pin connectors.
- Two spare U7 register inputs exposed on J55 with 10 k pull-ups.
- All 35 indicator LEDs are green Hubei KENTO `KT-0805G` 0805 parts.
- Two onsemi MC74AC541DWR2G 5 V motion buffers.
- Sixteen optically isolated general outputs, `D01-D16`, driven by two
  TBD62083AFG(Z,EL) arrays.
- Three 5 V encoder interfaces with a 3.3 V logic-side buffer.
- Four 0-10 V analog inputs and four ground-referenced 0-10 V analog outputs.
- MicroSD through J36 or the on-board SOFNG TF-15x15 socket J54.
- Passive HSTX-to-LVDS interface on J22 using two 4 x 330 ohm, 4 x 0603 arrays.
- Optional ESP-01 with a dedicated 3.3 V regulator.
- Isolated 24 V to 12 V backlight supply.

## I/O map

| Function | Signal | Connector mapping |
|---|---|---|
| PLC inputs | `I01-I16` | J7: `I01-I08`; J8: `I09-I16` |
| General outputs | `D01-D16` | J12: `D01-D08`; J32: `D09-D16` |
| Motion A0 | `EN3`, `STP0`, `DIR0` | J10; status J40 |
| Motion A1 | `EN3`, `STP1`, `DIR1` | J11; status J41 |
| Motion A2 | `EN3`, `STP2`, `DIR2` | J28; status J42 |
| Motion A3 | `EN4`, `STP3`, `DIR3` | J29; status J43 |
| Motion A4 | `EN4`, `STP4`, `DIR4` | J47; status J50 |
| Motion A5 | `EN4`, `STP5`, `DIR5` | J46; status J49 |
| Motion A6 | `EN4`, `STP6`, `DIR6` | J30; status J48 |

The isolated logic-side input names are `I01_N-I16_N`. Every motion connector
uses pin 1 for enable, pin 2 for STEP and pin 3 for DIR. Every paired status
connector uses pin 1 for `GND`, pin 2 for ERROR and pin 3 for ZERO.
On the assembled board, motion labels are printed in the opposite physical
reading direction as `DIRn STPn ENx`; the pad-to-net mapping above remains
authoritative.

## Open the project

Open `hardware/motherboard.kicad_pro` in KiCad 10.0 or newer.

- Root schematic: `hardware/motherboard.kicad_sch`
- PCB: `hardware/motherboard.kicad_pcb`
- Local symbols, footprints and 3D models: `hardware/libraries/`
- Manufacturing data: `manufacturing/` (see `manufacturing/README.md`)
- Design notes: `documentation/`

The checked-in KiCad board is authoritative. It contains the approved manual
placement and routing. Do not run a full PCB regeneration over that file.

## Design documentation

- [Board specification](documentation/board-specification.md)
- [GPIO map](documentation/gpio-map.md)
- [WeAct RP2350B pin allocation](documentation/rp2350-pinout.md)
- [Input and output bit map](documentation/io-bit-map.md)
- [Signal naming](documentation/naming.md)
- [Connector pinouts](documentation/connectors.md)
- [Power budget](documentation/power-budget.md)
- [PLC inputs](documentation/plc-inputs.md)
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
- [Design-process retrospective and next-time playbook](documentation/design-process-retrospective.md)

## Manufacturing review files

- [Combined board review](manufacturing/board-review.pdf)
- [Ordered first-batch PCB review](manufacturing/board-ordered-first-batch.jpg)
- [Board specification PDF](manufacturing/board-specification.pdf)
- [Front artwork and assembly layer](manufacturing/board-front.pdf)
- [Mirrored rear artwork](manufacturing/board-back.pdf)
- [Current top 3D render](manufacturing/board-3d-top-da42d9de.png)
- [Current bottom 3D render](manufacturing/board-3d-bottom-da42d9de.png)
- [Connector label orientation check](manufacturing/connector-label-check.png)
- [Complete grouped BOM](manufacturing/bom.csv)
- [SMT-only grouped BOM](manufacturing/bom-smt.csv)
- [SMT-only reference BOM](manufacturing/bom-smt-refs.csv)
- [JLCPCB-format grouped BOM](manufacturing/bom-jlcpcb.csv)
- [JLCPCB stock and Basic/Extended audit](manufacturing/jlcpcb-stock-audit.csv)
- [Non-SMT grouped BOM](manufacturing/bom-non-smt.csv)
- [Combined SMT and non-SMT BOM](manufacturing/bom-all-jlcpcb.csv)
- [Pick-and-place CPL](manufacturing/cpl-jlcpcb.csv)
- [PCB fabrication ZIP](manufacturing/uCNC_Pi_Board_PCB_Fabrication.zip)
- [PCB fabrication + SMT assembly ZIP](manufacturing/uCNC_Pi_Board_SMT_Assembly.zip)

## Verification status

The current netlist contains 274 schematic components in 321 nets. The PCB has
268 footprints, 2,221 routed track segments and 232 vias. DRC reports zero
unconnected items, no copper-clearance errors and eight silkscreen warnings.
ERC has no electrical errors and 35 library-symbol cache warnings.

This is a routed prototype manufacturing package. It is not a safety-rated
controller. Hazardous energy removal must remain an independent hard-wired
safety function and must be validated in the complete machine.
