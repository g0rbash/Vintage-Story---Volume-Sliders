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
    "recent": "Recently heard:",
    "play": "Play",
    "reset-shown": "Reset Shown to 100",
    "count": "Showing {0} of {1} sounds",
    "all-sounds": "Show every sound:",
}


# The "major" sounds people most often want quieter. The in-game window opens on these plus every creature
# and NPC voice sound (MAJOR_PREFIXES), with a switch to show everything.
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
MAJOR_PREFIXES = ["creature_", "voice_", "wearable_"]   # voice_ = NPC speech (traders, villagers); wearable_ = armor and clothing rustle
# ...except these, which stay out of the default list (still found by search, or with "Show every sound").
MINOR_PREFIXES = ["creature_bell_charlemange_"]   # Charlemange, the mini Bell

# Sounds that share ONE slider instead of getting one each. The mod stores the slider under "combo:<id>".
# The helve hammer plays only effect/anvilhit (the game picks one of anvilhit1-3); the hand hammer plays the same
# sound, so this slider quiets hammering at an anvil by hand too. The weld hit (anvilmergehit) is the hand hammer's alone, but it shares the slider to save space.
COMBINED = [
    {"id": "helvehammer", "name": "Helve Hammer and Anvil", "patterns": [r"effect_anvilhit\d", r"effect_anvilmergehit"]},
    # Traders and villagers speak by playing random notes from sounds/voice/<instrument>/ (listed as "voiceSounds" in
    # their entity files). Trader-male and villager share the same six instruments, and the female trader's three
    # overlap them, so the voices can't be told apart by NPC type. One slider quiets all of them.
    # The Bell mob's own sounds, including its deep bell. Deep, Nightmare and Tainted are the same mob at higher
    # difficulty and have no sound files of their own. Reception Bell (a block) stays separate.
    {"id": "bellmob", "name": "Bell Mob",
     "patterns": [r"creature_bell_(alarm|bell|death|hurt|listen|walk)", r"effect_deepbell"]},
    # Charlemange, the mini Bell: kept apart from the Bell mob and off the default list.
    {"id": "charlemange", "name": "Charlemange", "patterns": [r"creature_bell_charlemange_.*"]},
    # Armor: one slider per type, listed under an Armor group (no per-variant sliders).
    {"id": "armor-brigandine", "group": "Armor", "name": "Brigandine", "patterns": [r"wearable_brigandine\d"]},
    {"id": "armor-chain", "group": "Armor", "name": "Chain", "patterns": [r"wearable_chain\d"]},
    {"id": "armor-leather", "group": "Armor", "name": "Leather", "patterns": [r"wearable_leather\d"]},
    {"id": "armor-plate", "group": "Armor", "name": "Plate", "patterns": [r"wearable_plate\d"]},
    {"id": "armor-scale", "group": "Armor", "name": "Scale", "patterns": [r"wearable_scale\d"]},
    {"id": "npcvoices", "name": "NPC Voices", "patterns": [r"voice_.*"]},
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
    (r"creature_cicada_short_looping", "Insects: Cicada Short Loop"), (r"creature_cicada", "Insects: Cicada"),
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
    # The Player group is for the player's own body: voice, movement, eating. Everything else the player does by
    # hand goes under Combat or Crafting & Activities.
    (r"player_hurt(\d)", "Player: Hurt {n}"), (r"player_death(\d)", "Player: Death {n}"), (r"player_jump", "Player: Jump"),
    (r"player_eat", "Player: Eating"), (r"player_eat_crunchy", "Player: Eating Crunchy"), (r"player_drink(\d)", "Player: Drinking {n}"),
    (r"player_slap", "Combat: Slap"), (r"player_stab", "Combat: Stab"), (r"player_hackingspearhit", "Combat: Spear Hit"),
    (r"player_projectilehit", "Combat: Projectile Hit"), (r"player_throw", "Combat: Throw"), (r"player_quickthrow", "Combat: Quick Throw"),
    (r"player_build", "Crafting & Activities: Building"), (r"player_buildhigh", "Crafting & Activities: Building High"),
    (r"player_chalkdraw(\d)", "Crafting & Activities: Chalk Drawing {n}"),
    (r"player_clayform", "Crafting & Activities: Clay Forming"), (r"player_clayformhi", "Crafting & Activities: Clay Forming High"),
    (r"player_clothrepair", "Crafting & Activities: Cloth Repair"), (r"player_gluerepair(\d)", "Crafting & Activities: Glue Repair {n}"),
    (r"player_coin(\d)", "Crafting & Activities: Coins {n}"), (r"player_collect(\d)", "Crafting & Activities: Collecting {n}"),
    (r"player_destruct", "Crafting & Activities: Deconstructing"), (r"player_handdrill", "Crafting & Activities: Hand Drill"),
    (r"player_knap(\d)", "Crafting & Activities: Knapping {n}"), (r"player_messycraft", "Crafting & Activities: Messy Crafting"),
    (r"player_panning", "Crafting & Activities: Panning"), (r"player_poultice", "Crafting & Activities: Poultice"),
    (r"player_poultice_applied", "Crafting & Activities: Poultice Applied"), (r"player_scrape", "Crafting & Activities: Scraping"),
    (r"player_seal", "Crafting & Activities: Sealing"), (r"player_squeezehoneycomb", "Crafting & Activities: Squeezing Honeycomb"),
    (r"player_strike(\d)", "Crafting & Activities: Striking {n}"), (r"player_wetclothsqueeze", "Crafting & Activities: Squeezing Wet Cloth"),
    (r"effect_bellows", "Machines: Bellows"),
    (r"wearable_brigandine(\d)", "Armor: Brigandine {n}"), (r"wearable_chain(\d)", "Armor: Chain {n}"),
    (r"wearable_leather(\d)", "Armor: Leather {n}"), (r"wearable_plate(\d)", "Armor: Plate {n}"),
    (r"wearable_scale(\d)", "Armor: Scale {n}"),
]


