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

INTRO = ("Volume Sliders adds a volume slider for each sound in Vintage Story. The base game only has a few master "
         "volume sliders. With this mod you can turn down a single sound, such as the helve hammer, the rapids, the "
         "cicadas or the rain, and leave everything else as it is.")

FEATURES = [
    'A slider for every sound, from 0 to 100. 100 is the game\'s normal volume; no slider can go above it.',
    'Sounds are listed in groups (Water, Mobs, Armor and so on). Click a group, or its <b>&gt;</b>, to open it. A group\'s '
    'slider scales everything inside it.',
    'Some near-identical sounds share one slider: Bells (the Bell mob and its Deep, Nightmare and Tainted versions), NPC '
    'Voices, each type of armor, and the Anvil group (Helve Hammer and Hand Hammer).',
    'A search box, and a <i>Recently heard</i> switch that lists the sounds played in the last 30 seconds, for finding a '
    'sound you can\'t name.',
    'A Play button beside every slider.',
    'Changes apply immediately, including to loops that are already playing, such as a river.',
    'Sounds added by other mods are listed under <b>Mods</b>, grouped by mod. When a mod replaces one of the game\'s '
    'sounds, that slider shows the mod\'s name.',
]

# group label -> examples. The label is the text before ":" in each sound's name (see tools/generate.py).
GROUPS = [
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
    ('Machines', 'Quern, gears, bellows'),
]
MOBS = ('Creature sounds, grouped by creature: drifters, shivers, bowtorn, locusts, wolves, bears, goats, chickens and '
        'the rest. Bells is one slider for the Bell mob, including its deep bell and its Deep, Nightmare and Tainted '
        'versions.')
NPC = 'Speech from traders and villagers, on one slider.'
ARMOR = 'One slider each for Brigandine, Chain, Leather, Plate and Scale, and an Armor slider for all of them.'
ELSEWHERE = ('Everything else is available with <i>Show every sound</i>, or by searching: Player, Combat, Crafting &amp; '
             'Activities, Walk, Music and Miscellaneous. The mini Bell, Charlemange, is under Mobs.')
MODS = "Sounds added by other mods, grouped by mod. Salty's Temporal Symphony is one example."
ANVIL_GROUP = ('<i>Helve Hammer</i> and <i>Hand Hammer</i> have separate sliders. The game plays the same sound file for '
               'both, with the helve hammer at a much lower pitch, so the mod tells them apart by pitch. Hand Hammer also '
               'covers the weld hit. Placing or breaking an anvil is a different sound (Miscellaneous > Block).')

USING = [
    'Open the window with <b>Ctrl+Shift+V</b> (rebindable in the controls settings) or the chat command '
    '<b>.volumesliders</b>.',
    'A group\'s slider and the sliders inside it multiply: a group at 50% and a sound at 50% plays at 25%.',
    'The window opens on the sounds listed below plus creature sounds. <i>Show every sound</i> lists all of them. '
    '<i>Recently heard</i> lists whatever just played, whether it is on the default list or not.',
    'Settings are saved in <b>ModConfig/volumesliders.json</b>.',
]
COMPAT = [
    ('Vintage Story 1.22.7.', 'Client-side only.'),
    ('Accessibility Tweaks.', 'Its Sound Effects screen also scales sounds. Both apply, so a sound set to 50% in each '
                              'plays at 25%.'),
    ('Other mods.', 'Their sounds get sliders under Mods. A mod\'s own volume setting still applies on top of these '
                    'sliders. A mod that plays sound through its own audio code instead of the game\'s sound engine may '
                    'not respond.'),
]
INSTALL = [
    'Put <b>volumesliders_{v}.zip</b> in your Mods folder.'.format(v=VERSION),
    'Start the game. The first run creates <b>ModConfig/volumesliders.json</b>.',
    'To reset everything, delete that file, or use <i>Reset Shown to 100</i> in the window.',
]
# G0rbash's own wording (edited on GitHub); one string per line, as written. There is no credits section.
NOTE_LINES = [
    "I have not coded in C# since 1996, and json is just pure black magic I don't have time to relearn that skill while "
    "also learning skills for my #dayjob.",
    "I tested and reviewed the code to the best of my ability.",
    'I do not condone the unethical training and use of "AI" coding tools, but there is value for small projects like '
    'this that improve the happy times we have playing video games.',
    "All code is available for review on the GitHub page.",
]
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
combos = {c['id']: len(c['keys']) for c in json.load(open(os.path.join(cfg, 'config', 'combined.json'), encoding='utf-8'))}
armor_total = sum(n for i, n in combos.items() if i.startswith('armor-'))

by_label = {label: (f'<b>{label}</b>', examples, str(counts.get(label, 0))) for label, examples in GROUPS}
order = ['Water', 'Boat', 'Rain', 'Wind', 'Thunder', 'Fire', 'Lava', 'Insects', 'Bees']
sound_rows = [('<b>Anvil</b>', ANVIL_GROUP, str(1 + combos['anvilhammer']))]
sound_rows += [by_label[l] for l in order if counts.get(l)]
sound_rows += [('<b>Mobs</b>', MOBS, str(creature_total + combos['bellmob'])),
               ('<b>NPC Voices</b>', NPC, str(combos['npcvoices'])),
               ('<b>Armor</b>', ARMOR, str(armor_total))]
sound_rows += [by_label[l] for l in ('Temporal', 'Machines') if counts.get(l)]
sound_rows.append(('<b>Mods</b>', MODS, 'Varies'))
SOUNDS_INTRO = 'The window opens on these sounds. ' + ELSEWHERE

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
    return f'{group}: {includes}'


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
    '<h3>A note from G0rbash</h3>\n',
    '<p>' + ' '.join(NOTE_LINES).replace('"', '&quot;') + '</p>\n',
    f'<p>{SIGN}</p>\n',
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

Upload `releases/volumesliders_{VERSION}.zip` and set its game versions to 1.22.0 to {GAME} (`modinfo.json` asks for
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
    '## License\n\n'
    'Volume Sliders follows the [Vintage Story Mod DB terms](https://mods.vintagestory.at/terms): it is free to download '
    'and use, and it may not be reuploaded, modified or not, without the author\'s approval. The full text is in '
    '[LICENSE](LICENSE).\n',
    '## A note from G0rbash\n' + '\n'.join(NOTE_LINES) + f'\n\n{md(SIGN)}\n',
    '---\n\nBuilding from source: see [BUILDING.md](BUILDING.md).\n',
]
with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(readme))
print('wrote docs/moddb-description.html, docs/moddb-entry.md, and README.md')
