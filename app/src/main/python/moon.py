"""Offline, timezone-independent lunar calculations for the Android interface.

Inputs and outputs are Unix milliseconds. The UI owns local civil-time conversion.
Supported input range: 2001-01-01 through 2100-12-31 UTC. Upcoming events
outside that range are omitted. Phase labels are nearest-eighth approximations;
event times use numerical searches for true ecliptic longitude separation.
"""
import json
import math

import astronomy

MIN_EPOCH_MS = 978307200000
MAX_EPOCH_MS = 4133980800000  # exclusive: 2101-01-01 UTC
J2000_MS = 946728000000
DAY_MS = 86400000
PHASE_NAMES = (
    "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
    "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
)


def _time(epoch_ms):
    if isinstance(epoch_ms, bool) or not isinstance(epoch_ms, (int, float)):
        raise ValueError("A numeric Unix timestamp in milliseconds is required")
    if not math.isfinite(epoch_ms) or not MIN_EPOCH_MS <= epoch_ms < MAX_EPOCH_MS:
        raise ValueError("Choose a date from 2001 through 2100 (UTC)")
    return astronomy.Time((epoch_ms - J2000_MS) / DAY_MS)


def _snapshot(epoch_ms):
    time = _time(epoch_ms)
    degrees = astronomy.MoonPhase(time)
    return {
        "epoch_ms": int(epoch_ms),
        "phase_name": PHASE_NAMES[int((degrees + 22.5) // 45) % 8],
        "phase_degrees": degrees,
        "illumination": astronomy.Illumination(astronomy.Body.Moon, time).phase_fraction,
        "waxing": degrees < 180,
    }


def upcoming_events(epoch_ms, count=4):
    """Next new/full events strictly after the input, up to supported range end."""
    start = _time(epoch_ms)
    if isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 24:
        raise ValueError("Event count must be an integer from 0 to 24")
    candidates = []
    for degrees, name in ((0, "New Moon"), (180, "Full Moon")):
        cursor = start.AddDays(1 / DAY_MS)
        for _ in range(count):
            found = astronomy.SearchMoonPhase(degrees, cursor, 32)
            if found is None:
                raise RuntimeError("Lunar event search did not converge")
            stamp = int(round(found.ut * DAY_MS + J2000_MS))
            if stamp >= MAX_EPOCH_MS:
                break
            if stamp > epoch_ms:
                candidates.append({"name": name, "epoch_ms": stamp})
            cursor = found.AddDays(1)
    return sorted(candidates, key=lambda event: event["epoch_ms"])[:count]


def moon_data(epoch_ms):
    """JSON bridge entry point; illumination is a fraction, not a percentage."""
    result = _snapshot(epoch_ms)
    result["events"] = upcoming_events(epoch_ms)
    return json.dumps(result, allow_nan=False)


def calendar_data(epoch_millis_json):
    """JSON list of up to 42 local-noon timestamps supplied by Android."""
    stamps = json.loads(epoch_millis_json)
    if not isinstance(stamps, list) or len(stamps) > 42:
        raise ValueError("Calendar input must be a list of at most 42 timestamps")
    return json.dumps([_snapshot(stamp) for stamp in stamps], allow_nan=False)
