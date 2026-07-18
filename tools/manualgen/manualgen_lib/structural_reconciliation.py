from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json


PRIMARY_WORKSPACE = "developer_manual_publication_v1"
MEDIA_WORKSPACE = "developer_manual_publication_v1_media_section_v1"
CONTROLLED_WORKSPACE = "developer_manual_publication_v1_media_section_v1_man_cli_reference_v1"
CONTROLLED_COMBINED = "developer_manual_publication_v1_media_section_v1.md"
PARTIAL_HELP_APPENDIX = "partial_help_reference"


STRUCTURAL_REVIEW_DISPOSITIONS: dict[str, tuple[str, str, str]] = {
    "DOT|BANG": ("system_shell_and_files", "HIGH", "Authoritative source usage contract classifies BANG as a host-shell command with explicit external-process and filesystem risk."),
    "DOT|EXITS": ("documentation_modeling_and_project_notes", "MEDIUM", "Source contract defines EXITS as read-only document control over the reviewed extension manifest; it does not load or mutate exits."),
    "DOT|EXPORTFUNCTIONS": ("functions_and_expression_helpers", "HIGH", "Source contract exports the canonical expression/function catalog and retains EXPFUNCS as its registered compatibility alias."),
    "DOT|GENERIC": ("command_surface_dispatch_and_entry_variants", "MEDIUM", "DOTREF identifies a developer utility placeholder and source locates the command on the UI entry surface."),
    "DOT|HIER": ("relations_and_tuple_views", "MEDIUM", "DOTREF describes hierarchy-oriented data, relation, and teaching views; Relations and Tuple Views is the narrowest governed concept section."),
    "DOT|MULTIREP": ("tables_records_and_data_editing", "HIGH", "Runtime help defines one-pass multi-field record replacement with locking, memo, and index-maintenance behavior."),
    "DOT|PRN": ("system_shell_and_files", "HIGH", "Source and HELP define PRN as command-output destination routing, including console, file, printer, and null targets."),
    "DOT|VAR": ("scripting_and_control_flow", "HIGH", "DOTREF and source define session variables and macro-style script values."),
    "DOT|SB": ("navigation_browsing_and_search", "HIGH", "DOTREF declares SB an alias for SIMPLEBROWSER."),
    "DOT|SET VAR": ("scripting_and_control_flow", "HIGH", "DOTREF declares SET VAR as the script macro-variable setter and reader."),
    "DOT|SET VAR!": ("scripting_and_control_flow", "HIGH", "DOTREF declares SET VAR! as the force-set script macro-variable variant."),
    "DOT|SM": ("navigation_browsing_and_search", "HIGH", "DOTREF declares SM an alias for SMARTBROWSER."),
    "DOT|SMART": ("navigation_browsing_and_search", "HIGH", "DOTREF declares SMART an alias for SMARTBROWSER."),
}


