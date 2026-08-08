#!/usr/bin/env python3
"""Regression index -- wired FROM the engine's own curated registry.

The authoritative list of regression tests is the `kRegressionSpecs` table in
`src/cli/cmd_regression.cpp` -- the REGRESSION command's LIST/ALL surface. This module
PARSES that table so the website and the local /AI report show exactly what the engine
runs, instead of a hand-kept copy that drifts. The runtime `.dts` scripts live under
`dottalkpp/data/scripts/`; the tracked Python `test_*.py` are listed as a second group.

Design note: the registry source (`cmd_regression.cpp`) is tracked, so it is always
linkable; individual `.dts` targets are runtime data and mostly untracked, so a link is
emitted only when the file is actually in git -- otherwise the path is shown plainly and
tagged 'runtime', which is honest rather than a 404.

Usage (from D:\\code\\ccode):
    python tools/reports/regression_index.py --md            # Markdown fragment (site)
    python tools/reports/regression_index.py --html          # HTML fragment (local report)
    python tools/reports/regression_index.py --md --sha <c>  # pin GitHub links to a commit
"""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

REG_CPP = "src/cli/cmd_regression.cpp"
SCRIPT_ROOT = "dottalkpp/data/scripts"
GH = "https://github.com/deraldg/x64base/blob"

# Each entry: { "NAME", "script\\path.dts", "summary", true|false }. The char class
# handles escaped quotes and the doubled backslashes in Windows-style script paths.
_STR = r'"((?:[^"\\]|\\.)*)"'
SPEC_RE = re.compile(
    r"\{\s*" + _STR + r"\s*,\s*" + _STR + r"\s*,\s*" + _STR + r"\s*,\s*(true|false)\s*\}",
    re.DOTALL,
)


def _unescape(s: str) -> str:
    return s.replace('\\\\', '\\').replace('\\"', '"')


def parse_specs(root: Path) -> list[dict]:
    """Parse kRegressionSpecs from cmd_regression.cpp into ordered dicts."""
    text = (root / REG_CPP).read_text(encoding="utf-8", errors="replace")
    block = re.search(r"kRegressionSpecs\{\{(.*?)\}\};", text, re.DOTALL)
    body = block.group(1) if block else text
    specs: list[dict] = []
    for name, script, summary, default in SPEC_RE.findall(body):
        rel = _unescape(script).replace('\\', '/')
        cat = rel.split('/', 1)[0] if '/' in rel else "core"
        specs.append({
            "name": _unescape(name),
            "rel": rel,                                   # under dottalkpp/data/scripts
            "path": f"{SCRIPT_ROOT}/{rel}",
            "summary": _unescape(summary),
            "default": default == "true",
            "category": cat,                              # domain, from the script folder
        })
    return specs


