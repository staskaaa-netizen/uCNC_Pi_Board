# PCB Design Retrospective and Next-Time Playbook

## Verdict

This project was **human-directed AI implementation plus substantial EDA
automation**. It was not an autonomous "AI made a PCB" exercise.

The human remained the systems architect and final electrical reviewer and did
not manually draw the schematic. The AI generated and repeatedly changed the
native KiCad schematic, PCB data, netlist structure, placement scripts and
manufacturing outputs under human direction. This is substantially more than
AI-assisted drawing, but it is still different from a machine independently
deriving requirements, selecting a complete architecture, proving it
electrically and releasing it for manufacturing.

The accurate description is:

- **human-authored requirements and acceptance decisions**
- **AI-authored implementation and generated EDA artifacts**
- **human visual, physical and electrical review**
- **automated connectivity and manufacturing checks**

The result is closer to:

```text
human requirements and repeated corrections
    -> AI implementation and change propagation
    -> KiCad/netlist/DRC/artifact checks
    -> human visual and electrical review
    -> repeat
```

It is not:

```text
one prompt -> validated production PCB
```

## Project History: Original Brief Versus Final Board

### Starting size and fit estimate

The early AI assessment was that the original feature-rich design would not
fit within a nominal **150 x 200 mm** two-layer board. That estimate was
reasonable for the original scope.

The placement documentation records that the first connectivity-optimized
baseline used the preceding **312-component schematic** and an initial
**210 x 150 mm** outline. The first checked-in project snapshot then held:

- **310 schematic components**
- **327 nets**
- **299 physical BOM items** in 101 purchasing groups
- a nominal **200 x 150 mm** board
- complete placement but no routing
- 499 expected unrouted connections

Component counts moved slightly during the early corrections, generally in the
310-312 range, before the later feature removal and power cleanup began.

The original brief requested 24 opto-isolated PLC inputs, but the first
implemented baseline already used 16 isolated inputs. The final board retains
those 16 inputs and adds optically isolated general outputs. Therefore the
final board did not simply reduce every dimension of the feature set.

The board then passed through several sizes:

| Stage | Nominal size | Area | State |
|---|---:|---:|---|
| Original full-feature target | 150 x 200 mm | 30,000 mm² | early AI estimate: did not fit |
| Early connectivity baseline | 210 x 150 mm | 31,500 mm² | placement optimization |
| First committed baseline | 200 x 150 mm | 30,000 mm² | placed, unrouted |
| Compacted two-layer revision | 196.5 x 150 mm | 29,475 mm² | placed, unrouted |
| Requested release outline | 200 x 150 mm | 30,000 mm² | placed, then routed |
| Final reduced-scope board | 160 x 120 mm | 19,200 mm² | routed prototype |

The final board outline measures approximately **160.043 x 120.038 mm**. That
is about **36% less area** than the original 150 x 200 mm proposal. This did
not disprove the first estimate; it became possible because the functional
scope was reduced and the redundant circuitry was removed.

### Component-count history

| Metric | Early checked-in baseline | Final board | Change |
|---|---:|---:|---:|
| Schematic components | 310 | 281 | -29 |
| Nets | 327 | 320 | -7 |
| PCB footprints | 305 | 275 | -30 |
| Physical BOM items | 299 | 270 | -29 |
| BOM purchasing groups | 101 | 49 | -52 |
| SMT references | not separated in the first snapshot | 235 | current assembly metric |

Component count alone does not describe the simplification. Many parts were
replaced by functionally denser devices while other whole functions were
removed.

### Feature comparison

