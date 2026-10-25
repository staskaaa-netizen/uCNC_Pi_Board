# Analog input and output calibration

## Inputs AI0-AI2

Each input uses a 100 k upper divider and a 33 k lower divider:

```text
Vadc = Vin * 33 / (100 + 33)
Vin  = Vadc * 133 / 33
```

At 10.0 V, the ADC node is nominally 2.481 V. This leaves margin below the
RP2350B ADC reference.

Each ADC node has one 100 nF capacitor to the continuous `GND` plane. The
complete divider/filter group is placed beside J24 rather than the RP2350
module. This keeps the MCU area available for the dense digital buses. There is
no TVS, bypass link, or series ADC resistor in this minimum configuration. The
divider resistors are 1% 1206 parts.

Use the module's filtered `REFP`/ADC reference and calibrate each channel at two
points, for example 1 V and 9 V. Store gain and offset per channel.

## Outputs AOUT0-AOUT3

GPIO2, GPIO44, GPIO45 and GPIO46 generate the four PWM signals. Each channel
uses the requested two-stage low-pass filter:

```text
PWM -> 10 k / 1 uF -> 10 k / 100 nF -> TLV2374 non-inverting input
```

The unused connection in the supplied reference drawing was a unity-gain
follower, which cannot turn 3.3 V PWM into 10 V. The implemented feedback is
22 k from output to inverting input and 10 k from inverting input to GND:

```text
gain = 1 + 22 k / 10 k = 3.2
Vout = 3.2 * D * Vpwm
```

At a 3.3 V PWM high level, the ideal full-scale output is 10.56 V. Limit the
usable duty cycle to approximately 94.7% and calibrate the maximum command
against J25 channel by channel. A 20 kHz PWM carrier gives about 10 ms and 1 ms
filter time constants; change the carrier only after checking settling time,
ripple and the target VFD input.

U38 is a TLV2374 rail-to-rail quad op-amp. U37 derives its local 100 mA,
`+12V_AO` rail from `VIN_PROT`; 24 V board input is required for guaranteed
0-10 V output range. C100 is the regulator input bypass, C101 is the 12 V rail
reservoir and C102 is the op-amp bypass. J25 pin 1 is the common ground return;
pins 2-5 are AOUT0-AOUT3.
