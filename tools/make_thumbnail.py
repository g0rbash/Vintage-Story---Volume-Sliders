"""Make the Mod DB thumbnail from a real in-game screenshot of the sliders.

The picture is the screenshot itself: cropped square, scaled up with hard pixel edges (so the blocky game art stays
crisp), and colour-graded in one pass in floating point, rounded to 8-bit only once at the end so the 8-bit source
isn't posterised any further than it already is:
  - shadows crushed (black point raised) for deeper darks,
  - a gentle S-curve for contrast,
  - saturation boosted,
  - a soft vignette.
Then "Sliders" goes on a wooden plank along the bottom, in Almendra (SIL Open Font License, shipped with the game),
white with a dark outline like the sign on the original American Frontiersman thumbnail.

Rendered with Microsoft Edge in headless mode, like make_description.py.

usage: python -I make_thumbnail.py <screenshot.png> <output.png> [text]
"""
import base64
import os
import struct
import subprocess
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
TEXT = sys.argv[3] if len(sys.argv) > 3 else 'Sliders'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
BACKSLASH = chr(92)
FONT = 'file:///' + os.path.join(os.environ['APPDATA'], 'Vintagestory', 'assets', 'game', 'fonts',
                                 'Almendra-Bold.ttf').replace(BACKSLASH, '/')
SIZE = 480
BAND = round(SIZE * 0.17)

raw = open(SRC, 'rb').read()
w, h = struct.unpack('>II', raw[16:24])  # PNG IHDR
side = min(w, h)
sx, sy = (w - side) // 2, (h - side) // 2
data = base64.b64encode(raw).decode()

page = os.path.join(os.path.dirname(os.path.abspath(OUT)), '_thumbnail.html')
with open(page, 'w', encoding='utf-8') as f:
    f.write(f"""<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: Almendra; src: url('{FONT}'); font-weight: bold; }}
html, body {{ margin: 0; background: #1a120c; }}
canvas {{ display: block; }}
</style><body><canvas id="c" width="{SIZE}" height="{SIZE}"></canvas><script>
const SIZE = {SIZE}, BAND = {BAND};
const img = new Image();
img.onload = async () => {{
  await document.fonts.load('bold 60px Almendra');
  const c = document.getElementById('c'), g = c.getContext('2d', {{ willReadFrequently: true }});
  g.imageSmoothingEnabled = false;                       // hard pixel edges
  g.drawImage(img, {sx}, {sy}, {side}, {side}, 0, 0, SIZE, SIZE);

  // ---- grade, in float; rounded once at the end
  const d = g.getImageData(0, 0, SIZE, SIZE), p = d.data;
  const BLACK = 0.10, WHITE = 0.97, SAT = 1.45, CURVE = 0.55, VIGNETTE = 0.30;
  const smooth = (x) => x * x * (3 - 2 * x);
  const clamp = (x) => Math.min(1, Math.max(0, x));
  for (let y = 0; y < SIZE; y++) for (let x = 0; x < SIZE; x++) {{
    const i = (y * SIZE + x) * 4;
    let r = p[i] / 255, gr = p[i + 1] / 255, b = p[i + 2] / 255;
    // levels: crush the shadows, hold the highlights
    r = clamp((r - BLACK) / (WHITE - BLACK)); gr = clamp((gr - BLACK) / (WHITE - BLACK)); b = clamp((b - BLACK) / (WHITE - BLACK));
    // S-curve
    r += CURVE * (smooth(r) - r); gr += CURVE * (smooth(gr) - gr); b += CURVE * (smooth(b) - b);
    // saturation around luma
    const l = 0.2126 * r + 0.7152 * gr + 0.0722 * b;
    r = l + (r - l) * SAT; gr = l + (gr - l) * SAT; b = l + (b - l) * SAT;
    // vignette
    const dx = (x / SIZE - 0.5) * 2, dy = (y / SIZE - 0.5) * 2;
    const v = 1 - VIGNETTE * Math.min(1, (dx * dx + dy * dy) / 2);
    p[i] = Math.round(clamp(r * v) * 255);
    p[i + 1] = Math.round(clamp(gr * v) * 255);
    p[i + 2] = Math.round(clamp(b * v) * 255);
  }}
  g.putImageData(d, 0, 0);

  // ---- plank + lettering
  const top = SIZE - BAND;
  const grad = g.createLinearGradient(0, top, 0, SIZE);
  grad.addColorStop(0, '#8a6446'); grad.addColorStop(0.55, '#6e4c33'); grad.addColorStop(1, '#563a26');
  g.fillStyle = grad; g.fillRect(0, top, SIZE, BAND);
  g.fillStyle = '#2a1f16'; g.fillRect(0, top - 3, SIZE, 3);
  g.fillStyle = 'rgba(255,235,200,.25)'; g.fillRect(0, top, SIZE, 2);
  const px = Math.round(BAND * 0.78);
  g.font = 'bold ' + px + 'px Almendra'; g.textAlign = 'center'; g.textBaseline = 'middle';
  if ('letterSpacing' in g) g.letterSpacing = '5px';
  const ty = top + BAND / 2 + 2;
  g.lineJoin = 'round'; g.lineWidth = 7; g.strokeStyle = '#1a120c'; g.strokeText({TEXT!r}, SIZE / 2, ty);
  g.fillStyle = 'rgba(0,0,0,.45)'; g.fillText({TEXT!r}, SIZE / 2, ty + 3);
  g.fillStyle = '#fff'; g.fillText({TEXT!r}, SIZE / 2, ty);
}};
img.src = 'data:image/png;base64,{data}';
</script>""")
try:
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                    '--virtual-time-budget=4000', f'--window-size={SIZE},{SIZE}',
                    f'--screenshot={os.path.abspath(OUT)}', 'file:///' + page.replace(BACKSLASH, '/')],
                   check=True, capture_output=True, timeout=90)
finally:
    os.remove(page)
print(OUT)
