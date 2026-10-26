"""Make a Mod DB thumbnail from a real in-game screenshot of the sliders: crop a square and scale it to 480x480.
Nothing is drawn on top, so the thumbnail is always just what the game showed.

usage: python -I make_thumbnail.py <screenshot.png> <output.png> [x y size]
  x y size  top-left corner and side length of the square to keep, in screenshot pixels
            (default: the largest centred square)
"""
import base64
import os
import struct
import subprocess
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
SIZE = 480

raw = open(SRC, 'rb').read()
w, h = struct.unpack('>II', raw[16:24])  # PNG IHDR
if len(sys.argv) >= 6:
    x, y, side = (int(a) for a in sys.argv[3:6])
else:
    side = min(w, h)
    x, y = (w - side) // 2, (h - side) // 2
scale = SIZE / side

data = base64.b64encode(raw).decode()
page = os.path.join(os.path.dirname(os.path.abspath(OUT)), '_thumbnail.html')
with open(page, 'w', encoding='utf-8') as f:
    f.write(f"""<!doctype html><meta charset="utf-8"><style>html,body{{margin:0}}img{{image-rendering:auto}}</style>
<body style="width:{SIZE}px;height:{SIZE}px;overflow:hidden;position:relative">
<img src="data:image/png;base64,{data}" style="position:absolute;left:{-x * scale}px;top:{-y * scale}px;width:{w * scale}px;height:{h * scale}px">""")
try:
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files',
                    f'--window-size={SIZE},{SIZE}', f'--screenshot={os.path.abspath(OUT)}',
                    'file:///' + page.replace('\', '/')], check=True, capture_output=True, timeout=60)
finally:
    os.remove(page)
print(OUT)
