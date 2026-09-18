#!/usr/bin/env python3
"""Render the canonical public profile snapshot into light_mode.svg / dark_mode.svg.

Offline and deterministic: stdlib only, no network access, no GitHub API calls.
The script rewrites ONLY the right-hand <text> column of each SVG. Everything else
(styles, background rect, the ASCII portrait, and every statistical row emitted by
today.py) is preserved byte-for-byte, so the two scripts can run in any order.

Statistical fields owned by today.py (age_data, commit_data, star_data, repo_data,
contrib_data, follower_data, loc_data, loc_add, loc_del and their *_dots partners)
are copied verbatim, ids included.

Usage:
    python render_profile.py                      # uses ./profile.json next to this script
    python render_profile.py --profile ../my-portfolio/data/profile.json
    python render_profile.py --svg-dir .

Exit codes: 0 written, 1 missing/invalid input.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
Q = "{" + SVG_NS + "}"

# Geometry of the existing canvas (must not be changed: the ASCII portrait depends on it).
CANVAS_W = 985
CANVAS_MIN_H = 530
COL_X = 390
ROW_Y0 = 30
ROW_H = 20
# Longest row that stays inside the 985px canvas at 16px monospace (109% size-adjust).
LINE_LIMIT = 61

MAX_SKILL_ROWS = 8
MAX_EXPERIENCE_ROWS = 8
# Keys longer than this fall back to their first word so the value keeps room to breathe.
KEY_LABEL_MAX = 12

STATS_IDS = (
    "repo_data",
    "contrib_data",
    "star_data",
    "commit_data",
    "follower_data",
    "loc_data",
    "loc_add",
    "loc_del",
)
DYNAMIC_HEADER = "- GitHub Stats"


# --------------------------------------------------------------------------- helpers


def warn(message: str) -> None:
    print(f"render_profile: {message}", file=sys.stderr)


def load_profile(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(
            f"render_profile: profile snapshot not found: {path}\n"
            "Run the workspace sync (scripts/sync-profile.py) or pass --profile <path>."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"render_profile: cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("person"), dict):
        raise SystemExit(f"render_profile: {path} has no 'person' object")
    version = data.get("schema_version")
    if version != 1:
        warn(f"unexpected schema_version {version!r} in {path}; rendering best-effort")
    return data


def text(value: object, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip()
    return str(value)


def short_label(name: str, limit: int = KEY_LABEL_MAX) -> str:
    """Group/org names double as row keys; keep them narrow enough for the value.

    A usable leading word ("Cozwork Joint Stock Company" -> "Cozwork") reads better than
    an arbitrary cut, but too-short leads are dropped in favour of the name itself.
    """
    name = text(name)
    if len(name) <= limit:
        return name
    first = name.split()[0] if name.split() else name
    if 4 <= len(first) <= limit:
        return first
    return name[: limit - 1].rstrip() + "\u2026"


def compact_item(item: str) -> str:
    """Tighten separators only; technology names themselves stay untouched."""
    item = text(item)
    for sep in (" / ", " & ", " + "):
        item = item.replace(sep, sep.strip())
    return item


def truncate(value: str, budget: int, label: str) -> str:
    if budget < 1:
        return ""
    if len(value) <= budget:
        return value
    warn(f"{label}: value shortened to fit the canvas ({len(value)} > {budget} chars)")
    if budget == 1:
        return "\u2026"
    return value[: budget - 1].rstrip() + "\u2026"


def fit_items(items: list, budget: int, label: str) -> str:
    """Join as many whole items as fit, flagging the remainder rather than dropping it."""
    items = [compact_item(i) for i in items if text(i)]
    total = len(items)
    if not total:
        return ""
    for take in range(total, 0, -1):
        rest = total - take
        candidate = ", ".join(items[:take])
        if rest:
            candidate += f" +{rest} more"
        if len(candidate) <= budget:
            return candidate
    return truncate(items[0], budget, label)


def dot_pad(key: str, value: str) -> str:
    """Dot leader that right-aligns every value at LINE_LIMIT, like the original rows."""
    avail = LINE_LIMIT - (len(key) + 3) - len(value)
    if avail >= 3:
        return " " + "." * (avail - 2) + " "
    if avail == 2:
        return ". "
    return " "


def display_url(url: str) -> str:
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            url = url[len(prefix) :]
    if url.startswith("www."):
        url = url[4:]
    return url.rstrip("/")


def fmt_period(start: object, end: object) -> str:
    begin = text(start)[:4]
    finish = text(end)[:4]
    if not begin and not finish:
        return ""
    if not finish:
        return f"{begin}\u2013present"
    if not begin or begin == finish:
        return finish
    return f"{begin}\u2013{finish}"


def value_budget(key: str) -> int:
    """Room left for a value once the key, its colon and a separating space are placed."""
    return LINE_LIMIT - (len(key) + 3) - 1


def svg(tag: str, **attrs: object) -> ET.Element:
    element = ET.Element(Q + tag)
    for name, value in attrs.items():
        element.set(name, str(value))
    return element


# ------------------------------------------------------------------- row building


def build_header(title: str) -> ET.Element:
    """`- Title -------------` separator row, matching the existing glyph pattern."""
    prefix = f"- {title} "
    tail_len = LINE_LIMIT - len(prefix)
    tail = "\u2014" * max(0, tail_len - 3) + "-\u2014-" if tail_len >= 4 else "\u2014" * tail_len
    row = svg("tspan", x=COL_X, y=0)
    row.text = prefix.rstrip()
    row.tail = " " + tail
    return row


def build_row(key: str, value: str, href: str = "", label: str = "") -> ET.Element:
    """`.` key `:` dots value — with an optional link wrapper around the value."""
    label = label or key
    value = truncate(value, value_budget(key), label)
    if not value:
        value = "\u2014"
    start = svg("tspan", x=COL_X, y=0, **{"class": "cc"})
    start.text = ". "
    key_el = svg("tspan", **{"class": "key"})
    key_el.text = key
    key_el.tail = ":"
    dots_el = svg("tspan", **{"class": "cc"})
    dots_el.text = dot_pad(key, value)
    value_el = svg("tspan", **{"class": "value"})
    value_el.text = value
    if href:
        link = svg("a", href=href)
        link.append(value_el)
        value_el.tail = ""
        return start, key_el, dots_el, link
    return start, key_el, dots_el, value_el


def flatten(parts) -> list:
    if isinstance(parts, ET.Element):
        return [parts]
    out = []
    for part in parts:
        out.extend(flatten(part))
    return out


# --------------------------------------------------------------------- svg surgery


def group_rows(children: list) -> list:
    """Tspans carrying x/y start a new rendered line; the rest continue it."""
    rows: list = []
    for child in children:
        if "y" in child.attrib:
            rows.append([child])
        elif rows:
            rows[-1].append(child)
        else:
            rows.append([child])
    return rows


def row_index(rows: list, element_id: str) -> int:
    for index, row in enumerate(rows):
        for element in row:
            if element.get("id") == element_id:
                return index
        for element in row:
            for nested in element.iter():
                if nested.get("id") == element_id:
                    return index
    return -1


def copy_rows(text_el: ET.Element, first: int, last: int, target_y: int) -> list:
    """Deep-copy original rows (stats, uptime) so their ids and values survive verbatim."""
    children = list(text_el)
    rows = group_rows(children)
    flat = [element for row in rows[first : last + 1] for element in row]
    source_y = int(rows[first][0].get("y", ROW_Y0))
    delta = target_y - source_y
    copied = []
    for element in flat:
        clone = copy.deepcopy(element)
        if "y" in clone.attrib:
            clone.set("y", str(int(clone.get("y")) + delta))
        copied.append(clone)
    return copied


def profile_rows(profile: dict) -> list:
    """Ordered render plan: ('header', title) / ('row', key, value, href) / ('raw', id)."""
    person = profile.get("person") or {}
    plan: list = []

    name = text(person.get("name"))
    if name:
        plan.append(("row", "Name", name, ""))
    role = text(person.get("role"))
    if role:
        plan.append(("row", "Role", role, ""))
    experience = text(person.get("experience_label"))
    if experience:
        plan.append(("row", "Experience", experience, ""))
    location = text(person.get("location"))
    timezone = text(person.get("timezone"))
    if location:
        plan.append(("row", "Location", f"{location} ({timezone})" if timezone else location, ""))
    availability = text(person.get("availability"))
    if availability:
        plan.append(("row", "Remote", availability, ""))
    plan.append(("raw", "age_data"))

    contact = [
        ("Email", text(person.get("email")), "mailto:"),
        ("Phone", text(person.get("phone")), ""),
        ("Portfolio", display_url(text(person.get("portfolio_url"))), text(person.get("portfolio_url"))),
        ("LinkedIn", display_url(text(person.get("linkedin_url"))), text(person.get("linkedin_url"))),
        ("GitHub", display_url(text(person.get("github_url"))), text(person.get("github_url"))),
    ]
    contact = [row for row in contact if row[1]]
    if contact:
        plan.append(("header", "Contact"))
        for key, value, href in contact:
            link = f"mailto:{value}" if href == "mailto:" else href
            plan.append(("row", key, value, link))

    skills = [group for group in profile.get("skills") or [] if isinstance(group, dict)]
    skills = [group for group in skills if text(group.get("name")) and group.get("items")]
    if skills:
        plan.append(("header", "Capabilities"))
        for group in skills[:MAX_SKILL_ROWS]:
            key = short_label(text(group.get("name")))
            items = group.get("items") or []
            value = fit_items(items, value_budget(key), key)
            plan.append(("row", key, value, ""))
        if len(skills) > MAX_SKILL_ROWS:
            warn(f"{len(skills) - MAX_SKILL_ROWS} skill group(s) omitted from the SVG")

    jobs = [job for job in profile.get("experience") or [] if isinstance(job, dict)]
    jobs = [job for job in jobs if text(job.get("role")) or text(job.get("org"))]
    if jobs:
        plan.append(("header", "Work History"))
        for job in jobs[:MAX_EXPERIENCE_ROWS]:
            key = short_label(text(job.get("org")) or text(job.get("role")))
            period = fmt_period(job.get("start"), job.get("end"))
            role = text(job.get("role"))
            value = f"{role} ({period})" if role and period else (role or period)
            plan.append(("row", key, value, ""))
        if len(jobs) > MAX_EXPERIENCE_ROWS:
            warn(f"{len(jobs) - MAX_EXPERIENCE_ROWS} role(s) omitted from the SVG")

    plan.append(("raw", "stats"))
    return plan


def resolve_raw(plan: list, source: ET.Element) -> list:
    """Expand ('raw', id) markers into verbatim copies of the original rows."""
    children = list(source)
    rows = group_rows(children)
    out: list = []
    stats_start = row_index(rows, "repo_data")
    stats_header = stats_start - 1
    if stats_header < 0 or DYNAMIC_HEADER not in "".join(
        (element.text or "") for element in rows[stats_header]
    ):
        stats_header = stats_start
    for item in plan:
        if item[0] != "raw":
            out.append(item)
            continue
        marker = item[1]
        if marker == "age_data":
            index = row_index(rows, "age_data")
            if index < 0:
                warn("age_data row not found; skipping the uptime line")
                continue
            out.append(("copy", index, index))
        else:
            if stats_start < 0:
                warn("statistical rows not found; leaving the stats block out")
                continue
            missing = [i for i in STATS_IDS if row_index(rows, i) < 0]
            if missing:
                warn(f"statistical ids missing from the source SVG: {', '.join(missing)}")
            out.append(("copy", stats_header, len(rows) - 1))
    return out


def render_file(path: Path, plan: list) -> int:
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(path)
    root = tree.getroot()
    texts = [el for el in root.findall(f"{Q}text") if el.get("x") == str(COL_X)]
    if len(texts) != 1:
        raise SystemExit(f"render_profile: expected one right-hand <text> in {path}, found {len(texts)}")
    source = texts[0]

    children = list(source)
    resolved = resolve_raw(plan, source)

    # Identity header keeps its original handle and dash tail; the profile column
    # below it is rebuilt from the snapshot.
    original_first = children[0]
    title = svg("tspan", x=COL_X, y=ROW_Y0)
    title.text = original_first.text or ""
    title.tail = original_first.tail or ""

    y = ROW_Y0
    rebuilt = svg("text", x=COL_X, y=ROW_Y0, fill=source.get("fill", "#24292f"))
    title.set("y", str(y))
    rebuilt.append(title)
    y += ROW_H
    for item in resolved:
        if item[0] == "header":
            header = build_header(item[1])
            header.set("y", str(y))
            rebuilt.append(header)
        elif item[0] == "row":
            parts = flatten(build_row(item[1], item[2], item[3]))
            parts[0].set("y", str(y))
            for part in parts:
                rebuilt.append(part)
        else:
            for clone in copy_rows(source, item[1], item[2], y):
                rebuilt.append(clone)
            y += ROW_H * (item[2] - item[1] + 1)
            continue
        y += ROW_H

    for element in children:
        source.remove(element)
    for element in list(rebuilt):
        rebuilt.remove(element)
        source.append(element)

    total_rows = (y - ROW_Y0) // ROW_H
    canvas_h = max(CANVAS_MIN_H, ROW_Y0 + total_rows * ROW_H + 20)
    root.set("width", f"{CANVAS_W}px")
    root.set("height", f"{canvas_h}px")
    rect = root.find(f"{Q}rect")
    if rect is not None:
        rect.set("height", f"{canvas_h}px")

    tree.write(path, encoding="utf-8", xml_declaration=True)
    return total_rows


def esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_readme(path: Path, profile: dict) -> None:
    """Keep README.md a clean picture container (per AGENTS.md) linked to the portfolio.

    Generated rather than hand-edited so the destination URL cannot drift from the
    canonical profile.
    """
    person = profile.get("person") or {}
    owner = "vuuminhphuoc"
    github = text(person.get("github_url"))
    if github.startswith("https://github.com/"):
        owner = github.rstrip("/").split("/")[3] or owner
    destination = text(person.get("portfolio_url")) or f"https://github.com/{owner}"
    base = f"https://raw.githubusercontent.com/{owner}/{owner}/main"

    alt_bits = [
        text(person.get("name")),
        text(person.get("role")),
        text(person.get("experience_label")),
        text(person.get("location")),
    ]
    alt = " \u00b7 ".join(bit for bit in alt_bits if bit)
    alt = f"{alt}. Terminal-style GitHub profile card." if alt else "GitHub profile card."

    path.write_text(
        f'<a href="{esc(destination)}">\n'
        "  <picture>\n"
        f'    <source media="(prefers-color-scheme: dark)" srcset="{base}/dark_mode.svg">\n'
        f'    <img alt="{esc(alt)}" src="{base}/light_mode.svg">\n'
        "  </picture>\n"
        "</a>\n",
        encoding="utf-8",
    )


def main(argv: list | None = None) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--profile",
        default=str(here / "profile.json"),
        help="path to the canonical public profile snapshot (default: profile.json beside this script)",
    )
    parser.add_argument(
        "--svg-dir",
        default=str(here),
        help="directory holding light_mode.svg and dark_mode.svg (default: script directory)",
    )
    args = parser.parse_args(argv)

    profile = load_profile(Path(args.profile).expanduser())
    plan = profile_rows(profile)
    svg_dir = Path(args.svg_dir).expanduser()

    for name in ("light_mode.svg", "dark_mode.svg"):
        target = svg_dir / name
        if not target.is_file():
            raise SystemExit(f"render_profile: missing {target}")
        rows = render_file(target, plan)
        print(f"render_profile: {name} updated ({rows} rows)")

    render_readme(svg_dir / "README.md", profile)
    print("render_profile: README.md updated (picture container linked to the portfolio)")

    print(f"render_profile: profile={Path(args.profile).as_posix()} source=offline json (no network)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())