# Volume Sliders

A Vintage Story client mod that gives every sound its own 0-100 volume slider.

- 100 is the game's normal volume for that sound; sliders can only turn a sound down, never above default.
- Sounds have readable names ("Weather: Lightning Near 1"). Variants of a sound each get their own slider.
- Searchable window in the standard dialog style: `Ctrl+Shift+V` (rebindable) or `.volumesliders`.
- Also in Integrated Mod Manager: ambient, weather and Shiver sliders, plus a checkbox that opens the full window (IMM chokes on 800+ settings).
- Sounds from other mods show up automatically in the window (IMM lists the vanilla set).
- A "heard in the last 30 seconds" filter helps find the sound you just heard; the play button previews a sound.

Settings live in `ModConfig/volumesliders.json` as a flat `{ "walk_wood1": 40 }` map; missing = 100.

Works alongside Accessibility Tweaks' Sound Effects; the two multipliers stack.

## Build

Requires the .NET 10 SDK and a Vintage Story install (`VINTAGE_STORY` env var, default `%APPDATA%\Vintagestory`).

    python build.py     # regenerates imm.json + lang, builds, writes dist/volumesliders_<version>.zip

`tools/generate.py` and `src/SoundKeys.cs` must keep the same key and name rules.
