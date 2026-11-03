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

The op-amp is configured as a non-inverting gain stage. Its push-pull output
drives J25 directly; calibration is performed digitally.

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
| AO0 | GPIO44 | 6 | 2 |
| AO1 | GPIO46 | 5 | 3 |
| AO2 | GPIO45 | 20 | 4 |
| AO3 | GPIO47 | 19 | 5 |

J25 pin 1 is the common ground return. These are ground-referenced outputs, not
isolated outputs. AO0, AO1 and AO3 use MOD1 pins 6, 5 and 19 respectively;
the corresponding GPIO assignments are recorded in the firmware GPIO map.

Use the WeAct module's onboard LED; no separate status LED is connected to the
analog-output GPIOs.

## Power

U37 is an L78L12 100 mA linear regulator from `VIN_P`. Its expected load is
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
