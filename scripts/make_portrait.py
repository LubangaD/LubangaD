#!/usr/bin/env python3
"""
Turn a background-free portrait (PNG with transparency) into a monochrome ASCII
SVG that types itself in row by row, like a terminal printing, then holds.

Light areas of the photo get dense glyphs, so on the dark window the face reads
like it is lit; transparent pixels stay blank. Each row is shown through a clip
that wipes left to right (SMIL) with a block cursor riding the edge.

Run locally when the photo changes (needs Pillow + NumPy, see
requirements-portrait.txt):

    python scripts/make_portrait.py [photo.png] [output.svg]
    STATIC=1 python scripts/make_portrait.py      # frozen frame for previews
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

from terminal import CARD_H, CARD_W, FRAME, MUTED, PROMPT, SOFT, esc, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "assets", "portrait-source.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "portrait.svg")
STATIC = bool(os.environ.get("STATIC"))

COLS = int(os.environ.get("COLS", 160))
RAMP = " .`:-=+*cs#%@"          # sparse -> dense; index 0 is only for background
PAD = 20
ART_W = CARD_W - 2 * PAD
ART_TOP = 30 + 12
STATUS_H = 44
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8         # monospace glyphs are roughly 8:15
ROWS = int((CARD_H - ART_TOP - STATUS_H - 8) // CELL_H)
ART_H = ROWS * CELL_H

# photo tuning (env overrides make it quick to try variants)
CROP_SIZE = float(os.environ.get("CROP_SIZE", 0.75))  # square crop side, as a share of the shorter edge
CROP_X = float(os.environ.get("CROP_X", 0.51))        # crop centre across the photo (0-1)
CROP_Y = float(os.environ.get("CROP_Y", 0.0))         # crop top down the photo (0-1)
HEAD = 0.6            # top share of the crop used to set the tone range (face + hair, not the shirt)
DETAIL = float(os.environ.get("DETAIL", 2.0))         # local-contrast boost so features survive on darker skin
BLUR = float(os.environ.get("BLUR", 5))
GAMMA = float(os.environ.get("GAMMA", 0.8))           # <1 lifts mid-tones into denser glyphs

# reveal timing: one cursor sweeps the rows top to bottom in about 6 seconds
ROW_DUR = 6.0 / ROWS


def load(path):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    side = int(min(w, h) * CROP_SIZE)
    x0 = int(min(max(CROP_X * w - side / 2, 0), w - side))
    y0 = int(min(max(CROP_Y * h, 0), h - side))
    im = im.crop((x0, y0, x0 + side, y0 + side))
    gray = np.asarray(im.convert("L"), dtype=np.float32) / 255
    alpha = np.asarray(im.getchannel("A"), dtype=np.float32) / 255
    return gray, alpha


def tone(gray, alpha):
    head = alpha > 0.5
    head[int(len(head) * HEAD):] = False
    lo, hi = np.percentile(gray[head], [2, 98])
    t = np.clip((gray - lo) / max(hi - lo, 1e-3), 0, 1)
    # unsharp-style local contrast: push each pixel away from its neighbourhood
    blur = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(BLUR)),
                      dtype=np.float32) / 255
    t = np.clip(t + DETAIL * (t - blur), 0, 1)
    return np.power(t, GAMMA)


def to_rows(t, alpha):
    size = (COLS, ROWS)
    small = np.asarray(Image.fromarray((t * 255).astype(np.uint8)).resize(size, Image.LANCZOS), dtype=np.float32) / 255
    mask = np.asarray(Image.fromarray((alpha * 255).astype(np.uint8)).resize(size, Image.LANCZOS), dtype=np.float32) / 255
    top = len(RAMP) - 1
    rows = []
    for y in range(ROWS):
        line = []
        for x in range(COLS):
            if mask[y, x] < 0.5:
                line.append(" ")
            else:
                line.append(RAMP[1 + int(round(small[y, x] * (top - 1)))])
        rows.append("".join(line).rstrip())
    return rows


def render(rows):
    parts = window(CARD_W, CARD_H, f"{PROMPT}: ~$ ./portrait.sh")
    font = CELL_H * 0.86
    for ry, line in enumerate(rows):
        if not line:
            continue
        row_y = ART_TOP + ry * CELL_H
        width = len(line) * CELL_W
        text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H * 0.76:.1f}" fill="{SOFT}" '
                f'font-size="{font:.2f}" textLength="{width:.1f}" lengthAdjust="spacing">{esc(line)}</text>')
        if STATIC:
            parts.append(text)
            continue
        begin = ry * ROW_DUR
        parts.append(
            f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{ART_W}" begin="{begin:.3f}s" dur="{ROW_DUR:.3f}s" '
            f'fill="freeze"/></rect></clipPath><g clip-path="url(#r{ry})">{text}</g>'
            f'<rect y="{row_y + 1:.1f}" width="{CELL_W:.2f}" height="{CELL_H - 2:.2f}" fill="{SOFT}" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + ART_W}" begin="{begin:.3f}s" dur="{ROW_DUR:.3f}s" '
            f'fill="freeze"/><set attributeName="opacity" to="0.85" begin="{begin:.3f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>'
        )

    line_y = ART_TOP + ART_H + 8
    text_y = line_y + 25
    parts.append(f'<line x1="0" y1="{line_y:.1f}" x2="{CARD_W}" y2="{line_y:.1f}" stroke="{FRAME}"/>')
    status = f"{PROMPT}:~$ whoami "
    name = "Derrick Lubanga"
    char_w = 18 * 0.6   # textLength pins the width, so the cursor lands right after the name
    parts.append(f'<text x="{PAD}" y="{text_y:.1f}" fill="{MUTED}" font-size="18" '
                 f'textLength="{(len(status) + len(name)) * char_w:.1f}">{esc(status)}'
                 f'<tspan fill="{SOFT}" font-weight="700">{name}</tspan></text>')
    cursor_x = PAD + (len(status) + len(name)) * char_w + 4
    parts.append(f'<rect x="{cursor_x:.1f}" y="{text_y - 15:.1f}" width="10" height="19" fill="{SOFT}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" '
                 f'repeatCount="indefinite"/></rect>')
    parts.append("</svg>")
    return "".join(parts)


if __name__ == "__main__":
    gray, alpha = load(SRC)
    svg = render(to_rows(tone(gray, alpha), alpha))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)}: {COLS}x{ROWS} glyphs, {len(svg) // 1024} KB")
