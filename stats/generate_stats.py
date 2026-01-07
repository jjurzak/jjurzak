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
        "card_bg": "#161B22",
        "fg": "#C9D1D9",
        "title": "#58A6FF",
        "accent": "#1F6FEB",
        "border": "#30363D",
        "date": "#8B949E",
        "graph_bar": "#39D353",
        "graph_bg": "#0D1117",
        "gradient_start": "#7C3AED",
        "gradient_end": "#2563EB",
    },
    "light": {
        "bg": "#FFFFFF",
        "card_bg": "#F6F8FA",
        "fg": "#24292F",
        "title": "#0969DA",
        "accent": "#1F6FEB",
        "border": "#D0D7DE",
        "date": "#57606A",
        "graph_bar": "#2DA44E",
        "graph_bg": "#F6F8FA",
        "gradient_start": "#7C3AED",
        "gradient_end": "#2563EB",
    }
}

COLORS = THEMES.get(MODE, THEMES["dark"])

now = datetime.utcnow().strftime("%b %d, %Y")

# Language colors (GitHub standard colors)
LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "Java": "#B07219",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Jupyter Notebook": "#DA5B0B",
    "CSS": "#563D7C",
    "HTML": "#E34C26",
    "Shell": "#89E051",
    "R": "#198CE7",
    "Scala": "#C22D40",
    "Dart": "#00B4AB",
    "Answer Set Programming": "#4DB8A3",
}

def get_lang_color(lang):
    return LANG_COLORS.get(lang, COLORS["accent"])

# ==================== SVG CARD 1: OVERVIEW ====================

overview_svg = f"""<svg width="495" height="195" viewBox="0 0 495 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{COLORS['gradient_start']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{COLORS['gradient_end']};stop-opacity:1" />
    </linearGradient>
    
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .card {{ filter: drop-shadow(0 4px 12px rgba(0,0,0,0.25)); }}
      .bg {{ fill: {COLORS['card_bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .username {{ fill: {COLORS['date']}; font-size: 14px; font-weight: 500; font-family: 'Inter', sans-serif; }}
      .stat-label {{ fill: {COLORS['date']}; font-size: 12px; font-weight: 500; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.5px; }}
      .stat-value {{ fill: {COLORS['title']}; font-size: 32px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .footer {{ fill: {COLORS['date']}; font-size: 10px; font-family: 'Inter', sans-serif; }}
      .icon-circle {{ fill: url(#grad1); opacity: 0.15; }}
      .divider {{ stroke: {COLORS['border']}; stroke-width: 1; opacity: 0.5; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect class="card bg" x="0" y="0" width="495" height="195" rx="10"/>
  <rect x="0" y="0" width="495" height="195" rx="10" class="border"/>
  
  <!-- Decorative circles -->
  <circle class="icon-circle" cx="450" cy="40" r="60"/>
  <circle class="icon-circle" cx="40" cy="160" r="40"/>

  <!-- Header -->
  <text x="24" y="38" class="title">GitHub Stats</text>
  <text x="24" y="58" class="username">@{USERNAME}</text>

  <!-- Dividers -->
  <line x1="165" y1="85" x2="165" y2="150" class="divider"/>
  <line x1="330" y1="85" x2="330" y2="150" class="divider"/>

  <!-- Stats grid -->
  <g>
    <!-- Public Repos -->
    <text x="82" y="125" text-anchor="middle" class="stat-value">{public_repos}</text>
    <text x="82" y="145" text-anchor="middle" class="stat-label">Repositories</text>

    <!-- Followers -->
    <text x="247" y="125" text-anchor="middle" class="stat-value">{followers}</text>
    <text x="247" y="145" text-anchor="middle" class="stat-label">Followers</text>

    <!-- 30-day activity -->
    <text x="412" y="125" text-anchor="middle" class="stat-value">{streak}</text>
    <text x="412" y="145" text-anchor="middle" class="stat-label">Events (30d)</text>
  </g>

  <!-- Footer -->
  <text x="24" y="180" class="footer">↻ Updated {now}</text>
</svg>"""

# ==================== SVG CARD 2: TOP LANGUAGES ====================

lang_items = []
total_bytes = sum(b for _, b in top_langs)

