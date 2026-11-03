# Schematic readability experiment

Date: 2026-11-03

This directory compares two ways to turn the current PRE-FINAL label-only
KiCad hierarchy into conventional electrical schematics. The source hierarchy
and `hardware/motherboard.kicad_pcb` remain authoritative and were not changed.

## Current source contract

The contracts are extracted from `hardware/motherboard.net.xml`. The current
power sheet contains 55 components, 25 named nets and 114 connected pins.
`U3.4` is a genuinely unconnected power-good pad and is represented by one
no-connect marker in the generated schematics.

| Sheet | Components | Named nets | Connected pins |
| --- | ---: | ---: | ---: |
| Power | 55 | 25 | 114 |
| PLC inputs | 64 | 71 | 222 |
| PLC outputs | 72 | 130 | 366 |
| MCU / shift chains | 19 | 119 | 201 |
| Encoders | 9 | 22 | 45 |
| LVDS display | 3 | 18 | 32 |
| microSD / Wi-Fi / I2C | 16 | 25 | 75 |
| Analog I/O | 43 | 31 | 105 |
| **Total** | **281** | **441** | **1160** |

Source extract: [inputs/source-power.pdf](inputs/source-power.pdf). Exact
component, net and pin contracts are under `inputs/`.

## A: TheEnergyNerd/schemagen

The current power contract was rendered directly by schemagen and upgraded and
exported with KiCad 10. No placement coordinates were authored for Method A.

- [KiCad schematic](method-a/lean-power-a.kicad_sch)
- [PDF](method-a/lean-power-a.pdf)
- [Netlist](method-a/lean-power-a.net)
- [ERC](method-a/erc.json)
- [Netlist comparison](method-a/netlist-comparison.json)

Result: 55/55 components, 8 wires, 2 junctions, 112 global labels and one
no-connect. The netlist preserves every component, value, footprint, named net
and connected node. Schemagen still places 34 components in one oversized
regulation block and leaves the isolated 12 V converter in `MISC`.

## B: Python re-layout of KiCad symbols

`tools/build_python_power_schematic.py` uses the existing embedded symbols and
the fresh pin contract. Placement is divided into explicit electrical stages:

1. 24 V input, fuse, TVS and reverse-polarity protection.
2. 5 V buck converter, feedback and output capacitors.
3. 3V3 point-of-load regulator and ferrite-filtered analog rail.
4. 5 V and 3V3 status indicators.
5. Isolated PLC-24 V to 12 V backlight converter and feedback.
6. Off-sheet power references.

- [KiCad schematic](method-b/lean-power-b.kicad_sch)
- [PDF](method-b/lean-power-b.pdf)
- [Netlist](method-b/lean-power-b.net)
- [ERC](method-b/erc.json)
- [Netlist comparison](method-b/netlist-comparison.json)

Result: 55/55 components on a 1.27 mm grid, 40 wires, 3 junctions, 95 labels,
and one deliberate no-connect. The named netlist is identical after normalizing
KiCad's root-sheet `/` prefix. ERC reports exactly the same two isolated-label
warnings as the source power sheet and no errors.

[A/B comparison PDF](schematic-a-vs-b.pdf)

Method B remains the recommended review schematic. Its block structure follows
power flow and separates the 5 V and isolated 12 V converters; Method A is
useful as a fast connectivity scaffold.

## Other hierarchy sheets

All seven remaining hierarchy sheets were regenerated from the current
contracts. Every generated netlist has the same references, values, footprints,
named nets and connected nodes as its source sheet.

See [other-sheets/README.md](other-sheets/README.md) and
[all-other-sheets.pdf](other-sheets/all-other-sheets.pdf). Six sheets reproduce
source ERC counts and types exactly. The MCU sheet remains electrically
identical but KiCad 10 emits two fewer `Z4`-related presentation findings after
the label is moved.

[All Python schematics](all-sheets-python.pdf) combines the power winner and all
seven additional sheets into an eight-page package.

## Reproduction

Run from the repository root:

```powershell
$sheets = 'power','field_inputs','field_outputs','mcu_io','encoders',
          'display','storage_wifi_ui','analog_io'
foreach ($sheet in $sheets) {
  python experiments/power-schematic-readability/tools/extract_power_netlist.py `
    --netlist hardware/motherboard.net.xml `
    --sheet "$sheet.kicad_sch" `
    --outdir experiments/power-schematic-readability/inputs
}

python experiments/power-schematic-readability/tools/build_python_power_schematic.py --force
python experiments/power-schematic-readability/tools/build_python_hierarchy.py --force
python experiments/power-schematic-readability/tools/summarize_hierarchy.py
```

The generators fail if any current component is missing from a sheet's block
map. PDF, netlist, PNG and ERC exports use KiCad 10.0.1 `kicad-cli`.
