"""
Shared look for every profile SVG: a dark terminal window with a title bar and
the three traffic-light dots. GitHub shows SVGs through <img>, which runs CSS
keyframes and SMIL but never JavaScript, so all motion lives inside each file.
"""
import datetime
import html

PROMPT = "derrick@github"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

BG = "#0d1117"
BG2 = "#111722"
TILE = "#161b22"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#e6edf3"
SOFT = "#c9d1d9"
GREEN = "#39d353"
CYAN = "#22d3ee"
GOLD = "#f2cc60"
AMBER = "#f5a623"   # AbleSpeak accent
GREENS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]   # GitHub levels 0-4

TITLEBAR_H = 30
CARD_W, CARD_H = 840, 880   # portrait and info card share a canvas so they sit level side by side
REDUCED_MOTION = ("@media (prefers-reduced-motion: reduce){*{animation:none!important;"
                  "opacity:1!important;transform:none!important}}")


def esc(text):
    return html.escape(str(text), quote=False)


def short_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d:%b} {d.day}"


def window(w, h, title, css="", pad=20):
    """Opening tag, styles and window chrome. Close with '</svg>'."""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'font-family="{FONT}">',
        f'<style>{css}{REDUCED_MOTION}</style>',
        f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#bg)"/>',
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{w}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{pad + i * 16}" cy="{TITLEBAR_H / 2}" r="5" fill="{dot}"/>')
    parts.append(f'<text x="{w / 2}" y="{TITLEBAR_H / 2 + 4}" fill="{MUTED}" font-size="12" '
                 f'text-anchor="middle">{esc(title)}</text>')
    return parts