y_start = 75
for i, (lang, bytes_used) in enumerate(top_langs):
    percent = (bytes_used / total_bytes * 100) if total_bytes > 0 else 0
    bar_width = (percent / 100) * 300
    
    y_pos = y_start + i * 45
    color = get_lang_color(lang)
    
    # Format size
    if bytes_used >= 1024 * 1024:
        size_str = f"{round(bytes_used / (1024 * 1024), 1)} MB"
    else:
        size_str = f"{round(bytes_used / 1024)} KB"

    lang_items.append(f"""
    <!-- {lang} -->
    <g opacity="0.95">
      <text x="24" y="{y_pos}" class="lang-name">{lang}</text>
      <text x="24" y="{y_pos + 18}" class="lang-percent">{percent:.1f}%</text>
      <text x="455" y="{y_pos + 18}" text-anchor="end" class="lang-size">{size_str}</text>
      
      <!-- Progress bar background -->
      <rect x="130" y="{y_pos + 5}" width="300" height="8" rx="4" fill="{COLORS['graph_bg']}" opacity="0.3"/>
      <!-- Progress bar -->
      <rect x="130" y="{y_pos + 5}" width="{bar_width}" height="8" rx="4" fill="{color}">
        <animate attributeName="width" from="0" to="{bar_width}" dur="0.8s" fill="freeze"/>
      </rect>
    </g>
  """)

height = y_start + len(top_langs) * 45 + 25
lang_section = "\n".join(lang_items)

langs_svg = f"""<svg width="495" height="{height}" viewBox="0 0 495 {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .bg {{ fill: {COLORS['card_bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .lang-name {{ fill: {COLORS['fg']}; font-size: 15px; font-weight: 600; font-family: 'Inter', sans-serif; }}
      .lang-percent {{ fill: {COLORS['title']}; font-size: 13px; font-weight: 700; font-family: 'Inter', monospace; }}
      .lang-size {{ fill: {COLORS['date']}; font-size: 11px; font-family: 'Inter', monospace; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="495" height="{height}" rx="10" class="bg"/>
  <rect x="0" y="0" width="495" height="{height}" rx="10" class="border"/>

  <!-- Header -->
  <text x="24" y="38" class="title">💻 Top Languages</text>

  <!-- Language bars -->
  {lang_section}
</svg>"""

# ==================== SVG CARD 3: WEEKLY ACTIVITY ====================

days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
max_activity = max([weekly.get(d, 0) for d in days_short], default=1)

activity_bars = []
bar_spacing = 60
start_x = 40

for i, day in enumerate(days_short):
    count = weekly.get(day, 0)
    bar_height = max((count / max(max_activity, 1)) * 90, 3) if count > 0 else 0
    
    x_pos = start_x + i * bar_spacing
    y_base = 145
    
    # Color intensity
    if count == 0:
        bar_color = COLORS['graph_bg']
        opacity = 0.3
    else:
        bar_color = COLORS['graph_bar']
        opacity = 0.5 + (count / max(max_activity, 1)) * 0.5

    activity_bars.append(f"""
    <!-- {day} -->
    <g>
      <rect x="{x_pos}" y="{y_base - bar_height}" width="45" height="{bar_height}" rx="6" 
            fill="{bar_color}" opacity="{opacity}">
        <animate attributeName="height" from="0" to="{bar_height}" dur="0.6s" begin="{i * 0.1}s" fill="freeze"/>
        <animate attributeName="y" from="{y_base}" to="{y_base - bar_height}" dur="0.6s" begin="{i * 0.1}s" fill="freeze"/>
      </rect>
      {f'<text x="{x_pos + 22.5}" y="{y_base - bar_height - 10}" text-anchor="middle" class="count">{count}</text>' if count > 0 else ''}
      <text x="{x_pos + 22.5}" y="{y_base + 20}" text-anchor="middle" class="day-label">{day}</text>
    </g>
  """)

activity_section = "\n".join(activity_bars)

weekly_svg = f"""<svg width="495" height="195" viewBox="0 0 495 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .bg {{ fill: {COLORS['card_bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .subtitle {{ fill: {COLORS['date']}; font-size: 13px; font-weight: 500; font-family: 'Inter', sans-serif; }}
      .day-label {{ fill: {COLORS['date']}; font-size: 11px; font-weight: 600; font-family: 'Inter', sans-serif; }}
      .count {{ fill: {COLORS['title']}; font-size: 12px; font-weight: 700; font-family: 'Inter', monospace; }}
      .baseline {{ stroke: {COLORS['border']}; stroke-width: 1; opacity: 0.3; stroke-dasharray: 4,4; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="495" height="195" rx="10" class="bg"/>
  <rect x="0" y="0" width="495" height="195" rx="10" class="border"/>

  <!-- Header -->
  <text x="24" y="38" class="title">📈 Weekly Activity</text>
  <text x="24" y="58" class="subtitle">Last 7 days</text>

  <!-- Baseline -->
  <line x1="40" y1="145" x2="455" y2="145" class="baseline"/>

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
<p align="center">
  <img src="stats/overview.svg" alt="GitHub Stats" />
  <img src="stats/languages.svg" alt="Top Languages" />
  <img src="stats/weekly.svg" alt="Weekly Activity" />
</p>
""")
