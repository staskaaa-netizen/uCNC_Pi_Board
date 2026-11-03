# Vendor sources

- WeAct Studio RP2350B Core Board official hardware repository: https://github.com/WeActStudio/WeActStudio.RP2350BCoreBoard
- Official body drawing: `WeAct_RP2350B_dimensions.pdf` (41.402 mm x 41.148 mm).
- Official pinout image: `WeAct_RP2350B_PINOUT.png`.
- Official 3D STEP: `3d/WeAct_RP2350B.step`.
- Socket land pattern: generated from the published `WeActStudio.RP2350B.footprint` coordinate data, with the manufacturer pad labels mapped deterministically to module pins 1-64 so the schematic and PCB agree.
- Mechanical stack: the WeAct model is raised 8.5 mm to represent a 2.54 mm socket-and-pin assembly.
- Local footprint generation identifier: `cc58b075-f7d4-4117-8e41-c9e876fbf647`.
- SOFNG TF-15x15 socket: footprint converted from the JLCEDA/EasyEDA Official Library for LCSC `C111196`; local footprint and STEP/WRL files are under `LeanCam.pretty/` and `3d/`.
