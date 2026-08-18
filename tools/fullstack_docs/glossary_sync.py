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
import csv
import re
import subprocess
import sys
from pathlib import Path

GLOSSARY = "labtalk/ai_portal/AI_GLOSSARY_V1.md"
TERMS_CSV  = "docs/glossary/glossary_master_v0.csv"
ALIAS_CSV  = "docs/glossary/alias_map_v0.csv"
LEGACY_CSV = "docs/glossary/legacy_terms_v0.csv"
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


def rows(root: Path, rel: str):
    p = root / rel
    if not p.is_file():
        print(f"  NOTE: {rel} absent -- its section is omitted", file=sys.stderr)
        return []
    with open(p, newline="", encoding="utf-8", errors="replace") as fh:
        return [r for r in csv.DictReader(fh) if any((v or "").strip() for v in r.values())]


def cell(r, k):
    return (r.get(k) or "").strip().replace("|", "\\|")


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
    L.append('title: "Vocabulary Index"')
    L.append('description: "Generated index of the project vocabulary: coined house terms with '
             'their homes, product terminology with per-audience notes, aliases, and legacy '
             'wording. Derived from the maintained sources in the source tree."')
    L.append("---")
    L.append("")
    L.append(f"{ANCHOR}")
    L.append("")
    L.append("**GENERATED. Do not edit by hand.** This page is a derived projection of the")
    L.append("maintained vocabulary sources in the source tree. Hand edits are overwritten")
    L.append("and fail the drift gate. Regenerate with")
    L.append("`tools/fullstack_docs/glossary_sync.py emit`.")
    L.append("")
    L.append("It exists so the vocabulary is *reachable* from the published site. The")
    L.append("companion page [Coined Vocabulary (Glossary)](/docs/dev/coined-vocabulary)")
    L.append("explains why the glossary is doctrine; this page is the index itself.")
    L.append("")
    L.append("**Two instruments, projected together.** The coined vocabulary")
    L.append(f"(`{GLOSSARY}`) records terms the house MINTED -- doctrine, named by")
    L.append("this project for its own practice. The product terminology, aliases and legacy")
    L.append("tables (`docs/glossary/`) are a reader's dictionary -- what a word MEANS, what")
    L.append("to say instead, and what has been retired. They are maintained separately and")
    L.append("do not overlap; both are indexed here so one page answers \"what does this")
    L.append("word mean here?\"")
    L.append("")
    L.append("Definitions are NOT reproduced from the coined glossary. Each coined term names")
    L.append("a home, and the home holds the definition -- it is a pointer index, and so is")
    L.append("this.")
    L.append("")
    n_t, n_a, n_l = len(rows(root, TERMS_CSV)), len(rows(root, ALIAS_CSV)), len(rows(root, LEGACY_CSV))
    L.append(f"Source extraction snapshot: {len(entries)} coined terms ({homed} with a home), "
             f"{n_t} product terms, {n_a} aliases, {n_l} legacy terms; "
             f"from `{GLOSSARY}` and `docs/glossary/` at commit `{sha(root)}`.")
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

    coined = {term.lower() for _, term, _, _ in entries}

    terms = rows(root, TERMS_CSV)
    if terms:
        L.append("")
        L.append("## Product terminology (reader dictionary)")
        L.append("")
        L.append("A different instrument from the coined vocabulary above: what a word MEANS")
        L.append("for a reader, with notes per audience. Maintained as")
        L.append(f"`{TERMS_CSV}`.")
        L.append("")
        L.append("| Term | Definition | Student | User | Developer |")
        L.append("| --- | --- | --- | --- | --- |")
        for r in terms:
            L.append(f"| **{cell(r,'canonical_term')}** | {cell(r,'short_definition')} | "
                     f"{cell(r,'student_note')} | {cell(r,'user_note')} | {cell(r,'developer_note')} |")
        dup = sorted(cell(r, "canonical_term") for r in terms
                     if cell(r, "canonical_term").lower() in coined)
        if dup:
            L.append("")
            L.append(f"**Also coined:** {', '.join('`' + d + '`' for d in dup)} appear in the")
            L.append("coined vocabulary above as well. Two maintained sources, one term -- the")
            L.append("coined entry governs house practice, this entry governs reader-facing prose.")

    al = rows(root, ALIAS_CSV)
    if al:
        L.append("")
        L.append("## Aliases -- say this, not that")
        L.append("")
        L.append(f"Maintained as `{ALIAS_CSV}`.")
        L.append("")
        L.append("| If you say | Use | Status | Note |")
        L.append("| --- | --- | --- | --- |")
        for r in al:
            L.append(f"| {cell(r,'alias')} | **{cell(r,'canonical_term')}** | "
                     f"{cell(r,'term_status')} | {cell(r,'notes')} |")

    lg = rows(root, LEGACY_CSV)
    if lg:
        L.append("")
        L.append("## Legacy and watch terms")
        L.append("")
        L.append(f"Retired or historical wording. Maintained as `{LEGACY_CSV}`.")
        L.append("")
        L.append("| Legacy term | Prefer | Status | Note |")
        L.append("| --- | --- | --- | --- |")
        for r in lg:
            L.append(f"| {cell(r,'legacy_term')} | **{cell(r,'preferred_term')}** | "
                     f"{cell(r,'status')} | {cell(r,'notes')} |")

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
