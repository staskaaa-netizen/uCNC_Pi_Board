# Optional ESP-01 / ESP-01S Wi-Fi

The motherboard operates without a Wi-Fi module. J20 is a 2 x 4, 2.54 mm
female socket for the original ESP-01 or ESP-01S.

| Pin | Signal |
|---:|---|
| 1 | GND |
| 2 | ESP TX / GPIO1 → RP2350 UART RX |
| 3 | ESP GPIO2 |
| 4 | EN/CH_PD |
| 5 | ESP GPIO0 |
| 6 | RST |
| 7 | ESP RX / GPIO3 → RP2350 UART TX |
| 8 | `WIFI_3V3` |

U34 is a dedicated AMS1117-3.3 regulator from `5V`. C88 provides input
reservoir; C69 provides local output reservoir. This
supports the ESP8266 transmit-current pulse without loading U2.

For UART programming, ground ESP GPIO0 externally, reset the module, release
GPIO0 and program through the socket. No on-board ESP programming button is
fitted.

Keep the antenna end toward the board perimeter with at least 15 mm of copper-
and component-free clearance. Verify module pin-1 orientation before insertion;
clone boards can present a reversed socket view.
