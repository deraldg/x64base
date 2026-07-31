#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone

PHASE = "PHASE23S"
NAME = "PHASE23S-CMDHELP-LOCALE-PREVIEW-SOURCE-PATCH-STAGING"
STATUS_GREEN = "PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING_GREEN_SOURCE_HELD"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_APPLY"

TABLES = [
    "HELP_TOPIC_LOCALE",
    "HELP_SECTION_LOCALE",
    "HELP_LINE_LOCALE",
    "HELP_ARTIFACT_LOCALE",
]

SKIP_DIRS = {
    ".git", "build", "out", ".vs", ".vscode", "node_modules", "__pycache__",
    "candidate", "candidates", "published", "rollback", "backup", "backups",
}

SOURCE_EXTS = {".cpp", ".cxx", ".cc", ".c", ".hpp", ".hh", ".h"}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_dir():
        for p in sorted(x for x in path.rglob("*") if x.is_file()):
            h.update(str(p.relative_to(path)).replace("\\", "/").encode("utf-8"))
            h.update(b"\0")
            h.update(p.read_bytes())
            h.update(b"\0")
    else:
        h.update(path.read_bytes())
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def read_text_safe(path: Path, limit: int = 600_000) -> str:
    try:
        data = path.read_bytes()[:limit]
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def find_phase_green(repo: Path, phase_name: str, status_prefix: str) -> tuple[int, Path | None]:
    base = repo / "docs" / "locale" / "candidates" / phase_name
    if not base.exists():
        return 0, None
    manifest_hits = list((base / "manifests").glob("*.json")) if (base / "manifests").exists() else []
    report_hits = list((base / "reports").glob("*.md")) if (base / "reports").exists() else []
    for p in manifest_hits + report_hits:
        text = read_text_safe(p)
        if status_prefix in text:
            return 1, p
    return 0, (manifest_hits + report_hits)[0] if (manifest_hits + report_hits) else None


def active_artifact_counts(repo: Path) -> dict[str, str | int]:
    dbf_root = repo / "dottalkpp" / "data" / "HELP"
    cdx_root = repo / "dottalkpp" / "data" / "INDEXES" / "HELP"
    lmdb_root = repo / "dottalkpp" / "data" / "LMDB" / "HELP"
    lower_roots = [repo / "dottalkpp" / "data" / "help", repo / "dottalkpp" / "data" / "indexes" / "help", repo / "dottalkpp" / "data" / "lmdb" / "help"]
    if not dbf_root.exists() and lower_roots[0].exists():
        dbf_root = lower_roots[0]
    if not cdx_root.exists() and lower_roots[1].exists():
        cdx_root = lower_roots[1]
    if not lmdb_root.exists() and lower_roots[2].exists():
        lmdb_root = lower_roots[2]
    dbf = sum(1 for t in TABLES if (dbf_root / f"{t}.dbf").exists())
    cdx = sum(1 for t in TABLES if (cdx_root / f"{t}.cdx").exists())
    lmdb = sum(1 for t in TABLES if (lmdb_root / f"{t}.cdx.d").exists())
    return {
        "active_roots": ",".join([
            str(dbf_root.relative_to(repo)) if dbf_root.is_absolute() else str(dbf_root),
            str(cdx_root.relative_to(repo)) if cdx_root.is_absolute() else str(cdx_root),
            str(lmdb_root.relative_to(repo)) if lmdb_root.is_absolute() else str(lmdb_root),
        ]),
        "active_dbf_exists": f"{dbf}/4",
        "active_cdx_exists": f"{cdx}/4",
        "active_lmdb_exists": f"{lmdb}/4",
        "active_all_exists": int(dbf == 4 and cdx == 4 and lmdb == 4),
    }


def scan_source_candidates(repo: Path, limit: int = 80) -> list[dict]:
    rows: list[dict] = []
    roots = [repo / "src", repo / "dottalkpp", repo / "include"]
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if len(rows) >= limit:
                break
            if not p.is_file() or p.suffix.lower() not in SOURCE_EXTS:
                continue
            rel = p.relative_to(repo)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            if p in seen:
                continue
            name_hit = "cmdhelp" in p.name.lower() or "help" in p.name.lower() or "locale" in p.name.lower()
            text = ""
            content_hit = False
            usage_hit = False
            contract_hit = False
            if name_hit or p.stat().st_size < 1_500_000:
                text = read_text_safe(p, limit=250_000)
                up = text.upper()
                content_hit = "CMDHELP" in up or "HELP_TOPIC" in up or "LOCALE" in up or "SET LANGUAGE" in up
                usage_hit = "@DOTTALK.USAGE" in up
                contract_hit = "CMDHELP" in up and ("USAGE" in up or "TOPIC" in up or "HELP" in up)
            if name_hit or content_hit:
                seen.add(p)
                rows.append({
                    "source_path": str(rel),
                    "name_hit": int(name_hit),
                    "content_hit": int(content_hit),
                    "usage_contract_hit": int(usage_hit),
                    "cmdhelp_contract_hit": int(contract_hit),
                    "size_bytes": p.stat().st_size,
                    "sha256": sha256_path(p)[:16],
                    "recommended_role": recommend_role(str(rel), text),
                })
        if len(rows) >= limit:
            break
    return rows


