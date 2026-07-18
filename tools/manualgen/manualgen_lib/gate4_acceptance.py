from __future__ import annotations

import csv
import json
import re
import shutil
from pathlib import Path
from typing import Any

from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json


EXPECTED_RUN = re.compile(r"^MANRUN-\d{8}T\d{6}Z-[0-9A-F]{8}$")
BEGIN_RE = re.compile(r"^<!-- BEGIN SECTION:\s*(.*?)\s*-->\r?$", re.MULTILINE)
END_RE = re.compile(r"^<!-- END SECTION:\s*(.*?)\s*-->\r?$", re.MULTILINE)
REVIEW_STATUS_RE = re.compile(
    r"^Status:.*(?:REVIEW_REQUIRED|DRAFT|CANDIDATE|STAGED).*\r?$", re.MULTILINE
)
COMMAND_LINK_RE = re.compile(
    r"\]\((?:\.\./\.\./)?command_reference_v1/commands/([^\)#]+\.md)(?:#[^\)]*)?\)"
)
READER_COMMAND_PREFIX = "](../../command_reference_v1/commands/"
PUBLISHED_COMMAND_PREFIX = "](command_reference_v1/commands/"


def _load_json(path: Path, findings: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        findings.append(f"{label}_MISSING:{path}")
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


def _repo_path(repo_root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else repo_root / candidate).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    return resolved


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rewrite_status_source(source_text: str, current_status: str) -> str:
    """Promote one exact status while preserving its previous value in-place."""

    old = f"Status: {current_status}"
    if source_text.count(old) != 1:
        raise ValueError(f"expected exactly one status line: {old}")
    newline = "\r\n" if "\r\n" in source_text else "\n"
    new = (
        f"<!-- HISTORICAL STATUS: {current_status} -->"
        f"{newline}Status: REVIEWED_FOR_PUBLICATION"
    )
    return source_text.replace(old, new, 1)


def rewrite_reader_command_links(source_text: str) -> tuple[str, int]:
    count = source_text.count(READER_COMMAND_PREFIX)
    return source_text.replace(READER_COMMAND_PREFIX, PUBLISHED_COMMAND_PREFIX), count


def _stage_bytes(staged_root: Path, target_rel: str, payload: bytes) -> Path:
    staged = staged_root / Path(target_rel)
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(payload)
    return staged


def _mutation_row(
    repo_root: Path,
    staged_root: Path,
    target_rel: str,
    staged: Path,
    source_evidence: str,
    reason: str,
) -> dict[str, Any]:
    target = repo_root / Path(target_rel)
    exists = target.is_file()
    return {
        "operation": "REPLACE" if exists else "CREATE",
        "target": target_rel.replace("\\", "/"),
        "before_exists": int(exists),
        "before_sha256": sha256_file(target) if exists else "ABSENT",
        "staged_path": relpath_posix(staged, repo_root),
        "staged_sha256": sha256_file(staged),
        "source_evidence": source_evidence,
        "reason": reason,
    }


def _heading_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^#{1,6}\s+\S", line))


def _out_of_scope_reviews(publication_root: Path) -> list[dict[str, str]]:
    paths = [
        publication_root / "sections" / "sections" / "navigation_browsing_and_search.md",
        publication_root / "developer_manual_publication_v1_appendices.md",
    ]
    paths.extend(sorted((publication_root / "appendices").glob("*.md")))
    rows: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file():
            continue
        title = ""
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8-sig").splitlines(), 1
        ):
            if line.startswith("# "):
                title = line[2:].strip()
            if REVIEW_STATUS_RE.match(line):
                rows.append(
                    {
                        "path": path.as_posix(),
                        "line": str(line_number),
                        "title": title,
                        "status": line.removeprefix("Status:").strip(),
                        "disposition": "OUT_OF_SCOPE_REMAINS_REVIEW",
                    }
                )
    return rows


