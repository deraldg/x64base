#!/usr/bin/env python3
"""Recall: assemble a bounded working set from a trigger.

AIF-082, 6.3. The inverse of triage. Where consolidation compresses a session
down to a few durable records, recall expands a need back up into the smallest
set that restores competence (memory thesis, section 5.4).

The portal has 46 KB of doctrine in one linear document. Reading it is what the
127,704-byte entry-path measurement was measuring. This walks a typed graph from
"what am I about to do" and returns only the nodes on that path.

    python labtalk\\ai_portal\\recall.py                      # list triggers
    python labtalk\\ai_portal\\recall.py commit               # fuzzy match
    python labtalk\\ai_portal\\recall.py --demotable          # 6.6 decay report
    python labtalk\\ai_portal\\recall.py --validate           # graph integrity

THE DEMOTABLE REPORT is the point of the `enforced_by` edge. 6.6 says a rule
whose gate HARD-FAILS may demote out of the entry path, because the gate has
become the memory. That was a judgement call in prose; here it is a query.
Advisory and dormant gates are excluded by design -- 6.7 measured that an
unenforced obligation holds at 33 percent, so demoting behind a warning would
trade a read rule for no rule at all.

Exit codes: 0 ok, 1 registry unreadable, 2 validation failed, 3 no trigger match.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REGISTRY = Path("labtalk/registries/portal_recall_graph.yaml")
MAX_DEPTH = 2  # bounded traversal; recall assembles enough to begin, not everything

# NO HARDCODED DENOMINATOR. Both comparison figures are MEASURED at run time.
#
# AIF-090 D2, 2026-08-06. This module used to carry
# `ENTRY_PATH_BASELINE = 127704`, measured 2026-07-31 against the pre-Tier-0
# mandatory start path. Two problems, both found by a cold outside runner:
#
#   1. It is a perishable literal frozen in code, which is precisely what
#      AI_TIER1_SEED_V1.md's maintenance contract forbids ("If an agent can
#      cheaply measure it, say 'measure it'").
#   2. Tier 0 arrived and the entry path in force shrank to ~11 KB. So a 27,384 B
#      working set was 2.5x LARGER than the path it claimed to replace, and was
#      printed as "21%". The bound below, added specifically so this metric could
#      fail after the 217,471 B incident, was anchored to the stale constant and
#      therefore COULD NOT FIRE. Same file, same defect shape, second occurrence.
#
# The fix is not a fresher number; a fresher number goes stale too. The
# denominator is now DERIVED from the graph itself -- the corpus a reader would
# otherwise face is exactly the set of nodes this graph indexes -- so it tracks
# the graph automatically and there is nothing left to update by hand.


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / ".git").exists() and (c / "AI_README.md").exists():
            return c
    print("recall: cannot locate repository root", file=sys.stderr)
    raise SystemExit(1)


def load(root: Path) -> dict:
    """Minimal YAML reader for this file's shape.

    Deliberately dependency-free: the portal must be readable by an agent with
    nothing installed (6.10, the weakest admitted partner). PyYAML is not
    guaranteed present and this schema is small and flat.
    """
    path = root / REGISTRY
    if not path.is_file():
        print(f"recall: registry not found: {REGISTRY}", file=sys.stderr)
        raise SystemExit(1)

    triggers: list[dict] = []
    nodes: list[dict] = []
    edges: list[dict] = []
    entry_path: list[dict] = []
    # Section name -> bucket. Anything unrecognised falls through to `nodes`,
    # which is the pre-AIF-090 behaviour and keeps an unknown section from
    # silently vanishing.
    buckets = {"triggers": triggers, "nodes": nodes, "entry_path": entry_path}
    section = None
    current: dict | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[a-z_]+:", line):
            section = line.split(":", 1)[0]
            current = None
            continue
        stripped = line.strip()
        if section == "edges" and stripped.startswith("- {"):
            body = stripped[3:].rstrip("}")
            edge = {}
            for part in body.split(","):
                if ":" in part:
                    k, v = part.split(":", 1)
                    edge[k.strip()] = v.strip()
            edges.append(edge)
            continue
        if stripped.startswith("- "):
            current = {}
            buckets.get(section, nodes).append(current)
            stripped = stripped[2:]
        if current is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            v = v.strip().strip('"')
            current[k.strip()] = None if v == "null" else v
    return {"triggers": triggers, "nodes": nodes, "edges": edges,
            "entry_path": entry_path}


def corpus_size(root: Path, g: dict) -> tuple[int, int]:
    """Bytes of every DISTINCT node this graph indexes, measured now.

    This is the honest denominator for a working set: the alternative to a
    routed read is reading what the graph covers. Deduplicated by (path,
    anchor) because several nodes share AI_PORTAL.md and must not be counted
    twice -- the double-count is how the 217,471 B figure happened.
    """
    seen: set[tuple] = set()
    total = 0
    for n in g["nodes"]:
        key = (n.get("path"), n.get("anchor"))
        if key in seen:
            continue
        seen.add(key)
        total += section_size(root, n)
    return total, len(seen)


def entry_path_size(root: Path, g: dict) -> tuple[int, int]:
    """Bytes of the onboarding entry path currently in force, measured now.

    Membership is declared in the registry (`entry_path:`), not here, so the
    set is data and the size is measured. Reported as a SECOND figure, never as
    the headline: recall does not replace onboarding, it replaces reading the
    corpus after onboarding. Conflating the two is what made "21%" misleading.
    """
    total = 0
    n = 0
    for item in g.get("entry_path", []):
        p = root / item["path"] if item.get("path") else None
        if p and p.is_file():
            total += p.stat().st_size
            n += 1
    return total, n


def validate(g: dict) -> int:
    ids = {n["id"] for n in g["nodes"]} | {t["id"] for t in g["triggers"]}
    bad = []
    for e in g["edges"]:
        for end in ("from", "to"):
            if e.get(end) not in ids:
                bad.append(f"edge {e.get('from')} -> {e.get('to')}: unknown `{end}` {e.get(end)!r}")
    orphans = [
        n["id"] for n in g["nodes"]
        if not any(e.get("to") == n["id"] or e.get("from") == n["id"] for e in g["edges"])
    ]
    print(f"recall: {len(g['triggers'])} trigger(s), {len(g['nodes'])} node(s), {len(g['edges'])} edge(s)")
    for b in bad:
        print(f"  DANGLING  {b}")
    for o in orphans:
        print(f"  UNREACHABLE  {o}  -- no edge touches it; it cannot be recalled")
    if bad or orphans:
        print("")
        print("An unreachable node is the thesis 5.1 failure inside the recall graph")
        print("itself: stored, correct, and functionally absent.")
        return 2
    print("recall: PASS -- no dangling edges, every node reachable")
    return 0


def walk(g: dict, start: str) -> list[tuple[int, str, dict]]:
    by_id = {n["id"]: n for n in g["nodes"]}
    seen = {start}
    out: list[tuple[int, str, dict]] = []
    frontier = [(start, 0)]
    while frontier:
        nid, depth = frontier.pop(0)
        if depth >= MAX_DEPTH + 1:
            continue
        for e in g["edges"]:
            if e.get("from") != nid or e.get("to") in seen:
                continue
            tgt = e["to"]
            seen.add(tgt)
            if tgt in by_id:
                out.append((depth, e.get("type", "?"), by_id[tgt]))
                frontier.append((tgt, depth + 1))
    return out


def section_size(root: Path, node: dict) -> int:
    """Bytes an agent must actually read for this node.

    CORRECTED 2026-07-31T21:30Z. The first version summed whole FILE sizes, so a
    query touching six sections of AI_PORTAL.md counted that 48 KB file six
    times and reported a 217 KB "working set" -- larger than the 127,704-byte
    entry path the graph exists to replace. The headline metric of the tool
    proving this lane's thesis was itself unmeasured, and it was printed
    directly beneath the words "read these, not the corpus".

    An anchored node costs its SECTION: from the anchor to the next heading at
    the same level. Only an unanchored node costs its whole file. Nothing is
    counted twice, because sections do not overlap.

    CORRECTED AGAIN 2026-08-16 (AIF-118), same bug class as the 07-31 fix above:
    a confident number that was wrong. A `#` comment inside a FENCED CODE BLOCK
    matches `^#{1,2} ` and was being read as the next heading, so a section
    ending its first paragraph in a shell snippet was truncated there. Measured:
    `AI_README.md` "## Runtime Start Points" reported **64 B against an actual
    2943 B, a 46x under-report**, because line 2 of its first powershell block is
    `# From the repository root:`. Fenced blocks are now masked before the search.

    Blast radius when found: 1 of 20 anchored nodes, and it surfaced only because
    a node was added that pointed there. The bug was latent for as long as the
    function has existed -- nothing reported it, because an under-reported working
    set looks like a SMALL working set, which is exactly what this tool is
    supposed to produce. A metric whose failure mode is "looks like success" is
    the shape this repository keeps finding.
    """
    path = root / str(node.get("path", ""))
    if not path.is_file():
        return 0
    anchor = node.get("anchor")
    if not anchor:
        return path.stat().st_size

    text = path.read_text(encoding="utf-8", errors="replace")
    start = text.find(anchor)
    if start < 0:
        return path.stat().st_size

    body = text[start + len(anchor):]
    # Mask fenced blocks, preserving newline count so offsets into `body` stay
    # valid. Replacement must be the same LENGTH, not merely the same shape --
    # the match end is used as an index back into the unmasked body.
    masked = re.sub(
        r"^```.*?^```",
        lambda m: re.sub(r"[^\n]", " ", m.group(0)),
        body,
        flags=re.DOTALL | re.MULTILINE,
    )

    level = len(anchor) - len(anchor.lstrip("#"))
    if level:
        nxt = re.search(rf"^#{{1,{level}}} ", masked, flags=re.MULTILINE)
    else:
        nxt = re.search(r"^## ", masked, flags=re.MULTILINE)
    end = start + len(anchor) + (nxt.start() if nxt else len(body))
    return len(text[start:end].encode("utf-8"))


def demotable(g: dict) -> int:
    print("recall: 6.6 decay report -- which doctrine may demote out of the entry path")
    print("")
    yes, no = [], []
    for n in g["nodes"]:
        if n.get("tier") != "1":
            continue
        gate, hard = n.get("enforced_by"), str(n.get("hard_fails", "")).lower() == "true"
        (yes if (gate and hard) else no).append((n, gate, hard))
    print("MAY DEMOTE -- a hard-failing gate is now the memory:")
    for n, gate, _ in yes:
        print(f"  {n['id']}")
        print(f"      gate: {gate}")
    if not yes:
        print("  (none)")
    print("")
    print("MUST STAY on the entry path:")
    for n, gate, hard in no:
        why = "no mechanism at all" if not gate else "gate exists but does not hard-fail"
        print(f"  {n['id']}  -- {why}")
        if gate:
            print(f"      gate: {gate}")
    print("")
    print("6.7 measured the difference: obligations with gates held at 83-94 percent,")
    print("the one without held at 33. Demoting behind a warning trades a rule that is")
    print("read for a rule that is neither read nor enforced.")
    return 0


FALLBACK_DOC = "labtalk/ai_portal/RECALL_FALLBACK_TABLE_V1.md"

FALLBACK_HEADER = """<!-- GENERATED FROM labtalk/registries/portal_recall_graph.yaml -- DO NOT HAND-EDIT.
     Regenerate: python labtalk/ai_portal/recall.py --write-fallback
     Guarded by: labtalk/portal/tests/test_recall_fallback_sync.py -->

