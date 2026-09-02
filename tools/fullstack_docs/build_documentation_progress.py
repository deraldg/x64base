#!/usr/bin/env python3
# @dottalk.file v1
# subsystem: fullstack_docs
# layer: tool
# owns: the derivation of documentation-progress-v1.json from the producer
#       authorities, so the website's headline documentation measures stop
#       being re-typed on the far bank
# project: project.x64base.runtime
# lane: full_stack_documentation
# owner: member.derald
# status: review-needed
"""build_documentation_progress.py -- derive the website's progress artifact.

WHY THIS EXISTS
---------------
`public/artifacts/documentation-progress-v1.json` is the authority that
`scripts/check-site-freshness.mjs` binds `/docs/dottalk/command-reference` to,
via the `command-reference-current-snapshot` contract. A stale snapshot fails
the production build.

Measured 2026-09-01 (DOCFLUSH-20260901-002, Phase 8 entry check): **that artifact
had no producer anywhere in the development tree.** `help_reachable_topics`
occurred exactly zero times outside the site repo. `website_content_manifest.yaml`
lists `docs/dev/documentation-progress` under `maintained_current` with no
`generator:` key, one line above a sibling that declares both a generator and its
sources. The values carried at least three vintages at once:

    source_usage_contract_files  231    matched the tree that day
    source_file_coverage         100.0  matched the tree that day
    source_files                 1082   matched neither (tree was 1080)
    help topics / lines          670 / 29480   matched the 2026-08-26 store

A generator cannot produce that. Hand maintenance can, and did. This is the
north star's failure signature at the publication seam:

    "A fact is entered once, at the source, and carried across the span derived
     -- never re-typed on the far bank."

WHAT IT DOES NOT DO
-------------------
It does not write the site repo. It emits a candidate JSON and, with --check,
compares against a live artifact and reports drift. Promotion into the site tree
is a separate, owner-authorized mutation (Phase 8 M-3).

AUTHORITY REUSE -- DELIBERATE
-----------------------------
Every figure is read from the authority that already owns it. Nothing here
re-implements a parser:

    registry keys / catalog rows / fallback  command_catalog_sync.py
    source files / contracts / coverage      source_census.py
    HELP commands / topics / lines           dottalkpp/data/help/*.dbf via dbfread

`command_catalog_sync.main()` guards on Python 3.12, but the guard is in main()
only -- the library imports and runs on 3.10. That is why this tool calls the
functions rather than shelling out to the CLI. A second parser is how
`audit_contracts.py` acquired the substring bug that counted `.voluntary` blocks
as contracts; this tool exists to remove a copy, so it must not add one.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import command_catalog_sync as ccs  # noqa: E402
import dbfread  # noqa: E402
import source_census  # noqa: E402

SCHEMA = "documentation-progress-v1"

# The fields `site-freshness-contracts.json` substitutes into the page. If a
# field here stops being produced, the production build breaks -- so this list
# is the tool's contract with the website, not a convenience.
BOUND_FIELDS = (
    "website_command_keys",
    "website_command_rows_parsed",
    "website_command_fallback_rows",
    "help_commands",
    "help_reachable_topics",
    "help_lines",
    "manual_candidate_run",
    "first_open_entry",
)


def _dbf_rows(path: Path) -> int | None:
    try:
        return len(dbfread.read(path).rows)
    except Exception:  # noqa: BLE001
        return None


def help_measures(root: Path) -> dict:
    """HELP store measures, from the store's own inspector.

    `help_reachable_topics` is NOT the HELP_TOPIC row count. It is the number of
    distinct TOPICKEYs that HELP_LINE rows actually name -- what
    `tools/coordination/help_store_check.py` calls `topics_reachable`, and what
    `help_build_order_check` prints as "N topics reachable".

    The two agree only while the store is clean. A store with orphan headers has
    MORE topic rows than reachable topics, and that divergence is the entire
    defect `help_store_check` exists to find.

    The first draft of this tool used the raw row count. It matched (666 = 666)
    at this baseline and would have silently published the wrong number the first
    time an orphan header appeared -- a value right by coincidence and wrong by
    definition, in the tool written to end exactly that. So this calls the
    inspector rather than counting rows.
    """
    sys.path.insert(0, str(root / "tools" / "coordination"))
    import help_store_check as hsc  # noqa: PLC0415

    hd = root / "dottalkpp" / "data" / "help"
    d = hsc.inspect(hd)
    return {
        "help_commands": _dbf_rows(hd / "COMMANDS.dbf"),
        "help_reachable_topics": d["topics_reachable"],
        "help_topic_rows": d["topic_rows"],
        "help_lines": d["line_rows"],
        "help_cmd_args": _dbf_rows(hd / "CMD_ARGS.dbf"),
        "help_orphan_headers": len(d["orphan_headers"]),
        "help_store_generation": {"line": d["line_gen"], "topic": d["topic_gen"]},
    }


def source_measures(root: Path) -> dict:
    """@dottalk.file / @dottalk.usage census. Same call source_census makes."""
    c = source_census.census(root) if hasattr(source_census, "census") else None
    if c is None:  # fall back to the CLI shape, still one authority
        out = subprocess.run(
            [sys.executable, str(HERE / "source_census.py")],
            capture_output=True, text=True, cwd=str(root), check=False,
        ).stdout
        def _n(label: str, cast=int):
            m = re.search(rf"^{label}:\s*([0-9.]+)", out, re.M)
            return cast(m.group(1)) if m else None
        return {
            "source_files": _n("total source"),
            "source_usage_contract_files": _n(r"commands \(@usage\)"),
            "source_file_contract_coverage_percent": _n("coverage", float),
            "source_files_uncovered": _n("uncovered"),
        }
    return {
        "source_files": c.get("total"),
        "source_usage_contract_files": c.get("commands"),
        "source_file_contract_coverage_percent": c.get("coverage"),
        "source_files_uncovered": c.get("uncovered"),
    }


def website_measures(root: Path, catalog: Path | None) -> dict:
    """Registry-vs-catalog, via command_catalog_sync's own parsers."""
    keys = ccs.registry_keys(root)
    if catalog is None or not catalog.is_file():
        return {
            "website_command_keys": None,
            "website_command_rows_parsed": None,
            "website_command_fallback_rows": None,
            "registry_keys_hub": len(keys),
            "catalog_status": "ABSENT",
        }
    cat = ccs.parse_catalog(catalog)
    total = len(cat["rows"])
    ki = {k.upper() for k in keys}
    ri = {r.upper() for r in cat["rows"]}
    return {
        "website_command_keys": sum(1 for r in cat["rows"] if r.upper() in ki),
        "website_command_rows_parsed": total - cat["fallback"],
        "website_command_fallback_rows": cat["fallback"],
        "registry_keys_hub": len(keys),
        "catalog_rows": total,
        "catalog_missing": sorted(k for k in keys if k.upper() not in ri),
        "catalog_extra": sorted({r for r in cat["rows"] if r.upper() not in ki}),
        "catalog_status": "PRESENT",
    }


