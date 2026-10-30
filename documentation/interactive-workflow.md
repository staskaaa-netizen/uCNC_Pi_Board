# Interactive placement workflow

The PCB is optimized iteratively with explicit human checkpoints. The generator
remains authoritative and routing is not started until placement is approved.

## Checkpoint 1: mechanical anchors

The current anchors are:

- J1-J26: external and board-level connectors.
- MOD1: WeAct RP2350B module socket.
- SW2: ESP programming switch.
- H1-H4: M3 mounting holes.

Front and back checkpoint images are generated directly from the KiCad board by
`tools/render_checkpoint.py`. Red outlines mark proposed anchors, solid airwires
show same-side connections, and dashed airwires cross sides.

## Checkpoint 2: first connectivity iteration

The backlight request is now a direct MOSFET-drive signal and no longer passes
through the output safety gate. The HSTX mapping has also been corrected to the
verified PicoLVDS order. The two-sided placement was rerun from that netlist:

- Front: `hardware/checkpoints/checkpoint-02-next-front.png`
- Back: `hardware/checkpoints/checkpoint-02-next-back.png`
- Metrics: `hardware/checkpoint-02-next-metrics.json`
- Placement DRC: `hardware/checkpoint-02-next-drc.json`

Placement constraints still under review are the Wi-Fi antenna keepout, the
3.5 mm jack mating-body clearance and the HDMI connector opening relative to the
actual board edge. Component placement can continue from this checkpoint; the
anchors should not be regenerated from scratch.

## Optimization loop

After anchor approval:

1. Lock the approved anchors.
2. Optimize free components by connectivity, changing position and rotation.
3. Evaluate weighted airwire length, crossings and congestion per functional
   block and across the whole board.
4. Review significant channel-swap opportunities without changing the
   firmware-visible bit mapping unless explicitly approved.
5. Generate new front/back checkpoint images.
6. Incorporate human feedback and continue from the current result.
7. Run final placement DRC.
8. Start routing only after explicit placement approval.

Freerouting is never used to hide an unresolved placement problem.

## Staged module workflow

Unplaced components are parked outside the active board outline. They remain
connected in the netlist but are omitted from module checkpoint images and
inside-only metrics. The current board is the source of truth; each iteration
adds one functional module without disturbing modules already placed.

```powershell
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  .\tools\place_module.py --sheet "Power and supervision" --region "12,8,82,64"
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  .\tools\render_checkpoint.py --board hardware\motherboard.kicad_pcb `
  --outdir hardware\checkpoints --checkpoint checkpoint-08-power --inside-only
```

To rebuild the schematic-defined footprints without disturbing the staged
placement, seed the generator from the current board:

```powershell
$env:LEANCAM_STAGED_BOARD = 'hardware\motherboard.kicad_pcb'
& 'C:\Users\s.zachazevski\AppData\Local\Programs\KiCad\10.0\bin\python.exe' `
  .\tools\generate_pcb.py
Remove-Item Env:LEANCAM_STAGED_BOARD
```

This preserves every existing footprint's position, rotation and side while
adding or removing components from the regenerated netlist. New components are
parked outside the board for the next module pass.

The drilled field connectors now use Phoenix `MCV 1,5` vertical footprints.
`tools/sync_board_footprints.py` applies authoritative footprint substitutions
without changing staged positions.

Power and supervision is placed at checkpoint 8:

- Front: `hardware/checkpoints/checkpoint-08-power-front.png`
- Back: `hardware/checkpoints/checkpoint-08-power-back.png`
- Metrics: `hardware/checkpoint-08-power-metrics.json`
- DRC: `hardware/checkpoint-08-power-drc.json`

The module adds 48 footprints around J1. Its weighted internal airwire is
288.6 mm. After the decoupling revision, 88 footprints are inside the outline
and 224 are parked for the remaining modules. Placement DRC reports zero
violations.

After manual power-stage compaction, the power block was refined again:

- `PGND`, `AGND` and both ground net ties were removed in favor of one
  continuous GND plane.
- Dedicated 100 nF decoupling was added for every supply-bearing IC.
- Logic decoupling moved to 0805; high-voltage input ceramics remain 1206.
- `C4`/`C7` were placed at the U1 pins, and `C76`/`C10`/`C13` at U2.
- The power module now contributes 297.7 mm of weighted airwire with 142
  in-board crossings; placement DRC reports zero violations.

Final power review images are `checkpoint-11-power-final-front.png` and
`checkpoint-11-power-final-back.png`. The staged board is
`checkpoint-11-power-final.kicad_pcb`.

The intermediate AP63205 design was replaced by the requested single LMR36510
24 V-to-5 V, 1 A buck. The module's local 3.3 V regulator is retained for the
RP2350B only. Separate AMS1117-3.3 LDOs supply the peripheral rail and the
optional ESP-01S. The external reset button, LM66100 ideal diode, three-pin
reset diode, reset capacitor, TPS3839 supervisor, optional I2C pull-ups and old
3.3 V buck parts have been removed. The ESP programming button remains because
it is not provided by the WeAct board.

Checkpoint 17 is the current power-stage baseline:

- Front: `hardware/checkpoints/checkpoint-17-bottom-plane-front.png`
- Back: `hardware/checkpoints/checkpoint-17-bottom-plane-back.png`
- Board: `hardware/checkpoints/checkpoint-17-bottom-plane.kicad_pcb`
- Metrics: `hardware/checkpoint-17-bottom-plane-metrics.json`
- DRC: `hardware/checkpoint-17-bottom-plane-drc.json`

Only B.Cu has a full GND plane; the only F.Cu zone is the ESP antenna keepout.
The bottom plane is filled, the LMR36510 thermal-via field is connected, and
placement DRC reports zero violations. The 499 unconnected items are expected
before routing.

Checkpoint 18 removes the abandoned LCD-logic power path. The TPS22917 load
switch, its AND gate, J3 and their dedicated capacitors are absent from the
schematic and PCB rather than merely marked DNP. Only the J2 LED backlight path
remains, with JP1 selecting +5 V or `VIN_PROT` ahead of the Q2/Q3 switch.

- Front: `hardware/checkpoints/checkpoint-18-render/checkpoint-18-backlight-front.png`
- Back: `hardware/checkpoints/checkpoint-18-render/checkpoint-18-backlight-back.png`
- DRC: `hardware/checkpoint-18-backlight-drc.json`
- Metrics: `hardware/checkpoint-18-backlight-metrics.json`
- Decoupling map: `documentation/decoupling-map.md`

Checkpoint 19 keeps every IC at the position and rotation supplied in the
hand-moved board. It removes the unnecessary keyboard pull-down arrays RN14 and
RN15, then swaps equivalent 74HC595 Q outputs and 74AHCT541 channels for the
U10/U24 and U11/U25 pairs. The logical `OUTn -> BUFYn -> MOTIONn` contract is
unchanged.

- Before: `hardware/checkpoints/checkpoint-19-gate-before/checkpoint-19-before-front.png`
- After: `hardware/checkpoints/checkpoint-19-gate-swap/checkpoint-19-after-front.png`
- Board: `hardware/checkpoints/checkpoint-19-gate-swap.kicad_pcb`
- Gate analysis: `hardware/checkpoint-19-gate-swap-analysis.json`
- Metrics: `hardware/checkpoint-19-gate-swap-metrics.json`
- DRC: `hardware/checkpoint-19-gate-swap-drc.json`

The two optimized register/buffer pairs now have zero analyzed ratline
crossings, down from 37 and 38 respectively. Overall weighted airwire fell from
7124.2 mm to 6982.9 mm, total crossings from 741 to 655, and weighted crossings
from 1094.7 to 1008.7. The checkpoint has 45 placement violations inherited
from the hand-moved optocoupler/diode cluster and U34/C27; none involve the
gate-swap area.

Checkpoint 20 removes J21 and re-optimizes the RN16-RN19 motion resistor
channels together with the U10/U24 and U11/U25 equivalent channels. No IC was
moved. The `OUTn -> BUFYn` logical names remain stable; RN16/RN17 use the
explicit output-pair swap documented in `documentation/io-bit-map.md`, and the
physical 74HC595 pin permutation is recorded there as well.

- Front: `hardware/checkpoints/checkpoint-20-final/checkpoint-20-final-front.png`
- Board: `hardware/checkpoints/checkpoint-20-final.kicad_pcb`
- Analysis: `hardware/checkpoint-20-final-analysis.json`
- Metrics: `hardware/checkpoint-20-final-metrics.json`
- DRC: `hardware/checkpoint-20-final-drc.json`

Both register/buffer pairs now have zero analyzed local ratline crossings. The
latest checkpoint has zero placement DRC violations; its 499 unconnected items
are expected before routing.

Checkpoint 21 is the first component-by-component refinement after checkpoint
20:

- RN16/RN17 source pins remain fixed; only their MOTION output pairs are
  swapped `1↔2` and `3↔4`.
- U12, U26 and U27 channel assignments are optimized together from U12 through
  the DO connector. All IC positions remain unchanged.
- The U12/U26/U27 path now has zero analyzed local crossings.
- Board: `hardware/checkpoints/checkpoint-21-final.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-21-final/checkpoint-21-final-front.png`
- Analysis: `hardware/checkpoint-21-final-analysis.json`
- Metrics: `hardware/checkpoint-21-final-metrics.json`
- DRC: `hardware/checkpoint-21-final-drc.json`

Future input and passive placement follows the one-channel-at-a-time plan in
the repository root `TODO.md`.

Checkpoint 25 simplifies each analog input to one 100 k upper resistor and one
33 k lower resistor. R62/R65/R68 are removed and the `AIx_MID` nets no longer
exist. Divider/filter groups are placed beside J24, not around MOD1. AI1 and AI2
then copy the approved AI0 geometric template at their corresponding connector
pin heights.

- Board: `hardware/checkpoints/checkpoint-25-analog-final.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-25-analog/checkpoint-25-analog-front.png`
- DRC: `hardware/checkpoint-25-analog-drc.json`
- Metrics: `hardware/checkpoint-25-analog-metrics.json`

Checkpoint 26 adds the first output path. RN8 was placed beside RN16/J10,
completing the physical pull-down/series arrangement for motion outputs 0-3.
Only logical output 0 was routed:

- `OUT0`: U10 pin 1 to U24 pin 8
- `BUFY0`: U24 pin 12 to RN16 pin 3 and RN8 pin 1
- `MOTION1`: RN16 pin 6 to J10 pin 2

All three nets have zero unconnected items and the route uses F.Cu only. The
remaining output paths remain unrouted.

- Board: `hardware/checkpoints/checkpoint-26-output0.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-26-output0/checkpoint-26-output0-front.png`
- DRC: `hardware/checkpoint-26-output0-final-drc.json`
- Metrics: `hardware/checkpoint-26-output0-metrics.json`

Checkpoint 27 adds the first isolated PLC input:

