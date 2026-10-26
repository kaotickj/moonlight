# Lunar calculation validation — 2026-10-26

Command from project root: `python -m unittest discover -s tests -v`

Result on Python 3.12.10: **10 tests passed** (0.171 seconds).

Reference: Fred Espenak, NASA/GSFC, [Phases of the Moon: 2001 to 2100](https://eclipse.gsfc.nasa.gov/phase/phases2001.html), Universal Time, rounded to minute.

| Event | NASA UT | Calculated minus reference (seconds) |
|---|---|---:|
| Full | 2001-01-09 20:24 | +57.155 |
| New | 2001-01-24 13:07 | +30.182 |
| New | 2026-01-18 19:52 | +39.367 |
| Full | 2026-03-03 11:38 | +32.023 |
| New | 2026-08-12 17:37 | +11.344 |
| Full | 2026-08-28 04:18 | +66.085 |
| New | 2026-10-10 15:50 | +36.724 |
| Full | 2026-10-26 04:12 | +15.539 |
| New | 2026-11-09 07:02 | +42.392 |
| Full | 2026-11-24 14:53 | +64.191 |
| Full | 2050-01-08 01:39 | +27.762 |
| New | 2050-01-23 04:57 | +14.127 |
| New | 2100-01-10 12:55 | +72.626 |
| Full | 2100-01-26 02:49 | +65.358 |

Maximum observed difference: **72.626 seconds**, under the two-minute regression
tolerance. This is sample validation, not a universal precision guarantee.

Other tests cover new/full illumination extrema, all eight labels during an
October 2026 calendar, event order, next event after a previous event, UTC
equivalence across -04:00 and +13:00 offsets, finite numeric inputs, date-range
boundaries, unsupported future event omission, bounded calendar input, bounded
event counts, and SHA-256 integrity of the vendored source.

No Android build or device behavior is certified by this Python test report.
