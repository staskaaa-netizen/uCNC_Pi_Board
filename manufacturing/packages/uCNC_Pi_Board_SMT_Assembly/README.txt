uCNC Pi Board - SMT Assembly Package

PCB fabrication plus SMT assembly data.

- SMT references: 230
- SMT BOM groups: 33
- Placement origin: board lower-left
- Units: millimetres, Y positive upward
- Gerbers include front/back copper, paste, mask, silkscreen and board edge

Use `bom-smt.csv` for purchasing/grouped review and `cpl.csv` for placement.
`bom-smt-refs.csv` provides a one-row-per-reference cross-check.
`bom-jlcpcb.csv` and `cpl-jlcpcb.csv` use the column names commonly requested
by JLCPCB. D53 is excluded from automated assembly and is listed in the
manual/non-SMT BOM.

Use `bom-non-smt-jlcpcb.csv` for the through-hole and manual-fit parts, or
upload `bom-all-jlcpcb.csv` when requesting one combined JLC assembly
quotation. D53 is intentionally excluded from JLC assembly and listed in the
manual/non-SMT BOM.

J54 is included in the SMT BOM and CPL because all of its electrical pads are
SMD; its two unnumbered locating holes are NPTH. All through-hole connectors
and modules are excluded from the SMT BOM and CPL and listed separately in
`bom-non-smt.csv`. `bom-full.csv` lists the complete assembly.

The supplied JLC part numbers are included. D53 is excluded from automated
assembly and listed in the separate non-SMT/manual BOM for hand fitting.

