# Schematic readability experiment

Date: 2026-10-29

This experiment compares two ways to turn the label-only
`hardware/power.kicad_sch` sheet into a conventional electrical schematic.
The source schematic and `hardware/motherboard.kicad_pcb` were not modified.

## Scope and source contract

The authoritative XML netlist identifies 41 components on the power sheet,
88 connected pins, and 20 named nets. The extracted subdesign is stored in
`inputs/source-power.json`; its exact pin-to-net mapping is in
`inputs/source-pin-contract.json`.

Original source export: `inputs/source-power.pdf`

## A: TheEnergyNerd/schemagen

The extracted power-sheet netlist was passed directly to schemagen, then
upgraded and exported with KiCad 10. No layout coordinates were authored for
this result. Schemagen revision:
`92a645d3a0615d61d68bb0306e04c5ca42b8e163`.

- KiCad 10 schematic: `method-a/lean-power-a.kicad_sch`
- PDF: `method-a/lean-power-a.pdf`
- Netlist: `method-a/lean-power-a.net`
- Netlist comparison: `method-a/netlist-comparison.json`
- ERC: `method-a/erc.json`

Result: 41/41 components placed; 13 wires, 7 junctions, and 81 labels/power
symbols. The netlist is exactly identical to the source for all 41 references,
20 net names, and 88 connected pins. ERC reports 45 warnings and no errors:
41 missing-library metadata warnings for the generated `schemagen:*` symbols
plus four intentional single-label rail warnings.

Readability: weak. The heuristic puts 34 of 41 components into one oversized
`POWER REGULATION` block. Most capacitors are reduced to a uniform row, most
connections remain labels, and the buck, feedback, LDO, and status functions
are not visually separated.

## B: Python re-layout of existing symbols

`tools/build_python_power_schematic.py` copies the source embedded symbol
definitions, places all 41 instances on a 1.27 mm grid, and emits orthogonal
wires with explicit junctions. The layout follows the electrical power flow:

```text
24 V input -> fuse -> reverse-polarity protection -> 5 V buck
           -> 3V3 LDO -> ferrite-filtered analog rail
```

- KiCad 10 schematic: `method-b/lean-power-b.kicad_sch`
- PDF: `method-b/lean-power-b.pdf`
- Netlist: `method-b/lean-power-b.net`
- Netlist comparison: `method-b/netlist-comparison.json`
- ERC: `method-b/erc.json`

Side-by-side PDF: `schematic-a-vs-b.pdf`

Result: 41/41 components placed; 88 wires, 50 junctions, and 20 local labels.
The netlist is identical after normalizing KiCad's root-sheet `/` prefix on
local-label net names. ERC reports five warnings and no errors: four
intentional single-label rail warnings and one missing-library metadata warning
for the embedded `LeanCam` library.

Readability: substantially better. The schematic groups input protection, buck
conversion, feedback, point-of-load regulation, status LEDs, and off-sheet rails
into visible functional regions. The main rails and ground return are drawn as
wires. Remaining weaknesses are long ground stubs across the page and dense
wire/junction detail around the buck controller.

## Comparison

| Measure | Source | A: schemagen | B: Python re-layout |
| --- | ---: | ---: | ---: |
| Components | 41 | 41 | 41 |
| Nets | 20 | 20 | 20 |
| Connected nodes | 88 | 88 | 88 |
| Missing/changed connections | - | 0 | 0 |
| Actual wires | 0 | 13 | 88 |
| Labels / power symbols | 88 | 81 | 20 |
| Junctions | 0 | 7 | 50 |
| Wire length | 0 mm | 53.34 mm | 2877.82 mm |
| ERC warnings / errors | n/a | 45 / 0 | 5 / 0 |
| Original symbol graphics | yes | no | yes |
| Manual placement decisions | - | none | 41 placements plus routing |

A has the least setup effort but does not achieve a conventional reading flow.
B is electrically identical and is clearly more readable, but requires a
maintained Python layout with explicit placement and route definitions. The
large B wire-length figure reflects visible ground and rail buses; A's 53 mm is
low only because it offloads nearly all connectivity to labels.

Recommendation: use **B** for the human-readable power sheet. For future boards,
start from B's block/routing vocabulary but derive component locations and net
buses from structured metadata instead of repeatedly tuning a monolithic
schematic. Schemagen A is useful as a fast connectivity scaffold, but its
current automatic grouping is not suitable for final power-stage review.

## Other hierarchy sheets

The Python re-layout approach was subsequently applied to all seven remaining
hierarchy sheets. They retain the original embedded symbols, values, footprints
and local connectivity; short local nets are wired and cross-sheet or
high-fanout nets remain labelled.

See `other-sheets/README.md` for the per-sheet verification table and
`other-sheets/all-other-sheets.pdf` for a seven-page combined preview. Every
generated sheet has an identical named netlist to its source sheet. ERC
violation counts and types are also unchanged from standalone ERC on the source
sheet.

`all-sheets-python.pdf` combines the power-sheet winner with all seven
additional sheets into one eight-page review package.

## Reproduction

Run from the repository root:

```powershell
python experiments/power-schematic-readability/tools/extract_power_netlist.py `
  --netlist hardware/motherboard.net.xml `
  --outdir experiments/power-schematic-readability/inputs

python experiments/power-schematic-readability/tools/build_python_power_schematic.py

python experiments/power-schematic-readability/tools/compare_netlists.py `
  --source experiments/power-schematic-readability/inputs/source-power.json `
  --generated experiments/power-schematic-readability/method-b/lean-power-b.net `
  --out experiments/power-schematic-readability/method-b/netlist-comparison.json
```

Method A uses schemagen externally and then
`kicad-cli sch upgrade --force`, `kicad-cli sch export pdf`, and
`kicad-cli sch export netlist --format kicadsexpr`.
