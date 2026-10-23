#!/usr/bin/env python3
"""
Read the last year of daily contribution counts from GitHub's public
contributions fragment (the same HTML the profile page loads) and write
data/contributions.json with the days plus a few derived numbers.

Standard library only, no token. Run daily by .github/workflows/profile-art.yml.

    python scripts/fetch_contributions.py [username]
"""
import datetime
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PROFILE_USER", "LubangaD")
URL = f"https://github.com/users/{USER}/contributions"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "contributions.json")


class CalendarParser(HTMLParser):
    """Collects <td class="ContributionCalendar-day"> cells and their <tool-tip> labels."""

    def __init__(self):
        super().__init__()
        self.cells = {}      # cell id -> {date, level}
        self.tips = {}       # cell id -> tooltip text
        self._tip_for = None
        self._tip_text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (a.get("class") or "") and a.get("data-date"):
            self.cells[a.get("id")] = {"date": a["data-date"], "level": int(a.get("data-level") or 0)}
        elif tag == "tool-tip" and a.get("for"):
            self._tip_for, self._tip_text = a["for"], []

    def handle_data(self, data):
        if self._tip_for:
            self._tip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._tip_for:
            self.tips[self._tip_for] = "".join(self._tip_text).strip()
            self._tip_for = None


def fetch_days():
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-readme-bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8")

    parser = CalendarParser()
    parser.feed(html)
    if not parser.cells:
        sys.exit("no calendar cells found; GitHub's markup may have changed")

    days = []
    for cell_id, cell in parser.cells.items():
        tip = parser.tips.get(cell_id, "")
        m = re.match(r"([\d,]+) contribution", tip)
        count = int(m.group(1).replace(",", "")) if m else 0
        days.append({"date": cell["date"], "count": count, "level": cell["level"]})
    days.sort(key=lambda d: d["date"])
    return days


def streak_ending_at(days, end):
    start = end
    while start >= 0 and days[start]["count"] > 0:
        start -= 1
    return end - start, start + 1


def current_streak(days):
    end = len(days) - 1
    if days[end]["count"] == 0:
        end -= 1  # today isn't over yet, so an empty today doesn't break the streak
    length, start = streak_ending_at(days, end)
    if not length:
        return {"length": 0, "start": None, "end": None}
    return {"length": length, "start": days[start]["date"], "end": days[end]["date"]}


def longest_streak(days):
    best = {"length": 0, "start": None, "end": None}
    run_start = None
    for i, d in enumerate(days):
        if d["count"] == 0:
            run_start = None
            continue
        if run_start is None:
            run_start = i
        if i - run_start + 1 > best["length"]:
            best = {"length": i - run_start + 1, "start": days[run_start]["date"], "end": d["date"]}
    return best


def summarise(days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"])
    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "username": USER,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active,
        "avg_per_active_day": round(total / active, 1) if active else 0,
        "current_streak": current_streak(days),
        "longest_streak": longest_streak(days),
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "days": days,
    }


if __name__ == "__main__":
    data = summarise(fetch_days())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {os.path.normpath(OUT)}: {data['total_contributions']} contributions, "
          f"streak {data['current_streak']['length']} (longest {data['longest_streak']['length']})")
