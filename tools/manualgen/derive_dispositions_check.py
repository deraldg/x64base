#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: manualgen
# layer: tool
# owns: the report-only comparison between REVIEW_DISPOSITIONS as hand-maintained
#       and the same dispositions derived from measurable facts
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""derive_dispositions_check.py -- can REVIEW_DISPOSITIONS be derived?

WHY
---
`manualgen_lib.disposition.REVIEW_DISPOSITIONS` is a hand-maintained table that
decides which HELP topics enter the manual's review set and how each is treated.
It drifts against the store every time the store grows. Measured 2026-09-02
(DOCFLUSH-20260901-002): 13 entries named topics that had moved on and one topic
had no entry, and `build-disposition-candidate` reported FAIL until the table was
repaired by hand.

That is the shape this lane keeps finding: A HAND-KEPT LIST WHERE A DERIVATION
BELONGS. The same shape as `collect_set_subcommands()` in the reflection surface,
and as the 64-name literal that `cmdhelp.cpp` used to carry before it delegated
to the function catalog.

WHAT THIS IS, AND IS NOT
------------------------
This is REPORT-ONLY. It derives a disposition for every review topic from facts
the tree already holds, compares that against what the table says, and prints the
agreement rate and every disagreement.

It does NOT change the table, the disposition candidate, or anything the manual
reads. Replacing a hand-maintained policy that governs manual content is an
owner decision, and it should be taken on evidence rather than on the assertion
that derivation is possible. This tool produces that evidence.

    exit 0   every table entry agrees with its derived counterpart
    exit 2   at least one disagreement (the interesting case -- read them)

THE DERIVATION
--------------
Four of the six dispositions fall directly out of two measurable predicates:

    has_runtime   an active public SYSCMD row exists for the topic
    has_help      a physical HELP command row exists for the topic key

    has_runtime                      -> INCLUDE_WITH_RUNTIME_EVIDENCE
    has_help, no runtime             -> INCLUDE_PARTIAL_HELP_REFERENCE
    neither, source-mined + inferred -> ROUTE_SOURCE_FACT_APPENDIX
    neither, otherwise               -> DEFER_NO_RUNTIME_IDENTITY

The fifth, MERGE_ALIAS_TO_CANONICAL, needs to know that two names are the same
command. That is derivable and NOT guesswork: `shell_commands.cpp` registers
both names against the SAME HANDLER, so `command_catalog_sync.registry_handler_map`
already reports the pairing. Two keys sharing a handler are an alias pair, and
the canonical one is the key whose name matches the handler.

The sixth, ROUTE_DEVELOPER_DIAGNOSTIC_APPENDIX, keys on developer-surface naming
(LMDB, _BUFFER) exactly as `cmdhelp.cpp:is_developer_surface_name` does.

WHAT DERIVATION CANNOT RECOVER, and this is the honest limit: the table's
`rationale` prose. A derived rule can say WHAT a topic is; it cannot reproduce a
human's sentence about WHY. If the table is retired, those rationales should be
kept somewhere, not deleted -- they are the reasoning, and this lane has spent a
session learning what it costs when reasoning is thrown away and only the
conclusion survives.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "fullstack_docs"))

from manualgen_lib.disposition import (  # noqa: E402
    REVIEW_DISPOSITIONS,
    _auto_source_fact_policy,
    classify_topic,
)
from manualgen_lib.inventory import collect_inventory  # noqa: E402
from manualgen_lib.paths import ManualgenPaths  # noqa: E402
from manualgen_lib.reference_candidate import _read_harvest  # noqa: E402

REVIEW_BUCKETS = {
    "02_dot_command_review",
    "04_fox_command_review",
    "06_supplemental_public_candidates",
}
_DEVELOPER_SURFACE = re.compile(r"LMDB|_BUFFER")