def recommend_role(rel: str, text: str) -> str:
    low = rel.lower()
    up = text.upper()
    if "cmdhelp" in low:
        return "PRIMARY_CMDHELP_COMMAND_SURFACE_CANDIDATE"
    if "help" in low and "CMDHELP" in up:
        return "HELP_CMDHELP_LOOKUP_SUPPORT_CANDIDATE"
    if "locale" in low or "SET LANGUAGE" in up:
        return "LOCALE_SELECTION_SUPPORT_CANDIDATE"
    if "cmd" in low:
        return "CLI_PARSER_SUPPORT_CANDIDATE"
    return "SECONDARY_REVIEW_CANDIDATE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    cand = repo / "docs" / "locale" / "candidates" / NAME
    reports = cand / "reports"
    manifests = cand / "manifests"
    patches = cand / "patches"
    reports.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    patches.mkdir(parents=True, exist_ok=True)

    phase23r_green, phase23r_evidence = find_phase_green(
        repo,
        "PHASE23R-CMDHELP-LOCALE-PREVIEW-IMPLEMENTATION-PLAN",
        "PHASE23R_CMDHELP_LOCALE_PREVIEW_IMPLEMENTATION_PLAN_GREEN_REPORT_ONLY",
    )
    phase23q_green, _ = find_phase_green(
        repo,
        "PHASE23Q-CMDHELP-LOCALE-INTEGRATION-PLAN",
        "PHASE23Q_CMDHELP_LOCALE_INTEGRATION_PLAN_GREEN_REPORT_ONLY",
    )
    phase23o_green, _ = find_phase_green(
        repo,
        "PHASE23O-ACTIVE-HELP-LOCALE-READBACK-PROOF",
        "PHASE23O_ACTIVE_HELP_LOCALE_READBACK_PROOF_GREEN",
    )

    counts = active_artifact_counts(repo)
    source_rows = scan_source_candidates(repo, limit=80)

    command_contract_rows = [
        {"surface": "CMDHELP <topic>", "status": "MUST_REMAIN_UNCHANGED", "behavior": "Existing command output remains default/source text."},
        {"surface": "CMDHELP <topic> PREVIEW LOCALE <locale>", "status": "NEW_PREVIEW_ONLY", "behavior": "Show locale sidecar preview with fallback notes."},
        {"surface": "CMDHELP <topic> LOCALE <locale>", "status": "DEFER_OR_ALIAS_REVIEW", "behavior": "May be considered later; preview form is safer."},
        {"surface": "SET LANGUAGE <locale>", "status": "NO_IMPLICIT_CMDHELP_CHANGE_IN_THIS_PATCH", "behavior": "Locale selection can be consumed later after explicit preview is stable."},
        {"surface": "Command keywords", "status": "ENGLISH_ONLY", "behavior": "Command keywords remain English; localized content is data only."},
    ]
    parser_rows = [
        {"step": 1, "contract": "Parse PREVIEW as an explicit mode token after topic."},
        {"step": 2, "contract": "Parse LOCALE <locale> only for preview mode in this phase."},
        {"step": 3, "contract": "Reject unknown locale with clear diagnostic and no fallback mutation."},
        {"step": 4, "contract": "Preserve all existing CMDHELP syntax paths unchanged."},
        {"step": 5, "contract": "Update @dottalk.usage v1 comment/usage metadata in same guarded patch."},
    ]
    lookup_rows = [
        {"step": 1, "contract": "Resolve command/topic to TOPICKEY using existing CMDHELP topic path."},
        {"step": 2, "contract": "Open/attach active HELP_*_LOCALE sidecars read-only from active HELP roots."},
        {"step": 3, "contract": "Seek/read rows by TOPICKEY plus requested LOCALE_ID."},
        {"step": 4, "contract": "Require TRANSL_STATUS and REVIEW_STATUS gates before localized output."},
        {"step": 5, "contract": "If row is DRAFT_PLACEHOLDER or NEEDS_REVIEW, show source/default plus preview advisory."},
        {"step": 6, "contract": "Emit localized labels/text only in explicit preview mode until review-approved rows exist."},
        {"step": 7, "contract": "No writes to HELP data, no catalog regeneration, no CMDHELPCHK mutation in source patch."},
    ]
    fallback_rows = [
        {"condition": "locale row missing", "result": "fallback to source/default", "diagnostic": "LOCALE_FALLBACK_ROW_MISSING"},
        {"condition": "TRANSL_STATUS=DRAFT_PLACEHOLDER", "result": "fallback to source/default", "diagnostic": "LOCALE_PREVIEW_DRAFT_HELD"},
        {"condition": "REVIEW_STATUS=NEEDS_REVIEW", "result": "fallback to source/default", "diagnostic": "LOCALE_PREVIEW_NEEDS_REVIEW"},
        {"condition": "review approved future row", "result": "preview may display localized text", "diagnostic": "LOCALE_PREVIEW_APPROVED"},
        {"condition": "base CMDHELP no preview", "result": "unchanged source/default output", "diagnostic": "NONE"},
    ]
    patch_plan_rows = [
        {"artifact": "source_inventory", "action": "inspect candidate source rows", "mutation": 0},
        {"artifact": "cmdhelp_parser", "action": "plan PREVIEW LOCALE parser extension", "mutation": 0},
        {"artifact": "locale_lookup_helper", "action": "plan read-only sidecar lookup helper", "mutation": 0},
        {"artifact": "fallback_status_gate", "action": "plan draft/review/fallback guard", "mutation": 0},
        {"artifact": "usage_contract", "action": "plan @dottalk.usage v1 update with command docs", "mutation": 0},
        {"artifact": "runtime_smoke", "action": "plan command smoke tests", "mutation": 0},
        {"artifact": "cmdhelpchk", "action": "defer behavior changes to separate phase", "mutation": 0},
        {"artifact": "maint_bbox", "action": "defer visibility changes to separate phase", "mutation": 0},
    ]
    test_rows = [
        {"test": "CMDHELP AREA", "expect": "unchanged output"},
        {"test": "CMDHELP AREA PREVIEW LOCALE es", "expect": "preview path, draft held/fallback advisory"},
        {"test": "CMDHELP ABOUT PREVIEW LOCALE es", "expect": "preview path, draft held/fallback advisory"},
        {"test": "CMDHELP AREA PREVIEW LOCALE xx", "expect": "unknown locale diagnostic"},
        {"test": "SET LANGUAGE es; CMDHELP AREA", "expect": "unchanged until implicit language integration is authorized"},
        {"test": "CMDHELPCHK", "expect": "unchanged in this phase"},
    ]

    write_csv(reports / "phase23s_source_patch_target_inventory.csv", source_rows)
    write_csv(reports / "phase23s_preview_command_contract.csv", command_contract_rows)
    write_csv(reports / "phase23s_parser_patch_contract.csv", parser_rows)
    write_csv(reports / "phase23s_lookup_algorithm_contract.csv", lookup_rows)
    write_csv(reports / "phase23s_fallback_status_gate_contract.csv", fallback_rows)
    write_csv(reports / "phase23s_source_patch_plan.csv", patch_plan_rows)
    write_csv(reports / "phase23s_runtime_test_plan.csv", test_rows)

    patch_outline = patches / "PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_OUTLINE.md"
    patch_outline.write_text("\n".join([
        "# PHASE23S CMDHELP Locale Preview Source Patch Outline",
        "",
        "This is an outline only. It is not an applyable patch.",
        "",
        "## Intended command",
        "",
        "`CMDHELP <topic> PREVIEW LOCALE <locale>`",
        "",
        "## Guardrails",
        "",
        "- Preserve `CMDHELP <topic>` output exactly.",
        "- Keep command keywords English.",
        "- Read active HELP locale sidecars only; do not write HELP data.",
        "- Draft or NEEDS_REVIEW rows must fall back to source text by default.",
        "- Update `@dottalk.usage v1` metadata in the same guarded source patch.",
        "",
        "## Deferred",
        "",
        "- Implicit SET LANGUAGE consumption.",
        "- CMDHELPCHK behavior mutation.",
        "- MAINT/BBOX behavior mutation.",
        "",
    ]), encoding="utf-8")

    md = reports / "PHASE23S_CMDHELP_LOCALE_PREVIEW_SOURCE_PATCH_STAGING.md"
    md.write_text("\n".join([
        f"# {PHASE} CMDHELP Locale Preview Source Patch Staging",
        "",
        f"Status: `{STATUS_GREEN}`" if phase23r_green and counts["active_all_exists"] else "Status: `PHASE23S_REVIEW_REQUIRED`",
        "",
        "PHASE23S is source-facing but source-held. It inventories candidate source files and stages the patch contract for `CMDHELP <topic> PREVIEW LOCALE <locale>` without writing source files.",
        "",
        "## Gate inputs",
        "",
        f"- PHASE23R green: {phase23r_green}",
        f"- PHASE23Q green: {phase23q_green}",
        f"- PHASE23O green: {phase23o_green}",
        f"- Active DBF: {counts['active_dbf_exists']}",
        f"- Active CDX: {counts['active_cdx_exists']}",
        f"- Active LMDB: {counts['active_lmdb_exists']}",
        "",
        "## Source policy",
        "",
        "No source file is written by this phase. The next gate must decide whether to create a real patch/apply package.",
        "",
        f"Next gate: `{NEXT_GATE}`",
        "",
    ]), encoding="utf-8")

    manifest = {
        "phase": PHASE,
        "status": STATUS_GREEN if phase23r_green and counts["active_all_exists"] else "PHASE23S_REVIEW_REQUIRED",
        "created_at": utc_now(),
        "candidate_dir": str(cand.relative_to(repo)),
        "phase23r_green": phase23r_green,
        "phase23q_green": phase23q_green,
        "phase23o_green": phase23o_green,
        "phase23r_evidence": str(phase23r_evidence.relative_to(repo)) if phase23r_evidence else "",
        "read_scope": "ACTIVE_HELP_LOCALE_ROOTS",
        "active_roots": counts["active_roots"],
        "active_dbf_exists": counts["active_dbf_exists"],
        "active_cdx_exists": counts["active_cdx_exists"],
        "active_lmdb_exists": counts["active_lmdb_exists"],
        "implementation_model": "CMDHELP_PREVIEW_LOCALE_EXPLICIT_ONLY_DEFAULT_UNCHANGED",
        "source_candidate_rows": len(source_rows),
        "preview_command_contract_rows": len(command_contract_rows),
        "parser_contract_rows": len(parser_rows),
        "lookup_algorithm_rows": len(lookup_rows),
        "fallback_status_gate_rows": len(fallback_rows),
        "source_patch_plan_rows": len(patch_plan_rows),
        "test_plan_rows": len(test_rows),
        "source_files_written": 0,
        "source_patch_applied": 0,
        "active_help_dbf_written": 0,
        "active_help_cdx_written": 0,
        "active_help_lmdb_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "runtime_execution_by_python": 0,
        "next_gate": NEXT_GATE,
        "reports": {
            "source_inventory": str((reports / "phase23s_source_patch_target_inventory.csv").relative_to(repo)),
            "patch_plan": str((reports / "phase23s_source_patch_plan.csv").relative_to(repo)),
            "implementation_report": str(md.relative_to(repo)),
            "patch_outline": str(patch_outline.relative_to(repo)),
        },
    }
    manifest_path = manifests / "phase23s_cmdhelp_locale_preview_source_patch_staging_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    status = manifest["status"]
    print(status)
    print(f"candidate_dir: {cand.relative_to(repo)}")
    print(f"phase23r_green: {phase23r_green}")
    print(f"phase23q_green: {phase23q_green}")
    print(f"phase23o_green: {phase23o_green}")
    print("read_scope: ACTIVE_HELP_LOCALE_ROOTS")
    print(f"active_roots: {counts['active_roots']}")
    print(f"active_dbf_exists: {counts['active_dbf_exists']}")
    print(f"active_cdx_exists: {counts['active_cdx_exists']}")
    print(f"active_lmdb_exists: {counts['active_lmdb_exists']}")
    print("implementation_model: CMDHELP_PREVIEW_LOCALE_EXPLICIT_ONLY_DEFAULT_UNCHANGED")
    print(f"source_candidate_rows: {len(source_rows)}")
    print(f"preview_command_contract_rows: {len(command_contract_rows)}")
    print(f"parser_contract_rows: {len(parser_rows)}")
    print(f"lookup_algorithm_rows: {len(lookup_rows)}")
    print(f"fallback_status_gate_rows: {len(fallback_rows)}")
    print(f"source_patch_plan_rows: {len(patch_plan_rows)}")
    print(f"test_plan_rows: {len(test_rows)}")
    print(f"manifest: {manifest_path.relative_to(repo)}")
    print(f"source_patch_staging_report: {md.relative_to(repo)}")
    print(f"patch_outline: {patch_outline.relative_to(repo)}")
    print("source_files_written: 0")
    print("source_patch_applied: 0")
    print("active_help_dbf_written: 0")
    print("active_help_cdx_written: 0")
    print("active_help_lmdb_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print("runtime_execution_by_python: 0")
    print(f"next_gate: {NEXT_GATE}")
    return 0 if status == STATUS_GREEN else 2


if __name__ == "__main__":
    raise SystemExit(main())
