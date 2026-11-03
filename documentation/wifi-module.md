# Optional ESP-01 / ESP-01S Wi-Fi

The motherboard operates without a Wi-Fi module. J20 is a 2 x 4, 2.54 mm
female socket for the original ESP-01 or ESP-01S.

| Pin | Signal |
|---:|---|
| 1 | GND |
| 2 | `WIFI_3V3` |
| 3 | ESP GPIO2 |
| 4 | ESP GPIO0 |
| 5 | RP2350 GPIO11 `UART_RX` to ESP TX |
| 6 | RP2350 GPIO10 `UART_TX` to ESP RX |
| 7 | EN/CH_PD |
| 8 | RST |

RN36 provides 4 x 10 k pull-ups on ESP GPIO2, GPIO0, EN and RST. Its supply
reference is `WIFI_3V3`, so the ESP pins do not backfeed the motherboard
`3V3` rail when the ESP regulator is unpowered.

U34 is a dedicated AMS1117-3.3 regulator from `5V`. C88/C89 provide input
reservoir and bypass; C69/C70 provide local output reservoir and bypass. This
supports the ESP8266 transmit-current pulse without loading U2.

For UART programming, ground ESP GPIO0 externally, reset the module, release
GPIO0 and program through the socket. No on-board ESP programming button is
fitted.

Keep the antenna end toward the board perimeter with at least 15 mm of copper-
and component-free clearance. Verify module pin-1 orientation before insertion;
clone boards can present a reversed socket view.
