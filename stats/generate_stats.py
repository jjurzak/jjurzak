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

# Top repos by commits in last 6 months (excluding jjurzak repo)
print("🔍 Analyzing repo contributions (last 6 months)...")
repo_stats = []
six_months_ago = datetime.utcnow() - timedelta(days=180)

for repo in repos:
    if repo.get("fork", False) or repo.get("name") == "jjurzak":
        continue
    
    repo_name = repo.get("name", "")
    print(f"  Checking {repo_name}...")
    
    # Get commits from last 6 months
    since_date = six_months_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    commits_url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?author={USERNAME}&since={since_date}&per_page=100"
    commits = fetch(commits_url)
    
    commit_count = 0
    
    if commits and isinstance(commits, list):
        commit_count = len(commits)
    
    if commit_count > 0:
        repo_stats.append({
            "repo": repo,
            "commits": commit_count
        })
        print(f"    ✓ {commit_count} commits")
    else:
        print(f"    ✗ No commits in last 6 months")

# Sort by commits
top_repos = sorted(repo_stats, key=lambda x: x["commits"], reverse=True)[:3]
print(f"\n📊 Found {len(repo_stats)} repos with commits, showing top {len(top_repos)}")

# Weekly activity
print("📈 Analyzing activity...")
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
cutoff = datetime.utcnow() - timedelta(days=7)
cutoff30 = datetime.utcnow() - timedelta(days=30)

weekly_activity = Counter()
commit_hours = Counter()

for evt in events:
    try:
        t = datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if t >= cutoff:
            day = t.strftime("%a")
            weekly_activity[day] += 1
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

# ==================== BUILD DASHBOARD SVG ====================

# Top repos section
repo_items = []
for i, item in enumerate(top_repos[:3]):
    repo = item["repo"]
    commits = item["commits"]
    
    name = repo.get("name", "")
    desc = repo.get("description", "")
    lang = repo.get("language", "None")
    
    # Truncate description
    if desc and len(desc) > 38:
        desc = desc[:35] + "..."
    elif not desc:
        desc = "No description"
    
    y_pos = 260 + i * 75
    lang_color = get_lang_color(lang)
    
    # Language icon
    lang_icon = "🐍" if lang == "Python" else "📄"
    
    repo_items.append(f"""
    <!-- {name} -->
    <g opacity="0.95">
      <rect x="30" y="{y_pos - 15}" width="360" height="65" rx="8" fill="{COLORS['card_bg']}"/>
      <text x="45" y="{y_pos + 5}" class="repo-name">{name}</text>
      <text x="45" y="{y_pos + 25}" class="repo-desc">{desc}</text>
      <circle cx="50" cy="{y_pos + 42}" r="4" fill="{lang_color}"/>
      <text x="60" y="{y_pos + 46}" class="repo-lang">{lang}</text>
      <text x="180" y="{y_pos + 46}" class="repo-stat">📝 {commits} commits</text>
    </g>
  """)

repo_section = "\n".join(repo_items) if repo_items else """
    <text x="210" y="320" text-anchor="middle" class="repo-desc">No contributions in last 6 months</text>
"""

# Weekly activity bars
days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
max_activity = max([weekly_activity.get(d, 0) for d in days_short], default=1)

activity_bars = []
bar_spacing = 42
start_x = 450

for i, day in enumerate(days_short):
    count = weekly_activity.get(day, 0)
    bar_height = max((count / max(max_activity, 1)) * 60, 2) if count > 0 else 2
    
    x_pos = start_x + i * bar_spacing
    y_base = 335
    
    # Color intensity
    if count == 0:
        bar_color = COLORS['border']
        opacity = 0.3
    else:
        bar_color = COLORS['graph_bar']
        opacity = 0.5 + (count / max(max_activity, 1)) * 0.5

    activity_bars.append(f"""
    <g>
      <rect x="{x_pos}" y="{y_base - bar_height}" width="30" height="{bar_height}" rx="4" 
            fill="{bar_color}" opacity="{opacity}"/>
      {f'<text x="{x_pos + 15}" y="{y_base - bar_height - 6}" text-anchor="middle" class="count-small">{count}</text>' if count > 0 else ''}
      <text x="{x_pos + 15}" y="{y_base + 15}" text-anchor="middle" class="day-label-small">{day[:1]}</text>
    </g>
  """)

activity_section = "\n".join(activity_bars)

# Coding hours
time_blocks_data = [
    ("Night", "00-04", sum(commit_hours.get(h, 0) for h in range(0, 4))),
    ("Morning", "04-12", sum(commit_hours.get(h, 0) for h in range(4, 12))),
    ("Afternoon", "12-18", sum(commit_hours.get(h, 0) for h in range(12, 18))),
    ("Evening", "18-24", sum(commit_hours.get(h, 0) for h in range(18, 24))),
]

max_commits = max([c for _, _, c in time_blocks_data], default=1)

time_items = []
block_width = 70
start_x_time = 445

for i, (period, hours, count) in enumerate(time_blocks_data):
    x_pos = start_x_time + i * block_width
    intensity = (count / max(max_commits, 1)) if max_commits > 0 else 0
    
    # Color and emoji based on intensity
    if intensity > 0.7:
        color = COLORS['graph_bar']
        emoji = "🔥"
    elif intensity > 0.3:
        color = COLORS['accent']
        emoji = "⚡"
    elif intensity > 0:
        color = COLORS['border']
        emoji = "✨"
    else:
        color = COLORS['border']
        emoji = "💤"
    
    time_items.append(f"""
    <g>
      <rect x="{x_pos}" y="405" width="60" height="65" rx="6" 
            fill="{COLORS['card_bg']}" opacity="{0.5 + intensity * 0.5}"/>
      <text x="{x_pos + 30}" y="430" text-anchor="middle" class="emoji-small">{emoji}</text>
      <text x="{x_pos + 30}" y="448" text-anchor="middle" class="time-count">{count}</text>
      <text x="{x_pos + 30}" y="462" text-anchor="middle" class="time-label-small">{period}</text>
    </g>
  """)

