import requests
from datetime import datetime

USERNAME = "jjurzak"
API_URL = f"https://api.github.com/users/{USERNAME}"

r = requests.get(API_URL).json()

public_repos = r.get("public_repos", 0)
followers = r.get("followers", 0)

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

svg_template = f"""
<svg width="420" height="150" xmlns="http://www.w3.org/2000/svg">
<rect width="100%" height="100%" fill="#0D1117"/>
<style>
    .title {{ fill: #58A6FF; font-size: 18px; font-family: Arial, sans-serif; }}
    .label {{ fill: #C9D1D9; font-size: 14px; font-family: Arial, sans-serif; }}
</style>

<text x="20" y="35" class="title">GitHub Stats — {USERNAME}</text>
<text x="20" y="70" class="label">📁 Public repos: {public_repos}</text>
<text x="20" y="95" class="label">⭐ Followers: {followers}</text>
<text x="20" y="120" class="label">Updated: {now}</text>
</svg>
"""

with open("stats/card.svg", "w") as f:
    f.write(svg_template)