- R18, D13 and D14 are grouped at J7.
- C33 and the shared RN2 pull-up array are grouped beside U18/U9.
- `FIELD_IN0`, `FLD_LED0_A`, `FLD_OPTO0_A` and `PLC_IN0_N` are fully connected.
- The U18 field-common return uses a controlled B.Cu route and two vias.
- C33 has its own short GND via into the bottom plane.
- Board: `hardware/checkpoints/checkpoint-27-input0.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-27-input0/checkpoint-27-input0-front.png`
- DRC: `hardware/checkpoint-27-input0-final-drc.json`
- Metrics: `hardware/checkpoint-27-input0-metrics.json`

Checkpoint 28 keeps four-channel LTV-847S SOIC-16W optocouplers for the PLC
input groups while the dedicated E-stop and fault channels use individual
EL3H7 DIP-4 optocouplers. Input pull-up arrays and filter capacitors are
removed; each used output has an individual 4.7 k pull-up. Keyboard inputs
retain only the RN22/RN24 series arrays; RN23/RN25 and C59-C66 are removed.

- Board: `hardware/checkpoints/checkpoint-28-input0.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-28-final/checkpoint-28-final-front.png`
- DRC: `hardware/checkpoint-28-input0-final-drc.json`
- Metrics: `hardware/checkpoint-28-final-metrics.json`

Checkpoint 22 is based on the latest hand placement:

- Re-ran equivalent-pin optimization without moving any IC.
- Eliminated the remaining local U11/U25 crossing by changing one U11 Q-pin
  assignment.
- RN16/RN17 retain the requested output-pair swaps and both have zero local
  crossings. RN18 has one analyzed local crossing left for a later step.
- U12/U26/U27 remain at zero local crossings.
- Board: `hardware/checkpoints/checkpoint-22-final.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-22-final/checkpoint-22-final-front.png`
- Analysis: `hardware/checkpoint-22-final-analysis.json`
- Metrics: `hardware/checkpoint-22-final-metrics.json`
- DRC: `hardware/checkpoint-22-final-drc.json`

The DTU autoplacer was evaluated separately and rejected. See
`documentation/autoplacer-evaluation.md`.

Checkpoint 23 removes the remaining obsolete legacy branches and starts
incremental manual routing:

- Removed C9, C12, C21, C78, D3, D7, FB3, L2, R2, R3, R42, R43, SW1, U3 and
  U4 from the schematic, netlist, PCB and BOM.
- Kept RN28/RN29 as the intentional HDMI alternate-population arrays.
- Swapped RN18 output pins 3/4, eliminating its final analyzed local crossing.
- Routed only `OUT9` from U11 pin 1 to U25 pin 9 on F.Cu at 0.25 mm.
- Confirmed the staged generator preserves existing track segments.
- Board: `hardware/checkpoints/checkpoint-23-final.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-23-route-out9/checkpoint-23-route-out9-front.png`
- DRC: `hardware/checkpoint-23-final-drc.json`

Checkpoint 30 restores four-channel LTV-847S packages for PLC inputs while
keeping the dedicated E-stop and fault channels as individual EL3H7 DIP-4
parts. The approved R/LED/reverse-diode field chain is replicated for every PLC
input at its J7/J8 pin position.

- 48 field-chain components placed, none parked
- DRC: `hardware/checkpoint-30-input-chain-drc.json`
- Metrics: `hardware/checkpoint-30-input-chain-metrics.json`
- Board: `hardware/checkpoints/checkpoint-30-input-chain.kicad_pcb`
- Front: `hardware/checkpoints/checkpoint-30-input-chain/checkpoint-30-input-chain-front.png`

Checkpoint 31 places the retired U17 safety quad's individual replacements,
U35/U36, and their complete connector-local passive chains beside J5/J6. The
two safety optocouplers, their field-side R/LED/reverse-diode groups and R74/R75
are on B.Cu to preserve the occupied F.Cu anchor area. PLC inputs 0-15 retain
the same chain topology at J7/J8 and the existing firmware-visible bit map.

- Before: `hardware/checkpoints/checkpoint-31-before-individual-safety.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-31-individual-inputs.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-31-individual-inputs/`
- DRC: `hardware/checkpoint-31-individual-inputs-drc.json`
- Metrics: `hardware/checkpoint-31-individual-inputs-metrics.json`

Checkpoint 32 adds four PWM-to-0-10 V channels on the B.Cu analog island
between MOD1 and J25. The supplied reference had a unity-gain follower and
could not reach 10 V from a 3.3 V RP2350 PWM output, so the implementation adds
a 22 k / 10 k feedback network for 3.2x gain. Equivalent op-amp channel
assignments were enumerated; the existing AOUT0-AOUT3 mapping is already the
minimum-airwire permutation for the current placement.

J25 is placed between J24 and J6 and retains the user's hand-moved connector
group. DRC is clean after zone refill. The second filter-capacitor placement
iteration reduced the Analog I/O block's weighted airwire from 403.9 mm to
372.1 mm and removed one crossing.

- Before: `hardware/checkpoints/checkpoint-32-before-analog-outputs.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-32-analog-outputs.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-32-analog-outputs/`
- DRC: `hardware/checkpoint-32-analog-outputs-drc.json`
- Metrics: `hardware/checkpoint-32-analog-outputs-metrics.json`
- Output design: `documentation/analog-outputs.md`

Checkpoint 33 applies the requested pin swap and resistor simplification:

- MOD1 pin 34 now carries SD-card detect and pin 19 carries AOUT0 PWM.
- RN30-RN33 are removed.
- Sixteen individual 0805 resistors replace the four networks.
- The Analog I/O block decreased from 372.1 mm to 360.9 mm weighted airwire.
  The global crossing count is not directly comparable because four
  multi-pin networks became sixteen separate two-pin endpoints.

- Before: `hardware/checkpoints/checkpoint-33-before-simple-resistors.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-33-simple-output-resistors.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-33-simple-output-resistors/`
- DRC: `hardware/checkpoint-33-simple-output-resistors-drc.json`
- Metrics: `hardware/checkpoint-33-simple-output-resistors-metrics.json`

Checkpoint 34 removes the local machine-safety and backlight-power circuitry:

- backlight J2, JP1, Q2, Q3, D6, R6, R7 and C18 removed;
- `BL_PWM` now goes directly to J22 pin 6;
- output-enable gates U14-U16, Q4, R14/R15 and their bypass capacitors removed;
- 74HC595 and AHCT541 output-enable pins tied active;
- E-stop and fault receiver gates U22/U23 removed;
- J6 becomes the HOLD input and new J26 becomes START;
- U35/U36/U39 connect directly to GPIO37/38/39.

Hard output blocking, backlight power switching and current limiting are now
external responsibilities. The uCNC compatibility audit is documented in
`documentation/ucnc-rp2350.md`.

- Before: `hardware/checkpoints/checkpoint-34-before-safety-simplification.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-34-simplified-controls.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-34-simplified-controls/`
- DRC: `hardware/checkpoint-34-simplified-controls-drc.json`
- Metrics: `hardware/checkpoint-34-simplified-controls-metrics.json`

Checkpoint 35 moves the complete 0-10 V signal block back to B.Cu while leaving
the through-hole J25 anchor on the front. The user's hand-chosen filter rotations
were retained. The feedback capacitors and gain resistors were reordered to
match the mirrored bottom-side op-amp pin arrangement, and U38 was moved closer
to J25.

- Analog I/O weighted airwire: 292.858 mm -> 276.674 mm
- Board crossings: 505 -> 487
- Total weighted airwire: 7655.664 mm -> 7640.797 mm
- Placement DRC: zero violations

- Before: `hardware/checkpoints/checkpoint-35-before-analog-opt.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-35-analog-bottom-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-35-analog-bottom-opt/`
- DRC: `hardware/checkpoint-35-analog-bottom-opt-drc.json`
- Metrics: `hardware/checkpoint-35-analog-bottom-opt-metrics.json`

Checkpoint 36 applies the corrected front-side requirement. All 0-10 V parts,
including U37/U38 and the filter/feedback passives, are back on F.Cu. J25 was
already a front-side through-hole anchor.

- Analog I/O weighted airwire: 292.858 mm -> 276.698 mm
- Board crossings: 505 -> 498
- Total weighted airwire: 7655.664 mm -> 7639.504 mm
- Placement DRC: zero violations

- Before: `hardware/checkpoints/checkpoint-35-before-analog-opt.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-36-analog-top-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-36-analog-top-opt/`
- DRC: `hardware/checkpoint-36-analog-top-opt-drc.json`
- Metrics: `hardware/checkpoint-36-analog-top-opt-metrics.json`

Checkpoint 37 is the first connector-side pass after the analog work. It keeps
the RP2350 area fixed and moves the encoder interface toward J13-J15:

- U28 moved from x=53.0 to x=68.0 mm.
- U29 moved from x=73.0 to x=92.0 mm.
- D53, F2, C57 and C58 are now connector-local.
- The four encoder net groups stayed at six crossings while their combined
  airwire fell from 548.6 mm to 233.9 mm.
- The complete Encoders functional block fell from 338.5 mm to 269.5 mm
  weighted airwire.

- Before: `hardware/checkpoints/checkpoint-36-analog-top-opt.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-37-encoder-connector-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-37-encoder-connector-opt/`
- DRC: `hardware/checkpoint-37-encoder-connector-opt-drc.json`
- Metrics: `hardware/checkpoint-37-encoder-connector-opt-metrics.json`

Checkpoint 38 optimizes the J12 general-output connector group without moving
U26/U27 farther toward J12. Placing the ULNs near the connector shortened their
output path but made the OUT16-OUT23 side substantially worse and caused
collisions, so the original ULN compromise positions were retained.

The useful moves are the connector-local support parts:

- R34-R41 use the eight J12 channel positions.
- D45-D52 sit in series with the limit resistors immediately below J12.
- RN12/RN13 are grouped beside the U12 output pins.
- C55/C56 are placed at the U26/U27 DO_COM/GND pins.
- All moved parts are on F.Cu.

Connector-local net length fell from 4316.2 mm to 565.5 mm, with local crossings
falling from 125 to 66. Placement DRC remains clean.

- Before: `hardware/checkpoints/checkpoint-37-encoder-connector-opt.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-38-general-output-connector-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-38-general-output-connector-opt/`
- DRC: `hardware/checkpoint-38-general-output-connector-opt-drc.json`
- Metrics: `hardware/checkpoint-38-general-output-connector-opt-metrics.json`

Checkpoint 39 applies the next connector-side pass to J11/AX3-AX4. U25 remains
at its input/output compromise position. RN10 and RN11 sit directly above U25,
and C54 sits on the opposite side beneath the U25 `+5V` pin.

- J11-group airwire: 847.0 mm -> 279.0 mm
- J11-group crossings: 26 -> 2
- Placement DRC: zero violations

- Before: `hardware/checkpoints/checkpoint-39-before-motion-j11.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-39-motion-j11-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-39-motion-j11-opt/`
- DRC: `hardware/checkpoint-39-motion-j11-opt-drc.json`
- Metrics: `hardware/checkpoint-39-motion-j11-opt-metrics.json`

Checkpoint 40 applies the corresponding support placement to J10/AX0-AX2:

- RN9 is placed on F.Cu between RN17 and RN16.
- C53 is placed on B.Cu beneath U24's `+5V` pin.
- U24 remains at its existing input/output compromise position.
- RN16/RN17, RN8 and J10 remain fixed.

