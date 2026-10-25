# DTU KiCad-Autoplace evaluation

The DTU-EKB `KiCad-Autoplace` engine was tested against an isolated copy of the
current 200 x 150 mm, two-layer board. Existing connectors, the WeAct module,
switches, and mounting holes were listed as locked in the sidecar file.

## Run configuration

- Placement only; routing was not started.
- `ORIENT=1`
- `CROSS_WEIGHT=2`
- Seed 0
- 313 components processed
- 29 connector/module/mounting references reported locked

## Autoplacer result

| Metric | Autoplacer report |
|---|---:|
| HPWL before | 36828.67 mm |
| HPWL after | 17256.98 mm |
| HPWL reduction | 53.1% |
| Overlaps after | 0 |
| Autoplacer crossings | 4144 |
| Crossings change | +295 |

## Independent LeanCam result

| Metric | Current hand placement | Autoplaced candidate |
|---|---:|---:|
| Total airwire | 6144.7 mm | 18497.0 mm |
| Weighted airwire | 6632.3 mm | 19426.4 mm |
| Crossings | 522 | 5251 |
| Weighted crossings | 916.4 | 7042.4 |
| Mixed-side nets | 0 | 55 |
| DRC violations | 0 | 502 |

The autoplacer met its own overlap and HPWL objectives, but produced a layout
with much worse connectivity, more than 500 KiCad clearance errors, and many
cross-side nets. It is therefore not accepted and has not modified the
authoritative board.

The isolated input, output, sidecar, renders and DRC report remain under
`hardware/autoplace-test/` for reference.
