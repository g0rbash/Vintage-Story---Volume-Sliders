"""Build the mod description once and publish it three ways, from the same text:

  docs/moddb-description.html   the Mod DB's description box (paste it in the editor's source-code view). Paragraphs,
                                headings, and lists; no layout of its own.
  docs/moddb-entry.md           the other fields of the Mod DB form, and what to put in each
  README.md                     the same description for GitHub, with the screenshots in a collapsed section

The sound groups and slider counts are read from assets/volumesliders/config/major.json and
lang/en.json, so run tools/generate.py first (build.py does).

usage: python -I make_description.py <repo root>
"""
import json
import os
import re
import struct
import sys

ROOT = sys.argv[1]

VERSION = json.load(open(os.path.join(ROOT, 'modinfo.json'), encoding='utf-8'))['version']
GAME = '1.22.7'
AI_NOTE = 'This project was done with the help of Claude (Claude Sonnet 5.5).'

INTRO = ("Some sounds in Vintage Story you'll love for a hundred hours, and some will wear you down: the helve hammer "
         "through a long smithing session, the rapids beside your base, the cicadas, a rainstorm that won't quit. The "
         "base game only gives you a few master volume sliders. This mod gives the individual sounds their own slider, "
         "so you can turn down just the ones that bother you and leave the rest alone.")

FEATURES = [
    '<b>A slider for every sound.</b> 100 is the game\'s normal volume for that sound, and no slider can go above it.',
    '<b>Clear names.</b> "Water: Rapids", "Thunder: Near", "Drifter: Idle 2". Sounds that come in several versions get '
    'a slider for each version.',
    '<b>Groups that open.</b> Related sounds sit under a group marked with a <b>&gt;</b>. Open it to see each sound; '
    'the group\'s own slider turns the whole group up or down. Mobs are grouped by creature: Drifter, Bear, Bowtorn, '
    'and so on.',
    '<b>One slider for the helve hammer.</b> Everything the helve hammer plays is a single slider, instead of a '
    'handful of near-identical hits.',
    '<b>A searchable window</b> in the same style as the game\'s own settings.',
    '<b>Recently heard.</b> One switch lists only the sounds that played in the last 30 seconds, so you can find the '
    'one that is bugging you right now.',
    '<b>Changes apply immediately</b>, including sounds that are already playing, like a river loop.',
    '<b>Preview button</b> beside every slider.',
    '<b>Mod sounds too.</b> Sounds that other mods add get sliders under <b>Mods</b>, grouped by mod. Salty\'s Temporal '
    'Symphony, for example, has a <b>Temporal Storm</b> group for its storm rumbles, warnings, and thunder.',
    '<b>Changes are marked.</b> When a mod replaces one of the game\'s own sounds, that slider shows the mod\'s name '
    'beside it, and its group counts how many of its sounds were changed.',
]

# group label -> examples. The label is the text before ":" in each sound's name (see tools/generate.py).
GROUPS = [
    ('Anvil', 'The weld hit'),
    ('Water', 'Rapids, creek, waterfall, waves, underwater, splashes, waterwheel, wading, swimming'),
    ('Boat', 'Water against the raft, idle and moving'),
    ('Rain', 'Rain on leafy and bare trees, hail, rain on windows'),
    ('Wind', 'Ambient wind, wind in leafy and bare trees'),
    ('Thunder', 'Distant, near, very near, overhead, and the low rumbles'),
    ('Fire', 'Flames, fireplace'),
    ('Lava', 'Lava ambience'),
    ('Insects', 'Cicadas, grasshoppers, coqui frogs'),
    ('Bees', 'Hives, swarms, stings'),
    ('Temporal', 'Stability warnings, rifts, rift wards'),
    ('Bells', 'The deep bell'),
    ('Machines', 'Quern, gears, bellows'),
]
MOBS = 'Every creature sound, grouped by creature: drifters, shivers, bowtorn, locusts, wolves, bears, goats, chickens, and the rest'
MODS = ("Sounds added by other mods, grouped by mod. Temporal Symphony's temporal storm, thunder, and creature sounds are "
        "one example.")
HELVE = ('One slider for everything the helve hammer plays. Hammering at an anvil by hand plays the same hits, '
         'so it quiets those too.')

