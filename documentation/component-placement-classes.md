# Component placement classes

The complete per-reference manifest is
`hardware/component-placement-manifest.csv`. It covers every physical component
and records:

- functional block;
- associated analog/field/motion channel;
- electrical role;
- associated IC or net;
- placement rule;
- board side and current parked/inside status.

## Placement priority

The current complete placement uses a 0.5 mm grid for all in-board ICs,
passives, connectors and the controller module. Mounting holes remain fixed.

1. Mechanical anchors: J1-J26, MOD1, H1-H4.
2. Switching-power loops: U1, L1, input/output capacitors and feedback network.
3. Local IC decoupling: 100 nF from supply to GND at the associated IC pins.
4. Safety channels: optocoupler, LED, reverse diode, resistors and filter.
5. Analog channels: divider and ADC filter grouped beside J24.
6. Analog-output channels: place the PWM filter chain from R92-R99 through
   C92-C99 into U38, then toward J25; keep C102 at U38 supply pins.
7. Digital channel banks: shift registers, buffer/ULN channels and series arrays.
8. Connectors and optional display populations.

## Main categories

| Category | Placement rule |
|---|---|
| Buck input/output capacitors | Keep regulator current loops compact |
| Bootstrap capacitor | Place directly between BOOT and SW |
| IC decoupling capacitor | Within 3 mm of the VCC and GND pins |
| ADC filter capacitor | Group beside J24 with the associated analog channel |
| Analog-output filter | Keep R92-R99 and C92-C99 grouped between U38 and J25 |
| Analog-output gain | Keep R100-R107 close to the corresponding U38 feedback pins |
| Analog divider | Group the 100 k/33 k divider by channel at J24 |
| Isolated input channel | Keep field-side resistor/LED/reverse-diode group together at its connector and preserve isolation |
| Isolated wetting supply | U40, D56, F4, C103 and C105 are in the F.Cu power area near the encoder interface; no secondary net may touch GND |
| Input-mode selectors | JP2-JP4 are one 3-pin, 2.54 mm header per field bank on B.Cu |
| Safety input optocoupler | Place the individual EL3H7 close to its J5/J6 field chain and pull-up |
| PLC pull-up | Place the individual 4.7 k resistor beside its optocoupler collector on the U9 branch |
| Shift-register decoupling | C22-C29 sit immediately right of their respective U6-U13 VCC pins; ground via on the outer pad |
| Motion output array | Group source, pull-down, 100 ohm array and its connector; keep buffers between U10-U13 and J10-J11 |
| ULN output | Group both ULN banks, clamp rail, existing indicator chains, J12 and J32 |
| Encoder channel | Keep U28 between J13-J15 and the MCU with C57 at its supply; keep R110/R111 at J15 for the ENC2_Z divider |
| Keyboard matrix | J16, RN20/RN21 and RN22/RN24 stay on F.Cu away from the bottom edge; KOUT arrays sit above J16 and KIN arrays below |
| Expansion inputs | J9 and J27 flank U7 on F.Cu; each carries GND, +3V3 and four inputs |
| Display option | J22 driven by U41/C106 active LVDS; RN26/RN27 are the mutually exclusive passive-LVDS alternative |
| Fixed mechanical part | Do not move without explicit approval |

## Analog input block

All three analog inputs use the approved AI0 template on F.Cu:

| Ref | Role | Associated node |
|---|---|---|
| R61 | 100 k divider upper resistor | AI0 to AI0_ADC |
| R63 | 33 k divider lower resistor | AI0_ADC to GND |
| C73 | 100 nF ADC filter | AI0_ADC / MOD1 pin 8 |
| R64 / R66 / C74 | AI1 equivalent divider/filter | AI1_ADC / MOD1 pin 22 |
| R67 / R69 / C75 | AI2 equivalent divider/filter | AI2_ADC / MOD1 pin 7 |

Each three-part group is aligned to its corresponding J24 input pin.

## Analog output block

U38 is a single TLV2374 quad op-amp. R92-R95 and R96-R99 are the two individual
10 k filter stages per channel. R100-R103 are the 22 k feedback resistors and
R104-R107 are the 10 k gain-setting resistors. C92/C94/C96/C98 are the 1 uF
first-stage capacitors; C93/C95/C97/C99 are the 100 nF second-stage capacitors.

The entire front-side signal block is grouped between the RP2350 and J25.
C100 is placed at U37 input, C101 at its 12 V output and C102 near U38 supply.
J25 remains the front-side mechanical anchor at the board edge. The U38
placement was moved down to shorten the output and feedback paths. The four PWM
channel assignments were checked as
equivalent op-amp channels. Swapping physical channels 0 and 1 would save only
0.6 mm while changing the documented mapping, so AOUT0-AOUT3 remain unchanged.

## Power completion and indicators

The final main-power placement pass keeps the high-current loops local:

- C6/C11 form the 5 V output bulk capacitance and C7 provides local
  high-frequency bypass at U1. Redundant C8, C16, C17 and C77 are removed.
- C88/C89 and C69/C70 are grouped around U34 for the ESP-01/ESP-01S input and output
  rails.
- U41, the active DS90LV047A LVDS driver, and its C106 bypass are grouped
  between the HSTX source and J22.
- FB1 and C15 form the `+3V3_A` reference filter at MOD1 pin 48. The redundant
  10 uF C14 bulk capacitor is removed.
- R73 is the 100 k `PWR_GOOD_N` pull-up between U1 and GPIO43.
- D4/R4 indicate +5 V and D5/R5 indicate +3.3 V. Both pairs are placed in the
  open area between MOD1 and the regulators.

## Isolated input block

U17 was the original two-channel safety quad. Its E-stop channel became U35,
the former fault channel became the HOLD input U36, and the new START input uses
U39. U18-U21 remain four-channel LTV-847S packages for PLC inputs 1-16.

All 18 isolated field inputs use the same functional chain:

`connector input -> 2.2 k series resistor -> indicator LED -> optocoupler LED ->
reverse diode to ISO_GND`

The 16 PLC chains follow the nearest J7/J8 rows: J7 positions 1-8 feed logical
channels 9-16 and J8 positions 1-8 feed logical channels 1-8. The two dedicated
safety chains are grouped beside J5 and J6. The four optocoupler output banks
are also wired to their nearest 74HC165 data pins. Both permutations are fixed
in `documentation/io-bit-map.md` for firmware. Each optocoupler output has an
individual 4.7 k pull-up. No input-node capacitors are fitted; input debouncing
belongs in firmware.


## SD card interface

J19 remains the right-edge mechanical anchor. Its passives use three front-side
ranks in the 22 mm corridor between MOD1 and J19:

- R50-R54 are the five series resistors closest to J19 and align to the SCK,
  MOSI, MISO, CS and card-detect pins.
- R44-R49 are the six 10 k pull-ups on the next rank, grouped by their
  corresponding signal pin.
- FB2, C68 and C67 form the `+3V3` to `+3V3_SD` filter and local reservoir
  beside the connector power pin.

No SD signal passes through an ESD array; the card is enclosed and the approved
interface uses the five series resistors plus pull-ups.
