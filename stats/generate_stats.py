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
following = user.get("following", 0)
created_at = user.get("created_at", "")

# Calculate account age
if created_at:
    account_created = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    account_age_days = (datetime.utcnow() - account_created).days
else:
    account_age_days = 0

# Repo stats
total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
total_forks = sum(repo.get("forks_count", 0) for repo in repos)

# Top repos by commits (excluding jjurzak repo)
print("🔍 Analyzing repo contributions...")
repo_stats = []
for repo in repos:
    if repo.get("fork", False) or repo.get("name") == "jjurzak":
        continue
    
    # Get commit count and activity
    stats_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/stats/contributors"
    stats = fetch(stats_url)
    
    commit_count = 0
    weekly_commits = []
    
    if stats:
        for contributor in stats:
            if contributor.get("author", {}).get("login") == USERNAME:
                commit_count = contributor.get("total", 0)
                # Get last 12 weeks of activity
                weeks = contributor.get("weeks", [])[-12:]
                weekly_commits = [w.get("c", 0) for w in weeks]
                break
    
    if commit_count > 0:  # Only include repos with commits
        repo_stats.append({
            "repo": repo,
            "commits": commit_count,
            "weekly": weekly_commits
        })

# Sort by commits
top_repos = sorted(repo_stats, key=lambda x: x["commits"], reverse=True)[:3]

# Language aggregation (excluding Jupyter)
print("📝 Processing languages...")
lang_usage = defaultdict(int)
for repo in repos:
    langs = fetch(repo["languages_url"]) or {}
    for lang, bytes_used in langs.items():
        if lang != "Jupyter Notebook":  # Skip Jupyter
            lang_usage[lang] += bytes_used

top_langs = sorted(lang_usage.items(), key=lambda x: x[1], reverse=True)[:5]

# Weekly activity
print("📈 Analyzing activity...")
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
cutoff = datetime.utcnow() - timedelta(days=7)
cutoff30 = datetime.utcnow() - timedelta(days=30)

weekly = Counter()
commit_hours = Counter()

for evt in events:
    try:
        t = datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if t >= cutoff:
            day = t.strftime("%a")
            weekly[day] += 1
        if t >= cutoff30:
            commit_hours[t.hour] += 1
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
    "CSS": "#563D7C",
    "HTML": "#E34C26",
    "Shell": "#89E051",
    "R": "#198CE7",
    "Scala": "#C22D40",
    "Dart": "#00B4AB",
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

# ==================== SVG CARD 2: TOP REPOS ====================

repo_items = []
y_start = 75

for i, item in enumerate(top_repos[:3]):
    repo = item["repo"]
    commits = item["commits"]
    weekly = item["weekly"]
    
    name = repo.get("name", "")
    desc = repo.get("description", "")
    lang = repo.get("language", "Code")
    
    # Truncate description
    if desc and len(desc) > 40:
        desc = desc[:37] + "..."
    elif not desc:
        desc = "No description"
    
    y_pos = y_start + i * 80
    lang_color = get_lang_color(lang)
    
    # Generate EKG-style line chart
    max_weekly = max(weekly) if weekly else 1
    ekg_points = []
    chart_width = 250
    chart_height = 25
    chart_x = 220
    chart_y = y_pos + 10
    
    for j, count in enumerate(weekly):
        x = chart_x + (j / max(len(weekly) - 1, 1)) * chart_width
        y = chart_y + chart_height - (count / max(max_weekly, 1)) * chart_height
        ekg_points.append(f"{x},{y}")
    
    ekg_path = " ".join(ekg_points)
    
    repo_items.append(f"""
    <!-- {name} -->
    <g opacity="0.95">
      <text x="24" y="{y_pos}" class="repo-name">{name}</text>
      <text x="24" y="{y_pos + 18}" class="repo-desc">{desc}</text>
      
      <g transform="translate(24, {y_pos + 28})">
        <circle cx="5" cy="0" r="5" fill="{lang_color}"/>
        <text x="15" y="4" class="repo-lang">{lang}</text>
        <text x="100" y="4" class="repo-stat">📝 {commits} commits</text>
      </g>
      
      <!-- EKG Chart -->
      <g opacity="0.8">
        <polyline points="{ekg_path}" fill="none" stroke="{lang_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <animate attributeName="stroke-dasharray" from="0,1000" to="1000,0" dur="1.5s" fill="freeze"/>
        </polyline>
        <!-- Glow effect -->
        <polyline points="{ekg_path}" fill="none" stroke="{lang_color}" stroke-width="5" opacity="0.3" stroke-linecap="round" stroke-linejoin="round"/>
      </g>
    </g>
  """)

height = y_start + len(top_repos) * 80 + 25
repo_section = "\n".join(repo_items)

repos_svg = f"""<svg width="495" height="{height}" viewBox="0 0 495 {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .bg {{ fill: {COLORS['card_bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .repo-name {{ fill: {COLORS['title']}; font-size: 16px; font-weight: 600; font-family: 'Inter', monospace; }}
      .repo-desc {{ fill: {COLORS['date']}; font-size: 12px; font-family: 'Inter', sans-serif; }}
      .repo-lang {{ fill: {COLORS['fg']}; font-size: 12px; font-family: 'Inter', sans-serif; }}
      .repo-stat {{ fill: {COLORS['date']}; font-size: 11px; font-family: 'Inter', monospace; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="495" height="{height}" rx="10" class="bg"/>
  <rect x="0" y="0" width="495" height="{height}" rx="10" class="border"/>

  <!-- Header -->
  <text x="24" y="38" class="title">🚀 My Contributions</text>

  <!-- Repos -->
  {repo_section}
</svg>"""

