import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import html

USERNAME = "jjurzak"
HEADERS = {"Accept": "application/vnd.github+json"}

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 403:
            return None
        return r.json()
    except:
        return None

# Escape unsafe XML characters
def esc(s):
    return html.escape(s or "")

# ------------ Smoothing helpers -----------------

def catmull_rom_to_bezier(points):
    if not points:
        return ""
    if len(points) == 1:
        x, y = points[0]
        return f"M {x},{y}"
    if len(points) == 2:
        (x0, y0), (x1, y1) = points
        return f"M {x0},{y0} L {x1},{y1}"

    pts = [points[0]] + points + [points[-1]]
    path = [f"M {points[0][0]},{points[0][1]}"]

    for i in range(1, len(pts)-2):
        p0x,p0y = pts[i-1]
        p1x,p1y = pts[i]
        p2x,p2y = pts[i+1]
        p3x,p3y = pts[i+2]
        c1x = p1x + (p2x - p0x) / 6
        c1y = p1y + (p2y - p0y) / 6
        c2x = p2x - (p3x - p1x) / 6
        c2y = p2y - (p3y - p1y) / 6
        path.append(f"C {c1x},{c1y} {c2x},{c2y} {p2x},{p2y}")

    return " ".join(path)

def make_area(points, bottom_y, left_x, right_x):
    if not points:
        return ""
    first_x, first_y = points[0]
    top_path = catmull_rom_to_bezier(points).split(" ",3)[-1]
    return (
        f"M {left_x},{bottom_y} "
        f"L {first_x},{first_y} "
        f"{top_path} "
        f"L {right_x},{bottom_y} Z"
    )

# ------------ Fetch data -----------------

print("📊 Fetching...")

user = fetch(f"https://api.github.com/users/{USERNAME}") or {}
repos = fetch(f"https://api.github.com/users/{USERNAME}/repos?per_page=200") or []

public_repos = user.get("public_repos", 0)
followers = user.get("followers", 0)

six_months_ago = datetime.utcnow() - timedelta(days=180)

repo_stats = []
for repo in repos:
    if repo.get("fork") or repo.get("name") == USERNAME:
        continue
    commits = fetch(
        f"https://api.github.com/repos/{USERNAME}/{repo['name']}/commits"
        f"?author={USERNAME}&since={six_months_ago.strftime('%Y-%m-%dT%H:%M:%SZ')}&per_page=100"
    )
    if not isinstance(commits, list):
        continue
    weekly = [0]*26
    for c in commits:
        try:
            t = datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            week = (datetime.utcnow() - t).days // 7
            if 0 <= week < 26:
                weekly[25-week] += 1
        except:
            pass
    if sum(weekly)>0:
        repo_stats.append({"repo":repo,"commits":sum(weekly),"weekly":weekly})

top_repos = sorted(repo_stats, key=lambda x:x["commits"], reverse=True)[:3]

# 30-day event streak + hours
events = fetch(f"https://api.github.com/users/{USERNAME}/events?per_page=100") or []
weekly_act = Counter()
commit_hours = Counter()
cutoff7 = datetime.utcnow() - timedelta(days=7)
cutoff30 = datetime.utcnow() - timedelta(days=30)

for e in events:
    try:
        t = datetime.strptime(e["created_at"],"%Y-%m-%dT%H:%M:%SZ")
        if t>=cutoff7: weekly_act[t.strftime("%a")] += 1
        if t>=cutoff30: commit_hours[t.hour] += 1
    except:
        pass

# ------------ Colors ---------------
COLORS={
    "bg":"#0d1117",
    "card":"#11161f",
    "fg":"#C9D1D9",
    "title":"#ffffff",
    "date":"#8B949E",
    "border":"#1e2632",
    "green":"#2ecc71",
    "blue":"#1f6feb"
}

LANG_COLORS={"Python":"#3572A5","None":"#2ecc71"}
def langc(x): return LANG_COLORS.get(x, COLORS["blue"])

now = datetime.utcnow().strftime("%b %d, %Y")

# ------------ Layout ----------------
W,H=1200,750

# ---------- Build SVG ----------
svg = f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
 xmlns="http://www.w3.org/2000/svg">
<style>
* {{ font-family: Inter, sans-serif; }}
.bg {{ fill:{COLORS["bg"]}; }}
.card {{ fill:{COLORS["card"]}; stroke:{COLORS["border"]}; stroke-width:1; }}
.title {{ fill:{COLORS["title"]}; font-size:24px; font-weight:700; }}
.sub {{ fill:{COLORS["date"]}; font-size:12px; }}
.stat {{ fill:{COLORS["blue"]}; font-size:22px; font-weight:700; }}
.label {{ fill:{COLORS["date"]}; font-size:11px; }}
.repo-name {{ fill:{COLORS["blue"]}; font-size:14px; font-weight:600; }}
.repo-desc {{ fill:{COLORS["date"]}; font-size:11px; }}
.day-label {{ fill:{COLORS["date"]}; font-size:11px; }}
.count {{ fill:{COLORS["blue"]}; font-size:11px; font-weight:700; }}
.time-count {{ fill:{COLORS["blue"]}; font-size:15px; font-weight:700; }}
.time-label {{ fill:{COLORS["date"]}; font-size:11px; }}
</style>

