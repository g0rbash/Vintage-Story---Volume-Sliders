# Building Volume Sliders

Requires the .NET 10 SDK, Python 3, and a Vintage Story install (set `VINTAGE_STORY`, default `%APPDATA%\Vintagestory`). `make_description.py` and `make_thumbnail.py` also use Microsoft Edge to render.

    python build.py     # regenerates imm.json, major.json and lang, builds, writes dist/volumesliders_<version>.zip

Then copy the zip from `dist/` into your Mods folder.

## How it fits together

- `src/SoundPatch.cs` scales each sound through a Harmony postfix on the game's `LoadedSoundNative.GlobalVolume` getter, and re-sends the volume to sounds that are already playing when a slider moves. The factor is 0 to 1, so nothing gets louder than vanilla.
- `src/SoundKeys.cs` turns a sound's asset path into the key stored in `ModConfig/volumesliders.json` (`game:sounds/walk/wood1.ogg` becomes `walk_wood1`) and into a readable name. `tools/generate.py` must produce identical keys.
- `tools/generate.py` scans the installed game's sounds and writes `assets/volumesliders/config/imm.json` (the Integrated Mod Manager sliders), `config/major.json` (the "major sounds" list the window opens on), and `lang/en.json`. The list of major sounds and their friendly names is `MAJOR_PATTERNS` and `OVERRIDES` at the top of that script.
- Integrated Mod Manager draws every setting into one texture, so it can't show all ~800 sounds. It gets the major sounds, plus an `OpenWindow` checkbox that the mod watches for in the config file to open the full window.

## Tools

| Script | What it does |
|---|---|
| `tools/generate.py` | Writes `imm.json`, `major.json`, and `lang/en.json` from the installed game's sounds. |
| `tools/make_description.py` | Builds `docs/moddb-description.html`, the same panel as `docs/images/description.png`, and `README.md`. Run it with `python -I tools/make_description.py .` |
| `tools/make_thumbnail.py` | Crops and scales a real in-game screenshot to a square thumbnail. No overlay or generated art. |
