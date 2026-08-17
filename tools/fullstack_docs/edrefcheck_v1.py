#!/usr/bin/env python3
"""edrefcheck_v1 -- structural guard for the EDREF teaching catalog.

WHY THIS EXISTS
    EDREF gained kind/level/sequence/prereq/script_ref on 2026-08-15, BEFORE
    population, so the shape could be fixed while the catalog was still 29
    entries instead of 200. Fields nobody checks rot into decoration: a
    `script_ref` naming a script that does not exist is worse than no
    `script_ref`, because it claims the example runs.

    Companion to refcheck_v1.py, which guards the `*ref` command catalogs.
    This one guards the EDUCATIONAL catalog, whose failure mode is different:
    refcheck asks "does this command exist"; this asks "does this teaching
    material hold together as a course".

WHAT IT REFUSES TO DO
    It does not grade prose. Whether a summary teaches well is a human
    judgement and this tool will not pretend otherwise. It checks only what is
    mechanically knowable.

THE LESSON IT ENCODES (2026-08-15)
    refcheck_v1.catalog_names() returns [] for a MISSING file and [] for an
    EMPTY one. include/devref.hpp is empty, is named in the Tier 1 seed as a
    reference authority, declares `status: supported`, and no check has ever
    complained -- because zero findings and zero content look identical.

    So this tool reports the three states separately and treats an empty
    catalog as a FINDING, not a pass. A check that cannot fail is not a check.

Exit codes:
  0  no findings
  1  findings reported
  2  usage or environment error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The trailing comma is OPTIONAL, and that is not a detail.
#
# The first version of this pattern required `},` and therefore silently
# dropped the LAST entry in the catalog, which has no trailing comma. It
# reported 28 of 29 and passed. A guard that quietly miscounts is worse than
# no guard: it produces a number people then trust. Caught 2026-08-15 only
# because the count was compared against one taken a different way.
ENTRY_RE = re.compile(
    r'\{\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*R"\((.*?)\)"\s*,\s*(true|false)(.*?)\}\s*,?',
    re.S,
)
FIELD_RE = re.compile(r'\.(\w+)\s*=\s*([^,}]+)')

KINDS = {"Concept", "Example", "Exercise", "StudyGuide", "Assessment", "Glossary"}
LEVELS = {"Both", "Ap", "College"}


def repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".git").exists() and (p / "AI_README.md").exists():
            return p
    return start


def parse_catalog(path: Path):
    """Return (state, entries). state is 'absent' | 'empty' | 'populated'."""
    if not path.is_file():
        return "absent", []
    text = path.read_text(encoding="utf-8", errors="replace")
    if "catalog()" not in text:
        return "empty", []
    body = text.split("catalog()", 1)[-1]
    entries = []
    for m in ENTRY_RE.finditer(body):
        topic, syntax, summary, supported, tail = m.groups()
        fields = {k: v.strip() for k, v in FIELD_RE.findall(tail or "")}
        # `title` is the FIFTH POSITIONAL field, not a designated one, so it
        # appears in the tail as: ,\n "one sentence"
        # C++20 forbids mixing designated and positional initialisers in one
        # braced list, which is why it sits before the designated block and has
        # to be parsed positionally here.
        tm = re.match(r'\s*,\s*"((?:[^"\\]|\\.)*)"', tail or "")
        entries.append(
            {
                "topic": topic.strip(),
                "syntax": syntax.strip(),
                "summary": summary,
                "supported": supported == "true",
                "title": tm.group(1) if tm else "",
                "kind": fields.get("kind", "Kind::Concept").split("::")[-1],
                "level": fields.get("level", "Level::Both").split("::")[-1],
                "sequence": fields.get("sequence", "0"),
                "prereq": fields.get("prereq", '""').strip('"'),
                "script_ref": fields.get("script_ref", '""').strip('"'),
                "lab_ref": fields.get("lab_ref", '""').strip('"'),
            }
        )
    return ("populated" if entries else "empty"), entries


def check(root: Path) -> list[str]:
    findings: list[str] = []
    path = root / "include" / "edref.hpp"
    state, entries = parse_catalog(path)

    if state == "absent":
        return [f"include/edref.hpp does not exist"]
    if state == "empty":
        return [
            "include/edref.hpp parses to ZERO entries. An empty catalog and a "
            "healthy one are indistinguishable to a tool that only counts "
            "findings -- that is how include/devref.hpp stayed empty while "
            "being named in the Tier 1 seed as a supported authority."
        ]

    names = {e["topic"] for e in entries}

    # Enum values must be spelled correctly; the compiler catches this in C++,
    # but the catalog may also be read by tools that never compile it.
    for e in entries:
        if e["kind"] not in KINDS:
            findings.append(f"{e['topic']}: unknown kind {e['kind']!r}")
        if e["level"] not in LEVELS:
            findings.append(f"{e['topic']}: unknown level {e['level']!r}")

    # title is the compiled fallback's ENTIRE text, and it lands in
    # HELP_TOPIC.TITLE which is C80. Three ways it can be wrong, all checkable:
    # missing (the fallback says nothing), too long (silently truncated by the
    # DBF writer -- the exact failure SUMMARY already has, sitting at its C200
    # ceiling on all 29 rows), or an echo of the topic name, which is what TITLE
    # held before and is indistinguishable from having no summary at all.
    for e in entries:
        t = e.get("title", "").strip()
        if not t:
            findings.append(f"{e['topic']}: no title -- the compiled fallback would be empty")
        elif len(t) > 80:
            findings.append(
                f"{e['topic']}: title is {len(t)} chars; HELP_TOPIC.TITLE is C80 "
                "and would truncate it silently"
            )
        elif t.strip().upper() == e["topic"].strip().upper():
            findings.append(
                f"{e['topic']}: title merely echoes the topic name, which is the "
                "state this field exists to replace"
            )

    # script_ref must point at a file that exists. This is the whole point of
    # the field: an example that claims to run and does not is the defect.
    for e in entries:
        ref = e["script_ref"]
        if ref and not (root / ref).is_file():
            findings.append(f"{e['topic']}: script_ref not found: {ref}")

    # prereq must name topics that exist, or the syllabus DAG has dangling edges.
    for e in entries:
        for p in [x.strip() for x in e["prereq"].split(",") if x.strip()]:
            if p not in names:
                findings.append(f"{e['topic']}: prereq names unknown topic {p!r}")

    # A topic cannot be its own prerequisite.
    for e in entries:
        if e["topic"] in [x.strip() for x in e["prereq"].split(",")]:
            findings.append(f"{e['topic']}: lists itself as a prerequisite")

    # Duplicate sequence numbers make the reading order ambiguous. 0 means
    # "unplaced" and may repeat freely.
    seen: dict[str, str] = {}
    for e in entries:
        s = e["sequence"]
        if s == "0":
            continue
        if s in seen:
            findings.append(f"sequence {s} used by both {seen[s]} and {e['topic']}")
        seen[s] = e["topic"]

    if not any(e["topic"] == d for e in entries for d in [e["topic"]]):
        pass

    dupes = [n for n in names if [e["topic"] for e in entries].count(n) > 1]
    for n in sorted(set(dupes)):
        findings.append(f"duplicate topic: {n}")

    return findings


def summarise(root: Path) -> str:
    path = root / "include" / "edref.hpp"
    state, entries = parse_catalog(path)
    if state != "populated":
        return f"edrefcheck: catalog state = {state}"
    kinds: dict[str, int] = {}
    for e in entries:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    examples = [e for e in entries if e["kind"] == "Example"]
    no_script = [e for e in examples if not e["script_ref"]]
    unplaced = [e for e in entries if e["sequence"] == "0"]
    lines = [
        f"edrefcheck: {len(entries)} entries",
        "  by kind      : " + ", ".join(f"{k}={v}" for k, v in sorted(kinds.items())),
        f"  with title   : {sum(1 for e in entries if e.get('title','').strip())}"
        f"   (longest {max((len(e.get('title','')) for e in entries), default=0)} of 80)",
        f"  with script  : {sum(1 for e in entries if e['script_ref'])}",
        f"  with prereq  : {sum(1 for e in entries if e['prereq'])}",
        f"  unplaced     : {len(unplaced)} (sequence 0)",
    ]
    if no_script:
        lines.append(
            f"  ADVISORY: {len(no_script)} Example entr(ies) carry no script_ref -- "
            "an example nothing executes is the defect script_ref exists to prevent"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=None)
    ap.add_argument("--summary", action="store_true", help="print counts and exit 0")
    args = ap.parse_args(argv)

    root = Path(args.root) if args.root else repo_root(Path(__file__).resolve().parent)

    if args.summary:
        print(summarise(root))
        return 0

    findings = check(root)
    print(summarise(root))
    if findings:
        print()
        for f in findings:
            print(f"edrefcheck: FINDING: {f}", file=sys.stderr)
        print(f"edrefcheck: FAIL -- {len(findings)} finding(s)", file=sys.stderr)
        return 1
    print("edrefcheck: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
