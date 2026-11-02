# Mechanical and placement notes

- Board outline: 200 mm x 150 mm, two copper layers.
- Four M3 clearance mounting holes.
- WeAct body: 41.402 mm x 41.148 mm, socketed on 2.54 mm headers.
- The supplied WeAct STEP model uses its PCB corner as the model origin. The
  footprint applies `(-20.7, +20.6, 0) mm`, centering the module body within
  the four socket rows and placing its reference plane on the board top.
- The module is rotated so its USB connector faces the top board edge and remains
  accessible with the module installed.
- Dedicated E-stop connector J5 and PLC inputs J7/J8 are on the input
  side. Field outputs J10-J12 are on the opposite long edge.
- Input optocouplers straddle the marked field/logic boundary.
- The main assembly is on the front.
- The J36 1x9 header accepts the passive Open-Smart 3.3 V TF breakout.
- ESP-01/ESP-01S J20 is directly above and left of the RP2350 module; its antenna must
  face away from the PCB with at least 15 mm of copper clearance.
- LCD J22 follows the upper display edge on the front side.
- Encoder connectors J13-J15 are aligned along the bottom edge with additional
  spacing for mating connector bodies.
- The switch-mode supply is grouped away from encoders and analog circuitry.
- C2 is user-placed inside the 200 x 150 mm
  outline; final manual routing is in progress.
- No component is intentionally placed under the WeAct module footprint.