| Function | Original brief | Final board |
|---|---|---|
| MCU | Socketed WeAct RP2350B | Preserved |
| PLC inputs | 24 opto-isolated inputs requested; 16 present in the first implementation | 16 opto-isolated inputs, `I01-I16` |
| E-stop | Dedicated input | Preserved on dedicated GPIO9 |
| HOLD/START | Separate controls | Removed; only E-stop retained |
| Motion outputs | 16 register-driven motion outputs | Seven STEP/DIR axes with shared enable groups |
| General outputs | Eight ULN2003 low-side outputs without a requested logic-to-field opto stage | 16 outputs whose logic side is opto-isolated and whose field side is driven through TBD62083AFG arrays |
| Servo feedback | Not a separate feature | Seven paired ZERO/ERROR inputs |
| Input shift registers | Four 74HC165 in a continuous 32-bit chain | Four 74HC165 retained for PLC and servo-status inputs |
| Output shift registers | Four 74HC595 at 3.3 V | Four SN74AHCT595 at 5 V |
| Keyboard matrix | 8 x 8 scan matrix in the 32-bit chain | Removed |
| I2C keyboard expansion | Required | Keyboard-specific interface removed; generic I2C retained |
| Encoders | Three A/B/Z inputs | Three preserved with 5 V-to-3.3 V translation |
| Analog inputs | Three 0-10 V inputs | Four 0-10 V inputs |
| Analog outputs | Three PWM-derived 0-10 V outputs | Four PWM-derived 0-10 V outputs |
| HDMI | HDMI Type A alternative | Removed |
| LVDS | 20-pin HSTX/LVDS | Preserved, passive resistor interface only |
| Active LVDS driver | Optional alternate population | Removed |
| SD storage | Full-size SD socket | MicroSD socket plus 9-pin breakout header |
| Wi-Fi | Socketed ESP-01S | Preserved |
| Main supply | 12-24 V input, 5 V buck, multiple 3.3 V rails | 24 V-to-5 V buck, module 3.3 V regulator and peripheral 3.3 V rail |
| Backlight | LED/CCFL support with onboard switching | Isolated 24 V-to-12 V backlight supply, simplified control |
| Power-good/test points | Required | Removed |
| Output inhibit/supervision | Hardware safety chain | Removed; handled externally |
| Reset/SWD/user buttons | Motherboard reset, SWD and controls | Relied on the WeAct board where already provided |
| Board | Two layers, hand-assembly-friendly | Preserved, reduced to 160 x 120 mm |

### What the size history proves

The first AI fit statement was not simply wrong. The original requirements
contained too many connectors, ICs, protection stages, alternate populations
and field interfaces for a comfortable 150 x 200 mm two-layer hand-assembly
board.

The later success came from a different implementation of the design:

- fewer PLC input channels than the original 24-channel brief, although the
  implemented baseline had already settled on 16
- no keyboard matrix
- no HDMI alternate
- no full-size SD socket
- no active LVDS driver
- fewer supervision and safety components
- optically isolated field outputs added while input-channel count stayed at 16
- denser output-driver packages
- reuse of the WeAct module's existing reset and power functions

The useful conclusion is that three distinct changes made the final board
smaller:

1. **scope reduction** removed entire functions and interface domains
2. **implementation simplification** changed how the remaining functions were
   realized
3. **placement optimization** made the smaller arrangement routable

The 5 V AHCT595 chain, consolidated output drivers, revised optocoupler and
resistor structures, and reuse of the WeAct module's power/reset functions are
implementation simplifications, not feature removals.

### Current manufacturing status

The final manufacturing package was regenerated from the same PCB revision
that is checked into Git and is ready to send:

- `uCNC_Pi_Board_PCB_Fabrication.zip` for bare PCB fabrication
- `uCNC_Pi_Board_SMT_Assembly.zip` for PCB fabrication plus SMT assembly
- 270 physical BOM items in 51 purchasing groups
- 235 matched SMT BOM and CPL references
- 275 visible PCB references
- two copper layers and a nominal 160 x 120 mm outline
- zero DRC errors and zero unconnected items
- six non-field silkscreen warnings

The manufacturing files are ready for prototype ordering. This does not
constitute electrical bench validation or safety certification.

## What Was Actually Engineered

This was more than housekeeping. The work included real system-level changes:

- Generating and reconnecting the native KiCad schematic from the evolving
  hardware contract; the human did not manually draw schematic wires.
