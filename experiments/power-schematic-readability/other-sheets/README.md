# Generated hierarchy sheets

These are first-pass Python re-layouts of every hierarchy sheet except
`power.kicad_sch`. The source schematics and PCB were not modified.

| Sheet | Paper | Components | Nets | Wires | Labels | Netlist | ERC source/generated |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| Analog I/O / [KiCad](analog_io-python.kicad_sch) / [PDF](analog_io-python.pdf) | A1 | 43 | 31 | 94 | 68 | identical | 6/6 (same types) |
| LVDS display / [KiCad](display-python.kicad_sch) / [PDF](display-python.pdf) | A3 | 3 | 18 | 11 | 27 | identical | 10/10 (same types) |
| Encoders / [KiCad](encoders-python.kicad_sch) / [PDF](encoders-python.pdf) | A3 | 9 | 22 | 19 | 38 | identical | 10/10 (same types) |
| Isolated field inputs / [KiCad](field_inputs-python.kicad_sch) / [PDF](field_inputs-python.pdf) | A0 | 64 | 71 | 78 | 192 | identical | 8/8 (same types) |
| PLC and motion outputs / [KiCad](field_outputs-python.kicad_sch) / [PDF](field_outputs-python.pdf) | A0 | 72 | 130 | 27 | 353 | identical | 33/33 (same types) |
| RP2350B and shift chains / [KiCad](mcu_io-python.kicad_sch) / [PDF](mcu_io-python.pdf) | A2 | 19 | 119 | 14 | 194 | identical | 134/132 (different types) |
| Storage, Wi-Fi and UI / [KiCad](storage_wifi_ui-python.kicad_sch) / [PDF](storage_wifi_ui-python.pdf) | A2 | 16 | 25 | 24 | 66 | identical | 16/16 (same types) |

The KiCad files contain the original embedded symbol definitions and
preserve references, values, footprints and local connectivity. Local
nets are wired where a short orthogonal tree can be placed; cross-sheet
signals and high-fanout rails retain labels.

Six of the seven generated sheets reproduce the source ERC violation
counts and types exactly. The MCU sheet is electrically identical, but
KiCad 10 reports two fewer violations after `Z4` is moved to its new
location: one `isolated_pin_label` and one `pin_not_driven` are no
longer emitted. This is an ERC presentation difference, not a changed
connection; no node or net differs in the exported netlist.

Combined PDF: `all-other-sheets.pdf`
