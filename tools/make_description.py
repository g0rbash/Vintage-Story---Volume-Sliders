"""Build the mod description once and publish it twice, identical in style and content:

  docs/moddb-description.html   a plain description for the Mod DB's description box: paragraphs, headings, lists, and
                                the site's own spoiler for the screenshots (no layout of its own)
  docs/moddb-entry.md           the other fields of the Mod DB form, and what to put in each
  docs/images/description.png   that same panel rendered by Microsoft Edge (GitHub strips
                                inline styles, so the README shows the rendered panel)
  README.md                     the image, a plain-text copy of the same content, real screenshots
                                from docs/images/screenshots/ (if any), and links

Same look as the American Frontiersman: Western Wear description. Colours follow the Vintage Story
handbook (GuiStyle): #403529 dialog panel, #e9ddce / #edce98 text, #845c43 wood, #5a4530 dark brown.

The sound groups and slider counts are read from assets/volumesliders/config/major.json and
lang/en.json, so run tools/generate.py first (build.py does).

usage: python -I make_description.py <repo root>
"""
import base64
import glob
import json
import os
import re
import struct
import subprocess
import sys

ROOT = sys.argv[1]
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

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
        sound_rows.append((f'<b>{label.replace("&", "&amp;")}</b>', examples, str(n)))
sound_rows.insert(0, ('<b>Helve Hammer</b>', HELVE, str(combined_total)))
sound_rows.insert(9, ('<b>Mobs</b>', MOBS, str(creature_total)))
sound_rows.append(('<b>Mods</b>', MODS, 'Varies'))
SOUNDS_INTRO = (f'The window opens on these sounds, the ones people most often want quieter, and can show all {total} of '
                "the game's own, plus the sounds of any mods you have.")

# ---------------------------------------------------------------- styles
SERIF = "font-family: Lora, Georgia, 'Times New Roman', serif;"
SANS = "font-family: Montserrat, Verdana, sans-serif;"
INK = '#403529'
ACCENT = '#8a5426'
P = 'margin: 0 0 12px 0;'
TD = 'border: 1px solid #c9a66b; padding: 6px;'
ROW = ['#efe0b8', '#f6ebcd']


def h(title):
    return (f'<p style="margin: 20px 0 6px 0; color: {ACCENT}; {SERIF} font-size: 18px; font-weight: bold; '
            f'letter-spacing: 1px;">&#10022;&nbsp; {title.upper()}</p>\n')


def table(headers, rows):
    out = [f'<table style="border-collapse: collapse; margin: 0 0 14px 0; width: 100%; {SANS} font-size: 13px; '
           f'color: {INK};"><tbody>',
           '<tr style="background: #e3cc94;">' + ''.join(f'<td style="{TD}"><b>{c}</b></td>' for c in headers) + '</tr>']
    for i, r in enumerate(rows):
        out.append(f'<tr style="background: {ROW[i % 2]};">' + ''.join(f'<td style="{TD}">{c}</td>' for c in r) + '</tr>')
    return '\n'.join(out) + '</tbody></table>\n'


def ul(items, tag='ul'):
    return (f'<{tag} style="margin: 0 0 14px 22px; padding: 0;">'
            + ''.join(f'<li style="margin: 0 0 4px 0;">{i}</li>' for i in items) + f'</{tag}>\n')


def frame(color, pad, inner):
    return (f'<table style="border-collapse: collapse; width: 100%;"><tbody><tr>'
            f'<td style="background: {color}; padding: {pad}px;">{inner}</td></tr></tbody></table>')


# Real in-game screenshots (docs/images/screenshots). The README image shows them inline in their sections; the Mod DB
# page keeps them in one collapsed "spoiler" block so they don't clutter the description.
SHOTS = {
    'window': ('window.png', 'The window, opened with Ctrl+Shift+V. A group marked with > opens to show its sounds.'),
    'mods': ('mods-section.png', 'Sounds from other mods are listed under Mods, one group per mod.'),
}
# The Mod DB can't read local files, so the spoiler links to the repository's copies. These work once the repository
# is public; until then, upload the screenshots to the mod page and swap the addresses.
RAW = 'https://raw.githubusercontent.com/g0rbash/Vintage-Story---Volume-Sliders/main/docs/images/screenshots/'


def data_uri(key):
    with open(os.path.join(ROOT, 'docs', 'images', 'screenshots', SHOTS[key][0]), 'rb') as fh:
        return 'data:image/png;base64,' + base64.b64encode(fh.read()).decode()


def figure(key, src):
    caption = SHOTS[key][1].replace('>', '&gt;')
    return (f'<p style="margin: 4px 0 14px 0; text-align: center;"><img src="{src}" width="560" alt="{caption}"><br>'
            f'<span style="font-size: 12px; color: #6e5a44;"><i>{caption}</i></span></p>\n')


