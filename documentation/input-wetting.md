# Isolated PLC input wetting

The optocoupled input stage supports two field-wiring modes without changing
the motherboard resistor population:

- External 24 V wetting supply.
- Dry contacts powered by the onboard isolated 12 V supply.

The RP2350 side remains galvanically isolated because `+12V_FIELD` and
`ISO_GND` have no connection to motherboard `GND`.

## Isolated supply

`U40` is a Traco Power `TBA2-0512`: 5 V input, isolated 12 V output, 2 W
(approximately 167 mA). This covers 24 active channels at about 4.5 mA each
with margin. `F4` is the 750 mA primary fuse.

`D56` is an `SS54` Schottky diode in series with the converter output. It
blocks current from the field rail back into the converter. C103 is the 10 uF
primary bulk capacitor; C105 is the 10 uF, 100 V isolated-output capacitor.

U40, D56, F4, C103 and C105 are on F.Cu in the relocated bottom-left power
area near the encoder interface.

## One selector per input bank

Each field bank has one 2.54 mm three-pin header. Fit one removable shunt across
the required pair. The center pin is the isolated field common:

| Jumper | Input bank |
|---|---|
| JP2 | J7, eight PLC inputs |
| JP3 | J8, eight PLC inputs |
| JP4 | E-stop, HOLD and START |

Configuration:

| Pads bridged | Mode |
|---|---|
| 1-2 | External 24 V: field common connected to `ISO_GND` |
| 2-3 | `CONTACT`: field common connected to protected isolated `+12V_FIELD` |

Only one pair can be bridged on a three-pin selector. In 24 V mode the isolated
12 V rail is disconnected from the field common; D56 additionally blocks any
backfeed into U40. In `CONTACT` mode, an external dry contact merely shorts the
odd signal pin to its adjacent even common and the board supplies the isolated
loop current.

## Input current

The existing 2.2 k series resistor is retained for both modes. With about 3 V
total LED drop:

- 24 V mode: approximately 9.5 mA.
- Isolated 12 V mode, allowing about 0.5 V for D56: approximately 3.9 mA.

The LTV-847S channels are rated for these currents. If the selected
optocoupler shipment has lower-than-expected CTR at 12 V, use a 1.8-2.0 k
1206 resistor or two 3.6 k 1206 resistors in parallel. This remains one
resistor population, not a second switchable bank.