FAMILY_RULES: tuple[tuple[str, set[str], str], ...] = (
    ("expressions_querying_and_aggregates", {"AGGS", "AVERAGE", "AVG", "CALC", "CALCWRITE", "COUNT", "MAX", "MIN", "SUM", "WHERE", "WHERECACHE"}, "AGGREGATE_OR_QUERY_FAMILY"),
    ("functions_and_expression_helpers", {"BOOLEAN", "CASE", "FORMULA", "STRCAT"}, "EXPRESSION_HELPER_FAMILY"),
    ("navigation_browsing_and_search", {"BBOX", "BROWSETUI", "BROWSETV", "DISPLAY", "FIRST", "LAST", "NEXT", "PRIOR", "RBROWSE", "REFRESH", "SHOW", "SIMPLEBROWSE", "SIMPLEBROWSER", "SMARTBROWSE", "SMARTBROWSER"}, "BROWSE_OR_TRAVERSAL_FAMILY"),
    ("indexing_tags_relations_and_views", {"INDEXSEEK", "REL_LIST", "SET", "SET_CASE", "SET_CDX", "SET_CNX", "SET_FILTER", "SET_INDEX", "SET_LMDB", "SET_NEAR", "SET_ORDER", "SET_PATH", "SET_RELATION", "SET_UNIQUE", "SORT"}, "SET_INDEX_OR_RELATION_FAMILY"),
    ("tables_records_and_data_editing", {"APPEND_BLANK", "INSERT"}, "DATA_MUTATION_FAMILY"),
    ("tables_records_and_data_model", {"DBAREA", "DBAREAS", "DDICT", "DDL", "FIELDMGR", "FIELDS", "MEMO", "RECORD", "RECORDVIEW", "RECNO", "SCHEMA", "TABLE", "TABLEMETA"}, "DATA_MODEL_FAMILY"),
    ("workspaces_areas_and_session_state", {"WA"}, "WORK_AREA_FAMILY"),
    ("messages_errors_and_diagnostics", {"CMDARGCHK", "ERROR_CLEAR", "ERROR_STATUS", "ERROR_TEST", "MSGMGR", "STATUS"}, "DIAGNOSTIC_FAMILY"),
    ("help_metadata_cmdhelpchk_and_manualgen_alignment", {"CMDHELP", "CMDHELPCHK", "HELP", "MAINT", "MANSTAR", "MANUAL"}, "DOCUMENTATION_PIPELINE_FAMILY"),
    ("runtime_evidence_source_verification_and_canary_closure", {"CANARY", "REGRESSION", "TEST"}, "RUNTIME_PROOF_FAMILY"),
    ("import_export_and_storage_bridges", {"LIST_LMDB"}, "STORAGE_FAMILY"),
    ("getting_started_and_session_basics", {"ABOUT", "CLEAR", "COLOR", "ECHO", "EXIT", "QUIT", "VERSION"}, "SESSION_BASICS_FAMILY"),
    ("educational_and_demo_commands", {"ARCTICTALK", "BELL", "BETA", "HANUKKAH"}, "EDUCATION_OR_DEMO_FAMILY"),
)


