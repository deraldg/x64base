"""Build candidate pages for supported commands.

TWO SELECTORS, and the second is why this docstring is no longer one line.

  DEFAULT (--baseline-topics)  commands added AFTER a HELP baseline. What this
      file was written for and what its NAME still says. Unchanged, so the 8
      accepted post-baseline repair pages are not retroactively redefined.

  ALLOW-LIST (--only-topic-key) the caller NAMES the keys and the tool verifies
      them. Added 2026-08-25 for the 20 written-debt commands, which predate
      the baseline and so can never satisfy the default condition.

      IT IS AN ALLOW-LIST AND NOT A RULE ON PURPOSE. "Supported topic with no
      physical page" sounds like the right rule and returns 109 on this tree,
      measured -- the 20 are a NAMED subset of that, and no condition in the
      data distinguishes them. A tool must not pretend to deduce a list somebody
      chose.

COMPOSITION (--compose-catalog), R127 2a. A page may absorb the lines of a
same-TOPIC sibling in a composing catalog. DOT|BOOLEAN and EDU|BOOLEAN both
cite src/edu/edu_boolean.cpp -- one command, two miners, two keys. Ruled set
for a developer page is DOT + FOX + UI + DEV; EDU/EXT/INTERNAL/ED are separate
surfaces and are NOT composed.

THE NAME IS NOW NARROWER THAN THE FILE. Not renamed: it is cited by run
records and by the accepted pages' provenance layer, and the prepush_gate
precedent (a gate that runs at commit time and kept its push-time name) says
correct the docstring rather than break the citations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


MANUALGEN_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(MANUALGEN_ROOT))

from manualgen_lib.command_reference_candidate import (  # noqa: E402
    _deduplicate_lines,
    _render_page,
)


TRUE_VALUES = {"1", "T", "TRUE", "Y", "YES"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def slug_for(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", topic.strip().lower()).strip("_")


def all_topics(path: Path) -> dict[str, dict[str, str]]:
    """Every topic row, unfiltered. R127 composition needs the SIBLINGS, which
    are by definition not DOT and often not marked SUPPORTED."""
    return {row["TOPICKEY"]: row for row in read_csv(path)}


def supported(path: Path) -> dict[str, dict[str, str]]:
    return {
        row["TOPICKEY"]: row
        for row in read_csv(path)
        if row.get("CATALOG", "").upper() == "DOT"
        and row.get("SUPPORTED", "").upper() in TRUE_VALUES
    }


def build(
    current_topics_path: Path,
    baseline_topics_path: Path | None,
    help_lines_path: Path,
    accepted_command_dir: Path,
    output_dir: Path,
    expected_keys: set[str],
    only_keys: set[str] | None = None,
    compose_catalogs: tuple[str, ...] = (),
    reference_run: str | None = None,
    disposition_run: str = "POSTBASELINE_SUPPORTED_COVERAGE_REPAIR",
    dry_run: bool = False,
) -> dict[str, object]:
    current = supported(current_topics_path)
    every = all_topics(current_topics_path)
    physical_slugs = {path.stem.lower() for path in accepted_command_dir.glob("*.md")}
    findings: list[str] = []
    if only_keys:
        # R127 / allow-list mode. The written-debt commands are a NAMED LIST, not
        # the output of a selector rule -- "supported topic with no page" returns
        # 109 on this tree, measured 2026-08-25, and the 20 are a subset of it.
        # So the caller names them and the tool VERIFIES rather than deduces.
        missing = sorted(k for k in only_keys if k not in current)
        already = sorted(
            k for k in only_keys
            if k in current and slug_for(current[k].get("TOPIC", "")) in physical_slugs
        )
        if missing:
            findings.append("ONLY_KEY_NOT_SUPPORTED:" + ";".join(missing))
        if already:
            findings.append("ONLY_KEY_ALREADY_PAGED:" + ";".join(already))
        new_gaps = {k: current[k] for k in sorted(only_keys) if k in current}
    else:
        if baseline_topics_path is None:
            raise SystemExit("--baseline-topics is required unless --only-topic-key is given")
        baseline = supported(baseline_topics_path)
        new_gaps = {
            key: row
            for key, row in current.items()
            if key not in baseline and slug_for(row.get("TOPIC", "")) not in physical_slugs
        }
    if reference_run is None:
        raise SystemExit("reference_run is required -- a page must name the run that produced it")
    if set(new_gaps) != expected_keys:
        findings.append(
            "EXPECTED_KEY_MISMATCH:"
            f"actual={';'.join(sorted(new_gaps))}:"
            f"expected={';'.join(sorted(expected_keys))}"
        )

    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(help_lines_path):
        lines_by_topic[row.get("TOPICKEY", "")].append(row)

    # R127 2a: a same-TOPIC sibling in a COMPOSING catalog contributes its lines.
    # Not two subjects -- one command mined twice. DOT|BOOLEAN and EDU|BOOLEAN
    # both cite src/edu/edu_boolean.cpp; only the miner and the key differ.
    compose_set = {c.upper() for c in compose_catalogs}
    siblings: dict[str, list[str]] = {}
    crossrefs: dict[str, list[str]] = {}
    for key in new_gaps:
        name = new_gaps[key].get("TOPIC", "").strip().upper()
        same_name = [
            k for k, r in every.items()
            if k != key and r.get("TOPIC", "").strip().upper() == name
        ]
        siblings[key] = sorted(
            k for k in same_name if every[k].get("CATALOG", "").upper() in compose_set
        )
        # NAMED, NOT DROPPED. R127 2a excludes EDU/EXT/INTERNAL/ED from composing
        # a developer page, and requires their existence be recorded rather than
        # silently discarded. A page thin because material was RULED elsewhere is
        # a different fact from a page thin because nothing was written.
        crossrefs[key] = sorted(
            k for k in same_name if every[k].get("CATALOG", "").upper() not in compose_set
        )

    if dry_run:
        # SELECT, CLASSIFY, REPORT -- WRITE NOTHING. The contract gates generating
        # command-reference PROSE from harvested rows. Classification produces no
        # prose and no file, and running it here converts the thin-topic risk from
        # a guess into a number BEFORE the gated act is authorised: a topic whose
        # rows are all excluded appends NO_INCLUDED_HELP_ROWS and fails the WHOLE
        # run, so knowing in advance is the difference between one careful run and
        # a hard failure discovered halfway through.
        print(f"DRY RUN -- selected {len(new_gaps)} key(s), wrote nothing")
        print(f"  {'page key':26} {'own':>5} {'+comp':>6} {'=src':>6} {'incl':>5}  composed / cross-ref")
        would_fail = []
        for key in sorted(new_gaps):
            own = len(lines_by_topic.get(key, []))
            comp = sum(len(lines_by_topic.get(x, [])) for x in siblings[key])
            rows = [r for k in [key] + siblings[key] for r in lines_by_topic.get(k, [])]
            incl, _ = _deduplicate_lines(rows)
            if not incl:
                would_fail.append(key)
            bits = " ".join(f"+{x}" for x in siblings[key])
            xref = " ".join(f"xref:{x}" for x in crossrefs[key])
            flag = "  <-- WOULD FAIL THE RUN" if not incl else ""
            print(f"  {key:26} {own:>5} {comp:>6} {len(rows):>6} {len(incl):>5}  "
                  f"{bits} {xref}{flag}")
        if would_fail:
            print(f"  PREDICTED NO_INCLUDED_HELP_ROWS: {';'.join(would_fail)}")
        for finding in findings:
            print(f"  FINDING {finding}")
        return {
            "status": "PASS_CANDIDATE_ONLY" if not findings else "FAIL",
            "counts": {"pages": 0, "lineage_rows": 0, "findings": len(findings),
                       "selected": len(new_gaps), "would_fail": len(would_fail)},
            "findings": findings,
            "predicted_no_included_help_rows": would_fail,
            "dry_run": True,
        }

    commands_dir = output_dir / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    ledger: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for key in sorted(new_gaps):
        topic = dict(new_gaps[key])          # composed copy; the source row is not mutated
        label = topic.get("TITLE", "").strip() or topic.get("TOPIC", "").strip()
        slug = slug_for(topic.get("TOPIC", ""))
        contributing = [key] + siblings.get(key, [])
        source_rows = [r for k in contributing for r in lines_by_topic.get(k, [])]
        if siblings.get(key):
            # The page says what it is made of. _render_page reads CATALOG straight
            # from this dict, so composition is visible without touching the
            # renderer that the 191 accepted pages share.
            cats = [topic.get("CATALOG", "")] + [
                every[s].get("CATALOG", "") for s in siblings[key]
            ]
            topic["CATALOG"] = "+".join(dict.fromkeys(c for c in cats if c))
        selected, dispositions = _deduplicate_lines(source_rows)
        page = commands_dir / f"{slug}.md"
        page.write_text(
            _render_page(
                topic,
                label,
                selected,
                reference_run,
                disposition_run,
            ),
            encoding="utf-8",
        )
        ledger.append(
            {
                "topic_key": key,
                "topic": topic.get("TOPIC", ""),
                "slug": slug,
                "status": topic.get("STATUS", ""),
                "source_help_rows": len(source_rows),
                "included_help_rows": len(selected),
                "excluded_help_rows": len(source_rows) - len(selected),
                "composed_from": ";".join(contributing),
                "cross_reference": ";".join(crossrefs.get(key, [])),
                "candidate_path": str(page),
                "candidate_sha256": sha256(page),
            }
        )
        for contributor in contributing:
          for source_row in lines_by_topic.get(contributor, []):
            line_id = source_row.get("LINEID", "")
            disposition = dispositions.get(line_id, "EXCLUDE_UNCLASSIFIED")
            lineage.append(
                {
                    "topic_key": contributor,
                    "page_topic_key": key,
                    "slug": slug,
                    "line_id": line_id,
                    "kind": source_row.get("KIND", ""),
                    "source": source_row.get("SOURCE", ""),
                    "included": int(disposition == "INCLUDE_PUBLIC_HELP_EVIDENCE"),
                    "disposition": disposition,
                    "text_sha256": hashlib.sha256(
                        source_row.get("TEXT", "").encode("utf-8")
                    ).hexdigest().upper(),
                }
            )
        if not selected:
            findings.append(f"NO_INCLUDED_HELP_ROWS:{key}")

    ledger_path = output_dir / "postbaseline_supported_command_pages_v1.csv"
    lineage_path = output_dir / "postbaseline_supported_command_lineage_v1.csv"
    report_path = output_dir / "POSTBASELINE_SUPPORTED_COMMAND_PAGES_REVIEW_V1.md"
    manifest_path = output_dir / "postbaseline_supported_command_pages_manifest_v1.json"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "topic_key",
            "topic",
            "slug",
            "status",
            "source_help_rows",
            "included_help_rows",
            "excluded_help_rows",
            "composed_from",
            "cross_reference",
            "candidate_path",
            "candidate_sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)
    with lineage_path.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "topic_key",
            "page_topic_key",
            "slug",
            "line_id",
            "kind",
            "source",
            "included",
            "disposition",
            "text_sha256",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(lineage)

    report = [
        "# Post-baseline Supported Command Pages",
        "",
        f"Status: **{'PASS_CANDIDATE_ONLY' if not findings else 'FAIL'}**",
        "",
        "These pages close the supported-command coverage gaps introduced after",
        "the 2026-07-16 HELP baseline. They were rendered from the repaired",
        "isolated HELP candidate; no accepted publication file is changed by",
        "this candidate builder.",
        "",
        f"- Candidate pages: `{len(ledger)}`",
        f"- Lineage rows: `{len(lineage)}`",
        f"- Included HELP rows: `{sum(int(row['included_help_rows']) for row in ledger)}`",
        f"- Findings: `{len(findings)}`",
        "",
        "## Pages",
        "",
    ]
    report.extend(
        f"- [{row['topic']}](commands/{row['slug']}.md) — "
        f"`{row['included_help_rows']}` included HELP rows"
        for row in ledger
    )
    report.extend(["", "## Findings", ""])
    report.extend(f"- `{finding}`" for finding in findings)
    if not findings:
        report.append("- None.")
    report.append("")
    report_path.write_text("\n".join(report), encoding="utf-8")

    manifest = {
        "schema": "dottalk.manualgen.postbaseline_supported_command_pages.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "required_interpreter": "Python 3.12",
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "status": "PASS_CANDIDATE_ONLY" if not findings else "FAIL",
        "expected_topic_keys": sorted(expected_keys),
        "actual_topic_keys": sorted(new_gaps),
        "counts": {
            "pages": len(ledger),
            "lineage_rows": len(lineage),
            "included_help_rows": sum(int(row["included_help_rows"]) for row in ledger),
            "findings": len(findings),
        },
        "inputs": {
            "current_topics": str(current_topics_path),
            "current_topics_sha256": sha256(current_topics_path),
            "baseline_topics": str(baseline_topics_path),
            "baseline_topics_sha256": sha256(baseline_topics_path),
            "help_lines": str(help_lines_path),
            "help_lines_sha256": sha256(help_lines_path),
            "accepted_command_dir": str(accepted_command_dir),
        },
        "artifacts": {
            "ledger": str(ledger_path),
            "ledger_sha256": sha256(ledger_path),
            "lineage": str(lineage_path),
            "lineage_sha256": sha256(lineage_path),
            "report": str(report_path),
            "report_sha256": sha256(report_path),
        },
        "pages": ledger,
        "findings": findings,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    if sys.version_info[:2] != (3, 12):
        raise SystemExit("Python 3.12.x is required")
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-topics", type=Path, required=True)
    parser.add_argument("--baseline-topics", type=Path, default=None,
                        help="required unless --only-topic-key is given")
    parser.add_argument("--help-lines", type=Path, required=True)
    parser.add_argument("--accepted-command-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-topic-key", action="append", default=[])
    # R127: the written-debt commands are a NAMED LIST, not a selector result.
    parser.add_argument("--only-topic-key", action="append", default=[],
                        help="select exactly these keys; skips the baseline condition")
    parser.add_argument("--compose-catalog", action="append", default=[],
                        help="R127 2a: sibling catalogs whose same-TOPIC lines join the page")
    parser.add_argument("--reference-run", required=True,
                        help="the run that produced these pages; was hardcoded to a July run")
    parser.add_argument("--disposition-run", default="POSTBASELINE_SUPPORTED_COVERAGE_REPAIR")
    parser.add_argument("--dry-run", action="store_true",
                        help="select and report, write nothing")
    args = parser.parse_args()
    manifest = build(
        args.current_topics.resolve(),
        args.baseline_topics.resolve() if args.baseline_topics else None,
        args.help_lines.resolve(),
        args.accepted_command_dir.resolve(),
        args.output_dir.resolve(),
        set(args.expected_topic_key),
        only_keys=set(args.only_topic_key) or None,
        compose_catalogs=tuple(args.compose_catalog),
        reference_run=args.reference_run,
        disposition_run=args.disposition_run,
        dry_run=args.dry_run,
    )
    print(
        "postbaseline_supported_command_pages "
        f"status={manifest['status']} pages={manifest['counts']['pages']} "
        f"lineage={manifest['counts']['lineage_rows']}"
    )
    for finding in manifest.get("findings", []):
        print(f"  FINDING {finding}")
    return 0 if manifest["status"] == "PASS_CANDIDATE_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