# Friendly names for a popular mod's own sounds. The window finds mod sounds by itself and names them from their
# file paths; these just give the best-known ones a clearer name. Keys are "<domain>_<path without sounds/ and .ogg>".
# Salty's Temporal Symphony ships its own temporal-storm audio, which is what people most often want to quiet.
def mod_sound_names():
    d = "temporalsymphony_"
    names = {}
    for n in (1, 2, 3):
        names[f"{d}tempintense{n}"] = f"Temporal Storm: Intense {n}"
        names[f"{d}tempquake{n}"] = f"Temporal Storm: Quake {n}"
        names[f"{d}thunderlord_roar{n}"] = f"Thunder Lord: Roar {n}"
        names[f"{d}thunderlord_steam{n}"] = f"Thunder Lord: Steam {n}"
        names[f"{d}thunderlord_step{n}"] = f"Thunder Lord: Step {n}"
    for n in (1, 2):
        names[f"{d}tempwarning{n}"] = f"Temporal Storm: Warning {n}"
        names[f"{d}bass{n}"] = f"Temporal Storm: Bass {n}"
        names[f"{d}music_stormmusic{n}"] = f"Temporal Storm: Storm Music {n}"
    for n in range(1, 9):
        names[f"{d}thunder_specialthunder{n}"] = f"Temporal Storm: Special Thunder {n}"
    names[f"{d}tempwarningbell"] = "Temporal Storm: Warning Bell"
    names[f"{d}tempwarningbell_waning"] = "Temporal Storm: Warning Bell Waning"
    names[f"{d}riftweather_apocalyptic"] = "Temporal Storm: Apocalyptic Rift Weather"
    return names


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

    for k, name in mod_sound_names().items():
        lang["sound-" + k] = name

    combined = []
    for c in COMBINED:
        members = [k for k in keys if any(re.fullmatch(p, k) for p in c["patterns"])]
        combined.append({"id": c["id"], "name": c["name"], "group": c.get("group", ""), "keys": members})
    with open(os.path.join(ROOT, "assets/volumesliders/config/combined.json"), "w", encoding="utf-8") as f:
        json.dump(combined, f, indent="	")
    with open(os.path.join(ROOT, "assets/volumesliders/config/major.json"), "w", encoding="utf-8") as f:
        json.dump({"keys": major, "prefixes": MAJOR_PREFIXES, "minorPrefixes": MINOR_PREFIXES, "total": len(keys),
                   "creatures": len([k for k in keys if k.startswith("creature_")])}, f, indent="	")
    with open(os.path.join(ROOT, "assets/volumesliders/lang/en.json"), "w", encoding="utf-8") as f:
        json.dump(lang, f, indent="\t", ensure_ascii=False)
    print(f"{len(keys)} sounds, {len(major)} major")


main()