# ==================== SVG CARD 3: WEEKLY ACTIVITY (FIXED) ====================

days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
max_activity = max([weekly.get(d, 0) for d in days_short], default=1)

activity_bars = []
bar_spacing = 60
start_x = 40

for i, day in enumerate(days_short):
    count = weekly.get(day, 0)
    # Fixed: max bar height is now 70px instead of 90px
    bar_height = max((count / max(max_activity, 1)) * 70, 3) if count > 0 else 0
    
    x_pos = start_x + i * bar_spacing
    y_base = 135  # Moved up from 145
    
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
      {f'<text x="{x_pos + 22.5}" y="{y_base - bar_height - 8}" text-anchor="middle" class="count">{count}</text>' if count > 0 else ''}
      <text x="{x_pos + 22.5}" y="{y_base + 18}" text-anchor="middle" class="day-label">{day}</text>
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
  <line x1="40" y1="135" x2="455" y2="135" class="baseline"/>

  <!-- Activity bars -->
  {activity_section}
</svg>"""

# ==================== SVG CARD 4: COMMIT TIME HEATMAP ====================

# Group hours into 6 blocks of 4 hours each
time_blocks = {
    "Night\n(00-04)": sum(commit_hours.get(h, 0) for h in range(0, 4)),
    "Dawn\n(04-08)": sum(commit_hours.get(h, 0) for h in range(4, 8)),
    "Morning\n(08-12)": sum(commit_hours.get(h, 0) for h in range(8, 12)),
    "Afternoon\n(12-16)": sum(commit_hours.get(h, 0) for h in range(12, 16)),
    "Evening\n(16-20)": sum(commit_hours.get(h, 0) for h in range(16, 20)),
    "Night\n(20-24)": sum(commit_hours.get(h, 0) for h in range(20, 24)),
}

max_commits = max(time_blocks.values(), default=1)

time_items = []
block_width = 65
start_x = 30

for i, (period, count) in enumerate(time_blocks.items()):
    x_pos = start_x + i * block_width
    intensity = (count / max(max_commits, 1)) if max_commits > 0 else 0
    
    # Color based on intensity
    if intensity > 0.7:
        color = "#39D353"
        emoji = "🔥"
    elif intensity > 0.4:
        color = "#26A641"
        emoji = "⚡"
    elif intensity > 0:
        color = "#006D32"
        emoji = "✨"
    else:
        color = COLORS['graph_bg']
        emoji = "💤"
        
    period_lines = period.split("\n")
    
    time_items.append(f"""
    <!-- {period} -->
    <g>
      <rect x="{x_pos}" y="75" width="55" height="70" rx="8" 
            fill="{color}" opacity="{0.3 + intensity * 0.7}"/>
      <text x="{x_pos + 27.5}" y="100" text-anchor="middle" class="emoji">{emoji}</text>
      <text x="{x_pos + 27.5}" y="120" text-anchor="middle" class="time-count">{count}</text>
      <text x="{x_pos + 27.5}" y="165" text-anchor="middle" class="time-label">{period_lines[0]}</text>
      <text x="{x_pos + 27.5}" y="178" text-anchor="middle" class="time-label">{period_lines[1]}</text>
    </g>
  """)

time_section = "\n".join(time_items)

time_svg = f"""<svg width="495" height="195" viewBox="0 0 495 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .bg {{ fill: {COLORS['card_bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .subtitle {{ fill: {COLORS['date']}; font-size: 13px; font-weight: 500; font-family: 'Inter', sans-serif; }}
      .emoji {{ font-size: 20px; }}
      .time-count {{ fill: {COLORS['title']}; font-size: 16px; font-weight: 700; font-family: 'Inter', monospace; }}
      .time-label {{ fill: {COLORS['date']}; font-size: 10px; font-family: 'Inter', sans-serif; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect x="0" y="0" width="495" height="195" rx="10" class="bg"/>
  <rect x="0" y="0" width="495" height="195" rx="10" class="border"/>

  <!-- Header -->
  <text x="24" y="38" class="title">⏰ When I Code</text>
  <text x="24" y="58" class="subtitle">Last 30 days activity</text>

  <!-- Time blocks -->
  {time_section}
</svg>"""

# ==================== SAVE SVG FILES ====================

print("💾 Saving SVG files...")

os.makedirs("stats", exist_ok=True)

with open("stats/overview.svg", "w") as f:
    f.write(overview_svg)
    print("✅ stats/overview.svg")

with open("stats/repos.svg", "w") as f:
    f.write(repos_svg)
    print("✅ stats/repos.svg (NEW - top starred repos)")

with open("stats/weekly.svg", "w") as f:
    f.write(weekly_svg)
    print("✅ stats/weekly.svg (FIXED - bars stay in frame)")

with open("stats/time.svg", "w") as f:
    f.write(time_svg)
    print("✅ stats/time.svg (NEW - coding time distribution)")

print("\n✨ Done! Use in README:")
print("""
<p align="center">
  <img src="stats/overview.svg" alt="GitHub Stats" />
  <img src="stats/repos.svg" alt="Top Repositories" />
  <img src="stats/weekly.svg" alt="Weekly Activity" />
  <img src="stats/time.svg" alt="Coding Time" />
</p>
""")
