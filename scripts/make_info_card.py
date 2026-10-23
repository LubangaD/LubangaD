#!/usr/bin/env python3
"""
A neofetch-style "about me" card that sits beside the ASCII portrait. The
prompt types itself, then each line slides in on a stagger and a cursor blinks
at the end. Edit ROWS below and re-run when your details change.

    python scripts/make_info_card.py [output.svg]
"""
import os
import sys
import textwrap

from terminal import AMBER, CARD_H, CARD_W, CYAN, FRAME, GOLD, GREEN, MUTED, PROMPT, SOFT, esc, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "info-card.svg")

ROWS = [
    ("Name", "Derrick Lubanga, MSc"),
    ("Role", "Co-Founder & CEO, Tunga Innovation"),
    ("Also", "Data Scientist, Stahili"),
    ("Building", "AbleSpeak: a voice-controlled browser extension giving students with motor "
                 "disabilities hands-free access to digital learning"),
    ("Tuned for", "Kenyan accents and non-standard speech"),
    ("Award", "Royal Academy of Engineering LIF Advance Awardee 2026"),
    ("Alumni", "Nairobi Circular Economy ClimAccelerator"),
    ("Study", "MSc Data Science & Analytics, Strathmore"),
    ("Focus", "Predictive analytics · digital inclusion"),
    ("Stack", "Python · SQL · TensorFlow · Spark · LLMs"),
    ("Base", "Nairobi, Kenya"),
    ("Contact", "lderrickn254@gmail.com"),
]
HIGHLIGHT = {"Building": AMBER, "Award": GOLD}
MOTTO = "Every voice deserves access."

PAD = 36
FONT = 22
CHAR_W = FONT * 0.6
LINE = 33
KEY_W = 11 * CHAR_W
WRAP = int((CARD_W - 2 * PAD - KEY_W) // CHAR_W) - 1
BLOCKS = ["#0d1117", "#ff5f56", "#27c93f", "#ffbd2e", "#1f6feb", "#bc8cff", "#22d3ee", "#e6edf3"]

TYPE = 0.7           # seconds to type the prompt
STAGGER = 0.22       # gap between lines sliding in
SLIDE = 0.45

CSS = (
    f".l{{opacity:0;animation:in {SLIDE}s ease-out both}}"
    "@keyframes in{0%{opacity:0;transform:translateX(-10px)}100%{opacity:1;transform:translateX(0)}}"
)


def render():
    parts = window(CARD_W, CARD_H, f"{PROMPT}: ~$ neofetch", CSS)
    y = 30 + 48

    prompt = f"{PROMPT}:~$ neofetch"
    width = len(prompt) * CHAR_W
    parts.append(
        f'<clipPath id="type"><rect x="{PAD}" y="{y - FONT}" height="{FONT + 8}" width="0">'
        f'<animate attributeName="width" from="0" to="{width + 4:.0f}" dur="{TYPE}s" fill="freeze" '
        f'calcMode="discrete" values="{";".join(f"{width * i / len(prompt):.1f}" for i in range(len(prompt) + 1))}"/>'
        f'</rect></clipPath>'
        f'<text clip-path="url(#type)" x="{PAD}" y="{y}" font-size="{FONT}" fill="{MUTED}" '
        f'textLength="{width:.1f}">{esc(PROMPT)}:~$ <tspan fill="{SOFT}">neofetch</tspan></text>'
    )

    lines = []   # svg fragments with a {y} placeholder
    user, host = PROMPT.split("@")
    lines.append(f'<text x="{PAD}" y="{{y}}" font-size="{FONT + 6}" font-weight="700">'
                 f'<tspan fill="{GREEN}">{user}</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{CYAN}">{host}</tspan></text>')
    lines.append(f'<text x="{PAD}" y="{{y}}" font-size="{FONT}" fill="{FRAME}">{"-" * len(PROMPT)}</text>')
    for key, value in ROWS:
        colour = HIGHLIGHT.get(key, SOFT)
        for i, chunk in enumerate(textwrap.wrap(value, WRAP)):
            label = f'<tspan fill="{CYAN}" font-weight="700">{key}</tspan>' if i == 0 else ""
            lines.append(f'<text x="{PAD}" y="{{y}}" font-size="{FONT}">{label}'
                         f'<tspan x="{PAD + KEY_W:.0f}" fill="{colour}">{esc(chunk)}</tspan></text>')

    y += LINE + 12
    start = TYPE + 0.2
    for i, fragment in enumerate(lines):
        parts.append(f'<g class="l" style="animation-delay:{start + i * STAGGER:.2f}s">'
                     f'{fragment.replace("{y}", f"{y:.0f}")}</g>')
        y += LINE

    y += 14
    done = start + len(lines) * STAGGER
    parts.append(f'<g class="l" style="animation-delay:{done:.2f}s">')
    for i, colour in enumerate(BLOCKS):
        parts.append(f'<rect x="{PAD + i * 40}" y="{y}" width="40" height="22" fill="{colour}"/>')
    parts.append('</g>')

    y += 22 + 50
    motto_w = (len(MOTTO) + 2) * CHAR_W
    parts.append(f'<g class="l" style="animation-delay:{done + STAGGER:.2f}s">'
                 f'<text x="{PAD}" y="{y:.0f}" font-size="{FONT}" fill="{MUTED}" textLength="{motto_w:.1f}">'
                 f'&gt; <tspan fill="{AMBER}" font-style="italic">{esc(MOTTO)}</tspan></text>'
                 f'<rect x="{PAD + motto_w + 6:.1f}" y="{y - FONT + 3:.0f}" width="12" height="{FONT}" fill="{SOFT}">'
                 f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" '
                 f'repeatCount="indefinite"/></rect></g>')

    if y > CARD_H - 20:
        sys.exit(f"info card overflows: content ends at y={y:.0f}, canvas is {CARD_H}; trim ROWS")
    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    svg = render()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)} ({len(svg) // 1024} KB)")
