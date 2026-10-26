"""Generate assets/volumesliders/config/major.json and lang/en.json from the installed game's sounds.

Keys and display names must match src/SoundKeys.cs exactly.
Usage: python tools/generate.py [path to Vintagestory install]
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ["APPDATA"], "Vintagestory")

UI = {
    "title": "Volume Sliders",
    "hotkey": "Open Volume Sliders",
    "command-description": "Open the Volume Sliders window",
    "search": "Search:",
    "recent": "Heard in the last 30 seconds:",
    "reset-shown": "Reset Shown to 100",
    "count": "Showing {0} of {1} sounds",
    "all-sounds": "Show every sound:",
}


# The "major" sounds people most often want quieter. The in-game window opens on these plus every creature
# sound (MAJOR_PREFIXES), with a switch to show everything.
# Sources: forum/mod-page complaints (helve hammer anvil hit, boat water, quern, cicadas/insects, loud bells,
# temporal sounds) plus the user's own list (water, rain, wind, thunder, mobs). Gears/bellows/fire are judgment calls.
MAJOR_PATTERNS = [
    r"effect_anvilhit\d", r"effect_anvilmergehit",                                   # helve hammer + anvil
    r"environment_(rapids|creek|waterfall|waterwaves|underwater|largesplash\d|mediumsplash|smallsplash)",
    r"block_water", r"block_waterwheel_(water|wood)", r"walk_water\d", r"player_swim", r"raft_(idle|moving)",
    r"weather_tracks_(rain_leafy|rain_leafless|hail)", r"environment_rainwindow",   # rain
    r"environment_wind", r"weather_wind_(leafy|leafless)",                           # wind
    r"weather_lightning_.*", r"weather_lowgrumble", r"weather_tracks_(lowtremble|verylowtremble)",  # thunder
    r"environment_(fire|fireplace|lava)",
    r"creature_(cicada|cicada_short_looping|grasshopper|coqui|beehive|beehive_wild|beemob|beesting)",
    r"effect_tempstab_(drain|low|verylow)", r"effect_rift", r"effect_deepbell", r"block_riftward",
    r"block_quern", r"effect_(gears|bellows)",
]
MAJOR_PREFIXES = ["creature_"]

# Sounds that share ONE slider instead of getting one each. The mod stores the slider under "combo:<id>".
# The helve hammer plays only effect/anvilhit (the game picks one of anvilhit1-3); the hand hammer plays the same
# sound, so this slider quiets hammering at an anvil by hand too. The weld hit (anvilmergehit) is the hand hammer's alone.
COMBINED = [
    {"id": "helvehammer", "name": "Helve Hammer (and Anvil Hits)", "patterns": [r"effect_anvilhit\d"]},
]

# Friendly names where the file name alone isn't clear. {n} = trailing number.
OVERRIDES = [
    (r"effect_anvilhit(\d)", "Helve Hammer: Hit {n}"),
    (r"effect_anvilmergehit", "Anvil: Weld Hit"),
    (r"environment_rapids", "Water: Rapids"), (r"environment_creek", "Water: Creek"),
    (r"environment_waterfall", "Water: Waterfall"), (r"environment_waterwaves", "Water: Waves"),
    (r"environment_underwater", "Water: Underwater"),
    (r"environment_largesplash(\d)", "Water: Large Splash {n}"), (r"environment_mediumsplash", "Water: Medium Splash"),
    (r"environment_smallsplash", "Water: Small Splash"), (r"environment_drip(\d)", "Water: Drip {n}"),
    (r"block_water", "Water: Flowing Water Block"), (r"block_waterwheel_water", "Water: Waterwheel Splash"),
    (r"block_waterwheel_wood", "Water: Waterwheel Creak"), (r"walk_water(\d)", "Water: Wading {n}"),
    (r"player_swim", "Water: Swimming"), (r"raft_idle", "Boat: Idle on Water"), (r"raft_moving", "Boat: Moving Through Water"),
    (r"weather_tracks_rain_leafy", "Rain: Leafy Trees"), (r"weather_tracks_rain_leafless", "Rain: Bare Trees"),
    (r"weather_tracks_hail", "Rain: Hail"), (r"environment_rainwindow", "Rain: On Windows"),
    (r"environment_wind", "Wind: Ambient"), (r"weather_wind_leafy", "Wind: Leafy Trees"), (r"weather_wind_leafless", "Wind: Bare Trees"),
    (r"weather_lightning_distant", "Thunder: Distant"), (r"weather_lightning_near", "Thunder: Near"),
    (r"weather_lightning_verynear", "Thunder: Very Near"), (r"weather_lightning_nodistance", "Thunder: Overhead"),
    (r"weather_lowgrumble", "Thunder: Low Grumble"), (r"weather_tracks_lowtremble", "Thunder: Low Tremble"),
    (r"weather_tracks_verylowtremble", "Thunder: Very Low Tremble"),
    (r"environment_fire", "Fire: Flames"), (r"environment_fireplace", "Fire: Fireplace"),
    (r"environment_lava", "Lava: Ambient"), (r"block_lava", "Lava: Block"), (r"walk_lava", "Lava: Wading"),
    (r"creature_cicada_short_looping", "Insects: Cicada (Short Loop)"), (r"creature_cicada", "Insects: Cicada"),
    (r"creature_grasshopper", "Insects: Grasshopper"), (r"creature_coqui", "Insects: Coqui Frog"),
    (r"creature_beehive_wild", "Bees: Wild Hive"), (r"creature_beehive", "Bees: Hive"),
    (r"creature_beemob", "Bees: Swarm"), (r"creature_beesting", "Bees: Sting"),
    (r"effect_tempstab_drain", "Temporal: Stability Draining"), (r"effect_tempstab_low", "Temporal: Stability Low"),
    (r"effect_tempstab_verylow", "Temporal: Stability Very Low"), (r"effect_rift", "Temporal: Rift"),
    (r"effect_deepbell", "Bells: Deep Bell"), (r"effect_receptionbell", "Bells: Reception Bell"),
    (r"block_riftward", "Temporal: Rift Ward"),
    (r"block_quern", "Machines: Quern"), (r"effect_gears", "Machines: Gears"),
    (r"effect_gearbox_turn", "Machines: Gearbox Turning"), (r"effect_planetary_gears", "Machines: Planetary Gears"),
    (r"effect_woodgrind", "Machines: Wood Grinding"), (r"effect_metalgrinding", "Machines: Metal Grinding"),
    (r"effect_bellows", "Machines: Bellows"),
]


def is_major(key):
    return any(re.fullmatch(p, key) for p in MAJOR_PATTERNS)


def override_name(key):
    for pat, text in OVERRIDES:
        m = re.fullmatch(pat, key)
        if m:
            return text.replace("{n}", m.group(1) if m.groups() else "")
    return None


def title_case(s):
    out = ""
    for i, c in enumerate(s):
        if c in "-_ .":
            if out and not out.endswith(" "):
                out += " "
            continue
        boundary = out and not out.endswith(" ") and (
            (c.isdigit() and not s[i - 1].isdigit()) or (c.isupper() and s[i - 1].islower()))
        if boundary:
            out += " "
        out += c.upper() if (not out or out.endswith(" ")) else c
    return out


def describe(path):
    """path like 'sounds/walk/wood1.ogg' or 'music/x.ogg' (no domain) -> (key, display)."""
    p = path[:-4]
    if p.startswith("sounds/"):
        p = p[7:]
    key = re.sub(r"[^a-z0-9]", "_", p.lower())
    cat_src = p
    slash = cat_src.find("/")
    cat = "General" if slash < 0 else cat_src[:slash]
    file = p[p.rfind("/") + 1:]
    folder = p[:p.rfind("/")] if "/" in p else ""
    fs = folder.find("/")
    sub = "" if fs < 0 else folder[fs + 1:].replace("/", " ")
    name = title_case(file)
    if sub:
        name = title_case(sub) + " " + name
    return key, title_case(cat) + ": " + name


def main():
    found = {}
    assets = os.path.join(GAME, "assets")
    for domain in sorted(os.listdir(assets)):
        base = os.path.join(assets, domain)
        if not os.path.isdir(base):
            continue
        for cat in ("sounds", "music"):
            for dirpath, _, files in os.walk(os.path.join(base, cat)):
                for f in files:
                    if f.endswith(".ogg"):
                        rel = os.path.relpath(os.path.join(dirpath, f), base).replace("\\", "/")
                        key, display = describe(rel)
                        found.setdefault(key, display)

    keys = sorted(found)
    lang = dict(UI)
    major = []
    for k in keys:
        name = override_name(k)
        if name:  # only deliberate renames; every other name is built from the file path by src/SoundTree.cs
            lang["sound-" + k] = name
        if is_major(k):
            major.append(k)

    combined = []
    for c in COMBINED:
        members = [k for k in keys if any(re.fullmatch(p, k) for p in c["patterns"])]
        combined.append({"id": c["id"], "name": c["name"], "keys": members})
    with open(os.path.join(ROOT, "assets/volumesliders/config/combined.json"), "w", encoding="utf-8") as f:
        json.dump(combined, f, indent="	")
    with open(os.path.join(ROOT, "assets/volumesliders/config/major.json"), "w", encoding="utf-8") as f:
        json.dump({"keys": major, "prefixes": MAJOR_PREFIXES, "total": len(keys),
                   "creatures": len([k for k in keys if k.startswith("creature_")])}, f, indent="	")
    with open(os.path.join(ROOT, "assets/volumesliders/lang/en.json"), "w", encoding="utf-8") as f:
        json.dump(lang, f, indent="\t", ensure_ascii=False)
    print(f"{len(keys)} sounds, {len(major)} major")


main()
