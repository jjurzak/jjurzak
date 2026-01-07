import os
import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

USERNAME = "jjurzak"
HEADERS = {"Accept": "application/vnd.github+json"}

def fetch(url):
    """Fetch data from GitHub API"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 403:
            return None
        return r.json()
    except:
        return None

# ==================== DATA COLLECTION ====================

print("📊 Fetching GitHub stats...")

# User stats
user = fetch(f"https://api.github.com/users/{USERNAME}") or {}
repos = fetch(f"https://api.github.com/users/{USERNAME}/repos?per_page=100") or []

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)
bio = user.get("bio", "")

# Language aggregation
print("📝 Processing languages...")
lang_usage = defaultdict(int)
for repo in repos:
    langs = fetch(repo["languages_url"]) or {}
    for lang, bytes_used in langs.items():
        lang_usage[lang] += bytes_used

top_langs = sorted(lang_usage.items(), key=lambda x: x[1], reverse=True)[:6]

# Weekly activity
print("📈 Analyzing activity...")
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
cutoff = datetime.utcnow() - timedelta(days=7)
cutoff30 = datetime.utcnow() - timedelta(days=30)

weekly = Counter()
for evt in events:
    try:
        t = datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if t >= cutoff:
            day = t.strftime("%a")
            weekly[day] += 1
    except:
        continue

streak = sum(
    1 for evt in events
    if "created_at" in evt and
    datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ") >= cutoff30
)

# ==================== COLOR THEME ====================

MODE = os.getenv("THEME", "dark").lower()

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "fg": "#C9D1D9",
        "title": "#58A6FF",
        "accent": "#1F6FEB",
        "border": "#30363D",
        "date": "#6E7681",
        "graph_bar": "#1F6FEB",
        "graph_bg": "#161B22",
    },
    "light": {
        "bg": "#FFFFFF",
        "fg": "#24292F",
        "title": "#0969DA",
        "accent": "#1F6FEB",
        "border": "#D0D7DE",
        "date": "#57606A",
        "graph_bar": "#0969DA",
        "graph_bg": "#F6F8FA",
    }
}

COLORS = THEMES.get(MODE, THEMES["dark"])
BG = COLORS["bg"]
FG = COLORS["fg"]
TITLE = COLORS["title"]
ACCENT = COLORS["accent"]
BORDER = COLORS["border"]
DATE = COLORS["date"]
GRAPH_BAR = COLORS["graph_bar"]
GRAPH_BG = COLORS["graph_bg"]

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

# ==================== SVG CARD 1: OVERVIEW ====================

overview_svg = f"""<svg width="480" height="200" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .card {{ filter: drop-shadow(0 2px 8px rgba(0,0,0,0.15)); }}
      .bg {{ fill: {BG}; }}
      .border {{ fill: none; stroke: {BORDER}; stroke-width: 1.5; }}
      .title {{ fill: {TITLE}; font-size: 20px; font-weight: 700; font-family: 'Segoe UI', sans-serif; }}
      .stat-label {{ fill: {FG}; font-size: 13px; font-weight: 500; font-family: 'Segoe UI', sans-serif; opacity: 0.8; }}
      .stat-value {{ fill: {TITLE}; font-size: 24px; font-weight: 700; font-family: 'Monaco', monospace; }}
      .footer {{ fill: {DATE}; font-size: 11px; font-family: 'Monaco', monospace; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect class="card" x="0" y="0" width="480" height="200" rx="12" class="bg"/>
  <rect x="0" y="0" width="480" height="200" rx="12" class="border"/>

  <!-- Header -->
  <text x="20" y="35" class="title">📊 GitHub Stats</text>
  <text x="20" y="55" class="stat-label">@{USERNAME}</text>

  <!-- Stats grid -->
  <g>
    <!-- Repos -->
    <text x="30" y="95" class="stat-value">{public_repos}</text>
    <text x="30" y="115" class="stat-label">Public Repos</text>

    <!-- Followers -->
    <text x="180" y="95" class="stat-value">{followers}</text>
    <text x="180" y="115" class="stat-label">Followers</text>

    <!-- 30-day activity -->
    <text x="330" y="95" class="stat-value">{streak}</text>
    <text x="330" y="115" class="stat-label">30-day Events</text>
  </g>

  <!-- Footer -->
  <text x="20" y="185" class="footer">↻ Updated: {now}</text>
</svg>"""

# ==================== SVG CARD 2: TOP LANGUAGES ====================

# Build language bars
lang_items = []
max_bytes = max([b for _, b in top_langs], default=1)

for i, (lang, bytes_used) in enumerate(top_langs):
    percent = (bytes_used / max_bytes) * 100 if max_bytes > 0 else 0
    bar_width = (percent / 100) * 340  # Max bar width

    y_pos = 60 + i * 38

    lang_items.append(f"""
    <!-- {lang} -->
    <text x="20" y="{y_pos + 5}" class="lang-name">{lang}</text>
    <text x="20" y="{y_pos + 25}" class="lang-size">{round(bytes_used/1024)} KB</text>

    <!-- Progress bar -->
    <rect x="140" y="{y_pos - 8}" width="340" height="6" rx="3" fill="{GRAPH_BG}"/>
    <rect x="140" y="{y_pos - 8}" width="{bar_width}" height="6" rx="3" fill="{GRAPH_BAR}"/>
  """)

lang_section = "\n".join(lang_items)
height = 60 + len(top_langs) * 38 + 20

langs_svg = f"""<svg width="480" height="{height}" viewBox="0 0 480 {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .bg {{ fill: {BG}; }}
      .border {{ fill: none; stroke: {BORDER}; stroke-width: 1.5; }}
      .title {{ fill: {TITLE}; font-size: 20px; font-weight: 700; font-family: 'Segoe UI', sans-serif; }}
      .lang-name {{ fill: {TITLE}; font-size: 14px; font-weight: 600; font-family: 'Monaco', monospace; }}
      .lang-size {{ fill: {DATE}; font-size: 12px; font-family: 'Monaco', monospace; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="480" height="{height}" rx="12" class="bg"/>
  <rect x="0" y="0" width="480" height="{height}" rx="12" class="border"/>

  <!-- Header -->
  <text x="20" y="35" class="title">💻 Top Languages</text>

  <!-- Language bars -->
  {lang_section}
</svg>"""

# ==================== SVG CARD 3: WEEKLY ACTIVITY ====================

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
max_activity = max([weekly.get(d, 0) for d in days], default=1)

activity_bars = []
for i, day in enumerate(days):
    count = weekly.get(day, 0)
    bar_height = (count / max(max_activity, 1)) * 80 if max_activity > 0 else 0

    x_pos = 30 + i * 60
    y_base = 140

    # Color intensity based on activity
    if count == 0:
        bar_color = GRAPH_BG
    else:
        opacity = 0.3 + (count / max(max_activity, 1)) * 0.7
        # Simple opacity calculation
        bar_color = GRAPH_BAR

    activity_bars.append(f"""
    <!-- {day} -->
    <text x="{x_pos + 15}" y="165" class="day-label">{day}</text>
    <rect x="{x_pos}" y="{y_base - bar_height}" width="40" height="{bar_height}" rx="4" 
          fill="{bar_color}" opacity="{0.3 + (count / max(max_activity, 1)) * 0.7 if max_activity > 0 else 0.2}"/>
    <text x="{x_pos + 8}" y="{y_base - bar_height - 8}" class="count">{count}</text>
  """)

activity_section = "\n".join(activity_bars)

weekly_svg = f"""<svg width="480" height="200" viewBox="0 0 480 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .bg {{ fill: {BG}; }}
      .border {{ fill: none; stroke: {BORDER}; stroke-width: 1.5; }}
      .title {{ fill: {TITLE}; font-size: 20px; font-weight: 700; font-family: 'Segoe UI', sans-serif; }}
      .day-label {{ fill: {DATE}; font-size: 12px; font-weight: 500; font-family: 'Monaco', monospace; text-anchor: middle; }}
      .count {{ fill: {TITLE}; font-size: 11px; font-weight: 600; font-family: 'Monaco', monospace; text-anchor: middle; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="480" height="200" rx="12" class="bg"/>
  <rect x="0" y="0" width="480" height="200" rx="12" class="border"/>

  <!-- Header -->
  <text x="20" y="35" class="title">📅 Weekly Activity</text>

  <!-- Activity bars -->
  {activity_section}
</svg>"""

# ==================== SAVE SVG FILES ====================

print("💾 Saving SVG files...")

os.makedirs("stats", exist_ok=True)

with open("stats/overview.svg", "w") as f:
    f.write(overview_svg)
    print("✅ stats/overview.svg")

with open("stats/languages.svg", "w") as f:
    f.write(langs_svg)
    print("✅ stats/languages.svg")

with open("stats/weekly.svg", "w") as f:
    f.write(weekly_svg)
    print("✅ stats/weekly.svg")

print("\n✨ Done! Use in README:")
print("""
![GitHub Stats](stats/overview.svg)
![Top Languages](stats/languages.svg)
![Weekly Activity](stats/weekly.svg)
""")
