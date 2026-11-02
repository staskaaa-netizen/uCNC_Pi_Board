# uCNC RP2350B Motherboard

Native KiCad 10 design for a socketed WeAct Studio RP2350B Core Board. The
architecture uses a 32-bit input shift-register chain and a 32-bit output chain,
with 16 isolated PLC inputs, seven paired servo ZERO/ERROR inputs, a dedicated
direct E-stop input, seven STEP/DIR motion axes with grouped 3-axis/4-axis
enables, 16 general low-side field outputs, three encoders,
microSD, optional ESP-01/ESP-01S, LCD LVDS output, four 0-10 V analog inputs
and four 0-10 V analog outputs. The backlight has an isolated 24 V to 12 V
buck converter sourced from the J33/J45 PLC field rail.

## Open the project

Open `hardware/motherboard.kicad_pro` in KiCad 10.0 or newer.

- Root schematic: `hardware/motherboard.kicad_sch`
- PCB: `hardware/motherboard.kicad_pcb`
- Custom symbols/footprints: `hardware/libraries/`
- Manufacturing data: `manufacturing/`
- Design documentation: `documentation/`

## Key documents

- [Board specification](documentation/board-specification.md)
- [GPIO map](documentation/gpio-map.md)
- [RP2350 pin allocation](documentation/rp2350-pinout.md)
- [32-bit chain map](documentation/io-bit-map.md)
- [Connector pinouts](documentation/connectors.md)
- [Power budget](documentation/power-budget.md)
- [Isolated PLC input configuration](documentation/input-wetting.md)
- [Decoupling map](documentation/decoupling-map.md)
- [Component placement classes](documentation/component-placement-classes.md)
- [Display population options](documentation/display-population.md)
- [Wi-Fi module](documentation/wifi-module.md)
- [Analog calibration](documentation/analog-calibration.md)
- [Four-channel 0-10 V outputs](documentation/analog-outputs.md)
- [uCNC RP2350 pin compatibility](documentation/ucnc-rp2350.md)
- [Mechanical notes](documentation/mechanical.md)
- [Assembly options and caveats](documentation/assembly-options.md)
- [Placement optimization](documentation/placement-optimization.md)
- [Interactive placement workflow](documentation/interactive-workflow.md)
- [DTU autoplacer evaluation](documentation/autoplacer-evaluation.md)

## PCB PDFs

- [Combined board review](manufacturing/board-review.pdf)
- [Board specification PDF](manufacturing/board-specification.pdf)
- [Front artwork and assembly layer](manufacturing/board-front.pdf)
- [Mirrored rear artwork](manufacturing/board-back.pdf)
- [Top 3D render](manufacturing/board-3d-top.png)
- [Bottom 3D render](manufacturing/board-3d-bottom.png)

## Reproducible generation

The checked-in KiCad files are authoritative. The `tools/` scripts regenerate
them using KiCad 10 and the project-local vendor footprint:

```powershell
& C:\acc\rp2350\.kicad-mcp\venv\Scripts\python.exe .\tools\prepare_library.py
& C:\acc\rp2350\.kicad-mcp\venv\Scripts\python.exe .\tools\generate_schematic.py
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe' `
  sch export netlist --format kicadxml `
  --output hardware\motherboard.net.xml hardware\motherboard.kicad_sch
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  .\tools\generate_pcb.py
```

## Release status

The current board is a 200 x 150 mm, two-layer routed prototype variant.
The schematic netlist verifies with zero connectivity failures; manual PCB
routing and final DRC cleanup are still in progress. The design contains
documented prototype assumptions and is not a safety-certified controller.

## PLC I/O variant summary

- U8/U9 carry PLC inputs 1-16; U6/U7 carry paired servo ZERO/ERROR inputs.
- Servo axes use separate 3-pin output and input connectors; no shared alarm
  connector is fitted.
- Seven STEP/DIR axes use grouped `EN_3AX` and `EN_4AX` enables.
- Hardware I2C1 uses MOD1 pins 9/23; E-stop uses MOD1 pin 53.
- The backlight converter is isolated and is powered from the PLC 24 V field
  rail.
- U42/U43 retain local 100 nF bypass capacitors C115/C116.
