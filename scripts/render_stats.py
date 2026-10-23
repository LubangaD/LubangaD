#!/usr/bin/env python3
"""
Draw the numbers card from data/contributions.json: six tiles that slide in and
count up to the real value, beside a monthly bar chart whose bars grow in.

The count-up is a stack of pre-drawn frames switched on and off with SMIL <set>,
because GitHub runs SMIL and CSS inside <img> SVGs but never JavaScript.

    python scripts/render_stats.py [data.json] [output.svg]
"""
import datetime
import json
import os
import sys

from terminal import CYAN, FRAME, GOLD, GREEN, INK, MUTED, PROMPT, TILE, short_date, window

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "contributions.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "stats.svg")

W = 860
PAD, GAP = 20, 12
COLS, ROWS = 3, 2
TILE_W, TILE_H = 150, 118
TOP = 30 + PAD
CHART_X = PAD + COLS * TILE_W + (COLS - 1) * GAP + GAP
CHART_W = W - PAD - CHART_X
H = TOP + ROWS * TILE_H + (ROWS - 1) * GAP + PAD

# timing (seconds)
STAGGER, SLIDE, COUNT, FRAMES = 0.15, 0.45, 1.2, 16
BAR_START = STAGGER * COLS * ROWS + 0.3
BAR_STAGGER, BAR_GROW = 0.07, 0.6

CSS = (
    f".t{{opacity:0;animation:in {SLIDE}s ease-out both}}"
    "@keyframes in{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}"
    f".b{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow {BAR_GROW}s ease-out both}}"
    "@keyframes grow{to{transform:scaleY(1)}}"
)


def span(streak):
    return f'{short_date(streak["start"])} – {short_date(streak["end"])}' if streak["length"] else "start one today"


def number(value, like):
    return f"{value:,.1f}" if isinstance(like, float) else f"{int(round(value)):,}"


def tiles(data):
    cur, lng, best = data["current_streak"], data["longest_streak"], data["best_day"]
    n = len(data["days"])
    # (label, value, suffix, caption, colour)
    return [
        ("current streak", cur["length"], " days", span(cur), GREEN),
        ("longest streak", lng["length"], " days", span(lng), CYAN),
        ("contributions", data["total_contributions"], "", "in the last year", INK),
        ("active days", data["active_days"], f" / {n}", f'{data["active_days"] / n:.0%} of the year', INK),
        ("best day", best["count"], "", short_date(best["date"]), GOLD),
        ("avg / active day", data["avg_per_active_day"], "", "contributions", INK),
    ]


def render(data):
    parts = window(W, H, f"{PROMPT}: ~$ ./stats.sh", CSS)

    for i, (label, value, suffix, caption, colour) in enumerate(tiles(data)):
        x = PAD + (i % COLS) * (TILE_W + GAP)
        y = TOP + (i // COLS) * (TILE_H + GAP)
        start = i * STAGGER
        parts.append(f'<g class="t" style="animation-delay:{start:.2f}s">')
        parts.append(f'<rect x="{x}" y="{y}" width="{TILE_W}" height="{TILE_H}" rx="9" fill="{TILE}" stroke="{FRAME}"/>')
        parts.append(f'<text x="{x + 14}" y="{y + 26}" fill="{MUTED}" font-size="12">$ {label}</text>')
        count_start = start + SLIDE * 0.6
        for k in range(1, FRAMES + 1):
            shown = value * (1 - (1 - k / FRAMES) ** 3)   # ease out into the real number
            on = count_start + COUNT * (k - 1) / FRAMES
            anim = f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>'
            if k < FRAMES:
                anim += f'<set attributeName="opacity" to="0" begin="{count_start + COUNT * k / FRAMES:.3f}s"/>'
            parts.append(
                f'<text x="{x + 14}" y="{y + 72}" opacity="0" font-size="32" font-weight="700" fill="{colour}">'
                f'{number(shown, value)}<tspan font-size="13" font-weight="400" fill="{MUTED}">{suffix}</tspan>{anim}</text>'
            )
        parts.append(f'<text x="{x + 14}" y="{y + 100}" fill="{MUTED}" font-size="11">{caption}</text>')
        parts.append('</g>')

    chart_h = H - PAD - TOP
    parts.append(f'<g class="t" style="animation-delay:{BAR_START - 0.3:.2f}s">')
    parts.append(f'<rect x="{CHART_X}" y="{TOP}" width="{CHART_W}" height="{chart_h}" rx="9" fill="{TILE}" stroke="{FRAME}"/>')
    parts.append(f'<text x="{CHART_X + 14}" y="{TOP + 26}" fill="{MUTED}" font-size="12">$ contributions / month</text>')
    parts.append('</g>')

    monthly = data["monthly"]
    plot_top, plot_bot = TOP + 58, TOP + chart_h - 30
    plot_l, plot_r = CHART_X + 14, CHART_X + CHART_W - 14
    slot = (plot_r - plot_l) / len(monthly)
    bar_w = slot * 0.62
    peak = max(m["total"] for m in monthly) or 1
    for i, m in enumerate(monthly):
        bh = max(2, (plot_bot - plot_top) * m["total"] / peak)
        bx = plot_l + i * slot + (slot - bar_w) / 2
        delay = BAR_START + i * BAR_STAGGER
        top_bar = m["total"] == peak
        parts.append(f'<rect class="b" x="{bx:.1f}" y="{plot_bot - bh:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2" '
                     f'fill="{GREEN if top_bar else "#26a641"}" style="animation-delay:{delay:.2f}s">'
                     f'<title>{m["month"]}: {m["total"]:,}</title></rect>')
        initial = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")[0]
        parts.append(f'<text x="{bx + bar_w / 2:.1f}" y="{plot_bot + 18}" fill="{MUTED}" font-size="10" '
                     f'text-anchor="middle">{initial}</text>')
        if top_bar:
            parts.append(f'<text class="t" style="animation-delay:{delay + BAR_GROW:.2f}s" x="{bx + bar_w / 2:.1f}" '
                         f'y="{plot_bot - bh - 7:.1f}" fill="{INK}" font-size="11" text-anchor="middle">{peak:,}</text>')

    parts.append('</svg>')
    return "".join(parts)


if __name__ == "__main__":
    with open(SRC, encoding="utf-8") as f:
        svg = render(json.load(f))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {os.path.normpath(OUT)} ({len(svg) // 1024} KB)")
