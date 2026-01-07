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
        return f"M {x:.2f},{y:.2f}"
    if len(points) == 2:
        (x0, y0), (x1, y1) = points
        return f"M {x0:.2f},{y0:.2f} L {x1:.2f},{y1:.2f}"

    pts = [points[0]] + points + [points[-1]]
    path = []
    x0, y0 = pts[1]
    path.append(f"M {x0:.2f},{y0:.2f}")
    for i in range(1, len(pts)-2):
        p0x,p0y = pts[i-1]
        p1x,p1y = pts[i]
        p2x,p2y = pts[i+1]
        p3x,p3y = pts[i+2]
        c1x = p1x + (p2x - p0x) / 6
        c1y = p1y + (p2y - p0y) / 6
        c2x = p2x - (p3x - p1x) / 6
        c2y = p2y - (p3y - p1y) / 6
        path.append(f"C {c1x:.2f},{c1y:.2f} {c2x:.2f},{c2y:.2f} {p2x:.2f},{p2y:.2f}")
    return " ".join(path)

def make_area(points, bottom_y, left_x, right_x):
    if not points:
        return ""
    first_x, first_y = points[0]
    last_x, _ = points[-1]
    top = catmull_rom_to_bezier(points)
    top = top.replace(f"M {first_x:.2f},{first_y:.2f}", "").strip()
    return (
        f"M {left_x:.2f},{bottom_y:.2f} "
        f"L {first_x:.2f},{first_y:.2f} "
        f"{top} "
        f"L {right_x:.2f},{bottom_y:.2f} Z"
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
    name = repo.get("name", "")
    print("Checking", name)
    commits = fetch(
        f"https://api.github.com/repos/{USERNAME}/{name}/commits"
        f"?author={USERNAME}&since={six_months_ago.strftime('%Y-%m-%dT%H:%M:%SZ')}&per_page=100"
    )
    if not isinstance(commits, list):
        continue
    weekly = [0]*26
    for c in commits:
        try:
            t = datetime.strptime(c["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ")
            w = (datetime.utcnow() - t).days // 7
            if 0 <= w < 26:
                weekly[25-w]+=1
        except:
            pass
    if weekly and sum(weekly)>0:
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
    "bg":"#0D1117",
    "card":"#161B22",
    "fg":"#C9D1D9",
    "title":"#58A6FF",
    "date":"#8B949E",
    "border":"#30363D",
    "green":"#39D353"
}

LANG_COLORS={"Python":"#3572A5"}

def langc(x):
    return LANG_COLORS.get(x, COLORS["green"])

now = datetime.utcnow().strftime("%b %d, %Y")

# ------------ Layout ----------------
W,H=1200,720
left_x=30
left_w=560
right_x=left_x+left_w+20
right_w=W-right_x-30
chart_w=right_w-40
chart_h=70

# ------------ Repo section ----------
repo_svg=[]
for idx,item in enumerate(top_repos):
    repo=item["repo"]
    name=esc(repo.get("name"))
    desc=esc(repo.get("description") or "No description")
    lang=repo.get("language") or "Code"
    weekly=item["weekly"]
    color=langc(lang)

    maxw=max(weekly) if max(weekly)>0 else 1
    points=[]
    top_y=160+idx*(chart_h+90)
    for j,v in enumerate(weekly):
        x = right_x+20+(j/25)*chart_w
        y = top_y + chart_h*(1 - v/maxw)
        points.append((x,y))

    bottom=top_y+chart_h+6
    area=make_area(points,bottom,points[0][0],points[-1][0])
    line=catmull_rom_to_bezier(points)

    repo_svg.append(f"""
    <g>
      <text x="{right_x+20}" y="{top_y-10}" class="repo-name">{name}</text>
      <text x="{right_x+20}" y="{top_y+8}" class="repo-desc">{desc}</text>

      <defs>
        <linearGradient id="g{idx}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{color}" stop-opacity="0.45"/>
          <stop offset="70%" stop-color="{color}" stop-opacity="0.12"/>
          <stop offset="100%" stop-color="{color}" stop-opacity="0.03"/>
        </linearGradient>
      </defs>

      <path d="{area}" fill="url(#g{idx})"/>
      <path d="{line}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>

      <text x="{right_x+20+chart_w+5}" y="{top_y+4}" class="repo-desc">📝 {item["commits"]} commits</text>
    </g>
    """)

repo_block="\n".join(repo_svg) if repo_svg else "<text x='600' y='250'>No data</text>"

# ------------ Weekly bars -----------
days=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
max_act=max([weekly_act.get(d,0) for d in days], default=1)
bars=[]
bx=left_x+30
baseline=400
for i,d in enumerate(days):
    c=weekly_act.get(d,0)
    bh=(c/max_act)*90
    x=bx+i*75
    y=baseline-bh
    bars.append(f'<rect x="{x}" y="{y}" width="50" height="{bh}" rx="6" fill="{COLORS["green"]}" opacity="{0.45+(c/max_act)*0.5 if c else 0.25}"/>')
    bars.append(f'<text x="{x+25}" y="{baseline+16}" text-anchor="middle" class="day-label-small">{d}</text>')
    if c>0:
        bars.append(f'<text x="{x+25}" y="{y-6}" text-anchor="middle" class="count-small">{c}</text>')
bars="\n".join(bars)

# ------------ Time blocks ----------
tb=[]
tblocks=[
    ("00-04",sum(commit_hours[h] for h in range(0,4))),
    ("04-08",sum(commit_hours[h] for h in range(4,8))),
    ("08-12",sum(commit_hours[h] for h in range(8,12))),
    ("12-16",sum(commit_hours[h] for h in range(12,16))),
    ("16-20",sum(commit_hours[h] for h in range(16,20))),
    ("20-24",sum(commit_hours[h] for h in range(20,24))),
]
max_t=max((c for _,c in tblocks),default=1)
tx=left_x+20
for i,(lbl,c) in enumerate(tblocks):
    w=60
    x=tx+i*(w+12)
    op=0.25+(c/max_t)*0.7
    emoji="🔥" if c/max_t>0.6 else "⚡" if c/max_t>0.3 else "✨" if c>0 else "💤"
    tb.append(f'<rect x="{x}" y="500" width="{w}" height="75" rx="8" fill="{COLORS["card"]}" opacity="{op}"/>')
    tb.append(f'<text x="{x+w/2}" y="525" text-anchor="middle" class="emoji-small">{emoji}</text>')
    tb.append(f'<text x="{x+w/2}" y="545" text-anchor="middle" class="time-count">{c}</text>')
    tb.append(f'<text x="{x+w/2}" y="570" text-anchor="middle" class="time-label-small">{lbl}</text>')
tb="\n".join(tb)

# ------------ TEMPLATE -------------
svg=f"""<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
 xmlns="http://www.w3.org/2000/svg">
<style>
* {{ font-family: Inter, sans-serif; }}
.bg {{ fill:{COLORS["bg"]}; }}
.card {{ fill:{COLORS["card"]}; stroke:{COLORS["border"]}; stroke-width:1; }}
.dashboard-title {{ fill:{COLORS["fg"]}; font-size:22px; font-weight:700; }}
.dashboard-sub {{ fill:{COLORS["date"]}; font-size:12px; }}
.repo-name {{ fill:{COLORS["title"]}; font-size:14px; font-weight:600; }}
.repo-desc {{ fill:{COLORS["date"]}; font-size:11px; }}
.day-label-small {{ fill:{COLORS["date"]}; font-size:11px; }}
.count-small {{ fill:{COLORS["title"]}; font-size:11px; font-weight:700; }}
.emoji-small {{ font-size:16px; }}
.time-count {{ fill:{COLORS["title"]}; font-size:13px; font-weight:700; }}
.time-label-small {{ fill:{COLORS["date"]}; font-size:10px; }}
</style>

<rect width="{W}" height="{H}" class="bg"/>

<!-- Left side -->
<rect x="{left_x}" y="20" width="{left_w}" height="440" rx="10" class="card"/>
<text x="{left_x+20}" y="50" class="dashboard-title">📊 GitHub Activity • @{USERNAME}</text>
<text x="{left_x+20}" y="70" class="dashboard-sub">Updated {now}</text>
<text x="{left_x+20}" y="110" class="repo-name">Repos: {public_repos}</text>
<text x="{left_x+150}" y="110" class="repo-name">Followers: {followers}</text>

<text x="{left_x+20}" y="150" class="repo-name">📈 Weekly Activity</text>
{bars}

<!-- Time -->
<text x="{left_x+20}" y="480" class="repo-name">⏰ When I Code</text>
{tb}

<!-- Right side -->
<rect x="{right_x}" y="20" width="{right_w}" height="640" rx="10" class="card"/>
<text x="{right_x+20}" y="50" class="dashboard-title">🚀 Top Contributions (6 months)</text>

{repo_block}

</svg>
"""

os.makedirs("stats",exist_ok=True)
with open("stats/dashboard.svg","w",encoding="utf-8") as f:
    f.write(svg)

print("✅ stats/dashboard.svg ready!")