The J10 local group fell from 637.3 mm to 250.9 mm airwire and from 14 to 11
crossings. Placement DRC remains clean.

- Before: `hardware/checkpoints/checkpoint-40-before-motion-j10.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-40-motion-j10-opt.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-40-motion-j10-opt/`
- DRC: `hardware/checkpoint-40-motion-j10-opt-drc.json`
- Metrics: `hardware/checkpoint-40-motion-j10-opt-metrics.json`

Checkpoint 41 places all 16 individual PLC-input pull-ups on F.Cu directly
between each optocoupler collector and U9. R76-R91 use one aligned template per
opto package, mirrored only by the connector pin order. The pull-up bodies are
shifted 3 mm closer to the optocouplers than the earlier input-0 placement.

- PLC-input airwire before: 591.424 mm
- PLC-input airwire after: 591.424 mm
- Board crossings before/after: 585 / 585
- Placement DRC: zero violations

The shared `+3V3` connection adds 15.319 mm to the total weighted measure, while
adding no measurable length or crossings to the PLC signal nets themselves.

- Before: `hardware/checkpoints/checkpoint-41-before-pullups.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-41-input-pullups.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-41-input-pullups/`
- DRC: `hardware/checkpoint-41-input-pullups-drc.json`
- Metrics: `hardware/checkpoint-41-input-pullups-metrics.json`

Checkpoint 43 preserves the user's hand placement of the peripheral AMS1117 U2
at `(198.12, 94.00)` and focuses only on its four local capacitors. It restores
C76 and C13 to the board and groups C10/C76 on the +5 V side and C13/C90 on the
+3V3 side.

- Before: `hardware/checkpoints/checkpoint-43-before-u2-caps.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-43-u2-caps.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-43-u2-caps/`
- Placement decision: `hardware/checkpoint-43-u2-caps.json`
- DRC: `hardware/checkpoint-43-u2-caps-drc.json`
- Metrics: `hardware/checkpoint-43-u2-caps-metrics.json`

The before state had only C10/C90 in the board and still had C76/C13 parked.
After placing the complete local group, the board has 225 in-board footprints,
526 estimated crossings and 6739.516 mm weighted airwire. Placement DRC reports
zero violations and 499 intentionally unrouted connections. Routing remains
stopped pending review of this checkpoint.

Checkpoint 44 places the full-size SD-card passive block around the fixed J19:
five 22 R series resistors, six 10 k pull-ups, FB2, C67 and C68. The parts use
three front-side ranks between MOD1 and J19 rather than being scattered around
the RP2350:

- R50-R54 align with the connector-side SCK/MOSI/MISO/CS/card-detect pins.
- R44-R49 sit on the adjacent pull-up rank.
- FB2/C68/C67 form the local `+3V3_SD` filter and reservoir.

The connector-local block has 408.93 mm raw airwire and 21 analyzed crossings.
Moving its 14 parts in-board raises the whole-board weighted measure from
6739.516 mm to 7003.861 mm because the parked endpoints are now included. The
SD functional block itself contributes 78.766 mm weighted airwire.

Placement DRC reports zero violations and 499 intentionally unrouted
connections. All added SD parts are on F.Cu; routing remains stopped.

- Before: `hardware/checkpoints/checkpoint-44-before-sd-interface.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-44-sd-interface.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-44-sd-interface/`
- Placement decision: `hardware/checkpoint-44-sd-interface.json`
- DRC: `hardware/checkpoint-44-sd-interface-drc.json`
- Metrics: `hardware/checkpoint-44-sd-interface-metrics.json`

Checkpoint 45 completes the remaining main-power passives and power
indications without moving the hand-positioned connectors:

- C7/C8/C16/C17/C77 complete the +5 V bank at U1.
- C88/C89 and C69/C70 complete the U34 ESP regulator input/output decoupling.
- FB1/C15/C14 form the local `+3V3_A` reference filter near MOD1 pin 48.
- R73 pulls up `PWR_GOOD_N` between U1 and GPIO43.
- R4/D4 and R5/D5 are the 5 V and 3.3 V indicators, grouped between MOD1 and
  the two regulators.

The 17-part group measures 919.648 mm raw and 371.025 mm weighted airwire with
15 analyzed crossings. Whole-board weighted airwire is 6977.321 mm with 515
crossings. The increase from 6935.661 mm and 506 crossings is expected because
17 previously parked endpoints are now present.

Placement DRC reports zero violations and 499 intentionally unrouted
connections. All added power/indicator parts are on F.Cu. Routing remains
stopped.

- Before: `hardware/checkpoints/checkpoint-45-before-power-completion.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-45-power-completion.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-45-power-completion/`
- Placement decision: `hardware/checkpoint-45-power-completion.json`
- DRC: `hardware/checkpoint-45-power-completion-drc.json`
- Metrics: `hardware/checkpoint-45-power-completion-metrics.json`

Checkpoint 46 replaces the second encoder buffer U29 and its C58 bypass with
the requested divider for the sole remaining channel:

- R110, 5.1 k 0805: `ENC2_Z_5V` to `ENC2_Z_3V3`.
- R111, 10 k 0805: `ENC2_Z_3V3` to GND.
- U28 remains the eight-channel buffer for the other encoder signals.

At 5 V input the divider produces approximately 3.31 V. U29 and C58 are removed
from the schematic, netlist, PCB and BOM. R110/R111 are placed together above
J15 on F.Cu.

Placement DRC reports zero violations and 499 intentionally unrouted
connections. ERC reports no errors and 33 existing library-symbol mismatch
warnings. Whole-board weighted airwire is 6996.948 mm with 522 estimated
crossings; the Encoders block is 267.601 mm.

- Before: `hardware/checkpoints/checkpoint-46-before-u29-divider.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-46-u29-divider.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-46-u29-divider/`
- DRC: `hardware/checkpoint-46-u29-divider-drc.json`
- ERC: `hardware/checkpoint-46-u29-divider-erc.json`
- Metrics: `hardware/checkpoint-46-u29-divider-metrics.json`

Checkpoint 47 places the eight 74HC shift-register bypass capacitors:

- C22-C25 are aligned with the U6-U9 +3V3 pins.
- C26-C29 are aligned with U10-U13.
- All eight 0805 parts are on F.Cu, directly right of their IC courtyards, with
  the GND pad positioned for a short bottom-plane via.

All eight ICs now pass the local-decoupling audit. The input-register cap loops
measure 7.38 mm; the output-register loops measure 9.92 mm.

Whole-board weighted airwire changes from 6996.948 mm to 6999.800 mm while
estimated crossings fall from 522 to 513 and weighted crossings from 634.55 to
620.55. Placement DRC reports zero violations and 499 intentionally unrouted
connections.

- Before: `hardware/checkpoints/checkpoint-47-before-logic-decoupling.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-47-logic-decoupling.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-47-logic-decoupling/`
- Placement decision: `hardware/checkpoint-47-logic-decoupling.json`
- DRC: `hardware/checkpoint-47-logic-decoupling-drc.json`
- Metrics: `hardware/checkpoint-47-logic-decoupling-metrics.json`

Checkpoint 48 places the default passive LCD interface:

- J22 at `(170.50, 25.00)`, rotation 270 degrees.
- RN27 and RN26 below J22 at `(145.50, 31.00)` and `(153.50, 31.00)`,
  rotation 90 degrees.
- The isolated 4x330 ohm network pairs are reordered as an equivalent package
  pin swap so their outputs follow J22's CLK/D2/D1/D0 order.
- The RP2350 HSTX mapping and LVDS net names are unchanged.

Placement DRC is clean with 499 intentionally unrouted connections.

- Before: `hardware/checkpoints/checkpoint-48-before-lvds-interface.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-48-lvds-interface.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-48-lvds-interface/`
- DRC: `hardware/checkpoint-48-lvds-interface-drc.json`
- Metrics: `hardware/checkpoint-48-lvds-interface-metrics.json`

Checkpoint 49 places the remaining functional resistor groups:

- R10-R13 are individual 10 k parts in the open row between the input and
  output shift registers.
- RN20/RN21 and RN22/RN24 stay as keyboard-channel arrays on the J16 side.
- R55-R58 remain individual 10 k ESP pull-ups beside J20.
- RN6/RN7 remain 4x10 k expansion-input networks below U7.
- RN28/RN29 are placed as DNP HDMI alternate links beside J23.

Only F3, J9, J17 and J18 remain outside the board. Placement DRC reports zero
violations and 499 intentionally unrouted connections. The added resistor
endpoints increase the whole-board airwire measure to 9423.292 mm and 813
crossings; these totals include all previously parked resistor endpoints.

- Before: `hardware/checkpoints/checkpoint-49-before-remaining-resistors.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-49-remaining-resistors.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-49-remaining-resistors/`
- DRC: `hardware/checkpoint-49-remaining-resistors-drc.json`
- Metrics: `hardware/checkpoint-49-remaining-resistors-metrics.json`

Checkpoint 50 splits the spare expansion byte across two connectors around U7
and rebalances the J16 resistor placement:

- J9 carries GND, +3V3 and EXP_IN0-3.
- J27 carries GND, +3V3 and EXP_IN4-7.
- The two 1x6 headers are on F.Cu at `(64.0, 61.0)` and `(77.0, 61.0)`.
- RN6/RN7 remain between the headers and U7.
- J16 remains above the bottom edge on B.Cu. RN20/RN21 stay on its left for
  KOUT, while RN22/RN24 move to its right for KIN.

Weighted airwire improves from 9423.292 mm to 9284.016 mm, crossings fall from
813 to 798, and weighted crossings fall from 1053.05 to 1038.05. Placement DRC
reports zero violations and 499 intentionally unrouted connections. ERC has no
errors and the same 33 library-symbol mismatch warnings.

- Before: `hardware/checkpoints/checkpoint-50-before-j9-j16-rework.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-50-j9-j16-rework.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-50-j9-j16-rework/`
- DRC: `hardware/checkpoint-50-j9-j16-rework-drc.json`
- ERC: `hardware/checkpoint-50-j9-j16-rework-erc.json`
- Metrics: `hardware/checkpoint-50-j9-j16-rework-metrics.json`

Checkpoint 51 applies the equivalent pin maps requested for RN20, RN21, RN22
and RN24. No footprint, rotation or side was changed:

- RN20 uses alternating terminal orientations across its four elements.
- RN21, RN22 and RN24 reverse each isolated element's terminals.
- All related nets retain their logical KIN0-7 and KOUT0-7 assignments.
- All four resistor networks remain on F.Cu.

The local keyboard-network estimate drops from 98 to 30 crossings and from
428.968 mm to 394.071 mm. With the DNP HDMI arrays retained in their approved
positions, whole-board weighted airwire drops from 9284.016 mm to 9196.965 mm,
crossings from 798 to 697, and weighted crossings from 1038.05 to 940.05.
Placement DRC reports zero violations and 499 intentionally unrouted connections.

