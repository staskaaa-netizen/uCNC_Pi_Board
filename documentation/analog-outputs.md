# Four-channel 0-10 V analog output

## Signal path

Each channel reproduces the approved two-stage PWM filter and adds the gain
required for an RP2350 output:

```text
AOUTn_PWM (3.3 V)
  -> 10 k
  -> AOUTn_F1 -- 1 uF -> GND
  -> 10 k
  -> AOUTn_F2 -- 100 nF -> GND
  -> TLV2374 + input
  -> AOUTn
```

The op-amp feedback is 22 k from `AOUTn` to `AOUTn_FB`, with 10 k from
`AOUTn_FB` to GND. This gives:

```text
gain = 1 + 22 / 10 = 3.2
```

With 3.3 V PWM logic, use a maximum duty cycle near 94.7% for a 10.0 V output.
Leave the remaining range for calibration and supply tolerance.

The supplied drawing showed the op-amp output tied back to its inverting input
and a 10 k pull-up to +12 V. That is a unity-gain buffer, or an open-collector
comparator output, and cannot linearly convert a 3.3 V PWM duty cycle into
0-10 V. The implementation therefore omits the pull-up and unused trim/threshold
network, uses the TLV2374 push-pull output, and performs calibration digitally.

All signal resistors are individual 1% 0805 parts. No resistor networks are
used in this block:

| References | Value | Function |
|---|---:|---|
| R92-R95 | 10 k | First 1 uF filter stage |
| R96-R99 | 10 k | Second 100 nF filter stage |
| R100-R103 | 22 k | Feedback from output to inverting input |
| R104-R107 | 10 k | Feedback divider from inverting input to GND |

## GPIO and connector mapping

| Channel | RP2350 GPIO | MOD1 pin | J25 pin |
|---|---:|---:|---:|
| AOUT0 | GPIO47 | 19 | 2 |
| AOUT1 | GPIO44 | 6 | 3 |
| AOUT2 | GPIO45 | 20 | 4 |
| AOUT3 | GPIO46 | 5 | 5 |

J25 pin 1 is the common ground return. These are ground-referenced outputs, not
isolated outputs. MOD1 pins 34 and 19 are intentionally swapped relative to the
previous revision: GPIO2 now carries SD-card detect, while GPIO47 drives AOUT0.

The external status LED formerly on GPIO46 is removed. Use the WeAct module's
onboard LED; it is already fitted to the module.

## Power

U37 is an L78L12 100 mA linear regulator from `VIN_PROT`. Its expected load is
the TLV2374 quiescent current plus the feedback dividers and connected
high-impedance analog loads, typically only a few milliamps. At a 24 V input,
3 mA total load dissipates approximately 36 mW in U37.

- C100: 22 uF / 50 V at U37 input
- C101: 22 uF / 50 V at U37 output
- C102: 100 nF directly at U38 supply/GND

Do not short an output to ground or a 24 V field rail. The op-amp has internal
current limiting, but persistent faults are outside its thermal design.

## Firmware notes

- Drive all four outputs from the same PWM peripheral or synchronised PIO
  program. A 20 kHz carrier is the initial value.
- Use the calibrated relation `duty = target_voltage / 10.56`, clamped to the
  measured safe maximum.
- Disable the PWM outputs or force 0% duty when the machine is disabled; these
  analog outputs are not part of the isolated E-stop safety loop.
