# uCNC RP2350B Motherboard

Generated board documents:

- [Combined board review](../manufacturing/board-review.pdf)
- [Front artwork and assembly layer](../manufacturing/board-front.pdf)
- [Mirrored rear artwork](../manufacturing/board-back.pdf)

## Board specification

| Item | Specification |
|---|---|
| Product | LeanCam NCC / uCNC RP2350B Motherboard |
| Status | Routed prototype, pre-release |
| Controller | Socketed WeAct Studio RP2350B Core Board |
| PCB outline | 200 mm x 150 mm |
| PCB construction | Two copper layers, 1.6 mm finished thickness |
| Mounting | Four M3 clearance holes |
| Assembly | Functional parts on the front; J22, C57, JP2, JP3 and JP4 on the back |
| Input supply | 24 V DC nominal machine supply, documented operating range 12-24 V |
| Main 5 V rail | LMR36510 synchronous buck, 1 A |
| Logic supply | AMS1117-3.3, +3V3 |
| Wi-Fi supply | Separate AMS1117-3.3, +3V3_WIFI |
| Analog supply | L78L12, +12V_AO |
| Isolated field supply | Traco TBA2-0512, +12 V isolated wetting rail |
| Board ID | MOD1, the socketed RP2350B module |

The board is a machine-control carrier, not a safety-rated controller.
Hazardous output power must be removed through an independent hard-wired
safety circuit.

## Digital I/O architecture

| Function | Capacity | Implementation |
|---|---:|---|
| Isolated PLC inputs | 16 | Four LTV-847S quad optocouplers, one per channel |
| Dedicated safety/control inputs | 3 | E-stop, HOLD and START through individual EL3H7 optocouplers |
| 3.3 V expansion inputs | 8 | Two four-channel headers, J9 and J27 |
| Keyboard inputs | 8 | KIN0-KIN7 through the input shift chain |
| General field outputs | 16 | DO0-DO15 through ULN2003A outputs and two BSS138 low-side stages |
| Motion outputs | 15 | Five EN/STEP/DIR axes plus one AUX output |
| Keyboard outputs | 8 | KOUT0-KOUT7 through the output shift chain |
| Encoder inputs | 3 | A/B/Z channels with 5 V to 3.3 V conditioning |
| Analog inputs | 3 | 0-10 V, resistor-divided into RP2350 ADC inputs |
| Analog outputs | 4 | 0-10 V through TLV2374 and RC filtering |

The digital chains are 32 bits wide:

- Input: four cascaded 74HC165 registers, eight bits each.
- Output: four cascaded 74HC595 registers, eight bits each.
- Shift data uses GPIO20, GPIO21 and GPIO22; the input return is GPIO23.
- E-stop, HOLD and START connect directly to GPIO37, GPIO38 and GPIO39.

The complete GPIO and shift-bit mappings are in
`documentation/gpio-map.md` and `documentation/io-bit-map.md`. Firmware must
preserve the documented physical pin permutations.

## Isolated field inputs

The 16 PLC inputs support two modes:

- External 24 V wetting.
- Dry contacts powered from the onboard isolated 12 V supply.

JP2, JP3 and JP4 select the wetting source per field bank and safety channel.
The isolated field return is `FIELD_COM0` or `FIELD_COM1`; it is not connected
to motherboard GND. D56 prevents external field voltage from backfeeding U40.

Each PLC channel includes a 2.2 k series resistor, indicator LED,
reverse-protection diode, optocoupler channel and individual 4.7 k logic-side
pull-up. Firmware must debounce the sampled contacts.

## Connectors

| Ref | Function |
|---|---|
| J1 | 24 V DC power input |
| J4 | SWD programming/debug |
| J5 | Dedicated E-stop loop |
| J6, J26 | HOLD and START buttons |
| J7, J8, J34, J35 | 16 isolated PLC inputs |
| J9, J27 | Expansion inputs 0-7, 3.3 V logic only |
| J10, J11, J28, J29, J30 | Axis EN/STEP/DIR outputs |
| J12, J32 | General field outputs DO0-DO15 |
| J33 | General-output field supply and GND |
| J13-J15 | Encoders 0-2 |
| J16 | Keyboard KIN/KOUT |
| J17 | Keyboard power/reference |
| J18 | I2C0 |
| J19 | Full-size SD card, SPI mode |
| J20 | Optional ESP-01/ESP-01S |
| J22 | 2x10, 2.00 mm LCD LVDS |
| J24 | Three 0-10 V analog inputs |
| J25 | Four 0-10 V analog outputs |
| J31 | AUX low-side output |

Detailed connector pinouts are in `documentation/connectors.md`.

## Power and protection

- Main input path: F1 2 A fuse, D1 24 V TVS and Q1 reverse-polarity MOSFET.
- U1 converts the protected machine input to the 1 A +5 V rail.
- The WeAct module receives +5 V and uses its own regulated 3.3 V rail.
- U2 independently supplies board logic, SD and LCD logic at +3V3.
- U34 independently supplies the optional ESP module at +3V3_WIFI.
- U37 supplies only the analog-output amplifier, avoiding a local hot spot.
- U40 provides an isolated +12 V wetting rail for dry-contact input mode.

Do not use the analog or isolated field rails to power motors, lamps or
high-current solenoids. General field outputs are limited by their external
supply and the ULN2003A/MOSFET ratings.

## Display and storage

- J22 carries three LVDS data lanes and one clock lane for a 2x10 panel
  interface. Rows 9-10 and pins 17-20 are not connected.
- U41, a DS90LV047A, is the active LVDS driver population.
- RN26 and RN27 are a mutually exclusive passive LVDS alternative. Do not fit
  U41 and both resistor networks together.
- There is no HDMI connector or HDMI-specific support circuitry.
- The LCD connector has no backlight contact; backlight power is external.
- The full-size SD card uses 3.3 V SPI and includes card-detect.

## PCB and manufacturing data

| Metric | Value |
|---|---:|
| Placed PCB footprints | 318 |
| BOM component quantity | 312 |
| Front / back footprint density | 39.23 / 4.92 percent |
| Through-hole / SMD pads | 265 / 984 |
| Through vias | 207 |
| Minimum track width | 0.12 mm |
| Minimum drill | 0.30 mm |

The BOM is in `manufacturing/bom.csv`. This specification is informational and
does not replace the KiCad schematic, PCB, DRC or ERC reports.

## Verification status

The version documented here was checked with KiCad 10.0.1:

- DRC: zero unconnected items and no shorts.
- ERC: zero electrical-rule errors.
- Remaining release work: 108 standard clearance findings, 34 silkscreen
  warnings and two intentional alternate-population courtyard overlaps between
  U41 and RN26/RN27.
- ERC retains 34 library-symbol cache mismatch warnings.

These remaining findings must be reviewed before fabrication. The board is not
declared production-ready or safety-certified.