- Before: `hardware/checkpoints/checkpoint-51-before-keyboard-pin-swaps.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-51-keyboard-pin-swaps.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-51-keyboard-pin-swaps/`
- Optimization result: `tmp/keyboard-pin-swaps.json`
- DRC: `hardware/checkpoint-51-keyboard-pin-swaps-drc.json`
- Metrics: `hardware/checkpoint-51-keyboard-pin-swaps-metrics.json`

Checkpoint 53 performs the layout cleanup requested before routing:

- All in-board ICs, passives, connectors and MOD1 are snapped to a common
  0.5 mm grid with 90-degree rotations.
- The four M3 mounting holes remain at their fixed mechanical positions.
- All 283 non-hole footprints audit as on-grid with zero position or rotation
  errors.
- PLC field channels are renumbered 1-16 while retaining their physical order.
  Firmware bit indices remain 0-15; input channel `n` maps to bit `n-1`.
- The spare expansion byte remains split between J9 and J27.

Grid alignment changes weighted airwire from 9196.965 mm to 9203.198 mm and
crossings from 697 to 777. This small connectivity cost is accepted for the
uniform hand-placement grid. Placement DRC reports zero violations and 499
intentionally unrouted connections. ERC retains 33 existing library-symbol
mismatch warnings and no errors.

- Before: `hardware/checkpoints/checkpoint-52-before-grid-input-numbering.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-53-grid.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-53-grid/`
- Grid audit: `hardware/checkpoint-53-grid-audit.json`
- DRC: `hardware/checkpoint-53-grid-drc.json`
- ERC: `hardware/checkpoint-53-grid-erc.json`
- Metrics: `hardware/checkpoint-53-grid-metrics.json`

Checkpoint 55 repackages the motion and PLC connectors:

- J10, J11, J28, J29 and J30 are one 1x4 Phoenix connector per axis, ordered
  `EN/STEP/DIR/GND`.
- J31 is a separate 2-pin `MOTION14/AUX` and GND connector.
- J7 and J8 are two 1x16 Phoenix connectors with alternating input and
  isolated common pins.
- J12 remains the eight-channel general-output connector.
- The complete board remains on the 0.5 mm placement grid.

Weighted airwire rises from 9203.198 mm to 10022.697 mm and crossings from 777
to 929 because the paired connectors create additional endpoints. Placement
DRC reports zero violations and 499 intentionally unrouted connections.

- Before: `hardware/checkpoints/checkpoint-54-before-paired-connectors.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-55-paired-connectors.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-55-paired-connectors/`
- DRC: `hardware/checkpoint-55-paired-connectors-drc.json`
- ERC: `hardware/checkpoint-55-paired-connectors-erc.json`
- Metrics: `hardware/checkpoint-55-paired-connectors-metrics.json`

Checkpoint 57 validates the user-compacted board and untangles the PLC inputs:

- The compacted placement was re-audited before any new optimization. Stale
  zone fill was refreshed, six stranded GND vias were removed, the Wi-Fi RST
  pull-up was moved clear of SW2, and the H2 reference was moved inside the
  board edge.
- All 289 non-hole footprints are on the 0.5 mm grid with 90-degree rotations.
  PCB DRC reports zero violations and 499 expected unrouted connections.
- J7 positions 1-8 now feed logical `FIELD_IN9-16`; J8 positions 1-8 feed
  logical `FIELD_IN1-8`. This sorted physical fanout changes the connector-to-
  chain estimate from 64 crossings and 806.017 mm to zero crossings and
  445.552 mm.
- U8/U9 data-pin assignments now follow the nearest optocoupler outputs. This
  changes the optocoupler-to-74HC165 estimate from 44 crossings and 988.924 mm
  to zero crossings and 981.102 mm.
- The complete firmware permutation is recorded in `documentation/io-bit-map.md`.
  Firmware mappings are intentionally changed because the user confirmed that
  input channel reassignment is software-controlled.
- Whole-board weighted airwire falls from 9860.857 mm to 9492.582 mm, estimated
  crossings from 1061 to 937, and weighted crossings from 1329.2 to 1204.2.
  The PLC-input block falls from 1485.234 mm to 1124.769 mm.

- Before: `hardware/checkpoints/checkpoint-57-before-input-untangle.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-57-input-untangle.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-57-input-untangle/`
- DRC: `hardware/checkpoint-57-input-untangle-drc.json`
- ERC: `hardware/checkpoint-57-input-untangle-erc.json`
- Metrics: `hardware/checkpoint-57-input-untangle-metrics.json`

Checkpoint 58 completed the compacted 196.5 x 150 mm tidy-up:

- The outline is reduced from 210 x 150 mm to 196.5 x 150 mm, a 6.4% board-area
  reduction. The rightmost courtyards retain at least 1.27 mm to the new edge.
- The 150 mm height is retained because the bottom connector row and mounting
  holes occupy a 149.86 mm minimum envelope at the selected 1 mm clearance.
- All bottom-edge connectors are aligned at `y = 142.0 mm`.
- The user-moved left-center block is returned to the 0.5 mm grid; all 293
  non-hole footprints pass the grid audit.
- Previously parked C71, C72, R59 and R60 are now placed beside the HDMI
  connector and its +5 V support network. No footprints remain outside the
  board.
- PCB DRC reports zero violations and 499 expected unrouted connections.

- Board: `hardware/checkpoints/checkpoint-58-resized-tidy.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-58-resized-tidy/`
- DRC: `hardware/checkpoint-58-resized-tidy-drc.json`
- Metrics: `hardware/checkpoint-58-resized-tidy-metrics.json`
- Grid audit: `hardware/checkpoint-58-resized-tidy-grid-audit.json`
- Envelope audit: `hardware/checkpoint-58-resized-tidy-envelope.json`

Checkpoint 59 sets the release outline to the requested 200 x 150 mm:

- The outline is widened by 3.5 mm on the right edge to provide additional
  mechanical margin around the HDMI and SD connectors.
- The component placement, firmware input permutation and two-layer stackup
  remain unchanged from checkpoint 58.

Checkpoint 60 adds configurable isolated wetting for dry contacts:

- U40 is a 1 W Traco `TMA-0505S`, providing an isolated 5 V, 200 mA field rail;
  F4 limits its primary input current.
- C103 bulk-decouples the primary side and C105 bulk-decouples the isolated
  side; redundant 100 nF bypasses were removed.
- JP2-JP10 on B.Cu select external 24 V or internal 5 V operation independently
  for the J7, J8 and dedicated safety banks.
- Optocoupler cathodes and reverse-protection diodes now return through
  `FIELD_RETURN0`, `FIELD_RETURN1` and `FIELD_SAFETY_RETURN`, allowing the
  selector to change the wetting topology without connecting field circuits to
  motherboard GND.

Checkpoint 61 tidies the isolated-input hardware:

- U40 and F4 are on F.Cu in the left input area.
- C103 remains as the primary 10 uF bulk capacitor and C105 as the isolated
  10 uF bulk capacitor. The redundant C104/C106 100 nF parts are removed.
- JP2-JP10 remain bottom-side open solder pads but are grouped into three clear
  bank sets with mirrored B.SilkS configuration labels.
- PCB DRC is clean with 499 expected unrouted connections; the 0.5 mm grid audit
  passes and ERC contains only the existing 33 library-symbol warnings.

Checkpoint 63 replaces the isolated 5 V wetting rail with 12 V and simplifies
mode selection:

- U40 changes to a Traco `TBA2-0512`, 5 V input and isolated 12 V/2 W output.
- D56 is a series SS54 Schottky diode preventing field-rail backfeed into U40.
- F4 becomes 750 mA; C105 moves to the protected 12 V rail and uses a 100 V
  1206 capacitor.
- JP2-JP4 are single 3-pad selectors for J7, J8 and the safety bank:
  1-2 is external 24 V, 2-3 is isolated-12 V `CONTACT`.
- The existing 2.2 k input resistors remain. They produce approximately
  9.5 mA at 24 V and 3.9-4.5 mA at 12 V after the protection diode.

Checkpoint 64 preserves the user-moved power/encoder area and changes the input
mode selectors to removable hardware:

- JP2-JP4 now use standard 2.54 mm, 1x3 through-hole pin headers with one
  removable shunt per input bank.
- U40, D56, F4 and the two bulk capacitors remain in the relocated bottom-left
  power area beside the encoder interface.
- U40 is snapped to the 0.5 mm grid at `(39.00, 130.50)`.
- No SMT footprints remain on B.Cu, leaving the bottom copper primarily
  available for the ground plane.

Checkpoint 65 makes the shift-register output controls PIO-ready without moving
components:

- The 74HC595 controls are now `GPIO20 = DATA`, `GPIO21 = CLK` and
  `GPIO22 = LATCH`, satisfying the stock uCNC RP2350 PIO requirement for three
  consecutive pins in that exact order.
- The 74HC165 load and return move to `GPIO24` and `GPIO35` respectively.
- All 305 footprint positions and rotations are unchanged. Only five MOD1 pad
  nets and the affected ground-zone fill were updated.
- The logical 32-bit input/output maps and all 165/595 chain connections are
  unchanged. The standard bit-banged `shift_register` remains the complete
  runtime path; the stock 595 PIO path is output-only until input scanning gets
  separate/custom PIO support.
- Whole-board estimated airwire length changes from 9870.937 mm to 9874.034 mm
  (+3.097 mm) and weighted airwire from 9736.864 mm to 9741.509 mm
  (+4.645 mm). Estimated crossings fall from 897 to 896 and weighted crossings
  from 1186.4 to 1181.9. The tiny length cost buys the required PIO pin order.
- Verification reports no net-contract failures. PCB DRC has no errors and one
  unrelated silkscreen warning between D53 and the F2 reference. The board
  remains completely unrouted with 499 expected connections.

- Board: `hardware/checkpoints/checkpoint-65-shift-pio-ready.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-65-shift-pio-ready/`
- Metrics: `hardware/checkpoints/checkpoint-65-shift-pio-ready/metrics.json`

Checkpoint 66 snaps every unlocked footprint to KiCad 10's active PCB grid:

- The active grid was read from the PCB Editor settings as index 15,
  `0.5 mm x 0.5 mm`, with grid origin `(0, 0)`.
- Seven unlocked footprints moved by at most `0.197 mm`: H2, H4, J18, J4,
  JP2, JP3 and JP4. The other 298 footprints were already aligned.
- All 305 footprint rotations and relative pad offsets are unchanged. No locked
  footprints moved, and no locked footprints were present.
- Tracks and vias remain at zero, all seven board-level drawings are unchanged,
  and the ground-zone outline is unchanged. DRC refilled the existing zone.
- PCB DRC reports zero errors, the existing unrelated D53/F2 silkscreen warning,
  and 499 expected unrouted connections.

- Board: `hardware/checkpoints/checkpoint-66-active-grid-snap.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-66-active-grid-snap/`
- Snap report: `hardware/checkpoints/checkpoint-66-active-grid-snap/snap-report.json`
- Constraint check: `hardware/checkpoints/checkpoint-66-active-grid-snap/constraint-check.json`
- DRC: `hardware/checkpoints/checkpoint-66-active-grid-snap/drc.json`

Checkpoint 67 normalizes connectors by their native pitch and aligns the metric
connector rows by courtyard:

