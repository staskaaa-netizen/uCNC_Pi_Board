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

1. Mechanical anchors: remaining fitted connectors J1-J36, MOD1, H1-H4.
2. Switching-power loops: U1/L1 for +5 V and U3/L2 for isolated +12 V,
   including their input/output capacitors and feedback networks.
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
| Buck input/output capacitors | Keep both the U1 5 V and U3 isolated 12 V loops compact |
| Bootstrap capacitor | Place directly between each regulator's BOOT and SW pins |
| IC decoupling capacitor | Within 3 mm of the VCC and GND pins |
| ADC filter capacitor | Group beside J24 with the associated analog channel |
| Analog-output filter | Keep R92-R99 and C92-C99 grouped between U38 and J25 |
| Analog-output gain | Keep R100-R107 close to the corresponding U38 feedback pins |
| Analog divider | Group the 100 k/33 k divider by channel at J24 |
| Isolated input channel | Keep field-side resistor/LED/reverse-diode group together at its connector and preserve isolation |
| External field supply | J33/J45 supply parallel `+24V_FIELD` and `ISO_GND`; no field-domain net may touch logic GND |
| Safety input optocoupler | Place the TLP291 SOP-4 close to the J5 field chain and discrete pull-up |
| PLC pull-up | Place one 4x10 k network per four TLP291-4 collector outputs on the logic side |
| Shift-register decoupling | C22-C29 sit immediately right of their respective U6-U13 VCC pins; ground via on the outer pad |
| Shift-control state definitions | RN41 is reserved but marked DNP pending a keep/remove review |
| Motion output array | Group source and pulldowns; keep U42/U43 between U10-U13 and J10/J11/J28-J30/J46/J47 |
| ULN output | Group both ULN banks, clamp rail, existing indicator chains, J12 and J32 |
| Encoder channel | Keep U28 between J13-J15 and the MCU; keep R110/R111 at J15 for the ENC2_Z divider |
| Backlight power | Keep U3, L2, D3, C107-C114 and R126-R128 together; keep 2-pin J2 at an accessible edge |
| Display option | J22 driven through the fitted RN26/RN27 passive LVDS path |
| Fixed mechanical part | Do not move without explicit approval |

## Analog input block

All three analog inputs use the approved AI0 template on F.Cu:

| Ref | Role | Associated node |
|---|---|---|
| R61 | 100 k divider upper resistor | AI0 to AI0_ADC |
| R63 | 33 k divider lower resistor | AI0_ADC to GND |
| C73 | 100 nF ADC filter | AI0_ADC / MOD1 pin 8 |
| R64 / R66 / C74 | AI1 equivalent divider/filter | AI1_ADC / MOD1 pin 7 |
| R67 / R69 / C75 | AI2 equivalent divider/filter | AI2_ADC / MOD1 pin 22 |
| R182 / R183 / C118 | AI3 equivalent divider/filter | AI3_ADC / MOD1 pin 21 |

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
channel assignments were checked as equivalent op-amp channels. A later source
pin remap moved AOUT0, AOUT1 and AOUT3 to MOD1 pins 6, 5 and 19 respectively;
no analog component or connector placement changed.

## Power completion and indicators

The final main-power placement pass keeps the high-current loops local:

- C6/C11 form the 5 V output bulk capacitance and C7 provides local
  high-frequency bypass at U1. Redundant C8, C16, C17 and C77 are removed.
- C88/C89 and C69/C70 are grouped around U34 for the ESP-01/ESP-01S input and output
  rails.
- RN26/RN27 provide the passive LVDS series path between the HSTX source and
  J22. U41 and C106 are removed.
- FB1 and C15 form the `+3V3_A` reference filter at MOD1 pin 48. The redundant
  10 uF C14 bulk capacitor is removed.
- R73 is the 100 k `PWR_GOOD_N` pull-up between U1 and GPIO3/MOD1 pin 50.
- D4/R4 indicate +5 V and D5/R5 indicate +3.3 V. Both pairs are placed in the
  open area between MOD1 and the regulators.

Place D2 and D3 at their respective protected inputs. Keep U3, L2,
C107-C114 and R126-R128 as one short-loop isolated converter block. Keep the
2-pin isolated J2 power output at an accessible board edge.

## Isolated input block

U35 is a single-channel TLP291 for E-stop only. The HOLD and START inputs are
removed. U18-U21 handle PLC inputs 1-16. The isolated servo diagnostics are
removed; U6/U7 handle paired ZERO/ERROR inputs, while U8/U9 handle PLC inputs.

All 17 isolated field inputs use the same functional chain:

`connector input -> indicator LED -> 2.2 k series resistor -> optocoupler LED ->
reverse diode to ISO_GND`

The 16 PLC chains follow physical left-to-right channel order: J7 positions
1-8 feed logical channels 1-8 and J8 positions 1-8 feed logical channels
9-16. The E-stop chain
is grouped beside J5. The six optocoupler output banks
are also wired to their nearest 74HC165 data pins. Both permutations are fixed
in `documentation/io-bit-map.md` for firmware. RN32-RN35 provide 4x10 k
PLC pull-ups; RN6/RN7 pull up the isolated servo inputs and the E-stop output
retains one 4.7 k resistor. No
input-node capacitors are fitted; input debouncing belongs in firmware.
RN35/RN34/RN33/RN32 correspond to groups 1-4, 5-8, 9-12 and 13-16, with
each network's signal pins mirrored in `4-3-2-1` order.


## SD card interface

J36 is a 1x9 header for the passive Open-Smart 3.3 V TF Card Breakout. It must
be powered from `+3V3_SD`; do not fit a 5 V breakout variant. The full-size J19
and motherboard microSD sockets are removed. The SD passives remain grouped in
the former storage corridor:

- RN44 is the isolated four-element 22 ohm series array for the SCK, MOSI,
  MISO and CS pins. JP5 is the open two-pad card-detect solder jumper.
- RN42 and RN43 provide the six required 10 k pull-ups, with two spare
  elements on RN42.
- FB2, C68 and C67 form the `+3V3` to `+3V3_SD` filter and local reservoir
  beside the connector power pin.

No SD signal passes through an ESD array; the card is enclosed and the approved
interface uses the four RN44 series elements plus pull-ups.
