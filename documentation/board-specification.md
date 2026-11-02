# uCNC RP2350B Motherboard

Generated board documents:

- [Combined board review](../manufacturing/board-review.pdf)
- [Front artwork and assembly layer](../manufacturing/board-front.pdf)
- [Mirrored rear artwork](../manufacturing/board-back.pdf)
- [Top 3D render](../manufacturing/board-3d-top.png)
- [Bottom 3D render](../manufacturing/board-3d-bottom.png)

## Board specification

| Item | Specification |
|---|---|
| Product | LeanCam NCC / uCNC RP2350B Motherboard |
| Status | Placement prototype; copper routing intentionally deferred |
| Controller | Socketed WeAct Studio RP2350B Core Board |
| PCB outline | 200 mm x 150 mm |
| PCB construction | Two copper layers, 1.6 mm finished thickness |
| Mounting | Four M3 clearance holes |
| Assembly | Main assembly on the front; J22 on the back |
| Input supply | 24 V DC nominal machine supply, documented operating range 12-24 V |
| Main 5 V rail | LMR36510 synchronous buck, 1 A |
| Backlight rail | Isolated LMR36510 buck from PLC 24 V to `+12V_BL` |
| Logic supply | AMS1117-3.3, +3V3 |
| Wi-Fi supply | Separate AMS1117-3.3, +3V3_WIFI |
| Analog supply | L78L12, +12V_AO |
| Isolated field supply | External +24 V through J33/J45 |
| Board ID | MOD1, the socketed RP2350B module |

The board is a machine-control carrier, not a safety-rated controller.
Hazardous output power must be removed through an independent hard-wired
safety circuit.

## Digital I/O architecture

| Function | Capacity | Implementation |
|---|---:|---|
| Isolated PLC inputs | 16 | Four TLP291-4 quad optocouplers with four 4x10 k pull-up networks |
| Servo ZERO inputs | 7 | AX0-AX6, direct 3.3 V logic |
| Servo ERROR inputs | 7 | AX0-AX6, direct 3.3 V logic |
| Dedicated safety input | 1 | E-stop through a TLP291 SOP-4 optocoupler |
| General field outputs | 16 | DO0-DO15 through two TBD62083AFG packages |
| Motion outputs | 7 axes | STEP/DIR per axis, shared `EN_3AX` and `EN_4AX` enables |
| Encoder inputs | 3 | A/B/Z channels with 5 V to 3.3 V conditioning |
| SD storage | 1 | Open-Smart 3.3 V TF breakout on J36 |
| Analog inputs | 3 | 0-10 V, resistor-divided into RP2350 ADC inputs |
| Analog outputs | 4 | 0-10 V through TLV2374 and RC filtering |

The digital chains are 32 bits wide:

- Input: four cascaded 74HC165 registers, eight bits each. U8/U9 carry PLC
  inputs 1-8 and 9-16. U6/U7 carry paired servo ZERO/ERROR signals.
- Output: four cascaded 74HC595 registers, eight bits each.
- Shift data uses GPIO20, GPIO21 and GPIO22; the input return is GPIO23.
- E-stop connects directly to MOD1 pin 53. HOLD and START were removed.

The complete GPIO and shift-bit mappings are in
`documentation/gpio-map.md` and `documentation/io-bit-map.md`. Firmware must
preserve the documented physical pin permutations.

## Isolated field inputs

The 16 PLC inputs and dedicated E-stop form dry-contact loops powered from the
external isolated 24 V field supply. J33 and J45 are electrically parallel
two-pin access points for `+24V_FIELD` and the single `ISO_GND` return. The
isolated field domain is not connected to motherboard GND.

Each PLC channel includes an indicator LED, 2.2 k series resistor,
reverse-protection diode and one TLP291-4 optocoupler channel plus one element
from a 4x10 k logic-side pull-up network. The E-stop pull-up remains discrete.
Firmware must debounce the sampled contact.