- The 3.5 mm Phoenix connectors use a 0.25 mm grid, which aligns both their
  individual pads and their mechanical centers.
- The 2.54 mm headers and selector jumpers use a 0.635 mm grid.
- Remaining connector families keep a 0.5 mm anchor grid.
- All bottom-edge 3.5 mm connector courtyards now end at `Y = 148.545 mm`.
- All top-row 3.5 mm connector courtyards now begin at `Y = 3.205 mm`.
- Twenty-four connector footprints moved by at most 0.75 mm. Rotations,
  relative pad positions, board drawings, track/via counts and zone outlines
  remain unchanged.
- Weighted airwire changes from 9420.005 mm to 9430.654 mm (+10.649 mm);
  estimated crossings remain unchanged at 806.
- PCB DRC reports zero errors, the existing D53/F2 silkscreen warning and 499
  expected unrouted connections.

- Board: `hardware/checkpoints/checkpoint-67-connector-grid-tidy.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-67-connector-grid-tidy/`
- Connector report: `hardware/checkpoints/checkpoint-67-connector-grid-tidy/connector-report.json`
- Constraint check: `hardware/checkpoints/checkpoint-67-connector-grid-tidy/constraint-check.json`
- DRC: `hardware/checkpoints/checkpoint-67-connector-grid-tidy/drc.json`

Checkpoint 68 locally untangles RN12, RN13, RN20 and RN21 while treating the
existing routed copper as fixed:

- RN12 moves to `(58.5, 38.5)` at `-90 degrees`.
- RN13 moves to `(47.0, 35.5)` at `-90 degrees`.
- RN20 moves to `(32.0, 43.5)` at `0 degrees`.
- RN21 moves to `(40.0, 43.0)` at `90 degrees`.
- The local output/keyboard-array estimate falls from 48 crossings and
  379.440 mm to 22 crossings and 342.688 mm.
- Whole-board weighted airwire falls from 9316.985 mm to 9280.233 mm,
  crossings from 792 to 766, and weighted crossings from 1095.4 to 1069.4.
- Pad net assignments are unchanged. All 112 existing tracks/vias, board
  drawings and zone outlines remain unchanged.
- PCB DRC reports zero errors, the existing D53/F2 silkscreen warning and 499
  expected unrouted connections.

- Before: `hardware/motherboard-backups/motherboard-before-rn-untangle-2026-10-26_130827.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-68-rn-untangle.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-68-rn-untangle/`
- Placement search: `hardware/checkpoints/checkpoint-68-rn-untangle/placement-search.json`
- Constraint check: `hardware/checkpoints/checkpoint-68-rn-untangle/constraint-check.json`
- DRC: `hardware/checkpoints/checkpoint-68-rn-untangle/drc.json`

Checkpoint 69 supersedes checkpoint 68 after the user requested pin-only changes:

- All footprint positions, rotations and layers are restored/preserved exactly;
  no RN or other footprint moved for this checkpoint.
- RN12 reverses its four physical elements: pins 1-4 carry OUT19, OUT18,
  OUT17 and OUT16; pins 5-8 remain GND.
- RN13 similarly carries OUT23, OUT22, OUT21 and OUT20 on pins 1-4.
- RN20 maps pins 1-8 to KOUT1, KOUT2, KOUT3, KOUT0, OUT24, OUT27, OUT26,
  OUT25.
- RN21 changes only element 3 terminal orientation: pin 3 is OUT30 and pin 6
  is KOUT6.
- Eighteen RN pad-net assignments changed in total. The logical OUT16-OUT31
  and KOUT0-KOUT7 assignments remain unchanged.
- The fixed-position estimate falls from 34 crossings and 233.510 mm to
  16 crossings and 222.433 mm.
- Whole-board weighted airwire falls from 9316.985 mm to 9305.935 mm,
  crossings from 792 to 775, and weighted crossings from 1095.4 to 1078.9.
- All 112 existing tracks/vias, board drawings and zone outlines are unchanged.
  PCB DRC reports zero errors, the existing D53/F2 silkscreen warning and 499
  expected unrouted connections. ERC has no errors and retains its 33 existing
  library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-rn-pin-swaps-2026-10-26_133810.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-69-rn-pin-only.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-69-rn-pin-only/`
- Pin search: `hardware/checkpoints/checkpoint-69-rn-pin-only/pin-search.json`
- Constraint check: `hardware/checkpoints/checkpoint-69-rn-pin-only/constraint-check.json`
- DRC: `hardware/checkpoints/checkpoint-69-rn-pin-only/drc.json`

Checkpoint 70 applies the next pin-only permutation while keeping every
footprint fixed:

- RN8-RN11 use element/terminal permutations that reduce the local estimate
  from 13 crossings and 123.895 mm to zero crossings and 110.310 mm.
- RN21 remains in the requested state with pin 3 = OUT30 and pin 6 = KOUT6.
- RN20 applies the requested element cycle. Pins 1-8 are now KOUT0-KOUT3 on
  the input side and OUT24-OUT27 on the output side.
- No footprint position, rotation, layer or pad geometry changed. Existing
  tracks/vias, board drawings and zone outlines are unchanged.
- Whole-board weighted airwire falls from 9316.763 mm to 9303.785 mm,
  crossings from 783 to 769, and weighted crossings from 1086.4 to 1072.4.
- The explicit RN20 remap conflicts with its six existing routed nets. DRC
  therefore reports 13 routing errors around RN20 plus the existing D53/F2
  silkscreen warning. These are pending reroutes, not placement errors.
- ERC has no errors and retains the existing 33 library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-rn8-20-pin-swaps-2026-10-26_135837.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-70-rn-pin-remap-pending-reroute.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-70-rn-pin-remap-pending-reroute/`
- RN8-RN11 search: `hardware/checkpoints/checkpoint-70-rn-pin-remap-pending-reroute/output-pulldown-search.json`
- Constraint check: `hardware/checkpoints/checkpoint-70-rn-pin-remap-pending-reroute/constraint-check.json`
- DRC: `hardware/checkpoints/checkpoint-70-rn-pin-remap-pending-reroute/drc.json`

Checkpoint 71 expands the general low-side outputs from 8 to 16:

- U26 uses all seven channels for OUT16-OUT22 -> DO0-DO6.
- U27 uses all seven channels for OUT23-OUT29 -> DO7-DO13.
- OUT24-OUT29 remain connected to their keyboard nets while also driving the
  second ULN package.
- Q6 and Q7 are BSS138 low-side switches for OUT30-OUT31 -> DO14-DO15, using
  the same 100 ohm gate resistor and 100 k pull-down pattern as Q5.
- J32 is an 8-pin Phoenix 3.5 mm connector immediately to the right of J12.
  It exposes DO8-DO15; `DO_COM` and `GND` remain shared through J12.
- No existing footprint changed position or rotation. Seven new footprints
  were added: J32, Q6, Q7, R114, R115, R116 and R117.
- Schematic and PCB contract verification passes with 317 components and 337
  nets.
- DRC currently reports 22 errors from old routed segments crossing the new
  RN20/U26/U27 pad assignments. The new J32 and MOSFET gate components add no
  placement or copper-clearance errors. ERC has no errors and retains 33
  library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-expanded-uln-outputs-2026-10-26_142407.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-71-16-open-collector-outputs.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-71-16-open-collector-outputs/`
- DRC: `hardware/checkpoints/checkpoint-71-16-open-collector-outputs/drc.json`

Checkpoint 72 unifies the field connectors and completes the output remap:

- All Phoenix field connectors now use only 2-, 4-, 5- or 8-position bodies.
- J7/J8 are split across J7/J34 and J8/J35 respectively.
- J12 is now an 8-position DO0-DO7 connector; J33 carries DO_COM/GND.
- J24 initially used an 8-position analog-input connector in this checkpoint;
  checkpoint 73 replaces it with the final 5-position pinout.
- Output bit0 is AUX through Q5; bits1-15 drive MOTION0-MOTION14.
- DO8-DO15 now have LED indicators D57-D64 with series resistors R118-R125.
- The schematic and PCB contract check passes with 336 components and 344 nets.
- DRC has no placement, courtyard, hole or board-edge errors. Its 45 errors are
  all invalidated copper segments from the RN20/U26/U27/output-bit changes.

- Before: `hardware/motherboard-backups/motherboard-before-connector-unification-2026-10-26_150317.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-72-unified-connectors.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-72-unified-connectors/`
- DRC: `hardware/checkpoints/checkpoint-72-unified-connectors/drc.json`

Checkpoint 73 finalizes J24 as the 5-position analog-input connector:

- J24 pins are `AI0 / GND / AI1 / GND / AI2`.
- The connector anchor remains `(118.75, 145.0)` with zero rotation.
- This keeps the field-terminal inventory at 2, 4, 5 and 8 positions while
  avoiding two unnecessary positions on the analog input.
- The replacement introduces no placement or new-net DRC error. Current DRC
  remains at the 45 routing errors from previously invalidated copper, plus 19
  warnings.

- Board: `hardware/checkpoints/checkpoint-73-j24-five-pin.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-73-j24-five-pin/`
- DRC: `hardware/checkpoints/checkpoint-73-j24-five-pin/drc.json`

Checkpoint 74 normalizes the complete general-output fanout:

- U26 channels 1-7 connect OUT16-OUT22 to DO0-DO6 in order.
- U27 channels 1-7 connect OUT23-OUT29 to DO7-DO13 in order.
- Q6/Q7 continue to provide DO14/DO15 from OUT30/OUT31.
- DO8-DO15 indicators D57-D64 and resistors R118-R125 are placed directly
  below J32 in the same orientation and spacing as the DO0-DO7 row.
- Whole-board weighted airwire falls from 10786.636 mm to 10125.606 mm;
  estimated crossings fall from 1209 to 942.
- Schematic/netlist contract verification passes with 336 components and 344
  nets.
- No placement, courtyard, hole or board-edge errors remain. DRC reports 77
  errors from invalidated routed copper plus 26 silkscreen/track warnings.

- Before: `hardware/motherboard-backups/motherboard-before-output-order-tidy-2026-10-26_154246.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-74-output-order.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-74-output-order/`
- DRC: `hardware/checkpoints/checkpoint-74-output-order/drc.json`

Checkpoint 75 mirrors both ULN packages to remove the general-output fanout
crossings:

- U26 channels 1-7 connect OUT22-OUT16 to DO6-DO0. Each physical channel keeps
  its logical `OUTn -> DOn` pair.
- U27 channels 1-7 connect OUT29-OUT23 to DO13-DO7.
- DO8-DO15 LED/resistor pairs are aligned with J32 pins and retain the same
  spacing and orientation as DO0-DO7.
- Whole-board weighted airwire falls from 10125.606 mm to 10086.459 mm;
  estimated crossings fall from 942 to 845.
- The schematic/netlist contract passes with 336 components and 344 nets.
- No footprint placement, courtyard, hole or board-edge errors remain. DRC
  reports 77 invalidated-copper errors and 26 silkscreen/track warnings; ERC
  has no errors and retains 33 library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-output-order-tidy-2026-10-26_154246.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-75-uln-mirrored.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-75-uln-mirrored/`
