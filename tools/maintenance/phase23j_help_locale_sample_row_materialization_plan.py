#!/usr/bin/env python3
"""
PHASE23J HELP locale sample row materialization plan.

Candidate-only planner. It stages sample HELP locale rows for a small proof set
of topics and starter locales. It does not create active DBF/CDX/LMDB tables,
change CMDHELP/CMDHELPCHK/MAINT/BBOX behavior, or mutate source files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

STATUS = "PHASE23J_HELP_LOCALE_SAMPLE_ROW_MATERIALIZATION_PLAN_GREEN_CANDIDATE_ONLY"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF"
PHASE23I_STATUS = "PHASE23I_HELP_LOCALE_COMPANION_SCHEMA_STAGING_GREEN_CANDIDATE_ONLY_MAINT_BBOX_PLAN_INCLUDED"

STARTER_LOCALES = [
    {"LOCALE_ID": "en-US", "TEXT_DIR": "LTR", "BASE_LOCALE": "en", "TRANSL_STATUS": "SOURCE_CANONICAL"},
    {"LOCALE_ID": "es", "TEXT_DIR": "LTR", "BASE_LOCALE": "es", "TRANSL_STATUS": "DRAFT_PLACEHOLDER"},
    {"LOCALE_ID": "fr", "TEXT_DIR": "LTR", "BASE_LOCALE": "fr", "TRANSL_STATUS": "DRAFT_PLACEHOLDER"},
    {"LOCALE_ID": "de", "TEXT_DIR": "LTR", "BASE_LOCALE": "de", "TRANSL_STATUS": "DRAFT_PLACEHOLDER"},
    {"LOCALE_ID": "it", "TEXT_DIR": "LTR", "BASE_LOCALE": "it", "TRANSL_STATUS": "DRAFT_PLACEHOLDER"},
]

TOPICS = [
    {
        "TOPICKEY": "DOT|AREA",
        "COMMAND": "AREA",
        "TITLE": "AREA",
        "SUMMARY": "Report the current work-area slot and current area file/session state.",
        "USAGE": "AREA",
        "NOTE": "AREA is read-only; it reports current area state and does not mutate table data.",
    },
    {
        "TOPICKEY": "DOT|ABOUT",
        "COMMAND": "ABOUT",
        "TITLE": "ABOUT",
        "SUMMARY": "Print DotTalk++ project identity, lineage, build/runtime information, and current session summary.",
        "USAGE": "ABOUT",
        "NOTE": "Use ABOUT to inspect the current build/runtime identity without mutating data.",
    },
    {
        "TOPICKEY": "DOT|CMDHELP",
        "COMMAND": "CMDHELP",
        "TITLE": "CMDHELP",
        "SUMMARY": "Report current generated HELP DATA and display command or topic help.",
        "USAGE": "CMDHELP [USAGE] [<topic>]",
        "NOTE": "CMDHELP reads generated HELP DATA; CMDHELP BUILD is the explicit rebuild path.",
    },
    {
        "TOPICKEY": "DOT|SET LANGUAGE",
        "COMMAND": "SET LANGUAGE",
        "TITLE": "SET LANGUAGE",
        "SUMMARY": "Select or report the runtime message language.",
        "USAGE": "SET LANGUAGE [TO] <en-US|es|fr|de|it|DEFAULT>",
        "NOTE": "SET LANGUAGE selects message text templates; it does not localize command keywords.",
    },
    {
        "TOPICKEY": "DOT|SET LOCALE",
        "COMMAND": "SET LOCALE",
        "TITLE": "SET LOCALE",
        "SUMMARY": "Select or report the runtime message locale.",
        "USAGE": "SET LOCALE [TO] <en-US|es|fr|de|it|DEFAULT>",
        "NOTE": "SET LOCALE should share the same locale spine used by messages and localized HELP.",
    },
]

LABELS = {
    "en-US": {
        "prefix": "",
        "summary_label": "SUMMARY",
        "usage_label": "USAGE",
        "note_label": "NOTE",
    },
    "es": {
        "prefix": "[es draft] ",
        "summary_label": "RESUMEN",
        "usage_label": "USO",
        "note_label": "NOTA",
    },
    "fr": {
        "prefix": "[fr draft] ",
        "summary_label": "RESUME",
        "usage_label": "UTILISATION",
        "note_label": "NOTE",
    },
    "de": {
        "prefix": "[de draft] ",
        "summary_label": "ZUSAMMENFASSUNG",
        "usage_label": "VERWENDUNG",
        "note_label": "HINWEIS",
    },
    "it": {
        "prefix": "[it draft] ",
        "summary_label": "RIEPILOGO",
        "usage_label": "USO",
        "note_label": "NOTA",
    },
}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_phase23i_green(repo_root: Path) -> bool:
    candidates = repo_root / "docs" / "locale" / "candidates"
    if not candidates.exists():
        return False
    target = candidates / "PHASE23I-HELP-LOCALE-COMPANION-SCHEMA-STAGING"
    roots = [target] if target.exists() else [candidates]
    for root in roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.stat().st_size > 2_000_000:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if PHASE23I_STATUS in text:
                return True
    return False


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def localized_text(locale_id: str, source_text: str) -> str:
    info = LABELS[locale_id]
    if locale_id == "en-US":
        return source_text
    # These are review-required placeholders, deliberately not production translations.
    return info["prefix"] + source_text


def build_rows(run_id: str, created_at: str) -> Dict[str, List[Dict[str, object]]]:
    topic_rows: List[Dict[str, object]] = []
    section_rows: List[Dict[str, object]] = []
    line_rows: List[Dict[str, object]] = []
    artifact_rows: List[Dict[str, object]] = []
    fallback_rows: List[Dict[str, object]] = []

    for topic in TOPICS:
        source_topic_hash = stable_hash("|".join([topic["TOPICKEY"], topic["TITLE"], topic["SUMMARY"]]))
        source_artifact_hash = stable_hash("|".join([topic["TOPICKEY"], topic["SUMMARY"], topic["USAGE"], topic["NOTE"]]))
        for loc in STARTER_LOCALES:
            locale_id = loc["LOCALE_ID"]
            loc_info = LABELS[locale_id]
            transl_status = loc["TRANSL_STATUS"]
            review_status = "SOURCE" if locale_id == "en-US" else "NEEDS_REVIEW"
            topic_locale_id = stable_hash(f"HELP_TOPIC_LOCALE|{topic['TOPICKEY']}|{locale_id}")
            section_locale_id = stable_hash(f"HELP_SECTION_LOCALE|{topic['TOPICKEY']}|OVERVIEW|{locale_id}")
            artifact_locale_id = stable_hash(f"HELP_ARTIFACT_LOCALE|{topic['TOPICKEY']}|CMDHELP|{locale_id}")
            localized_title = localized_text(locale_id, topic["TITLE"])
            localized_summary = localized_text(locale_id, topic["SUMMARY"])
            localized_usage = localized_text(locale_id, topic["USAGE"])
            localized_note = localized_text(locale_id, topic["NOTE"])

            topic_rows.append({
                "RUN_ID": run_id,
                "TOPIC_LOCALE_ID": topic_locale_id,
                "TOPICKEY": topic["TOPICKEY"],
                "COMMAND": topic["COMMAND"],
                "LOCALE_ID": locale_id,
                "TEXT_DIR": loc["TEXT_DIR"],
                "SOURCE_TITLE": topic["TITLE"],
                "LOCALIZED_TITLE": localized_title,
                "SOURCE_HASH": source_topic_hash,
                "LOCALIZED_HASH": stable_hash(localized_title),
                "TRANSL_STATUS": transl_status,
                "REVIEW_STATUS": review_status,
                "FALLBACK_ALLOWED": 1,
                "CREATED_AT": created_at,
            })

            section_rows.append({
                "RUN_ID": run_id,
                "SECTION_LOCALE_ID": section_locale_id,
                "TOPICKEY": topic["TOPICKEY"],
                "SECTION_KEY": "OVERVIEW",
                "LOCALE_ID": locale_id,
                "SECTION_ORDER": 10,
                "SOURCE_LABEL": "OVERVIEW",
                "LOCALIZED_LABEL": localized_text(locale_id, "OVERVIEW"),
                "SOURCE_HASH": stable_hash(f"{topic['TOPICKEY']}|OVERVIEW"),
                "LOCALIZED_HASH": stable_hash(localized_text(locale_id, "OVERVIEW")),
                "TRANSL_STATUS": transl_status,
                "REVIEW_STATUS": review_status,
                "FALLBACK_ALLOWED": 1,
                "CREATED_AT": created_at,
            })

            line_defs = [
                ("SUMMARY", loc_info["summary_label"], topic["SUMMARY"], localized_summary, 10),
                ("USAGE", loc_info["usage_label"], topic["USAGE"], localized_usage, 20),
                ("NOTE", loc_info["note_label"], topic["NOTE"], localized_note, 30),
            ]
            for kind, label, source_text, loc_text, order in line_defs:
                line_rows.append({
                    "RUN_ID": run_id,
                    "LINE_LOCALE_ID": stable_hash(f"HELP_LINE_LOCALE|{topic['TOPICKEY']}|{kind}|{locale_id}"),
                    "TOPICKEY": topic["TOPICKEY"],
                    "SECTION_KEY": "OVERVIEW",
                    "KIND": kind,
                    "ROLE": "TEXT",
                    "LINE_ORDER": order,
                    "LOCALE_ID": locale_id,
                    "LOCALIZED_LABEL": label,
                    "SOURCE_TEXT": source_text,
                    "LOCALIZED_TEXT": loc_text,
                    "SOURCE_HASH": stable_hash(f"{topic['TOPICKEY']}|{kind}|{source_text}"),
                    "LOCALIZED_HASH": stable_hash(loc_text),
                    "TRANSL_STATUS": transl_status,
                    "REVIEW_STATUS": review_status,
                    "FALLBACK_ALLOWED": 1,
                    "CREATED_AT": created_at,
                })

            artifact_rows.append({
                "RUN_ID": run_id,
                "ARTIFACT_LOCALE_ID": artifact_locale_id,
                "TOPICKEY": topic["TOPICKEY"],
                "ARTIFACT_KIND": "CMDHELP_TOPIC_VIEW",
                "LOCALE_ID": locale_id,
                "SOURCE_ARTIFACT_HASH": source_artifact_hash,
                "LOCALIZED_ARTIFACT_HASH": stable_hash("|".join([localized_title, localized_summary, localized_usage, localized_note])),
                "TRANSL_STATUS": transl_status,
                "REVIEW_STATUS": review_status,
                "FALLBACK_ALLOWED": 1,
                "CREATED_AT": created_at,
            })

    for loc in STARTER_LOCALES:
        locale_id = loc["LOCALE_ID"]
        fallback_rows.append({
            "RUN_ID": run_id,
            "LOCALE_ID": locale_id,
            "FALLBACK_CHAIN": "en-US" if locale_id == "en-US" else f"{locale_id}->en-US",
            "EXPECTED_BEHAVIOR": "source canonical" if locale_id == "en-US" else "use localized row when present, otherwise fall back to en-US/source",
            "FALLBACK_VISIBLE_IN_REPORT_MODE": 1,
            "CREATED_AT": created_at,
        })

    return {
        "topic": topic_rows,
        "section": section_rows,
        "line": line_rows,
        "artifact": artifact_rows,
        "fallback": fallback_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage PHASE23J HELP locale sample rows candidate-only.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")

    candidate_dir = repo_root / "docs" / "locale" / "candidates" / "PHASE23J-HELP-LOCALE-SAMPLE-ROW-MATERIALIZATION-PLAN"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    created_at = now_utc()
    run_id = "PHASE23J-" + stable_hash(str(candidate_dir) + created_at).upper()
    phase23i_green = 1 if find_phase23i_green(repo_root) else 0
    rows = build_rows(run_id, created_at)

    write_csv(candidate_dir / "phase23j_help_topic_locale_sample_rows.csv", rows["topic"])
    write_csv(candidate_dir / "phase23j_help_section_locale_sample_rows.csv", rows["section"])
    write_csv(candidate_dir / "phase23j_help_line_locale_sample_rows.csv", rows["line"])
    write_csv(candidate_dir / "phase23j_help_artifact_locale_sample_rows.csv", rows["artifact"])
    write_csv(candidate_dir / "phase23j_locale_fallback_sample_rows.csv", rows["fallback"])

    boundary = {
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "candidate_dbf_created": 0,
        "candidate_cdx_created": 0,
        "candidate_lmdb_created": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution": 0,
        "latest_pointer_changed": 0,
    }
    counts = {
        "seed_topics": len(TOPICS),
        "starter_locales": len(STARTER_LOCALES),
        "topic_locale_rows": len(rows["topic"]),
        "section_locale_rows": len(rows["section"]),
        "line_locale_rows": len(rows["line"]),
        "artifact_locale_rows": len(rows["artifact"]),
        "fallback_rows": len(rows["fallback"]),
        "total_sample_rows": sum(len(v) for v in rows.values()),
    }
    manifest = {
        "status": STATUS,
        "run_id": run_id,
        "created_at": created_at,
        "repo_root": str(repo_root),
        "candidate_dir": str(candidate_dir.relative_to(repo_root)),
        "phase23i_green": phase23i_green,
        "next_gate": NEXT_GATE,
        "starter_locales": STARTER_LOCALES,
        "seed_topics": TOPICS,
        "counts": counts,
        "boundary": boundary,
        "notes": [
            "Candidate-only sample rows; no active HELP/CMDHELP/CMDHELPCHK/MAINT/BBOX/source mutation.",
            "Non-en-US localized text values are review-required placeholders, not approved production translations.",
            "PHASE23K may use these CSV artifacts to build candidate-only DBF/CDX/LMDB proof tables if authorized.",
        ],
    }
    (candidate_dir / "phase23j_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    md_lines = [
        f"# {STATUS}",
        "",
        f"Run ID: `{run_id}`",
        f"Created at: `{created_at}`",
        f"Candidate dir: `{candidate_dir.relative_to(repo_root)}`",
        "",
        "## Purpose",
        "",
        "Stage sample HELP locale rows for a small proof set without creating active DBF/CDX/LMDB artifacts or changing runtime behavior.",
        "",
        "## Seed topics",
        "",
    ]
    for topic in TOPICS:
        md_lines.append(f"- `{topic['TOPICKEY']}` - {topic['SUMMARY']}")
    md_lines.extend([
        "",
        "## Starter locales",
        "",
    ])
    for loc in STARTER_LOCALES:
        md_lines.append(f"- `{loc['LOCALE_ID']}` ({loc['TRANSL_STATUS']})")
    md_lines.extend([
        "",
        "## Counts",
        "",
    ])
    for key, value in counts.items():
        md_lines.append(f"- `{key}`: {value}")
    md_lines.extend([
        "",
        "## Boundary",
        "",
    ])
    for key, value in boundary.items():
        md_lines.append(f"- `{key}`: {value}")
    md_lines.extend([
        "",
        "## Next gate",
        "",
        f"`{NEXT_GATE}`",
        "",
    ])
    (candidate_dir / "PHASE23J_HELP_LOCALE_SAMPLE_ROW_MATERIALIZATION_PLAN.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(STATUS)
    print(f"candidate_dir: {candidate_dir.relative_to(repo_root)}")
    print(f"phase23i_green: {phase23i_green}")
    for key in [
        "seed_topics", "starter_locales", "topic_locale_rows", "section_locale_rows",
        "line_locale_rows", "artifact_locale_rows", "fallback_rows", "total_sample_rows",
    ]:
        print(f"{key}: {counts[key]}")
    for key in [
        "source_files_written", "active_help_dbf_written", "active_help_cdx_written", "active_help_lmdb_written",
        "candidate_dbf_created", "candidate_cdx_created", "candidate_lmdb_created",
        "cmdhelp_behavior_changed", "cmdhelpchk_behavior_changed", "maint_behavior_changed", "bbox_behavior_changed",
    ]:
        print(f"{key}: {boundary[key]}")
    print(f"next_gate: {NEXT_GATE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
