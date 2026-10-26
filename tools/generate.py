"""Generate assets/volumesliders/config/imm.json and lang/en.json from the installed game's sounds.

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
}


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
    settings = []
    for k in keys:
        lang["sound-" + k] = found[k]
        settings.append({
            "Type": "Slider",
            "Label": "volumesliders:sound-" + k,
            "Map": k,
            "Min": 0,
            "Max": 100,
            "Step": 1,
        })
    imm = {"Configuration": [{
        "ConfigFile": "volumesliders.json",
        "ConfigLabel": "volumesliders:title",
        "ConfigSide": "Client",
        "Settings": settings,
    }]}

    with open(os.path.join(ROOT, "assets/volumesliders/config/imm.json"), "w", encoding="utf-8") as f:
        json.dump(imm, f, indent="\t")
    with open(os.path.join(ROOT, "assets/volumesliders/lang/en.json"), "w", encoding="utf-8") as f:
        json.dump(lang, f, indent="\t", ensure_ascii=False)
    print(f"{len(keys)} sounds")


main()
