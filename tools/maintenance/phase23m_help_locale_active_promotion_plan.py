#!/usr/bin/env python3
"""
PHASE23M HELP locale active promotion plan.

Report-only gate. It validates the PHASE23LS count/smartlist/tuple proof,
inventories the PHASE23K candidate HELP locale companion artifacts, and stages
a promotion/rollback plan for copying candidate DBF/CDX/LMDB artifacts into the
active HELP roots. This script does not copy or mutate active HELP artifacts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
PHASE23LS_NAME = "PHASE23LS-CMDHELP-LOCALE-COUNT-SMARTLIST-TUPLE-READBACK-PROOF"
PHASE23M_NAME = "PHASE23M-HELP-LOCALE-ACTIVE-PROMOTION-PLAN"

STATUS_GREEN = "PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN_GREEN_REPORT_ONLY_APPLY_HELD"
STATUS_REQUIRED = "PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN_REVIEW_REQUIRED"

@dataclass
class ArtifactRow:
    table: str
    kind: str
    candidate_path: str
    candidate_exists: int
    candidate_sha256: str
    candidate_size_bytes: int
    active_path: str
    active_exists: int
    active_sha256: str
    active_size_bytes: int
    action: str


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(path: Path) -> str:
    if not path.exists():
        return ""
    if path.is_file():
        return sha256_file(path)
    h = hashlib.sha256()
    for p in sorted(x for x in path.rglob("*") if x.is_file()):
        h.update(str(p.relative_to(path)).replace("\\", "/").encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def size_tree(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def count_occ(text: str, needle: str) -> int:
    return text.count(needle)


def build_artifact_rows(repo: Path, phase23k_dir: Path) -> list[ArtifactRow]:
    active_dbf = repo / "dottalkpp" / "data" / "HELP"
    active_idx = repo / "dottalkpp" / "data" / "INDEXES" / "HELP"
    active_lmdb = repo / "dottalkpp" / "data" / "LMDB" / "HELP"
    rows: list[ArtifactRow] = []
    for table in TABLES:
        specs = [
            ("dbf", phase23k_dir / "dbf" / f"{table}.dbf", active_dbf / f"{table}.dbf"),
            ("cdx", phase23k_dir / "indexes" / f"{table}.cdx", active_idx / f"{table}.cdx"),
            ("lmdb", phase23k_dir / "lmdb" / f"{table}.cdx.d", active_lmdb / f"{table}.cdx.d"),
        ]
        for kind, cand, active in specs:
            action = "copy_new"
            if active.exists():
                cand_hash = sha256_tree(cand)
                active_hash = sha256_tree(active)
                action = "replace_with_backup" if cand_hash != active_hash else "already_matches_candidate"
            rows.append(
                ArtifactRow(
                    table=table,
                    kind=kind,
                    candidate_path=rel(cand, repo),
                    candidate_exists=1 if cand.exists() else 0,
                    candidate_sha256=sha256_tree(cand),
                    candidate_size_bytes=size_tree(cand),
                    active_path=rel(active, repo),
                    active_exists=1 if active.exists() else 0,
                    active_sha256=sha256_tree(active),
                    active_size_bytes=size_tree(active),
                    action=action,
                )
            )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()

    phase23k_dir = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    phase23ls_dir = repo / "docs" / "locale" / "candidates" / PHASE23LS_NAME
    phase23m_dir = repo / "docs" / "locale" / "candidates" / PHASE23M_NAME
    reports_dir = phase23m_dir / "reports"
    manifests_dir = phase23m_dir / "manifests"
    runtime_dir = phase23m_dir / "runtime"
    phase23m_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    retained_dts = phase23ls_dir / "runtime" / "phase23ls_cmdhelp_locale_count_smartlist_tuple_probe.dts"
    transcript = phase23ls_dir / "transcripts" / "phase23ls_cmdhelp_locale_count_smartlist_tuple_probe_transcript.txt"
    t = read_text(transcript)

    artifact_rows = build_artifact_rows(repo, phase23k_dir)
    artifact_dicts = [asdict(r) for r in artifact_rows]
    write_csv(
        reports_dir / "phase23m_candidate_to_active_artifact_plan.csv",
        artifact_dicts,
        list(artifact_dicts[0].keys()) if artifact_dicts else [],
    )

    active_roots = [
        repo / "dottalkpp" / "data" / "HELP",
        repo / "dottalkpp" / "data" / "INDEXES" / "HELP",
        repo / "dottalkpp" / "data" / "LMDB" / "HELP",
    ]
    root_rows = []
    for p in active_roots:
        root_rows.append({
            "root": rel(p, repo),
            "exists": 1 if p.exists() else 0,
            "planned_role": "active_help_target_root",
        })
    write_csv(reports_dir / "phase23m_active_target_roots.csv", root_rows, ["root", "exists", "planned_role"])

    plan_rows = [
        {"seq": 1, "step": "validate_phase23ls_green_contract", "apply_now": 0},
        {"seq": 2, "step": "inventory_candidate_dbf_cdx_lmdb_artifacts", "apply_now": 0},
        {"seq": 3, "step": "inventory_active_help_target_roots", "apply_now": 0},
        {"seq": 4, "step": "create_rollback_backup_before_any_copy", "apply_now": 0},
        {"seq": 5, "step": "copy_candidate_dbf_to_active_help_root", "apply_now": 0},
        {"seq": 6, "step": "copy_candidate_cdx_to_active_help_indexes_root", "apply_now": 0},
        {"seq": 7, "step": "copy_candidate_lmdb_envdirs_to_active_help_lmdb_root", "apply_now": 0},
        {"seq": 8, "step": "run_active_readback_validation_with_count_smartlist_tuple", "apply_now": 0},
        {"seq": 9, "step": "append_locale_savepoint_on_green_only", "apply_now": 0},
    ]
    write_csv(reports_dir / "phase23m_promotion_sequence_plan.csv", plan_rows, ["seq", "step", "apply_now"])

    copy_plan = runtime_dir / "phase23m_APPLY_HELD_copy_plan.ps1"
    copy_plan.write_text(
        "# PHASE23M report-only copy plan. Do not run as-is.\n"
        "# This file is staged to make the promotion sequence auditable.\n"
        "# PHASE23N should generate an execution script with backups and validation if authorized.\n"
        "$ErrorActionPreference = 'Stop'\n"
        "Write-Host 'PHASE23M is APPLY_HELD. Authorize PHASE23N before active copy.'\n",
        encoding="utf-8",
    )

    checks = {
        "phase23k_candidate_dir_exists": int(phase23k_dir.exists()),
        "phase23ls_candidate_dir_exists": int(phase23ls_dir.exists()),
        "retained_dotscript_exists": int(retained_dts.exists()),
        "dts_extension_ok": int(retained_dts.suffix.lower() == ".dts"),
        "transcript_exists": int(transcript.exists()),
        "transcript_markers_ok": int("PHASE23LS_DOTSCRIPT_START" in t and "PHASE23LS_DOTSCRIPT_END" in t),
        "contract_marker_ok": int("PHASE23LS_COUNT_SMARTLIST_N_TUPLE_CONTRACT" in t),
        "no_list_contract_marker_ok": int("PHASE23LS_NO_LIST_NO_SMARTLIST_ALL" in t),
        "table_markers_ok": int(all(f"PHASE23LS_READBACK_{name}" in t for name in TABLES)),
        "topickey_order_count": count_occ(t, "SET ORDER: CDX TAG 'TOPICKEY'"),
        "count_command_count": count_occ(t, "> COUNT"),
        "smartlist_n_command_count": count_occ(t, "> SMARTLIST 10") + count_occ(t, "> SMARTLIST 30"),
        "smartlist_all_command_count": count_occ(t, "> SMARTLIST ALL"),
        "list_command_count": count_occ(t, "> LIST"),
        "tuple_values_command_count": count_occ(t, "TUPLE * --VALUES-ONLY"),
        "compact_tuple_command_count": count_occ(t, "TUPLE TOPICKEY,LOCALE_ID,TRANSL_STATUS,REVIEW_STATUS --VALUES-ONLY"),
        "record_listed_count": count_occ(t, "record(s) listed"),
        "draft_placeholder_rows_detected": int("DRAFT_PLACEHOLDER" in t),
        "needs_review_detected": int("NEEDS_REVIEW" in t),
        "es_draft_detected": int("[es draft]" in t or " es " in t),
        "path_reset_ok": int("PHASE23LS_PATH_RESET_TO_DEFAULT_DATA_ROOTS" in t and "SETPATH: LMDB = D:\\code\\ccode\\dottalkpp\\data\\lmdb" in t),
        "candidate_dbf_exists_count": sum(1 for r in artifact_rows if r.kind == "dbf" and r.candidate_exists),
        "candidate_cdx_exists_count": sum(1 for r in artifact_rows if r.kind == "cdx" and r.candidate_exists),
        "candidate_lmdb_exists_count": sum(1 for r in artifact_rows if r.kind == "lmdb" and r.candidate_exists),
        "active_existing_artifact_count": sum(1 for r in artifact_rows if r.active_exists),
        "promotion_plan_rows": len(plan_rows),
        "artifact_plan_rows": len(artifact_rows),
        "source_files_written": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "active_promotion_executed": 0,
    }
    bad_patterns = [
        "DOTSCRIPT: script not found",
        "Unknown command",
        "SET ORDER: tag 'TOPICKEY' not found",
        "SET INDEX: file not found",
        "BUILDLMDB: failed to build LMDB environment",
    ]
    checks["no_bad_hits"] = int(not any(p in t for p in bad_patterns))

    green = (
        checks["phase23k_candidate_dir_exists"] == 1
        and checks["phase23ls_candidate_dir_exists"] == 1
        and checks["retained_dotscript_exists"] == 1
        and checks["dts_extension_ok"] == 1
        and checks["transcript_markers_ok"] == 1
        and checks["contract_marker_ok"] == 1
        and checks["no_list_contract_marker_ok"] == 1
        and checks["table_markers_ok"] == 1
        and checks["topickey_order_count"] >= 4
        and checks["count_command_count"] >= 4
        and checks["smartlist_n_command_count"] >= 4
        and checks["smartlist_all_command_count"] == 0
        and checks["list_command_count"] == 0
        and checks["tuple_values_command_count"] >= 4
        and checks["compact_tuple_command_count"] >= 4
        and checks["record_listed_count"] >= 4
        and checks["candidate_dbf_exists_count"] == 4
        and checks["candidate_cdx_exists_count"] == 4
        and checks["candidate_lmdb_exists_count"] == 4
        and checks["path_reset_ok"] == 1
        and checks["no_bad_hits"] == 1
    )

    status = STATUS_GREEN if green else STATUS_REQUIRED
    manifest = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE23M",
        "candidate_dir": rel(phase23m_dir, repo),
        "phase23k_candidate_dir": rel(phase23k_dir, repo),
        "phase23ls_candidate_dir": rel(phase23ls_dir, repo),
        "checks": checks,
        "active_target_roots": [rel(p, repo) for p in active_roots],
        "next_gate": "HOLD_OR_AUTHORIZE_PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_EXECUTION_STAGING" if green else "FIX_OR_RERUN_PHASE23LS_OR_PHASE23M_PLAN",
    }
    (manifests_dir / "phase23m_help_locale_active_promotion_plan_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    md = [
        f"# PHASE23M HELP Locale Active Promotion Plan",
        "",
        f"Status: `{status}`",
        "",
        "This is a report-only promotion plan. It does not copy candidate artifacts into active HELP roots.",
        "",
        "## Promotion source",
        f"- Candidate artifacts: `{rel(phase23k_dir, repo)}`",
        f"- Readback proof: `{rel(phase23ls_dir, repo)}`",
        "",
        "## Active targets planned",
    ]
    for p in active_roots:
        md.append(f"- `{rel(p, repo)}`")
    md.extend([
        "",
        "## Required execution behavior for PHASE23N",
        "- Create rollback backups before any active copy.",
        "- Promote exactly four HELP locale companion tables: HELP_TOPIC_LOCALE, HELP_SECTION_LOCALE, HELP_LINE_LOCALE, HELP_ARTIFACT_LOCALE.",
        "- Copy DBF, CDX, and LMDB envdir artifacts together.",
        "- Run active readback validation using COUNT, bounded SMARTLIST n, and TUPLE * --VALUES-ONLY.",
        "- Keep retained DotScripts as .dts files.",
        "- Avoid LIST and SMARTLIST ALL in proof lanes unless those commands are explicitly under test.",
        "- Append savepoint only after active validation is green.",
        "",
        "## Boundary",
        "- source_files_written: 0",
        "- active_help_dbf_written: 0",
        "- active_help_cdx_written: 0",
        "- active_help_lmdb_written: 0",
        "- active_promotion_executed: 0",
        "",
        f"Next gate: `{manifest['next_gate']}`",
        "",
    ])
    (reports_dir / "PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN.md").write_text("\n".join(md), encoding="utf-8")

    print(status)
    print(f"candidate_dir: {rel(phase23m_dir, repo)}")
    print(f"phase23k_candidate_dir: {rel(phase23k_dir, repo)}")
    print(f"phase23ls_candidate_dir: {rel(phase23ls_dir, repo)}")
    print(f"phase23ls_green: {1 if green else 0}")
    print(f"retained_dotscript: {rel(retained_dts, repo)}")
    print(f"dts_extension_ok: {checks['dts_extension_ok']}")
    print("candidate_tables: 4")
    print(f"candidate_dbf_exists: {checks['candidate_dbf_exists_count']}/4")
    print(f"candidate_cdx_exists: {checks['candidate_cdx_exists_count']}/4")
    print(f"candidate_lmdb_exists: {checks['candidate_lmdb_exists_count']}/4")
    print(f"active_existing_artifact_count: {checks['active_existing_artifact_count']}")
    print(f"promotion_plan_rows: {checks['promotion_plan_rows']}")
    print(f"artifact_plan_rows: {checks['artifact_plan_rows']}")
    print(f"path_reset_ok: {checks['path_reset_ok']}")
    print(f"active_target_roots: {','.join(rel(p, repo) for p in active_roots)}")
    print(f"manifest: {rel(manifests_dir / 'phase23m_help_locale_active_promotion_plan_manifest.json', repo)}")
    print(f"promotion_plan: {rel(reports_dir / 'PHASE23M_HELP_LOCALE_ACTIVE_PROMOTION_PLAN.md', repo)}")
    print(f"copy_plan_apply_held: {rel(copy_plan, repo)}")
    for key in [
        "source_files_written",
        "active_help_dbf_written",
        "active_help_cdx_written",
        "active_help_lmdb_written",
        "cmdhelp_behavior_changed",
        "cmdhelpchk_behavior_changed",
        "maint_behavior_changed",
        "bbox_behavior_changed",
        "runtime_execution_by_python",
        "active_promotion_executed",
    ]:
        print(f"{key}: {checks[key]}")
    print(f"next_gate: {manifest['next_gate']}")
    return 0 if green else 2


if __name__ == "__main__":
    raise SystemExit(main())
