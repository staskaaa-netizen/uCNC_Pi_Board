# Manufacturing files

## BOMs

- `bom.csv`: complete grouped BOM for the current design, covering all
  270 physical sourced parts in 49 lines.
- `bom-smt.csv`: SMT-only grouped BOM, covering 235 SMD footprints in 39
  lines. It includes the PCB side for each group.
- `bom-smt-refs.csv`: the same 235 SMT parts in one-row-per-reference format.
- `bom-report.json`: generation counts and the complete non-SMT exclusion list.

The SMT BOM was generated from actual PCB pad types, not only footprint names.
It includes every footprint whose pads are exclusively SMD and excludes:

- 34 through-hole connectors/modules.
- `J54`, whose microSD footprint contains mixed SMD and through-hole pads.

`JP5` is a solder-jumper PCB feature with no part to place and is intentionally
omitted. Power-flag symbols are logical-only and have no physical footprint.
Connector designators and function labels are printed on `F.Silkscreen`; the
J22 LVDS pinout uses its dedicated row legends. All visible reference and value
fields are placed clear of pads, vias and other silkscreen features. All 275
component references are visible; center placement is preferred, with a nearby
clear fallback for small passives where a legal 0.8 mm label cannot fit inside
the body. All 309 visible reference/value fields use 0.8 mm text and a 0.12 mm
stroke. LED functional channel values remain on `F.Fab`.

All currently eligible SMT parts are on side F. Manufacturer and MPN fields
are complete, but this repository does not contain LCSC part numbers. A direct
JLCPCB SMT upload therefore requires those LCSC numbers to be populated first;
an assembly house that sources from MPNs can use these files as generated.
All 35 indicators use the green Lite-On `LTST-C150KGKT` 1206 LED.

## Ready-to-upload packages

- `uCNC_Pi_Board_PCB_Fabrication.zip`: Gerbers and Excellon drill files only.
- `uCNC_Pi_Board_SMT_Assembly.zip`: fabrication data, both SMT BOM formats,
  the matching 235-reference `cpl.csv`, assembly PDFs and the full BOM.

The SMT placement origin is the PCB lower-left corner. Coordinates are in
millimetres with positive Y upward. Rebuild both archives after any PCB change:

```powershell
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  tools/export_manufacturing_packages.py
```