def build_gate4_acceptance_plan(
    paths,
    command_run: str,
    structure_run: str,
    status_approval_value: str,
    logger: RunLogger | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Build an exact Gate 4 mutation package without editing canonical files."""

    findings: list[str] = []
    if not EXPECTED_RUN.fullmatch(command_run):
        findings.append(f"COMMAND_RUN_INVALID:{command_run}")
    if not EXPECTED_RUN.fullmatch(structure_run):
        findings.append(f"STRUCTURE_RUN_INVALID:{structure_run}")

    command_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_command_reference_candidates"
        / command_run
    )
    structure_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_publication_structure_candidates"
        / structure_run
    )
    command_manifest_path = command_dir / "command_reference_candidate_manifest.json"
    structure_manifest_path = structure_dir / "manual_publication_structure_manifest.json"
    command_manifest = _load_json(command_manifest_path, findings, "COMMAND_MANIFEST")
    structure_manifest = _load_json(structure_manifest_path, findings, "STRUCTURE_MANIFEST")
    try:
        approval_path = _repo_path(paths.repo_root, status_approval_value)
    except ValueError as exc:
        findings.append(f"STATUS_APPROVAL_PATH:{exc}")
        approval_path = paths.repo_root / "__invalid__"
    approval = _load_json(approval_path, findings, "STATUS_APPROVAL")

    if command_manifest:
        if command_manifest.get("schema") != "dottalk.manualgen.command_reference_candidate.v1":
            findings.append("COMMAND_MANIFEST_SCHEMA")
        if command_manifest.get("run_id") != command_run:
            findings.append("COMMAND_RUN_MISMATCH")
        if command_manifest.get("status") != "PASS_CANDIDATE_ONLY":
            findings.append("COMMAND_STATUS")
        expected_command_counts = {
            "candidate_pages": 164,
            "reader_link_destinations": 164,
            "lineage_rows": 3119,
            "attention_labelled_pages": 4,
            "findings": 0,
            "local_path_hits": 0,
        }
        for key, expected in expected_command_counts.items():
            actual = command_manifest.get("counts", {}).get(key)
            if actual != expected:
                findings.append(f"COMMAND_COUNT:{key}:{actual}")
        for key in (
            "candidate_only",
            "accepted_reader_mutated",
            "publication_authority_claimed",
            "source_staging_mutated",
            "website_mutated",
        ):
            expected = 1 if key == "candidate_only" else 0
            if command_manifest.get(key) != expected:
                findings.append(f"COMMAND_BOUNDARY:{key}")

    if structure_manifest:
        if structure_manifest.get("schema") != "dottalk.manualgen.publication_structure_candidate.v1":
            findings.append("STRUCTURE_MANIFEST_SCHEMA")
        if structure_manifest.get("run_id") != structure_run:
            findings.append("STRUCTURE_RUN_MISMATCH")
        if structure_manifest.get("status") != "PASS_CANDIDATE_ONLY":
            findings.append("STRUCTURE_STATUS")
        expected_structure_counts = {
            "inserted_end_markers": 11,
            "candidate_begin_markers": 24,
            "candidate_end_markers": 24,
            "status_dispositions": 14,
            "remaining_review_statuses": 0,
            "historical_status_comments": 14,
            "headings_before": 237,
            "headings_after": 237,
            "findings": 0,
        }
        for key, expected in expected_structure_counts.items():
            actual = structure_manifest.get("counts", {}).get(key)
            if actual != expected:
                findings.append(f"STRUCTURE_COUNT:{key}:{actual}")

    status_ledger_path = structure_dir / "status_disposition_ledger.csv"
    expected_status_sha = str(
        structure_manifest.get("artifacts", {}).get("status_ledger_sha256", "")
    ).upper()
    if not status_ledger_path.is_file():
        findings.append("STATUS_LEDGER_MISSING")
        status_rows: list[dict[str, str]] = []
    else:
        if sha256_file(status_ledger_path) != expected_status_sha:
            findings.append("STATUS_LEDGER_HASH")
        status_rows = _read_csv(status_ledger_path)
    if len(status_rows) != 14:
        findings.append(f"STATUS_ROW_COUNT:{len(status_rows)}")

    if approval:
        if approval.get("schema") != "dottalk.fullstack.gate4_status_disposition_approval.v1":
            findings.append("STATUS_APPROVAL_SCHEMA")
        if approval.get("structure_candidate_run") != structure_run:
            findings.append("STATUS_APPROVAL_RUN")
        if str(approval.get("status_ledger_sha256", "")).upper() != expected_status_sha:
            findings.append("STATUS_APPROVAL_LEDGER_HASH")
        if approval.get("decision") != "APPROVE_ALL_ROWS":
            findings.append("STATUS_APPROVAL_DECISION")
        if approval.get("approved_rows") != 14 or approval.get("held_rows") != 0:
            findings.append("STATUS_APPROVAL_COUNTS")

    reader_rel = str(structure_manifest.get("accepted_reader", ""))
    reader = _repo_path(paths.repo_root, reader_rel) if reader_rel else paths.repo_root / "__invalid__"
    reader_before_hash = sha256_file(reader) if reader.is_file() else ""
    expected_reader_hash = str(structure_manifest.get("accepted_reader_sha256", "")).upper()
    if reader_before_hash != expected_reader_hash:
        findings.append("ACCEPTED_READER_HASH")

    structure_candidate_path = structure_dir / "manual_publication_structure_candidate.md"
    expected_structure_sha = str(
        structure_manifest.get("artifacts", {}).get("candidate_sha256", "")
    ).upper()
    if not structure_candidate_path.is_file() or sha256_file(structure_candidate_path) != expected_structure_sha:
        findings.append("STRUCTURE_CANDIDATE_HASH")

    command_ledger_path = command_dir / "command_reference_candidate_ledger.csv"
    expected_command_ledger_sha = str(
        command_manifest.get("artifacts", {}).get("ledger_sha256", "")
    ).upper()
    if not command_ledger_path.is_file() or sha256_file(command_ledger_path) != expected_command_ledger_sha:
        findings.append("COMMAND_LEDGER_HASH")
        command_rows: list[dict[str, str]] = []
    else:
        command_rows = _read_csv(command_ledger_path)
    if len(command_rows) != 164:
        findings.append(f"COMMAND_ROW_COUNT:{len(command_rows)}")

    run_id = logger.run_id if logger else "MANRUN-GATE4-PLAN"
    created_utc = utc_now_iso()
    output_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_gate4_acceptance_plans"
        / run_id
    )
    staged_root = output_dir / "staged_after"
    output_dir.mkdir(parents=True, exist_ok=True)
    mutation_rows: list[dict[str, Any]] = []

    publication_root = reader.parent
    published_command_root_rel = relpath_posix(
        publication_root / "command_reference_v1", paths.repo_root
    )
    staged_command_names: set[str] = set()
    for row in command_rows:
        source_rel = row.get("candidate_path", "")
        try:
            source = _repo_path(paths.repo_root, source_rel)
        except ValueError as exc:
            findings.append(f"COMMAND_PATH:{exc}")
            continue
        name = source.name
        if name in staged_command_names:
            findings.append(f"COMMAND_DUPLICATE:{name}")
            continue
        staged_command_names.add(name)
        expected_sha = row.get("candidate_sha256", "").upper()
        if not source.is_file() or sha256_file(source) != expected_sha:
            findings.append(f"COMMAND_PAGE_HASH:{name}")
            continue
        target_rel = f"{published_command_root_rel}/commands/{name}"
        staged = _stage_bytes(staged_root, target_rel, source.read_bytes())
        mutation_rows.append(
            _mutation_row(
                paths.repo_root,
                staged_root,
                target_rel,
                staged,
                source_rel,
                "Project one hash-bound command-reference page.",
            )
        )

    index_rel = str(command_manifest.get("artifacts", {}).get("index", ""))
    try:
        index_source = _repo_path(paths.repo_root, index_rel)
    except ValueError as exc:
        findings.append(f"COMMAND_INDEX_PATH:{exc}")
        index_source = paths.repo_root / "__invalid__"
    expected_index_sha = str(command_manifest.get("artifacts", {}).get("index_sha256", "")).upper()
    if not index_source.is_file() or sha256_file(index_source) != expected_index_sha:
        findings.append("COMMAND_INDEX_HASH")
    else:
        index_target_rel = f"{published_command_root_rel}/README.md"
        staged_index = _stage_bytes(staged_root, index_target_rel, index_source.read_bytes())
        mutation_rows.append(
            _mutation_row(
                paths.repo_root,
                staged_root,
                index_target_rel,
                staged_index,
                index_rel,
                "Publish the human index for the 164 command pages.",
            )
        )

    if structure_candidate_path.is_file():
        structure_text = structure_candidate_path.read_bytes().decode("utf-8")
        planned_reader, link_rewrites = rewrite_reader_command_links(structure_text)
        staged_reader = _stage_bytes(
            staged_root, reader_rel, planned_reader.encode("utf-8")
        )
        mutation_rows.append(
            _mutation_row(
                paths.repo_root,
                staged_root,
                reader_rel,
                staged_reader,
                relpath_posix(structure_candidate_path, paths.repo_root),
                "Balance section markers, apply approved statuses, and make command links reader-relative.",
            )
        )
    else:
        planned_reader = ""
        link_rewrites = 0
        staged_reader = staged_root / "__invalid__"

    section_target_names: set[str] = set()
    for row in status_rows:
        section_ref = row.get("section", "").replace("\\", "/")
        source = publication_root / "sections" / Path(section_ref)
        target_rel = relpath_posix(source, paths.repo_root)
        if source.name in section_target_names:
            findings.append(f"STATUS_SECTION_DUPLICATE:{source.name}")
            continue
        section_target_names.add(source.name)
        if not source.is_file():
            findings.append(f"STATUS_SECTION_MISSING:{target_rel}")
            continue
        try:
            candidate_text = rewrite_status_source(
                source.read_bytes().decode("utf-8-sig"), row.get("current_status", "")
            )
        except (UnicodeDecodeError, ValueError) as exc:
            findings.append(f"STATUS_SECTION_REWRITE:{source.name}:{exc}")
            continue
        staged = _stage_bytes(staged_root, target_rel, candidate_text.encode("utf-8"))
        mutation_rows.append(
            _mutation_row(
                paths.repo_root,
                staged_root,
                target_rel,
                staged,
                relpath_posix(status_ledger_path, paths.repo_root),
                "Persist one approved section status with its historical value retained.",
            )
        )

    primary_record_rel = "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json"
    canonical_record_rel = "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json"
    command_record_rel = "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json"
    primary_record = _load_json(paths.repo_root / primary_record_rel, findings, "PRIMARY_READER_RECORD")
    canonical_record = _load_json(paths.repo_root / canonical_record_rel, findings, "CANONICAL_RECORD")
    planned_reader_sha = sha256_file(staged_reader) if staged_reader.is_file() else ""
    approval_rel = relpath_posix(approval_path, paths.repo_root)
    if primary_record:
        primary_record.update(
            {
                "acceptance_authorization_record": approval_rel,
                "acceptance_plan_run": run_id,
                "acceptance_source_runs": [command_run, structure_run],
                "accepted_utc": created_utc,
                "artifact_heading_count": _heading_count(planned_reader),
                "artifact_lines": len(planned_reader.splitlines()),
                "artifact_sha256": planned_reader_sha,
                "command_reference_pages": 164,
                "section_statuses_reviewed": 14,
                "section_marker_balance": {"begin": 24, "end": 24},
                "status": "PRIMARY_READER_AND_COMMAND_REFERENCE_ACCEPTED_POINTER_UNCHANGED",
            }
        )
        staged = _stage_bytes(
            staged_root,
            primary_record_rel,
            (json.dumps(primary_record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        mutation_rows.append(
            _mutation_row(paths.repo_root, staged_root, primary_record_rel, staged, approval_rel, "Refresh accepted-reader evidence for Gate 4.")
        )
    if canonical_record:
        canonical_record.update(
            {
                "acceptance_authorization_record": approval_rel,
                "acceptance_plan_run": run_id,
                "acceptance_source_runs": [command_run, structure_run],
                "accepted_utc": created_utc,
                "current_reference_sha256": planned_reader_sha,
                "command_reference_pages_projected": 164,
                "section_statuses_reviewed": 14,
                "section_markers_balanced": 24,
                "status": "GATE4_CANONICAL_READER_AND_COMMAND_REFERENCE_ACCEPTED",
            }
        )
        staged = _stage_bytes(
            staged_root,
            canonical_record_rel,
            (json.dumps(canonical_record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        mutation_rows.append(
            _mutation_row(paths.repo_root, staged_root, canonical_record_rel, staged, approval_rel, "Refresh canonical-manifest evidence for Gate 4.")
        )

    command_record = {
        "schema": "dottalk.manualgen.accepted_command_reference.v1",
        "accepted_utc": created_utc,
        "acceptance_plan_run": run_id,
        "authorization_record": approval_rel,
        "source_command_run": command_run,
        "source_command_manifest": relpath_posix(command_manifest_path, paths.repo_root),
        "source_command_manifest_sha256": sha256_file(command_manifest_path) if command_manifest_path.is_file() else "",
        "publication_root": published_command_root_rel,
        "index": f"{published_command_root_rel}/README.md",
        "page_count": 164,
        "attention_labelled_pages": 4,
        "lineage_rows": 3119,
        "reader_sha256": planned_reader_sha,
        "status": "ACCEPTED_PENDING_EXACT_GATE4_APPLY",
        "boundaries": {
            "reader_pointer_mutated": 0,
            "source_staging_mutated": 0,
            "website_mutated": 0,
        },
    }
    staged = _stage_bytes(
        staged_root,
        command_record_rel,
        (json.dumps(command_record, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    mutation_rows.append(
        _mutation_row(paths.repo_root, staged_root, command_record_rel, staged, approval_rel, "Create accepted command-reference evidence for Gate 4.")
    )

    mutation_rows.sort(key=lambda row: row["target"])
    for sequence, row in enumerate(mutation_rows, 1):
        row["sequence"] = sequence

    reader_destinations = set(COMMAND_LINK_RE.findall(planned_reader))
    if reader_destinations != staged_command_names:
        missing = sorted(reader_destinations - staged_command_names)
        extra = sorted(staged_command_names - reader_destinations)
        findings.append(f"READER_COMMAND_DESTINATIONS:missing={len(missing)}:extra={len(extra)}")
    if link_rewrites < 164:
        findings.append(f"READER_LINK_REWRITES:{link_rewrites}")
    if len(BEGIN_RE.findall(planned_reader)) != 24 or len(END_RE.findall(planned_reader)) != 24:
        findings.append("READER_MARKER_BALANCE")
    if REVIEW_STATUS_RE.search(planned_reader):
        findings.append("READER_REVIEW_STATUS_REMAINS")
    if planned_reader.count("<!-- HISTORICAL STATUS:") != 14:
        findings.append("READER_HISTORICAL_STATUS_COUNT")

    staged_publication_root = staged_root / Path(relpath_posix(publication_root, paths.repo_root))
    section_link_gap_rows: list[dict[str, str]] = []
    all_section_files = sorted((publication_root / "sections" / "sections").glob("*.md"))
    staged_by_target = {row["target"]: row["staged_path"] for row in mutation_rows}
    for section in all_section_files:
        target_rel = relpath_posix(section, paths.repo_root)
        selected = (
            paths.repo_root / staged_by_target[target_rel]
            if target_rel in staged_by_target
            else section
        )
        for name in COMMAND_LINK_RE.findall(selected.read_text(encoding="utf-8-sig")):
            if not (staged_publication_root / "command_reference_v1" / "commands" / name).is_file():
                section_link_gap_rows.append(
                    {
                        "section": target_rel,
                        "destination": f"command_reference_v1/commands/{name}",
                        "present_in_accepted_reader_destination_set": "0",
                        "introduced_by_gate4": "0",
                        "disposition": "PREEXISTING_STANDALONE_SOURCE_GAP_HELD_FOR_RECONCILIATION",
                    }
                )

    section_link_gap_ledger = output_dir / "standalone_section_link_gap_ledger.csv"
    write_csv(section_link_gap_ledger, section_link_gap_rows)

    out_of_scope_rows = _out_of_scope_reviews(publication_root)
    out_of_scope_ledger = output_dir / "out_of_scope_review_status_ledger.csv"
    for row in out_of_scope_rows:
        row["path"] = relpath_posix(Path(row["path"]), paths.repo_root)
    write_csv(out_of_scope_ledger, out_of_scope_rows)

    ledger_path = output_dir / "gate4_planned_mutations.csv"
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
    reader_after_generation = sha256_file(reader) if reader.is_file() else ""
    if reader_after_generation != reader_before_hash:
        findings.append("ACCEPTED_READER_MUTATED_DURING_PLAN")

    command_page_rows = sum(
        1 for row in mutation_rows if "/command_reference_v1/commands/" in row["target"]
    )
    create_rows = sum(1 for row in mutation_rows if row["operation"] == "CREATE")
    replace_rows = sum(1 for row in mutation_rows if row["operation"] == "REPLACE")
    counts = {
        "planned_mutation_rows": len(mutation_rows),
        "planned_create_rows": create_rows,
        "planned_replace_rows": replace_rows,
        "command_pages": command_page_rows,
        "command_indexes": 1 if any(row["target"].endswith("command_reference_v1/README.md") for row in mutation_rows) else 0,
        "section_status_files": len(section_target_names),
        "reader_link_rewrites": link_rewrites,
        "reader_begin_markers": len(BEGIN_RE.findall(planned_reader)),
        "reader_end_markers": len(END_RE.findall(planned_reader)),
        "reader_historical_statuses": planned_reader.count("<!-- HISTORICAL STATUS:"),
        "reader_review_statuses": len(REVIEW_STATUS_RE.findall(planned_reader)),
        "reader_command_destinations": len(reader_destinations),
        "standalone_section_link_gaps": len(section_link_gap_rows),
        "out_of_scope_review_occurrences": len(out_of_scope_rows),
        "review_items": int(bool(section_link_gap_rows)) + int(bool(out_of_scope_rows)),
        "findings": len(findings),
    }
    status = "PASS_PLAN_ONLY" if not findings else "FAIL_PLAN"
    report_path = output_dir / "GATE4_CONTROLLED_ACCEPTANCE_PLAN.md"
    report_lines = [
        "# Gate 4 Controlled Acceptance Plan",
        "",
        f"- Status: `{status}`",
        f"- Plan run: `{run_id}`",
        f"- Planned mutations: `{len(mutation_rows)}` (`{create_rows}` create, `{replace_rows}` replace)",
        f"- Command reference: `{command_page_rows}` pages plus `1` human index",
        f"- Persistent section-status files: `{len(section_target_names)}`",
        f"- Reader links rewritten: `{link_rewrites}`",
        f"- Reader marker balance: `{counts['reader_begin_markers']} BEGIN / {counts['reader_end_markers']} END`",
        f"- Reader historical statuses: `{counts['reader_historical_statuses']}`",
        f"- Accepted reader before/after planning: `{reader_before_hash}` / `{reader_after_generation}`",
        "- Canonical files mutated by this command: `0`",
        "- Website files mutated: `0`",
        "",
        "## Approval binding",
        "",
        f"The all-row decision is bound to status ledger `{expected_status_sha}` and approval record `{approval_rel}`.",
        "",
        "## Deliberately held review states",
        "",
        "The standalone Navigation section and appendix review states are not in the approved 14-row accepted-reader ledger. They remain unchanged. See `out_of_scope_review_status_ledger.csv`.",
        "",
        "## Standalone section link reconciliation",
        "",
        f"The accepted reader's complete 164-destination set resolves in the staged publication. `{len(section_link_gap_rows)}` pre-existing links found only in richer standalone section sources are recorded in `standalone_section_link_gap_ledger.csv`; Gate 4 does not introduce them or invent unsupported pages for them.",
        "",
        "## Apply boundary",
        "",
        "This package is plan-only. Application requires a durable authorization naming this plan run and the exact plan-manifest and mutation-ledger hashes.",
        "",
        "## Findings",
        "",
    ]
    report_lines.extend([f"- `{finding}`" for finding in findings] or ["- None."])
    report_lines.append("")
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    manifest_path = output_dir / "gate4_acceptance_plan_manifest.json"
    manifest = {
        "schema": "dottalk.manualgen.gate4_acceptance_plan.v1",
        "created_utc": created_utc,
        "run_id": run_id,
        "status": status,
        "plan_only": 1,
        "apply_available": 0,
        "bindings": {
            "command_run": command_run,
            "command_manifest": relpath_posix(command_manifest_path, paths.repo_root),
            "command_manifest_sha256": sha256_file(command_manifest_path) if command_manifest_path.is_file() else "",
            "structure_run": structure_run,
            "structure_manifest": relpath_posix(structure_manifest_path, paths.repo_root),
            "structure_manifest_sha256": sha256_file(structure_manifest_path) if structure_manifest_path.is_file() else "",
            "status_approval": approval_rel,
            "status_approval_sha256": sha256_file(approval_path) if approval_path.is_file() else "",
            "accepted_reader": reader_rel,
            "accepted_reader_sha256": reader_before_hash,
        },
        "counts": counts,
        "findings": findings,
        "artifacts": {
            "review": relpath_posix(report_path, paths.repo_root),
            "review_sha256": sha256_file(report_path),
            "mutation_ledger": relpath_posix(ledger_path, paths.repo_root),
            "mutation_ledger_sha256": sha256_file(ledger_path),
            "out_of_scope_status_ledger": relpath_posix(out_of_scope_ledger, paths.repo_root),
            "out_of_scope_status_ledger_sha256": sha256_file(out_of_scope_ledger),
            "standalone_section_link_gap_ledger": relpath_posix(section_link_gap_ledger, paths.repo_root),
            "standalone_section_link_gap_ledger_sha256": sha256_file(section_link_gap_ledger),
            "staged_root": relpath_posix(staged_root, paths.repo_root),
        },
        "boundaries": {
            "canonical_files_mutated": 0,
            "reader_pointer_mutated": 0,
            "source_staging_mutated": 0,
            "website_mutated": 0,
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("gate4_acceptance_plan", report_path, "Human review entrypoint for the exact Gate 4 plan.")
        logger.artifact("gate4_mutation_ledger", ledger_path, "Every planned create/replace row with before and staged hashes.")
        logger.artifact("gate4_plan_manifest", manifest_path, "Hash-bound, plan-only Gate 4 manifest.")
        logger.artifact("gate4_out_of_scope_statuses", out_of_scope_ledger, "Review statuses deliberately excluded from the 14-row approval.")
        logger.artifact("gate4_standalone_section_link_gaps", section_link_gap_ledger, "Pre-existing links outside the accepted reader's 164-destination set.")
        logger.boundary("canonical_files_mutated", 0, "PASS", "All proposed files live under generated/staged_after.")
        logger.boundary("reader_pointer_mutated", 0, "PASS", "The active reader pointer is not a planned target.")
        logger.boundary("website_mutated", 0, "PASS", "No website write path exists.")
        logger.boundary("product_source_mutated", 0, "PASS", "Only documentation tooling and generated plan artifacts are written.")
    return {
        "status": status,
        "output_dir": relpath_posix(output_dir, paths.repo_root),
        "review": relpath_posix(report_path, paths.repo_root),
        "manifest": relpath_posix(manifest_path, paths.repo_root),
    }, counts