def moddb_spoiler(src_for):
    """The Mod DB's own spoiler markup (div.spoiler > div.spoiler-toggle + div.spoiler-text; the site styles it), the
    same as the "Features" spoiler under the intro on mods.vintagestory.at/deciduoustrees."""
    parts = []
    for key in ('window', 'mods'):
        with open(os.path.join(ROOT, 'docs', 'images', 'screenshots', SHOTS[key][0]), 'rb') as fh:
            px_w, px_h = struct.unpack('>II', fh.read(24)[16:24])
        width = 700
        caption = SHOTS[key][1].replace('>', '&gt;')
        parts.append(f'<p><img src="{src_for(key)}" width="{width}" height="{round(px_h * width / px_w)}" alt="{caption}"></p>\n'
                     f'<p><i>{caption}</i></p>\n')
    return ('<div class="spoiler">\n<div class="spoiler-toggle">Screenshots</div>\n<div class="spoiler-text">\n'
            + ''.join(parts) + '</div>\n</div>\n')


def make_body(src_for):
    """The sections of the README image (the panel on GitHub). src_for(key) gives each screenshot's address."""
    inline = lambda k: figure(k, src_for(k))
    return [
        f'<p style="{P} font-size: 12px; color: #6e5a44;"><i>{AI_NOTE}</i></p>\n',
        f'<p style="{P}">{INTRO}</p>\n',
        h('What You Get'),
        ul(FEATURES),
        h('The Sounds'),
        f'<p style="{P}">{SOUNDS_INTRO}</p>\n',
        table(['Group', 'Includes', 'Sounds'], sound_rows),
        inline('mods'),
        h('Using It'),
        ul(USING),
        inline('window'),
        h('Compatibility'),
        ul([f'<b>{a}</b> {b}' for a, b in COMPAT]),
        h('Installation'),
        ul(INSTALL, 'ol'),
        h('Credits'),
        ul([f'<b>{a}</b> {b}' for a, b in CREDITS]),
        h('A Note from G0rbash'),
        f'<p style="{P}">{NOTE}</p>\n<p style="{P}">{SIGN}</p>\n',
    ]


title_cell = (f'<td style="background: #403529; padding: 16px; text-align: center;">'
              f'<span style="{SERIF} font-size: 34px; font-weight: bold; letter-spacing: 3px; color: #e9ddce;">VOLUME SLIDERS</span><br><br>'
              f'<span style="{SANS} font-size: 12px; letter-spacing: 3px; color: #b5a48c;">WATER &nbsp;&#10022;&nbsp; RAIN &nbsp;&#10022;&nbsp; WIND &nbsp;&#10022;&nbsp; THUNDER &nbsp;&#10022;&nbsp; MOBS &nbsp;&#10022;&nbsp; MACHINES</span><br><br>'
              f'<span style="{SANS} font-size: 12px; font-weight: bold; letter-spacing: 2px; color: #c58948;">v{VERSION} &mdash; VINTAGE STORY {GAME} &mdash; A SLIDER FOR EVERY SOUND</span></td>')
footer = (f'<td style="background: #5a4530; padding: 8px; text-align: center;">'
          f'<span style="{SANS} font-size: 12px; letter-spacing: 2px; color: #e9ddce;">VOLUME SLIDERS &nbsp;v{VERSION} &nbsp;&#10022;&nbsp; VINTAGE STORY {GAME} &nbsp;&#10022;&nbsp; CLIENT SIDE &nbsp;&#10022;&nbsp; BY G0RBASH</span><br>'
          f'<span style="{SANS} font-size: 10px; color: #b5a48c;">Made with AI assistance.</span></td>')


def make_panel(body):
    content = (f'<table style="border-collapse: collapse; width: 100%;"><tbody><tr>{title_cell}</tr></tbody></table>'
               f'<table style="border-collapse: collapse; width: 100%;"><tbody><tr>'
               f'<td style="background: #f6ebcd; color: {INK}; padding: 18px; {SANS} font-size: 14px; line-height: 1.55;">\n{"".join(body)}</td></tr></tbody></table>'
               f'<table style="border-collapse: collapse; width: 100%;"><tbody><tr>{footer}</tr></tbody></table>')
    html_out = ('<div style="max-width: 920px;">'
                + frame('#2a1f16', 4, frame('#845c43', 3, frame('#5a4530', 3, content))) + '</div>\n')
    return re.sub(r'<(/?)i>', r'<\1em>', re.sub(r'<(/?)b>', r'<\1strong>', html_out))


panel = make_panel(make_body(data_uri))     # the README image: screenshots inline

docs = os.path.join(ROOT, 'docs')
os.makedirs(os.path.join(docs, 'images'), exist_ok=True)
def plain(text):
    """The Mod DB's own editor writes <strong> and <em>."""
    return re.sub(r'<(/?)i>', r'<\1em>', re.sub(r'<(/?)b>', r'<\1strong>', text))


def items(entries, tag='ul'):
    return f'<{tag}>\n' + ''.join(f'<li>{plain(e)}</li>\n' for e in entries) + f'</{tag}>\n'


def sound_line(group, includes, count):
    n = '' if count == 'Varies' else f' ({count})'
    return f'{group}{n}: {includes}'


