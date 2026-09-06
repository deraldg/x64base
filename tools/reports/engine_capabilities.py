#!/usr/bin/env python3
"""Engine capability authority -- generated FROM kRegressionSpecs.

WHY THIS EXISTS. The site's freshness contracts compare EXACT VALUES: a page
says 245 keys, the authority says 245 keys, they agree or the build stops.
That discipline is sound and it is blind to the failure that actually happened
on 2026-09-05, when five pages said x64base had no JOIN and no NULL. Nothing
disagreed with a number. The pages disagreed with the ENGINE, and no contract
had the engine's capabilities to compare against.

So this emits them. The authority is `kRegressionSpecs` in cmd_regression.cpp
-- the same table `regression_index.py` parses, and the strongest capability
statement the tree makes, because a spec in the default suite is a claim the
engine re-proves on every REGRESSION ALL.

WHAT IS HAND-MAINTAINED AND WHY THAT IS THE RISK. CAPABILITIES below is written
by a person: a spec name cannot know which English words a documentation page
would use to deny it. That map is the part that rots. Two guards:

  1. Every spec named here must exist in the registry. A rename in the engine
     fails this generator LOUDLY rather than silently emitting a capability
     with no evidence behind it.
  2. `state` is DERIVED, never declared. Nobody can hand-promote a capability
     to default-suite; only the registry's own flag does that.

The token lists are deliberately SHORT. The consumer flags a negation near a
token, so a broad token set produces noise, and an advisory nobody reads decays
-- coordination/OPEN_ITEMS.md measures 33% compliance for ungated obligations
against 83-94% for gated ones. Prefer missing a page to crying wolf on twenty.

Usage (from D:\\code\\ccode):
    python tools/reports/engine_capabilities.py --out <path-to-site>/scripts/engine-capabilities-v1.json
    python tools/reports/engine_capabilities.py --print
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from regression_index import parse_specs  # noqa: E402

SCHEMA_VERSION = 1

# NO NEGATION LIST LIVES HERE. It used to, and it was wrong twice over.
#
# First, the denial GRAMMAR is the consumer's business -- a flat word list
# cannot express "this word denies when it comes BEFORE the capability but not
# after", which is the rule that took the false-positive count from 34 to 2.
# Two lists that must agree are one list that will not.
#
# Second, and this is the owner's ruling of 2026-09-06: the website is alpha
# prose about alpha and beta components, and "planned", "almost done" and
# "in dev" are HONEST THINGS TO SAY. An early draft of this file listed
# "planned", "future", "someday" and "roadmap" as negations, which would have
# turned the project's own accurate maturity vocabulary into a standing
# advisory. The sweep polices assertions of ABSENCE, not statements of
# maturity. See check-capability-contradictions.mjs for the grammar.

# id -> (title, spec names, tokens a page would use)
# TOKENS ARE MATCHED CASE-INSENSITIVELY AS WHOLE PHRASES.
CAPABILITIES = [
    ("sql.join.inner", "SQL INNER JOIN",
     ["SQLSEL_INNER_JOIN", "SQLSEL_JOIN_EDGES"],
     # BARE "join" earns its place: the 2026-09-05 pages said "no `JOIN` or
     # `GROUP BY` yet", and a token list without it missed the exact sentence
     # this whole mechanism exists for. It is only safe because the denial has
     # to GOVERN the token -- affirmative prose like "both surfaces now join"
     # and "relations drive navigation and joins" carries no denial in window.
     ["join", "inner join", "sql join", "join support"]),
    ("sql.join.outer", "SQL outer joins (LEFT / RIGHT / FULL)",
     ["SQLSEL_LEFT_JOIN", "SQLSEL_JOIN_FAMILY"],
     ["left join", "right join", "full join", "outer join"]),
    ("sql.join.cross", "SQL CROSS JOIN",
     ["SQLSEL_JOIN_FAMILY"],
     ["cross join", "cartesian product"]),
    ("sql.join.advanced", "Self-joins, composite ON, multi-table chains",
     ["SQLSEL_ADVANCED_JOIN"],
     ["self-join", "self join", "three-table join", "composite on"]),
    ("sql.group_by", "GROUP BY / HAVING with aggregates",
     ["SQLSEL_AGGREGATES"],
     ["group by", "having clause", "aggregate function"]),
    ("sql.subquery", "Correlated and uncorrelated subqueries",
     ["SQLSEL_SUBQUERIES"],
     ["subquery", "subqueries", "correlated subquery"]),
    ("sql.set_ops", "SELECT DISTINCT and the set operations",
     ["SQLSEL_SET_OPS"],
     ["union all", "intersect", "except clause", "select distinct"]),
    ("sql.dml", "Typed INSERT / UPDATE / DELETE with WAL-backed transactions",
     ["SQLSEL_DML"],
     ["sql dml", "sql insert", "sql update", "sql delete"]),
    # NOTE the absence of a bare "sqlsel" token. It was there for one run and
    # produced four false positives in a row -- "without the `SQLSEL` prefix"
    # denies the BARE SELECT ALIAS, and "there is also no server -- SQLsel runs
    # in-process" denies a SERVER. A product name that appears in every
    # sentence about the product cannot carry a negation test.
    ("sql.select", "The SQLsel statement surface",
     ["SQLSEL_SELECT_V1", "SQLSEL_BUFFER_VIS", "EVALDIFF"],
     ["sql select", "set-oriented select", "relational select"]),
    ("store.null", "Stored NULL on VFP-flavor tables (_NullFlags)",
     ["NULLASSERT"],
     # BARE "null" for the same reason: the page said "x64base has no NULL".
     # SQL syntax (NOT NULL / IS NULL / NOT EXISTS) is masked by the consumer
     # before any denial is looked for, which is what makes this survivable.
     ["null", "stored null", "null value", "_nullflags", "isnull"]),
    ("workspace.multi", "Several workspaces resident at once, each owning its paths",
     ["WSMULTI", "WSENV", "RELSCOPE2", "WORKSPACE_SCOPE"],
     ["multiple workspaces", "simultaneous workspaces", "workspace scope"]),
    ("workspace.memo", "Workspaces and whole mini-databases carried in a memo",
     ["WORKSPACE_MEMO", "WORKSPACE_MINIDB", "WORKSPACE_WRITEBACK"],
     ["memo-resident", "workspace in a memo", "mini-database"]),
    ("index.cnx_on_x64", "CNX explicitly attached to an x64 table",
     ["INDEX_X64_CNX"],
     ["cross-generation index", "cnx on x64"]),
    ("ram.vdisk", "Whole tables and their indexes resident in RAM",
     ["MEM", "WORKSPACE_RAM"],
     ["ram disk", "in-memory table", "virtual disk"]),
]


def build(root: Path) -> dict:
    specs = parse_specs(root)
    by_name = {s["name"]: s for s in specs}

    unknown: list[str] = []
    out = []
    for cap_id, title, spec_names, tokens in CAPABILITIES:
        missing = [n for n in spec_names if n not in by_name]
        if missing:
            unknown.append(f"{cap_id}: {', '.join(missing)}")
            continue
        defaults = [n for n in spec_names if by_name[n]["default"]]
        state = "default-suite" if defaults else "explicit-run"
        out.append({
            "id": cap_id,
            "title": title,
            "state": state,
            # default-suite is re-proven every REGRESSION ALL, so a page that
            # denies it is simply wrong; explicit-run is proven but unsoaked,
            # so a page denying it may be describing the soak honestly.
            "severity": "flag" if state == "default-suite" else "review",
            "specs": spec_names,
            "default_specs": defaults,
            "tokens": tokens,
        })

    if unknown:
        raise SystemExit(
            "engine_capabilities: spec name(s) in CAPABILITIES are not in the "
            "registry -- the map has drifted from the engine and must be "
            "corrected before this authority can be trusted:\n  "
            + "\n  ".join(unknown)
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tools/reports/engine_capabilities.py",
        "generated_from": "src/cli/cmd_regression.cpp (kRegressionSpecs)",
        "spec_totals": {
            "registered": len(specs),
            "default_suite": sum(1 for s in specs if s["default"]),
        },
        "capabilities": out,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--out", type=Path, default=None,
                    help="write the JSON here (usually the site's scripts/ dir)")
    ap.add_argument("--print", action="store_true", dest="do_print")
    args = ap.parse_args(argv)

    doc = build(args.root.resolve())
    text = json.dumps(doc, indent=2) + "\n"

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        flagged = sum(1 for c in doc["capabilities"] if c["severity"] == "flag")
        print(f"engine_capabilities -> {args.out} "
              f"({len(doc['capabilities'])} capabilities, {flagged} flag / "
              f"{len(doc['capabilities']) - flagged} review; "
              f"{doc['spec_totals']['default_suite']} of "
              f"{doc['spec_totals']['registered']} specs in the default suite)")
    if args.do_print or not args.out:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
