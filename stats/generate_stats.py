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
created_at = user.get("created_at", "")

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
    weekly_commits = [0] * 26
    
    if commits and isinstance(commits, list):
        commit_count = len(commits)
        for commit in commits:
            try:
                commit_date = commit.get("commit", {}).get("author", {}).get("date", "")
                if commit_date:
                    t = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ")
                    weeks_ago = (datetime.utcnow() - t).days // 7
                    if 0 <= weeks_ago < 26:
                        weekly_commits[25 - weeks_ago] += 1
            except:
                continue
    
    if commit_count > 0:
        repo_stats.append({
            "repo": repo,
            "commits": commit_count,
            "weekly": weekly_commits
        })

top_repos = sorted(repo_stats, key=lambda x: x["commits"], reverse=True)[:3]
print(f"📊 Found {len(repo_stats)} repos with commits, showing top {len(top_repos)}")

# Weekly activity & Time
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

streak = sum(1 for evt in events if "created_at" in evt and datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ") >= cutoff30)

# ==================== COLOR THEME ====================

MODE = os.getenv("THEME", "dark").lower()
THEMES = {
    "dark": {
        "bg": "#0D1117", "card_bg": "#161B22", "fg": "#C9D1D9", "title": "#58A6FF",
        "accent": "#1F6FEB", "border": "#30363D", "date": "#8B949E", "graph_bar": "#39D353",
        "graph_bg": "#0D1117", "gradient_start": "#7C3AED", "gradient_end": "#2563EB",
    },
    "light": {
        "bg": "#FFFFFF", "card_bg": "#F6F8FA", "fg": "#24292F", "title": "#0969DA",
        "accent": "#1F6FEB", "border": "#D0D7DE", "date": "#57606A", "graph_bar": "#2DA44E",
        "graph_bg": "#F6F8FA", "gradient_start": "#7C3AED", "gradient_end": "#2563EB",
    }
}
COLORS = THEMES.get(MODE, THEMES["dark"])
now = datetime.utcnow().strftime("%b %d, %Y")

LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#F1E05A", "TypeScript": "#3178C6", "Java": "#B07219",
    "C++": "#F34B7D", "C#": "#178600", "Go": "#00ADD8", "Rust": "#DEA584", "PHP": "#4F5D95",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "CSS": "#563D7C", "HTML": "#E34C26", "Shell": "#89E051",
}
def get_lang_color(lang): return LANG_COLORS.get(lang, COLORS["accent"])

# ==================== GENERATION HELPERS ====================

CARD_WIDTH = 495
CARD_GAP = 20  # Odstęp między kartami w pionie