- Reworking the I/O architecture and connector mapping.
- Reallocating RP2350B GPIO, PIO, ADC, I2C and HSTX functions.
- Simplifying opto-isolated field input and output stages.
- Changing output shift registers to 5 V SN74AHCT595 devices while retaining
  3.3 V input registers.
- Adding and checking motion buffers, low-side drivers and isolation stages.
- Reworking power distribution, buck converters and decoupling placement.
- Maintaining schematic, PCB, BOM, connector documentation and manufacturing
  outputs through repeated design changes.
- Building scripts for placement, field cleanup, verification and artifact
  export.
- Running DRC, netlist checks and manufacturing-package checks.

## What Was Mostly Housekeeping

A large part of the effort was necessary but not inventive PCB design:

- Moving reference designators and functional labels.
- Restoring or repairing connectivity after manual edits.
- Keeping BOM, CPL, PDFs, Gerbers, drills and 3D views synchronized.
- Correcting net names, pin order, connector labels and stale documentation.
- Moving fields out of pads, vias and other silkscreen.
- Rebuilding archives after every board change.
- Fixing cache and filename problems for rendered images.

That work matters, but it should not be confused with architecture innovation.
Most of it is a change-management problem that can be automated more
systematically.

## Human Contributions That Remained Essential

The human did not draft the schematic, but several higher-level decisions could
not safely have been delegated wholesale:

- Deciding which interfaces were actually required.
- Choosing which features to remove to make the board manufacturable.
- Rejecting unnecessary protection and supervision circuitry.
- Resolving connector semantics and physical pin ordering.
- Deciding safety boundaries around E-stop and field power.
- Choosing placement compromises after visual inspection.
- Confirming firmware and uCNC pin compatibility.
- Recognizing incorrect or misleading text on the assembled board.
- Accepting remaining mechanical, sourcing and manufacturing compromises.

The repeated phrase "you turn" describes an iterative human/AI design loop,
not autonomous design.

## Strong Parts of the Process

- Changes were regularly checked with KiCad DRC and netlist verification.
- The project retained useful engineering documentation and generated outputs.
- Scripts made otherwise tedious KiCad transformations repeatable.
- The workflow adapted quickly when the architecture changed.
- The final PCB is electrically connected with zero DRC errors and zero
  unconnected items.
- All 275 component references are visible and use one silkscreen text size.
- The manufacturing BOM and CPL are cross-checked at 235 SMT references.
- Rendered 3D images now use content-addressed filenames to avoid stale browser
  caches.

## Weak Parts That Should Improve

### The source of truth was ambiguous

The checked-in PCB contains approved manual placement and routing, while
scripts also contain placement and generator logic. Running the generator too
casually could discard manual work.

For the next project, choose one of these models before layout begins:

1. **Generator-owned:** every manual edit is encoded in configuration and the
   board can always be rebuilt deterministically.
2. **Board-owned:** the PCB is authoritative and generators are limited to
   additive analysis or explicitly approved bulk edits.

Do not mix the two without a clear ownership rule.

### Human inspection carried too much verification load

Wrong labels and placement problems were repeatedly found visually after the
automated checks passed. DRC proves geometry and connectivity rules; it does
not prove that a connector label describes the actual physical pin order.

Pin maps, cable orientation, mating-connector view direction and silkscreen
meaning need a separate machine-checkable contract.

### Documentation drifted

At the time of this retrospective, `README.md` still contains old verification
numbers even though the board specification records the current six warnings.
Generated and hand-written status sections must come from one source.

### "Done" was used before visual approval

Several passes were mechanically valid but not subjectively acceptable. For
future work, distinguish these states:

- generated
- electrically equivalent
- DRC-clean
- visually reviewed
- approved
- manufacturing-ready

## Recommended Workflow for the Next Board

### Phase 0: Freeze the requirements

Create a machine-readable requirements file covering:

- input and output counts and electrical classes
- connector families, pin counts and orientation
- isolation boundaries
- power rails and maximum currents
- controller/module pin constraints
- firmware signal requirements
- board size, layers and assembly side
- environmental and safety assumptions

