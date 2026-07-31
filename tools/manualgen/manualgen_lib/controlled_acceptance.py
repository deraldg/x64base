from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import __version__
from .paths import ManualgenPaths
from .prose_review import COMMAND_SLUG, PARTIAL_HELP_SLUG, RUNTIME_SLUG
from .runlog import RunLogger, utc_now_iso
from .selective_merge import (
    COMMAND_ALIAS_ANCHOR,
    COMMAND_SURFACE_ANCHOR,
    RUNTIME_ANCHOR,
    _delta_counts,
    _extract_from_heading,
    _insert_after_h2_section,
)
from .util import relpath_posix, sha256_file, write_csv, write_json


EXPECTED_REVIEW = "CONTROLLED_PUBLICATION_MATCHES_PRIMARY_READER"
EXPECTED_RUN = re.compile(r"^MANRUN-\d{8}T\d{6}Z-[0-9A-F]{8}$")
EXPECTED_TARGETS = {
    RUNTIME_SLUG: "copied_section",
    COMMAND_SLUG: "copied_section",
    PARTIAL_HELP_SLUG: "candidate_appendix",
}


def _repo_file(repo_root: Path, value: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else repo_root / path
    resolved = path.resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"Input escapes repository root: {value}") from exc
    return resolved


def _load_json(path: Path, findings: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        findings.append(f"{label}_MISSING:{path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"{label}_INVALID_JSON:{exc}")
        return {}
    if not isinstance(value, dict):
        findings.append(f"{label}_NOT_OBJECT")
        return {}
    return value


def validate_pointer_audit(payload: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    if payload.get("schema") != "dottalk.fullstack.manual_pointer_audit.v1":
        findings.append("POINTER_AUDIT_SCHEMA")
    summary = payload.get("summary", {})
    if summary != {"pass": 21, "review": 1, "fail": 0}:
        findings.append(f"POINTER_AUDIT_SUMMARY:{summary}")
    reviews = [
        str(row.get("check_id", ""))
        for row in payload.get("checks", [])
        if row.get("status") == "REVIEW"
    ]
    if reviews != [EXPECTED_REVIEW]:
        findings.append(f"POINTER_AUDIT_REVIEW_SET:{';'.join(reviews)}")
    return findings


def _heading_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^#{1,6}\s+\S", line))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def build_controlled_acceptance_plan(
    paths: ManualgenPaths,
    candidate_run: str,
    pointer_audit_value: str,
    context_decision_value: str,
    logger: RunLogger | None = None,
) -> tuple[dict[str, Any], dict[str, int]]:
    """Build an exact, report-only acceptance package; never mutate canonical files."""

    findings: list[str] = []
    if not EXPECTED_RUN.fullmatch(candidate_run):
        findings.append(f"CANDIDATE_RUN_ID_INVALID:{candidate_run}")

    candidate_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_selective_merge_candidates"
        / candidate_run
    )
    candidate_manifest_path = candidate_dir / "manual_selective_merge_candidate_manifest.json"
    candidate = _load_json(candidate_manifest_path, findings, "CANDIDATE_MANIFEST")

    try:
        pointer_audit_path = _repo_file(paths.repo_root, pointer_audit_value)
        context_decision_path = _repo_file(paths.repo_root, context_decision_value)
    except ValueError as exc:
        findings.append(f"INPUT_PATH:{exc}")
        pointer_audit_path = context_decision_path = paths.repo_root / "__invalid__"

    pointer_audit = _load_json(pointer_audit_path, findings, "POINTER_AUDIT")
    findings.extend(validate_pointer_audit(pointer_audit) if pointer_audit else [])

    context_text = (
        context_decision_path.read_text(encoding="utf-8-sig", errors="replace")
        if context_decision_path.is_file()
        else ""
    )
    for required in (
        "Decision: approved for canonical acceptance preflight.",
        f"Selective merge: `{candidate_run}`.",
        "Canonical mutation authorized: no.",
        "Publication authorized: no.",
    ):
        if required not in context_text:
            findings.append(f"CONTEXT_DECISION_REQUIRED_TEXT:{required}")

    if candidate:
        if candidate.get("schema") != "dottalk.manualgen.selective_merge_candidate.v1":
            findings.append("CANDIDATE_SCHEMA")
        if candidate.get("run_id") != candidate_run:
            findings.append("CANDIDATE_RUN_MISMATCH")
        if candidate.get("status") != "PASS":
            findings.append("CANDIDATE_STATUS")
        for key, expected in (
            ("candidate_only", 1),
            ("canonical_manual_mutated", 0),
            ("accepted_appendix_mutated", 0),
            ("reader_pointer_mutated", 0),
            ("publication_authority_claimed", 0),
        ):
            if candidate.get(key) != expected:
                findings.append(f"CANDIDATE_BOUNDARY:{key}")

    merge_rows = candidate.get("artifacts", {}).get("merge_targets", []) if candidate else []
    merge_by_target = {str(row.get("target", "")): row for row in merge_rows}
    if set(merge_by_target) != set(EXPECTED_TARGETS):
        findings.append("MERGE_TARGET_SET")
    for target, kind in EXPECTED_TARGETS.items():
        if merge_by_target.get(target, {}).get("target_kind") != kind:
            findings.append(f"MERGE_TARGET_KIND:{target}")

    counts = candidate.get("counts", {}) if candidate else {}
    expected_counts = {
        "reviewed_topics": 8,
        "section_candidates": 2,
        "appendix_candidates": 1,
        "reader_candidates": 1,
        "diff_files": 3,
        "hash_failures": 0,
        "anchor_failures": 0,
        "extraction_failures": 0,
        "section_deletions": 0,
        "canonical_hash_changes": 0,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            findings.append(f"CANDIDATE_COUNT:{key}:{counts.get(key)}")

    reader_input = candidate.get("input", {}).get("base_reader", "") if candidate else ""
    try:
        reader_path = _repo_file(paths.repo_root, str(reader_input))
    except ValueError as exc:
        findings.append(f"READER_PATH:{exc}")
        reader_path = paths.repo_root / "__invalid__"
    reader_text = reader_path.read_text(encoding="utf-8") if reader_path.is_file() else ""
    reader_sha = sha256_file(reader_path) if reader_path.is_file() else ""
    if reader_sha != candidate.get("input", {}).get("base_reader_sha256", ""):
        findings.append("BASE_READER_HASH")
    audit_reader_sha = str(pointer_audit.get("active_reader", {}).get("sha256", ""))
    if reader_sha != audit_reader_sha:
        findings.append("POINTER_AUDIT_READER_HASH")

    candidate_files: dict[str, Path] = {}
    for row in candidate.get("input", {}).get("prose_candidate_files", []) if candidate else []:
        try:
            path = _repo_file(paths.repo_root, str(row.get("relative_path", "")))
        except ValueError as exc:
            findings.append(f"PROSE_PATH:{exc}")
            continue
        if not path.is_file() or sha256_file(path) != row.get("sha256"):
            findings.append(f"PROSE_HASH:{row.get('candidate_file', '')}")
        candidate_files[str(row.get("candidate_file", ""))] = path

    runtime_name = f"{RUNTIME_SLUG}_PROSE_DELTA_CANDIDATE.md"
    command_name = f"{COMMAND_SLUG}_PROSE_DELTA_CANDIDATE.md"
    appendix_name = f"{PARTIAL_HELP_SLUG}_PROSE_APPENDIX_CANDIDATE.md"
    if set(candidate_files) != {runtime_name, command_name, appendix_name}:
        findings.append("PROSE_FILE_SET")

    planned_sections: dict[str, str] = {}
    appendix_text = ""
    planned_reader = ""
    try:
        runtime_prose = candidate_files[runtime_name].read_text(encoding="utf-8")
        command_prose = candidate_files[command_name].read_text(encoding="utf-8")
        appendix_prose = candidate_files[appendix_name].read_text(encoding="utf-8")
        runtime_fragment = _extract_from_heading(
            runtime_prose, "## REGRESSION and TEST as proof launchers"
        )
        generic_fragment = _extract_from_heading(
            command_prose,
            "### GENERIC remains a developer-utility canary",
            "## Candidate insertion B",
        )
        ui_fragment = _extract_from_heading(
            command_prose, "### Application-style UI entry points"
        )
        appendix_body = _extract_from_heading(appendix_prose, "## Reading this appendix")
        appendix_text = "# Partial HELP Reference\n\n" + appendix_body.strip() + "\n"

        for slug in (RUNTIME_SLUG, COMMAND_SLUG):
            row = merge_by_target[slug]
            base = _repo_file(paths.repo_root, str(row.get("base_path", "")))
            candidate_path = _repo_file(paths.repo_root, str(row.get("candidate_path", "")))
            if sha256_file(base) != row.get("base_sha256"):
                findings.append(f"SECTION_BASE_HASH:{slug}")
            if sha256_file(candidate_path) != row.get("candidate_sha256"):
                findings.append(f"SECTION_CANDIDATE_HASH:{slug}")
            base_text = base.read_text(encoding="utf-8")
            if slug == RUNTIME_SLUG:
                rebuilt = _insert_after_h2_section(base_text, RUNTIME_ANCHOR, runtime_fragment)
            else:
                rebuilt = _insert_after_h2_section(
                    base_text, COMMAND_SURFACE_ANCHOR, generic_fragment
                )
                rebuilt = _insert_after_h2_section(rebuilt, COMMAND_ALIAS_ANCHOR, ui_fragment)
            if rebuilt != candidate_path.read_text(encoding="utf-8"):
                findings.append(f"SECTION_REBUILD_MISMATCH:{slug}")
            additions, deletions = _delta_counts(base_text, rebuilt)
            expected_additions = 33 if slug == RUNTIME_SLUG else 22
            if (additions, deletions) != (expected_additions, 0):
                findings.append(f"SECTION_DELTA:{slug}:{additions}:{deletions}")
            planned_sections[slug] = rebuilt

        appendix_row = merge_by_target[PARTIAL_HELP_SLUG]
        appendix_candidate = _repo_file(
            paths.repo_root, str(appendix_row.get("candidate_path", ""))
        )
        if sha256_file(appendix_candidate) != appendix_row.get("candidate_sha256"):
            findings.append("APPENDIX_CANDIDATE_HASH")
        if appendix_text != appendix_candidate.read_text(encoding="utf-8"):
            findings.append("APPENDIX_REBUILD_MISMATCH")

        reader_body = _insert_after_h2_section(reader_text, RUNTIME_ANCHOR, runtime_fragment)
        reader_body = _insert_after_h2_section(
            reader_body, COMMAND_SURFACE_ANCHOR, generic_fragment
        )
        reader_body = _insert_after_h2_section(reader_body, COMMAND_ALIAS_ANCHOR, ui_fragment)
        planned_reader = reader_body.rstrip() + "\n\n---\n\n" + appendix_text.rstrip() + "\n"

        candidate_reader = _repo_file(
            paths.repo_root,
            str(candidate.get("artifacts", {}).get("reader_candidate", "")),
        )
        if sha256_file(candidate_reader) != candidate.get("artifacts", {}).get(
            "reader_candidate_sha256"
        ):
            findings.append("READER_CANDIDATE_HASH")
        expected_banner = (
            "<!-- Candidate-only selective merge reader. Not publication. -->\n"
            f"<!-- Base reader SHA-256: {reader_sha} -->\n"
            f"<!-- Approved prose review: {candidate.get('input', {}).get('prose_review_run_id', '')} -->\n\n"
        )
        if candidate_reader.read_text(encoding="utf-8") != expected_banner + planned_reader:
            findings.append("READER_INDEPENDENT_REBUILD_MISMATCH")
    except (KeyError, OSError, ValueError) as exc:
        findings.append(f"ASSEMBLY:{exc}")

    run_id = logger.run_id if logger else "MANRUN-CONTROLLED-ACCEPTANCE-PLAN"
    output_dir = (
        paths.manualgen_root
        / "generated"
        / "manualgen_controlled_acceptance_plans"
        / run_id
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    mutation_rows: list[dict[str, Any]] = []
    planned_artifacts: dict[str, str] = {}
    if not findings:
        planned_root = output_dir / "planned_outputs"
        section_root = planned_root / "sections"
        appendix_root = planned_root / "appendices"
        runtime_output = section_root / f"{RUNTIME_SLUG}.md"
        command_output = section_root / f"{COMMAND_SLUG}.md"
        appendix_output = appendix_root / f"{PARTIAL_HELP_SLUG}.md"
        reader_output = planned_root / "developer_manual_publication_v1.md"
        aggregate_output = planned_root / "developer_manual_publication_v1_appendices.md"
        for path, text in (
            (runtime_output, planned_sections[RUNTIME_SLUG]),
            (command_output, planned_sections[COMMAND_SLUG]),
            (appendix_output, appendix_text),
            (reader_output, planned_reader),
        ):
            _write_text(path, text)

        aggregate_path = (
            paths.manualgen_root
            / "published"
            / "developer_manual_publication_v1"
            / "developer_manual_publication_v1_appendices.md"
        )
        aggregate_text = aggregate_path.read_text(encoding="utf-8")
        if "# Partial HELP Reference" in aggregate_text:
            findings.append("PARTIAL_HELP_ALREADY_IN_AGGREGATE")
        planned_aggregate = (
            aggregate_text.rstrip() + "\n\n---\n\n" + appendix_text.rstrip() + "\n"
        )
        _write_text(aggregate_output, planned_aggregate)

        planned_reader_sha = sha256_file(reader_output)
        reader_record_path = paths.manualgen_root / "accepted_artifacts" / "primary_reader_artifact_v1.json"
        reader_record = json.loads(reader_record_path.read_text(encoding="utf-8-sig"))
        reader_record.update(
            {
                "mdo": "DOCFLUSH-20260716-001",
                "status": "PRIMARY_READER_CONTENT_ACCEPTANCE_PLANNED_POINTER_UNCHANGED",
                "artifact_sha256": planned_reader_sha.lower(),
                "artifact_lines": len(planned_reader.splitlines()),
                "artifact_heading_count": _heading_count(planned_reader),
                "acceptance_source_run": candidate_run,
            }
        )
        reader_record_output = planned_root / "primary_reader_artifact_v1.planned.json"
        write_json(reader_record_output, reader_record)

        canonical_path = paths.manualgen_root / "accepted_manifests" / "developer_manual_canonical_manifest_v1.json"
        canonical = json.loads(canonical_path.read_text(encoding="utf-8-sig"))
        canonical.update(
            {
                "mdo": "DOCFLUSH-20260716-001",
                "status": "CONTROLLED_SELECTIVE_MERGE_ACCEPTANCE_PLANNED_POINTER_UNCHANGED",
                "current_reference_sha256": planned_reader_sha,
                "acceptance_source_run": candidate_run,
            }
        )
        canonical_output = planned_root / "developer_manual_canonical_manifest_v1.planned.json"
        write_json(canonical_output, canonical)

        appendix_record_output = planned_root / "DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.planned.md"
        _write_text(
            appendix_record_output,
            "\n".join(
                [
                    "# DOCFLUSH-20260716-001 Appendix Acceptance Record",
                    "",
                    "Status: PLANNED_NOT_APPLIED",
                    f"Source run: `{candidate_run}`",
                    f"Partial HELP SHA-256: `{sha256_file(appendix_output)}`",
                    "",
                    "Apply mode must replace this status with an execution result and retain the prior MDO-215 manifest as history.",
                ]
            ),
        )

        planned_map = [
            (runtime_output, merge_by_target[RUNTIME_SLUG]["base_path"], "replace"),
            (command_output, merge_by_target[COMMAND_SLUG]["base_path"], "replace"),
            (
                appendix_output,
                "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/appendices/partial_help_reference.md",
                "create",
            ),
            (
                aggregate_output,
                "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/developer_manual_publication_v1_appendices.md",
                "replace",
            ),
            (reader_output, str(reader_input), "replace"),
            (
                reader_record_output,
                "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json",
                "regenerate_on_apply",
            ),
            (
                canonical_output,
                "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json",
                "regenerate_on_apply",
            ),
            (
                appendix_record_output,
                "docs/manuals/developer/manualgen/accepted_manifests/DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.md",
                "generate_on_apply",
            ),
        ]
        for planned_path, target, action in planned_map:
            target_path = paths.repo_root / target
            mutation_rows.append(
                {
                    "target": target,
                    "action": action,
                    "before_exists": 1 if target_path.exists() else 0,
                    "before_sha256": sha256_file(target_path) if target_path.is_file() else "",
                    "planned_candidate": relpath_posix(planned_path, paths.repo_root),
                    "planned_sha256": sha256_file(planned_path),
                    "apply_authorized": 0,
                }
            )
            planned_artifacts[target] = relpath_posix(planned_path, paths.repo_root)

    mutation_ledger = output_dir / "controlled_acceptance_mutation_ledger.csv"
    write_csv(
        mutation_ledger,
        mutation_rows,
        [
            "target",
            "action",
            "before_exists",
            "before_sha256",
            "planned_candidate",
            "planned_sha256",
            "apply_authorized",
        ],
    )

    status = "PASS_PLAN_ONLY" if not findings else "FAIL"
    review_path = output_dir / "CONTROLLED_ACCEPTANCE_DRY_RUN_REVIEW.md"
    review_lines = [
        "# Controlled Acceptance Dry-Run Review",
        "",
        f"- Run: `{run_id}`",
        f"- Selective merge: `{candidate_run}`",
        f"- Status: `{status}`",
        "- Apply available: no",
        "- Canonical files changed: 0",
        f"- Planned mutation rows: {len(mutation_rows)}",
        f"- Validation findings: {len(findings)}",
        "",
        "## Findings",
        "",
    ]
    review_lines.extend([f"- `{item}`" for item in findings] or ["- None."])
    review_lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This package is report-only. It cannot apply the plan, update the reader pointer, mutate accepted documentation, or publish a website.",
            "",
        ]
    )
    _write_text(review_path, "\n".join(review_lines))

    manifest_path = output_dir / "controlled_acceptance_plan_manifest.json"
    manifest = {
        "schema": "dottalk.manualgen.controlled_acceptance_plan.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "source_candidate_run": candidate_run,
        "status": status,
        "plan_only": 1,
        "apply_available": 0,
        "publication_authority_claimed": 0,
        "canonical_files_mutated": 0,
        "reader_pointer_mutated": 0,
        "inputs": {
            "candidate_manifest": relpath_posix(candidate_manifest_path, paths.repo_root),
            "candidate_manifest_sha256": sha256_file(candidate_manifest_path)
            if candidate_manifest_path.is_file()
            else "",
            "pointer_audit": relpath_posix(pointer_audit_path, paths.repo_root),
            "pointer_audit_sha256": sha256_file(pointer_audit_path)
            if pointer_audit_path.is_file()
            else "",
            "context_decision": relpath_posix(context_decision_path, paths.repo_root),
            "context_decision_sha256": sha256_file(context_decision_path)
            if context_decision_path.is_file()
            else "",
            "active_reader_sha256": reader_sha,
        },
        "counts": {
            "planned_mutation_rows": len(mutation_rows),
            "validation_findings": len(findings),
            "reviewed_topics": 8 if not findings else 0,
        },
        "findings": findings,
        "artifacts": {
            "mutation_ledger": relpath_posix(mutation_ledger, paths.repo_root),
            "review": relpath_posix(review_path, paths.repo_root),
            "planned_outputs": planned_artifacts,
        },
    }
    write_json(manifest_path, manifest)

    if logger:
        logger.artifact("controlled_acceptance_plan_manifest", manifest_path, "Report-only fail-closed acceptance plan.")
        logger.artifact("controlled_acceptance_mutation_ledger", mutation_ledger, "Allow-listed future mutation preview.")
        logger.artifact("controlled_acceptance_dry_run_review", review_path, "Human review surface for the plan-only run.")
        for name in (
            "canonical_files_mutated",
            "reader_pointer_mutated",
            "accepted_documentation_mutated",
            "publication_authority_claimed",
            "apply_available",
        ):
            logger.boundary(name, 0, "PASS", "Plan-only command has no apply path.")

    result_counts = {
        "planned_mutation_rows": len(mutation_rows),
        "validation_findings": len(findings),
        "reviewed_topics": 8 if not findings else 0,
    }
    return {
        "status": status,
        "output_dir": relpath_posix(output_dir, paths.repo_root),
        "manifest": relpath_posix(manifest_path, paths.repo_root),
    }, result_counts
