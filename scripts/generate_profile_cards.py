#!/usr/bin/env python3
import json, os, urllib.request, html
from collections import Counter

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT_DIR", "dist")
USER = "sinavm"
os.makedirs(OUT, exist_ok=True)

def gql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "sinavm-profile-cards",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        payload = json.loads(r.read().decode())
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    return payload["data"]

QUERY = '''
{
  user(login: "USER_LOGIN") {
    name
    followers { totalCount }
    repositories(first: 50, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        stargazerCount
        forkCount
        primaryLanguage { name color }
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
    pullRequests { totalCount }
    issues { totalCount }
  }
}
'''.replace("USER_LOGIN", USER)

data = gql(QUERY)

u = data["user"]
repos = u["repositories"]["nodes"]
stars = sum(r["stargazerCount"] for r in repos)
contrib = u["contributionsCollection"]["contributionCalendar"]["totalContributions"]
followers = u["followers"]["totalCount"]
pr = u["pullRequests"]["totalCount"]
issues = u["issues"]["totalCount"]
repo_count = u["repositories"]["totalCount"]

lang_size = Counter()
lang_color = {}
for r in repos:
    for e in r["languages"]["edges"]:
        name = e["node"]["name"]
        lang_size[name] += e["size"]
        lang_color[name] = e["node"]["color"] or "#8B8CF8"

top_langs = lang_size.most_common(6)
total_lang = sum(v for _, v in top_langs) or 1

def esc(s):
    return html.escape("" if s is None else str(s))

def card(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none">'
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="12" fill="#0D0B1A" stroke="#2A2750"/>'
        f'{body}</svg>'
    )

rows = [
    ("Repos", repo_count),
    ("Stars", stars),
    ("Followers", followers),
    ("Contributions", contrib),
    ("Pull requests", pr),
    ("Issues", issues),
]
lines = []
for i, (label, val) in enumerate(rows):
    y = 58 + i * 22
    lines.append(f'<text x="28" y="{y}" fill="#A3A0C2" font-family="Verdana, sans-serif" font-size="13">{esc(label)}</text>')
    lines.append(f'<text x="230" y="{y}" fill="#EDE9FE" font-family="Verdana, sans-serif" font-size="13" font-weight="700">{val:,}</text>')
stats = card(360, 200, (
    '<text x="28" y="32" fill="#8B8CF8" font-family="Verdana, sans-serif" font-size="16" font-weight="700">GitHub stats</text>'
    f'<text x="28" y="48" fill="#6B6888" font-family="Verdana, sans-serif" font-size="11">@{USER}</text>'
    + ''.join(lines)
))
open(f"{OUT}/stats.svg", "w").write(stats)

bar_y = 58
lang_body = ['<text x="28" y="32" fill="#8B8CF8" font-family="Verdana, sans-serif" font-size="16" font-weight="700">Top languages</text>']
x = 28
for name, size in top_langs:
    w = max(4, int(304 * size / total_lang))
    color = lang_color.get(name, "#8B8CF8")
    lang_body.append(f'<rect x="{x}" y="{bar_y}" width="{w}" height="10" fill="{color}"/>')
    x += w
ly = 88
for name, size in top_langs:
    pct = size * 100 / total_lang
    color = lang_color.get(name, "#8B8CF8")
    lang_body.append(f'<circle cx="34" cy="{ly-4}" r="4" fill="{color}"/>')
    lang_body.append(f'<text x="46" y="{ly}" fill="#D3D3D3" font-family="Verdana, sans-serif" font-size="12">{esc(name)}  {pct:.1f}%</text>')
    ly += 20
langs = card(360, 88 + 20 * len(top_langs) + 8, ''.join(lang_body))
open(f"{OUT}/langs.svg", "w").write(langs)

pins = [
    ("sinavm", "pin-sinavm.svg"),
    ("SVM", "pin-svm.svg"),
    ("melishekan", "pin-melishekan.svg"),
    ("sing-box", "pin-singbox.svg"),
]
by_name = {r["name"]: r for r in repos}
for name, fname in pins:
    r = by_name.get(name)
    if not r:
        continue
    desc = (r["description"] or "").replace("\n", " ")
    if len(desc) > 78:
        desc = desc[:75] + "..."
    lang = (r["primaryLanguage"] or {}).get("name") or ""
    lcolor = (r["primaryLanguage"] or {}).get("color") or "#8B8CF8"
    body = (
        f'<text x="22" y="32" fill="#8B8CF8" font-family="Verdana, sans-serif" font-size="16" font-weight="700">{esc(name)}</text>'
        f'<text x="22" y="58" fill="#C9C6E0" font-family="Verdana, sans-serif" font-size="12">{esc(desc)}</text>'
        f'<circle cx="28" cy="88" r="4" fill="{lcolor}"/>'
        f'<text x="38" y="92" fill="#A3A0C2" font-family="Verdana, sans-serif" font-size="12">{esc(lang)}</text>'
        f'<text x="140" y="92" fill="#A3A0C2" font-family="Verdana, sans-serif" font-size="12">* {r["stargazerCount"]}</text>'
        f'<text x="220" y="92" fill="#A3A0C2" font-family="Verdana, sans-serif" font-size="12">fork {r["forkCount"]}</text>'
    )
    open(f"{OUT}/{fname}", "w").write(card(400, 120, body))

streak = card(360, 120, (
    '<text x="28" y="32" fill="#8B8CF8" font-family="Verdana, sans-serif" font-size="16" font-weight="700">Activity</text>'
    '<text x="28" y="68" fill="#A3A0C2" font-family="Verdana, sans-serif" font-size="13">Contributions this year</text>'
    f'<text x="28" y="96" fill="#EDE9FE" font-family="Verdana, sans-serif" font-size="28" font-weight="700">{contrib:,}</text>'
))
open(f"{OUT}/streak.svg", "w").write(streak)
print("wrote cards to", OUT)