## Connectors

| Ref | Function |
|---|---|
| J1 | 24 V DC power input |
| J2 | Backlight/CCFL: `+12V_BL`, `ISO_GND`, protected 3.3 V PWM |
| J4 | Physical 1x4 header; debug data pins unconnected |
| J5 | Dedicated E-stop loop |
| J7, J8 | 16 isolated PLC input signals |
| J10, J11, J28, J29, J30, J46, J47 | Seven 3-pin axis outputs: grouped EN, STEP, DIR |
| J12, J32 | General field outputs DO0-DO15 |
| J33 | External isolated field +24 V supply and relay common return |
| J45 | Second parallel +24 V field supply / return connector |
| J13-J15 | Encoders 0-2 |
| J40-J43, J48-J50 | Seven paired ZERO/ERROR/GND input connectors |
| J18 | 5-pin hardware I2C1: SDA, SCL, 3.3 V, 5 V, GND |
| J36 | 1x9 header for Open-Smart 3.3 V TF Card Breakout |
| J20 | Optional ESP-01/ESP-01S |
| J22 | 2x10, 2.00 mm LCD LVDS |
| J24 | Three 0-10 V analog inputs |
| J25 | Four 0-10 V analog outputs |

Detailed connector pinouts are in `documentation/connectors.md`.

## Power and protection

- Main input path: F1 2 A fuse, D1 24 V TVS and one 1 A SS16 series diode.
- D2 provides reverse-polarity protection for the logic-side input; D3 protects
  the isolated backlight-converter feed from J33/J45.
- U1 converts the protected machine input to the 1 A +5 V rail.
- U3 converts the isolated PLC 24 V field rail to `+12V_BL` at up to 1 A.
- The WeAct module receives +5 V and uses its own regulated 3.3 V rail.
- U2 independently supplies board logic, SD and LCD logic at +3V3.
- U34 independently supplies the optional ESP module at +3V3_WIFI.
- U37 supplies only the analog-output amplifier, avoiding a local hot spot.
- J33 and J45 provide parallel access to the external isolated +24 V field rail
  and its single `ISO_GND` return, used for dry-contact wetting and
  relay-output common.

Do not use the analog or isolated field rails to power motors, lamps or
high-current solenoids. General field outputs are limited by their external
supply and the two TBD62083AFG ratings.

## Display and storage

- J22 carries three LVDS data lanes and one clock lane for a 2x10 panel
  interface. Rows 9-10 and pins 17-20 are not connected.
- RN26 and RN27 are fitted as the passive LVDS series path. The DS90LV047A
  driver U41 is removed.
- There is no HDMI connector or HDMI-specific support circuitry.
- The LCD connector has no backlight contact. J2 carries the isolated
  `+12V_BL`, `ISO_GND`, and a 3.3 V `BL_PWM` signal from GPIO35 through R131.
  The external backlight driver must provide PWM isolation.
- High-current backlight switching and the CCFL inverter remain external.
- The microSD card uses 3.3 V SPI and includes card-detect.

## PCB and manufacturing data

| Metric | Value |
|---|---:|
| PCB footprints | 274 |
| Physical BOM components | 270 |
| Routed vias | 112 |
| Minimum configured track width | 0.12 mm |
| Minimum drill | 0.30 mm |

The BOM is in `manufacturing/bom.csv`. This specification is informational and
does not replace the KiCad schematic, PCB, DRC or ERC reports.

## Verification status

The version documented here was checked with KiCad 10.0.1:

- DRC: 233 findings, including 124 open connections, 61 clearance findings,
  56 silkscreen overlaps, 24 starved thermals and minor dangling copper.
- ERC: zero electrical-rule errors and 37 library-symbol cache warnings.
- The routed board is a working prototype variant, not a fabrication release.

These remaining findings must be reviewed before fabrication. The board is not
declared production-ready or safety-certified.
