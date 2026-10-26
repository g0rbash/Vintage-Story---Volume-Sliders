# Building Volume Sliders

Requires the .NET 10 SDK, Python 3, and a Vintage Story install (set `VINTAGE_STORY`, default `%APPDATA%\Vintagestory`). `make_thumbnail.py` also uses Microsoft Edge to render.

    python build.py     # regenerates major.json and lang, builds, writes releases/volumesliders_<version>.zip

Then copy the zip from `releases/` into your Mods folder. The `releases/` folder is local (git ignores it) and keeps the zip of every version you build.

## Updating a published version

The zip is named after `"version"` in `modinfo.json`. Once a version has been released (it has a `v<version>` tag), its code is fixed: `build.py` refuses to rebuild it if `src/`, `assets/`, `modinfo.json` or the project file have changed since the tag. To publish an update, raise the version in `modinfo.json` first, build (which makes a new zip with the new number and keeps the old one), commit, then tag and release that version. Run `python -I tools/make_description.py .` too, so the README and the Mod DB text show the new number.

## How it fits together

- `src/SoundPatch.cs` scales each sound through a Harmony postfix on the game's `LoadedSoundNative.GlobalVolume` getter, and re-sends the volume to sounds that are already playing when a slider moves. The factor is 0 to 1, so nothing gets louder than vanilla.
- `src/SoundKeys.cs` turns a sound's asset path into the key stored in `ModConfig/volumesliders.json` (`game:sounds/walk/wood1.ogg` becomes `walk_wood1`) and into a readable name. `tools/generate.py` must produce identical keys.
- `tools/generate.py` scans the installed game's sounds and writes `assets/volumesliders/config/major.json` (the "major sounds" list the window opens on) and `lang/en.json`. The list of major sounds and their friendly names is `MAJOR_PATTERNS` and `OVERRIDES` at the top of that script.

## Tools

| Script | What it does |
|---|---|
| `tools/generate.py` | Writes `major.json` and `lang/en.json` from the installed game's sounds. |
| `tools/make_description.py` | Writes the description once and publishes it three ways: `docs/moddb-description.html` (for the Mod DB's description box; no screenshots, since the Mod DB gallery shows them), `docs/moddb-entry.md` (what goes in each field of the Mod DB form), and `README.md` (the same text for GitHub, screenshots in a collapsed section). The screenshots live in `docs/images/screenshots/`. Run it with `python -I tools/make_description.py .` |
| `tools/make_thumbnail.py` | Makes the Mod DB thumbnail from a real screenshot of the sliders (`docs/images/thumbnail-source.png`): square crop, hard-edged upscale, colour grade (crushed shadows, S-curve, saturation, vignette), and "Sliders" in Almendra on a plank. Run it with `python -I tools/make_thumbnail.py docs/images/thumbnail-source.png docs/images/thumbnail.png`. |
