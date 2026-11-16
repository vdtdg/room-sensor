"""Execute the shared display lambda against a local C++ recording display."""
import itertools
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parent.parent
EVAL = "--eval" in sys.argv
if EVAL:
    sys.argv.remove("--eval")

HARNESS = r'''
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#define id(x) x
enum class TextAlign { TOP_LEFT, TOP_CENTER, TOP_RIGHT,
                       BOTTOM_LEFT, BOTTOM_CENTER, BOTTOM_RIGHT };
struct Sensor {
  float state;
  bool available;
  bool has_state() const { return available; }
} temperature, humidity, co2;
struct Time {
  bool valid;
  int hour, minute;
  bool is_valid() const { return valid; }
  std::string strftime(const char *format) {
    if (std::string(format) != "%H:%M") std::abort();
    char text[16];
    std::snprintf(text, sizeof(text), "%02d:%02d", hour, minute);
    return text;
  }
} clock_value;
struct Clock { Time now() const { return clock_value; } } display_time;
int header_size = 12, reading_size = 10, measurement_size = 18, compact_size = 12;
int *font_header = &header_size, *font_reading = &reading_size,
    *font_measurement = &measurement_size, *font_compact = &compact_size;
struct Display {
  void print(int x, int y, int *font, TextAlign align, const char *text) {
    std::printf("%d|%d|%d|%s|%d\n", x, y, int(align), text, *font);
  }
  template<typename... Args>
  void printf(int x, int y, int *font, TextAlign align,
              const char *format, Args... args) {
    char text[128];
    std::snprintf(text, sizeof(text), format, args...);
    print(x, y, font, align, text);
  }
} it;
int main(int argc, char **argv) {
  if (argc != 8) return 1;
  temperature = {std::strtof(argv[1], nullptr), bool(std::atoi(argv[4]) & 1)};
  humidity = {std::strtof(argv[2], nullptr), bool(std::atoi(argv[4]) & 2)};
  co2 = {std::strtof(argv[3], nullptr), bool(std::atoi(argv[4]) & 4)};
  clock_value = {bool(std::atoi(argv[5])), std::atoi(argv[6]), std::atoi(argv[7])};
  // LAMBDA
}
'''


class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="display-test-")
        cls.addClassCleanup(cls.tmp.cleanup)
        source = Path(cls.tmp.name) / "display.cpp"
        cls.binary = source.with_suffix("")
        code = textwrap.dedent((ROOT / "display.yaml").read_text().split("lambda: |-\n", 1)[1])
        code = code.replace("${display_name}", "Atelier")
        source.write_text(HARNESS.replace("// LAMBDA", code))
        subprocess.run(["g++", "-std=c++17", "-Wall", "-Werror", str(source),
                        "-o", str(cls.binary)], check=True, capture_output=True)

    def render(self, temp="21.5", hum="45", co2="850", mask=7, valid=1, hour=7, minute=5):
        output = subprocess.check_output(
            [str(self.binary), str(temp), str(hum), str(co2), str(mask),
             str(valid), str(hour), str(minute)], text=True)
        return [line.split("|") for line in output.splitlines()]

    def test_layout_and_readings(self):
        self.assertEqual(self.render(), [
            ["0", "0", "0", "Atelier", "12"], ["128", "0", "2", "07:05", "12"],
            ["0", "20", "0", "Temp °C", "10"], ["64", "20", "1", "Hum %", "10"],
            ["128", "20", "2", "CO2 ppm", "10"],
            ["0", "60", "3", "21.5", "18"], ["64", "60", "4", "45", "18"],
            ["128", "60", "5", "850", "18"],
        ])

    def test_startup_and_independent_missing_sensors(self):
        self.assertEqual(self.render(valid=0)[1][3], "--:--")
        for mask in range(8):
            readings = [row[3] for row in self.render(mask=mask)[5:]]
            self.assertEqual(readings, [
                "21.5" if mask & 1 else "--",
                "45" if mask & 2 else "--",
                "850" if mask & 4 else "--",
            ])

    def test_nonfinite_values(self):
        for value in ("nan", "inf", "-inf"):
            self.assertEqual([row[3] for row in self.render(value, value, value)[5:]],
                             ["--", "--", "--"])

    def test_large_co2_uses_compact_font_after_rounding(self):
        for value, expected, size in ((9999.4, "9999", "18"),
                                      (9999.5, "10000", "12"),
                                      (40000, "40000", "12")):
            row = self.render(co2=value)[7]
            self.assertEqual(row[3:], [expected, size])

    @unittest.skipUnless(EVAL, "extended boundary evaluation")
    def test_text_fits_columns(self):
        # Use the same downloaded font as ESPHome, not estimated character counts.
        from PIL import ImageFont
        font_path = ROOT / ".esphome/font/Roboto@400@False@v1.ttf"
        for size, texts, max_width in (
                (10, ("Temp °C", "Hum %", "CO2 ppm"), 44),
                (18, ("-10.0", "60.0", "100", "9999", "--"), 42),
                (12, ("10000", "40000"), 42)):
            font = ImageFont.truetype(str(font_path), size)
            for text in texts:
                width = sum(round(font.getlength(char)) for char in text)
                self.assertLessEqual(width, max_width, (text, size, width))

    @unittest.skipUnless(EVAL, "extended boundary evaluation")
    def test_boundary_matrix(self):
        # All cases must preserve order, units, formatting and clock padding.
        for temp, hum, co2, hour in itertools.product(
                (-10, 0, 60), (0, 50, 100), (0, 400, 5000, 40000), (0, 12, 23)):
            rows = self.render(temp, hum, co2, hour=hour, minute=59)
            self.assertEqual(rows[1][3], f"{hour:02d}:59")
            self.assertEqual([row[3] for row in rows[5:]],
                             [f"{temp:.1f}", str(hum), str(co2)])
            self.assertEqual([row[4] for row in rows[5:]],
                             ["18", "18", "12" if co2 >= 10000 else "18"])


if __name__ == "__main__":
    unittest.main()
