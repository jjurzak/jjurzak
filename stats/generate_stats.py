import os, requests, json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

USERNAME = "jjurzak"
HEADERS = {"Accept": "application/vnd.github+json"}

def fetch(url):
    r = requests.get(url, headers=HEADERS)
    if r.status_code == 403:
        return None
    return r.json()

# --- User stats (repos + followers) ---
user = fetch(f"https://api.github.com/users/{USERNAME}") or {}
repos = fetch(f"https://api.github.com/users/{USERNAME}/repos?per_page=100") or []

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)

# --- Language aggregation ---
lang_usage = defaultdict(int)
for repo in repos:
    langs = fetch(repo["languages_url"]) or {}
    for lang, bytes_used in langs.items():
        lang_usage[lang] += bytes_used

top_langs = sorted(lang_usage.items(), key=lambda x: x[1], reverse=True)[:6]

# --- Weekly commits (past 7 days) ---
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
cutoff = datetime.utcnow() - timedelta(days=7)

weekly = Counter()
for evt in events:
    try:
        t = datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    except:
        continue
    if t < cutoff: continue
    day = t.strftime("%a")
    weekly[day] += 1

days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
weekly_lines = "\n".join(
    f'<text x="20" y="{60 + i*18}" class="text">{d}: {weekly.get(d,0)}</text>'
    for i,d in enumerate(days)
)

# --- Commit streak (past 30 days)
cutoff30 = datetime.utcnow() - timedelta(days=30)
streak_events = [evt for evt in events if "created_at" in evt]
streak = sum(
    1 for evt in streak_events
    if datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ") > cutoff30
)

# --- Theme detection via ENV (dark default)
MODE = os.getenv("THEME","dark")
BG = "#FFFFFF" if MODE == "light" else "#0D1117"
FG = "#1F2328" if MODE == "light" else "#C9D1D9"
TITLE = "#0969DA" if MODE == "light" else "#58A6FF"
DATE = "#57606A" if MODE == "light" else "#6E7681"
BORDER = "#D0D7DE" if MODE == "light" else "#30363D"

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# === CARD 1: Overview ===
overview = f"""
<svg width="420" height="160" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="10" fill="{BG}"/>
  <rect x="2" y="2" width="416" height="156" rx="10" fill="none" stroke="{BORDER}" stroke-width="2"/>
  <style>
    .title {{ fill: {TITLE}; font-size: 18px; font-family: Consolas, monospace; font-weight: 600; }}
    .text {{ fill: {FG}; font-size: 14px; font-family: Consolas, monospace; }}
    .date {{ fill: {DATE}; font-size: 12px; font-family: Consolas, monospace; }}
  </style>
  <text x="20" y="35" class="title">GitHub Stats — {USERNAME}</text>
  <text x="20" y="70" class="text">📁 Public repos: {public_repos}</text>
  <text x="20" y="95" class="text">⭐ Followers: {followers}</text>
  <text x="20" y="120" class="text">🔥 30-day activity: {streak} events</text>
  <text x="20" y="145" class="date">Updated: {now}</text>
</svg>
"""
open("stats/card.svg","w").write(overview)

# === CARD 2: Top Languages ===
height = 60 + len(top_langs)*18
lang_lines = "\n".join(
    f'<text x="20" y="{60 + i*18}" class="text">• {lang}: {round(bytes_used/1024)} KB</text>'
    for i, (lang, bytes_used) in enumerate(top_langs)
) or '<text x="20" y="60" class="text">No language data</text>'

langs_svg = f"""
<svg width="420" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="10" fill="{BG}"/>
  <rect x="2" y="2" width="416" height="{height-4}" rx="10" fill="none" stroke="{BORDER}" stroke-width="2"/>
  <style>
    .title {{ fill: {TITLE}; font-size: 18px; font-family: Consolas, monospace; font-weight: 600; }}
    .text {{ fill: {FG}; font-size: 14px; font-family: Consolas, monospace; }}
  </style>
  <text x="20" y="35" class="title">Top Languages</text>
  {lang_lines}
</svg>
"""
open("stats/langs.svg","w").write(langs_svg)

# === CARD 3: Weekly commits ===
weekly_svg = f"""
<svg width="420" height="190" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" rx="10" fill="{BG}"/>
  <rect x="2" y="2" width="416" height="186" rx="10" fill="none" stroke="{BORDER}" stroke-width="2"/>
  <style>
    .title {{ fill: {TITLE}; font-size: 18px; font-family: Consolas, monospace; font-weight: 600; }}
    .text {{ fill: {FG}; font-size: 14px; font-family: Consolas, monospace; }}
  </style>
  <text x="20" y="35" class="title">Weekly Activity</text>
  {weekly_lines}
</svg>
"""
open("stats/weekly.svg","w").write(weekly_svg)
