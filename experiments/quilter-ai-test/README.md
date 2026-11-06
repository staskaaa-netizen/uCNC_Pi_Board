# Quilter AI Test Project

This is a separate copy of the uCNC RP2350B board for Quilter experiments.
The released manufacturing PCB is untouched.

## Upload for routing

Use:

`hardware/motherboard.kicad_pcb`

It preserves:

- the exact board outline: 160.043 x 120.038 mm
- 275 placed footprints
- component references, values and net names
- pad net assignments, net classes and board rules
- two-layer stackup, mechanical holes and silkscreen

It deliberately contains:

- 0 copper tracks
- 0 vias
- 0 copper zones

Unconnected-item DRC results are expected because this board is entirely
unrouted.

Two convenience archives are outside this directory:

- `../quilter-ai-test-unrouted-board.zip`
- `../quilter-ai-test-outline-only.zip`
- `../quilter-ai-test-project.zip`

## Upload for placement only

Use:

`hardware/motherboard-outline-only.kicad_pcb`

This contains only the exact board edge, with no footprints, electrical
components, tracks, vias or zones.

## Opening the project

Open `hardware/motherboard.kicad_pro`. Schematics, local symbols, footprints,
3D models and design rules are included so the project remains editable in
KiCad 10.

This experiment is not a released manufacturing package.
