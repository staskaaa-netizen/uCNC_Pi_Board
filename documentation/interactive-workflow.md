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
