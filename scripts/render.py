import datetime
import html
import math
import os
import re
import sys
import textwrap
import urllib.request

USER = os.environ.get("GH_USER", "ShanedixonGit")
OUT = os.environ.get("OUT_DIR", "dist")
DAYS = int(os.environ.get("DAYS", 30))

QUOTE = "The right question is usually more important than the right answer"
QUOTE_ATTRIB = "Attributed to Plato"

PALETTE = """
  .grid { stroke: #D1242F; stroke-opacity: .18; }
  .tick { fill: #57606A; font-size: 11px; }
  .head { fill: #57606A; font-size: 12px; letter-spacing: 2px; }
  .edge { stroke: #DA3633; }
  .node { fill: #DA3633; }
  .halo { stroke: #DA3633; }
  @media (prefers-color-scheme: dark) {
    .grid { stroke: #F85149; stroke-opacity: .16; }
    .tick, .head { fill: #8B949E; }
    .edge { stroke: #F85149; }
    .node { fill: #FF7B72; }
    .halo { stroke: #FF7B72; }
  }
"""


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
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) or 1

    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<style>{PALETTE}</style>",
        '<defs><linearGradient id="f" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#F85149" stop-opacity="0.40"/>'
        '<stop offset="100%" stop-color="#F85149" stop-opacity="0.02"/></linearGradient></defs>',
        f'<text class="head" x="{PL}" y="24" opacity="0">COMMIT ACTIVITY &#183; LAST {len(days)} DAYS'
        '<animate attributeName="opacity" from="0" to="1" begin="0s" dur="0.6s" fill="freeze" /></text>',
    ]

    for k in range(5):
        y = PT + ih - (ih * k / 4)
        b = 0.05 * k
        s.append(f'<line class="grid" x1="{PL}" y1="{y:.1f}" x2="{W - PR}" y2="{y:.1f}" opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur="0.5s" fill="freeze" /></line>')
        s.append(f'<text class="tick" x="{PL - 10}" y="{y + 4:.1f}" text-anchor="end" opacity="0">{round(top * k / 4)}'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur="0.5s" fill="freeze" /></text>')

    s.append(f'<polygon points="{area}" fill="url(#f)" opacity="0">'
             '<animate attributeName="opacity" from="0" to="1" begin="0.9s" dur="0.9s" fill="freeze" /></polygon>')
    s.append(f'<polyline class="edge" points="{line}" fill="none" stroke-width="2.2" '
             f'stroke-linejoin="round" stroke-linecap="round" stroke-dasharray="{length:.1f}" '
             f'stroke-dashoffset="{length:.1f}">'
             f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" begin="0.25s" dur="1.7s" '
             'calcMode="spline" keySplines="0.37 0 0.21 1" fill="freeze" /></polyline>')

    peak = max(range(len(vals)), key=lambda i: vals[i])
    if vals[peak]:
        px, py = pts[peak]
        s.append(f'<circle class="halo" cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="none" stroke-width="1.5" opacity="0">'
                 '<animate attributeName="r" values="4.5;13" begin="2.2s" dur="2.4s" repeatCount="indefinite" />'
                 '<animate attributeName="opacity" values="0.55;0" begin="2.2s" dur="2.4s" repeatCount="indefinite" /></circle>')
        s.append(f'<circle class="node" cx="{px:.1f}" cy="{py:.1f}" r="0">'
                 '<animate attributeName="r" values="0;5.8;4.5" keyTimes="0;0.68;1" begin="1.95s" '
                 'dur="0.55s" fill="freeze" /></circle>')

    for i in (0, len(days) // 2, len(days) - 1):
        d = datetime.date.fromisoformat(days[i][0])
        anchor = "start" if i == 0 else ("end" if i == len(days) - 1 else "middle")
        s.append(f'<text class="tick" x="{PL + i * step:.1f}" y="{PT + ih + 24:.0f}" '
                 f'text-anchor="{anchor}" opacity="0">{d.strftime("%d %b")}'
                 '<animate attributeName="opacity" from="0" to="1" begin="1.6s" dur="0.6s" fill="freeze" /></text>')

    total = sum(vals)
    s.append(f'<text class="tick" x="{W - PR}" y="24" text-anchor="end" opacity="0">{total} contributions'
             '<animate attributeName="opacity" from="0" to="1" begin="1.9s" dur="0.6s" fill="freeze" /></text>')
    s.append("</svg>")
    return "\n".join(s)


def quote_svg():
    lines = textwrap.wrap(QUOTE, 52)
    W = 820
    H = 58 + len(lines) * 30
    bar = H - 34
    s = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        """<style>
  .quote { fill: #57606A; font-size: 16px; font-style: italic; }
  .by    { fill: #B62324; font-size: 13px; font-weight: 700; }
  .rule  { stroke: #DA3633; }
  @media (prefers-color-scheme: dark) {
    .quote { fill: #B9C2CC; }
    .by    { fill: #FF7B72; }
    .rule  { stroke: #F85149; }
  }
</style>""",
        f'<line class="rule" x1="0" y1="8" x2="0" y2="8" stroke-width="3" stroke-linecap="round">'
        f'<animate attributeName="y2" from="8" to="{bar}" begin="0.1s" dur="0.8s" '
        'calcMode="spline" keySplines="0.22 1 0.36 1" fill="freeze" /></line>',
    ]
    for i, ln in enumerate(lines):
        s.append(f'<text class="quote" x="{W / 2:.0f}" y="{34 + i * 30}" text-anchor="middle" opacity="0">'
                 f'{html.escape(ln)}'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{0.35 + i * 0.22:.2f}s" dur="0.7s" fill="freeze" />'
                 '</text>')
    s.append(f'<text class="by" x="{W / 2:.0f}" y="{34 + len(lines) * 30 + 6}" text-anchor="middle" opacity="0">'
             f'&#8212; {html.escape(QUOTE_ATTRIB)}'
             f'<animate attributeName="opacity" from="0" to="1" begin="{0.35 + len(lines) * 0.22:.2f}s" dur="0.7s" fill="freeze" />'
             '</text>')
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
