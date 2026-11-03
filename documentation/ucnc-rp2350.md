# uCNC RP2350 compatibility

This page records the firmware-facing constraints found in the local uCNC
RP2350 source review. The motherboard needs a LeanCam-specific board map; the
stock Pico 2 map does not match these pin assignments.

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
one state machine and one index GPIO. ENC0 is compatible with that implementation.
ENC1 and ENC2 require the backend to be generalized or instantiated three times.

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
types on arbitrary GPIOs and is the complete runtime path for this board.

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
| `ESTOP` | `ESTOP_N` | GPIO9 | 53 | Active low |

E-stop is a direct input outside the shift-register chain. Configure the
LeanCam board map for active-low E-stop and keep the machine's hard-wired
safety energy removal independent of firmware.

## I/O remapping

The physical chain assignments are in
[Input and output bit map](io-bit-map.md). The LeanCam board map must preserve
the U6-U9 input order, U10-U13 output order, paired motion outputs and the three
servo status connectors per axis.

## WeAct preparation

Remove WeAct module resistor R16 before using GPIO23 as the 74HC165 return.
GPIO25 is also connected to the module's onboard LED. GPIO0 is reserved for
optional module PSRAM and must not be assigned to SD or other motherboard I/O.
