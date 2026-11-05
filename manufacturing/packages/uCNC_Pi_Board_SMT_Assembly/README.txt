uCNC Pi Board - SMT Assembly Package

PCB fabrication plus SMT assembly data.

- SMT references: 236
- SMT BOM groups: 42
- Placement origin: board lower-left
- Units: millimetres, Y positive upward
- Gerbers include front/back copper, paste, mask, silkscreen and board edge

Use `bom-smt.csv` for purchasing/grouped review and `cpl.csv` for placement.
`bom-smt-refs.csv` provides a one-row-per-reference cross-check.
`bom-jlcpcb.csv` and `cpl-jlcpcb.csv` use the column names commonly requested
by JLCPCB. The JLCPCB part-number column is present but blank because this
repository does not contain verified LCSC part numbers.

Use `bom-non-smt-jlcpcb.csv` for the through-hole and mixed-mount parts, or
upload `bom-all-jlcpcb.csv` when requesting one combined SMT and through-hole
assembly quotation.

J54 is included in the SMT BOM and CPL because all of its electrical pads are
SMD; its two unnumbered locating holes are NPTH. All through-hole connectors
and modules are excluded from the SMT BOM and CPL and listed separately in
`bom-non-smt.csv`. `bom-full.csv` lists the complete assembly.

LCSC part numbers are not present. The BOM is suitable for an assembly house
that sources by manufacturer/MPN; direct JLCPCB upload requires LCSC numbers.

