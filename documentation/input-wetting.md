# Isolated PLC input wetting

The optocoupled input stage is fixed for dry-contact field loops powered from
the external isolated 24 V field supply. No input-mode selectors are fitted.
The RP2350 side remains galvanically isolated because `+24V_FIELD` and
`ISO_GND` have no connection to motherboard `GND`.

## Field supply

J33 and J45 are electrically parallel two-pin connections:

| Pin | Net | Function |
|---:|---|---|
| 1 | `+24V_FIELD` | External isolated 24 V field supply |
| 2 | `ISO_GND` | Single isolated field return |

Either connector can supply the field domain. The second connector provides a
parallel terminal for convenient wiring or looping to another enclosure
connection; it is not an additional logic supply and must not be connected to
motherboard GND.

The same field supply feeds the 16 PLC contact loops, the isolated servo
diagnostic channels and the relay-output common. The onboard isolated DC/DC
converter and its support components are removed.

## Field wiring

Each J7/J8 input pin is one side of a normally open dry-contact loop. Wire the
other side of every contact to `+24V_FIELD` from J33 or J45. The optocoupler
cathode and reverse-protection diode return through the shared `ISO_GND` pin.
J7/J8 therefore carry signals only; duplicate return pins are not provided on
the input connectors.

The dedicated E-stop loop on J5 uses the same `ISO_GND` field return. It drives
GPIO9 on MOD1 pin 53 directly and remains outside the shift-register chain.

## Input current

Each channel retains one 2.2 k field-side series resistor. With approximately
3 V total LED drop at 24 V, the nominal loop current is about 9.5 mA.

The TLP291-4 channels are rated for this current. If the selected optocoupler
shipment has lower-than-expected CTR, use a 1.8-2.0 k 1206 resistor or two
3.6 k 1206 resistors in parallel. Do not fit the lower value in addition to the
nominal resistor.
