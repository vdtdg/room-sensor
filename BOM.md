# Bill of materials

Quantities are for one unit. Component links are provided below; check the
selected variant when ordering. Prices, enclosure hardware, and print
requirements still need confirmation.

| Qty | Part | Requirements / status |
| --- | --- | --- |
| 1 | [ESP32-C3 development board](https://fr.aliexpress.com/item/1005008234672660.html) | Firmware uses `esp32-c3-devkitm-1` with ESP-IDF. Confirm the physical board and enclosure fit. |
| 1 | [SCD41 CO₂, temperature, and humidity sensor module](https://fr.aliexpress.com/item/1005008661290129.html) | I²C breakout, supported by ESPHome's `scd4x` component. |
| 1 | [SSD1306 OLED module](https://fr.aliexpress.com/item/1005006038663076.html) | 128 × 64 pixels, I²C address `0x3C`. Confirm module dimensions before printing. |
| As needed | Wire / connectors | Shared I²C bus plus power and ground. Lengths and connector types to confirm. |
| 1 | Suitable power supply and cable | Match the development board's documented input. Connector and rating to confirm. |
| 1 set | Printed enclosure | Models and printing notes in [`models/`](models/). |


## Wiring

Both modules share the I²C bus (SDA and SCL), along with the same 3.3 V supply and ground:

```text
ESP32-C3      SCD41       SSD1306

3V3  ─────── VCC ─────── VCC
GND  ─────── GND ─────── GND
GPIO0 ────── SDA ─────── SDA
GPIO1 ────── SCL ─────── SCL
```
