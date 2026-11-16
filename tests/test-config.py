"""Local configuration checks; --eval validates with disposable credentials."""
import base64
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parent.parent
EVAL = "--eval" in sys.argv
if EVAL:
    sys.argv.remove("--eval")


class Loader(yaml.SafeLoader):
    pass


for tag in ("!include", "!secret"):
    Loader.add_constructor(tag, lambda loader, node: (node.tag, loader.construct_scalar(node)))


def load(name):
    return yaml.load((ROOT / name).read_text(), Loader=Loader)


class ConfigTests(unittest.TestCase):
    def test_credentials_are_secret_references(self):
        common = load("common.yaml")
        device = load("room-sensor.yaml")
        self.assertEqual(device["substitutions"]["device_name"], "room-sensor")
        self.assertEqual(common["wifi"]["ssid"], ("!secret", "wifi_ssid"))
        self.assertEqual(common["wifi"]["password"], ("!secret", "wifi_password"))
        self.assertEqual(device["api"]["encryption"]["key"], ("!secret", "api_key"))
        self.assertNotIn("manual_ip", common["wifi"])

    def test_shared_hardware_and_display(self):
        device = load("room-sensor.yaml")
        common = load("common.yaml")
        self.assertEqual(device["packages"]["device"], ("!include", "common.yaml"))
        self.assertEqual(common["packages"]["screen"], ("!include", "display.yaml"))
        self.assertEqual(common["esp32"]["board"], "esp32-c3-devkitm-1")
        self.assertEqual(common["i2c"]["sda"], "GPIO0")
        self.assertEqual(common["i2c"]["scl"], "GPIO1")
        sensor = common["sensor"][0]
        self.assertEqual(sensor["platform"], "scd4x")
        self.assertEqual(sensor["temperature_offset"], "${temperature_offset}")
        self.assertEqual({sensor[key]["id"] for key in ("temperature", "humidity", "co2")},
                         {"temperature", "humidity", "co2"})
        self.assertIn("encryption", common["ota"][0])
        self.assertEqual(load("display.yaml")["display"][0]["address"], 0x3C)

    def test_local_secrets_and_build_outputs_are_ignored(self):
        paths = ("secrets.yaml", "room/secrets.yaml", ".esphome/build/output.bin",
                 "room/.esphome/build/output.bin", ".venv/bin/python",
                 "tests/__pycache__/test.pyc")
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "--stdin"], cwd=ROOT,
            input="\n".join(paths) + "\n", capture_output=True, text=True, check=True)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))
        self.assertEqual(subprocess.run(
            ["git", "check-ignore", "--no-index", "secrets.example.yaml"],
            cwd=ROOT, capture_output=True).returncode, 1)

    @unittest.skipUnless(EVAL, "ESPHome integration evaluation")
    def test_esphome_validation(self):
        with tempfile.TemporaryDirectory(prefix="room-sensor-eval-") as directory:
            root = Path(directory)
            for name in ("room-sensor.yaml", "common.yaml", "display.yaml"):
                shutil.copyfile(ROOT / name, root / name)
            (root / "secrets.yaml").write_text(yaml.safe_dump({
                "wifi_ssid": "test-network",
                "wifi_password": secrets.token_urlsafe(24),
                "api_key": base64.b64encode(secrets.token_bytes(32)).decode(),
            }))
            result = subprocess.run(
                ["esphome", "config", "room-sensor.yaml"], cwd=root,
                capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, "ESPHome validation failed")


if __name__ == "__main__":
    unittest.main()
