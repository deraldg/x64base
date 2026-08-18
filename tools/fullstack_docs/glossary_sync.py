#!/usr/bin/env python3
"""glossary_sync.py -- make the coined vocabulary reachable without copying it.

`content/docs/dev/coined-vocabulary.mdx` tells a public reader that the maintained
glossary lives at `labtalk/ai_portal/AI_GLOSSARY_V1.md` in the source tree. That
file is not on the published branch, so the pointer does not resolve for the
audience it is written for -- a WIDOW in the house sense.

The page is also right to refuse a hand-kept copy ("a copied glossary is a stale
glossary"). Both constraints hold at once if the public index is DERIVED: a
generated projection cannot drift, because a gate re-derives and compares.

What it projects: the TERM INDEX -- name, one-line gloss, home pointer, grouped by
the glossary's own sections. Not the definitions. The glossary describes itself as
"a pointer index, not a corpus: each term gets one line and a home; definitions
live in the homes." Projecting the index is projecting what it is.

Modes, following `command_catalog_sync.py`:

  emit   Re-derive the index page from the glossary.
  check  Validate an existing page against the current glossary. Exit 2 on drift.
         This is the push-checklist gate.

Anchor contract: the maintained page carries the marker line below. `check` refuses
to validate a file without it, so it cannot be pointed at the wrong document.

Usage:
  python glossary_sync.py emit  --source-root D:/code/ccode \
      --out D:/dev/x64base-site/content/docs/dev/coined-vocabulary-index.mdx
  python glossary_sync.py check --source-root D:/code/ccode \
      --page D:/dev/x64base-site/content/docs/dev/coined-vocabulary-index.mdx
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
from pathlib import Path

GLOSSARY = "labtalk/ai_portal/AI_GLOSSARY_V1.md"
ANCHOR = "Derived index: GLOSSARY-INDEX-001"

TERM_RE = re.compile(
    r"^- \*\*(?P<term>[^*]+?)\.?\*\*"        # term, optional trailing period inside the bold
    r"(?P<qual>\s*\([^)]*\))?"                 # optional parenthetical qualifier
    r"\s*(?:--\s*)?"                            # dash separator is optional
    r"(?P<body>.*)$"
)
HOME_RE = re.compile(r"Home:\s*(?P<home>.+?)(?:\.\s*$|$)", re.IGNORECASE)


def parse(md: str):
    """Return [(section, term, gloss, home)] in document order."""
    out, section = [], "(unsectioned)"
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            section = line[3:].strip()
            i += 1
            continue
        m = TERM_RE.match(line)
        if not m:
            i += 1
            continue
        body = [m.group("body").strip()]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and not lines[i].lstrip().startswith("- "):
            body.append(lines[i].strip())
            i += 1
        full = " ".join(body)
        hm = HOME_RE.search(full)
        home = hm.group("home").strip() if hm else ""
        gloss = full[: hm.start()].strip() if hm else full
        # one line: first sentence, bounded
        gloss = re.split(r"(?<=[a-z0-9)\"'])\.\s+", gloss)[0].strip().rstrip(".")
        if len(gloss) > 220:
            gloss = gloss[:217].rsplit(" ", 1)[0] + "..."
        out.append((section, m.group("term").strip(), gloss, home))
    return out


def sha(root: Path) -> str:
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-C", str(root),
                            "log", "-1", "--format=%h", "--", GLOSSARY],
                           capture_output=True, text=True, timeout=60)
        return r.stdout.strip() or "unknown"
    except Exception as exc:
        print(f"  provenance unavailable ({type(exc).__name__})", file=sys.stderr)
        return "unknown"


def render(root: Path) -> str:
    src = (root / GLOSSARY)
    raw = src.read_text(encoding="utf-8", errors="replace")
    entries = parse(raw)
    bullets = [l for l in raw.splitlines() if l.startswith("- **")]
    if len(entries) != len(bullets):
        got = {t for _, t, _, _ in entries}
        lost = [l[:90] for l in bullets if not any(g in l for g in got)]
        raise SystemExit(
            f"REFUSING TO EMIT: parsed {len(entries)} of {len(bullets)} glossary bullets. "
            f"A projection that silently drops terms is worse than no projection.\n  "
            + "\n  ".join(lost))
    homed = sum(1 for e in entries if e[3])
    L = []
    L.append("---")
    L.append('title: "Coined Vocabulary -- Term Index"')
    L.append('description: "Generated index of the house coined vocabulary: every term, '
             'its one-line gloss, and where its definition lives. Derived from the '
             'maintained glossary in the source tree."')
    L.append("---")
    L.append("")
    L.append(f"{ANCHOR}")
    L.append("")
    L.append("**GENERATED. Do not edit by hand.** This page is a derived projection of")
    L.append(f"`{GLOSSARY}` in the source tree. Hand edits are overwritten and fail the")
    L.append("drift gate. Regenerate with `tools/fullstack_docs/glossary_sync.py emit`.")
    L.append("")
    L.append("It exists so the vocabulary is *reachable* from the published site. The")
    L.append("companion page [Coined Vocabulary (Glossary)](/docs/dev/coined-vocabulary)")
    L.append("explains why the glossary is doctrine; this page is the index itself.")
    L.append("")
    L.append("Definitions are NOT reproduced here. Each term names a home, and the home")
    L.append("holds the definition -- the glossary is a pointer index, and so is this.")
    L.append("")
    L.append(f"Source extraction snapshot: {len(entries)} terms, {homed} with a home, "
             f"from `{GLOSSARY}` at commit `{sha(root)}`.")
    L.append("")
    cur = None
    for section, term, gloss, home in entries:
        if section != cur:
            cur = section
            L.append(f"## {section}")
            L.append("")
            L.append("| Term | Gloss | Home |")
            L.append("| --- | --- | --- |")
        h = home.replace("|", "\\|") if home else "_(in this glossary)_"
        g = gloss.replace("|", "\\|")
        L.append(f"| **{term}** | {g} | {h} |")
        nxt = None
        L.append("") if False else None
    L.append("")
    return "\n".join(L) + "\n"


def strip_volatile(s: str) -> str:
    return "\n".join(l for l in s.splitlines()
                     if not l.startswith("Source extraction snapshot:"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("emit");  e.add_argument("--source-root", type=Path, required=True); e.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("check"); c.add_argument("--source-root", type=Path, required=True); c.add_argument("--page", type=Path, required=True)
    a = ap.parse_args()

    body = render(a.source_root)

    if a.cmd == "emit":
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(body, encoding="utf-8", newline="\n")
        n = len(parse((a.source_root / GLOSSARY).read_text(encoding="utf-8", errors="replace")))
        print(f"  wrote {a.out}  {len(body.encode())} B  {n} terms")
        return 0

    if not a.page.is_file():
        print(f"  FAIL: {a.page} does not exist. Run emit.", file=sys.stderr)
        return 2
    cur = a.page.read_text(encoding="utf-8", errors="replace")
    if ANCHOR not in cur:
        print(f"  FAIL: anchor '{ANCHOR}' not found -- refusing to validate the wrong file.",
              file=sys.stderr)
        return 2
    if strip_volatile(cur) == strip_volatile(body):
        print("  glossary-index: PASS -- page matches the maintained glossary")
        return 0
    print("  glossary-index: FAIL -- page has drifted from the glossary. "
          "Regenerate with `glossary_sync.py emit`.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
