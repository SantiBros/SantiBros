"""Fills the "Latest releases" list in README.md from the ports' GitHub releases.

Run by .github/workflows/snake.yml. Only the text between the RELEASES markers changes.
"""
import json
import os
import re
import urllib.request

OWNER = os.environ.get("OWNER", "SantiBros")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = "README.md"
EMOJI = {"nfsmostwanted2012-android-switch": "🏎️", "spiderman2-2004-nx": "🕷️", "compendium-nx": "🃏"}
NAMES = {"nfsmostwanted2012-android-switch": "NFS Most Wanted 2012 (Android)",
         "compendium-nx": "Compendium (Persona mods)",
         "spiderman2-2004-nx": "Spider-Man 2 (Xbox)"}
START, END = "<!-- RELEASES:START -->", "<!-- RELEASES:END -->"


def api(path):
    req = urllib.request.Request("https://api.github.com/" + path)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    repos = [r for r in api(f"users/{OWNER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"].lower() != OWNER.lower()]
    rels = []
    for r in repos:
        for rel in api(f"repos/{OWNER}/{r['name']}/releases?per_page=10"):
            if rel["draft"]:
                continue
            key = r["name"].lower()
            rels.append((rel["published_at"], EMOJI.get(key, "🎮"), NAMES.get(key, r["name"]),
                         rel["tag_name"], rel["name"] or rel["tag_name"], rel["html_url"]))
    rels.sort(reverse=True)
    lines = []
    for date, emoji, port, tag, title, url in rels[:5]:
        title = title.replace("|", "-").strip()
        for prefix in (tag, tag.lstrip("vV")):
            if prefix and title.lower().startswith(prefix.lower()):
                title = title[len(prefix):].lstrip(" -–—:").strip()
                break
        if title.lower().rstrip(" .") .endswith((tag.lower(), tag.lstrip("vV").lower())) and len(title) <= len(tag) + 20:
            title = ""
        desc = f": {title}" if title else ""
        lines.append(f"- {emoji} **{port}** [{tag}]({url}){desc} <sub>({date[:10]})</sub>")
    block = START + "\n" + ("\n".join(lines) or "- No releases yet") + "\n" + END
    text = open(README, encoding="utf-8").read()
    new = re.sub(re.escape(START) + ".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
        print("README updated")
    else:
        print("No changes")


if __name__ == "__main__":
    main()