def _slug(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", text.lower())).strip("_")


def _topic_identity(text: str) -> str:
    return _slug(text).upper()


def _latest_disposition_dir(paths: ManualgenPaths) -> Path | None:
    root = paths.manualgen_root / "generated" / "manualgen_disposition_candidates"
    candidates = []
    for directory in root.glob("MANRUN-*") if root.exists() else []:
        manifest = directory / "manual_disposition_manifest.json"
        approved = directory / "manual_section_factory_approved_topics.csv"
        if manifest.exists() and approved.exists():
            candidates.append(directory)
    return sorted(candidates, key=lambda path: path.name)[-1] if candidates else None


def _primary_sections(paths: ManualgenPaths) -> dict[str, Path]:
    root = paths.published_dir / PRIMARY_WORKSPACE / "sections" / "sections"
    return {path.stem: path for path in sorted(root.glob("*.md"))}


def _primary_appendices(paths: ManualgenPaths) -> dict[str, Path]:
    root = paths.published_dir / PRIMARY_WORKSPACE / "appendices"
    return {path.stem: path for path in sorted(root.glob("*.md"))}


def _controlled_sections(paths: ManualgenPaths) -> list[dict[str, Any]]:
    combined = paths.published_dir / CONTROLLED_WORKSPACE / CONTROLLED_COMBINED
    text = combined.read_text(encoding="utf-8", errors="replace") if combined.exists() else ""
    rows = []
    pattern = re.compile(r"^<!-- MDO-347E-CANDIDATE-SECTION ordinal=(\d+) title=(.*?) -->$", re.MULTILINE)
    for match in pattern.finditer(text):
        title = match.group(2).strip()
        rows.append({"ordinal": int(match.group(1)), "title": title, "slug": _slug(title)})
    return rows


def _existing_assignments(section_paths: dict[str, Path]) -> dict[str, set[str]]:
    assignments: dict[str, set[str]] = defaultdict(set)
    pattern = re.compile(r"^- \[([^]]+)\]\(", re.MULTILINE)
    for section_slug, path in section_paths.items():
        text = path.read_text(encoding="utf-8", errors="replace")
        for command in pattern.findall(text):
            assignments[_topic_identity(command)].add(section_slug)
    return assignments


def _family_target(topic: str) -> tuple[str, str] | None:
    identity = _topic_identity(topic)
    for target, members, rule in FAMILY_RULES:
        if identity in members:
            return target, rule
    return None


def _choose_mapping(
    row: dict[str, str],
    assignments: dict[str, set[str]],
    order: dict[str, int],
    appendix_assignments: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    catalog = row.get("catalog", "")
    topic = row.get("topic", "")
    group = row.get("section_group", "")
    exact = sorted(assignments.get(_topic_identity(topic), set()), key=lambda slug: order.get(slug, 999))
    appendix_exact = sorted((appendix_assignments or {}).get(_topic_identity(topic), set()))
    appendix_text = ";".join(appendix_exact)
    if group == "05_partial_help_reference":
        return {"target_slug": PARTIAL_HELP_APPENDIX, "target_kind": "NEW_CANDIDATE_APPENDIX", "mapping_basis": "PARTIAL_HELP_EVIDENCE_BOUNDARY", "mapping_confidence": "HIGH", "delta_action": "ADD_PARTIAL_HELP_APPENDIX_ENTRY", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text}
    review = STRUCTURAL_REVIEW_DISPOSITIONS.get(row.get("topic_key", ""))
    if review:
        return {"target_slug": review[0], "target_kind": "EXISTING_SECTION", "mapping_basis": "EXPLICIT_STRUCTURAL_REVIEW_DISPOSITION", "mapping_confidence": review[1], "delta_action": "RESOLVE_STRUCTURAL_REVIEW_TOPIC", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text, "structural_review_rationale": review[2]}
    if catalog == "FOX":
        target = "legacy_and_compatibility_surfaces"
        return {"target_slug": target, "target_kind": "EXISTING_SECTION", "mapping_basis": "FOX_CATALOG_COMPATIBILITY_BOUNDARY", "mapping_confidence": "HIGH", "delta_action": "REFRESH_EXISTING_TOPIC" if target in exact else "ADD_COMPATIBILITY_TOPIC", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text}
    if catalog in {"ED", "EDU", "EXT"}:
        target = "educational_and_demo_commands"
        return {"target_slug": target, "target_kind": "EXISTING_SECTION", "mapping_basis": "EDUCATION_CATALOG_BOUNDARY", "mapping_confidence": "HIGH", "delta_action": "REFRESH_EXISTING_TOPIC" if target in exact else "ADD_EDUCATION_TOPIC", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text}
    if catalog == "UI":
        target = "command_surface_dispatch_and_entry_variants"
        return {"target_slug": target, "target_kind": "EXISTING_SECTION", "mapping_basis": "UI_ENTRY_SURFACE_BOUNDARY", "mapping_confidence": "HIGH", "delta_action": "REFRESH_EXISTING_TOPIC" if target in exact else "ADD_UI_ENTRY_TOPIC", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text}
    if exact:
        return {"target_slug": exact[0], "target_kind": "EXISTING_SECTION", "mapping_basis": "EXACT_EXISTING_COMMAND_ASSIGNMENT", "mapping_confidence": "HIGH", "delta_action": "REFRESH_EXISTING_TOPIC", "existing_assignments": ";".join(exact), "existing_appendix_assignments": appendix_text}
    family = _family_target(topic)
    if family:
        return {"target_slug": family[0], "target_kind": "EXISTING_SECTION", "mapping_basis": family[1], "mapping_confidence": "MEDIUM", "delta_action": "ADD_FAMILY_TOPIC", "existing_assignments": "", "existing_appendix_assignments": appendix_text}
    if appendix_exact:
        return {"target_slug": "command_reference_assembly_aliases_and_generated_page_hygiene", "target_kind": "EXISTING_SECTION", "mapping_basis": "EXISTING_REVIEW_APPENDIX_RECURATION", "mapping_confidence": "REVIEW", "delta_action": "RECURATE_EXISTING_APPENDIX_TOPIC", "existing_assignments": "", "existing_appendix_assignments": appendix_text}
    return {"target_slug": "command_reference_assembly_aliases_and_generated_page_hygiene", "target_kind": "EXISTING_SECTION", "mapping_basis": "SAFE_COMMAND_REFERENCE_REVIEW_FALLBACK", "mapping_confidence": "REVIEW", "delta_action": "ADD_TO_COMMAND_REFERENCE_REVIEW", "existing_assignments": "", "existing_appendix_assignments": ""}


def build_structural_reconciliation(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    disposition_dir = _latest_disposition_dir(paths)
    primary = _primary_sections(paths)
    appendices = _primary_appendices(paths)
    controlled = _controlled_sections(paths)
    media_path = paths.published_dir / MEDIA_WORKSPACE / "sections" / "media_storyboards_and_data_trail_teaching_layer.md"
    approved_path = disposition_dir / "manual_section_factory_approved_topics.csv" if disposition_dir else Path()
    disposition_manifest = disposition_dir / "manual_disposition_manifest.json" if disposition_dir else Path()
    approved = read_csv(approved_path) if disposition_dir else []
    order = {row["slug"]: int(row["ordinal"]) for row in controlled}
    assignments = _existing_assignments(primary)
    appendix_assignments = _existing_assignments(appendices)

    controlled_slugs = {row["slug"] for row in controlled}
    primary_slugs = set(primary)
    media_slugs = primary_slugs | ({"media_storyboards_and_data_trail_teaching_layer"} if media_path.exists() else set())
    union_slugs = controlled_slugs | primary_slugs | media_slugs
    title_by_slug = {row["slug"]: row["title"] for row in controlled}
    for slug in primary:
        title_by_slug.setdefault(slug, slug.replace("_", " ").title())
    title_by_slug["media_storyboards_and_data_trail_teaching_layer"] = "Media Storyboards and Data-Trail Teaching Layer"

    baseline_rows = []
    for slug in sorted(union_slugs, key=lambda item: (order.get(item, 999), item)):
        baseline_rows.append({"section_slug": slug, "title": title_by_slug.get(slug, slug), "primary_24": 1 if slug in primary_slugs else 0, "media_revision_25": 1 if slug in media_slugs else 0, "controlled_runtime_25": 1 if slug in controlled_slugs else 0, "controlled_ordinal": order.get(slug, ""), "structural_role": "COMMON_CORE" if slug in primary_slugs else ("MEDIA_OVERLAY" if slug.startswith("media_storyboards") else "RUNTIME_INVOCATION_OVERLAY")})

    mapping_rows = []
    for row in approved:
        mapping = _choose_mapping(row, assignments, order, appendix_assignments)
        mapping.setdefault("structural_review_rationale", "")
        mapping_rows.append({"topic_key": row.get("topic_key", ""), "catalog": row.get("catalog", ""), "topic": row.get("topic", ""), "status": row.get("status", ""), "source_group": row.get("section_group", ""), "approval_basis": row.get("approval_basis", ""), "disposition": row.get("disposition", ""), **mapping})

    targets = set(union_slugs) | {PARTIAL_HELP_APPENDIX}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mapping_rows:
        grouped[row["target_slug"]].append(row)
    section_delta_rows = []
    for slug in sorted(targets, key=lambda item: (order.get(item, 999), item)):
        rows = grouped.get(slug, [])
        counts: dict[str, int] = defaultdict(int)
        for row in rows:
            counts[row["delta_action"]] += 1
        section_delta_rows.append({"target_slug": slug, "target_kind": "NEW_CANDIDATE_APPENDIX" if slug == PARTIAL_HELP_APPENDIX else "EXISTING_SECTION", "topic_delta_count": len(rows), "refresh_existing_count": counts["REFRESH_EXISTING_TOPIC"], "add_topic_count": len(rows) - counts["REFRESH_EXISTING_TOPIC"], "review_fallback_count": sum(row["mapping_confidence"] == "REVIEW" for row in rows), "proposed_section_action": "PRESERVE_NO_TOPIC_DELTA" if not rows else ("ADD_CANDIDATE_APPENDIX" if slug == PARTIAL_HELP_APPENDIX else "MERGE_TOPIC_DELTA"), "replacement_authorized": 0})

    missing_targets = [row for row in mapping_rows if row["target_slug"] not in targets]
    duplicate_keys = len(mapping_rows) - len({row["topic_key"] for row in mapping_rows})
    review_fallbacks = sum(row["mapping_confidence"] == "REVIEW" for row in mapping_rows)
    exact_mentions = sum(bool(row["existing_assignments"]) for row in mapping_rows)
    appendix_mentions = sum(bool(row["existing_appendix_assignments"]) for row in mapping_rows)
    appendix_recurations = sum(row["delta_action"] == "RECURATE_EXISTING_APPENDIX_TOPIC" for row in mapping_rows)
    unplaced_fallbacks = sum(row["delta_action"] == "ADD_TO_COMMAND_REFERENCE_REVIEW" for row in mapping_rows)
    resolved_review_rows = [row for row in mapping_rows if row["delta_action"] == "RESOLVE_STRUCTURAL_REVIEW_TOPIC"]
    invalid_review_targets = [key for key, policy in STRUCTURAL_REVIEW_DISPOSITIONS.items() if policy[0] not in targets]
    missing_review_topics = sorted(set(STRUCTURAL_REVIEW_DISPOSITIONS) - {row["topic_key"] for row in resolved_review_rows})
    status = "PASS" if disposition_dir and len(primary) == 24 and len(appendices) == 3 and len(controlled) == 25 and len(media_slugs) == 25 and len(union_slugs) == 26 and len(approved) == 462 and len(mapping_rows) == 462 and len(STRUCTURAL_REVIEW_DISPOSITIONS) == 13 and len(resolved_review_rows) == 13 and not review_fallbacks and not unplaced_fallbacks and not invalid_review_targets and not missing_review_topics and not duplicate_keys and not missing_targets else "FAIL"

    run_id = logger.run_id if logger else "MANRUN-STRUCTURAL-RECONCILIATION"
    output_dir = paths.manualgen_root / "generated" / "manualgen_structural_reconciliations" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = output_dir / "manual_structural_baseline_ledger.csv"
    mapping_path = output_dir / "manual_topic_structural_mapping.csv"
    delta_path = output_dir / "manual_section_delta_ledger.csv"
    review_path = output_dir / "manual_structural_review_disposition_ledger.csv"
    proposal_path = output_dir / "manual_structural_delta_proposal.md"
    manifest_path = output_dir / "manual_structural_reconciliation_manifest.json"
    write_csv(baseline_path, baseline_rows)
    write_csv(mapping_path, mapping_rows)
    write_csv(delta_path, section_delta_rows)
    write_csv(review_path, resolved_review_rows)

    proposal = ["<!-- Candidate-only structural reconciliation. Not publication. -->", "# Developer Manual Structural Delta Proposal", "", f"Status: `{status}`", "", "## Baseline resolution", "", "- Primary reader body: 24 common-core sections.", "- Media revision: 25 sections (24 common core plus the media/storyboard teaching layer).", "- Controlled runtime/MAN-CLI comparison body: 25 sections (24 common core plus Runtime Operation, Invocation, and Automation).", "- Union of governed section surfaces: 26.", "- The primary reader pointer remains unchanged.", "", "## Proposal doctrine", "", "- Preserve all existing sections; no wholesale replacement is proposed or authorized.", "- Merge refreshed topic evidence into existing sections after human review.", "- Keep FOX material inside the compatibility boundary.", "- Keep partial HELP evidence in a candidate appendix until runtime identity is established.", "- Treat REVIEW-confidence fallback rows as a curation queue, not automatic placement authority.", "", "## Section deltas", "", "| Target | Topics | Refresh | Add | Review fallback | Proposal |", "|---|---:|---:|---:|---:|---|"]
    for row in section_delta_rows:
        proposal.append(f"| `{row['target_slug']}` | {row['topic_delta_count']} | {row['refresh_existing_count']} | {row['add_topic_count']} | {row['review_fallback_count']} | `{row['proposed_section_action']}` |")
    proposal.extend(["", "## Gate result", "", f"- Approved topics mapped: {len(mapping_rows)}/{len(approved)}.", f"- Topics already named in an existing section command list: {exact_mentions}.", f"- Topics also named in one of three review appendices: {appendix_mentions}.", f"- Structural review dispositions: {len(resolved_review_rows)}/13.", f"- Remaining review-confidence topics: {review_fallbacks}.", f"- Remaining unplaced fallbacks: {unplaced_fallbacks}.", f"- Missing structural targets: {len(missing_targets)}.", f"- Duplicate topic keys: {duplicate_keys}.", "- Canonical manual mutation: 0.", "- Reader-pointer mutation: 0.", "- Publication authority claimed: 0.", "", "Next gate: generate per-section additive delta drafts from the accepted mapping; section replacement and publication remain separately gated."])
    proposal_path.write_text("\n".join(proposal) + "\n", encoding="utf-8")

    action_counts: dict[str, int] = defaultdict(int)
    for row in mapping_rows:
        action_counts[row["delta_action"]] += 1
    manifest = {"schema": "dottalk.manualgen.structural_reconciliation_candidate.v1", "created_utc": utc_now_iso(), "manualgen_version": __version__, "run_id": run_id, "status": status, "candidate_only": 1, "publication_authority_claimed": 0, "canonical_manual_mutated": 0, "reader_pointer_mutated": 0, "input": {"disposition_run_id": disposition_dir.name if disposition_dir else "", "approved_topics": relpath_posix(approved_path, paths.repo_root) if disposition_dir else "", "approved_topics_sha256": sha256_file(approved_path) if disposition_dir else "", "disposition_manifest": relpath_posix(disposition_manifest, paths.repo_root) if disposition_dir else "", "disposition_manifest_sha256": sha256_file(disposition_manifest) if disposition_dir else ""}, "counts": {"primary_sections": len(primary_slugs), "primary_appendices": len(appendices), "media_revision_sections": len(media_slugs), "controlled_runtime_sections": len(controlled_slugs), "union_section_surfaces": len(union_slugs), "approved_topics": len(approved), "mapped_topics": len(mapping_rows), "exact_existing_section_mentions": exact_mentions, "exact_existing_appendix_mentions": appendix_mentions, "structural_review_policy_rows": len(STRUCTURAL_REVIEW_DISPOSITIONS), "structural_review_resolved_rows": len(resolved_review_rows), "review_fallback_topics": review_fallbacks, "appendix_recuration_topics": appendix_recurations, "unplaced_fallback_topics": unplaced_fallbacks, "invalid_review_targets": len(invalid_review_targets), "missing_review_topics": len(missing_review_topics), "duplicate_topic_keys": duplicate_keys, "missing_structural_targets": len(missing_targets)}, "delta_action_counts": dict(sorted(action_counts.items())), "artifacts": {}}
    for key, path in {"baseline_ledger": baseline_path, "topic_mapping": mapping_path, "section_delta_ledger": delta_path, "review_disposition_ledger": review_path, "delta_proposal": proposal_path}.items():
        manifest["artifacts"][key] = relpath_posix(path, paths.repo_root)
        manifest["artifacts"][f"{key}_sha256"] = sha256_file(path)
    write_json(manifest_path, manifest)

    if logger:
        logger.artifact("manual_structural_baseline_ledger", baseline_path, "Primary, media, and controlled-runtime section topology.")
        logger.artifact("manual_topic_structural_mapping", mapping_path, "All approved topics mapped to governed structural targets.")
        logger.artifact("manual_section_delta_ledger", delta_path, "Non-replacement per-section delta summary.")
        logger.artifact("manual_structural_review_disposition_ledger", review_path, "Explicit evidence-backed dispositions for all 13 structural review topics.")
        logger.artifact("manual_structural_delta_proposal", proposal_path, "Human-readable structural reconciliation proposal.")
        logger.artifact("manual_structural_reconciliation_manifest", manifest_path, "Structural reconciliation manifest.")
        for boundary in ("canonical_manual_mutated", "reader_pointer_mutated", "publication_authority_claimed", "source_help_metadata_mutated"):
            logger.boundary(boundary, 0, "PASS", "Candidate-only reconciliation does not cross this boundary.")

    state = {"created": 1, "status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "manifest": relpath_posix(manifest_path, paths.repo_root), "proposal": relpath_posix(proposal_path, paths.repo_root)}
    return state, manifest["counts"]