def _alias_pairs(repo_root: Path) -> dict[str, str]:
    """KEY -> canonical KEY, for keys that share a handler with another key.

    Derived from the registry, not from a list. `registry_handler_map` returns
    KEY -> handler base name; two keys mapping to one handler are the same
    command reached by two spellings, and the canonical spelling is the one that
    matches the handler name.
    """
    try:
        import command_catalog_sync as ccs
    except ImportError:
        return {}
    handlers = ccs.registry_handler_map(repo_root)
    by_handler: dict[str, list[str]] = {}
    for key, handler in handlers.items():
        by_handler.setdefault(handler.upper(), []).append(key)
    out: dict[str, str] = {}
    for handler, keys in by_handler.items():
        if len(keys) < 2:
            continue
        canonical = next((k for k in keys if k.upper().replace(" ", "_") == handler), None)
        if canonical is None:
            canonical = sorted(keys, key=len)[0]
        for key in keys:
            if key != canonical:
                out[key.upper()] = canonical.upper()
    return out


def derive(topic: dict[str, str], has_help: bool, has_runtime: bool,
           aliases: dict[str, str]) -> tuple[str, str]:
    """Return (disposition, target). Target is '' unless it is an alias merge."""
    name = topic.get("TOPIC", "").strip().upper()
    if name in aliases:
        return "MERGE_ALIAS_TO_CANONICAL", aliases[name]
    if has_runtime:
        return "INCLUDE_WITH_RUNTIME_EVIDENCE", ""
    if has_help:
        if _DEVELOPER_SURFACE.search(name):
            return "ROUTE_DEVELOPER_DIAGNOSTIC_APPENDIX", ""
        return "INCLUDE_PARTIAL_HELP_REFERENCE", ""
    if _auto_source_fact_policy(topic, has_help, has_runtime) is not None:
        return "ROUTE_SOURCE_FACT_APPENDIX", ""
    return "DEFER_NO_RUNTIME_IDENTITY", ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--harvest-workspace",
                    default="docs/manuals/developer/manualgen/harvested")
    ap.add_argument("--publication-workspace",
                    default="developer_manual_publication_v1_media_section_v1")
    ap.add_argument("--show-agreements", action="store_true")
    a = ap.parse_args(argv)

    root = Path(a.repo_root).resolve()
    paths = ManualgenPaths(repo_root=root, manual_id="developer",
                           publication_workspace=a.publication_workspace,
                           harvest_workspace=a.harvest_workspace)
    inv = collect_inventory(paths)
    topics = _read_harvest(paths, inv, "HELP_HELP_TOPIC.csv")
    commands = _read_harvest(paths, inv, "HELP_COMMANDS.csv")
    syscmd = _read_harvest(paths, inv, "META_SYSCMD.csv")

    command_keys = {r.get("CMDKEY", "") for r in commands}
    syscmd_by_name = {r.get("CAN_NAME", "").strip().upper(): r for r in syscmd}
    aliases = _alias_pairs(root)

    review = {r.get("TOPICKEY", ""): r for r in topics
              if classify_topic(r)[0] in REVIEW_BUCKETS}

    agree, disagree, underived = [], [], []
    for key, topic in sorted(review.items()):
        table = REVIEW_DISPOSITIONS.get(key)
        meta = syscmd_by_name.get(topic.get("TOPIC", "").strip().upper())
        has_help = key in command_keys
        has_runtime = bool(meta and meta.get("VIS") == "public"
                           and meta.get("ACTIVE", "").lower() == "t")
        got, target = derive(topic, has_help, has_runtime, aliases)
        if table is None:
            underived.append((key, got))
            continue
        want = table["disposition"]
        (agree if got == want else disagree).append((key, want, got, target))

    print(f"  review topics            : {len(review)}")
    print(f"  covered by the table     : {len(agree) + len(disagree)}")
    print(f"  derivation AGREES        : {len(agree)}")
    print(f"  derivation DISAGREES     : {len(disagree)}")
    print(f"  not in the table at all  : {len(underived)} (derived without it)")
    if agree or disagree:
        rate = 100.0 * len(agree) / (len(agree) + len(disagree))
        print(f"  agreement rate           : {rate:.1f}%")
    if disagree:
        print("\n  DISAGREEMENTS -- each is a place the table knows something the rules do not,")
        print("  OR a place the table is stale. Both are worth reading; neither is auto-resolvable.")
        for key, want, got, target in disagree:
            print(f"    {key:<26} table={want:<36} derived={got}{(' -> ' + target) if target else ''}")
    if a.show_agreements and agree:
        print("\n  agreements:")
        for key, want, _got, _t in agree:
            print(f"    {key:<26} {want}")
    return 2 if disagree else 0


if __name__ == "__main__":
    raise SystemExit(main())
