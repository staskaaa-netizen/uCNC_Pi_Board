# Mechanical notes

- PCB outline: 160 mm x 120 mm, two copper layers, 1.6 mm nominal thickness.
- Mounting: four M3 clearance holes.
- Main assembly and J22 are on F.Cu.
- The WeAct body is 41.402 mm x 41.148 mm and uses 2.54 mm perimeter headers.
- The WeAct module is not soldered directly to the carrier. Fit four 1 x 15,
  2.54 mm female sockets on the motherboard and mating male pin headers on the
  module.
- The 3D module reference is raised 8.5 mm above F.Cu to represent the mated
  socket stack. Confirm the chosen socket hardware against the enclosure
  clearance and USB opening.
- The module USB connector faces the accessible board edge.
- J5, J7 and J8 are grouped on the isolated field-input side.
- J10-J12 and J28-J30/J32 are grouped on the output side.
- The J36 TF-card breakout header and J54 microSD socket share one electrical
  interface. Use one card source at a time.
- ESP socket J20 faces the board perimeter. Keep at least 15 mm of copper- and
  component-free clearance around its antenna.
- J22 is a 2 x 10, 2.00 mm LCD connector on F.Cu.
- J13-J15 are aligned on one long edge for encoder access.
- The switching supplies are grouped away from the ADC dividers and encoder
  receivers.
- No component is intentionally placed under the WeAct module.
