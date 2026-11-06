"""Builds the profile's stats and languages cards from the GitHub API.

Run by .github/workflows/snake.yml. Writes dist/stats.svg and dist/languages.svg.
"""
import json
import os
import sys
import urllib.request
from html import escape

OWNER = os.environ.get("OWNER", "SantiBros")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist"

BG, ORANGE, TEXT, MUTED, LINE = "#0E0B1A", "#FF6A2B", "#F5F1EA", "#CFC8D8", "#2b2f38"
LANG_COLORS = ["#FF6A2B", "#FFA47F", "#C44F22", "#8B5CF6", "#22C3A6", "#CFC8D8"]


def api(path):
    req = urllib.request.Request("https://api.github.com/" + path)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    repos = [r for r in api(f"users/{OWNER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"].lower() != OWNER.lower()]
    stats = {"repos": len(repos), "stars": 0, "forks": 0, "releases": 0, "downloads": 0}
    langs = {}
    for r in repos:
        stats["stars"] += r["stargazers_count"]
        stats["forks"] += r["forks_count"]
        for rel in api(f"repos/{OWNER}/{r['name']}/releases?per_page=100"):
            stats["releases"] += 1
            stats["downloads"] += sum(a["download_count"] for a in rel.get("assets", []))
        for lang, size in api(f"repos/{OWNER}/{r['name']}/languages").items():
            langs[lang] = langs.get(lang, 0) + size
    return stats, langs


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def card(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<style>text{{font-family:"Segoe UI",Ubuntu,"Helvetica Neue",Arial,sans-serif}}</style>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{LINE}"/>'
            f'<text x="25" y="38" fill="{ORANGE}" font-size="18" font-weight="700">{escape(title)}</text>'
            f'{body}</svg>')


def stats_svg(s):
    rows = [("Projects released", s["repos"]), ("Releases", s["releases"]),
            ("Total downloads", s["downloads"]), ("Stars", s["stars"]), ("Forks", s["forks"])]
    body = ""
    for i, (label, val) in enumerate(rows):
        y = 74 + i * 26
        body += (f'<rect x="25" y="{y - 10}" width="8" height="8" rx="2" fill="{ORANGE}"/>'
                 f'<text x="43" y="{y - 1}" fill="{MUTED}" font-size="14">{label}</text>'
                 f'<text x="370" y="{y - 1}" fill="{TEXT}" font-size="14" font-weight="700" text-anchor="end">{fmt(val)}</text>')
    return card(400, 205, f"{OWNER}' project stats", body)


def langs_svg(langs):
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    body, x = "", 25.0
    for i, (lang, size) in enumerate(top):
        w = 300 * size / total
        body += f'<rect x="{x:.1f}" y="56" width="{max(w, 1):.1f}" height="10" fill="{LANG_COLORS[i]}"/>'
        x += w
    body = f'<clipPath id="c"><rect x="25" y="56" width="300" height="10" rx="5"/></clipPath><g clip-path="url(#c)">{body}</g>'
    for i, (lang, size) in enumerate(top):
        col, row = i % 2, i // 2
        cx, cy = 25 + col * 150, 96 + row * 30
        body += (f'<circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{LANG_COLORS[i]}"/>'
                 f'<text x="{cx + 16}" y="{cy}" fill="{TEXT}" font-size="13">{escape(lang)} '
                 f'<tspan fill="{MUTED}">{100 * size / total:.1f}%</tspan></text>')
    return card(350, 205, "Top languages", body)


def achievements_svg(s, langs):
    items = [
        ("🚀", "First release", s["releases"] >= 1),
        ("📦", "10+ releases", s["releases"] >= 10),
        ("⬇️", "1k downloads", s["downloads"] >= 1000),
        ("🔥", "10k downloads", s["downloads"] >= 10000),
        ("⭐", "25+ stars", s["stars"] >= 25),
        ("🌟", "100+ stars", s["stars"] >= 100),
        ("🎮", "3 projects", s["repos"] >= 3),
        ("🕹️", "5 projects", s["repos"] >= 5),
    ]
    body = ""
    for i, (icon, label, done) in enumerate(items):
        col, row = i % 4, i // 4
        x, y = 25 + col * 182, 60 + row * 64
        fill, stroke, txt = ("#1C1630", ORANGE, TEXT) if done else (BG, LINE, "#6B6478")
        op = "1" if done else "0.35"
        body += (f'<rect x="{x}" y="{y}" width="170" height="52" rx="10" fill="{fill}" stroke="{stroke}"/>'
                 f'<text x="{x + 16}" y="{y + 33}" font-size="20" opacity="{op}">{icon}</text>'
                 f'<text x="{x + 48}" y="{y + 32}" fill="{txt}" font-size="14" font-weight="700">{escape(label)}</text>')
    return card(770, 200, "Achievements", body)


def main():
    stats, langs = collect()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "stats.svg"), "w", encoding="utf-8") as f:
        f.write(stats_svg(stats))
    with open(os.path.join(OUT, "languages.svg"), "w", encoding="utf-8") as f:
        f.write(langs_svg(langs))
    with open(os.path.join(OUT, "achievements.svg"), "w", encoding="utf-8") as f:
        f.write(achievements_svg(stats, langs))
    print(stats, sorted(langs.items(), key=lambda kv: -kv[1])[:6])


if __name__ == "__main__":
    main()