# Wspólne style CSS dla całego pliku
GLOBAL_STYLES = f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap');
    .bg {{ fill: {COLORS['card_bg']}; }}
    .border {{ fill: none; stroke: {COLORS['border']}; stroke-width: 1; }}
    .title {{ fill: {COLORS['fg']}; font-size: 22px; font-weight: 700; font-family: 'Inter', sans-serif; }}
    .username {{ fill: {COLORS['date']}; font-size: 14px; font-weight: 500; font-family: 'Inter', sans-serif; }}
    .stat-label {{ fill: {COLORS['date']}; font-size: 12px; font-weight: 500; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.5px; }}
    .stat-value {{ fill: {COLORS['title']}; font-size: 32px; font-weight: 700; font-family: 'Inter', sans-serif; }}
    .footer {{ fill: {COLORS['date']}; font-size: 10px; font-family: 'Inter', sans-serif; }}
    .icon-circle {{ fill: url(#grad1); opacity: 0.15; }}
    .divider {{ stroke: {COLORS['border']}; stroke-width: 1; opacity: 0.5; }}
    
    .repo-name {{ fill: {COLORS['title']}; font-size: 16px; font-weight: 600; font-family: 'Inter', monospace; }}
    .repo-desc {{ fill: {COLORS['date']}; font-size: 12px; font-family: 'Inter', sans-serif; }}
    .repo-lang {{ fill: {COLORS['fg']}; font-size: 12px; font-family: 'Inter', sans-serif; }}
    .repo-stat {{ fill: {COLORS['date']}; font-size: 11px; font-family: 'Inter', monospace; }}
    
    .subtitle {{ fill: {COLORS['date']}; font-size: 13px; font-weight: 500; font-family: 'Inter', sans-serif; }}
    .day-label {{ fill: {COLORS['date']}; font-size: 11px; font-weight: 600; font-family: 'Inter', sans-serif; }}
    .count {{ fill: {COLORS['title']}; font-size: 12px; font-weight: 700; font-family: 'Inter', monospace; }}
    .baseline {{ stroke: {COLORS['border']}; stroke-width: 1; opacity: 0.3; stroke-dasharray: 4,4; }}
    
    .emoji {{ font-size: 20px; }}
    .time-count {{ fill: {COLORS['title']}; font-size: 16px; font-weight: 700; font-family: 'Inter', monospace; }}
    .time-label {{ fill: {COLORS['date']}; font-size: 10px; font-family: 'Inter', sans-serif; }}
</style>
"""

GLOBAL_DEFS = f"""
<linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" style="stop-color:{COLORS['gradient_start']};stop-opacity:1" />
    <stop offset="100%" style="stop-color:{COLORS['gradient_end']};stop-opacity:1" />
</linearGradient>
"""

# ==================== PART 1: OVERVIEW CONTENT ====================
overview_h = 195
overview_body = f"""
  <!-- Card background -->
  <rect class="bg" x="0" y="0" width="{CARD_WIDTH}" height="{overview_h}" rx="10"/>
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{overview_h}" rx="10" class="border"/>
  
  <circle class="icon-circle" cx="450" cy="40" r="60"/>
  <circle class="icon-circle" cx="40" cy="160" r="40"/>

  <text x="24" y="38" class="title">GitHub Stats</text>
  <text x="24" y="58" class="username">@{USERNAME}</text>

  <line x1="165" y1="85" x2="165" y2="150" class="divider"/>
  <line x1="330" y1="85" x2="330" y2="150" class="divider"/>

  <g>
    <text x="82" y="125" text-anchor="middle" class="stat-value">{public_repos}</text>
    <text x="82" y="145" text-anchor="middle" class="stat-label">Repositories</text>

    <text x="247" y="125" text-anchor="middle" class="stat-value">{followers}</text>
    <text x="247" y="145" text-anchor="middle" class="stat-label">Followers</text>

    <text x="412" y="125" text-anchor="middle" class="stat-value">{streak}</text>
    <text x="412" y="145" text-anchor="middle" class="stat-label">Events (30d)</text>
  </g>
  <text x="24" y="180" class="footer">↻ Updated {now}</text>
"""

# ==================== PART 2: REPOS CONTENT ====================
repo_items = []
y_start = 75
if not top_repos:
    repos_h = 195
    repo_items.append('<text x="247" y="100" text-anchor="middle" class="repo-desc">No data available</text>')
else:
    for i, item in enumerate(top_repos[:3]):
        repo = item["repo"]
        commits = item["commits"]
        weekly_data = item["weekly"]
        name = repo.get("name", "")
        desc = repo.get("description", "") or "No description"
        if len(desc) > 40: desc = desc[:37] + "..."
        lang = repo.get("language", "Code")
        
        y_pos = y_start + i * 80
        lang_color = get_lang_color(lang)
        
        # Mini Chart
        max_weekly = max(weekly_data) if weekly_data and max(weekly_data) > 0 else 1
        chart_width, chart_height = 240, 30
        chart_x, chart_y = 225, y_pos + 5
        
        points = []
        for j, count in enumerate(weekly_data):
            x = chart_x + (j / max(len(weekly_data) - 1, 1)) * chart_width
            normalized = (count / max_weekly) if max_weekly > 0 else 0
            y = chart_y + chart_height - (normalized * chart_height * 0.8)
            points.append((x, y))
            
        area_path = f"M {chart_x},{chart_y + chart_height} " + "".join([f"L {x},{y} " for x,y in points]) + f"L {chart_x + chart_width},{chart_y + chart_height} Z"
        line_path = " ".join([f"{x},{y}" for x, y in points])

        # Extra defs for this specific repo gradient
        grad_def = f"""<linearGradient id="areaGrad{i}" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" style="stop-color:{lang_color};stop-opacity:0.4" /><stop offset="100%" style="stop-color:{lang_color};stop-opacity:0.05" /></linearGradient>"""
        GLOBAL_DEFS += grad_def

        repo_items.append(f"""
        <g opacity="0.95">
            <text x="24" y="{y_pos}" class="repo-name">{name}</text>
            <text x="24" y="{y_pos + 18}" class="repo-desc">{desc}</text>
            <circle cx="29" cy="{y_pos + 28}" r="5" fill="{lang_color}"/>
            <text x="39" y="{y_pos + 32}" class="repo-lang">{lang}</text>
            <text x="124" y="{y_pos + 32}" class="repo-stat">📝 {commits} commits</text>
            <path d="{area_path}" fill="url(#areaGrad{i})"><animate attributeName="opacity" from="0" to="1" dur="0.8s" fill="freeze"/></path>
            <polyline points="{line_path}" fill="none" stroke="{lang_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
        """)
    repos_h = y_start + len(top_repos) * 80 + 20

repos_body = f"""
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{repos_h}" rx="10" class="bg"/>
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{repos_h}" rx="10" class="border"/>
  <text x="24" y="38" class="title">🚀 My Contributions (6 months)</text>
  {"".join(repo_items)}
"""

# ==================== PART 3: WEEKLY CONTENT ====================
weekly_h = 195
days_short = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
max_activity = max([weekly_activity.get(d, 0) for d in days_short], default=1)
bar_items = []
for i, day in enumerate(days_short):
    count = weekly_activity.get(day, 0)
    bar_height = max((count / max(max_activity, 1)) * 70, 3) if count > 0 else 0
    x_pos = 40 + i * 60
    y_base = 135
    color = COLORS['graph_bar'] if count > 0 else COLORS['graph_bg']
    opacity = 0.5 + (count / max(max_activity, 1)) * 0.5 if count > 0 else 0.3
    
    bar_items.append(f"""
    <g>
      <rect x="{x_pos}" y="{y_base - bar_height}" width="45" height="{bar_height}" rx="6" fill="{color}" opacity="{opacity}">
        <animate attributeName="height" from="0" to="{bar_height}" dur="0.6s" begin="{i * 0.1}s" fill="freeze"/>
        <animate attributeName="y" from="{y_base}" to="{y_base - bar_height}" dur="0.6s" begin="{i * 0.1}s" fill="freeze"/>
      </rect>
      {f'<text x="{x_pos + 22.5}" y="{y_base - bar_height - 8}" text-anchor="middle" class="count">{count}</text>' if count > 0 else ''}
      <text x="{x_pos + 22.5}" y="{y_base + 18}" text-anchor="middle" class="day-label">{day}</text>
    </g>
    """)

weekly_body = f"""
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{weekly_h}" rx="10" class="bg"/>
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{weekly_h}" rx="10" class="border"/>
  <text x="24" y="38" class="title">📈 Weekly Activity</text>
  <text x="24" y="58" class="subtitle">Last 7 days</text>
  <line x1="40" y1="135" x2="455" y2="135" class="baseline"/>
  {"".join(bar_items)}
"""

# ==================== PART 4: TIME CONTENT ====================
time_h = 195
time_blocks = {
    "Night\n(00-04)": sum(commit_hours.get(h, 0) for h in range(0, 4)),
    "Dawn\n(04-08)": sum(commit_hours.get(h, 0) for h in range(4, 8)),
    "Morning\n(08-12)": sum(commit_hours.get(h, 0) for h in range(8, 12)),
    "Afternoon\n(12-16)": sum(commit_hours.get(h, 0) for h in range(12, 16)),
    "Evening\n(16-20)": sum(commit_hours.get(h, 0) for h in range(16, 20)),
    "Night\n(20-24)": sum(commit_hours.get(h, 0) for h in range(20, 24)),
}
max_commits_time = max(time_blocks.values(), default=1)
time_items = []
for i, (period, count) in enumerate(time_blocks.items()):
    x_pos = 30 + i * 65
    intensity = (count / max(max_commits_time, 1)) if max_commits_time > 0 else 0
    
    if intensity > 0.7: color, emoji = "#39D353", "🔥"
    elif intensity > 0.4: color, emoji = "#26A641", "⚡"
    elif intensity > 0: color, emoji = "#006D32", "✨"
    else: color, emoji = COLORS['graph_bg'], "💤"
    
    time_items.append(f"""
    <g>
      <rect x="{x_pos}" y="75" width="55" height="70" rx="8" fill="{color}" opacity="{0.3 + intensity * 0.7}"/>
      <text x="{x_pos + 27.5}" y="100" text-anchor="middle" class="emoji">{emoji}</text>
      <text x="{x_pos + 27.5}" y="120" text-anchor="middle" class="time-count">{count}</text>
      <text x="{x_pos + 27.5}" y="165" text-anchor="middle" class="time-label">{period.split()[0]}</text>
      <text x="{x_pos + 27.5}" y="178" text-anchor="middle" class="time-label">{period.split()[1]}</text>
    </g>
    """)

time_body = f"""
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{time_h}" rx="10" class="bg"/>
  <rect x="0" y="0" width="{CARD_WIDTH}" height="{time_h}" rx="10" class="border"/>
  <text x="24" y="38" class="title">⏰ When I Code</text>
  <text x="24" y="58" class="subtitle">Last 30 days activity</text>
  {"".join(time_items)}
"""

# ==================== ASSEMBLY (STACKING) ====================

print("💾 Assembling combined SVG...")

# Calculate positions
y_1 = 0
y_2 = y_1 + overview_h + CARD_GAP
y_3 = y_2 + repos_h + CARD_GAP
y_4 = y_3 + weekly_h + CARD_GAP
total_height = y_4 + time_h

combined_svg = f"""<svg width="{CARD_WIDTH}" height="{total_height}" viewBox="0 0 {CARD_WIDTH} {total_height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    {GLOBAL_STYLES}
    {GLOBAL_DEFS}
  </defs>

  <!-- Part 1: Overview -->
  <g transform="translate(0, {y_1})">
    {overview_body}
  </g>

  <!-- Part 2: Repos -->
  <g transform="translate(0, {y_2})">
    {repos_body}
  </g>

  <!-- Part 3: Weekly -->
  <g transform="translate(0, {y_3})">
    {weekly_body}
  </g>

  <!-- Part 4: Time -->
  <g transform="translate(0, {y_4})">
    {time_body}
  </g>
</svg>"""

# Save file
os.makedirs("stats", exist_ok=True)
with open("stats/combined.svg", "w", encoding="utf-8") as f:
    f.write(combined_svg)

print(f"✅ Created stats/combined.svg (Size: {CARD_WIDTH}x{total_height})")
print("\n✨ Usage in README:")
print('![GitHub Stats](stats/combined.svg)')
