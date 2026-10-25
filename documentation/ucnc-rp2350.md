# uCNC RP2350 pin compatibility

Checked against the local uCNC source in `tmp/leancam-sources/uCNC`.

## Encoders

There are two relevant uCNC paths:

- the generic encoder module, which uses GPIO interrupts and pulse/dir inputs;
- `modules/rp2350_pio_encoder`, which replaces the backend with one PIO
  quadrature counter.

The RP2350 PIO module requires encoder A at `ENC0_PULSE_GPIO` and encoder B at
the immediately following GPIO. The board's A/B pairs satisfy that requirement:

| Encoder | A / PULSE | B / DIR | Z / INDEX |
|---|---|---|---|
| ENC0 | GPIO26 | GPIO27 | GPIO28 |
| ENC1 | GPIO29 | GPIO30 | GPIO31 |
| ENC2 | GPIO32 | GPIO33 | GPIO34 |

However, the checked-in `rp2350_pio_encoder.c` currently hard-codes one encoder:

- only `ENC0_*` configuration macros exist;
- `enc_custom_read()` returns a count only when `i == ENC0`;
- only one PIO block, state machine, program offset and index GPIO are stored;
- Z/index is handled by a separate GPIO interrupt, not by the PIO program.

Therefore ENC0 is compatible with the module as-is. ENC1 and ENC2 require the
module to be generalized or instanced three times. The hardware already has the
correct adjacent A/B pairs for that work.

The natural three-channel implementation is to place ENC0, ENC1 and ENC2 on
three state machines in one PIO block, all using the same 24-instruction
quadrature program. Their independent `IN_BASE` settings select GPIO26, GPIO29
and GPIO32. The three Z pins can remain GPIO interrupts, as the module already
does for ENC0.

The local `cnc_hal_overrides.h` is also still configured for the previous board:
it sets ENC0 A/B to GPIO20/21 and Z to GPIO26, and enables only one encoder.
That does not match this motherboard's GPIO26/27/28 assignment.

## 74HC165/74HC595 chain

The normal uCNC `shift_register` driver toggles individual GPIOs and supports
both 74HC165 inputs and 74HC595 outputs. It can therefore use this board's
existing pins:

| Function | GPIO | MOD1 pin |
|---|---:|---:|
| `SHIFT_REGISTER_SDO` | GPIO24 | 45 |
| `SHIFT_REGISTER_SDI` | GPIO22 | 44 |
| `SHIFT_REGISTER_CLK` | GPIO20 | 43 |
| `IC74HC595_LATCH` | GPIO35 | 25 |
| `IC74HC165_LOAD` | GPIO21 | 59 |

The current mapping is **not compatible with uCNC's optional
`IC74HC595_CUSTOM_SHIFT_IO` PIO path**. That path:

- handles only the four 74HC595 outputs;
- requires exactly four 595 devices;
- programs DATA, CLK and LATCH as three consecutive pins;
- would require a separate PIO implementation for the 74HC165 inputs.

DATA=GPIO24, CLK=GPIO20 and LATCH=GPIO35 are not consecutive. Use the standard
bit-banged `shift_register` driver unless the hardware map or uCNC PIO code is
changed.

The five shift-register pins fit within one RP2350 PIO GPIO window, so a custom
dual 74HC165/74HC595 PIO program is feasible. It is not the implementation
provided by uCNC.

The current `uCNC-master` target has `IC74HC595_COUNT 0` and
`IC74HC165_COUNT 0`, so it does not currently use either shift-register path.
Enabling both PIO encoders and the stock 595 PIO also requires deliberate
PIO-block, state-machine and program-offset allocation: the encoder module
defaults to PIO0/SM0/offset0, while the 595 PIO path also initializes PIO0/SM0.

## Control inputs

The RP2350 inputs are active-low open-collector outputs from U35/U36/U39:

| uCNC function | Signal | GPIO | MOD1 pin |
|---|---|---:|---:|
| `ESTOP` | `ESTOP_N` | GPIO37 | 24 |
| `FHOLD` | `HOLD_N` | GPIO38 | 9 |
| `CS_RES` | `START_N` | GPIO39 | 23 |

Configure the expected polarity in the custom uCNC board map. `HOLD_N` and
`START_N` are normally-open pushbutton inputs: pressing a button energizes its
optocoupler LED and pulls the RP2350 input low.

The stock Pico 2 board map must not be used unchanged: it assigns step/dir and
other functions to different GPIOs. A LeanCam-specific uCNC board map is needed.
