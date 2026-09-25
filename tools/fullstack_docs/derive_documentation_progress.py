#!/usr/bin/env python3
"""Re-derive the website's documentation-progress authority FROM MEASURED SOURCES.

    python tools/fullstack_docs/derive_documentation_progress.py \
        --root D:\\code\\ccode --site-root D:\\dev\\x64base-site \
        --static-pages 177 --indexed-pages 170
    ... --check          re-derive into memory and diff; write nothing

WHY THIS EXISTS, stated plainly because the defect it closes is recorded.

public/artifacts/documentation-progress-v1.json is the authority behind six
freshness contracts and, until 2026-09-14, it was TYPED BY HAND. Every contract
keyed to it therefore passed while the whole cluster sat twelve days stale: the
pages agreed with the authority, the authority agreed with itself, and nothing
compared either to the engine. On 2026-09-14 the site published release 145 with
a chrome banner reading "Full-stack docs reconciled 2026-09-02" on all 151
pages, and no gate reported anything.

That is the failure named in the header of derive-primary-key-authority.mjs --
a page and its authority agreeing with each other while both are wrong about the
engine -- arriving for the second time, in the one authority that had no
generator.

WHAT IS MEASURED HERE, and from where:

  HELP/META counts, canonical harvest rows
      docs/manuals/developer/manualgen/harvested/HELP_META_EXPORT_MANIFEST_v1.csv
      -- the export manifest's own row_count column, summed.

  website command keys / parsed / fallback
      command_catalog_sync.py check, by its printed verdict line.

  website function rows
      command_catalog_sync.py fn-check, by its printed verdict line.

  run id, manual candidate
      the newest docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-*
      directory and its gate4_apply_authorization.json.

  static pages built / pagefind pages indexed
      REQUIRED ARGUMENTS. They come from the site build and this tool cannot see
      it. They are required rather than optional ON PURPOSE: a field this tool
      silently carried forward is a field that goes stale exactly the way the
      whole artifact did.

WHAT IS CARRIED, not measured: accepted_manual, pinocchio, source_promotion,
separate_missions, published_checkpoint, authority_note. Those blocks are
preserved byte-for-byte from the existing artifact and listed under
"carried_fields" in the output, so the difference between a measured number and
a remembered one is visible in the artifact itself.

A DELIBERATE SEMANTIC CORRECTION. The hand-written artifact reported
canonical_harvest_tables_current = 14 of 14. The export manifest says ten tables
are EXPORTED from the current store and four are CARRIED_STALE_MAY, carried
forward from May seeds because their source is not yet current. Reporting 14/14
conflated "matches the store" with "exported from the current store". This tool
reports the split.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "x64base.documentation.progress.v1"

MANIFEST_REL = Path("docs/manuals/developer/manualgen/harvested/HELP_META_EXPORT_MANIFEST_v1.csv")
RUNS_REL = Path("docs/maintenance/lanes/full_stack_documentation/runs")
ARTIFACT_REL = Path("public/artifacts/documentation-progress-v1.json")

GATE8_EVIDENCE = "gate8_publication_evidence.json"
GATE8_AUTHORIZATION = "gate8_publication_authorization.json"
GATE8_DECISION = "PUBLICATION_ENTERED"

CARRIED_BLOCKS = (
    "published_checkpoint",
    "accepted_manual",
    "source_promotion",
    "pinocchio",
    "separate_missions",
    "authority_note",
)

# Harvest manifest target_csv -> the artifact field its row_count feeds.
HARVEST_FIELDS = {
    "HELP_COMMANDS.csv": "help_commands",
    "HELP_CMD_ARGS.csv": "help_arguments",
    "HELP_HELP_TOPIC.csv": "help_reachable_topics",
    "HELP_HELP_LINE.csv": "help_lines",
}


class DeriveError(RuntimeError):
    """A measurement could not be taken. Never guessed, never defaulted."""


def read_harvest(root: Path) -> dict:
    path = root / MANIFEST_REL
    if not path.exists():
        raise DeriveError(
            f"harvest export manifest not found: {path}\n"
            "  The canonical harvest is gitignored (.gitignore:525), so a fresh\n"
            "  clone has none. Export and promote a harvest first."
        )
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise DeriveError(f"harvest export manifest is empty: {path}")

    out = {}
    total = 0
    exported = 0
    carried = 0
    for row in rows:
        name = (row.get("target_csv") or "").strip()
        status = (row.get("status") or "").strip()
        try:
            count = int((row.get("row_count") or "").strip())
        except ValueError as exc:
            raise DeriveError(f"unreadable row_count for {name!r}: {exc}") from exc
        total += count
        if status == "EXPORTED":
            exported += 1
        else:
            carried += 1
        if name in HARVEST_FIELDS:
            out[HARVEST_FIELDS[name]] = count

    missing = sorted(set(HARVEST_FIELDS.values()) - set(out))
    if missing:
        raise DeriveError(
            "harvest manifest does not name every required table; missing "
            + ", ".join(missing)
        )

    out["canonical_harvest_rows"] = total
    out["canonical_harvest_tables_required"] = len(rows)
    out["canonical_harvest_tables_exported"] = exported
    out["canonical_harvest_tables_carried_stale"] = carried
    return out


def verdict(root: Path, args: list[str], pattern: str, label: str) -> re.Match:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
    match = re.search(pattern, blob)
    if not match:
        raise DeriveError(
            f"{label}: could not find its verdict line in the output.\n"
            f"  exit={proc.returncode}\n"
            f"  looked for: {pattern}\n"
            "  A missing verdict is NOT a zero. Refusing to derive."
        )
    return match


def read_catalogs(root: Path, site_root: Path) -> dict:
    tools = root / "tools" / "fullstack_docs" / "command_catalog_sync.py"
    content = site_root / "content"

    cmd = verdict(
        root,
        [
            str(tools), "check",
            "--source-root", str(root),
            "--catalog", str(content / "docs" / "dottalk" / "command-catalog.mdx"),
        ],
        r"registry_keys=(\d+)\s+catalog_rows=(\d+)\s+parsed=(\d+)\s+fallback=(\d+)",
        "command catalog check",
    )
    fn = verdict(
        root,
        [
            str(tools), "fn-check",
            "--source-root", str(root),
            "--catalog", str(content / "docs" / "dottalk" / "function-catalog.mdx"),
        ],
        r"core=(\d+)\s+self_registered=(\d+)\s+website_rows=(\d+)",
        "function catalog check",
    )
    return {
        "website_command_keys": int(cmd.group(1)),
        "website_command_rows_parsed": int(cmd.group(3)),
        "website_command_fallback_rows": int(cmd.group(4)),
        "website_function_core_rows": int(fn.group(1)),
        "website_function_extension_rows": int(fn.group(2)),
    }


def read_run(root: Path) -> dict:
    runs = root / RUNS_REL
    if not runs.is_dir():
        raise DeriveError(f"run directory not found: {runs}")
    candidates = sorted(
        (p for p in runs.iterdir() if p.is_dir() and p.name.startswith("DOCFLUSH-")),
        key=lambda p: p.name,
    )
    if not candidates:
        raise DeriveError(f"no DOCFLUSH-* run directory under {runs}")
    run_dir = candidates[-1]

    out = {"run_id": run_dir.name, "_run_dir": run_dir}
    auth = run_dir / "gate4_apply_authorization.json"
    if auth.exists():
        data = json.loads(auth.read_text(encoding="utf-8"))
        plan_run = data.get("plan_run")
        if not isinstance(plan_run, str) or not plan_run.startswith("MANRUN-"):
            raise DeriveError(f"gate4_apply_authorization.json has no usable plan_run: {auth}")
        out["manual_candidate_run"] = plan_run
    else:
        raise DeriveError(
            f"no gate4_apply_authorization.json in {run_dir}.\n"
            "  The manual candidate is the applied plan run; without the\n"
            "  authorization record there is nothing to name."
        )
    return out


def read_gate8(run_dir: Path) -> dict | None:
    """Read the E8 publication record, if the owner has written one.

    Returns None when the authorization is absent -- that is not an error. It is
    the honest state: publication happened but was never recorded, so the site
    should keep reporting E8 open. A gate whose closure leaves no artifact cannot
    be measured, and inventing the value here would be exactly the hand-typed
    authority this whole tool exists to remove.

    When the authorization IS present it must bind to the evidence by hash. An
    authorization that merely names a run could silently come to describe
    different evidence; both harvest promotions in this lane bind the same way,
    through plan_manifest_sha256 and mutation_ledger_sha256.
    """
    evidence_path = run_dir / GATE8_EVIDENCE
    auth_path = run_dir / GATE8_AUTHORIZATION

    if not auth_path.exists():
        return None

    if not evidence_path.exists():
        raise DeriveError(
            f"{GATE8_AUTHORIZATION} exists but {GATE8_EVIDENCE} does not, in {run_dir}.\n"
            "  An authorization with nothing to bind to is not a record."
        )

    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest().upper()
    auth = json.loads(auth_path.read_text(encoding="utf-8"))

    schema = auth.get("schema")
    if schema != "dottalk.fullstack.gate8_publication_authorization.v1":
        raise DeriveError(f"unexpected gate8 authorization schema: {schema!r}")

    decision = auth.get("decision")
    if decision != GATE8_DECISION:
        raise DeriveError(
            f"gate8 authorization decision is {decision!r}, expected {GATE8_DECISION!r}.\n"
            "  Refusing to read publication as entered on any other wording."
        )

    named = str(auth.get("evidence_sha256") or "").upper()
    if named != digest:
        raise DeriveError(
            "gate8 authorization does not bind to the evidence beside it.\n"
            f"  authorization names: {named or '(absent)'}\n"
            f"  evidence hashes to : {digest}\n"
            "  The evidence changed after it was authorized, or the wrong hash "
            "was recorded. Nothing is derived from an unbound authorization."
        )

    if auth.get("run") != run_dir.name:
        raise DeriveError(
            f"gate8 authorization names run {auth.get('run')!r} "
            f"but sits in {run_dir.name}"
        )

    state = auth.get("publication_state")
    if not isinstance(state, str) or not state:
        raise DeriveError("gate8 authorization has no publication_state string")

    return {
        "publication_state": state,
        "vertical": {"first_open_entry": "none", "publication_authorized": True},
    }


def render(root: Path, site_root: Path, static_pages: int, indexed_pages: int) -> str:
    artifact_path = site_root / ARTIFACT_REL
    if not artifact_path.exists():
        raise DeriveError(f"existing artifact not found: {artifact_path}")
    prior = json.loads(artifact_path.read_text(encoding="utf-8"))

    prior_vertical = prior.get("current_vertical") or {}

    measured = {}
    measured.update(read_harvest(root))
    measured.update(read_catalogs(root, site_root))
    run_info = read_run(root)
    run_dir = run_info.pop("_run_dir")
    measured.update(run_info)
    # A --check run has no build to read, so the two build-derived counts may
    # arrive as None. They stay in `measured` either way: if --check reclassified
    # them as carried, measured_fields/carried_fields would differ from a real
    # run and every check would fail on its own bookkeeping. The values fall back
    # to the prior artifact, and --check SAYS SO rather than implying it compared
    # them.
    measured["website_static_pages_built"] = (
        prior_vertical.get("website_static_pages_built")
        if static_pages is None else static_pages
    )
    measured["website_pagefind_pages_indexed"] = (
        prior_vertical.get("website_pagefind_pages_indexed")
        if indexed_pages is None else indexed_pages
    )

    gate8 = read_gate8(run_dir)
    publication_state = prior.get("publication_state")
    if gate8 is not None:
        publication_state = gate8["publication_state"]
        measured.update(gate8["vertical"])

    vertical = dict(prior_vertical)
    vertical.update(measured)
    # BOOKKEEPING is not data. Both of these keys live inside current_vertical,
    # so a prior artifact's copies come back in prior_vertical on the next run.
    # Excluding only "measured_fields" let "carried_fields" count ITSELF as a
    # carried field -- the count read one too high from the second run onward,
    # and the list named itself. Measured 2026-09-14 by a predicted 13 arriving
    # as 14.
    bookkeeping = ("measured_fields", "carried_fields")
    vertical["measured_fields"] = sorted(measured)
    vertical["carried_fields"] = sorted(
        k for k in prior_vertical if k not in measured and k not in bookkeeping
    )

    out = {
        "schema": SCHEMA,
        "as_of_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "maintenance_class": prior.get("maintenance_class", "maintained_current"),
        "current_work_route": prior.get("current_work_route", "/docs/labtalk/current-work"),
        "publication_state": publication_state,
        "note": (
            "GENERATED by tools/fullstack_docs/derive_documentation_progress.py "
            "from the engine tree, the harvest export manifest, and the site "
            "build. Do not hand-edit: re-derive instead. Fields under "
            "current_vertical.measured_fields are measured every run; fields "
            "under carried_fields are preserved from the prior artifact and are "
            "as old as the last time a person touched them."
        ),
    }
    for block in CARRIED_BLOCKS:
        if block in prior:
            out[block] = prior[block]
    out["current_vertical"] = vertical
    return json.dumps(out, indent=2) + "\n"


def strip_volatile(text: str) -> str:
    return re.sub(r'"as_of_date": "[^"]*",\n', "", text)


# The fields strip_volatile removes from the TEXT comparison, so field_differences
# does not report them either. One list, so the two comparisons cannot disagree.
VOLATILE_FIELDS = ("as_of_date",)


def flatten(value, prefix: str = ""):
    """Yield (dotted_path, scalar) for every leaf, lists compared whole.

    A list is emitted as one canonical JSON string rather than per-index leaves.
    measured_fields and carried_fields are lists of names whose ORDER is not
    meaningful, and a per-index diff of a reordered list reports every element as
    changed, which buries the one field that actually moved.
    """
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from flatten(inner, f"{prefix}.{key}" if prefix else key)
    elif isinstance(value, list):
        yield prefix, json.dumps(sorted(value, key=repr), sort_keys=True)
    else:
        yield prefix, value


def field_differences(on_disk_text: str, rendered_text: str):
    """Return [(field, on_disk, fresh)] or None when either side is not JSON.

    None means "cannot say", NOT "no differences" -- an unparseable artifact is
    exactly the case where a caller printing an empty list would read as clean.
    The text comparison in main() remains the verdict; this only explains it, so a
    None here never turns a FAIL into a PASS.
    """
    try:
        disk = json.loads(on_disk_text)
        fresh = json.loads(rendered_text)
    except (ValueError, TypeError):
        return None
    flat_disk = dict(flatten(disk))
    flat_fresh = dict(flatten(fresh))
    absent = object()
    rows = []
    for field in sorted(set(flat_disk) | set(flat_fresh)):
        if field in VOLATILE_FIELDS or field.split(".")[-1] in VOLATILE_FIELDS:
            continue
        was = flat_disk.get(field, absent)
        now = flat_fresh.get(field, absent)
        if was != now:
            rows.append((field,
                         "<absent>" if was is absent else was,
                         "<absent>" if now is absent else now))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="ccode authority root")
    parser.add_argument("--site-root", type=Path, required=True, help="website source root")
    parser.add_argument(
        "--static-pages",
        type=int,
        default=None,
        help="static pages built, from the `next build` output of this run. "
             "REQUIRED to write; optional with --check, which has no build.",
    )
    parser.add_argument(
        "--indexed-pages",
        type=int,
        default=None,
        help="pages indexed, from the pagefind output of this run. "
             "REQUIRED to write; optional with --check, which has no build.",
    )
    parser.add_argument("--check", action="store_true", help="diff only; write nothing")
    args = parser.parse_args()

    if not args.check and (args.static_pages is None or args.indexed_pages is None):
        print("documentation-progress: FAIL -- --static-pages and --indexed-pages "
              "are required to write the artifact. They come from this run's own "
              "build; a field carried forward silently is a field that rots.")
        return 2

    root = args.root.resolve()
    site_root = args.site_root.resolve()
    out_path = site_root / ARTIFACT_REL

    try:
        rendered = render(root, site_root, args.static_pages, args.indexed_pages)
    except DeriveError as exc:
        print(f"documentation-progress: FAIL -- {exc}")
        return 2

    on_disk = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    same = strip_volatile(on_disk) == strip_volatile(rendered)

    if args.check:
        if args.static_pages is None or args.indexed_pages is None:
            print("documentation-progress check: website_static_pages_built and "
                  "website_pagefind_pages_indexed NOT compared -- no build in "
                  "scope. Every other measured field was.")
        if same:
            print("documentation-progress check=PASS -- artifact matches a fresh derivation")
            return 0
        print("documentation-progress check=FAIL -- artifact differs from a fresh derivation")
        # A boolean FAIL is not actionable. Until 2026-09-25 this printed the
        # verdict and the remedy and NOTHING ABOUT WHAT MOVED, so the only way to
        # comply was to re-derive blind -- which overwrites the authority with
        # whatever the tree currently says and launders a regression into it as
        # readily as it records real progress. Naming the fields is what makes
        # "re-derive" a decision instead of an obedience.
        rows = field_differences(on_disk, rendered)
        if rows is None:
            print("  fields: NOT COMPARED -- one side is not parseable JSON. "
                  "That is not the same as no differences.")
        elif not rows:
            print("  fields: the text differs but no JSON field does. Formatting, "
                  "key order or line endings moved. Do not re-derive to chase it; "
                  "find what rewrote the file.")
        else:
            print(f"  {len(rows)} field(s) differ (on disk -> fresh):")
            for field, was, now in rows:
                print(f"      {field}")
                print(f"          on disk : {was}")
                print(f"          fresh   : {now}")
        print("  re-derive: drop --check and re-run with this build's page counts")
        return 2

    # newline="\n" is load-bearing: the default translates to CRLF on
    # Windows, and this artifact is LF in git. Without it every re-derive
    # is a whole-file diff and git warns on each commit.
    out_path.write_text(rendered, encoding="utf-8", newline="\n")
    data = json.loads(rendered)["current_vertical"]
    print(
        "documentation-progress written: "
        f"as_of {json.loads(rendered)['as_of_date']}, "
        f"run {data['run_id']}, "
        f"catalog {data['website_command_keys']}/{data['website_command_rows_parsed']} "
        f"fallback {data['website_command_fallback_rows']}, "
        f"HELP {data['help_commands']}/{data['help_reachable_topics']} "
        f"lines {data['help_lines']}, "
        f"harvest {data['canonical_harvest_rows']} rows over "
        f"{data['canonical_harvest_tables_exported']} exported + "
        f"{data['canonical_harvest_tables_carried_stale']} carried-stale tables, "
        f"{len(data['measured_fields'])} measured / {len(data['carried_fields'])} carried."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