# Recall fallback -- retrieve by what you are about to do

**This is the Tier 2 landing place for the table demoted out of
`AI_TIER1_SEED_V1.md` on 2026-08-16 (AIF-118, executing AIF-115's proposal).**

Prefer the resolver: `python labtalk/ai_portal/recall.py <trigger>` returns the
smallest working set, measured, and can follow `requires` edges this flat table
cannot. Use this page only when you cannot run it.

It is GENERATED from the graph, so it cannot drift from the resolver. The seed's
maintenance contract says demoting means *moving*, not restating -- and AIF-082
6.8 records that two shims which restate each other will diverge, and have. A
hand-copied table here would have been exactly that shim.

| About to | Read |
| --- | --- |
"""


def fallback_markdown(root: Path, g: dict) -> str:
    """Render the trigger index as the flat table the seed used to carry."""
    nodes = {n["id"]: n for n in g["nodes"]}
    fires: dict[str, list[str]] = {}
    for e in g["edges"]:
        if e.get("type") == "fires_at":
            fires.setdefault(e["from"], []).append(e["to"])

    rows = []
    for t in g["triggers"]:
        targets = fires.get(t["id"], [])
        cells = []
        for nid in targets:
            n = nodes.get(nid)
            if not n:
                continue
            path = str(n.get("path", ""))
            label = str(n.get("label", "")).replace("|", "\\|")
            cells.append(f"{label} -- `{path}`")
        label = str(t.get("label", "")).replace("|", "\\|")
        rows.append(f"| {label} | {'<br>'.join(cells) or '(no nodes)'} |")
    return FALLBACK_HEADER + "\n".join(rows) + "\n"


def write_fallback(root: Path, g: dict) -> int:
    target = root / FALLBACK_DOC
    target.write_text(fallback_markdown(root, g), encoding="utf-8")
    print(f"recall: wrote {FALLBACK_DOC} ({target.stat().st_size} B, "
          f"{len(g['triggers'])} trigger(s))")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble a working set from a trigger.")
    ap.add_argument("query", nargs="?", help="what you are about to do")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--demotable", action="store_true")
    ap.add_argument("--write-fallback", action="store_true",
                    help="regenerate the Tier 2 fallback table from the graph")
    args = ap.parse_args()

    root = repo_root()
    g = load(root)

    if args.validate:
        return validate(g)
    if args.demotable:
        return demotable(g)
    if args.write_fallback:
        return write_fallback(root, g)

    if not args.query:
        print("recall: name what you are about to do. Triggers:")
        for t in g["triggers"]:
            print(f"  {t['id'].replace('trigger.', ''):<18} {t.get('label', '')}")
        return 0

    # Match on normalized text and token overlap. The first version compared the
    # raw query against `trigger.understand_why`, so the natural-language phrasing
    # the tool ASKS FOR ("understand why") missed the trigger named after it.
    # A retrieval tool that fails on the phrasing it invites is a retrieval
    # failure of its own kind.
    def norm(s: str) -> str:
        return re.sub(r"[^a-z0-9 ]+", " ", str(s).lower().replace("_", " ")).strip()

    q = norm(args.query)
    qt = set(q.split())

    scored = []
    for t in g["triggers"]:
        hay = f"{norm(t['id'])} {norm(t.get('label', ''))}"
        ht = set(hay.split())
        if q and q in hay:
            score = 100 + len(q)
        else:
            score = len(qt & ht) * 10
        if score:
            scored.append((score, t))

    if not scored:
        print(f"recall: no trigger matches {args.query!r}. Triggers:", file=sys.stderr)
        for t in g["triggers"]:
            print(f"  {t['id'].replace('trigger.', ''):<18} {t.get('label','')}", file=sys.stderr)
        return 3

    scored.sort(key=lambda r: -r[0])
    hits = [t for _, t in scored]
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        print(f"recall: ambiguous, using {hits[0]['id']}. Also matched: "
              + ", ".join(t["id"].replace("trigger.", "") for t in hits[1:4]))

    trig = hits[0]
    print(f"=== recall: {trig['id']} -- {trig.get('label', '')}")
    rows = walk(g, trig["id"])
    if not rows:
        print("  (nothing linked; that is a gap in the graph, not in the corpus)")
        return 0

    total = 0
    for depth, etype, n in rows:
        pad = "  " + "    " * depth
        anchor = f"   [{n['anchor']}]" if n.get("anchor") else ""
        print(f"{pad}{etype:<12} {n['path']}{anchor}")
        size = section_size(root, n)
        print(f"{pad}             {n.get('label','')}  "
              f"({n.get('class','?')}, tier {n.get('tier','?')}, {size} B)")
        total += size
    print("")
    corpus, corpus_n = corpus_size(root, g)
    entry, entry_n = entry_path_size(root, g)

    pct = round(100 * total / corpus) if corpus else 0
    print(f"working set: {len(rows)} node(s), {total} B to read "
          f"({pct}% of the {corpus} B corpus this graph indexes, {corpus_n} nodes).")
    if entry:
        ratio = total / entry
        note = "smaller" if ratio < 1 else f"{ratio:.1f}x LARGER"
        print(f"  for scale: the onboarding entry path in force is {entry} B "
              f"({entry_n} files); this working set is {note}.")
        print(f"  recall does NOT replace onboarding -- it replaces reading the "
              f"corpus afterwards.")

    # The bound that makes this metric able to fail, now anchored to something
    # that moves with the graph. An unbounded byte count is a claim nobody
    # checks -- which is how the first version published 217,471 B, six times
    # the truth, on the line above the words "read these, not the corpus"; and
    # how the second version compared against a frozen 127,704 B constant that
    # no longer gated anyone, so it could never fire (AIF-090 D2). See
    # AI_PORTAL.md, "Build It to Prove It".
    if corpus and total >= corpus:
        print("")
        print(f"  WARNING: this working set is not smaller than the corpus it")
        print(f"  replaces ({total} B vs {corpus} B). Either the graph is")
        print(f"  over-linking this trigger, or the metric is wrong again.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
