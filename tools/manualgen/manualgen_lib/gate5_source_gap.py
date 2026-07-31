from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from . import __version__
from .command_reference_candidate import (
    LOCAL_PATH_RE,
    _deduplicate_lines,
    _extract_command_links,
    _load_bound_manifest,
    _render_page,
    _resolve_topic,
    _shift_markdown_headings,
)
from .runlog import utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json


EXPECTED_GAP_COUNT = 19
EXPECTED_STATUS_OCCURRENCES = 7
EXPECTED_SECTIONS = {
    "navigation_browsing_and_search.md": 13,
    "workspaces_areas_and_session_state.md": 6,
}
PROMOTE_ADDITIONS = (
    "docs/manuals/developer/manualgen/accepted_artifacts/ACTIVE_PRIMARY_READER_ARTIFACT.txt",
    "docs/manuals/developer/manualgen/accepted_artifacts/primary_reader_artifact_v1.json",
    "docs/manuals/developer/manualgen/accepted_artifacts/command_reference_artifact_v1.json",
    "docs/manuals/developer/manualgen/accepted_manifests/ACTIVE_MANUALGEN_MANIFEST.txt",
    "docs/manuals/developer/manualgen/accepted_manifests/developer_manual_canonical_manifest_v1.json",
    "docs/manuals/developer/manualgen/accepted_manifests/DOCFLUSH-20260716-001_APPENDIX_ACCEPTANCE_RECORD.md",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/*.md",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/appendices/*.md",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/sections/sections/*.md",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/command_reference_v1/*.md",
    "docs/manuals/developer/manualgen/published/developer_manual_publication_v1/command_reference_v1/commands/*.md",
    "tools/manualgen/*.py",
    "tools/manualgen/*.md",
    "tools/manualgen/manualgen_lib/*.py",
    "tools/manualgen/tests/*.py",
    "tools/fullstack_docs/*.py",
    "tools/fullstack_docs/tests/*.py",
    "docs/maintenance/lanes/full_stack_documentation/*.md",
    "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/DOCUMENTATION_FLUSH_PROGRESS_LOG_V1.md",
    "docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001/documentation_flush_progress_ledger_v1.csv",
)


def _repo_file(repo_root: Path, value: str) -> Path:
    path = Path(value)
    resolved = (path if path.is_absolute() else repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ValueError(f"path escapes repository: {value}") from exc
    return resolved


def _topic_inputs(paths, reference: dict, disposition: dict, findings: list[str]):
    for key in ("markdown", "lineage", "command_resolution"):
        artifact = paths.repo_root / reference["artifacts"][key]
        if not artifact.is_file() or sha256_file(artifact) != reference["artifacts"][key + "_sha256"]:
            findings.append(f"REFERENCE_ARTIFACT_HASH:{key}")
    for key in ("approved_topics", "disposition_ledger"):
        artifact = paths.repo_root / disposition["artifacts"][key]
        if not artifact.is_file() or sha256_file(artifact) != disposition["artifacts"][key + "_sha256"]:
            findings.append(f"DISPOSITION_ARTIFACT_HASH:{key}")
    harvest = {row["file_name"]: row for row in reference["harvest"]["files"]}
    for name in ("HELP_HELP_TOPIC.csv", "HELP_HELP_LINE.csv"):
        row = harvest.get(name, {})
        artifact = paths.repo_root / row.get("relative_path_posix", "__missing__")
        if not artifact.is_file() or sha256_file(artifact) != row.get("sha256"):
            findings.append(f"HARVEST_HASH:{name}")
    topics = read_csv(paths.repo_root / harvest["HELP_HELP_TOPIC.csv"]["relative_path_posix"])
    lines = read_csv(paths.repo_root / harvest["HELP_HELP_LINE.csv"]["relative_path_posix"])
    approved = {
        row.get("topic_key", ""): row
        for row in read_csv(paths.repo_root / disposition["artifacts"]["approved_topics"])
    }
    reviews = {
        row.get("topic_key", ""): row
        for row in read_csv(paths.repo_root / disposition["artifacts"]["disposition_ledger"])
    }
    return harvest, topics, lines, approved, reviews


def _status_decisions(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("title", ""), row.get("status", ""))].append(row)
    decisions: list[dict[str, object]] = []
    for (title, status), occurrences in sorted(grouped.items()):
        is_navigation = title == "Navigation, Browsing, and Search"
        decisions.append(
            {
                "title": title,
                "current_status": status,
                "occurrence_count": len(occurrences),
                "paths": ";".join(row.get("path", "") for row in occurrences),
                "proposed_decision": (
                    "CONDITIONAL_APPROVE_AFTER_19_PAGE_ACCEPTANCE"
                    if is_navigation
                    else "HOLD_REVIEW_REQUIRED"
                ),
                "proposed_visible_status": (
                    "REVIEWED_FOR_PUBLICATION" if is_navigation else status
                ),
                "reason": (
                    "Navigation has 13 supported missing page destinations; promote only with their accepted projection."
                    if is_navigation
                    else "Appendix purpose is explicitly review/deferred; do not erase that semantic state."
                ),
                "maintainer_decision": "PENDING",
            }
        )
    return decisions


def build_gate5_source_gap_candidate(
    paths,
    reference_run: str,
    disposition_run: str,
    gap_ledger_value: str,
    status_ledger_value: str,
    logger=None,
):
    if sys.version_info[:2] != (3, 12):
        raise ValueError("build-gate5-source-gap-candidate requires Python 3.12.x")
    findings: list[str] = []
    manualgen = paths.manualgen_root
    reference_manifest_path = manualgen / "generated" / "manualgen_reference_candidates" / reference_run / "help_topic_reference_manifest.json"
    disposition_manifest_path = manualgen / "generated" / "manualgen_disposition_candidates" / disposition_run / "manual_disposition_manifest.json"
    reference = _load_bound_manifest(reference_manifest_path, "dottalk.manualgen.help_topic_reference_candidate.v1", reference_run)
    disposition = _load_bound_manifest(disposition_manifest_path, "dottalk.manualgen.review_disposition_candidate.v1", disposition_run)
    if reference.get("transform_status") != "PASS" or disposition.get("status") != "PASS":
        findings.append("SOURCE_TRANSFORM_NOT_PASS")
    gap_ledger = _repo_file(paths.repo_root, gap_ledger_value)
    status_ledger = _repo_file(paths.repo_root, status_ledger_value)
    gap_rows = read_csv(gap_ledger)
    status_rows = read_csv(status_ledger)
    if len(gap_rows) != EXPECTED_GAP_COUNT:
        findings.append(f"GAP_ROW_COUNT:{len(gap_rows)}")
    if len(status_rows) != EXPECTED_STATUS_OCCURRENCES:
        findings.append(f"STATUS_OCCURRENCE_COUNT:{len(status_rows)}")
    for row in gap_rows:
        if row.get("introduced_by_gate4") != "0" or row.get("present_in_accepted_reader_destination_set") != "0":
            findings.append(f"GAP_BOUNDARY:{row.get('destination', '')}")

    harvest, topics, help_lines, approved, reviews = _topic_inputs(paths, reference, disposition, findings)
    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in help_lines:
        lines_by_topic[row.get("TOPICKEY", "")].append(row)

    expected_pairs = {(row["section"].replace("\\", "/"), row["destination"]) for row in gap_rows}
    actual_links: list[dict[str, object]] = []
    section_hashes: list[dict[str, str]] = []
    for section_name, expected_count in EXPECTED_SECTIONS.items():
        section = manualgen / "published" / "developer_manual_publication_v1" / "sections" / "sections" / section_name
        section_rel = relpath_posix(section, paths.repo_root)
        links = _extract_command_links(section.read_text(encoding="utf-8-sig"))
        missing_only = [
            link for link in links
            if (section_rel, f"command_reference_v1/commands/{link['slug']}.md") in expected_pairs
        ]
        if len(missing_only) != expected_count:
            findings.append(f"SECTION_GAP_COUNT:{section_name}:{len(missing_only)}")
        section_hashes.append({"path": section_rel, "sha256": sha256_file(section)})
        for link in missing_only:
            actual_links.append({**link, "section": section_rel})
    actual_pairs = {
        (str(row["section"]), f"command_reference_v1/commands/{row['slug']}.md")
        for row in actual_links
    }
    if actual_pairs != expected_pairs:
        findings.append(f"GAP_LEDGER_SOURCE_DRIFT:{len(actual_pairs)}:{len(expected_pairs)}")

    output_dir = manualgen / "generated" / "manualgen_gate5_source_gap_candidates" / logger.run_id
    commands_dir = output_dir / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)
    page_rows: list[dict[str, object]] = []
    lineage_rows: list[dict[str, object]] = []
    attention_pages = 0
    publication_commands = manualgen / "published" / "developer_manual_publication_v1" / "command_reference_v1" / "commands"
    for link in sorted(actual_links, key=lambda row: str(row["slug"])):
        slug, label = str(link["slug"]), str(link["label"])
        topic, rule, match_count = _resolve_topic(label, slug, topics)
        if topic is None:
            findings.append(f"{rule}:{slug}")
            continue
        topic_key = topic.get("TOPICKEY", "")
        if topic_key not in approved:
            findings.append(f"NOT_APPROVED_BY_DISPOSITION:{slug}:{topic_key}")
            continue
        if (publication_commands / f"{slug}.md").exists():
            findings.append(f"TARGET_ALREADY_EXISTS:{slug}")
            continue
        selected, line_dispositions = _deduplicate_lines(lines_by_topic.get(topic_key, []))
        page = commands_dir / f"{slug}.md"
        page.write_text(_render_page(topic, label, selected, reference_run, disposition_run), encoding="utf-8")
        local_hits = len(LOCAL_PATH_RE.findall(page.read_text(encoding="utf-8")))
        if local_hits:
            findings.append(f"LOCAL_PATH_LEAK:{slug}:{local_hits}")
        status = topic.get("STATUS", "").lower()
        supported = topic.get("SUPPORTED", "").upper()
        attention = status not in {"supported", "current"} or supported not in {"T", "TRUE", "YES", "1"}
        attention_pages += int(attention)
        review = reviews.get(topic_key, {})
        page_rows.append({
            "slug": slug,
            "label": label,
            "section": link["section"],
            "topic_key": topic_key,
            "resolution_rule": rule,
            "identity_match_count": match_count,
            "status": topic.get("STATUS", ""),
            "implemented": topic.get("IMPLEMENT", ""),
            "supported": topic.get("SUPPORTED", ""),
            "attention_label": int(attention),
            "disposition": review.get("disposition", approved[topic_key].get("disposition", "")),
            "source_help_rows": len(lines_by_topic.get(topic_key, [])),
            "included_help_rows": len(selected),
            "excluded_help_rows": len(lines_by_topic.get(topic_key, [])) - len(selected),
            "candidate_path": relpath_posix(page, paths.repo_root),
            "candidate_sha256": sha256_file(page),
            "publication_target": relpath_posix(publication_commands / f"{slug}.md", paths.repo_root),
            "publication_target_exists": 0,
            "local_path_hits": local_hits,
        })
        for row in lines_by_topic.get(topic_key, []):
            line_id = row.get("LINEID", "").strip()
            disposition_text = line_dispositions.get(line_id, "EXCLUDE_UNCLASSIFIED")
            lineage_rows.append({
                "slug": slug,
                "topic_key": topic_key,
                "line_id": line_id,
                "kind": row.get("KIND", ""),
                "source": row.get("SOURCE", ""),
                "confidence": row.get("CONFID", ""),
                "included": int(disposition_text == "INCLUDE_PUBLIC_HELP_EVIDENCE"),
                "disposition": disposition_text,
                "text_sha256": hashlib.sha256(row.get("TEXT", "").encode("utf-8")).hexdigest().upper(),
            })

    if len(page_rows) != EXPECTED_GAP_COUNT:
        findings.append(f"PAGE_COVERAGE:{len(page_rows)}/{EXPECTED_GAP_COUNT}")
    decisions = _status_decisions(status_rows)
    if len(decisions) != 4:
        findings.append(f"LOGICAL_STATUS_DECISIONS:{len(decisions)}")
    if sum(row["proposed_decision"] == "CONDITIONAL_APPROVE_AFTER_19_PAGE_ACCEPTANCE" for row in decisions) != 1:
        findings.append("NAVIGATION_STATUS_POLICY")

    page_ledger = output_dir / "gate5_source_gap_page_ledger.csv"
    lineage_ledger = output_dir / "gate5_source_gap_lineage.csv"
    status_decisions = output_dir / "gate5_status_decision_ledger.csv"
    index_path = output_dir / "GATE5_SOURCE_GAP_INDEX.md"
    combined_path = output_dir / "GATE5_SOURCE_GAP_COMBINED_REVIEW.md"
    promote_path = output_dir / "PROMOTE_MANIFEST_DELTA_CANDIDATE.md"
    review_path = output_dir / "GATE5_SOURCE_STAGING_REVIEW.md"
    manifest_path = output_dir / "gate5_source_gap_manifest.json"
    write_csv(page_ledger, page_rows)
    write_csv(lineage_ledger, lineage_rows)
    write_csv(status_decisions, decisions)

    index_lines = [
        "<!-- GATE 5 CANDIDATE ONLY: no publication or source-staging authority. -->",
        "# Gate 5 Supplemental Command Pages",
        "",
        f"All **{len(page_rows)}** standalone-section destinations are exposed here for review.",
        "",
        "| # | Page | Section | Topic | Evidence rows |",
        "| ---: | --- | --- | --- | ---: |",
    ]
    for number, row in enumerate(page_rows, 1):
        index_lines.append(f"| {number} | [{row['label']}](commands/{row['slug']}.md) | `{Path(str(row['section'])).name}` | `{row['topic_key']}` | {row['included_help_rows']} |")
    index_path.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    combined_lines = [
        "<!-- GATE 5 CANDIDATE ONLY: combined review book; no publication authority. -->",
        "# Gate 5 Supplemental Command Pages — Combined Review",
        "",
    ]
    for row in page_rows:
        page = paths.repo_root / str(row["candidate_path"])
        combined_lines.extend(["---", "", _shift_markdown_headings(page.read_text(encoding="utf-8").rstrip()), ""])
    combined_path.write_text("\n".join(combined_lines).rstrip() + "\n", encoding="utf-8")

    existing_manifest = (paths.repo_root / "PROMOTE.manifest").read_text(encoding="utf-8")
    delta_lines = [
        "# Gate 5 PROMOTE.manifest delta candidate",
        "",
        "Report-only proposal. These allow-list entries publish reviewed manual artifacts and reproducibility tools without generated candidates or backups.",
        "",
        "```text",
    ]
    for entry in PROMOTE_ADDITIONS:
        delta_lines.append(entry if entry not in existing_manifest else f"# ALREADY PRESENT: {entry}")
    delta_lines.extend(["```", ""])
    promote_path.write_text("\n".join(delta_lines), encoding="utf-8")

    status = "PASS_CANDIDATE_ONLY" if not findings else "FAIL_CANDIDATE"
    review_lines = [
        "# Gate 5 Source-Staging Review",
        "",
        f"- Status: `{status}`",
        f"- Supplemental pages: `{len(page_rows)}/19`",
        f"- HELP lineage rows: `{len(lineage_rows)}`",
        f"- Attention-labelled pages: `{attention_pages}`",
        f"- Logical status decisions: `{len(decisions)}` from `{len(status_rows)}` occurrences",
        f"- Current PROMOTE.manifest SHA-256: `{sha256_file(paths.repo_root / 'PROMOTE.manifest')}`",
        "- C:\\x64base mutation: `0`",
        "- Accepted manual mutation: `0`",
        "",
        "## Recommendation",
        "",
        "Accept the 19 supported pages and Navigation status as one controlled documentation package. Hold the three review/deferred appendix statuses. Separately review the PROMOTE.manifest delta before any C:\\x64base overlay.",
        "",
        "## Findings",
        "",
    ]
    review_lines.extend([f"- `{finding}`" for finding in findings] or ["- None."])
    review_lines.append("")
    review_path.write_text("\n".join(review_lines), encoding="utf-8")
    manifest = {
        "schema": "dottalk.manualgen.gate5_source_gap_candidate.v1",
        "created_utc": utc_now_iso(),
        "run_id": logger.run_id,
        "manualgen_version": __version__,
        "status": status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "accepted_manual_mutated": 0,
        "source_staging_mutated": 0,
        "website_mutated": 0,
        "bindings": {
            "reference_run": reference_run,
            "reference_manifest": relpath_posix(reference_manifest_path, paths.repo_root),
            "reference_manifest_sha256": sha256_file(reference_manifest_path),
            "disposition_run": disposition_run,
            "disposition_manifest": relpath_posix(disposition_manifest_path, paths.repo_root),
            "disposition_manifest_sha256": sha256_file(disposition_manifest_path),
            "gap_ledger": relpath_posix(gap_ledger, paths.repo_root),
            "gap_ledger_sha256": sha256_file(gap_ledger),
            "status_ledger": relpath_posix(status_ledger, paths.repo_root),
            "status_ledger_sha256": sha256_file(status_ledger),
            "help_topic_sha256": harvest["HELP_HELP_TOPIC.csv"]["sha256"],
            "help_line_sha256": harvest["HELP_HELP_LINE.csv"]["sha256"],
            "section_sources": section_hashes,
            "accepted_reader_sha256": sha256_file(manualgen / "published" / "developer_manual_publication_v1" / "developer_manual_publication_v1.md"),
            "promote_manifest_sha256": sha256_file(paths.repo_root / "PROMOTE.manifest"),
        },
        "counts": {
            "source_gap_rows": len(gap_rows),
            "candidate_pages": len(page_rows),
            "lineage_rows": len(lineage_rows),
            "attention_pages": attention_pages,
            "status_occurrences": len(status_rows),
            "logical_status_decisions": len(decisions),
            "promote_manifest_additions": len(PROMOTE_ADDITIONS),
            "findings": len(findings),
        },
        "findings": findings,
        "artifacts": {
            "review": relpath_posix(review_path, paths.repo_root),
            "review_sha256": sha256_file(review_path),
            "page_ledger": relpath_posix(page_ledger, paths.repo_root),
            "page_ledger_sha256": sha256_file(page_ledger),
            "lineage": relpath_posix(lineage_ledger, paths.repo_root),
            "lineage_sha256": sha256_file(lineage_ledger),
            "status_decisions": relpath_posix(status_decisions, paths.repo_root),
            "status_decisions_sha256": sha256_file(status_decisions),
            "index": relpath_posix(index_path, paths.repo_root),
            "index_sha256": sha256_file(index_path),
            "combined": relpath_posix(combined_path, paths.repo_root),
            "combined_sha256": sha256_file(combined_path),
            "promote_manifest_delta": relpath_posix(promote_path, paths.repo_root),
            "promote_manifest_delta_sha256": sha256_file(promote_path),
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("gate5_source_staging_review", review_path, "Human Gate 5 entrypoint.")
        logger.artifact("gate5_source_gap_index", index_path, "Index of all 19 supplemental pages.")
        logger.artifact("gate5_source_gap_combined", combined_path, "Single review book for all 19 pages.")
        logger.artifact("gate5_status_decisions", status_decisions, "Four logical decisions covering seven status occurrences.")
        logger.artifact("gate5_promote_manifest_delta", promote_path, "Report-only public staging allow-list proposal.")
        logger.artifact("gate5_source_gap_manifest", manifest_path, "Hash-bound Gate 5 candidate manifest.")
        logger.boundary("accepted_manual_mutated", 0, "PASS", "Outputs remain beneath generated/.")
        logger.boundary("source_staging_mutated", 0, "PASS", "C:\\x64base is read-only during this command.")
        logger.boundary("website_mutated", 0, "PASS", "Website is a later gate.")
    return {"status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "review": relpath_posix(review_path, paths.repo_root)}, manifest["counts"]
