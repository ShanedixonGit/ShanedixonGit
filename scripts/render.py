import datetime
import html
import os
import random
import re
import sys
import textwrap
import urllib.request

USER = os.environ.get("GH_USER", "ShanedixonGit")
OUT = os.environ.get("OUT_DIR", "dist")
DAYS = int(os.environ.get("DAYS", 30))

QUOTES = [
    ("Everything should be made as simple as possible, but not simpler.", "Albert Einstein"),
    ("In God we trust. All others must bring data.", "W. Edwards Deming"),
    ("The goal is to turn data into information, and information into insight.", "Carly Fiorina"),
    ("Torture the data long enough and it will confess to anything.", "Ronald Coase"),
    ("Premature optimisation is the root of all evil.", "Donald Knuth"),
    ("All models are wrong, but some are useful.", "George Box"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Without data you're just another person with an opinion.", "W. Edwards Deming"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("The most damaging phrase in the language is: we've always done it this way.", "Grace Hopper"),
    ("Data is a precious thing and will last longer than the systems themselves.", "Tim Berners-Lee"),
    ("If you can't describe what you are doing as a process, you don't know what you're doing.", "W. Edwards Deming"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("It is a capital mistake to theorise before one has data.", "Arthur Conan Doyle"),
    ("The best way to get the right answer is to state the wrong one confidently.", "Cunningham's Law"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("A good forecast is not the one that is right, it is the one you can defend.", "Anonymous"),
    ("Complexity is the enemy of execution.", "Tony Robbins"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Numbers have an important story to tell. They rely on you to give them a voice.", "Stephen Few"),
]


def fetch_days():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "readme-activity-graph", "Accept": "text/html"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8", "replace")

    counts = {}
    for tid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        m = re.match(r"(\d+)\s+contribution", text.strip())
        counts[tid] = int(m.group(1)) if m else 0

    days = []
    for cell in re.findall(r"<td[^>]*>", page):
        d = re.search(r'data-date="([^"]+)"', cell)
        i = re.search(r'id="([^"]+)"', cell)
        if not d:
            continue
        days.append((d.group(1), counts.get(i.group(1) if i else "", 0)))

    days.sort()
    today = datetime.date.today().isoformat()
    days = [x for x in days if x[0] <= today]
    return days[-DAYS:]


def activity_svg(days):
    W, H = 900, 260
    PL, PR, PT, PB = 52, 24, 46, 42
    iw, ih = W - PL - PR, H - PT - PB
    vals = [c for _, c in days]
    top = max(max(vals), 1)
    step = iw / max(len(days) - 1, 1)

    pts = [(PL + i * step, PT + ih - (v / top) * ih) for i, v in enumerate(vals)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{PL:.1f},{PT + ih:.1f} " + line + f" {PL + (len(pts) - 1) * step:.1f},{PT + ih:.1f}"

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        """<style>
  .g { stroke: #8B949E; stroke-opacity: .2; }
  .t { fill: #57606A; font-size: 11px; }
  .h { fill: #57606A; font-size: 12px; letter-spacing: 2px; }
  @media (prefers-color-scheme: dark) { .t, .h { fill: #8B949E; } }
</style>""",
        '<defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#1F6FEB" stop-opacity="0.42"/>'
        '<stop offset="100%" stop-color="#1F6FEB" stop-opacity="0.02"/></linearGradient></defs>',
        f'<text class="h" x="{PL}" y="24">COMMIT ACTIVITY &#183; LAST {len(days)} DAYS</text>',
    ]

    for k in range(5):
        y = PT + ih - (ih * k / 4)
        s.append(f'<line class="g" x1="{PL}" y1="{y:.1f}" x2="{W - PR}" y2="{y:.1f}" />')
        s.append(f'<text class="t" x="{PL - 10}" y="{y + 4:.1f}" text-anchor="end">{round(top * k / 4)}</text>')

    s.append(f'<polygon points="{area}" fill="url(#f)" />')
    s.append(f'<polyline points="{line}" fill="none" stroke="#2F81F7" stroke-width="2.2" '
             'stroke-linejoin="round" stroke-linecap="round" />')

    peak = max(range(len(vals)), key=lambda i: vals[i])
    if vals[peak]:
        px, py = pts[peak]
        s.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#58A6FF" />')

    for i in (0, len(days) // 2, len(days) - 1):
        d = datetime.date.fromisoformat(days[i][0])
        anchor = "start" if i == 0 else ("end" if i == len(days) - 1 else "middle")
        s.append(f'<text class="t" x="{PL + i * step:.1f}" y="{PT + ih + 24:.0f}" '
                 f'text-anchor="{anchor}">{d.strftime("%d %b")}</text>')

    total = sum(vals)
    s.append(f'<text class="t" x="{W - PR}" y="24" text-anchor="end">{total} contributions</text>')
    s.append("</svg>")
    return "\n".join(s)


def quote_svg():
    seed = datetime.date.today().toordinal()
    text, author = random.Random(seed).choice(QUOTES)
    lines = textwrap.wrap(text, 62)
    W = 820
    H = 58 + len(lines) * 30
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        """<style>
  .q { fill: #57606A; font-size: 16px; font-style: italic; }
  .a { fill: #2F81F7; font-size: 13px; font-weight: 700; }
  @media (prefers-color-scheme: dark) { .q { fill: #B9C2CC; } }
</style>""",
        f'<line x1="0" y1="8" x2="0" y2="{H - 34}" stroke="#2F81F7" stroke-width="3" />',
    ]
    for i, ln in enumerate(lines):
        s.append(f'<text class="q" x="{W / 2:.0f}" y="{34 + i * 30}" text-anchor="middle">'
                 f'{html.escape(ln)}</text>')
    s.append(f'<text class="a" x="{W / 2:.0f}" y="{34 + len(lines) * 30 + 6}" text-anchor="middle">'
             f'&#8212; {html.escape(author)}</text>')
    s.append("</svg>")
    return "\n".join(s)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "quote.svg"), "w") as f:
        f.write(quote_svg())
    try:
        days = fetch_days()
    except Exception as e:
        print(f"contribution fetch failed: {e}", file=sys.stderr)
        return 1
    if not days:
        print("no contribution data parsed", file=sys.stderr)
        return 1
    with open(os.path.join(OUT, "activity-graph.svg"), "w") as f:
        f.write(activity_svg(days))
    print(f"rendered {len(days)} days, {sum(c for _, c in days)} contributions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
