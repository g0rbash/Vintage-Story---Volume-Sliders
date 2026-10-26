"""Build the mod description once and publish it twice, identical in style and content:

  docs/moddb-description.html   inline-styled panel, pasted into mods.vintagestory.at
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
import glob
import json
import os
import re
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
         "from 0 to 100, so you can turn down just the ones that bother you and leave the rest alone.")

FEATURES = [
    '<b>0 to 100 per sound.</b> 100 is the game\'s normal volume for that sound, and no slider can go above it.',
    '<b>Clear names.</b> "Water: Rapids", "Thunder: Near", "Anvil &amp; Helve Hammer: Hit 2". Sounds that come in '
    'several versions get a slider for each version.',
    '<b>A searchable window</b> in the same style as the game\'s own settings.',
    '<b>Heard in the last 30 seconds.</b> One switch lists only the sounds that just played, so you can find the one '
    'that is bugging you right now.',
    '<b>Changes apply immediately</b>, including sounds that are already playing, like a river loop.',
    '<b>Preview button</b> beside every slider.',
    '<b>Other mods\' sounds</b> show up in the window automatically.',
]

# group label -> examples. The label is the text before ":" in each sound's name (see tools/generate.py).
GROUPS = [
    ('Anvil & Helve Hammer', 'The anvil hit, which is also the helve hammer\'s sound'),
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
MOBS = 'Every creature sound: drifters, shivers, bowtorn, locusts, wolves, bears, goats, chickens, and the rest'

USING = [
    'Press <b>Ctrl+Shift+V</b> (you can rebind it in the controls settings), or type <b>.volumesliders</b> in chat.',
    'The window opens on the sounds most people want quieter, plus every creature sound. Flip <i>Show every sound</i> '
    "to list all of them, including other mods'.",
    'Your settings are saved in <b>ModConfig/volumesliders.json</b>.',
]
COMPAT = [
    ('Vintage Story 1.22.7.', 'Client-side only.'),
    ('Accessibility Tweaks.', 'Its Sound Effects screen scales sounds too. The two multipliers stack, so a sound set to '
                              '50% in each plays at 25%.'),
    ('Other mods.', 'Their sounds get sliders in the full window. A mod that plays sound through its own audio code, '
                    'instead of the game\'s sound engine, may not respond to them.'),
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
major = json.load(open(os.path.join(cfg, 'config', 'major.json'), encoding='utf-8'))['keys']
total = len([k for k in lang if k.startswith('sound-')])


def group_of(key):
    return lang['sound-' + key].split(':')[0]


counts = {}
for k in major:
    counts[group_of(k)] = counts.get(group_of(k), 0) + 1
creature_total = len([k for k in lang if k.startswith('sound-creature_')])

sound_rows = []
for label, examples in GROUPS:
    n = counts.get(label, 0)
    if n:
        sound_rows.append((f'<b>{label.replace("&", "&amp;")}</b>', examples, str(n)))
sound_rows.insert(8, ('<b>Mobs</b>', MOBS, str(creature_total)))
SOUNDS_INTRO = (f'The window opens on these sounds, the ones people most often want quieter, and can show all {total} of '
                "the game's own, plus any added by other mods.")

# ---------------------------------------------------------------- styles
SERIF = "font-family: Lora, Georgia, 'Times New Roman', serif;"
SANS = "font-family: Montserrat, Verdana, sans-serif;"
INK = '#403529'
ACCENT = '#8a5426'
P = 'margin: 0 0 12px 0;'
TD = 'border: 1px solid #c9a66b;'
ROW = ['#efe0b8', '#f6ebcd']


def h(title):
    return (f'<p style="margin: 20px 0 6px 0; color: {ACCENT}; {SERIF} font-size: 18px; font-weight: bold; '
            f'letter-spacing: 1px;">&#10022;&nbsp; {title.upper()}</p>\n')


def table(headers, rows):
    out = [f'<table style="border-collapse: collapse; margin: 0 0 14px 0; width: 100%; {SANS} font-size: 13px; '
           f'color: {INK};" cellpadding="6"><tbody>',
           '<tr style="background: #e3cc94;">' + ''.join(f'<td style="{TD}"><b>{c}</b></td>' for c in headers) + '</tr>']
    for i, r in enumerate(rows):
        out.append(f'<tr style="background: {ROW[i % 2]};">' + ''.join(f'<td style="{TD}">{c}</td>' for c in r) + '</tr>')
    return '\n'.join(out) + '</tbody></table>\n'


def ul(items, tag='ul'):
    return (f'<{tag} style="margin: 0 0 14px 22px; padding: 0;">'
            + ''.join(f'<li style="margin: 0 0 4px 0;">{i}</li>' for i in items) + f'</{tag}>\n')


def frame(color, pad, inner):
    return (f'<table style="border-collapse: collapse; width: 100%;" cellpadding="0"><tbody><tr>'
            f'<td style="background: {color}; padding: {pad}px;">{inner}</td></tr></tbody></table>')


body = [
    f'<p style="{P} font-size: 12px; color: #6e5a44;"><i>{AI_NOTE}</i></p>\n',
    f'<p style="{P}">{INTRO}</p>\n',
    h('What You Get'),
    ul(FEATURES),
    h('The Sounds'),
    f'<p style="{P}">{SOUNDS_INTRO}</p>\n',
    table(['Group', 'Includes', 'Sliders'], sound_rows),
    h('Using It'),
    ul(USING),
    h('Compatibility'),
    ul([f'<b>{a}</b> {b}' for a, b in COMPAT]),
    h('Installation'),
    ul(INSTALL, 'ol'),
    h('Credits'),
    ul([f'<b>{a}</b> {b}' for a, b in CREDITS]),
    h('A Note from G0rbash'),
    f'<p style="{P}">{NOTE}</p>\n<p style="{P}">{SIGN}</p>\n',
]

title_cell = (f'<td style="background: #403529;" align="center">'
              f'<span style="{SERIF} font-size: 34px; font-weight: bold; letter-spacing: 3px; color: #e9ddce;">VOLUME SLIDERS</span><br><br>'
              f'<span style="{SANS} font-size: 12px; letter-spacing: 3px; color: #b5a48c;">WATER &nbsp;&#10022;&nbsp; RAIN &nbsp;&#10022;&nbsp; WIND &nbsp;&#10022;&nbsp; THUNDER &nbsp;&#10022;&nbsp; MOBS &nbsp;&#10022;&nbsp; MACHINES</span><br><br>'
              f'<span style="{SANS} font-size: 12px; font-weight: bold; letter-spacing: 2px; color: #c58948;">v{VERSION} &mdash; VINTAGE STORY {GAME} &mdash; A SLIDER FOR EVERY SOUND</span></td>')
footer = (f'<td style="background: #5a4530;" align="center">'
          f'<span style="{SANS} font-size: 12px; letter-spacing: 2px; color: #e9ddce;">VOLUME SLIDERS &nbsp;v{VERSION} &nbsp;&#10022;&nbsp; VINTAGE STORY {GAME} &nbsp;&#10022;&nbsp; CLIENT SIDE &nbsp;&#10022;&nbsp; BY G0RBASH</span><br>'
          f'<span style="{SANS} font-size: 10px; color: #b5a48c;">Made with AI assistance.</span></td>')
content = (f'<table style="border-collapse: collapse; width: 100%;" cellpadding="16"><tbody><tr>{title_cell}</tr></tbody></table>'
           f'<table style="border-collapse: collapse; width: 100%;" cellpadding="18"><tbody><tr>'
           f'<td style="background: #f6ebcd; color: {INK}; {SANS} font-size: 14px; line-height: 1.55;">\n{"".join(body)}</td></tr></tbody></table>'
           f'<table style="border-collapse: collapse; width: 100%;" cellpadding="8"><tbody><tr>{footer}</tr></tbody></table>')
panel = ('<div style="max-width: 920px;">'
         + frame('#2a1f16', 4, frame('#845c43', 3, frame('#5a4530', 3, content))) + '</div>\n')

docs = os.path.join(ROOT, 'docs')
os.makedirs(os.path.join(docs, 'images'), exist_ok=True)
with open(os.path.join(docs, 'moddb-description.html'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('<!-- Paste into the mod description editor on mods.vintagestory.at (source / HTML view). '
            'Generated by tools/make_description.py; edit the content there. -->\n' + panel)

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


shots = sorted(glob.glob(os.path.join(docs, 'images', 'screenshots', '*.png')))
r = [
    '<p align="center"><img src="docs/images/description.png" alt="Volume Sliders, a 0 to 100 volume slider for every '
    'sound in Vintage Story 1.22.7. The full text is below." width="920"></p>\n',
    '<details><summary><b>Text version</b> (the same content as the image above)</summary>\n',
    f'*{AI_NOTE}*\n',
    INTRO + '\n',
    '### What You Get\n\n' + ''.join(f'- {md(t)}\n' for t in FEATURES),
    f'### The Sounds\n\n{SOUNDS_INTRO}\n\n| Group | Includes | Sliders |\n|---|---|---|\n'
    + ''.join(f'| {md(a)} | {md(b)} | {c} |\n' for a, b, c in sound_rows),
    '### Using It\n\n' + ''.join(f'- {md(t)}\n' for t in USING),
    '### Compatibility\n\n' + ''.join(f'- **{a}** {b}\n' for a, b in COMPAT),
    '### Installation\n\n' + ''.join(f'{i}. {md(t)}\n' for i, t in enumerate(INSTALL, 1)),
    '### Credits\n\n' + ''.join(f'- **{a}** {md(b)}\n' for a, b in CREDITS),
    f'### A Note from G0rbash\n\n{md(NOTE)}\n\n{md(SIGN)}\n',
    '</details>\n',
]
if shots:
    r.append('### Screenshots\n\n' + '\n'.join(
        f'<img src="docs/images/screenshots/{os.path.basename(s)}" width="440" alt="Volume Sliders screenshot">'
        for s in shots) + '\n')
r.append('**Links:** [Accessibility Tweaks](https://mods.vintagestory.at/accessibilitytweaks)\n\n'
         '**Building from source:** see [BUILDING.md](BUILDING.md).\n')
with open(os.path.join(ROOT, 'README.md'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(r))
print(f'wrote docs/moddb-description.html, docs/images/description.png (920x{height}), and README.md '
      f'({len(shots)} screenshots)')
