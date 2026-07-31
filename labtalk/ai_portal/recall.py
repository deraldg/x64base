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
            (triggers if section == "triggers" else nodes).append(current)
            stripped = stripped[2:]
        if current is not None and ":" in stripped:
            k, v = stripped.split(":", 1)
            v = v.strip().strip('"')
            current[k.strip()] = None if v == "null" else v
    return {"triggers": triggers, "nodes": nodes, "edges": edges}


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble a working set from a trigger.")
    ap.add_argument("query", nargs="?", help="what you are about to do")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--demotable", action="store_true")
    args = ap.parse_args()

    root = repo_root()
    g = load(root)

    if args.validate:
        return validate(g)
    if args.demotable:
        return demotable(g)

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
        print(f"{pad}             {n.get('label','')}  ({n.get('class','?')}, tier {n.get('tier','?')})")
        p = root / str(n["path"])
        if p.is_file():
            total += p.stat().st_size
    print("")
    print(f"working set: {len(rows)} node(s), {total} B of source. Read these, not the corpus.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
