# Placement optimization

The board is fixed at 200 x 150 mm with exactly two copper layers. Freerouting
has not been run. The generated placement is the input to routing, not a routed
result.

## Method

Connectors, the module socket, mounting holes and the main functional ICs are
anchored first. Remaining components are then selected in order of connectivity
to already-placed parts and placed at the lowest weighted airwire cost among
legal positions and rotations. A local pass then tries nearby moves and 90-degree
rotations, accepting only improvements.

The local passes converged as follows:

| Pass | Improved parts | Airwire reduction |
|---:|---:|---:|
| 1 | 30 | 42.8 mm |
| 2 | 8 | 5.4 mm |
| 3 | 1 | 1.3 mm |

Airwire metric weights:

- Safety nets: 3.0
- HSTX/LVDS: 2.5
- Shift-clock, shift-data and encoder nets: 1.5
- General signals: 1.0
- Power distribution: 0.35
- Ground: 0.0, because GND is completed by copper zones

## Comparison

The initial comparison used the preceding 312-component schematic and the
original 210 x 150 mm two-layer outline. The baseline uses front-only
sheet-region packing without connectivity scoring or local refinement. The
optimized result uses both sides and places connected parts together.

| Metric | Baseline | Optimized | Reduction |
|---|---:|---:|---:|
| Total airwire | 24,761.6 mm | 14,160.3 mm | 42.8% |
| Weighted airwire | 28,919.5 mm | 14,282.0 mm | 50.6% |
| Estimated crossings | 6,930 | 2,705 | 61.0% |
| Weighted crossings | 10,539.9 | 3,781.5 | 64.1% |
| 95th-percentile congestion | 0.03976 | 0.02776 | 30.2% |
| Peak congestion | 0.08402 | 0.05476 | 34.8% |

## Checkpoint 2: backlight and HSTX correction

The backlight safety gate was removed so GPIO3 drives its NPN/P-MOSFET rail
switch independently of E-stop. The HSTX outputs were corrected to the
PicoLVDS pin order: D0 on GPIO12/13, D1 on GPIO14/15, D2 on GPIO16/17 and clock
on GPIO18/19, with P on the lower-numbered GPIO. The regenerated design has 311
components, 320 nets and 300 placed PCB components plus four mounting holes.

The connectivity-aware placement was rerun from the updated netlist. Local
refinement converged after passes that improved 32, 7 and 1 parts:

| Metric | Prior optimized revision | Checkpoint 2 | Change |
|---|---:|---:|---:|
| Total airwire | 14,160.3 mm | 14,138.9 mm | -21.3 mm |
| Weighted airwire | 14,282.0 mm | 14,168.2 mm | -113.9 mm |
| Estimated crossings | 2,705 | 2,725 | +20 |
| Weighted crossings | 3,781.5 | 3,779.3 | -2.2 |
| 95th-percentile congestion | 0.02776 | 0.02701 | -2.7% |
| Peak congestion | 0.05476 | 0.05476 | unchanged |

The crossing count increased by 20, but weighted crossings decreased slightly
and both weighted length and congestion improved. Mixed-side signal nets remain
46. Placement DRC reports zero violations and 499 expected unrouted airwires.
Front and back evidence images are
`hardware/checkpoints/checkpoint-02-next-front.png` and
`hardware/checkpoints/checkpoint-02-next-back.png`.

The later power-module refinement supersedes the component count in this
historical checkpoint. The current schematic has 328 components and 321 nets,
including dedicated local decoupling, one LMR36510 buck, two peripheral 3.3 V
LDOs and one continuous GND net.

Per-block weighted airwire from the initial comparison through this checkpoint:

| Block | Initial baseline | Checkpoint 2 | Reduction |
|---|---:|---:|---:|
| PLC inputs and expansion | 3,825.4 mm | 1,321.5 mm | 65.5% |
| PLC outputs | 2,773.3 mm | 1,362.4 mm | 50.9% |
| Analog inputs | 451.5 mm | 408.4 mm | 9.5% |
| Display | 6,418.7 mm | 1,285.0 mm | 80.0% |
| Encoders | 411.1 mm | 468.0 mm | -13.8% |
| MCU and shift chains | 1,984.4 mm | 1,397.0 mm | 29.6% |
| Power | 960.4 mm | 197.2 mm | 79.5% |
| Storage, Wi-Fi and UI | 1,066.5 mm | 703.4 mm | 34.0% |
| Global nets | 11,028.1 mm | 7,025.1 mm | 36.3% |

The generated board has 105 front-side SMD footprints, 166 back-side SMD
footprints and 33 through-hole footprints. Forty-six signal nets span both SMD
sides, setting a lower bound of 46 layer transitions before local via placement.

## Channel review

The optimizer evaluated every interchangeable 74HC165 data input, 74HC595
output assignment, 74AHCT541 channel pair and ULN2003 input channel. The best
possible channel permutations would save only 30.4 mm of raw airwire, about
0.21% of the optimized weighted length. Applying those permutations would change
the firmware-visible bit order.

The existing logical mapping is therefore retained. The 595-to-541 mapping
already keeps seven of eight connections straight across each aligned package
pair. The audit is stored in
`hardware/channel-optimization-detailed.json`.

## DRC and remaining work

The optimized placement has zero placement DRC violations. Its 499 unconnected
items are the unrouted airwires expected before routing. GND connections are
completed by the front and back copper zones after routing.

Routing should not begin unless the ownership split between the two layers and
keepouts around the isolated input barrier are checked against this measured
placement.