def registry_blind_spot(root: Path) -> dict:
    """Commands registered ONLY outside the hub file.

    `command_catalog_sync.registry_keys()` reads `src/cli/shell_commands.cpp`
    alone. A command that self-registers in its own translation unit and is NOT
    also in the hub is invisible to it -- and therefore invisible to the website
    catalog AND to the catalog's own `check`, which compares two views that share
    the blind spot. Measured 2026-09-01: PREDHELP and PREDICATES, both published
    in `include/dotref.hpp` as implemented and supported, both absent from
    `command-catalog.mdx`, with `check` reporting missing=0 extra=0.

    That is the AIF-118 shape -- a check whose PASS and whose blind spot are the
    same answer -- so this tool measures it rather than inheriting it.
    """
    # Reuse the authority's OWN pattern. A local regex here was measured wrong
    # on first write -- it required an uppercase first character and so missed
    # the keys `!` and `EXPFUNCs`, reporting 237 where registry_keys() reports
    # 239. Two counts of one thing inside the artifact built to end exactly
    # that. Fixed by deleting the second parser rather than correcting it.
    hub = root / "src" / "cli" / "shell_commands.cpp"
    pat = ccs.REGISTRY_ADD_RE
    hub_keys = set(pat.findall(hub.read_text(encoding="utf-8", errors="replace")))
    outside: dict[str, str] = {}
    for f in sorted((root / "src").rglob("*.cpp")):
        if f == hub:
            continue
        try:
            for k in pat.findall(f.read_text(encoding="utf-8", errors="replace")):
                if k not in hub_keys:
                    outside.setdefault(k, str(f.relative_to(root)).replace("\\", "/"))
        except OSError:
            continue
    return {
        "hub_registered_keys": len(hub_keys),
        "registered_only_outside_hub": outside,
        "invisible_to_catalog_generator": sorted(outside),
    }