# Same order as the Deciduous Trees page: the intro, then the screenshots in a spoiler, then the details.
moddb_description = ''.join([
    f'<p><em>{AI_NOTE}</em></p>\n',
    f'<p>{plain(INTRO)}</p>\n',
    plain(moddb_spoiler(lambda k: RAW + SHOTS[k][0])),
    '<h3>What you get</h3>\n', items(FEATURES),
    '<h3>The sounds</h3>\n', f'<p>{plain(SOUNDS_INTRO)}</p>\n',
    items([sound_line(a, b, c) for a, b, c in sound_rows]),
    '<h3>Using it</h3>\n', items(USING),
    '<h3>Compatibility</h3>\n', items([f'<b>{a}</b> {b}' for a, b in COMPAT]),
    '<h3>Installation</h3>\n', items(INSTALL, 'ol'),
    '<h3>Credits</h3>\n', items([f'<b>{a}</b> {b}' for a, b in CREDITS]),
    '<h3>A note from G0rbash</h3>\n', f'<p>{NOTE}</p>\n<p>{SIGN}</p>\n',
])
with open(os.path.join(docs, 'moddb-description.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(moddb_description)

SUMMARY = 'A searchable list of volume sliders for every sound in the game.'
assert len(SUMMARY) <= 100, 'the Mod DB summary is limited to 100 characters'
REPO = 'https://github.com/g0rbash/Vintage-Story---Volume-Sliders'
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
`docs/moddb-description.html`, and press Save in the dialog. It uses only what the editor itself writes: paragraphs,
headings, bold and italic, lists, and the site's own spoiler (the same kind as the one under the intro on the Deciduous
Trees page). The two icons at the end of the toolbar look like spoiler controls, if you'd rather build the spoiler by hand.

The screenshots inside the spoiler link to this repository's copies, which load once the repository is public. Until then,
after you upload the screenshots below, swap the two image addresses in the spoiler for the uploaded ones, or delete the
images there and add them with the editor's image button.

## Screenshots (drag to upload; drag to reorder)

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


# ---------------------------------------------------------------- render for GitHub
page = os.path.join(docs, '_render.html')
url = 'file:///' + page.replace('\\', '/')


def edge(*args):
    return subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', *args, url],
                          check=True, capture_output=True, timeout=120, text=True, encoding='utf-8').stdout


with open(page, 'w', encoding='utf-8') as f:
    f.write('<!doctype html><meta charset="utf-8"><body style="margin:0;width:920px;background:#2a1f16">' + panel +
            '<script>document.title="H"+document.body.scrollHeight</script>')
height = int(re.search(r'<title>H(\d+)</title>', edge('--window-size=920,2000', '--dump-dom')).group(1))
edge(f'--window-size=920,{height}', '--screenshot=' + os.path.join(docs, 'images', 'description.png'))
os.remove(page)


# ---------------------------------------------------------------- README
def md(text):
    text = re.sub(r'<a href="([^"]+)">([^<]+)</a>', r'[\2](\1)', text)
    for a, b in (('<b>', '**'), ('</b>', '**'), ('<i>', '*'), ('</i>', '*'), ('<br>', '  \n'),
                 ('&amp;', '&'), ('&quot;', '"'), ('&mdash;', '—')):
        text = text.replace(a, b)
    return text


def shot_md(key):
    name, caption = SHOTS[key]
    return (f'<p align="center"><img src="docs/images/screenshots/{name}" width="560" alt="{caption}"><br>'
            f'<i>{caption}</i></p>\n')


r = [
    '<p align="center"><img src="docs/images/description.png" alt="Volume Sliders, a searchable list for every '
    'sound in Vintage Story 1.22.7. The full text is below." width="920"></p>\n',
    '<details><summary><b>Text version</b> (the same content as the image above)</summary>\n',
    f'*{AI_NOTE}*\n',
    INTRO + '\n',
    '### What You Get\n\n' + ''.join(f'- {md(t)}\n' for t in FEATURES),
    f'### The Sounds\n\n{SOUNDS_INTRO}\n\n| Group | Includes | Sounds |\n|---|---|---|\n'
    + ''.join(f'| {md(a)} | {md(b)} | {c} |\n' for a, b, c in sound_rows),
    shot_md('mods'),
    '### Using It\n\n' + ''.join(f'- {md(t)}\n' for t in USING),
    shot_md('window'),
    '### Compatibility\n\n' + ''.join(f'- **{a}** {b}\n' for a, b in COMPAT),
    '### Installation\n\n' + ''.join(f'{i}. {md(t)}\n' for i, t in enumerate(INSTALL, 1)),
    '### Credits\n\n' + ''.join(f'- **{a}** {md(b)}\n' for a, b in CREDITS),
    f'### A Note from G0rbash\n\n{md(NOTE)}\n\n{md(SIGN)}\n',
    '</details>\n',
    '**Links:** [Accessibility Tweaks](https://mods.vintagestory.at/accessibilitytweaks)\n\n'
    '**Building from source:** see [BUILDING.md](BUILDING.md).\n',
]
with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(r))
print(f'wrote docs/moddb-description.html, docs/moddb-entry.md, docs/images/description.png (920x{height}), and README.md')
