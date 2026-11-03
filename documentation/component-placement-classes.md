# Component placement classes

The per-reference manifest is
`hardware/component-placement-manifest.csv`. It records the functional block,
channel, electrical role, associated IC or net, placement rule, board side and
in-board status for each assembly component.

## Mechanical anchors

- MOD1 is the socketed WeAct RP2350B module.
- H1-H4 are the four M3 mounting holes.
- J1, J2, J5, J7/J8, J10-J15, J18, J20, J22, J24/J25, J28-J30, J32/J33,
  J36, J40-J43, J45-J51 and J54 are the physical interfaces.
- J22 is the 2 x 10, 2.00 mm LCD connector on F.Cu.
- J54 is the SOFNG TF-15x15 card socket on F.Cu.

Do not move a connector unless its mating geometry, cable direction and access
to the board edge have been rechecked.

## Main placement rules

1. Keep U1, L1, C3-C7, C11, C86 and C91 in one compact 5 V converter loop.
2. Keep U3, L2, D3, C107-C114 and R126-R128 in one isolated 12 V converter loop.
3. Keep U2 and U34 input/output capacitors local to each regulator.
4. Keep every logic-supply bypass beside its IC supply and ground pins.
5. Keep field input protection, LED and optocoupler parts at J5/J7/J8.
6. Keep PLC pull-up arrays on the logic side of the optocouplers.
7. Keep general-output optocouplers and TBD62083 arrays between U12/U13 and
   J12/J32.
8. Keep motion buffers close to the 74AHCT595 outputs and axis connectors.
9. Keep analog dividers at J24 and analog-output filters between the RP2350 PWM
   pins and J25.
10. Keep SD pull-ups and series arrays at J36/J54.
11. Keep LVDS series arrays at J22 and preserve pair polarity.

## Power blocks

| Block | Associated parts |
|---|---|
| Main input protection | F1, D1, D2, C2 |
| 5 V converter | U1, L1, C3-C7, C11, C86, C91, R70-R72 |
| Isolated backlight converter | U3, L2, D3, C107-C114, R126-R128 |
| Peripheral 3.3 V | U2, C10, C13, C76, C90 |
| ESP 3.3 V | U34, C69, C70, C88, C89 |
| Analog 12 V | U37, C100-C102 |

C3-C5 form the U1 input loop. C6/C11 are output bulk and C7 is the switching
node bypass. C86 bridges BOOT and SW; C91 bypasses the internal VCC. U1 and U3
each have six ground vias under the PowerPAD.

U3 has no `PWR_GOOD` connection. Its input, output and feedback all use the
isolated `ISO_GND` domain.

## Digital input block

U8 carries PLC inputs 1-8 and U9 carries inputs 9-16. U6/U7 carry the paired
servo ZERO/ERROR signals. Each register has a local `+3V3` bypass:

| Register | Bypass |
|---|---|
| U6 | C22 |
| U7 | C23 |
| U8 | C24 |
| U9 | C25 |

U18-U21 are placed with the PLC field chains and four isolated 4 x 10 k pull-up
networks RN32-RN35. Each channel has an LED, 2.2 k field resistor, reverse diode
and optocoupler input. U35 and its small field chain are at J5.

Servo status channels use direct 3.3 V logic. U6/U7 data-pin assignments are in
`documentation/io-bit-map.md`.

## Digital output block

U10-U13 are the cascaded 5 V SN74AHCT595 registers. Their local bypasses are
C29-C26, respectively. OUT0-OUT15 feed the two TC74AC541F motion buffers;
U42 handles OUT0-OUT7 and U43 handles OUT8-OUT15.

General outputs use this chain:

`OUT16-OUT31 -> RN37-RN40 (1 k) -> U61-U64 (TLP291-4) -> U26/U27 TBD62083AFG`

J12 and J32 expose the resulting low-side outputs DO0-DO15. RN8-RN13, RN30 and
RN31 provide 10 k state-definition pull-downs at the register outputs.

## Encoders

U28 receives the nine 5 V A/B/Z signals from J13-J15 and drives 3.3 V levels to
the RP2350. C119 bypasses U28 at its own supply pin. The encoder connector
signals are push-pull; open-collector encoders need external pull-ups.

The A/B pairs are adjacent RP2350 pins as documented in
`documentation/gpio-map.md`.

## Analog input block

All four channels use the same 100 k / 33 k divider and one 100 nF ADC-node
capacitor:

| Channel | Upper | Lower | Filter | RP2350 GPIO / MOD1 pin |
|---|---|---|---|---|
| AI0 | R61 | R63 | C73 | GPIO40 / 8 |
| AI1 | R64 | R66 | C74 | GPIO42 / 7 |
| AI2 | R67 | R69 | C75 | GPIO41 / 22 |
| AI3 | R182 | R183 | C118 | GPIO43 / 21 |

Each group is placed beside its J24 pin rather than at MOD1.

## Analog output block

U38 is the quad TLV2374. Each channel uses:

`PWM -> 10 k / 1 uF -> 10 k / 100 nF -> TLV2374 -> AOUT`

R92-R95 and R96-R99 are the filter resistors. R100-R103 are 22 k feedback
resistors and R104-R107 are 10 k gain-setting resistors. C92/C94/C96/C98 are
the first-stage 1 uF capacitors; C93/C95/C97/C99 are the second-stage 100 nF
capacitors. J25 carries the four outputs and the common ground.

## SD and display

J36 and J54 share the same SPI signals. RN43 provides four 10 k pull-ups and
RN44 provides four 22 ohm series resistors. FB2, C67 and C68 form the
`+3V3_SD` filter beside the storage interface. JP5 enables card detect.

RN26/RN27 are the 4 x 330 ohm HSTX series arrays. They sit beside J22. Keep each
differential pair short and preserve the P/N assignment documented in
`documentation/display-population.md`.
