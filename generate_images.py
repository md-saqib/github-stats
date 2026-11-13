#!/usr/bin/python3

import asyncio
import datetime as dt
import os
from html import escape
from typing import Any, Dict, List

import aiohttp

from github_stats import Stats

SANS = "Geist, Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": {
        "card": "#0d1117",
        "fg": "#e6edf3",
        "muted": "#8b949e",
        "subtle": "#161b22",
        "border": "#30363d",
        "blue": "#60a5fa",
        "violet": "#a78bfa",
        "pink": "#f472b6",
        "cyan": "#22d3ee",
        "green": "#3fb950",
        "yellow": "#e3b341",
        "heatmap": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
    },
    "light": {
        "card": "#ffffff",
        "fg": "#1f2328",
        "muted": "#59636e",
        "subtle": "#eff2f5",
        "border": "#d8dee4",
        "blue": "#2563eb",
        "violet": "#7c3aed",
        "pink": "#db2777",
        "cyan": "#0891b2",
        "green": "#1a7f37",
        "yellow": "#bf8700",
        "heatmap": ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"],
    },
}

ICONS = {
    "commit": "M1 2.5A2.5 2.5 0 013.5 0h8.75a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0V1.5h-8a1 1 0 00-1 1v6.708A2.492 2.492 0 013.5 9h3.25a.75.75 0 010 1.5H3.5a1 1 0 100 2h5.75a.75.75 0 010 1.5H3.5A2.5 2.5 0 011 11.5v-9zm13.23 7.79a.75.75 0 001.06-1.06l-2.505-2.505a.75.75 0 00-1.06 0L9.22 9.229a.75.75 0 001.06 1.061l1.225-1.224v6.184a.75.75 0 001.5 0V9.066l1.224 1.224z",
    "star": "M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.818 6.374a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z",
    "repo": "M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z",
    "diff": "M8.75 1.75a.75.75 0 00-1.5 0V5H4a.75.75 0 000 1.5h3.25v3.25a.75.75 0 001.5 0V6.5H12A.75.75 0 0012 5H8.75V1.75zM4 13a.75.75 0 000 1.5h8a.75.75 0 100-1.5H4z",
    "eye": "M1.679 7.932c.412-.621 1.242-1.75 2.366-2.717C5.175 4.242 6.527 3.5 8 3.5c1.473 0 2.824.742 3.955 1.715 1.124.967 1.954 2.096 2.366 2.717a.119.119 0 010 .136c-.412.621-1.242 1.75-2.366 2.717C10.825 11.758 9.473 12.5 8 12.5c-1.473 0-2.824-.742-3.955-1.715C2.92 9.818 2.09 8.69 1.679 8.068a.119.119 0 010-.136zM8 2c-1.981 0-3.67.992-4.933 2.078C1.797 5.169.88 6.423.43 7.1a1.619 1.619 0 000 1.798c.45.678 1.367 1.932 2.637 3.024C4.329 13.008 6.019 14 8 14c1.981 0 3.67-.992 4.933-2.078 1.27-1.091 2.187-2.345 2.637-3.023a1.619 1.619 0 000-1.798c-.45-.678-1.367-1.932-2.637-3.023C11.671 2.992 9.981 2 8 2zm0 8a2 2 0 100-4 2 2 0 000 4z",
    "fork": "M5 3.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm0 2.122a2.25 2.25 0 10-1.5 0v.878A2.25 2.25 0 005.75 8.5h1.5v2.128a2.251 2.251 0 101.5 0V8.5h1.5a2.25 2.25 0 002.25-2.25v-.878a2.25 2.25 0 10-1.5 0v.878a.75.75 0 01-.75.75h-4.5A.75.75 0 015 6.25v-.878zm3.75 7.378a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm3-8.75a.75.75 0 100-1.5.75.75 0 000 1.5z",
}

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def fmt(n: int) -> str:
    if n < 100_000:
        return f"{n:,}"
    for div, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            v = n / div
            return (f"{v:.1f}".rstrip("0").rstrip(".") if v < 100 else f"{v:.0f}") + suffix
    return str(n)