def manual_candidate(root: Path) -> str | None:
    d = root / "docs/manuals/developer/manualgen/generated/manualgen_build_dry_runs"
    runs = sorted((p.name for p in d.iterdir() if p.is_dir()), reverse=True) if d.is_dir() else []
    return runs[0] if runs else None


def build(root: Path, catalog: Path | None, first_open_entry: str) -> dict:
    cv: dict = {}
    cv.update(source_measures(root))
    cv.update(help_measures(root))
    cv.update(website_measures(root, catalog))
    cv["manual_candidate_run"] = manual_candidate(root)
    cv["first_open_entry"] = first_open_entry
    return {
        "schema": SCHEMA,
        "as_of_date": _dt.date.today().isoformat(),
        "generator": "tools/fullstack_docs/build_documentation_progress.py",
        "generator_note": (
            "Every field below is DERIVED. Do not hand-edit: re-run the "
            "generator. A hand edit here is the defect this tool was built to "
            "remove."
        ),
        "authorities": {
            "source": "tools/fullstack_docs/source_census.py",
            "website": "tools/fullstack_docs/command_catalog_sync.py",
            "help": "dottalkpp/data/help/*.dbf (written by CMDHELP BUILD)",
        },
        "current_vertical": cv,
        "registry_coverage": registry_blind_spot(root),
    }


def compare(built: dict, live_path: Path) -> int:
    live = json.loads(live_path.read_text(encoding="utf-8"))
    b, l = built["current_vertical"], live.get("current_vertical", {})
    print(f"live as_of_date {live.get('as_of_date')}   built {built['as_of_date']}")
    print(f"live generator  {live.get('generator', 'NONE DECLARED')}")
    print()
    print(f"{'field':<40} {'live':>12} {'derived':>12}   state")
    drift = 0
    for k in BOUND_FIELDS:
        lv, bv = l.get(k), b.get(k)
        if bv is None:
            state = "NOT DERIVABLE HERE"
        elif lv is None:
            state = "ABSENT FROM LIVE"
            drift += 1
        elif str(lv) == str(bv):
            state = "match"
        else:
            state = "DRIFT"
            drift += 1
        print(f"{k:<40} {str(lv):>12} {str(bv):>12}   {state}")
    print()
    print(f"bound fields drifted: {drift} of {len(BOUND_FIELDS)}")
    if drift:
        print("The live page publishes the LIVE column. Every DRIFT row is a "
              "number the reader is being shown that the engine disagrees with.")
    return 2 if drift else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo-root", default=".")
    p.add_argument("--catalog", help="command-catalog.mdx in the site repo")
    p.add_argument("--out", help="write the derived artifact here (candidate)")
    p.add_argument("--check", metavar="LIVE_JSON",
                   help="compare against a live artifact; exit 2 on drift")
    p.add_argument("--first-open-entry", default="E5",
                   help="first open Phase-8 entry row, per the entry check")
    a = p.parse_args()

    root = Path(a.repo_root).resolve()
    catalog = Path(a.catalog).resolve() if a.catalog else None
    built = build(root, catalog, a.first_open_entry)

    if a.out:
        out = Path(a.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(built, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
        print(f"wrote candidate -> {out}")

    if a.check:
        return compare(built, Path(a.check).resolve())

    if not a.out:
        print(json.dumps(built, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
