# Mechanical and placement notes

- Board outline: 200 mm x 150 mm, two copper layers.
- Four M3 clearance mounting holes.
- WeAct body: 41.402 mm x 41.148 mm, socketed on 2.54 mm headers.
- The module is rotated so its USB connector faces the top board edge and remains
  accessible with the module installed.
- Dedicated E-stop/HOLD connectors J5/J6, START connector J26 and PLC inputs J7/J8 are on the input
  side. Field outputs J10-J12 are on the opposite long edge.
- Input optocouplers straddle the marked field/logic boundary.
- Connectors, module, power and display circuitry stay on the front. Most
  input/output conditioning, shift logic, keyboard filtering and analog-input
  networks are placed on the back.
- Full-size SD J19 is on the right edge with the insertion mouth outward.
- ESP-01S J20 is directly above and left of the RP2350 module; its antenna must
  face away from the PCB with at least 15 mm of copper clearance.
- HDMI J23 is rotated 90 degrees so its connector opening follows the top board
  edge. LCD J22 uses the same edge.
- Encoder connectors J13-J15 are aligned along the bottom edge with additional
  spacing for mating connector bodies.
- The switch-mode supply is grouped away from encoders and analog circuitry.
- No component is intentionally placed under the WeAct module footprint.
