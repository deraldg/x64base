#!/usr/bin/env python3
"""PHASE23I HELP locale companion schema staging.

Candidate-only behavior:
- Reads PHASE23H planning output when present.
- Stages exact candidate schemas for HELP locale companion tables.
- Stages CMDHELPCHK locale validation contracts.
- Stages MAINT/BBOX lane wording for LOCALE and HELP_LOCALE.
- Writes only under docs/locale/candidates/PHASE23I-HELP-LOCALE-COMPANION-SCHEMA-STAGING.
- Does not mutate active HELP DATA, source, CMDHELP, CMDHELPCHK, DBF, CDX, LMDB, workspace schemas, or latest pointers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Any

PHASE = "PHASE23I"
PHASE_SLUG = "PHASE23I-HELP-LOCALE-COMPANION-SCHEMA-STAGING"
STATUS_GREEN = "PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING_GREEN_CANDIDATE_ONLY_MAINT_BBOX_PLAN_INCLUDED"
STATUS_REVIEW = "PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING_REVIEW_REQUIRED_CANDIDATE_ONLY"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23J_HELP_LOCALE_SAMPLE_ROW_MATERIALIZATION_PLAN"
PREV_PHASE_SLUG = "PHASE23H-HELP-LOCALE-CONSUMER-INTEGRATION-PLAN"

ACTIVE_MUTATION_ROOTS = [
    "src",
    "include",
    "dottalkpp/data/help",
    "dottalkpp/data/indexes/help",
    "dottalkpp/data/lmdb/help",
    "dottalkpp/data/HELP",
    "dottalkpp/data/INDEXES/HELP",
    "dottalkpp/data/LMDB/HELP",
    "docs/help",
    "docs/cmdhelpchk",
]

CANONICAL_HELP_TABLES = ["HELP_TOPIC", "HELP_SECTION", "HELP_LINE", "HELP_ARTIFACTS"]
STARTER_LOCALES = [
    ("en-US", "en-US", "ltr", "source", "Base/source locale."),
    ("es", "en-US", "ltr", "starter", "Spanish starter locale."),
    ("fr", "en-US", "ltr", "starter", "French starter locale."),
    ("de", "en-US", "ltr", "starter", "German starter locale."),
    ("it", "en-US", "ltr", "starter", "Italian starter locale."),
]

@dataclass(frozen=True)
class FieldSpec:
    table: str
    ordinal: int
    field: str
    dbf_type: str
    width: int
    decimals: int
    required: str
    key_role: str
    description: str

@dataclass(frozen=True)
class TagSpec:
    table: str
    tag: str
    expression: str
    unique: str
    purpose: str

@dataclass(frozen=True)
class TableSpec:
    table: str
    parent_table: str
    purpose: str
    canonical_join: str
    primary_key: str
    candidate_only: str

@dataclass(frozen=True)
class CheckSpec:
    check_id: str
    severity: str
    target_table: str
    description: str
    green_condition: str

@dataclass(frozen=True)
class LaneSpec:
    lane: str
    owner: str
    purpose: str
    read_only_first_surface: str
    mutation_policy: str

TABLES: list[TableSpec] = [
    TableSpec(
        "HELP_TOPIC_LOCALE",
        "HELP_TOPIC",
        "Localized topic title/summary metadata attached to canonical HELP topic identity.",
        "TOPICKEY + LOCALE_ID",
        "TOPICKEY + LOCALE_ID",
        "yes",
    ),
    TableSpec(
        "HELP_SECTION_LOCALE",
        "HELP_SECTION",
        "Localized section headings and display labels attached to canonical HELP section identity.",
        "TOPICKEY + SECTION_ID + LOCALE_ID",
        "TOPICKEY + SECTION_ID + LOCALE_ID",
        "yes",
    ),
    TableSpec(
        "HELP_LINE_LOCALE",
        "HELP_LINE",
        "Localized HELP body lines tied to stable canonical line identity and source hash.",
        "TOPICKEY + SECTION_ID + LINE_ID + LOCALE_ID",
        "TOPICKEY + SECTION_ID + LINE_ID + LOCALE_ID",
        "yes",
    ),
    TableSpec(
        "HELP_ARTIFACT_LOCALE",
        "HELP_ARTIFACTS",
        "Localized artifact labels/descriptions without duplicating canonical artifacts.",
        "ARTIFACT_ID + LOCALE_ID",
        "ARTIFACT_ID + LOCALE_ID",
        "yes",
    ),
]

COMMON_FIELDS: list[tuple[str, str, int, int, str, str, str]] = [
    ("LOCALE_ID", "C", 16, 0, "yes", "locale", "Locale key from SYSTEM_LOCALES."),
    ("SOURCE_LOCALE", "C", 16, 0, "yes", "source_locale", "Locale of canonical/source text; normally en-US."),
    ("TEXT_DIR", "C", 8, 0, "yes", "rendering", "Text direction such as ltr or rtl."),
    ("LOCAL_TEXT", "M", 10, 0, "yes", "payload", "Localized text payload."),
    ("SOURCE_HASH", "C", 64, 0, "yes", "stale_guard", "Hash of canonical source text and identity."),
    ("LOCAL_HASH", "C", 64, 0, "yes", "stale_guard", "Hash of localized text payload."),
    ("TRANSL_STATUS", "C", 16, 0, "yes", "workflow", "missing, draft, machine, reviewed, approved, stale."),
    ("REVIEW_STATUS", "C", 16, 0, "yes", "workflow", "unreviewed, reviewed, approved, rejected."),
    ("REVIEWED_BY", "C", 64, 0, "no", "workflow", "Optional reviewer id."),
    ("REVIEWED_AT", "C", 32, 0, "no", "workflow", "ISO timestamp for review."),
    ("FALLBACK_ALLOWED", "L", 1, 0, "yes", "fallback", "Whether fallback may satisfy this row."),
    ("FALLBACK_FROM", "C", 16, 0, "no", "fallback", "Locale used when this row is produced by fallback/projection."),
    ("CREATED_AT", "C", 32, 0, "yes", "audit", "ISO timestamp for candidate row creation."),
    ("UPDATED_AT", "C", 32, 0, "yes", "audit", "ISO timestamp for last candidate update."),
]

SPECIFIC_KEY_FIELDS: dict[str, list[tuple[str, str, int, int, str, str, str]]] = {
    "HELP_TOPIC_LOCALE": [
        ("TOPICKEY", "C", 96, 0, "yes", "parent_key", "Canonical HELP_TOPIC topic key."),
        ("TOPIC_LABEL", "C", 160, 0, "no", "display", "Optional localized topic display label."),
    ],
    "HELP_SECTION_LOCALE": [
        ("TOPICKEY", "C", 96, 0, "yes", "parent_key", "Canonical HELP_SECTION topic key."),
        ("SECTION_ID", "N", 10, 0, "yes", "parent_key", "Canonical HELP_SECTION section id/ordinal."),
        ("KIND", "C", 32, 0, "no", "classification", "Section kind, such as SUMMARY, USAGE, SYNTAX, NOTE."),
        ("SECTION_LABEL", "C", 160, 0, "no", "display", "Optional localized section heading."),
    ],
    "HELP_LINE_LOCALE": [
        ("TOPICKEY", "C", 96, 0, "yes", "parent_key", "Canonical HELP_LINE topic key."),
        ("SECTION_ID", "N", 10, 0, "yes", "parent_key", "Canonical section id/ordinal."),
        ("LINE_ID", "N", 10, 0, "yes", "parent_key", "Canonical line id/ordinal."),
        ("KIND", "C", 32, 0, "no", "classification", "Line kind inherited from HELP_LINE."),
        ("ROLE", "C", 32, 0, "no", "classification", "Line role inherited from HELP_LINE."),
    ],
    "HELP_ARTIFACT_LOCALE": [
        ("ARTIFACT_ID", "C", 96, 0, "yes", "parent_key", "Canonical HELP_ARTIFACTS artifact id."),
        ("TOPICKEY", "C", 96, 0, "no", "parent_key", "Optional related topic key."),
        ("ARTIFACT_LABEL", "C", 160, 0, "no", "display", "Localized artifact label."),
    ],
}

TAGS: list[TagSpec] = [
    TagSpec("HELP_TOPIC_LOCALE", "TOPIC_LOCALE", "TOPICKEY + LOCALE_ID", "yes", "Unique localized topic row."),
    TagSpec("HELP_TOPIC_LOCALE", "LOCALE_TOPIC", "LOCALE_ID + TOPICKEY", "no", "Locale-first topic browsing."),
    TagSpec("HELP_SECTION_LOCALE", "SECTION_LOCALE", "TOPICKEY + STR(SECTION_ID) + LOCALE_ID", "yes", "Unique localized section row."),
    TagSpec("HELP_SECTION_LOCALE", "LOCALE_SECTION", "LOCALE_ID + TOPICKEY + STR(SECTION_ID)", "no", "Locale-first section browsing."),
    TagSpec("HELP_LINE_LOCALE", "LINE_LOCALE", "TOPICKEY + STR(SECTION_ID) + STR(LINE_ID) + LOCALE_ID", "yes", "Unique localized line row."),
    TagSpec("HELP_LINE_LOCALE", "LOCALE_LINE", "LOCALE_ID + TOPICKEY + STR(SECTION_ID) + STR(LINE_ID)", "no", "Locale-first line browsing."),
    TagSpec("HELP_LINE_LOCALE", "SOURCE_HASH", "SOURCE_HASH", "no", "Stale-translation scan."),
    TagSpec("HELP_ARTIFACT_LOCALE", "ART_LOCALE", "ARTIFACT_ID + LOCALE_ID", "yes", "Unique localized artifact row."),
    TagSpec("HELP_ARTIFACT_LOCALE", "LOCALE_ART", "LOCALE_ID + ARTIFACT_ID", "no", "Locale-first artifact browsing."),
]

CHECKS: list[CheckSpec] = [
    CheckSpec("LOCALE_ID_VALID", "FAIL", "ALL", "Localized HELP rows must reference SYSTEM_LOCALES.", "0 invalid LOCALE_ID rows."),
    CheckSpec("FALLBACK_PATH_VALID", "FAIL", "ALL", "Requested locales must have reachable SYSTEM_LOCALE_FALLBACK chain.", "0 broken fallback chains."),
    CheckSpec("SOURCE_HASH_MATCH", "WARN", "ALL", "Localized rows become stale when canonical HELP source hash changes.", "0 stale rows for release locales."),
    CheckSpec("ORPHAN_LOCALIZED_ROW", "FAIL", "ALL", "Localized rows must have live canonical parent rows.", "0 orphan localized rows."),
    CheckSpec("MISSING_REQUIRED_TRANSLATION", "WARN", "HELP_LINE_LOCALE", "Required user-facing lines should exist for target release locales.", "0 missing required rows for release locale, or documented fallback."),
    CheckSpec("TEXT_DIR_COMPAT", "WARN", "ALL", "TEXT_DIR must be known before rendering locale-specific output.", "All rows inherit ltr/rtl from SYSTEM_LOCALES."),
    CheckSpec("REVIEW_STATUS_READY", "WARN", "ALL", "Release locale rows require reviewed or approved status.", "No unreviewed release rows."),
    CheckSpec("DUPLICATE_LOCALE_ROW", "FAIL", "ALL", "No duplicate localized row for same canonical key and LOCALE_ID.", "0 duplicates by unique tag contract."),
]

LANES: list[LaneSpec] = [
    LaneSpec("LOCALE", "shared locale spine", "Own SYSTEM_LOCALES and SYSTEM_LOCALE_FALLBACK for all consumers.", "MAINT LOCALE / CMDHELP LOCALES candidate report", "report-first; explicit authorization for active catalog mutation"),
    LaneSpec("HELP_LOCALE", "HELP consumer of shared locale spine", "Own localized HELP companion rows and fallback/readback contracts.", "CMDHELPCHK LOCALE <locale> candidate report", "candidate-only until DBF/CDX/LMDB readback is green"),
    LaneSpec("MESSAGING", "message catalog", "Own typed localized runtime message symbols and placeholder rendering.", "SET MESSAGE CATALOG CHECK", "seam-by-seam message migration, no command keyword localization"),
    LaneSpec("MAINT", "maintenance governance", "Report lane status, boundaries, cookbooks, and next gates.", "MAINT STATUS / MAINT LANES / MAINT BBOX", "read-only first wave; no script execution by default"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except ValueError:
        return str(path).replace("/", "\\")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def get_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def candidate_dir_for(root: Path) -> Path:
    return root / "docs" / "locale" / "candidates" / PHASE_SLUG


def previous_phase_status(root: Path) -> dict[str, Any]:
    prev = root / "docs" / "locale" / "candidates" / PREV_PHASE_SLUG
    result: dict[str, Any] = {
        "phase23h_candidate_dir_exists": prev.exists(),
        "phase23h_manifest_found": False,
        "phase23h_status": "not_found",
        "phase23h_green": False,
    }
    if not prev.exists():
        return result
    manifests = list(prev.glob("*.json"))
    for m in manifests:
        try:
            data = json.loads(m.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        status = str(data.get("status", ""))
        if "PHASE23H" in status:
            result["phase23h_manifest_found"] = True
            result["phase23h_status"] = status
            result["phase23h_manifest"] = rel(m, root)
            result["phase23h_green"] = "GREEN" in status and "REPORT_ONLY" in status
            return result
    return result


def count_existing_surfaces(root: Path) -> dict[str, Any]:
    paths = {
        "active_help_dbf_dir": root / "dottalkpp" / "data" / "help",
        "active_help_indexes_dir": root / "dottalkpp" / "data" / "indexes" / "help",
        "active_help_lmdb_dir": root / "dottalkpp" / "data" / "lmdb" / "help",
        "locale_docs_dir": root / "docs" / "locale",
        "cmdhelp_sources_hint": root / "src",
    }
    help_dbfs = list(paths["active_help_dbf_dir"].glob("*.dbf")) if paths["active_help_dbf_dir"].exists() else []
    result = {k + "_exists": v.exists() for k, v in paths.items()}
    result.update({
        "active_help_dbf_count": len(help_dbfs),
        "canonical_help_tables_planned": len(CANONICAL_HELP_TABLES),
        "starter_locale_rows_planned": len(STARTER_LOCALES),
        "companion_tables_planned": len(TABLES),
        "schema_fields_planned": sum(len(SPECIFIC_KEY_FIELDS[t.table]) + len(COMMON_FIELDS) for t in TABLES),
        "tags_planned": len(TAGS),
        "cmdhelpchk_locale_checks_planned": len(CHECKS),
        "maint_bbox_lane_rows_planned": len(LANES),
    })
    return result


def build_fields() -> list[FieldSpec]:
    fields: list[FieldSpec] = []
    for table in TABLES:
        ordinal = 1
        for name, typ, width, dec, req, role, desc in SPECIFIC_KEY_FIELDS[table.table]:
            fields.append(FieldSpec(table.table, ordinal, name, typ, width, dec, req, role, desc))
            ordinal += 1
        for name, typ, width, dec, req, role, desc in COMMON_FIELDS:
            fields.append(FieldSpec(table.table, ordinal, name, typ, width, dec, req, role, desc))
            ordinal += 1
    return fields


def boundary_rows(candidate_dir: Path, root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed = rel(candidate_dir, root)
    rows.append({
        "boundary": "candidate_output_root",
        "path": allowed,
        "policy": "writes allowed for PHASE23I candidate artifacts only",
        "status": "ALLOW",
    })
    for item in ACTIVE_MUTATION_ROOTS:
        rows.append({
            "boundary": "protected_active_root",
            "path": item,
            "policy": "must not be written by PHASE23I package",
            "status": "HELD",
        })
    return rows


def markdown_plan(status: str, prev: dict[str, Any], surface: dict[str, Any], manifest_hash: str) -> str:
    lines: list[str] = []
    lines.append("# PHASE23I HELP Locale Companion Schema Staging")
    lines.append("")
    lines.append(f"Status: `{status}`")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Stage exact candidate schemas for localized HELP companion rows, plus CMDHELPCHK locale checks and MAINT/BBOX lane wording. Canonical HELP remains source-owned and rebuildable; localized HELP attaches through companion rows keyed to canonical HELP identities and shared locale-spine rows.")
    lines.append("")
    lines.append("## Preconditions")
    lines.append("")
    lines.append(f"- PHASE23H candidate directory exists: `{prev.get('phase23h_candidate_dir_exists')}`")
    lines.append(f"- PHASE23H green manifest found: `{prev.get('phase23h_green')}`")
    lines.append(f"- PHASE23H status observed: `{prev.get('phase23h_status')}`")
    lines.append("")
    lines.append("## Proposed companion tables")
    lines.append("")
    lines.append("| Table | Parent | Primary key | Purpose |")
    lines.append("|---|---|---|---|")
    for t in TABLES:
        lines.append(f"| {t.table} | {t.parent_table} | {t.primary_key} | {t.purpose} |")
    lines.append("")
    lines.append("## Shared row contract")
    lines.append("")
    lines.append("Every localized row includes `LOCALE_ID`, `SOURCE_LOCALE`, `TEXT_DIR`, `LOCAL_TEXT`, `SOURCE_HASH`, `LOCAL_HASH`, `TRANSL_STATUS`, `REVIEW_STATUS`, review metadata, and fallback metadata. `SOURCE_HASH` is the stale-translation guard after `CMDHELP BUILD` refreshes canonical HELP.")
    lines.append("")
    lines.append("## CMDHELPCHK locale checks")
    lines.append("")
    for c in CHECKS:
        lines.append(f"- `{c.check_id}` ({c.severity}): {c.description}")
    lines.append("")
    lines.append("## MAINT/BBOX lane additions")
    lines.append("")
    lines.append("PHASE23I stages wording only. Runtime command text is not changed in this package.")
    lines.append("")
    for lane in LANES:
        lines.append(f"- `{lane.lane}`: {lane.purpose}")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("PHASE23I writes candidate planning artifacts only under `docs\\locale\\candidates\\PHASE23I-HELP-LOCALE-COMPANION-SCHEMA-STAGING`. It does not create active DBF/CDX/LMDB tables, change CMDHELP/CMDHELPCHK/MAINT/BBOX runtime behavior, modify source files, or alter latest pointers.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    for key in sorted(surface):
        lines.append(f"- {key}: `{surface[key]}`")
    lines.append("")
    lines.append(f"Manifest hash: `{manifest_hash}`")
    lines.append("")
    lines.append(f"Next gate: `{NEXT_GATE}`")
    lines.append("")
    return "\n".join(lines)


def run(repo_root: Path) -> int:
    root = repo_root.resolve()
    candidate_dir = candidate_dir_for(root)
    candidate_dir.mkdir(parents=True, exist_ok=True)

    previous = previous_phase_status(root)
    surface = count_existing_surfaces(root)
    fields = build_fields()
    status = STATUS_GREEN if previous.get("phase23h_green") else STATUS_REVIEW

    table_rows = [asdict(t) for t in TABLES]
    field_rows = [asdict(f) for f in fields]
    tag_rows = [asdict(t) for t in TAGS]
    check_rows = [asdict(c) for c in CHECKS]
    lane_rows = [asdict(l) for l in LANES]
    locale_rows = [
        {
            "locale_id": loc,
            "source_locale": src,
            "text_dir": text_dir,
            "role": role,
            "note": note,
        }
        for loc, src, text_dir, role, note in STARTER_LOCALES
    ]
    boundary = boundary_rows(candidate_dir, root)

    write_csv(candidate_dir / "phase23i_companion_tables.csv", table_rows, list(table_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_companion_fields.csv", field_rows, list(field_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_companion_tags.csv", tag_rows, list(tag_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_cmdhelpchk_locale_checks.csv", check_rows, list(check_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_maint_bbox_lane_plan.csv", lane_rows, list(lane_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_starter_locale_rows.csv", locale_rows, list(locale_rows[0].keys()))
    write_csv(candidate_dir / "phase23i_boundary_ledger.csv", boundary, list(boundary[0].keys()))

    manifest_core = {
        "phase": PHASE,
        "status": status,
        "created_at_utc": now_iso(),
        "repo_root": str(root),
        "candidate_dir": rel(candidate_dir, root),
        "previous_phase": previous,
        "surface_inventory": surface,
        "canonical_help_tables": CANONICAL_HELP_TABLES,
        "starter_locales": locale_rows,
        "proposed_companion_tables": table_rows,
        "field_count": len(field_rows),
        "tag_count": len(tag_rows),
        "cmdhelpchk_locale_checks": check_rows,
        "maint_bbox_lane_plan": lane_rows,
        "boundary": {
            "candidate_only": True,
            "source_files_written": 0,
            "active_help_dbf_written": 0,
            "active_help_cdx_written": 0,
            "active_help_lmdb_written": 0,
            "cmdhelp_behavior_changed": 0,
            "cmdhelpchk_behavior_changed": 0,
            "maint_behavior_changed": 0,
            "bbox_behavior_changed": 0,
            "latest_pointer_changed": 0,
            "runtime_execution": 0,
        },
        "next_gate": NEXT_GATE,
    }
    content_hash = sha256_text(json.dumps(manifest_core, sort_keys=True))
    manifest = dict(manifest_core)
    manifest["manifest_hash"] = content_hash
    manifest_path = candidate_dir / "phase23i_manifest.json"
    write_json(manifest_path, manifest)

    md = markdown_plan(status, previous, surface, content_hash)
    md_path = candidate_dir / "PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING.md"
    md_path.write_text(md, encoding="utf-8")

    file_manifest_rows = []
    for p in sorted(candidate_dir.glob("*")):
        if p.is_file():
            file_manifest_rows.append({
                "file": rel(p, root),
                "bytes": p.stat().st_size,
                "sha256": get_file_hash(p),
            })
    write_csv(candidate_dir / "phase23i_file_manifest.csv", file_manifest_rows, ["file", "bytes", "sha256"])

    print(status)
    print(f"candidate_dir: {rel(candidate_dir, root)}")
    print(f"phase23h_green: {1 if previous.get('phase23h_green') else 0}")
    print(f"companion_tables: {len(table_rows)}")
    print(f"companion_fields: {len(field_rows)}")
    print(f"companion_tags: {len(tag_rows)}")
    print(f"cmdhelpchk_locale_checks: {len(check_rows)}")
    print(f"maint_bbox_lane_rows: {len(lane_rows)}")
    print(f"starter_locale_rows: {len(locale_rows)}")
    print("source_files_written: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print(f"next_gate: {NEXT_GATE}")
    return 0 if status == STATUS_GREEN else 2


def main() -> int:
    parser = argparse.ArgumentParser(description="PHASE23I HELP locale companion schema staging")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    args = parser.parse_args()
    return run(Path(args.repo_root))

if __name__ == "__main__":
    raise SystemExit(main())