time_section = "\n".join(time_items)

# ==================== MEGA DASHBOARD SVG ====================

dashboard_svg = f"""<svg width="800" height="520" viewBox="0 0 800 520" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="headerGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{COLORS['gradient_start']};stop-opacity:1" />
      <stop offset="50%" style="stop-color:{COLORS['gradient_end']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{COLORS['graph_bar']};stop-opacity:1" />
    </linearGradient>
    
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
      
      .card {{ filter: drop-shadow(0 4px 16px rgba(0,0,0,0.3)); }}
      .bg {{ fill: {COLORS['bg']}; }}
      .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
      .card-section {{ fill: {COLORS['card_bg']}; }}
      
      .dashboard-title {{ fill: {COLORS['fg']}; font-size: 24px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .dashboard-subtitle {{ fill: {COLORS['date']}; font-size: 12px; font-weight: 500; font-family: 'Inter', sans-serif; }}
      
      .stat-value-big {{ fill: {COLORS['title']}; font-size: 28px; font-weight: 700; font-family: 'Inter', sans-serif; }}
      .stat-label-small {{ fill: {COLORS['date']}; font-size: 10px; font-weight: 500; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.5px; }}
      
      .section-title {{ fill: {COLORS['fg']}; font-size: 16px; font-weight: 600; font-family: 'Inter', sans-serif; }}
      
      .repo-name {{ fill: {COLORS['title']}; font-size: 15px; font-weight: 600; font-family: 'Inter', monospace; }}
      .repo-desc {{ fill: {COLORS['date']}; font-size: 11px; font-family: 'Inter', sans-serif; }}
      .repo-lang {{ fill: {COLORS['fg']}; font-size: 11px; font-family: 'Inter', sans-serif; }}
      .repo-stat {{ fill: {COLORS['date']}; font-size: 11px; font-family: 'Inter', monospace; }}
      
      .day-label-small {{ fill: {COLORS['date']}; font-size: 10px; font-weight: 600; font-family: 'Inter', sans-serif; }}
      .count-small {{ fill: {COLORS['title']}; font-size: 11px; font-weight: 700; font-family: 'Inter', monospace; }}
      
      .emoji-small {{ font-size: 18px; }}
      .time-count {{ fill: {COLORS['title']}; font-size: 16px; font-weight: 700; font-family: 'Inter', monospace; }}
      .time-label-small {{ fill: {COLORS['date']}; font-size: 9px; font-family: 'Inter', sans-serif; }}
      
      .divider {{ stroke: {COLORS['border']}; stroke-width: 1; opacity: 0.5; }}
    </style>
  </defs>

  <!-- Card background -->
  <rect class="card bg" x="0" y="0" width="800" height="520" rx="12"/>
  <rect x="0" y="0" width="800" height="520" rx="12" class="border"/>
  
  <!-- Header gradient bar -->
  <rect x="0" y="0" width="800" height="4" fill="url(#headerGrad)"/>

  <!-- Header -->
  <text x="30" y="45" class="dashboard-title">📊 GitHub Activity Dashboard</text>
  <text x="30" y="65" class="dashboard-subtitle">@{USERNAME} • Updated {now}</text>

  <!-- Mini Stats -->
  <g>
    <!-- Repositories -->
    <rect x="30" y="90" width="170" height="85" rx="8" class="card-section"/>
    <text x="115" y="130" text-anchor="middle" class="stat-value-big">{public_repos}</text>
    <text x="115" y="148" text-anchor="middle" class="stat-label-small">Repositories</text>
    
    <!-- Followers -->
    <rect x="220" y="90" width="170" height="85" rx="8" class="card-section"/>
    <text x="305" y="130" text-anchor="middle" class="stat-value-big">{followers}</text>
    <text x="305" y="148" text-anchor="middle" class="stat-label-small">Followers</text>
    
    <!-- Events -->
    <rect x="410" y="90" width="360" height="85" rx="8" class="card-section"/>
    <text x="590" y="130" text-anchor="middle" class="stat-value-big">{streak}</text>
    <text x="590" y="148" text-anchor="middle" class="stat-label-small">Events (30 days)</text>
  </g>

  <!-- Left Section: Top Contributions -->
  <text x="30" y="215" class="section-title">🚀 Top Contributions (6 months)</text>
  {repo_section}

  <!-- Right Section: Activity -->
  <text x="445" y="215" class="section-title">📈 Weekly Activity</text>
  <text x="445" y="235" class="dashboard-subtitle">Last 7 days</text>
  
  <!-- Weekly bars -->
  <line x1="445" y1="335" x2="745" y2="335" class="divider" stroke-dasharray="4,4"/>
  {activity_section}

  <!-- Coding Hours -->
  <text x="445" y="385" class="section-title">⏰ When I Code</text>
  {time_section}
</svg>"""

# ==================== SAVE SVG FILES ====================

print("💾 Saving dashboard...")

os.makedirs("stats", exist_ok=True)

with open("stats/dashboard.svg", "w") as f:
    f.write(dashboard_svg)
    print("✅ stats/dashboard.svg")

print("\n✨ Done! Use in README:")
print("""
<div align="center">
  <img src="stats/dashboard.svg" alt="GitHub Activity Dashboard" width="100%" />
</div>
""")
