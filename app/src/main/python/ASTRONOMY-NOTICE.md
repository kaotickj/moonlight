# Astronomy Engine

Vendored unmodified from Don Cross's Astronomy Engine v2.1.19:
https://raw.githubusercontent.com/cosinekitty/astronomy/v2.1.19/source/python/astronomy/astronomy.py

SHA-256: `5f3a17c0b14290d084eeb0d29b00b3139cd1703a8d30fa5eb141398a24719261`

MIT license and copyright are retained at the top of astronomy.py.
No external Python packages or runtime network calls are required.

The wrapper uses MoonPhase, Illumination and SearchMoonPhase. It does not
estimate events by repeatedly adding an average synodic month. Astronomy
Engine accounts for orbital perturbations and converts dynamical time to UT
with its Espenak/Meeus delta-T model. UTC and UT1 are approximated as equal
(under 0.9 seconds difference in the modern era). Far-future civil event
times remain uncertain because Earth rotation is not predictable exactly.

Phase names use the nearest of eight 45-degree longitude sectors; the labels
"New Moon" and "Full Moon" describe a neighborhood, not an exact instant.
Illumination is the geometric sunlit fraction of the disk, not eclipse dimming.
Renderings are schematic, with no observer-dependent orientation or libration.

Reference event tests acknowledge Fred Espenak, NASA/GSFC:
https://eclipse.gsfc.nasa.gov/phase/phases2001.html
Those tables are rounded to the minute; regression tolerance is 2 minutes.
This tolerance is a tested sample bound, not a guaranteed error for every date.
