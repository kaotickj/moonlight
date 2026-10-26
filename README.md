# Moonlight

Your window to the night. An offline moon phase app for **Windows, Linux and Android**, with a starry backdrop and a prominent illustration of the Moon in its calculated phase.

**Free means free.** No ads, telemetry, tracking, accounts, subscriptions or email collection. No data is collected, sold or shared. Moon calculations happen entirely on your device; Android requests no permissions. No runtime downloads or network services.

## Features

- Current phase and illuminated percentage, refreshed each minute in Now mode.
- Explore dates from 2001 through 2100 at local noon.
- Upcoming new and full moons, with local times and each event’s UTC offset.
- Tools for returning to now, choosing a date and copying details to the clipboard.
- About, privacy, credits and licenses, and a guide to reading the Moon.
- Procedural night sky and cratered Moon artwork; no remote image assets.

The illustration is decorative: waxing is illuminated on the right. It does not reproduce your local sky orientation, libration or eclipse darkening. Phase names are nearest-eighth categories, not exact event instants.

## Version 0.2.0 status

| Platform | Status |
| --- | --- |
| Windows | Portable executable built; desktop startup, date selection, return-to-now and credits smoke checks passed. |
| Linux | Shared desktop source ready; requires Python 3.10+ and Tkinter. No native Linux binary built or verified yet. |
| Android | APK build and lint passed (0 errors, 14 warnings); release signing and phone testing pending. Android 7+, arm64-v8a and x86_64. |

No downloadable release is published yet. Build outputs and signing keys are excluded from source control.

## Run the desktop app

Install Python 3.10 or later with Tkinter, then run:

```sh
python desktop.py
```

On Linux the command is usually `python3 desktop.py`; install your distribution’s Tkinter package if needed (for example `python3-tk` on Debian/Ubuntu). No third-party Python packages are needed to run the app. Desktop date entry uses `YYYY-MM-DD`.

For a bundled Windows or Linux build, run PyInstaller on that operating system, including `app/src/main/python` at the same relative path and `CREDITS.txt` and `PYTHON-LICENSE.txt` at the bundle root. Native Linux packaging remains to be verified.

## Build Android

Use JDK 17, Gradle 8.7, Android SDK platform 34/build-tools 34.0.0, and Python 3.12. The project pins Android Gradle Plugin 8.5.2 and Chaquopy 17.1.0. Set `ANDROID_HOME` or an ignored `local.properties` for the SDK.

```sh
gradle :app:assembleDebug :app:lintDebug
```

Debug output is intentionally unsigned. Release keys must be stored privately, backed up, and never committed. Signing credentials are not part of this repository. Android builds may download build dependencies; the installed app remains offline.

## Verify calculations

```sh
python -m unittest discover -s tests -v
```

All 10 regression tests passed for this patch. The original offline astronomy engine is unchanged. Fourteen selected NASA reference phase events agree within two minutes; this sample tolerance is not an accuracy guarantee across the full supported range. Device clock and time-zone settings affect displayed dates.

## Attribution and licensing

Moonlight is licensed under **GPL-3.0**; see [LICENSE](LICENSE). Third-party components retain their own licenses and notices.

- **Astronomy Engine 2.1.19**, Don Cross — MIT; original copyright and license retained in `astronomy.py`.
- Reference tables: **Fred Espenak, NASA/GSFC**; used for regression tests, not runtime requests.
- Android Python bridge: **Chaquopy** contributors; Python: **Python Software Foundation** and contributors.
- Desktop UI: **Tcl/Tk** via Python’s Tkinter.

See [CREDITS.txt](CREDITS.txt), [Astronomy Engine notice](app/src/main/python/ASTRONOMY-NOTICE.md), and [Python license](PYTHON-LICENSE.txt). Platform runtime distributions retain their bundled license notices.

The official Moonlight app is free, ad-free and tracking-free. GPL preserves software freedoms; it does not prohibit commercial redistribution or require forks to follow this product promise.
