from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from .gate4_acceptance import _mutation_row, _stage_bytes, rewrite_status_source
from .gate5_source_gap import PROMOTE_ADDITIONS
from .runlog import utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json


EXPECTED_PAGES = 19
EXPECTED_EXISTING_PAGES = 164
EXPECTED_TOTAL_PAGES = 183
EXPECTED_LINEAGE_ROWS = 855
EXPECTED_MUTATIONS = 25
INDEX_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*\[([^\]]+)\]\(commands/([^)]+\.md)\)(\s*⚠)?\s*"
    r"\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*$"
)
INDEX_LINK_RE = re.compile(r"\]\(commands/([^)]+\.md)\)")
LOCAL_PATH_RE = re.compile(r"(?i)(?:[A-Z]:\\|[A-Z]:/|/home/|/mnt/[a-z]/)")


def _load_object(path: Path, findings: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        findings.append(f"{label}_MISSING")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"{label}_INVALID:{exc}")
        return {}
    if not isinstance(value, dict):
        findings.append(f"{label}_NOT_OBJECT")
        return {}
    return value


def _repo_file(repo_root: Path, value: str) -> Path:
    raw = Path(value)
    resolved = (raw if raw.is_absolute() else repo_root / raw).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    return resolved


def _parse_existing_index(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = INDEX_ROW_RE.match(line)
        if not match:
            continue
        label, filename, attention, topic, status, evidence = match.groups()
        rows.append(
            {
                "label": label,
                "filename": filename,
                "attention": bool(attention),
                "topic_key": topic,
                "status": status,
                "evidence_rows": int(evidence),
            }
        )
    return rows


def _render_accepted_index(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: (str(row["label"]).upper(), str(row["filename"])))
    lines = [
        "# DotTalk++ / x64base Command Reference",
        "",
        f"This accepted index exposes all **{len(ordered)}** evidence-backed command pages.",
        "",
        "The primary reader links 164 pages directly. Nineteen additional pages close supported links in the richer standalone Navigation and Workspace sections.",
        "",
        "| # | Command page | Topic | Status | Evidence rows |",
        "| ---: | --- | --- | --- | ---: |",
    ]
    for number, row in enumerate(ordered, 1):
        flag = " ⚠" if row.get("attention") else ""
        lines.append(
            f"| {number} | [{row['label']}](commands/{row['filename']}){flag} | "
            f"`{row['topic_key']}` | `{row['status']}` | {row['evidence_rows']} |"
        )
    lines.extend(["", "⚠ indicates a partial, pending, or unsupported source status.", ""])
    return "\n".join(lines)


def _append_manifest_entries(text: str) -> str:
    missing = [entry for entry in PROMOTE_ADDITIONS if entry not in text.splitlines()]
    if not missing:
        return text
    prefix = text.rstrip("\r\n")
    lines = [
        prefix,
        "",
        "# --- reviewed Developer Manual publication lane --------------------------",
        "# Generated candidates, backups, environments, and runtime data remain excluded.",
        *missing,
        "",
    ]
    return "\n".join(lines)


def _stage_json(staged_root: Path, target: str, value: dict[str, Any]) -> Path:
    return _stage_bytes(
        staged_root,
        target,
        (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )


def build_gate5_development_plan(
    paths,
    candidate_run: str,
    decision_value: str,
    logger=None,
):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("build-gate5-development-plan requires Python 3.12.x")
    findings: list[str] = []
    repo_root = paths.repo_root
    candidate_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_gate5_source_gap_candidates"
        / candidate_run
    )
    candidate_manifest_path = candidate_dir / "gate5_source_gap_manifest.json"
    decision_path = _repo_file(repo_root, decision_value)
    candidate = _load_object(candidate_manifest_path, findings, "CANDIDATE_MANIFEST")
    decision = _load_object(decision_path, findings, "DECISION")
    candidate_sha = sha256_file(candidate_manifest_path) if candidate_manifest_path.is_file() else ""
    if candidate.get("schema") != "dottalk.manualgen.gate5_source_gap_candidate.v1":
        findings.append("CANDIDATE_SCHEMA")
    if candidate.get("run_id") != candidate_run or candidate.get("status") != "PASS_CANDIDATE_ONLY":
        findings.append("CANDIDATE_STATE")
    if decision.get("schema") != "dottalk.fullstack.gate5_source_package_disposition_approval.v1":
        findings.append("DECISION_SCHEMA")
    if decision.get("candidate_run") != candidate_run:
        findings.append("DECISION_RUN_BINDING")
    bindings = {
        "candidate_manifest_sha256": candidate_sha,
        "page_ledger_sha256": candidate.get("artifacts", {}).get("page_ledger_sha256", ""),
        "status_ledger_sha256": candidate.get("artifacts", {}).get("status_decisions_sha256", ""),
        "promote_manifest_delta_sha256": candidate.get("artifacts", {}).get("promote_manifest_delta_sha256", ""),
    }
    for key, actual in bindings.items():
        if str(decision.get(key, "")).upper() != str(actual).upper():
            findings.append(f"DECISION_HASH_BINDING:{key}")
    expected_decisions = {
        "supplemental_pages": "APPROVE_ALL_19_FOR_EXACT_PLANNING",
        "navigation_status": "APPROVE_REVIEWED_FOR_PUBLICATION_WITH_19_PAGES",
        "command_reference_general_review_appendix": "HOLD_REVIEW_REQUIRED",
        "alias_and_variant_review_appendix": "HOLD_REVIEW_REQUIRED",
        "set_family_review_appendix": "HOLD_REVIEW_REQUIRED",
        "promote_manifest_delta": "APPROVE_ALL_20_ENTRIES_FOR_EXACT_PLANNING",
    }
    if decision.get("decisions") != expected_decisions:
        findings.append("DECISION_DISPOSITION")

    artifact_paths: dict[str, Path] = {}
    for key in ("page_ledger", "lineage", "status_decisions", "promote_manifest_delta"):
        rel = str(candidate.get("artifacts", {}).get(key, ""))
        try:
            path = _repo_file(repo_root, rel)
        except ValueError as exc:
            findings.append(f"CANDIDATE_PATH:{key}:{exc}")
            continue
        artifact_paths[key] = path
        expected = str(candidate.get("artifacts", {}).get(f"{key}_sha256", "")).upper()
        if not path.is_file() or sha256_file(path) != expected:
            findings.append(f"CANDIDATE_ARTIFACT_HASH:{key}")

    page_rows = read_csv(artifact_paths.get("page_ledger", repo_root / "__missing__"))
    lineage_rows = read_csv(artifact_paths.get("lineage", repo_root / "__missing__"))
    status_rows = read_csv(artifact_paths.get("status_decisions", repo_root / "__missing__"))
    if len(page_rows) != EXPECTED_PAGES:
        findings.append(f"PAGE_COUNT:{len(page_rows)}")
    if len(lineage_rows) != EXPECTED_LINEAGE_ROWS:
        findings.append(f"LINEAGE_COUNT:{len(lineage_rows)}")
    if len(status_rows) != 4:
        findings.append(f"STATUS_DECISION_COUNT:{len(status_rows)}")
    if sum(row.get("proposed_visible_status") == "REVIEWED_FOR_PUBLICATION" for row in status_rows) != 1:
        findings.append("NAVIGATION_STATUS_DECISION")
    if sum(row.get("proposed_decision") == "HOLD_REVIEW_REQUIRED" for row in status_rows) != 3:
        findings.append("APPENDIX_HOLD_DECISIONS")

    run_id = logger.run_id if logger else "MANRUN-GATE5-DEVELOPMENT-PLAN"
    created_utc = utc_now_iso()
    output_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_gate5_development_plans"
        / run_id
    )
    staged_root = output_dir / "staged_after"
    output_dir.mkdir(parents=True, exist_ok=True)
    mutation_rows: list[dict[str, Any]] = []
    decision_rel = relpath_posix(decision_path, repo_root)

    supplemental_index_rows: list[dict[str, Any]] = []
    for row in page_rows:
        source_rel = row.get("candidate_path", "")
        target_rel = row.get("publication_target", "")
        try:
            source = _repo_file(repo_root, source_rel)
            target = _repo_file(repo_root, target_rel)
        except ValueError as exc:
            findings.append(f"PAGE_PATH:{exc}")
            continue
        if target.is_file() or row.get("publication_target_exists") != "0":
            findings.append(f"PAGE_TARGET_NOT_ABSENT:{target_rel}")
        if not source.is_file() or sha256_file(source) != row.get("candidate_sha256", "").upper():
            findings.append(f"PAGE_HASH:{source_rel}")
            continue
        if row.get("status", "").lower() not in {"supported", "current"} or row.get("implemented", "").upper() != "T" or row.get("supported", "").upper() != "T":
            findings.append(f"PAGE_SUPPORT:{row.get('slug', '')}")
        if row.get("attention_label") != "0" or row.get("local_path_hits") != "0":
            findings.append(f"PAGE_REVIEW_LABEL:{row.get('slug', '')}")
        staged = _stage_bytes(staged_root, target_rel, source.read_bytes())
        mutation_rows.append(
            _mutation_row(repo_root, staged_root, target_rel, staged, source_rel, "Project one approved supplemental command page.")
        )
        supplemental_index_rows.append(
            {
                "label": row["label"],
                "filename": f"{row['slug']}.md",
                "attention": False,
                "topic_key": row["topic_key"],
                "status": row["status"],
                "evidence_rows": int(row["included_help_rows"]),
            }
        )

    publication_root = paths.manualgen_root / "published" / "developer_manual_publication_v1"
    index_path = publication_root / "command_reference_v1" / "README.md"
    existing_index_rows = _parse_existing_index(index_path.read_text(encoding="utf-8-sig")) if index_path.is_file() else []
    if len(existing_index_rows) != EXPECTED_EXISTING_PAGES:
        findings.append(f"EXISTING_INDEX_ROWS:{len(existing_index_rows)}")
    all_index_rows = existing_index_rows + supplemental_index_rows
    filenames = [str(row["filename"]) for row in all_index_rows]
    if len(filenames) != EXPECTED_TOTAL_PAGES or len(set(filenames)) != EXPECTED_TOTAL_PAGES:
        findings.append(f"MERGED_INDEX_UNIQUENESS:{len(filenames)}:{len(set(filenames))}")
    index_rel = relpath_posix(index_path, repo_root)
    staged_index = _stage_bytes(staged_root, index_rel, _render_accepted_index(all_index_rows).encode("utf-8"))
    mutation_rows.append(
        _mutation_row(repo_root, staged_root, index_rel, staged_index, decision_rel, "Replace the candidate-labelled index with the accepted 183-page index.")
    )

    navigation = publication_root / "sections" / "sections" / "navigation_browsing_and_search.md"
    navigation_rel = relpath_posix(navigation, repo_root)
    try:
        navigation_after = rewrite_status_source(
            navigation.read_text(encoding="utf-8-sig"),
            "DRAFT_PROSE_REWRITE / REVIEW_REQUIRED",
        )
    except (OSError, ValueError) as exc:
        findings.append(f"NAVIGATION_STATUS_REWRITE:{exc}")
        navigation_after = navigation.read_text(encoding="utf-8-sig") if navigation.is_file() else ""
    staged_navigation = _stage_bytes(staged_root, navigation_rel, navigation_after.encode("utf-8"))
    mutation_rows.append(
        _mutation_row(repo_root, staged_root, navigation_rel, staged_navigation, decision_rel, "Advance Navigation only with all 19 approved supplemental pages; retain historical status.")
    )

    promote = repo_root / "PROMOTE.manifest"
    promote_before = promote.read_text(encoding="utf-8-sig")
    promote_after = _append_manifest_entries(promote_before)
    if sum(entry in promote_after.splitlines() for entry in PROMOTE_ADDITIONS) != len(PROMOTE_ADDITIONS):
        findings.append("PROMOTE_ADDITION_COVERAGE")
    promote_rel = "PROMOTE.manifest"
    staged_promote = _stage_bytes(staged_root, promote_rel, promote_after.encode("utf-8"))
    mutation_rows.append(
        _mutation_row(repo_root, staged_root, promote_rel, staged_promote, decision_rel, "Allow-list the reviewed manual and reproducibility lane; generated and runtime artifacts remain excluded.")
    )

    record_specs = [
        (
            "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json",
            {
                "gate5_plan_run": run_id,
                "gate5_decision_record": decision_rel,
                "command_reference_pages": EXPECTED_TOTAL_PAGES,
                "reader_linked_command_reference_pages": EXPECTED_EXISTING_PAGES,
                "supplemental_standalone_command_reference_pages": EXPECTED_PAGES,
                "supplemental_command_reference_run": candidate_run,
                "status": "GATE5_SUPPLEMENTAL_SOURCE_PLAN_PENDING_APPLY",
            },
        ),
        (
            "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json",
            {
                "gate5_plan_run": run_id,
                "gate5_decision_record": decision_rel,
                "command_reference_pages_projected": EXPECTED_TOTAL_PAGES,
                "reader_linked_command_reference_pages": EXPECTED_EXISTING_PAGES,
                "supplemental_standalone_command_reference_pages": EXPECTED_PAGES,
                "status": "GATE5_SUPPLEMENTAL_SOURCE_PLAN_PENDING_APPLY",
            },
        ),
        (
            "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json",
            {
                "gate5_plan_run": run_id,
                "gate5_decision_record": decision_rel,
                "page_count": EXPECTED_TOTAL_PAGES,
                "reader_linked_pages": EXPECTED_EXISTING_PAGES,
                "supplemental_standalone_pages": EXPECTED_PAGES,
                "supplemental_source_run": candidate_run,
                "supplemental_source_manifest": relpath_posix(candidate_manifest_path, repo_root),
                "supplemental_source_manifest_sha256": candidate_sha,
                "supplemental_lineage_rows": EXPECTED_LINEAGE_ROWS,
                "lineage_rows": int(candidate.get("counts", {}).get("lineage_rows", 0)) + 3119,
                "status": "GATE5_SUPPLEMENTAL_SOURCE_PLAN_PENDING_APPLY",
            },
        ),
    ]
    for target_rel, updates in record_specs:
        record = _load_object(repo_root / target_rel, findings, f"RECORD:{Path(target_rel).name}")
        record.update(updates)
        record["gate5_plan_created_utc"] = created_utc
        staged = _stage_json(staged_root, target_rel, record)
        mutation_rows.append(
            _mutation_row(repo_root, staged_root, target_rel, staged, decision_rel, "Synchronize accepted evidence for the 164 plus 19 page role split.")
        )

    mutation_rows.sort(key=lambda row: row["target"])
    for sequence, row in enumerate(mutation_rows, 1):
        row["sequence"] = sequence
    if len(mutation_rows) != EXPECTED_MUTATIONS:
        findings.append(f"MUTATION_COUNT:{len(mutation_rows)}")

    staged_publication = staged_root / Path(relpath_posix(publication_root, repo_root))
    link_names = INDEX_LINK_RE.findall(staged_index.read_text(encoding="utf-8"))
    unresolved: list[str] = []
    for name in link_names:
        staged_page = staged_publication / "command_reference_v1" / "commands" / name
        live_page = publication_root / "command_reference_v1" / "commands" / name
        if not staged_page.is_file() and not live_page.is_file():
            unresolved.append(name)
    if len(link_names) != EXPECTED_TOTAL_PAGES or unresolved:
        findings.append(f"INDEX_LINK_CLOSURE:{len(link_names)}:{len(unresolved)}")
    local_hits = len(LOCAL_PATH_RE.findall(staged_index.read_text(encoding="utf-8")))
    if local_hits:
        findings.append(f"INDEX_LOCAL_PATHS:{local_hits}")
    if "Status: REVIEWED_FOR_PUBLICATION" not in navigation_after or navigation_after.count("<!-- HISTORICAL STATUS:") != 1:
        findings.append("NAVIGATION_STATUS_RESULT")

    ledger_path = output_dir / "gate5_planned_mutations.csv"
    write_csv(
        ledger_path,
        mutation_rows,
        [
            "sequence",
            "operation",
            "target",
            "before_exists",
            "before_sha256",
            "staged_path",
            "staged_sha256",
            "source_evidence",
            "reason",
        ],
    )
    create_rows = sum(row["operation"] == "CREATE" for row in mutation_rows)
    replace_rows = sum(row["operation"] == "REPLACE" for row in mutation_rows)
    counts = {
        "planned_mutation_rows": len(mutation_rows),
        "planned_create_rows": create_rows,
        "planned_replace_rows": replace_rows,
        "supplemental_pages": len(page_rows),
        "accepted_index_links": len(link_names),
        "unresolved_index_links": len(unresolved),
        "navigation_status_files": 1,
        "acceptance_records": len(record_specs),
        "promote_manifest_additions": len(PROMOTE_ADDITIONS),
        "held_appendix_statuses": 3,
        "findings": len(findings),
    }
    status = "PASS_PLAN_ONLY" if not findings else "FAIL_PLAN"
    report_path = output_dir / "GATE5_DEVELOPMENT_MUTATION_PLAN.md"
    report_lines = [
        "# Gate 5 Development Mutation Plan",
        "",
        f"- Status: `{status}`",
        f"- Plan run: `{run_id}`",
        f"- Planned mutations: `{len(mutation_rows)}` (`{create_rows}` create, `{replace_rows}` replace)",
        f"- Command reference after plan: `{len(link_names)}` pages (`164` reader-linked plus `19` supplemental)",
        "- Navigation status: `REVIEWED_FOR_PUBLICATION` with historical status retained",
        "- Appendix review/deferred statuses: `3` logical topics held unchanged",
        f"- PROMOTE.manifest additions: `{len(PROMOTE_ADDITIONS)}`",
        "- Accepted reader byte mutation: `0`",
        "- C:\\x64base mutation: `0`",
        "- Git/website mutation: `0`",
        "",
        "## Apply boundary",
        "",
        "This package is plan-only. Development application requires a separate durable authorization naming this run and the exact plan-manifest and mutation-ledger hashes. C:\\x64base preservation/reconciliation remains a later, separate authorization.",
        "",
        "## Findings",
        "",
    ]
    report_lines.extend([f"- `{finding}`" for finding in findings] or ["- None."])
    report_lines.append("")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    manifest_path = output_dir / "gate5_development_plan_manifest.json"
    manifest = {
        "schema": "dottalk.manualgen.gate5_development_plan.v1",
        "created_utc": created_utc,
        "run_id": run_id,
        "status": status,
        "plan_only": 1,
        "apply_available": 0,
        "bindings": {
            "candidate_run": candidate_run,
            "candidate_manifest": relpath_posix(candidate_manifest_path, repo_root),
            "candidate_manifest_sha256": candidate_sha,
            "decision_record": decision_rel,
            "decision_record_sha256": sha256_file(decision_path) if decision_path.is_file() else "",
            "accepted_reader_sha256": candidate.get("bindings", {}).get("accepted_reader_sha256", ""),
            "promote_manifest_before_sha256": candidate.get("bindings", {}).get("promote_manifest_sha256", ""),
        },
        "counts": counts,
        "findings": findings,
        "artifacts": {
            "review": relpath_posix(report_path, repo_root),
            "review_sha256": sha256_file(report_path),
            "mutation_ledger": relpath_posix(ledger_path, repo_root),
            "mutation_ledger_sha256": sha256_file(ledger_path),
            "staged_root": relpath_posix(staged_root, repo_root),
        },
        "boundaries": {
            "accepted_reader_mutated": 0,
            "canonical_files_mutated": 0,
            "source_staging_mutated": 0,
            "git_mutated": 0,
            "website_mutated": 0,
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("gate5_development_plan", report_path, "Human review entrypoint for the exact development plan.")
        logger.artifact("gate5_development_mutation_ledger", ledger_path, "All 25 planned development mutations with before and staged hashes.")
        logger.artifact("gate5_development_plan_manifest", manifest_path, "Hash-bound, plan-only Gate 5 development manifest.")
        logger.boundary("accepted_reader_mutated", 0, "PASS", "The accepted reader is not a target.")
        logger.boundary("canonical_files_mutated", 0, "PASS", "All proposed bytes remain under generated/staged_after.")
        logger.boundary("source_staging_mutated", 0, "PASS", "C:\\x64base remains read-only.")
        logger.boundary("website_mutated", 0, "PASS", "Website work begins after source staging.")
    return {
        "status": status,
        "output_dir": relpath_posix(output_dir, repo_root),
        "review": relpath_posix(report_path, repo_root),
        "manifest": relpath_posix(manifest_path, repo_root),
    }, counts
