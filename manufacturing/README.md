# Manufacturing files

## BOMs

- `bom.csv`: complete grouped BOM for the current design, covering all
  263 physical sourced parts in 44 lines.
- `bom-smt.csv`: SMT-only grouped BOM, covering 227 SMD footprints in 33
  lines. It includes the PCB side for each group.
- `bom-smt-refs.csv`: the same 227 SMT parts in one-row-per-reference format.
- `bom-jlcpcb.csv`: grouped SMT BOM using the columns `Comment`, `Designator`,
  `Footprint` and `JLCPCB Part #`.
- `cpl.csv`: complete placement list using the assembly house's explicit
  KiCad field names.
- `cpl-jlcpcb.csv`: one row per SMT reference using `Designator`, `Mid X`,
  `Mid Y`, `Layer` and `Rotation`.
- `jlcpcb-report.json`: BOM/CPL cross-check result, coordinate origin and
  missing JLCPCB part-number count.
- `jlcpcb-stock-audit.csv`: live stock, catalogue class (Basic/Extended),
  package and manufacturer part number for every SMT BOM group.
- `bom-non-smt.csv`: grouped through-hole and manual-fit parts excluded from
  the SMT CPL.
- `bom-non-smt-refs.csv`: the same non-SMT parts in one-row-per-reference
  format.
- `bom-non-smt-jlcpcb.csv`: grouped non-SMT BOM using the JLCPCB
  column names.
- `bom-all-jlcpcb.csv`: one combined JLC assembly BOM covering 262 parts for
  an SMT-plus-through-hole quotation; manual-only D53 is omitted.
- `bom-report.json`: generation counts and the complete non-SMT exclusion list.

The SMT BOM was generated from actual PCB pad types, not only footprint names.
It includes every footprint whose electrical pads are exclusively SMD and
excludes 35 through-hole connectors/modules plus manually fitted D53. J54 is
included because its eleven electrical pads are SMD; its two unnumbered
locating holes are NPTH.

`JP5` is a solder-jumper PCB feature with no part to place and is intentionally
omitted. Power-flag symbols are logical-only and have no physical footprint.
Connector designators and function labels are printed on `F.Silkscreen`; the
J22 LVDS pinout uses its dedicated row legends. All visible reference and value
fields are placed clear of pads, vias and other silkscreen features. All 268
component references are visible; center placement is preferred, with a nearby
clear fallback for small passives where a legal 0.8 mm label cannot fit inside
the body. All 309 visible reference/value fields use 0.8 mm text and a 0.12 mm
stroke. LED functional channel values remain on `F.Fab`.

All automated SMT parts are on side F. Manufacturer and MPN fields are
complete. The supplied `RP23CNC_JLCPCB_BOM_upload.csv` mapping is applied to
`bom-jlcpcb.csv`. D53 is excluded from automated assembly and appears in the
separate non-SMT/manual BOM.
All 35 indicators use the green Hubei KENTO `KT-0805G` 0805 LED.
The stock audit from 2026-11-07 shows all 33 SMT groups in stock: 16 Basic and
17 Extended groups.

## Ready-to-upload packages

- `uCNC_Pi_Board_PCB_Fabrication.zip`: Gerbers and Excellon drill files only.
- `uCNC_Pi_Board_SMT_Assembly.zip`: fabrication data, SMT and non-SMT BOMs,
  the matching 227-reference `cpl.csv`, assembly PDFs and the combined BOM.

The Gerbers, drill files and SMT placement files all use the shared drill/place
origin at the PCB lower-left corner. Coordinates are in millimetres with
positive Y upward. JLCPCB footprint-orientation corrections are applied in
`cpl-jlcpcb.csv`. Rebuild both archives after any PCB change:

```powershell
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  tools/export_manufacturing_packages.py
```
