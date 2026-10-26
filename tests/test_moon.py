"""Run: python -m unittest discover -s tests -v (from project root)."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys
import unittest

PYTHON_DIR = Path(__file__).resolve().parents[1] / "app/src/main/python"
sys.path.insert(0, str(PYTHON_DIR))
import moon


def stamp(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


# Fred Espenak / NASA GSFC, Universal Time, rounded to minute.
# https://eclipse.gsfc.nasa.gov/phase/phases2001.html
REFERENCES = [
    ("Full Moon", "2001-01-09T20:24Z"),
    ("New Moon", "2001-01-24T13:07Z"),
    ("New Moon", "2026-01-18T19:52Z"),
    ("Full Moon", "2026-03-03T11:38Z"),
    ("New Moon", "2026-08-12T17:37Z"),
    ("Full Moon", "2026-08-28T04:18Z"),
    ("New Moon", "2026-10-10T15:50Z"),
    ("Full Moon", "2026-10-26T04:12Z"),
    ("New Moon", "2026-11-09T07:02Z"),
    ("Full Moon", "2026-11-24T14:53Z"),
    ("Full Moon", "2050-01-08T01:39Z"),
    ("New Moon", "2050-01-23T04:57Z"),
    ("New Moon", "2100-01-10T12:55Z"),
    ("Full Moon", "2100-01-26T02:49Z"),
]


class MoonTests(unittest.TestCase):
    def test_authoritative_event_times(self):
        for name, iso in REFERENCES:
            with self.subTest(iso=iso):
                expected = stamp(iso)
                event = moon.upcoming_events(expected - moon.DAY_MS, 1)[0]
                self.assertEqual(event["name"], name)
                self.assertLess(abs(event["epoch_ms"] - expected), 120000)

    def test_new_full_illumination(self):
        for name, iso in REFERENCES:
            data = json.loads(moon.moon_data(stamp(iso)))
            self.assertEqual(data["phase_name"], name)
            if name == "New Moon":
                self.assertLess(data["illumination"], .003)
            else:
                self.assertGreater(data["illumination"], .997)

    def test_calendar_and_phase_progression(self):
        stamps = [stamp(f"2026-10-{day:02d}T12:00Z") for day in range(1, 32)]
        data = json.loads(moon.calendar_data(json.dumps(stamps)))
        self.assertEqual(len(data), 31)
        self.assertEqual(set(row["phase_name"] for row in data), set(moon.PHASE_NAMES))
        for row in data:
            self.assertTrue(0 <= row["illumination"] <= 1)
            self.assertTrue(0 <= row["phase_degrees"] < 360)

    def test_timezone_equivalent_instants(self):
        utc = stamp("2026-10-26T04:12Z")
        ny = stamp("2026-10-26T00:12-04:00")
        nz = stamp("2026-10-26T17:12+13:00")
        self.assertEqual(moon.moon_data(utc), moon.moon_data(ny))
        self.assertEqual(moon.moon_data(utc), moon.moon_data(nz))

    def test_events_order_and_next_after_event(self):
        now = stamp("2026-10-01T12:00Z")
        events = moon.upcoming_events(now)
        self.assertEqual(len(events), 4)
        for event in events:
            self.assertGreater(event["epoch_ms"], now)
            now = event["epoch_ms"]
        after = moon.upcoming_events(events[0]["epoch_ms"] + 1000, 1)[0]
        self.assertEqual(after["name"], events[1]["name"])
        self.assertLess(abs(after["epoch_ms"] - events[1]["epoch_ms"]), 1000)

    def test_invalid_timestamp(self):
        for value in (-1, float("nan"), float("inf"), -float("inf"), True, None, "2026", moon.MIN_EPOCH_MS - 1, moon.MAX_EPOCH_MS):
            with self.subTest(value=value), self.assertRaises(ValueError):
                moon.moon_data(value)

    def test_range_boundaries_and_no_out_of_range_events(self):
        self.assertEqual(len(json.loads(moon.moon_data(moon.MIN_EPOCH_MS))["events"]), 4)
        self.assertEqual(json.loads(moon.moon_data(moon.MAX_EPOCH_MS - 1))["events"], [])

    def test_invalid_calendar(self):
        for value in ({}, [moon.MIN_EPOCH_MS] * 43, [None]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                moon.calendar_data(json.dumps(value))

    def test_invalid_count(self):
        for count in (-1, 25, True, 1.5):
            with self.assertRaises(ValueError):
                moon.upcoming_events(moon.MIN_EPOCH_MS, count)

    def test_pinned_vendor_integrity(self):
        digest = hashlib.sha256((PYTHON_DIR / "astronomy.py").read_bytes()).hexdigest()
        self.assertEqual(digest, "5f3a17c0b14290d084eeb0d29b00b3139cd1703a8d30fa5eb141398a24719261")


if __name__ == "__main__":
    unittest.main()