USING = [
    'Press <b>Ctrl+Shift+V</b> (you can rebind it in the controls settings), or type <b>.volumesliders</b> in chat.',
    'Click a group, or its <b>&gt;</b>, to open or close it. The group\'s slider scales everything inside, and each '
    'sound keeps its own slider too. They multiply, so a group at 50% and a sound at 50% plays at 25%.',
    'The window opens on the sounds most people want quieter, plus every creature sound. Flip <i>Show every sound</i> '
    "to list every sound, including mods' quieter ones.",
    'Your settings are saved in <b>ModConfig/volumesliders.json</b>.',
]
COMPAT = [
    ('Vintage Story 1.22.7.', 'Client-side only.'),
    ('Accessibility Tweaks.', 'Its Sound Effects screen scales sounds too. The two multipliers stack, so a sound set to '
                              '50% in each plays at 25%.'),
    ('Other mods.', 'Their sounds get sliders under Mods, and a game sound a mod replaces is marked with the mod\'s name. '
                    'If a mod has its own volume setting, it still applies on top of these sliders. A mod that plays sound '
                    'through its own audio code, instead of the game\'s sound engine, may not respond.'),
]
INSTALL = [
    'Drop <b>volumesliders_{v}.zip</b> into your Mods folder.'.format(v=VERSION),
    'Start the game. The first run writes <b>ModConfig/volumesliders.json</b> with every sound at 100.',
    'To reset everything, delete that file, or use <i>Reset Shown to 100</i> in the window.',
]
CREDITS = [
    ('G0rbash', 'design, testing, and the Vintage Story 1.22.7 build.'),
    ('ApacheTech Solutions', 'for <a href="https://mods.vintagestory.at/accessibilitytweaks">Accessibility Tweaks</a>, '
                             'whose Sound Effects feature showed the way to scale a single sound.'),
]
NOTE = ("I have not coded in C# since 1996 and don't have time to relearn that skill while also learning skill for my "
        "#dayjob. I tested and reviewed the code to the best of my ability. I do not condone the unethical training "
        "and use of &quot;AI&quot; coding tools, but there is value for small projects like this that improve the "
        "happy times we have playing video games.")
SIGN = 'Thank you,<br>G0rbash'

# ---------------------------------------------------------------- sound data
cfg = os.path.join(ROOT, 'assets', 'volumesliders')
lang = json.load(open(os.path.join(cfg, 'lang', 'en.json'), encoding='utf-8'))
major_cfg = json.load(open(os.path.join(cfg, 'config', 'major.json'), encoding='utf-8'))
major = [k for k in major_cfg['keys'] if 'sound-' + k in lang]
total = major_cfg['total']


def group_of(key):
    return lang['sound-' + key].split(':')[0]


counts = {}
for k in major:
    counts[group_of(k)] = counts.get(group_of(k), 0) + 1
creature_total = major_cfg['creatures']
combined_total = sum(len(c['keys']) for c in json.load(open(os.path.join(cfg, 'config', 'combined.json'), encoding='utf-8')))

sound_rows = []
for label, examples in GROUPS:
    n = counts.get(label, 0)
    if n:
        sound_rows.append((f'<b>{label}</b>', examples, str(n)))
sound_rows.insert(0, ('<b>Helve Hammer</b>', HELVE, str(combined_total)))
sound_rows.insert(9, ('<b>Mobs</b>', MOBS, str(creature_total)))
sound_rows.append(('<b>Mods</b>', MODS, 'Varies'))
SOUNDS_INTRO = (f'The window opens on these sounds, the ones people most often want quieter, and can show all {total} of '
                "the game's own, plus the sounds of any mods you have.")

# Real in-game screenshots (docs/images/screenshots).
SHOTS = {  # file, caption, short alt text for when the image can't load
    'window': ('window.png', 'The window, opened with Ctrl+Shift+V. A group marked with > opens to show its sounds.',
               'Screenshot of the Volume Sliders window'),
    'mods': ('mods-section.png', 'Sounds from other mods are listed under Mods, one group per mod.',
             'Screenshot of the Mods group opened in the Volume Sliders window'),
}
REPO = 'https://github.com/g0rbash/Vintage-Story---Volume-Sliders'
SUMMARY = 'A searchable list of volume sliders for every sound in the game.'
assert len(SUMMARY) <= 100, 'the Mod DB summary is limited to 100 characters'


def shot_size(key, width=700):
    with open(os.path.join(ROOT, 'docs', 'images', 'screenshots', SHOTS[key][0]), 'rb') as fh:
        px_w, px_h = struct.unpack('>II', fh.read(24)[16:24])
    return width, round(px_h * width / px_w)


def sound_line(entry):
    group, includes, count = entry
    return f'{group}{"" if count == "Varies" else f" ({count})"}: {includes}'


# ---------------------------------------------------------------- Mod DB description (HTML)
def plain(text):
    """The Mod DB's own editor writes <strong> and <em>."""
    return re.sub(r'<(/?)i>', r'<\1em>', re.sub(r'<(/?)b>', r'<\1strong>', text))


def items(entries, tag='ul'):
    return f'<{tag}>\n' + ''.join(f'<li>{plain(e)}</li>\n' for e in entries) + f'</{tag}>\n'


docs = os.path.join(ROOT, 'docs')
os.makedirs(docs, exist_ok=True)