- DRC: `hardware/checkpoints/checkpoint-75-uln-mirrored/drc.json`

Checkpoint 76 swaps RN21 pins 3 and 6:

- RN21 pin 3 is now KOUT6 and pin 6 is now OUT30.
- The footprint position and rotation are unchanged; all other RN21 terminals
  retain their connections.
- Schematic, netlist and PCB verification pass with no contract failures.
- PCB DRC drops from 77 to 23 routing errors, with 23 silkscreen/track
  warnings. ERC has no errors and retains 33 library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-rn21-pin3-6-swap-2026-10-26_155800.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-76-rn21-pin-swap.kicad_pcb`
- DRC: `hardware/checkpoints/checkpoint-76-rn21-pin-swap/drc.json`

Checkpoint 77 completes the U27 input pull-down network:

- RN30 provides 10 k pull-downs for OUT24-OUT27.
- RN31 provides 10 k pull-downs for OUT28 and OUT29; its other two elements
  are spare.
- Together with RN13's OUT23 pull-down, every U27 input now has a defined
  level while the 74HC595 outputs are tri-stated.
- RN30/RN31 are on F.Cu between the LED rows and their respective U27 inputs.
- Netlist validation passes with 338 components and 344 nets.
- DRC remains at 23 invalidated-copper errors and 24 silkscreen/track
  warnings, with no placement, courtyard, hole or edge errors. ERC has no
  errors and 35 existing library-symbol warnings.

- Before: `hardware/motherboard-backups/motherboard-before-u27-pulldowns-2026-10-26_160655.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-77-u27-pulldowns.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-77-u27-pulldowns/`
- DRC: `hardware/checkpoints/checkpoint-77-u27-pulldowns/drc.json`

Checkpoint 78 separates U26/U27 pull-down ownership and normalizes motion
connector ordering:

- RN13 now covers only OUT20-OUT22; its fourth element is spare.
- RN30 covers OUT23-OUT26 and RN31 covers OUT27-OUT29, so U27 no longer uses
  a common pull-down with U26.
- J10-J30 use consistent `EN/STEP/DIR/GND` pin order.
- `J10=AX0`, `J11=AX1`, `J28=AX2`, `J29=AX3`, `J30=AX4`, with
  `MOTION0..MOTION14` assigned in consecutive groups.
- The alternate strict left-to-right axis ordering produced 89 local
  crossings; the selected connector assignment produces 19.
- Netlist validation passes with 338 components and 344 nets.
- DRC reports 29 invalidated-copper errors and 24 silkscreen/track warnings,
  with no placement/courtyard/hole/edge errors.

- Before: `hardware/motherboard-backups/motherboard-before-u27-rn-and-motion-order-2026-10-26_161555.kicad_pcb`
- Board: `hardware/checkpoints/checkpoint-78-u27-rn-motion-order.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-78-u27-rn-motion-order/`
- DRC: `hardware/checkpoints/checkpoint-78-u27-rn-motion-order/drc.json`

Checkpoint 79 re-runs pin-map optimization against the current, deliberately
off-board motion-connector anchors:

- RN30 element order is now OUT24/OUT26/OUT25/OUT23 and RN31 is
  OUT29/OUT28/OUT27/spare. All footprints retain their positions and rotations.
- The isolated resistor element and terminal swaps reduce the local RN30/RN31
  estimate from 10 crossings and 38.903 mm to 3 crossings and 38.143 mm.
- The motion-connector allocation remains `J10=AX0` through `J30=AX4`. With
  `EN/STEP/DIR` fixed to pins 1/2/3, this is already the best axis order.
- Equivalent terminal flips on RN16-RN19 reduce the combined
  buffer-to-resistor-to-connector ratline estimate from 42 crossings and
  1051.891 mm to 34 crossings and 1075.066 mm. Crossings are prioritized over
  length, and all `BUFYn -> MOTIONn` logical pairs remain unchanged.
- Across the whole board, estimated crossings fall from 857 to 835 and
  weighted crossings from 1161.9 to 1139.9. Weighted airwire rises slightly
  from 10469.779 mm to 10484.058 mm because the crossing-first objective accepts
  short detours; peak congestion also falls from 0.100708 to 0.099921.
- Stale spare-pad assignments on RN13 and RN19 are cleared, eliminating the
  unintended OUT20 and MOTION12 duplicates.

- Board: `hardware/checkpoints/checkpoint-79-rn-motion-swaps.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-79-rn-motion-swaps/`
- Optimization report: `hardware/checkpoints/checkpoint-79-rn-motion-swaps/optimization.json`
- DRC: `hardware/checkpoints/checkpoint-79-rn-motion-swaps/drc.json`
- ERC: `hardware/checkpoints/checkpoint-79-rn-motion-swaps/erc.json`

Checkpoint 80 replaces the checkpoint-79 motion mapping with the requested
linear physical ordering:

- U24/U25 output pad order is matched monotonically to the upper pad rows of
  RN16-RN19.
- RN16-RN19 lower pad order feeds the physical connector pin order without
  reversing pairs inside the chain. RN16 element 3 is the single spare.
- The 15 active physical chains, from left to right, are BUFY15, 14, 13, 12,
  11, 10, 8, 9, 6, 7, 4, 5, 2, 3, 1.
- A geometric linear-order check reports 15 active chains, zero crossings and
  1020.326 mm of total buffer-to-RN-to-connector path length.
- Whole-board crossings fall from 835 at checkpoint 79 to 797; weighted
  crossings fall from 1139.9 to 1101.9 and weighted airwire from 10484.058 mm
  to 10430.515 mm.
- PCB DRC drops to 11 invalidated-copper errors and 24 silkscreen warnings,
  with no placement, courtyard, hole or board-edge errors. ERC has no errors.
- This remaps firmware-facing OUT/MOTION bits and supersedes the checkpoint-79
  `BUFY n -> MOTION n` assumption.

- Board: `hardware/checkpoints/checkpoint-80-linear-motion-chain.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-80-linear-motion-chain/`
- Linear-order report: `hardware/checkpoints/checkpoint-80-linear-motion-chain/motion-linear-order.json`
- DRC: `hardware/checkpoints/checkpoint-80-linear-motion-chain/drc.json`
- ERC: `hardware/checkpoints/checkpoint-80-linear-motion-chain/erc.json`

Checkpoint 81 uses the remaining U24 channel as the AUX MOSFET driver:

- `OUT0` enters U24 pin 8.
- U24 pin 12 (`BUFY0`) replaces the direct `OUT0` connection at R112 pin 1.
- R112, R113 and the BSS138 Q5 gate/drain circuit remain unchanged.
- U24's sixteen outputs are now fully used: BUFY0 for AUX and BUFY1-BUFY15 for
  the fifteen monotonic motion channels.
- Current user connector positions remain unchanged and preserve the
  crossing-free motion ordering.

- Board: `hardware/checkpoints/checkpoint-81-aux-buffer-driver.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-81-aux-buffer-driver/`
- DRC: `hardware/checkpoints/checkpoint-81-aux-buffer-driver/drc.json`
- ERC: `hardware/checkpoints/checkpoint-81-aux-buffer-driver/erc.json`

Checkpoint 82 removes R112 and uses the already-present RN16 spare element:

- U24 pin 12 (`BUFY0`) now connects directly to RN16 pin 3.
- RN16 pin 6 drives `AUX_GATE`; the 100 k pulldown R113 remains.
- R112 is removed from the schematic, PCB and PCB placement generator.
- All four RN16 elements are now used, so there is no spare motion resistor.
- The linear motion chain remains at 15 active paths and zero crossings.
- PCB DRC drops to 8 stale-copper errors and 32 warnings, with no placement,
  courtyard, hole or board-edge errors. ERC has no errors.

- Board: `hardware/checkpoints/checkpoint-82-rn16-aux-driver.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-82-rn16-aux-driver/`
- Motion report: `hardware/checkpoints/checkpoint-82-rn16-aux-driver/motion-linear-order.json`
- DRC: `hardware/checkpoints/checkpoint-82-rn16-aux-driver/drc.json`
- ERC: `hardware/checkpoints/checkpoint-82-rn16-aux-driver/erc.json`

Checkpoint 83 installs routing classes and decoupling-ground returns:

- Project netclasses initially cover `Default`, `Power`, `FieldPower`,
  `Ground`, `DigitalDiffPair` and `Analog`.
- Power is 0.8 mm, field power and ground are 0.5 mm, analog is 0.25 mm and
  differential pairs are defined at 0.2 mm width / 0.2 mm gap.
- Thirty-one 100 nF decoupling capacitors receive a 0.6/0.3 mm GND via on the
  side away from the supply pad, joined by a 0.5 mm F.Cu stub.
- The added vias reduce unresolved DRC connections from 470 to 439.
- Existing 0.2 mm power and wide-clearance routing now produces expected
  netclass clearance findings that must be corrected during routing cleanup.

- Board: `hardware/checkpoints/checkpoint-83-netclasses-ground-vias.kicad_pcb`
- Project rules: `hardware/checkpoints/checkpoint-83-netclasses-ground-vias/motherboard.kicad_pro`
- Front/back: `hardware/checkpoints/checkpoint-83-netclasses-ground-vias/`
- Via report: `hardware/checkpoints/checkpoint-83-netclasses-ground-vias/decoupling-ground-vias.json`
- DRC: `hardware/checkpoints/checkpoint-83-netclasses-ground-vias/drc.json`

Checkpoint 84 applies the netclass widths to the tracks already routed:

- `AnalogPower` and `EncoderPower` are added as low-current 0.3 mm subclasses
  so the tight U38 and J13 regions are not forced onto the 0.8 mm main-power
  width.
- 284 segments across 39 nets were resized without changing endpoints or
  layers.
- Main power nets are now 0.8 mm, field power and ground are 0.5 mm, analog is
  0.25 mm, and the low-current analog and encoder supplies use 0.3 mm.
- The tight `+12V_AO` and `+5V_ENC` areas remain on 0.3 mm subclasses rather
  than being forced to 0.8 mm, avoiding new shorts around U38 and J13.
- DRC retains only the four pre-existing RN13 shorting pairs and their four
  solder-mask bridges. The remaining findings are expected netclass-clearance
  cleanup from routes drawn at the old 0.2 mm defaults.

- Board: `hardware/checkpoints/checkpoint-84-netclass-track-widths.kicad_pcb`
- Project rules: `hardware/checkpoints/checkpoint-84-netclass-track-widths/motherboard.kicad_pro`
- Front/back: `hardware/checkpoints/checkpoint-84-netclass-track-widths/`
- Width report: `hardware/checkpoints/checkpoint-84-netclass-track-widths/netclass-track-widths.json`
- DRC: `hardware/checkpoints/checkpoint-84-netclass-track-widths/drc.json`

Checkpoint 85 replaces the undersized SOT-23 input MOSFET:

- Q1 is now an Infineon IRF7240PBF, `-40 V` / `-10.5 A` P-channel MOSFET in
  the standard SO-8 pinout.
- Source pins 1-3 connect to `VIN_PROT`, gate pin 4 to `Q1_GATE`, and drain
  pins 5-8 to `VIN_FUSED`.
- The existing 100 k gate pulldown and 12 V gate-source zener remain suitable;
  the IRF7240 gate rating is +/-20 V.

- Board: `hardware/checkpoints/checkpoint-85-q1-irf7240-so8.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-85-q1-irf7240-so8/`
- Datasheet: `hardware/checkpoints/checkpoint-85-q1-irf7240-so8/IRF7240PBF.pdf`
- DRC: `hardware/checkpoints/checkpoint-85-q1-irf7240-so8/drc.json`
- ERC: `hardware/checkpoints/checkpoint-85-q1-irf7240-so8/erc.json`

Checkpoint 86 reverses the active RN13 elements to match the copper that was
already routed to its pads:

- RN13 element 2 pins 2/7 are `OUT22/GND`.
- RN13 element 3 pins 3/6 are `OUT21/GND`.
- RN13 element 4 pins 4/5 are `OUT20/GND`.
- RN13 element 1 pins 1/8 is now the spare element.
- The RN13 footprint position and rotation are unchanged.
- DRC falls from 217 to 209 items: the four RN13 shorting errors and four
  solder-mask bridges are eliminated. Unresolved connections fall from 439 to
  436.

- Board: `hardware/checkpoints/checkpoint-86-rn13-straight-order.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-86-rn13-straight-order/`
- Pin-order analysis: `hardware/checkpoints/checkpoint-86-rn13-straight-order/rn13-optimization.json`
- DRC: `hardware/checkpoints/checkpoint-86-rn13-straight-order/drc.json`
- ERC: `hardware/checkpoints/checkpoint-86-rn13-straight-order/erc.json`

Checkpoint 87 swaps only the two active terminals of RN30:

- RN30 pin 1 is now `OUT26`; pin 2 is now `OUT24`.
- Pins 3/6 remain `OUT25/GND`; pins 4/5 remain `OUT23/GND`.
- The footprint position, rotation, GND terminals and all other components are
  unchanged.
- No existing copper was moved. Because the two local stubs still terminate at
  the previous OUT24/OUT26 pad positions, DRC now reports three local
  shorting items and three mask bridges that require local rerouting.

- Board: `hardware/checkpoints/checkpoint-87-rn30-pin-swap.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-87-rn30-pin-swap/`
- DRC: `hardware/checkpoints/checkpoint-87-rn30-pin-swap/drc.json`
- ERC: `hardware/checkpoints/checkpoint-87-rn30-pin-swap/erc.json`

Checkpoint 88 removes redundant 5 V reservoir/bypass parts:

- C8 (10 uF) is redundant with the two fitted 22 uF output capacitors C6/C11.
- C16 (10 uF) is removed from the general 5 V rail.
- C17 and C77 (100 nF) are removed because each supply-bearing IC already has
  a local bypass capacitor.
- The U2 regulator group remains C10/C76 on the input and C90/C13 on the
  output.

Checkpoint 88 also adds the active LVDS option:

- U41 is a DS90LV047A quad CMOS-to-LVDS driver in SOIC-16.
- `HSTX_D0_P`, `HSTX_D1_P`, `HSTX_D2_P` and `HSTX_CLK_P` drive its four
  single-ended inputs.
- `EN` is tied to `+3V3`; `EN*` is tied to GND.
- Its outputs drive the existing J22 LVDS lanes, with C106 providing local
  100 nF decoupling.
- RN26/RN27 remain available as the passive alternate but are marked DNP.

- Board: `hardware/checkpoints/checkpoint-88-active-lvds-and-cap-cleanup.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-88-active-lvds-and-cap-cleanup/`
- LVDS datasheet: `hardware/checkpoints/checkpoint-88-active-lvds-and-cap-cleanup/DS90LV047A.pdf`
- DRC: `hardware/checkpoints/checkpoint-88-active-lvds-and-cap-cleanup/drc.json`
- ERC: `hardware/checkpoints/checkpoint-88-active-lvds-and-cap-cleanup/erc.json`

Checkpoint 89 fixes the WeAct 3D model alignment:

- The STEP file uses the module PCB corner as its origin rather than the
  footprint center.
- The footprint and placed MOD1 instance now use offset
  `(-20.7, +20.6, 0) mm`.
- The 41.4 x 41.1 mm module body is centered inside the four socket rows and
  its mounting reference plane is on the board top.
- No electrical footprints, pads, tracks or vias were moved.

- Board: `hardware/checkpoints/checkpoint-89-weact-3d-alignment.kicad_pcb`
- Front/back: `hardware/checkpoints/checkpoint-89-weact-3d-alignment/`
- 3D top: `hardware/checkpoints/checkpoint-89-weact-3d-alignment/board-3d-top.png`
- 3D isometric: `hardware/checkpoints/checkpoint-89-weact-3d-alignment/board-3d-isometric.png`

Checkpoint 90 removes the HDMI connector and its dedicated circuitry:

- J22 remains the sole LCD LVDS connector; U41/C106 remain the active LVDS
  driver population and RN26/RN27 remain the unfitted passive alternative.
- J23, U30-U32, RN28/RN29, R59/R60, F3 and C71/C72 are removed. This covers the
  HDMI Type-A receptacle, three ESD arrays, +5 V fuse and local capacitors,
  DDC pull-ups and HDMI 0R link arrays.
- No HDMI net, HDMI power flag or HDMI footprint remains in the schematic,
  netlist or PCB.
- The generator retains the retired reference slots so unrelated parts do not
  renumber. It no longer emits HDMI symbols, footprints or nets.
- The hand-placed PCB, two-layer stackup, 200 x 150 mm outline and corrected
  WeAct 3D offset are preserved. Freerouting was not started.
- The regenerated netlist contract passes with 323 components and 331 nets.
  The PCB has 319 footprints, zero HDMI components and zero HDMI nets.
- DRC reports 188 pre-existing clearance/assembly findings and 350 unresolved
  connections, none referencing HDMI. ERC has no functional errors; its 34
  warnings are existing library-symbol mismatches.

- Board: `hardware/checkpoints/checkpoint-90-hdmi-removed.kicad_pcb`
- Front/back ratsnest: `hardware/checkpoints/checkpoint-90-hdmi-removed/`
- 3D top: `hardware/checkpoints/checkpoint-90-hdmi-removed/board-3d-top.png`
- 3D isometric: `hardware/checkpoints/checkpoint-90-hdmi-removed/board-3d-isometric.png`
- DRC: `hardware/checkpoints/checkpoint-90-hdmi-removed/drc.json`
- ERC: `hardware/checkpoints/checkpoint-90-hdmi-removed/erc.json`

Checkpoint 91 applies the supplied LCD connector pinout:

- J22 uses odd pins as the left column and even pins as the right column.
- Rows 1-8 are used. Rows 9-10 and pins 17-20 remain unconnected.
- +3V3 is on pins 1-3; GND is on pins 4-6 and 13-14.
- D0-/D0+, D1-/D1+, D2-/D2+ and CLK-/CLK+ occupy pins 7/8, 9/10, 11/12
  and 15/16 respectively.
- The supplied pinout has no backlight contact. MOD1 GPIO1 is documented as
  reserved for a future backlight PWM, but currently has no board net or
  external connector assigned.
- The footprint position and all copper remain unchanged. The B.Cu ground zone
  was refilled after the pad-net update.
- The netlist contract passes with 323 components, 330 nets and no single-node
  nets. DRC remains at 188 findings and unconnected items fall from 350 to 349.
  ERC remains at 34 existing library-symbol warnings with no functional errors.

- Board: `hardware/checkpoints/checkpoint-91-verified-lvds-pinout.kicad_pcb`
- Front/back ratsnest: `hardware/checkpoints/checkpoint-91-verified-lvds-pinout/`
- DRC: `hardware/checkpoints/checkpoint-91-verified-lvds-pinout/drc.json`
- ERC: `hardware/checkpoints/checkpoint-91-verified-lvds-pinout/erc.json`

Checkpoint 92 adds the narrow LVDS connector routing class:

- `LVDS_D0_N/P`, `LVDS_D1_N/P`, `LVDS_D2_N/P` and `LVDS_CLK_N/P` use the
  dedicated `LVDSConnector` netclass.
- Track and differential-pair width are 0.15 mm, differential gap is 0.20 mm
  and clearance is 0.20 mm.
- `HSTX_*` source nets remain in `DigitalDiffPair` at 0.20 mm.
- The board-wide minimum track width is reduced from 0.20 mm to 0.15 mm so the
  connector class is legal. No existing track segments required resizing.
- DRC remains at 188 findings and 349 unconnected items; ERC remains at 34
  existing library-symbol warnings.

- Board: `hardware/checkpoints/checkpoint-92-lvds-connector-width.kicad_pcb`
- Project: `hardware/checkpoints/checkpoint-92-lvds-connector-width/motherboard.kicad_pro`
- Width report: `hardware/checkpoints/checkpoint-92-lvds-connector-width/netclass-widths.json`
- DRC: `hardware/checkpoints/checkpoint-92-lvds-connector-width/drc.json`
- ERC: `hardware/checkpoints/checkpoint-92-lvds-connector-width/erc.json`

Checkpoint 93 finishes the 0.12 mm J22 fanout geometry:

- `LVDSConnector` now uses 0.12 mm track width, 0.12 mm differential gap and
  0.12 mm clearance.
- The board-wide minimum track width is 0.12 mm.
- Six existing user-routed LVDS nets containing 16 segments were narrowed from
  0.20 mm to 0.12 mm without moving endpoints.
- With 1.35 mm pads on 2.00 mm pitch, the fanout budget is
  `0.12 + 0.12 + 0.12 + 2 x 0.12 = 0.60 mm` inside the available 0.65 mm.
- The B.Cu ground zone was refilled after the latest user position changes.
- DRC reports no J22 or `LVDS_*` clearance violations. Overall DRC is 189
  findings with 343 unresolved connections; ERC remains at 34 existing
  library-symbol warnings with no functional errors.

- Board: `hardware/checkpoints/checkpoint-93-lvds-012-fanout.kicad_pcb`
- Project: `hardware/checkpoints/checkpoint-93-lvds-012-fanout/motherboard.kicad_pro`
- Width report: `hardware/checkpoints/checkpoint-93-lvds-012-fanout/netclass-widths.json`
- DRC: `hardware/checkpoints/checkpoint-93-lvds-012-fanout/drc.json`
- ERC: `hardware/checkpoints/checkpoint-93-lvds-012-fanout/erc.json`

Checkpoint 94 adds the J22-only clearance override:

- Global `Ground` and `Power` clearances remain 0.30 mm.
- A board-specific DRC rule applies 0.12 mm clearance when an `LVDSConnector`
  track is beside a J22 pad, overriding the larger GND or power netclass value
  only inside that connector fanout.
- The rule is stored in `hardware/motherboard.kicad_dru`; unrelated board areas
  continue to use their normal netclass clearances.
- A temporary test segment placed 0.12 mm from J22 GND pad 5 passed the
  clearance check. Its only finding was the expected dangling-end warning from
  the artificial test geometry, and the temporary board was removed.
- The live DRC remains at 189 findings and 343 unconnected items, with no
  J22 or `LVDS_*` clearance violations.

- Board: `hardware/checkpoints/checkpoint-94-j22-clearance-rule.kicad_pcb`
- Project: `hardware/checkpoints/checkpoint-94-j22-clearance-rule/motherboard.kicad_pro`
- Custom rules: `hardware/checkpoints/checkpoint-94-j22-clearance-rule/motherboard.kicad_dru`
- DRC: `hardware/checkpoints/checkpoint-94-j22-clearance-rule/drc.json`
- ERC: `hardware/checkpoints/checkpoint-94-j22-clearance-rule/erc.json`

Checkpoint 95 makes the LVDS rules resilient to KiCad project rewrites:

- The open KiCad editor rewrote `motherboard.kicad_pro`, removing the
  `LVDSConnector` class and restoring the 0.20 mm board minimum. This caused
  16 false `track_width` errors on the existing 0.12 mm LVDS segments.
- `motherboard.kicad_dru` now matches `LVDS_*` by net name directly. It
  constrains track width to 0.12 mm and sets 0.12 mm as the preferential
  differential gap without requiring a project netclass to exist.
- The J22 footprint clearance override also matches `LVDS_*` by net name, so
  GND and power pads still receive 0.12 mm clearance only in that connector
  fanout regardless of project netclass rewrites.
- With the project class intentionally absent, DRC returned to 193 findings
  before the differential-gap maximum was removed, then 189 once that overly
  strict check was corrected. With the project class restored, the final DRC
  is 188 findings.
  No LVDS width or J22 clearance errors remain. The `LVDSConnector` class and
  0.12 mm project minimum were then restored.
- The running KiCad process must discard/reload the project or be restarted
  before interactive routing will display the new 0.12 mm defaults.

- Board: `hardware/checkpoints/checkpoint-95-lvds-rule-resilience.kicad_pcb`
- Project: `hardware/checkpoints/checkpoint-95-lvds-rule-resilience/motherboard.kicad_pro`
- Custom rules: `hardware/checkpoints/checkpoint-95-lvds-rule-resilience/motherboard.kicad_dru`
- DRC: `hardware/checkpoints/checkpoint-95-lvds-rule-resilience/drc.json`
- ERC: `hardware/checkpoints/checkpoint-95-lvds-rule-resilience/erc.json`

Checkpoint 96 swaps the passive-LVDS resistor-network terminals:

- RN26 element 1 pins 1/8 and element 2 pins 2/7 exchange their D1
  connections.
- RN26 element 3 pins 3/6 and element 4 pins 4/5 exchange their D0
  connections.
- RN27 applies the same two element swaps to CLK and D2.
- Both network positions, rotations and sides are unchanged. Their footprints
  were not regenerated or moved.
- Existing copper was intentionally left untouched. As a result, routes that
  still terminate on the old RN pads now report eight shorting items, eight
  solder-mask bridges and eight additional dangling endpoints. These local
  LVDS branches require rerouting to the newly assigned pads.
- DRC currently reports 213 findings and 348 unresolved connections. ERC
  remains at 34 existing library-symbol warnings with no functional errors.

- Board: `hardware/checkpoints/checkpoint-96-rn26-rn27-pin-swaps.kicad_pcb`
- Mapping: `hardware/checkpoints/checkpoint-96-rn26-rn27-pin-swaps/rn-pin-swap.json`
- DRC: `hardware/checkpoints/checkpoint-96-rn26-rn27-pin-swaps/drc.json`
- ERC: `hardware/checkpoints/checkpoint-96-rn26-rn27-pin-swaps/erc.json`

Checkpoint 97 moves the shift-register return to the free MOD1 corner pad:

- `SR_IN_Q7` moves from GPIO35/MOD1.25 to GPIO23/MOD1.60.
- GPIO35 is released as an unconnected spare.
- U9 pin 9 escapes on F.Cu to a via at `(100.800, 60.500)`, crosses on B.Cu
  to `(100.410, 68.800)`, and returns to MOD1 pin 60 on F.Cu.
- The new route uses 0.20 mm tracks and two 0.80/0.40 mm vias.
- The B.Cu ground zone was refilled. DRC reports no `SR_IN_Q7` track, via or
  clearance errors and is now at 192 findings with 329 unresolved connections.
- GPIO23 is connected to the WeAct module's onboard USER key through R16 (0R).
  Remove R16 before fitting the module; this isolates the SW3 key network and
  WeAct C27 capacitor position from U9 Q7. Motherboard C27 at U11 is unrelated.

- Board: `hardware/checkpoints/checkpoint-97-gp23-shift-return.kicad_pcb`
- Pin map: `hardware/checkpoints/checkpoint-97-gp23-shift-return/gp23-shift-return.json`
- DRC: `hardware/checkpoints/checkpoint-97-gp23-shift-return/drc.json`
- ERC: `hardware/checkpoints/checkpoint-97-gp23-shift-return/erc.json`

Checkpoint 98 removes the debugger-reset dependency from the output registers:

- J4 changes from a five-pin header to a four-pin SWD header:
  `1=+3V3`, `2=SWDIO`, `3=SWCLK`, `4=GND`.
- WeAct MOD1 `RUN` is no longer connected externally. The module's onboard
  reset button remains the MCU reset.
- U10-U13 pin 10 (`~SRCLR`) are assigned to `+3V3`, following the conventional
  74HC595 all-enabled configuration.
- The obsolete `RESET_N` net and six existing reset track stubs are removed.
  J4 is replaced in place with a 1x04 header.
- The four new `~SRCLR` connections remain part of the normal +3V3 power-routing
  work; they are not a separate reset net.
- DRC improves to 184 findings and 326 unresolved connections. ERC remains at
  34 existing library-symbol warnings with no functional errors.

- Board: `hardware/checkpoints/checkpoint-98-four-pin-swd.kicad_pcb`
- Reset map: `hardware/checkpoints/checkpoint-98-four-pin-swd/reset-map.json`
- DRC: `hardware/checkpoints/checkpoint-98-four-pin-swd/drc.json`
- ERC: `hardware/checkpoints/checkpoint-98-four-pin-swd/erc.json`

Checkpoint 99 tidies the SD/Wi-Fi clusters and simplifies the ADC reference:

- C16 was already removed. C14, the redundant 10 uF bulk capacitor on
  `+3V3_A`, is now also removed. FB1 and C15 (100 nF) remain as the reference
  filter and move to B.Cu near MOD1 pin 48.
- R55-R58 are on one exact vertical grid line at x=161.925 mm. C70, C69 and
  C89 share the y=37.465 mm line; C69 moves closer to J20 to improve ESP supply
  transient support.
- FB2, C68 and C67 form a vertical line at x=166.370 mm beside J19, with
  5.715 mm pitch.
- No connectors or routed copper moved.
- The original ESP-01 and ESP-01S both use the same eight-pad interface. The
  motherboard's R55-R58 provide the external 10 k pull-ups that the non-S
  ESP-01 requires on GPIO2, GPIO0, CH_PD/EN and RST. U34 and its 10 uF/100 nF
  output bank provide the dedicated 3.3 V supply.
- DRC is 182 findings with 319 unresolved connections; ERC remains at 34
  existing library-symbol warnings with no functional errors.

- Board: `hardware/checkpoints/checkpoint-99-sd-wifi-tidy.kicad_pcb`
- Placement: `hardware/checkpoints/checkpoint-99-sd-wifi-tidy/placement.json`
- DRC: `hardware/checkpoints/checkpoint-99-sd-wifi-tidy/drc.json`
- ERC: `hardware/checkpoints/checkpoint-99-sd-wifi-tidy/erc.json`

Checkpoint 100 applies a safe coarse-grid pass:

- FB1 and C15 return to F.Cu near MOD1 and now use only the 100 nF reference
  bypass.
- U41 and C106 return to F.Cu as an aligned LCD-driver pair. The only
  remaining back-side footprints are the intentional JP2-JP4 field-mode
  jumpers on B.Cu.
- Thirty-seven unrouted footprints were snapped to the 0.635 mm imperial grid.
  The pass intentionally excludes components with attached routing where a
  snap would introduce clearance damage.
- A blind full-board 1.27 mm snap was rejected after testing because it added
  331 DRC findings. With the routed footprints protected and U41/C106 aligned,
  the final DRC is 187 findings.
- The WiFi and SD passive clusters are on exact 0.635 mm grid lines without
  moving their connectors. Their final DRC has 323 unresolved connections.

- Board: `hardware/checkpoints/checkpoint-100-coarse-grid-front.kicad_pcb`
- Grid report: `hardware/checkpoints/checkpoint-100-coarse-grid-front/coarse-grid.json`
- Front/back ratsnest: `hardware/checkpoints/checkpoint-100-coarse-grid-front/`
- DRC: `hardware/checkpoints/checkpoint-100-coarse-grid-front/drc.json`
- ERC: `hardware/checkpoints/checkpoint-100-coarse-grid-front/erc.json`

Checkpoint 101 replaces Q1 with diode-fed power branches and adds the
backlight converter:

- The common input retains F1 and D1. Two 1 A, 60 V SS16 series diodes split
  the protected feed into `VIN_PROT` for logic/analog housekeeping and
  `VIN_BL_PROT` for the backlight converter.
- Q1, R1 and the Q1 gate zener are removed.
- U3 is a second LMR36510ADDAR buck configured for 12 V / 1 A. The passive
  set is standardized with the other regulators: 47 uH, 100 k / 9.09 k
  feedback, 3 x 22 uF/25 V output, 22 uF/50 V input, 1 uF VCC bypass and
  100 nF bootstrap. C1 is removed because both diode-fed branches retain bulk
  input capacitance.
- The existing U37 L78L12 `+12V_AO` rail remains unchanged for the four
  0-10 V outputs.
- J2 exposes backlight power, PWM, ground and an optional low-side LED return.
  The direct PWM and Q8 gate share GPIO35/MOD1 pin 25. The redundant two-pin J3
  output and unused BL power-good network are omitted. GPIO1, GPIO3 and GPIO36
  remain uncommitted spare outputs.
- A 100 ohm R131 is inserted between the MCU PWM output and J2 pin 3. R129
  branches from the same MCU-side node to Q8. A dedicated 0.2 mm
  BacklightControl netclass covers `BL_PWM_MCU`, `BL_PWM` and `BL_SW_GATE`;
  only `+12V_BL` and `BL_LED_N` remain on the 0.8 mm Power class.
- RN36 pulls ESP `EN`, `RST`, `GPIO0` and `GPIO2` to `+3V3_WIFI`, keeping
  those interface pins in the dedicated ESP supply domain.
- RN32-RN35 provide four PLC 4x4.7 k pull-up networks and RN36 provides the
  ESP 4x10 k pull-up network. The three safety pull-ups remain discrete.
- The PC817C experiment was reverted because the separate optocouplers did not
  fit. The four LTV-847S and three EL3H7 footprints are restored, and no
  existing copper was changed.
- All footprints are inside the 200 x 150 mm PCB outline and the routed
  connectivity is complete.
- ERC has no electrical errors. PCB DRC reports no shorts and no unconnected
  items; documented clearance and silkscreen findings remain.
