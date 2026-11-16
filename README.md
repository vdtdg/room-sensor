# ESPHome room sensor

An ESP32-C3 with an SCD4x sensor and a 128 × 64 OLED, integrated with Home
Assistant through ESPHome.

The screen shows room name, time, temperature (°C), humidity (%), and CO₂ (ppm).

<img src="photos/IMG_4729.jpg" alt="Finished green room monitor with a white lid, displaying CO₂, temperature, and humidity" width="640">

*Finished build in its printed enclosure. The photo shows an earlier display
layout; the current firmware uses the layout described below.*

## Build

- [Bill of materials and wiring](BOM.md)
- [Enclosure models and print notes](models/)
- [Finished-build photos](photos/)

### Inside the enclosure

<img src="photos/IMG_4722.jpg" alt="Open enclosure showing the internal wiring, electronics, and printed divider, with the lid removed" width="480">

*Lid removed, showing the component placement and internal wiring.*

### Multiple units

I built 10 units to monitor conditions throughout my house. Collecting data
over time will help me plan future renovations.

<img src="photos/IMG_4748.jpg" alt="Seven assembled room monitors with orange enclosures and white lids" width="640">

*A batch of assembled units in orange and white.*

## Firmware setup

Install [ESPHome](https://esphome.io/guides/installing_esphome/) and OpenSSL.
The configuration has been validated with ESPHome **2026.9.1**.

1. Copy the credentials template:

   ```bash
   cp secrets.example.yaml secrets.yaml
   openssl rand -base64 32
   ```

2. Edit `secrets.yaml` with your Wi-Fi credentials and the generated API key.
   The template key is intentionally invalid. Keep this file private.
3. In `room-sensor.yaml`, set a unique `device_name` and a short `display_name`.
   Verify the board, GPIO pins, and display model in `common.yaml` and
   `display.yaml` against your hardware.
4. Connect the ESP32 by USB, then validate and flash:

   ```bash
   esphome config room-sensor.yaml
   esphome run room-sensor.yaml
   ```

5. Add the ESPHome device in Home Assistant, using the same API encryption key.

Wi-Fi uses DHCP. No personal network addresses or room inventory are included.
OTA updates use ESPHome encryption, reusing the API key. Keep the same key for
routine firmware updates. For multiple devices, use separate config files with
unique names and separate API keys referenced through `!secret`.

The clock synchronizes from Home Assistant and displays `--:--` until available.
Missing sensor readings display `--`. Five-digit CO₂ values use smaller text.

### Temperature compensation

`common.yaml` retains the existing build's `4.0` °C SCD4x temperature offset.
This is not a universal calibration value. Compare your assembled unit with a
reference thermometer and adjust `temperature_offset` for your enclosure.
Override it under `substitutions` in `room-sensor.yaml` if needed. In my build,
most sensors needed a temperature offset of 4.5 °C.

## Checks

With Python, PyYAML, and a C++17 compiler installed:

```bash
python tests/test-config.py
python tests/test-display.py
```

Extended checks require ESPHome, Pillow, and Roboto downloaded by ESPHome:

```bash
esphome config room-sensor.yaml
python tests/test-config.py --eval
python tests/test-display.py --eval
```

The configuration evaluation creates disposable credentials in a temporary
directory, never reading your real `secrets.yaml`. All evaluation cases must
pass. Display evaluation covers boundary readings and text fit.

Enable the local gate tests before committing:

```bash
git config core.hooksPath .githooks
```

## Before publishing

- Print settings are embedded in the 3MF; add any additional assembly notes.
- Strip metadata and check for visible private details in any new photos
  (the three included photos have been checked).
- Confirm the draft BOM against the actual parts.
- Include attribution and license notices for any third-party materials.
- Check the complete Git diff and history for credentials and private files.
  `.gitignore` prevents common mistakes, but does not remove already tracked secrets.

## License

- Firmware configuration, display code, tests, and scripts: [MIT](LICENSE).
- Documentation, enclosure models, and photos: [CC BY 4.0](LICENSE-ASSETS.md),
  unless otherwise noted.

Both allow modification and commercial reuse with attribution. Third-party
materials retain their own licenses.