# The screenshots are in the Mod DB's gallery above the description, so they aren't repeated here.
moddb_description = ''.join([
    f'<p><em>{AI_NOTE}</em></p>\n',
    f'<p>{plain(INTRO)}</p>\n',
    '<h3>What you get</h3>\n', items(FEATURES),
    '<h3>The sounds</h3>\n', f'<p>{plain(SOUNDS_INTRO)}</p>\n',
    items([sound_line(e) for e in sound_rows]),
    '<h3>Using it</h3>\n', items(USING),
    '<h3>Compatibility</h3>\n', items([f'<b>{a}</b> {b}' for a, b in COMPAT]),
    '<h3>Installation</h3>\n', items(INSTALL, 'ol'),
    '<h3>Credits</h3>\n', items([f'<b>{a}</b> {b}' for a, b in CREDITS]),
    '<h3>A note from G0rbash</h3>\n', f'<p>{NOTE}</p>\n<p>{SIGN}</p>\n',
])
with open(os.path.join(docs, 'moddb-description.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(moddb_description)

# ---------------------------------------------------------------- Mod DB form sheet
with open(os.path.join(docs, 'moddb-entry.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(f"""# Mod DB entry: Volume Sliders

What to put in each part of the "Add new Mod" form at https://mods.vintagestory.at/edit/mod, in the order the form shows
them (`docs/reference/moddb-form.png` is a screenshot of it). Generated by `tools/make_description.py`, so the wording and
numbers match the README.

## Top row

| Field | Value |
|---|---|
| Status | Draft. Leave it until you're ready to publish. |
| Category | Game Mod (the other choices are Server Specific-Tweak, External Tool, and Other) |
| Tags | QoL, Utility, Tweak, Sound, Audio, Accessibility (other pages use short free-form words like these) |
| Name | Volume Sliders |
| URL Alias | volumesliders (matches the mod ID in `modinfo.json`) |

## Summary (100 characters or less)

{SUMMARY}  ({len(SUMMARY)} characters)

## Text

Click the **source code** button in the editor toolbar (the `<>` icon, or Tools > Source code), paste the whole of
`docs/moddb-description.html` into the window that opens, and press Save in that window. Pasting straight into the text
box instead shows the tags as literal text. The description uses only what the editor itself writes (paragraphs,
headings, bold and italic, lists) and has no screenshots of its own, because the gallery above the description shows them.

## Screenshots (drag to upload; drag to reorder; they appear in the gallery above the description)

1. `docs/images/screenshots/window.png`
2. `docs/images/screenshots/mods-section.png`
3. `docs/images/thumbnail.png`: this one is for the logo (below), and the form says logo images are not shown in the slideshow.

## Links

| Field | Value |
|---|---|
| Homepage or Forum Post Url | (leave blank, or the forum thread if you start one) |
| Trailer Video Url | (blank) |
| Source Code Url | {REPO} (once the repository is public) |
| Issue tracker Url | {REPO}/issues (once the repository is public) |
| Wiki Url | (blank) |
| Donate Url | (yours, if you want one) |

## Additional information

| Field | Value |
|---|---|
| Side | Client side mod |
| ModDB Logo image | `thumbnail.png`, picked from the screenshots you uploaded (the form wants 480 x 480 or 480 x 320; it is 480 x 480) |
| External Logo image | Default (crop ModDB image) is fine; it is used for social media previews |

## After saving

Upload `dist/volumesliders_{VERSION}.zip` and set its game versions to 1.22.0 to {GAME} (`modinfo.json` asks for
1.22.0; it was tested on {GAME}). I couldn't see where the form does this, so look for it after the first save.
""")


# ---------------------------------------------------------------- README (GitHub): the same text, as markdown
def md(text):
    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r'[\2](\1)', text)
    for a, b in (('<b>', '**'), ('</b>', '**'), ('<i>', '*'), ('</i>', '*'), ('<br>', '  \n'),
                 ('&amp;', '&'), ('&quot;', '"'), ('&mdash;', '—'), ('&gt;', '>')):
        text = text.replace(a, b)
    return text


def bullets(entries):
    return ''.join(f'- {md(e)}\n' for e in entries)


def readme_screenshots():
    parts = []
    for key in ('window', 'mods'):
        width, _ = shot_size(key)
        name, caption, alt = SHOTS[key]
        parts.append(f'<img src="docs/images/screenshots/{name}" width="{width}" alt="{alt}">\n\n*{caption}*\n')
    return '<details>\n<summary><b>Screenshots</b></summary>\n\n' + '\n'.join(parts) + '\n</details>\n'


readme = [
    '# Volume Sliders\n',
    f'Version {VERSION} · Vintage Story {GAME} · client side\n',
    f'*{AI_NOTE}*\n',
    INTRO + '\n',
    readme_screenshots(),
    '## What you get\n\n' + bullets(FEATURES),
    f'## The sounds\n\n{md(SOUNDS_INTRO)}\n\n' + bullets([sound_line(e) for e in sound_rows]),
    '## Using it\n\n' + bullets(USING),
    '## Compatibility\n\n' + bullets([f'<b>{a}</b> {b}' for a, b in COMPAT]),
    '## Installation\n\n' + ''.join(f'{i}. {md(t)}\n' for i, t in enumerate(INSTALL, 1)),
    '## Credits\n\n' + bullets([f'<b>{a}</b> {b}' for a, b in CREDITS]),
    f'## A note from G0rbash\n\n{md(NOTE)}\n\n{md(SIGN)}\n',
    '---\n\nBuilding from source: see [BUILDING.md](BUILDING.md).\n',
]
with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(readme))
print('wrote docs/moddb-description.html, docs/moddb-entry.md, and README.md')