<rect width="{W}" height="{H}" class="bg"/>

<!-- HEADER -->
<text x="40" y="60" class="title">📊 GitHub Activity Dashboard</text>
<text x="40" y="80" class="sub">@{USERNAME} • Updated {now}</text>
<line x1="40" y1="95" x2="{W-40}" y2="95" stroke="{COLORS['border']}" stroke-width="1"/>

<!-- Stats -->
<text x="160"  y="150" text-anchor="middle" class="stat">{public_repos}</text>
<text x="160"  y="170" text-anchor="middle" class="label">REPOSITORIES</text>

<text x="600"  y="150" text-anchor="middle" class="stat">{followers}</text>
<text x="600"  y="170" text-anchor="middle" class="label">FOLLOWERS</text>

<text x="1040" y="150" text-anchor="middle" class="stat">{sum(commit_hours.values())}</text>
<text x="1040" y="170" text-anchor="middle" class="label">EVENTS (30D)</text>

<!-- Top Contributions -->
<text x="40" y="220" class="repo-name">🚀 Top Contributions</text>
"""

# ---- CONTRIBUTION CARDS WITH GRAPH ----
start_y=240
for idx,item in enumerate(top_repos):
    repo=item["repo"]
    y = start_y + idx*85
    name = esc(repo.get("name"))
    lang = esc(repo.get("language") or "None")
    commits = item["commits"]
    weekly = item["weekly"]
    color = langc(lang)

    svg += f'<rect x="40" y="{y}" width="{W-80}" height="70" rx="8" class="card"/>'
    svg += f'<text x="60" y="{y+22}" class="repo-name">{name}</text>'
    svg += f'<text x="60" y="{y+42}" class="repo-desc">{lang} • {commits} commits</text>'

    chart_left=60
    chart_right=W-120
    chart_width=chart_right-chart_left
    chart_height=40
    top_line=y+20

    maxw=max(weekly) if max(weekly)>0 else 1
    points=[]
    for j,v in enumerate(weekly):
        x=chart_left+(j/25)*chart_width
        yy=top_line+chart_height*(1-v/maxw)
        points.append((x,yy))

    area=make_area(points,top_line+chart_height+2,points[0][0],points[-1][0])
    line=catmull_rom_to_bezier(points)

    svg += f"""
    <defs>
      <linearGradient id="gr{idx}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{color}" stop-opacity="0.4"/>
        <stop offset="75%" stop-color="{color}" stop-opacity="0.15"/>
        <stop offset="100%" stop-color="{color}" stop-opacity="0.05"/>
      </linearGradient>
    </defs>
    <path d="{area}" fill="url(#gr{idx})"/>
    <path d="{line}" fill="none" stroke="{color}" stroke-width="2.3" stroke-linecap="round"/>
    """

# ---- WEEKLY ----
svg += f"""
<!-- Weekly -->
<text x="40" y="500" class="repo-name">📈 Weekly Activity</text>
"""

days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
max_act=max([weekly_act.get(d,0) for d in days], default=1)

base=520
for i,d in enumerate(days):
    c=weekly_act.get(d,0)
    h=(c/max_act)*100
    x=60+i*70
    y=base-h
    svg+=f'<rect x="{x}" y="{y}" width="55" height="{h}" rx="6" fill="{COLORS["green"]}" opacity="{0.45+(c/max_act)*0.5 if c else 0.25}"/>'
    svg+=f'<text x="{x+27}" y="{base+18}" text-anchor="middle" class="day-label">{d}</text>'
    if c>0:
        svg+=f'<text x="{x+27}" y="{y-6}" text-anchor="middle" class="count">{c}</text>'

# ---- TIME BLOCKS ----
svg+=f'<text x="40" y="650" class="repo-name">🕒 Coding Hours</text>'

blocks=[
    ("Night\n00-04", sum(commit_hours.get(h,0) for h in range(0,4))),
    ("Morning\n04-12", sum(commit_hours.get(h,0) for h in range(4,12))),
    ("Afternoon\n12-16", sum(commit_hours.get(h,0) for h in range(12,16))),
    ("Evening\n16-24", sum(commit_hours.get(h,0) for h in range(16,24))),
]

max_t=max((c for _,c in blocks),default=1)
x0=60
for i,(lbl,c) in enumerate(blocks):
    op=0.3+(c/max_t)*0.7
    svg+=f'<rect x="{x0+i*200}" y="665" width="170" height="60" rx="8" fill="{COLORS["card"]}" opacity="{op}"/>'
    svg+=f'<text x="{x0+i*200+85}" y="690" text-anchor="middle" class="time-count">{c}</text>'
    svg+=f'<text x="{x0+i*200+85}" y="710" text-anchor="middle" class="time-label">{lbl.replace("\\n"," ")}</text>'

svg+="</svg>"

# SAVE
os.makedirs("stats",exist_ok=True)
with open("stats/dashboard.svg","w",encoding="utf-8") as f:
    f.write(svg)

print("✅ stats/dashboard.svg ready!")
