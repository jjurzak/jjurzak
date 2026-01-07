import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter

USERNAME = "jjurzak"
HEADERS = {"Accept": "application/vnd.github+json"}

def fetch(url):
    """Fetch data from GitHub API (simple safe wrapper)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 403:
            return None
        return r.json()
    except Exception:
        return None

# ---------- Helpers for smooth area/line paths ----------
def catmull_rom_to_bezier(points):
    """
    Convert a list of (x,y) points to a smooth cubic-bezier path using Catmull-Rom to Bezier conversion.
    Returns path string of 'M x0,y0 C ...' (does not close).
    """
    if not points:
        return ""
    if len(points) == 1:
        x, y = points[0]
        return f"M {x:.2f},{y:.2f}"
    if len(points) == 2:
        (x0, y0), (x1, y1) = points
        return f"M {x0:.2f},{y0:.2f} L {x1:.2f},{y1:.2f}"

    # duplicate start/end to act as neighbours
    pts = [points[0]] + points + [points[-1]]
    path = []
    x0, y0 = points[0]
    path.append(f"M {x0:.2f},{y0:.2f}")

    for i in range(1, len(pts)-2):
        p0x, p0y = pts[i-1]
        p1x, p1y = pts[i]
        p2x, p2y = pts[i+1]
        p3x, p3y = pts[i+2]

        # Catmull-Rom to Bezier conversion factor
        c1x = p1x + (p2x - p0x) / 6.0
        c1y = p1y + (p2y - p0y) / 6.0
        c2x = p2x - (p3x - p1x) / 6.0
        c2y = p2y - (p3y - p1y) / 6.0

        path.append(f"C {c1x:.2f},{c1y:.2f} {c2x:.2f},{c2y:.2f} {p2x:.2f},{p2y:.2f}")

    return " ".join(path)

def make_area_path(points, bottom_y, left_x, right_x):
    """
    Given a list of points (x,y) that form the top curve,
    return a closed area path string: start at left bottom, up to first point, smooth curve to last, then to right bottom, close.
    left_x and right_x allow area to align with chart box edges.
    """
    if not points:
        return ""
    # Build smooth top path
    top_path = catmull_rom_to_bezier(points)
    # Construct area by starting from bottom-left, then along top_path, then to bottom-right and close
    first_x, first_y = points[0]
    last_x, last_y = points[-1]
    area = f"M {left_x:.2f},{bottom_y:.2f} "  # bottom-left
    area += f"L {first_x:.2f},{first_y:.2f} "  # up to first top point
    # append the smooth path but drop the leading "M x,y" because we're already at that point
    if top_path.startswith("M "):
        area += top_path[ top_path.find(" ")+1 + top_path[top_path.find(" ")+1:].find(" ")+1:] if False else top_path.replace(f"M {first_x:.2f},{first_y:.2f} ", "")
        # simpler: append full bezier but ensure not duplicating the first point
        area += " " + top_path.replace(f"M {first_x:.2f},{first_y:.2f}", "").strip()
    else:
        area += " " + top_path
    area += f" L {right_x:.2f},{bottom_y:.2f} Z"
    return area

# ---------- Data collection ----------
print("📊 Fetching GitHub stats...")

user = fetch(f"https://api.github.com/users/{USERNAME}") or {}
repos = fetch(f"https://api.github.com/users/{USERNAME}/repos?per_page=200") or []

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)

six_months_ago = datetime.utcnow() - timedelta(days=180)

repo_stats = []
for repo in repos:
    if repo.get("fork", False) or repo.get("name") == USERNAME:
        continue
    name = repo.get("name", "")
    print(f"  Checking {name}...")
    commits_url = f"https://api.github.com/repos/{USERNAME}/{name}/commits?author={USERNAME}&since={six_months_ago.strftime('%Y-%m-%dT%H:%M:%SZ')}&per_page=100"
    commits = fetch(commits_url) or []
    commit_count = len(commits) if isinstance(commits, list) else 0

    weekly_commits = [0] * 26
    if commit_count > 0:
        for c in commits:
            try:
                date_str = c.get("commit", {}).get("author", {}).get("date")
                if date_str:
                    t = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    weeks_ago = (datetime.utcnow() - t).days // 7
                    if 0 <= weeks_ago < 26:
                        weekly_commits[25 - weeks_ago] += 1
            except Exception:
                continue

    if commit_count > 0:
        repo_stats.append({
            "repo": repo,
            "commits": commit_count,
            "weekly": weekly_commits
        })

# choose top 3
top_repos = sorted(repo_stats, key=lambda x: x["commits"], reverse=True)[:3]

# Weekly activity and commit hours
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
cutoff = datetime.utcnow() - timedelta(days=7)
cutoff30 = datetime.utcnow() - timedelta(days=30)

weekly_activity = Counter()
commit_hours = Counter()
for evt in events:
    try:
        t = datetime.strptime(evt["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if t >= cutoff:
            weekly_activity[t.strftime("%a")] += 1
        if t >= cutoff30:
            commit_hours[t.hour] += 1
    except Exception:
        continue

# ---------- Theme ----------
MODE = "dark"
THEMES = {
    "dark": {
        "bg": "#0D1117",
        "card_bg": "#0F1720",
        "fg": "#C9D1D9",
        "title": "#58A6FF",
        "accent": "#1F6FEB",
        "border": "#27303a",
        "date": "#8B949E",
        "graph_bar": "#39D353",
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
    }
}
COLORS = THEMES[MODE]
now = datetime.utcnow().strftime("%b %d, %Y")

# language colors (short)
LANG_COLORS = {"Python":"#3572A5"}
def get_lang_color(lang):
    return LANG_COLORS.get(lang, COLORS["accent"])

# ---------- Build one big dashboard SVG ----------
W = 1200
H = 680

# layout areas
left_x = 30
left_w = 560
right_x = left_x + left_w + 20
right_w = W - right_x - 30

# repo chart parameters
chart_w = right_w - 40
chart_h = 70
chart_left = right_x + 20

# Compose repo blocks
repo_blocks_svg = []
for idx, item in enumerate(top_repos):
    repo = item["repo"]
    commits = item["commits"]
    weekly = item["weekly"]
    name = repo.get("name", "repo")
    desc = repo.get("description") or "No description"
    lang = repo.get("language") or "Code"
    lang_color = get_lang_color(lang)

    # Prepare points for chart (26 weeks)
    max_week = max(weekly) if max(weekly, default=0) > 0 else 1
    points = []
    for j, v in enumerate(weekly):
        x = chart_left + (j / max(25, 1)) * chart_w
        # invert Y: larger v => smaller y
        normalized = v / max_week
        y = 180 + idx * (chart_h + 90) + (chart_h - normalized * chart_h)
        points.append((x, y))

    # bottom baseline for area
    bottom_y = 180 + idx * (chart_h + 90) + chart_h + 6
    area_path = make_area_path(points, bottom_y, points[0][0], points[-1][0])
    line_path = catmull_rom_to_bezier(points)

    repo_block = f"""
    <!-- Repo {idx} -->
    <g opacity="0.98">
      <text x="{chart_left}" y="{150 + idx * (chart_h + 90)}" class="repo-name">{name}</text>
      <text x="{chart_left}" y="{165 + idx * (chart_h + 90)}" class="repo-desc">{desc}</text>

      <g transform="translate(0,0)">
        <defs>
          <linearGradient id="areaGrad{idx}" x1="0" y1="0" x2="0" y2="1" gradientUnits="objectBoundingBox">
            <stop offset="0%" stop-color="{lang_color}" stop-opacity="0.42"/>
            <stop offset="60%" stop-color="{lang_color}" stop-opacity="0.12"/>
            <stop offset="100%" stop-color="{lang_color}" stop-opacity="0.02"/>
          </linearGradient>
        </defs>

        <!-- area fill -->
        <path d="{area_path}" fill="url(#areaGrad{idx})" stroke="none" />

        <!-- smooth line -->
        <path d="{line_path}" fill="none" stroke="{lang_color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />

        <!-- small circles on points (optional) -->
      </g>

      <text x="{chart_left + chart_w + 8}" y="{160 + idx * (chart_h + 90)}" class="repo-stat">📝 {commits} commits</text>
    </g>
    """
    repo_blocks_svg.append(repo_block)

repo_blocks_joined = "\n".join(repo_blocks_svg) if repo_blocks_svg else '<text x="{chart_left+20}" y="240" class="repo-desc">No contributions in last 6 months</text>'

# Weekly activity bars (simple)
days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
max_act = max([weekly_activity.get(d,0) for d in days], default=1)
bar_svg = []
bar_w = (left_w - 60) / len(days)
bx = left_x + 30
by = 430
for i,d in enumerate(days):
    cnt = weekly_activity.get(d,0)
    h = (cnt / max_act) * 90 if max_act>0 else 0
    x = bx + i * (bar_w + 6)
    y = by - h
    opacity = 0.45 + (cnt / max_act) * 0.5 if cnt>0 else 0.25
    bar_svg.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="6" fill="{COLORS["graph_bar"]}" opacity="{opacity:.2f}" />')
    if cnt>0:
        bar_svg.append(f'<text x="{x + bar_w/2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="count-small">{cnt}</text>')
    bar_svg.append(f'<text x="{x + bar_w/2:.1f}" y="{by + 18:.1f}" text-anchor="middle" class="day-label-small">{d[:3]}</text>')

bar_joined = "\n".join(bar_svg)

# Time blocks
time_blocks = [
    ("00-04", sum(commit_hours.get(h,0) for h in range(0,4))),
    ("04-08", sum(commit_hours.get(h,0) for h in range(4,8))),
    ("08-12", sum(commit_hours.get(h,0) for h in range(8,12))),
    ("12-16", sum(commit_hours.get(h,0) for h in range(12,16))),
    ("16-20", sum(commit_hours.get(h,0) for h in range(16,20))),
    ("20-24", sum(commit_hours.get(h,0) for h in range(20,24))),
]
max_time = max((c for _,c in time_blocks), default=1)
tb_svg = []
tx = left_x + 30
for i,(lbl,cnt) in enumerate(time_blocks):
    w = 60
    x = tx + i * (w + 12)
    intensity = (cnt / max_time) if max_time>0 else 0
    op = 0.25 + 0.65*intensity
    tb_svg.append(f'<rect x="{x}" y="520" width="{w}" height="70" rx="8" fill="{COLORS["card_bg"]}" opacity="{op:.2f}" />')
    tb_svg.append(f'<text x="{x + w/2}" y="545" text-anchor="middle" class="emoji-small">{"🔥" if intensity>0.6 else "⚡" if intensity>0.3 else "✨" if intensity>0 else "💤"}</text>')
    tb_svg.append(f'<text x="{x + w/2}" y="565" text-anchor="middle" class="time-count">{cnt}</text>')
    tb_svg.append(f'<text x="{x + w/2}" y="590" text-anchor="middle" class="time-label-small">{lbl}</text>')
tb_joined = "\n".join(tb_svg)

# Final big SVG
svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
      .bg {{ fill: {COLORS["bg"]}; }}
      .card {{ fill: {COLORS["card_bg"]}; stroke: {COLORS["border"]}; stroke-width: 1; rx: 12; }}
      .dashboard-title {{ fill: {COLORS["fg"]}; font-size: 22px; font-weight:700; font-family:Inter, sans-serif; }}
      .dashboard-sub {{ fill: {COLORS["date"]}; font-size:12px; font-family:Inter, sans-serif; }}
      .repo-name {{ fill: {COLORS["title"]}; font-size:14px; font-weight:600; font-family:Inter, monospace; }}
      .repo-desc {{ fill: {COLORS["date"]}; font-size:11px; font-family:Inter, sans-serif; }}
      .repo-stat {{ fill: {COLORS["date"]}; font-size:11px; font-family:Inter, monospace; }}
      .day-label-small {{ fill: {COLORS["date"]}; font-size:11px; font-family:Inter, sans-serif; }}
      .count-small {{ fill: {COLORS["title"]}; font-size:11px; font-weight:700; font-family:Inter, monospace; }}
      .emoji-small {{ font-size:16px; }}
      .time-count {{ fill: {COLORS["title"]}; font-size:13px; font-weight:700; font-family:Inter, monospace; }}
      .time-label-small {{ fill: {COLORS["date"]}; font-size:10px; font-family:Inter, sans-serif; }}
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="{W}" height="{H}" class="bg" rx="0" />

  <!-- Left card (overview + weekly + time) -->
  <g transform="translate({left_x},20)">
    <rect class="card" x="0" y="0" width="{left_w}" height="380" rx="10"/>
    <text x="20" y="34" class="dashboard-title">📊 GitHub Activity • @{USERNAME}</text>
    <text x="20" y="54" class="dashboard-sub">Updated {now}</text>

    <!-- mini stats -->
    <text x="20" y="92" class="repo-name">Repositories</text>
    <text x="20" y="112" class="repo-desc">{public_repos}</text>
    <text x="140" y="92" class="repo-name">Followers</text>
    <text x="140" y="112" class="repo-desc">{followers}</text>

    <!-- Weekly activity -->
    <text x="20" y="160" class="repo-name">📈 Weekly Activity (last 7 days)</text>
    {bar_joined}
  </g>

  <!-- Right card (repos with contribution-like charts) -->
  <g>
    <rect class="card" x="{right_x}" y="20" width="{right_w}" height="360" rx="10"/>
    <text x="{right_x + 20}" y="48" class="dashboard-title">🚀 Top Contributions (6 months)</text>
    {repo_blocks_joined}
  </g>

  <!-- Bottom: time blocks -->
  <g transform="translate(0,0)">
    <rect class="card" x="{left_x}" y="470" width="{W - 2*left_x}" height="180" rx="10"/>
    <text x="{left_x + 20}" y="500" class="repo-name">⏰ When I Code (last 30 days)</text>
    {tb_joined}
  </g>
</svg>
'''

# Save file
os.makedirs("stats", exist_ok=True)
with open("stats/dashboard.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Saved stats/dashboard.svg (one big dashboard with gradient area under repo lines).")
print("👉 Otwórz stats/dashboard.svg w przeglądarce lub w README używając <img src='stats/dashboard.svg'/>")