Record uncertain items separately. Do not silently resolve them during layout.

### Phase 1: Architecture and interface contract

Produce and approve:

- block diagram
- power tree
- isolation map
- controller pin allocation
- connector pinout tables
- net naming convention
- firmware interface table

Gate: every external signal has a source, destination, voltage domain and
connector pin.

### Phase 2: Schematic

- Build one functional channel before replicating it.
- Review the first channel visually and electrically.
- Only then expand to the remaining channels.
- Maintain a net-name and pin-mapping contract independently of either the
  schematic or PCB.

Gate: ERC clean or every exception documented; schematic-to-contract comparison
passes.

### Phase 3: Placement

- Lock mechanical parts and connectors first.
- Review each functional block separately.
- Track airwire length, crossings, congestion and placement anomalies.
- Keep decoupling and protection parts tied to their actual electrical nodes.
- End every manual editing session with a recorded artifact build.

Gate: human placement approval plus placement checks.

### Phase 4: Routing

- Review and lock power and differential pairs before general routing.
- Prevent autorouting from compensating for bad placement.
- Track vias, layer changes, track widths and reference-plane continuity.
- Refill zones and rerun DRC after every route batch.

Gate: zero unconnected nets, zero errors, reviewed exceptions and no
unaccepted high-current or high-speed compromises.

### Phase 5: Manufacturing

- Generate BOM, CPL, Gerbers, drills, test drawings and 3D previews from one
  immutable board revision.
- Compare BOM, CPL and footprint references one-to-one.
- Check connector orientation against the mating view.
- Check component availability, lifecycle and assembly constraints.
- Read the fabrication README after generation, not before.

Gate: manufacturing review package approved against the exact Git commit.

## Rules for AI Assistance

Use these rules in future prompts:

1. State which file is authoritative.
2. Separate electrical changes from cosmetic changes.
3. Never claim "verified" without naming the verification performed.
4. Preserve user edits unless explicitly asked to restore or regenerate.
5. Back up the PCB before programmatic modification.
6. Report every moved component and every changed net.
7. Keep a before/after DRC comparison.
8. Treat DRC cleanliness and visual correctness as separate gates.
9. Regenerate all dependent artifacts after a board change.
10. Never push unless explicitly requested.
11. Use content-addressed or revisioned names for published images.
12. Stop for human approval at architecture, placement and routing boundaries.

## Definition of Done

A board revision is complete only when all of the following are true:

- requirements and interface contract are traceable
- schematic, PCB and firmware pin map agree
- ERC and DRC results are recorded
- every DRC exception has an explicit reason and owner
- no unconnected nets remain
- BOM and CPL references match the PCB
- connector labels and physical pin order are visually confirmed
- manufacturing files were generated from the committed board
- PDF and 3D previews are generated from the same revision
- generated documentation contains no stale status numbers
- Git contains the board, scripts, documentation and manufacturing package
- a human has approved the final revision

## Short Prompt Template for the Next Project

```text
Authoritative source: <schematic|PCB|generator|config>
Fixed requirements: <list>
Items allowed to change: <list>
Preserve: <connectors, pin maps, placement regions, firmware contract>
Task scope: <analysis|schematic|placement|routing|manufacturing>
Required gates: ERC, DRC, netlist comparison, BOM/CPL comparison
Stop for approval before: <major architecture, placement or routing changes>
Deliverables: <files and verification report>
Do not push or regenerate unrelated artifacts unless requested.
```

## Final Opinion

The project demonstrated that AI can materially accelerate an experienced
engineer's PCB workflow. It can generate code, transform KiCad data, maintain
large mappings, run repeated checks and keep artifact sets synchronized.

It did not prove that AI can independently engineer a production-ready board.
The real design intent, safety judgment, trade-offs and acceptance decisions
still came from the human. The next step toward genuine AI PCB design is not a
larger one-shot prompt; it is a stricter, machine-checkable engineering process
with clear source ownership and mandatory review gates.
