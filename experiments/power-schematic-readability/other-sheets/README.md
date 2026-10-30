# Generated hierarchy sheets

These are first-pass Python re-layouts of every hierarchy sheet except
`power.kicad_sch`. The source schematics and PCB were not modified.

| Sheet | Paper | Components | Nets | Wires | Labels | Netlist | ERC source/generated |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Analog I/O · [KiCad](analog_io-python.kicad_sch) · [PDF](analog_io-python.pdf) | A1 | 40 | 29 | 62 | 71 | identical | 6/6 (same types) |
| LVDS display · [KiCad](display-python.kicad_sch) · [PDF](display-python.pdf) | A3 | 5 | 18 | 32 | 38 | identical | 9/9 (same types) |
| Encoders · [KiCad](encoders-python.kicad_sch) · [PDF](encoders-python.pdf) | A3 | 9 | 22 | 22 | 37 | identical | 10/10 (same types) |
| Isolated field inputs · [KiCad](field_inputs-python.kicad_sch) · [PDF](field_inputs-python.pdf) | A0 | 102 | 94 | 140 | 247 | identical | 12/12 (same types) |
| PLC and motion outputs · [KiCad](field_outputs-python.kicad_sch) · [PDF](field_outputs-python.pdf) | A1 | 71 | 110 | 99 | 269 | identical | 41/41 (same types) |
| RP2350B and shift chains · [KiCad](mcu_io-python.kicad_sch) · [PDF](mcu_io-python.pdf) | A2 | 23 | 119 | 20 | 196 | identical | 139/139 (same types) |
| Storage, Wi-Fi and UI · [KiCad](storage_wifi_ui-python.kicad_sch) · [PDF](storage_wifi_ui-python.pdf) | A2 | 31 | 49 | 34 | 92 | identical | 30/30 (same types) |

The KiCad files contain the original embedded symbol definitions and
preserve references, values, footprints and local connectivity. Local
nets are wired where a short orthogonal tree can be placed; cross-sheet
signals and high-fanout rails retain labels.

ERC violations are unchanged in count and type from the corresponding
standalone source sheet. Most are expected because power sources and
signal drivers live on other sheets.

Combined PDF: `all-other-sheets.pdf`