def by_category(specs: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group specs by domain category, categories alphabetical, defaults first within."""
    cats: dict[str, list[dict]] = {}
    for s in specs:
        cats.setdefault(s["category"], []).append(s)
    for items in cats.values():
        items.sort(key=lambda s: (not s["default"], s["name"]))
    return sorted(cats.items())


def _git_lines(root: Path, *args: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True, stderr=subprocess.DEVNULL, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def tracked_set(root: Path) -> set[str]:
    return set(_git_lines(root, "--no-optional-locks", "ls-files"))


def python_tests(tracked: set[str]) -> list[str]:
    return sorted(p for p in tracked
                  if p.endswith(".py") and Path(p).name.startswith("test_"))


# ---------------------------------------------------------------- renderers

def _blob(sha: str, path: str) -> str:
    return f"{GH}/{sha}/{path}"


def _mdx(s: str) -> str:
    """Escape the characters MDX parses as JSX/HTML, so a summary containing `{`,
    `<`, or `>` (e.g. '{}/$a[n]', '16-bit') does not break the site build."""
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace("{", "&#123;").replace("}", "&#125;"))


def render_markdown(root: Path, sha: str) -> str:
    specs = parse_specs(root)
    tracked = tracked_set(root)
    tests = python_tests(tracked)
    grouped = by_category(specs)
    default_n = sum(1 for s in specs if s["default"])

    def row(s: dict) -> str:
        if s["path"] in tracked:
            link = f"[`{s['rel']}`]({_blob(sha, s['path'])})"
        else:
            link = f"`{s['rel']}` _(runtime script -- not in the public tree)_"
        tag = "default" if s["default"] else "explicit"
        return f"- **{_mdx(s['name'])}** `[{tag}]` -- {_mdx(s['summary'])}<br/>{link}"

    out: list[str] = []
    out.append(
        "The list below is generated from the engine's own registry -- the "
        f"`kRegressionSpecs` table in [`src/cli/cmd_regression.cpp`]({_blob(sha, REG_CPP)}), "
        f"the same set `REGRESSION LIST` / `REGRESSION ALL` drive ({len(specs)} entries, "
        f"{default_n} in the default suite), grouped by domain. It cannot drift from what "
        "the engine runs, because it is parsed from that source. Regenerate with "
        "`python tools/reports/regression_index.py --md`.")
    out.append("")
    for cat, items in grouped:
        d = sum(1 for s in items if s["default"])
        out.append(f"<details>\n<summary><strong>{_mdx(cat)}</strong> "
                   f"({len(items)}; {d} default)</summary>\n")
        out.extend(row(s) for s in items)
        out.append("\n</details>")
        out.append("")
    out.append(f"<details>\n<summary><strong>Python test scripts</strong> "
               f"({len(tests)}; tracked, CI-style)</summary>\n")
    out.extend(f"- [`{t}`]({_blob(sha, t)})" for t in tests)
    out.append("\n</details>")
    out.append("")
    return "\n".join(out)


def render_html(root: Path, sha: str, *, script_href) -> str:
    """HTML fragment for the local /AI report. `script_href(rel)` builds the link a
    .dts should point at (the local server serves them from disk, so untracked scripts
    still resolve locally)."""
    specs = parse_specs(root)
    tracked = tracked_set(root)
    tests = python_tests(tracked)
    grouped = by_category(specs)

    def li(s: dict) -> str:
        badge = ('<span style="color:#16a34a">default</span>' if s["default"]
                 else '<span style="color:#a16207">explicit</span>')
        return (f'<li><a href="{html.escape(script_href(s["rel"]))}"><code>'
                f'{html.escape(s["rel"])}</code></a> [{badge}] &mdash; '
                f'{html.escape(s["summary"])}</li>')

    def block(title: str, sub: str, inner: str) -> str:
        return (f'<details><summary><strong>{html.escape(title)}</strong> '
                f'{html.escape(sub)}</summary><ul>{inner}</ul></details>')

    parts = ['<section style="margin-top:1.5rem">', '<h2>Regression tests</h2>',
             f'<p>Generated from the engine registry '
             f'<a href="{_blob(sha, REG_CPP)}"><code>cmd_regression.cpp</code></a> '
             '(<code>REGRESSION LIST/ALL</code>), grouped by domain; links open the '
             'real script.</p>']
    for cat, items in grouped:
        d = sum(1 for s in items if s["default"])
        parts.append(block(cat, f"({len(items)}; {d} default)",
                           "".join(li(s) for s in items)))
    parts.append(block("Python test scripts", f"({len(tests)}; tracked)",
                       "".join(f'<li><a href="{_blob(sha, t)}"><code>'
                               f'{html.escape(t)}</code></a></li>' for t in tests)))
    parts.append('</section>')
    return "".join(parts)


# Auto-generation into a maintained MDX page: the generated list lives between these
# MDX-comment markers so the page can be regenerated (never hand-edited) and cannot drift.
MDX_BEGIN = "{/* regression-index:begin -- generated by tools/reports/regression_index.py; do not edit between markers */}"
MDX_END = "{/* regression-index:end */}"


def write_mdx(root: Path, sha: str, target: Path) -> str:
    frag = render_markdown(root, sha)
    block = f"{MDX_BEGIN}\n\n{frag}\n{MDX_END}"
    text = target.read_text(encoding="utf-8")
    if MDX_BEGIN in text and MDX_END in text:
        pre = text[: text.index(MDX_BEGIN)]
        post = text[text.index(MDX_END) + len(MDX_END):]
        new = pre + block + post
        action = "replaced generated block"
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
        action = "appended generated block (markers not found)"
    target.write_text(new, encoding="utf-8", newline="\n")
    return action


def _default_sha(root: Path) -> str:
    got = _git_lines(root, "--no-optional-locks", "rev-parse", "HEAD")
    return got[0] if got else "development"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--sha", default=None, help="commit to pin GitHub links to")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--html", action="store_true")
    ap.add_argument("--write-mdx", metavar="PATH", default=None,
                    help="regenerate the marked block inside an MDX page (auto-generate)")
    a = ap.parse_args(argv)
    root = Path(a.root).resolve()
    sha = a.sha or _default_sha(root)
    if a.write_mdx:
        action = write_mdx(root, sha, Path(a.write_mdx))
        print(f"regression_index: {action} in {a.write_mdx}  (pinned {sha[:9]})")
    elif a.html:
        print(render_html(root, sha, script_href=lambda rel: f"/AI/script/{rel}"))
    else:
        print(render_markdown(root, sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
