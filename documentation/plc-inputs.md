# PLC inputs

The PLC inputs are isolated dry-contact loops powered from `PLC 24+` and
`PLC -`. The PLC domain is separate from motherboard GND.

## PLC supply

J33 and J45 are parallel two-pin access points:

| Pin | Net | Function |
|---:|---|---|
| 1 | `PLC_24V` | PLC 24+ |
| 2 | `PLC_0V` | PLC - |

Either connector can feed the field domain. The second connector is useful for
looping the supply to another enclosure terminal. Never connect `PLC_0V` to
logic GND.

The same field domain supplies the PLC contact loops, the E-stop loop, the
general-output optocouplers and the isolated backlight converter.

## Wiring

Each J7/J8 pin is one side of a dry-contact loop. Wire the other side of the
contact to `PLC_24V` from J33 or J45. The optocoupler input current returns
through the shared `PLC_0V`.

The dedicated E-stop loop on J5 uses the same field return. Its optocoupler
output drives GPIO9 on MOD1 pin 53 and is outside the shift-register chain.

Each input contains:

`connector -> LED -> 2.2 k -> optocoupler LED -> reverse diode -> PLC -`

U18-U21 provide the sixteen PLC channels. U35 provides the E-stop channel.
RN32-RN35 provide logic-side 10 k pull-ups, and R74 pulls up the E-stop output.
There are no input-node filter capacitors; debounce in firmware or at the
contact/field wiring level.

## Current

With approximately 3 V total LED drop at 24 V, the nominal 2.2 k loop current
is about 9.5 mA. Confirm optocoupler CTR and saturation over temperature before
production.

If a selected optocoupler batch needs more LED current, reduce the series value
to no less than 1.8 k and verify total package dissipation. Do not fit a second
parallel resistor in addition to the nominal part.
