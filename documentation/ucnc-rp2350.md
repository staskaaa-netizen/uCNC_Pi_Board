# uCNC RP2350 compatibility

This page records the firmware-facing constraints found in the local uCNC
RP2350 source review. The implemented board map is
`src/hal/boards/rp2350/boardmap_leancam_ncc_rp2350b.h`; both LVDS machine
environments select it.

## Encoders

The uCNC RP2350 PIO encoder backend requires the quadrature pair on adjacent
GPIOs, with the PULSE input at the configured base and DIR at the next GPIO.
The board provides three adjacent A/B pairs:

| Encoder | A / PULSE | B / DIR | Z / INDEX |
|---|---|---|---|
| ENC0 | GPIO33 | GPIO32 | GPIO31 |
| ENC1 | GPIO30 | GPIO29 | GPIO28 |
| ENC2 | GPIO27 | GPIO26 | GPIO25 |

The reviewed `rp2350_pio_encoder.c` implements one encoder only: one PIO block,
one state machine and one index GPIO. The machine map configures ENC0 on the
ascending GPIO32/GPIO33 pair. GPIO32 is the carrier's B phase, so the backend
sets `ENC0_RP2350_ENCODER_INVERT 1`; GPIO31 is the physical index. ENC1 and
ENC2 still require the backend to be generalized or instantiated separately.

The current machine build uses three axes (`AXIS_COUNT 3`, A0-A2). The carrier
and shift-register map retain their seven-axis physical documentation, but the
unused A3-A6 motion interfaces are not part of the firmware configuration.

The machine map also assigns uCNC's existing `ACTIVITY_LED` heartbeat
(`DOUT31`) directly to GPIO25, which is the WeAct module's active-high onboard
LED. This uses the GPIO25 output for the live heartbeat, so ENC2 index cannot
also be configured in the same firmware build.

A practical three-channel implementation is one state machine per encoder in one
PIO block, using GPIO32, GPIO29 and GPIO26 as the three A/B input bases. Keep
the Z inputs on GPIO interrupts as the existing module does.

The generic uCNC encoder backend uses GPIO interrupts and is not restricted to
adjacent pins. Either backend can use this hardware layout, but the LeanCam board
map must preserve the A/B polarity used by the selected driver.

## Shift registers

The hardware interface is:

| Function | GPIO | MOD1 pin |
|---|---:|---:|
| 74AHCT595 serial data / PIO DATA | GPIO20 | 43 |
| Shared clock / PIO CLK | GPIO21 | 59 |
| 74AHCT595 latch / PIO LATCH | GPIO22 | 44 |
| 74HC165 serial return | GPIO23 | 60 |
| 74HC165 parallel load | GPIO24 | 45 |

The standard uCNC bit-banged `shift_register` driver supports both register
types on arbitrary GPIOs and is the complete runtime path for this board. The
machine map enables four registers in each direction, including the A4/A6
non-sequential motion bits and the two shared enable bits.

The optional `IC74HC595_CUSTOM_SHIFT_IO` PIO path can use GPIO20/21/22 because
they are contiguous and in the required DATA, CLK, LATCH order:

```c
#define IC74HC595_CUSTOM_SHIFT_IO
#define IC74HC595_PIO_DATA 20
#define IC74HC595_PIO_CLK 21
#define IC74HC595_PIO_LATCH 22
#define IC74HC595_COUNT 4
```

That driver handles the four outputs only. It does not read the four 74HC165
input registers. Use the bit-banged combined path, or add a separate custom PIO
input scanner, before selecting the output-only PIO path for the full machine
I/O interface.

The encoder PIO backend and the 595 PIO path both claim one PIO block/state
machine by default. A combined firmware must allocate distinct PIO resources
and program offsets deliberately.

## E-stop

| uCNC function | Signal | GPIO | MOD1 pin | Polarity |
|---|---|---|---:|---|
| `ESTOP` | `ESTOP` | GPIO9 | 53 | Active low |

E-stop is a direct input outside the shift-register chain. The board map uses
uCNC's `INVERT_EMERGENCY_STOP` because U35 pulls GPIO9 low when the isolated
loop is energized. Keep the machine's hard-wired safety energy removal
independent of firmware.

## I/O remapping

The physical chain assignments are in
[Input and output bit map](io-bit-map.md). The LeanCam board map preserves the
U6-U9 input order, U10-U13 output order, paired motion outputs and the servo
status connectors per axis.

Axis IDs follow the top-to-bottom connector order: A0-A3 use J10/J11/J28/J29,
A4 uses J47/J50, A5 uses J46/J49 and A6 uses J30/J48. The STEP/DIR bits for A4
and A6 are therefore not sequential; use the bit table directly.

## WeAct preparation

Remove WeAct module resistor R16 before using GPIO23 as the 74HC165 return.
GPIO25 is also connected to the module's onboard LED. GPIO0 is reserved for
optional module PSRAM and must not be assigned to SD or other motherboard I/O.