def frame(
    w: int, h: int, t: Dict[str, Any], accent: str, accent2: str, title: str, body: str, css: str = ""
) -> str:
    style = (
        f".sans{{font-family:{SANS}}}"
        f".mono{{font-family:{MONO};letter-spacing:.12em}}"
        ".num{font-variant-numeric:tabular-nums}"
        "@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        ".rise{animation:rise .8s cubic-bezier(.22,1,.36,1) both}"
        ".fade{animation:fade .6s ease-out both}"
        + css
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    a, b = t[accent], t[accent2]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" role="img" aria-labelledby="title">
<title id="title">{escape(title)}</title>
<style>{style}</style>
<defs>
<clipPath id="clip"><rect width="{w}" height="{h}" rx="12"/></clipPath>
<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" stroke="{t['fg']}" stroke-opacity=".06"/></pattern>
<radialGradient id="glow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate({w * 0.75:.0f} 0) scale({w * 0.7:.0f} {h * 1.2:.0f})"><stop stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
<mask id="fade"><rect width="{w}" height="{h}" fill="url(#glow)"/></mask>
<radialGradient id="tint" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate({w} 0) scale({w * 0.75:.0f} {h * 1.4:.0f})"><stop stop-color="{a}" stop-opacity=".22"/><stop offset="1" stop-color="{a}" stop-opacity="0"/></radialGradient>
<radialGradient id="tint2" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(0 {h}) scale({w * 0.6:.0f} {h * 1.1:.0f})"><stop stop-color="{b}" stop-opacity=".14"/><stop offset="1" stop-color="{b}" stop-opacity="0"/></radialGradient>
<linearGradient id="brand" x1="0" x2="{w}" y1="0" y2="0" gradientUnits="userSpaceOnUse"><stop stop-color="{t['blue']}"/><stop offset=".5" stop-color="{t['violet']}"/><stop offset="1" stop-color="{t['pink']}"/></linearGradient>
<linearGradient id="rule" x1="24" x2="{w - 24}" y1="0" y2="0" gradientUnits="userSpaceOnUse"><stop stop-color="{a}"/><stop offset=".6" stop-color="{b}" stop-opacity=".5"/><stop offset="1" stop-color="{t['border']}"/></linearGradient>
</defs>
<g clip-path="url(#clip)"><rect width="{w}" height="{h}" fill="{t['card']}"/><rect width="{w}" height="{h}" fill="url(#tint)"/><rect width="{w}" height="{h}" fill="url(#tint2)"/><rect width="{w}" height="{h}" fill="url(#grid)" mask="url(#fade)"/><rect width="{w}" height="3" fill="url(#brand)"/></g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="11.5" stroke="{t['border']}"/>
{body}
</svg>
"""


def label_row(t: Dict[str, Any], w: int, color: str, text: str, right: str = "") -> str:
    out = (
        f'<text class="mono fade" x="24" y="34" font-size="11" fill="{t["muted"]}">'
        f'<tspan fill="{color}">✦</tspan><tspan dx="8">{escape(text.upper())}</tspan></text>'
    )
    if right:
        out += (
            f'<text class="mono fade" x="{w - 24}" y="34" font-size="11" fill="{t["muted"]}" '
            f'text-anchor="end">{escape(right.upper())}</text>'
        )
    return out


def title_text(t: Dict[str, Any], lead: str, strong: str, x: int = 24, y: int = 68) -> str:
    return (
        f'<text class="sans rise" x="{x}" y="{y}" font-size="22" font-weight="600" letter-spacing="-.02em" '
        f'fill="{t["fg"]}"><tspan fill="{t["muted"]}">{escape(lead)}</tspan>{escape(strong)}</text>'
    )


def render_overview(d: Dict[str, Any], t: Dict[str, Any]) -> str:
    w, h = 410, 220
    cells = [
        ("Contributions", d["contributions"], "commit", "green"),
        ("Stars", d["stars"], "star", "yellow"),
        ("Repos", d["repos"], "repo", "blue"),
        ("Lines changed", d["lines"], "diff", "violet"),
        ("Views · 14d", d["views"], "eye", "cyan"),
        ("Forks", d["forks"], "fork", "pink"),
    ]
    xs = [24, 162, 284]
    title = title_text(t, "On GitHub since ", str(d["since"])) if d.get("since") else title_text(t, "", d["name"])
    body = [
        label_row(t, w, t["violet"], "Overview", f"Updated {d['updated']}"),
        title,
        f'<path d="M24 88.5H{w - 24}" stroke="url(#rule)"/>',
        f'<path d="M146.5 102V200M268.5 102V200" stroke="{t["border"]}"/>',
    ]
    for i, (label, value, icon, color) in enumerate(cells):
        x, top = xs[i % 3], 88 + 58 * (i // 3)
        body.append(
            f'<g class="rise" style="animation-delay:{150 + i * 70}ms">'
            f'<text class="sans num" x="{x}" y="{top + 34}" font-size="24" font-weight="600" '
            f'letter-spacing="-.02em" fill="{t["fg"]}">{fmt(value)}</text>'
            f'<path transform="translate({x} {top + 41}) scale(.75)" fill-rule="evenodd" fill="{t[color]}" d="{ICONS[icon]}"/>'
            f'<text class="mono" x="{x + 18}" y="{top + 51}" font-size="10" fill="{t["muted"]}">'
            f"{escape(label.upper())}</text></g>"
        )
    return frame(w, h, t, "violet", "blue", "GitHub overview", "\n".join(body))


def render_languages(d: Dict[str, Any], t: Dict[str, Any]) -> str:
    w, h = 410, 220
    langs = sorted(d["languages"], key=lambda x: -x[1])
    if len(langs) > 6:
        langs = langs[:5] + [("Other", sum(p for _, p, _ in langs[5:]), None)]
    colors = [c or t["muted"] for _, _, c in langs]

    body = [
        label_row(t, w, t["blue"], "Languages", "By code size"),
        title_text(t, "Mostly ", langs[0][0]) if langs else title_text(t, "", "No languages yet"),
    ]

    bar_x, bar_y, bar_w = 24, 86, w - 48
    gap = 2
    usable = bar_w - gap * max(len(langs) - 1, 0)
    segments, x = [], float(bar_x)
    for (_, prop, _), color in zip(langs, colors):
        seg = max(usable * prop / 100, 2)
        segments.append(f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" height="10" fill="{color}"/>')
        x += seg + gap
    body.append(
        f'<defs><clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath></defs>'
        f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{t["subtle"]}"/>'
        f'<g clip-path="url(#bar)"><g class="grow">{"".join(segments)}</g></g>'
    )

    cols = [(24, 193), (217, w - 24)]
    rows = [134, 166, 198]
    for i, ((name, prop, _), color) in enumerate(zip(langs, colors)):
        (left, right), y = cols[i // 3], rows[i % 3]
        name = name if len(name) <= 14 else name[:13] + "…"
        body.append(
            f'<g class="rise" style="animation-delay:{300 + i * 70}ms">'
            f'<circle cx="{left + 5}" cy="{y - 5}" r="5" fill="{color}"/>'
            f'<text class="sans" x="{left + 18}" y="{y}" font-size="14" fill="{t["fg"]}">{escape(name)}</text>'
            f'<text class="mono num" x="{right}" y="{y}" font-size="12" fill="{t["muted"]}" '
            f'text-anchor="end" letter-spacing="0">{prop:.1f}%</text></g>'
        )
    css = (
        "@keyframes grow{from{transform:scaleX(0)}}"
        ".grow{transform-origin:24px 0;animation:grow 1.2s cubic-bezier(.22,1,.36,1) .2s both}"
    )
    return frame(w, h, t, "blue", "cyan", "Most used languages", "\n".join(body), css)


def render_activity(d: Dict[str, Any], t: Dict[str, Any]) -> str:
    w, h = 840, 272
    weeks = d["weeks"][-53:]
    ramp = t["heatmap"]
    css = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(ramp))

    body = [
        label_row(t, w, t["green"], "Activity", "Last 12 months"),
        f'<text class="sans rise num" x="24" y="72" font-size="22" font-weight="600" letter-spacing="-.02em" '
        f'fill="{t["fg"]}">{d["total"]:,}<tspan fill="{t["muted"]}"> contributions</tspan></text>',
    ]

    best_count, best_date = d["best"]
    stats = [
        ("Best day", f"{best_count:,}", best_date, "yellow"),
        ("Longest streak", f"{d['longest']:,}", "days", "violet"),
        ("Current streak", f"{d['current']:,}", "days", "green"),
    ]
    for i, (label, value, unit, color) in enumerate(stats):
        x = w - 24 - 140 * (2 - i)
        body.append(
            f'<g class="rise" style="animation-delay:{150 + i * 70}ms">'
            f'<text class="sans num" x="{x}" y="66" font-size="20" font-weight="600" letter-spacing="-.02em" '
            f'fill="{t[color]}" text-anchor="end">{value}<tspan fill="{t["muted"]}" font-size="12" '
            f'font-weight="400" letter-spacing="0" dx="4">{escape(unit)}</tspan></text>'
            f'<text class="mono" x="{x}" y="84" font-size="10" fill="{t["muted"]}" text-anchor="end">'
            f"{escape(label.upper())}</text></g>"
        )

    x0, y0, pitch, cell = 24, 124, 15, 12
    months: List[str] = []
    last_month, last_x = None, -100
    for col, week in enumerate(weeks):
        days = week.get("contributionDays", [])
        if not days:
            continue
        month = dt.date.fromisoformat(days[0]["date"]).strftime("%b")
        x = x0 + col * pitch
        if month != last_month and x - last_x >= 36 and col <= len(weeks) - 3:
            months.append(
                f'<text class="mono" x="{x}" y="114" font-size="10" fill="{t["muted"]}">{month.upper()}</text>'
            )
            last_x = x
        last_month = month
    body.append(f'<g class="fade">{"".join(months)}</g>')

    for col, week in enumerate(weeks):
        x = x0 + col * pitch
        rects = "".join(
            f'<rect x="{x}" y="{y0 + day.get("weekday", 0) * pitch}" width="{cell}" height="{cell}" rx="3" '
            f'class="l{LEVELS.get(day.get("contributionLevel"), 0)}"/>'
            for day in week.get("contributionDays", [])
        )
        body.append(f'<g class="fade" style="animation-delay:{200 + col * 12}ms">{rects}</g>')

    legend = "".join(
        f'<rect x="{w - 24 - 34 - (4 - i) * 15 - 12}" y="242" width="{cell}" height="{cell}" rx="3" class="l{i}"/>'
        for i in range(5)
    )
    body.append(
        f'<g class="fade" style="animation-delay:900ms">'
        f'<text class="mono" x="24" y="252" font-size="10" fill="{t["muted"]}">'
        f'<tspan fill="{t["green"]}">{d["active"]:,}</tspan> ACTIVE DAYS</text>'
        f'<text class="mono" x="{w - 24 - 34 - 4 * 15 - 12 - 8}" y="252" font-size="10" fill="{t["muted"]}" '
        f'text-anchor="end">LESS</text>{legend}'
        f'<text class="mono" x="{w - 24}" y="252" font-size="10" fill="{t["muted"]}" text-anchor="end">MORE</text></g>'
    )
    return frame(w, h, t, "green", "cyan", "Contribution activity over the last year", "\n".join(body), css)


def render_mix(d: Dict[str, Any], t: Dict[str, Any]) -> str:
    w, h = 410, 220
    palette = {
        "Commits": "violet",
        "Pull requests": "blue",
        "Code reviews": "pink",
        "Issues": "cyan",
        "New repos": "green",
        "Private": "yellow",
    }
    items = [(k, v, t[palette.get(k, "muted")]) for k, v in d["items"].items() if v > 0]
    items.sort(key=lambda x: -x[1])
    total = sum(v for _, v, _ in items)

    body = [label_row(t, w, t["pink"], "Contribution mix", "Last 12 months")]
    if not total:
        body.append(title_text(t, "", "No contributions yet"))
        return frame(w, h, t, "pink", "violet", "Contribution mix", "\n".join(body))
    body.append(title_text(t, "Mostly ", items[0][0].lower()))

    cx, cy, r = 88, 146, 44
    gap = 0.8 if len(items) > 1 else 0
    arcs, start = [], 0.0
    for i, (_, v, color) in enumerate(items):
        share = 100 * v / total
        arcs.append(
            f'<circle class="arc" cx="{cx}" cy="{cy}" r="{r}" pathLength="100" stroke="{color}" stroke-width="14" '
            f'stroke-dasharray="{max(share - gap, 0.01):.2f} {100 - max(share - gap, 0.01):.2f}" '
            f'stroke-dashoffset="{-start:.2f}" transform="rotate(-90 {cx} {cy})" style="animation-delay:{200 + i * 120}ms"/>'
        )
        start += share
    body.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{t["subtle"]}" stroke-width="14"/>{"".join(arcs)}'
        f'<text class="sans num rise" x="{cx}" y="{cy + 4}" font-size="20" font-weight="600" letter-spacing="-.02em" '
        f'fill="{t["fg"]}" text-anchor="middle">{fmt(total)}</text>'
        f'<text class="mono rise" x="{cx}" y="{cy + 20}" font-size="9" fill="{t["muted"]}" text-anchor="middle">TOTAL</text>'
    )

    step = 21 if len(items) <= 5 else 19
    first = cy - (len(items) - 1) * step / 2 + 4
    for i, (name, v, color) in enumerate(items):
        y = first + i * step
        body.append(
            f'<g class="rise" style="animation-delay:{300 + i * 70}ms">'
            f'<circle cx="{172}" cy="{y - 4.5:.1f}" r="4.5" fill="{color}"/>'
            f'<text class="sans" x="184" y="{y:.1f}" font-size="13" fill="{t["fg"]}">{escape(name)}</text>'
            f'<text class="mono num" x="{w - 24}" y="{y:.1f}" font-size="12" fill="{t["fg"]}" text-anchor="end" '
            f'letter-spacing="0">{v:,}<tspan fill="{t["muted"]}" dx="8">{100 * v / total:.0f}%</tspan></text></g>'
        )
    css = (
        "@keyframes draw{from{stroke-dasharray:0 100}}"
        ".arc{animation:draw 1.1s cubic-bezier(.22,1,.36,1) both}"
    )
    return frame(w, h, t, "pink", "violet", "Contribution mix over the last year", "\n".join(body), css)


def render_rhythm(d: Dict[str, Any], t: Dict[str, Any]) -> str:
    w, h = 410, 220
    sums = [0] * 7
    for day in d["days"]:
        sums[day.get("weekday", 0)] += day.get("contributionCount", 0)
    peak = max(range(7), key=lambda i: sums[i])
    top = max(sums) or 1

    body = [
        label_row(t, w, t["cyan"], "Weekly rhythm", "Last 12 months"),
        title_text(t, "Most active on ", WEEKDAYS[peak] + "s") if any(sums) else title_text(t, "", "No activity yet"),
        f'<defs><linearGradient id="bars" x1="0" x2="0" y1="100" y2="186" gradientUnits="userSpaceOnUse">'
        f'<stop stop-color="{t["violet"]}"/><stop offset="1" stop-color="{t["cyan"]}"/></linearGradient></defs>',
        f'<path d="M24 186.5H{w - 24}" stroke="{t["border"]}"/>',
    ]
    pitch = (w - 48) / 7
    bar_w = 28
    for i, total in enumerate(sums):
        bh = max(3, 84 * total / top)
        x = 24 + i * pitch + (pitch - bar_w) / 2
        cx = x + bar_w / 2
        is_peak = i == peak and any(sums)
        body.append(
            f'<rect class="bar" x="{x:.1f}" y="{186 - bh:.1f}" width="{bar_w}" height="{bh:.1f}" rx="6" '
            f'fill="url(#bars)" fill-opacity="{1 if is_peak else 0.5}" style="animation-delay:{200 + i * 80}ms"/>'
            f'<g class="rise" style="animation-delay:{500 + i * 80}ms">'
            f'<text class="mono num" x="{cx:.1f}" y="{180 - bh:.1f}" font-size="10" letter-spacing="0" '
            f'fill="{t["fg"] if is_peak else t["muted"]}" text-anchor="middle">{fmt(total)}</text>'
            f'<text class="mono" x="{cx:.1f}" y="205" font-size="10" fill="{t["cyan"] if is_peak else t["muted"]}" '
            f'text-anchor="middle">{WEEKDAYS[i][:3].upper()}</text></g>'
        )
    css = (
        "@keyframes growy{from{transform:scaleY(0)}}"
        ".bar{transform-box:fill-box;transform-origin:50% 100%;animation:growy .9s cubic-bezier(.22,1,.36,1) both}"
    )
    return frame(w, h, t, "cyan", "violet", "Contributions by day of the week", "\n".join(body), css)


async def collect(s: Stats) -> Dict[str, Dict[str, Any]]:
    lines = await s.lines_changed
    calendar = await s.calendar
    current, longest = await s.streaks
    days = [day for week in calendar.get("weeks", []) for day in week.get("contributionDays", [])]
    best = max(days, key=lambda day: day.get("contributionCount", 0), default=None)
    best_date = dt.date.fromisoformat(best["date"]).strftime("%d %b").lstrip("0") if best else "—"
    return {
        "overview": {
            "name": await s.name,
            "since": await s.first_year,
            "stars": await s.stargazers,
            "forks": await s.forks,
            "contributions": await s.total_contributions,
            "lines": lines[0] + lines[1],
            "views": await s.views,
            "repos": len(await s.repos),
            "updated": dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y").lstrip("0"),
        },
        "languages": {
            "languages": [
                (k, v.get("prop", 0), v.get("color")) for k, v in (await s.languages).items()
            ],
        },
        "activity": {
            "total": calendar.get("totalContributions", 0),
            "weeks": calendar.get("weeks", []),
            "current": current,
            "longest": longest,
            "best": (best.get("contributionCount", 0) if best else 0, best_date),
            "active": sum(1 for day in days if day.get("contributionCount", 0) > 0),
        },
        "mix": {"items": await s.contribution_mix},
        "rhythm": {"days": days},
    }


def write_cards(data: Dict[str, Dict[str, Any]], out_dir: str = "generated") -> None:
    renderers = {
        "overview": render_overview,
        "languages": render_languages,
        "activity": render_activity,
        "mix": render_mix,
        "rhythm": render_rhythm,
    }
    os.makedirs(out_dir, exist_ok=True)
    for card, render in renderers.items():
        for theme_name, theme in THEMES.items():
            path = os.path.join(out_dir, f"{card}-{theme_name}.svg")
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(render(data[card], theme))


async def main() -> None:
    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise Exception("A personal access token is required to proceed!")
    user = os.getenv("GITHUB_ACTOR")
    if user is None:
        raise RuntimeError("Environment variable GITHUB_ACTOR must be set.")
    exclude_repos = os.getenv("EXCLUDED")
    excluded_repos = {x.strip() for x in exclude_repos.split(",")} if exclude_repos else None
    exclude_langs = os.getenv("EXCLUDED_LANGS")
    excluded_langs = {x.strip() for x in exclude_langs.split(",")} if exclude_langs else None
    raw_ignore_forked_repos = os.getenv("EXCLUDE_FORKED_REPOS")
    ignore_forked_repos = (
        not not raw_ignore_forked_repos and raw_ignore_forked_repos.strip().lower() != "false"
    )
    async with aiohttp.ClientSession() as session:
        s = Stats(
            user,
            access_token,
            session,
            exclude_repos=excluded_repos,
            exclude_langs=excluded_langs,
            ignore_forked_repos=ignore_forked_repos,
        )
        write_cards(await collect(s))


if __name__ == "__main__":
    asyncio.run(main())
