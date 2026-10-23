#!/usr/bin/env python3
"""
Draw data/contributions.json as a GitHub-style contribution calendar in a
terminal window. Cells pop in once on a diagonal sweep (green ones flash as they
land), then the graph holds still.

    python scripts/render_heatmap.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

from terminal import GREENS, GREEN, INK, MUTED, PROMPT, esc, short_date, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "contrib-heatmap.svg")

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 20
LABEL_W = 32
MONTH_H = 22
FOOTER_H = 58

# reveal timing (seconds): columns sweep left to right, rows cascade down
COL_T, ROW_T, POP = 0.035, 0.06, 0.5

CSS = (
    f".c{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop {POP}s ease-out both}}"
    f".g{{animation:pop {POP}s ease-out both,flash {POP + 0.2}s ease-out both}}"
    "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.15)}"
    "100%{opacity:1;transform:scale(1)}}"
    "@keyframes flash{0%,40%{filter:brightness(2.2)}100%{filter:brightness(1)}}"
    ".f{opacity:0;animation:fade .6s ease-out both}"
    "@keyframes fade{to{opacity:1}}"
)


def weeks(days):
    """Columns of 7 (Sunday first); None pads the first and last week."""
    first = datetime.date.fromisoformat(days[0]["date"])
    col = [None] * ((first.weekday() + 1) % 7)
    out = []
    for d in days:
        col.append(d)
        if len(col) == 7:
            out.append(col)
            col = []
    if col:
        out.append(col + [None] * (7 - len(col)))
    return out


def render(data):
    grid = weeks(data["days"])
    left = PAD + LABEL_W
    top = 30 + MONTH_H + 6
    w = left + len(grid) * STEP - GAP + PAD
    h = top + 7 * STEP + FOOTER_H
    parts = window(w, h, f"{PROMPT}: ~/contributions --graph", CSS)

    labels = []   # (column, month name); a stub month too close to the next one is dropped
    for ci, col in enumerate(grid):
        first = next(c for c in col if c)
        if labels and first["date"][:7] == labels[-1][2]:
            continue
        if labels and ci - labels[-1][0] < 3:
            labels.pop()
        if ci < len(grid) - 2:
            labels.append((ci, datetime.date.fromisoformat(first["date"]).strftime("%b"), first["date"][:7]))
    for ci, label, _ in labels:
        parts.append(f'<text x="{left + ci * STEP}" y="{top - 9}" fill="{MUTED}" font-size="11">{label}</text>')
    for row, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(f'<text x="{PAD}" y="{top + row * STEP + CELL - 2}" fill="{MUTED}" font-size="10">{name}</text>')

    for ci, col in enumerate(grid):
        for ri, day in enumerate(col):
            if not day:
                continue
            delay = ci * COL_T + ri * ROW_T
            cls = "c g" if day["level"] else "c"
            plural = "" if day["count"] == 1 else "s"
            parts.append(
                f'<rect class="{cls}" x="{left + ci * STEP}" y="{top + ri * STEP}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" fill="{GREENS[day["level"]]}" style="animation-delay:{delay:.2f}s">'
                f'<title>{day["count"]} contribution{plural} on {short_date(day["date"])}</title></rect>'
            )

    done = (len(grid) - 1) * COL_T + 6 * ROW_T + POP
    foot = top + 7 * STEP + 10
    parts.append(f'<g class="f" style="animation-delay:{done:.2f}s">')
    lx = w - PAD - len(GREENS) * (CELL + 2) - 34
    parts.append(f'<text x="{lx - 6}" y="{foot + CELL - 2}" fill="{MUTED}" font-size="11" text-anchor="end">Less</text>')
    for i, colour in enumerate(GREENS):
        parts.append(f'<rect x="{lx + i * (CELL + 2)}" y="{foot}" width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"/>')
    parts.append(f'<text x="{lx + len(GREENS) * (CELL + 2) + 4}" y="{foot + CELL - 2}" fill="{MUTED}" font-size="11">More</text>')
    rng = data["range"]
    parts.append(
        f'<text x="{left}" y="{foot + 40}" font-size="14" fill="{GREEN}"><tspan font-weight="700">'
        f'{data["total_contributions"]:,}</tspan><tspan fill="{MUTED}"> contributions in the last year</tspan></text>'
    )
    parts.append(f'<text x="{w - PAD}" y="{foot + 40}" font-size="12" fill="{MUTED}" text-anchor="end">'
                 f'{esc(rng["start"])} <tspan fill="{INK}">&#8594;</tspan> {esc(rng["end"])}</text>')
    parts.append('</g></svg>')
    return "".join(parts)


if __name__ == "__main__":
    with open(SRC, encoding="utf-8") as f:
        svg = render(json.load(f))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)} ({len(svg) // 1024} KB)")
