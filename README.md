# uCNC RP2350B Motherboard

Native KiCad 10 design for a socketed WeAct Studio RP2350B Core Board. The
architecture preserves LeanCam's 32-bit input and output shift-register chains,
with 16 isolated PLC inputs, dedicated direct E-stop, HOLD and START inputs, an
eight-input expansion header, 16 motion outputs, eight open-collector field
outputs, eight keyboard outputs, three encoders, full-size SD, optional ESP-01/ESP-01S,
LCD LVDS output, three 0-10 V analog inputs and four 0-10 V analog outputs.

## Open the project

Open `hardware/motherboard.kicad_pro` in KiCad 10.0 or newer.

- Root schematic: `hardware/motherboard.kicad_sch`
- PCB: `hardware/motherboard.kicad_pcb`
- Custom symbols/footprints: `hardware/libraries/`
- Manufacturing data: `manufacturing/`
- Design documentation: `documentation/`

## Key documents

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

The current board is a partially routed 200 x 150 mm, two-layer prototype. PCB
DRC currently reports 209 items: 171 errors from routing/netclass cleanup and
38 warnings, with no shorts. There are 410 unconnected items remaining. ERC has
no errors and retains the existing library-symbol mismatch warnings.
Freerouting has not been started. The design contains documented prototype
assumptions; it is not a safety-certified controller.
