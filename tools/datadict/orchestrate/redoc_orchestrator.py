#!/usr/bin/env python3
"""
DD-024 DotTalk++ / x64base data-dictionary redocumentation orchestrator.

Report-only by default. This script scans source/evidence files and emits a stable
fingerprint-oriented DD-022-compatible run manifest. DD-024 adds default exclusions so
redocumentation runs do not count their own generated reports as source changes.

Python: target 3.12+
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

STEP_ROWS = [
    (1, "SCAN_SOURCES", "scan", "SOURCE_SCAN_OK", "report-only source discovery with DD-024 stable exclusions"),
    (2, "EXTRACT_PHYSICAL_DECLARED", "extract", "PHYSICAL_EXTRACT_OK", "planned physical/schema/static extraction"),
    (3, "EXTRACT_SOURCE_CONTRACTS", "extract", "SOURCE_CONTRACT_EXTRACT_OK", "planned usage/registry/MetaFact extraction"),
    (4, "SCAN_HELP_MESSAGES", "scan", "HELP_MESSAGE_SCAN_OK", "planned HELP/message/diagnostic scan"),
    (5, "SCAN_RULES_XEXPR", "scan", "RULE_XEXPR_SCAN_OK", "planned rules/constraints/xexpr scan"),
    (6, "SCAN_RELATIONS_TUPLES", "scan", "RELATION_TUPLE_SCAN_OK", "planned workspace/relation/tuple scan"),
    (7, "OPTIONAL_RUNTIME_PROOF_CAPTURE", "proof", "RUNTIME_CAPTURE_AUTHORIZED", "blocked unless explicitly run locally"),
    (8, "PARSE_TRANSCRIPTS", "proof", "TRANSCRIPT_PARSE_OK", "not run unless transcript input is supplied"),
    (9, "RECONCILE_EVIDENCE", "reconcile", "RECONCILIATION_OK", "planned evidence reconciliation"),
    (10, "BUILD_STAGING_PACKAGE", "stage", "STAGING_PACKAGE_BUILT", "planned staging package build"),
    (11, "VALIDATE_STAGING_PACKAGE", "validate", "STAGING_VALIDATED", "planned staging validation"),
    (12, "WRITE_RUN_SUMMARY", "report", "RUN_SUMMARY_WRITTEN", "write this dry-run manifest"),
    (13, "REVIEW_QUEUE_TRIAGE", "review", "REVIEW_DISPOSITION_RECORDED", "blocked pending human review"),
    (14, "PROMOTION", "promote", "EXPLICIT_PROMOTION_AUTHORIZED", "blocked by design"),
    (15, "DOC_REGEN", "redocument", "DOC_REGEN_AUTHORIZED", "blocked by design"),
]

SOURCE_EXTS = {
    ".cpp", ".hpp", ".h", ".c", ".cc", ".hh", ".cxx", ".hxx",
    ".py", ".ps1", ".dts", ".json", ".cmake", ".txt", ".md", ".yml", ".yaml"
}

# Directory names to prune wherever they occur.
DEFAULT_EXCLUDE_DIR_NAMES = {
    ".git", ".svn", ".hg", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "build", "build-msvc", "build-pro-md", "build-wsl", "build-tests", "build_rdi",
    "dist", "target", "vcpkg_installed", "node_modules", ".mdo_backups",
}

# Repo-relative prefixes to exclude by default because they are generated/volatile lanes.
# Use forward slashes, case-insensitive matching on Windows-friendly normalized paths.
DEFAULT_EXCLUDE_PREFIXES = [
    "docs/datadict/reports/",
    "docs/datadict/manifests/",
    "docs/datadict/staging/",
    "docs/datadict/tmp/",
    "docs/datadict/cache/",
    "docs/datadict/transcripts/local/",
    "docs/datadict/runlog/local/",
    "docs/manuals/developer/manualgen/backups/",
    "docs/manuals/developer/manualgen/generated/",
    "docs/manuals/developer/manualgen/logs/",
    "docs/manuals/developer/manualgen/published/",
    "dottalkpp/data/lmdb/",
    "dottalkpp/data/indexes/backups/",
    "dottalkpp/data/backup/",
    "dottalkpp/data/logs/",
    "dottalkpp/data/out/",
    "dottalkpp/data/tmp/",
]

# Glob-like file/path patterns to exclude anywhere. These are intentionally conservative.
DEFAULT_EXCLUDE_GLOBS = [
    "*.tlog", "*.obj", "*.pdb", "*.ilk", "*.exe", "*.dll", "*.lib", "*.exp",
    "*.pyc", "*.pyo", "*.tmp", "*.log",
]


def norm_rel(path: Path) -> str:
    return path.as_posix().replace("\\", "/")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def should_exclude_rel(rel: str, prefixes: list[str], globs: list[str]) -> tuple[bool, str]:
    low = rel.lower().replace("\\", "/")
    for prefix in prefixes:
        if low == prefix.rstrip("/").lower() or low.startswith(prefix.lower()):
            return True, f"prefix:{prefix}"
    name = Path(rel).name
    for pat in globs:
        if fnmatch.fnmatch(name.lower(), pat.lower()) or fnmatch.fnmatch(low, pat.lower()):
            return True, f"glob:{pat}"
    return False, ""


def discover_sources(
    repo_root: Path,
    max_files: int = 100000,
    use_default_excludes: bool = True,
    include_generated_evidence: bool = False,
    extra_excludes: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], dict[str, Any]]:
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    extra_excludes = extra_excludes or []

    if not repo_root.exists():
        return rows, excluded, [f"repo root does not exist: {repo_root}"], {}

    dir_names = set(DEFAULT_EXCLUDE_DIR_NAMES) if use_default_excludes else set()
    prefixes = list(DEFAULT_EXCLUDE_PREFIXES) if use_default_excludes else []
    globs = list(DEFAULT_EXCLUDE_GLOBS) if use_default_excludes else []

    if include_generated_evidence:
        prefixes = [p for p in prefixes if not p.startswith("docs/datadict/")]

    # Extra excludes may be either prefix-style entries ending in / or glob-style patterns.
    for item in extra_excludes:
        item = item.replace("\\", "/")
        if item.endswith("/") or "/" in item:
            prefixes.append(item if item.endswith("/") else item + "/")
        else:
            globs.append(item)

    count = 0
    root = repo_root.resolve()
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        rel_dir = safe_rel(current_path, root)
        if rel_dir == ".":
            rel_dir = ""

        # Prune directory-name defaults and prefix excludes before descending.
        kept_dirs = []
        for d in dirs:
            child = current_path / d
            child_rel = norm_rel(Path(safe_rel(child, root)))
            reason = ""
            if d in dir_names:
                reason = f"dir_name:{d}"
            else:
                ex, why = should_exclude_rel(child_rel + "/", prefixes, globs=[])
                if ex:
                    reason = why
            if reason:
                excluded.append({"path": child_rel + "/", "kind": "directory", "reason": reason})
            else:
                kept_dirs.append(d)
        dirs[:] = kept_dirs

        for filename in files:
            path = current_path / filename
            rel = norm_rel(Path(safe_rel(path, root)))
            ex, why = should_exclude_rel(rel, prefixes, globs)
            if ex:
                excluded.append({"path": rel, "kind": "file", "reason": why})
                continue
            if path.suffix.lower() not in SOURCE_EXTS:
                continue
            count += 1
            if count > max_files:
                warnings.append(f"source scan truncated at {max_files} files")
                break
            try:
                digest = sha256_file(path)
                rows.append({
                    "path": rel,
                    "suffix": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                    "stable_fingerprint": sha256_text(f"{rel}\n{path.stat().st_size}\n{digest}"),
                })
            except OSError as exc:
                warnings.append(f"could not hash {path}: {exc}")
        if count > max_files:
            break

    rows.sort(key=lambda r: r["path"].lower())
    excluded.sort(key=lambda r: r["path"].lower())
    aggregate = hashlib.sha256()
    for row in rows:
        aggregate.update(f"{row['path']}\t{row['bytes']}\t{row['sha256']}\n".encode("utf-8"))
    policy = {
        "use_default_excludes": use_default_excludes,
        "include_generated_evidence": include_generated_evidence,
        "default_exclude_dir_names": sorted(dir_names),
        "exclude_prefixes": prefixes,
        "exclude_globs": globs,
        "source_exts": sorted(SOURCE_EXTS),
        "stable_source_count": len(rows),
        "excluded_count": len(excluded),
        "aggregate_fingerprint": aggregate.hexdigest(),
    }
    return rows, excluded, warnings, policy


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="DD-024 report-only redocumentation orchestrator with stable exclusions")
    parser.add_argument("--repo-root", default=".", help="Repo root to scan in dry-run mode")
    parser.add_argument("--out-dir", default="docs/datadict/reports/local-dd024-dry-run", help="Output directory for dry-run report artifacts")
    parser.add_argument("--run-id", default=None, help="Stable run id; default is timestamped")
    parser.add_argument("--profile", action="append", default=["ENGINE", "PROFESSIONAL"], help="Profile scope label; may be repeated")
    parser.add_argument("--plan-only", action="store_true", help="Do not scan files; emit planned steps only")
    parser.add_argument("--no-exclude-defaults", action="store_true", help="Disable DD-024 default exclusions; intended only for diagnostics")
    parser.add_argument("--include-generated-evidence", action="store_true", help="Include docs/datadict generated evidence lanes in the scan deliberately")
    parser.add_argument("--exclude", action="append", default=[], help="Additional exclusion prefix or glob; may be repeated")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir).resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("DD024-DRYRUN-%Y%m%dT%H%M%SZ")

    warnings: list[str] = []
    source_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    exclusion_policy: dict[str, Any] = {}
    if not args.plan_only:
        source_rows, excluded_rows, scan_warnings, exclusion_policy = discover_sources(
            repo_root,
            use_default_excludes=not args.no_exclude_defaults,
            include_generated_evidence=args.include_generated_evidence,
            extra_excludes=args.exclude,
        )
        warnings.extend(scan_warnings)
    else:
        exclusion_policy = {
            "use_default_excludes": not args.no_exclude_defaults,
            "include_generated_evidence": args.include_generated_evidence,
            "default_exclude_dir_names": sorted(DEFAULT_EXCLUDE_DIR_NAMES),
            "exclude_prefixes": DEFAULT_EXCLUDE_PREFIXES,
            "exclude_globs": DEFAULT_EXCLUDE_GLOBS,
            "source_exts": sorted(SOURCE_EXTS),
            "stable_source_count": 0,
            "excluded_count": 0,
            "aggregate_fingerprint": "",
        }

    out_dir.mkdir(parents=True, exist_ok=True)
    source_csv = out_dir / "dd022_source_inventory.csv"  # keep DD-022-compatible output name
    excluded_csv = out_dir / "dd024_excluded_inventory.csv"
    if not args.plan_only:
        write_csv(source_csv, source_rows, ["path", "suffix", "bytes", "sha256", "stable_fingerprint"])
        write_csv(excluded_csv, excluded_rows, ["path", "kind", "reason"])

    steps = []
    gates = []
    for step_no, step_id, phase, gate, notes in STEP_ROWS:
        if step_id in {"OPTIONAL_RUNTIME_PROOF_CAPTURE", "REVIEW_QUEUE_TRIAGE", "PROMOTION", "DOC_REGEN"}:
            status = "BLOCKED"
        elif step_id == "PARSE_TRANSCRIPTS":
            status = "NOT_RUN"
        elif step_id == "SCAN_SOURCES" and not args.plan_only and not source_rows:
            status = "REVIEW"
        elif step_id == "WRITE_RUN_SUMMARY":
            status = "PASS"
        else:
            status = "PLANNED"
        steps.append({"step_no": step_no, "step_id": step_id, "phase": phase, "status": status, "gate": gate, "notes": notes})
        gates.append({"gate": gate, "status": status if status in {"PASS", "REVIEW", "FAIL", "BLOCKED", "NOT_RUN"} else "NOT_RUN", "notes": notes})

    artifacts = []
    for p, kind in [(source_csv, "source_inventory"), (excluded_csv, "excluded_inventory")]:
        if p.exists():
            artifacts.append({"path": str(p), "kind": kind, "sha256": sha256_file(p), "bytes": p.stat().st_size})

    summary_rows = [
        {"metric": "run_id", "value": run_id},
        {"metric": "mode", "value": "plan_only" if args.plan_only else "dry_run"},
        {"metric": "repo_root", "value": str(repo_root)},
        {"metric": "source_files_scanned", "value": str(len(source_rows))},
        {"metric": "excluded_paths", "value": str(len(excluded_rows))},
        {"metric": "warnings", "value": str(len(warnings))},
        {"metric": "blocked_steps", "value": str(sum(1 for s in steps if s["status"] == "BLOCKED"))},
        {"metric": "planned_steps", "value": str(sum(1 for s in steps if s["status"] == "PLANNED"))},
        {"metric": "aggregate_fingerprint", "value": exclusion_policy.get("aggregate_fingerprint", "")},
        {"metric": "default_exclusions_enabled", "value": str(not args.no_exclude_defaults)},
        {"metric": "include_generated_evidence", "value": str(args.include_generated_evidence)},
    ]
    write_csv(out_dir / "dd022_run_summary.csv", summary_rows, ["metric", "value"])
    write_csv(out_dir / "dd022_step_status.csv", steps, ["step_no", "step_id", "phase", "status", "gate", "notes"])

    status = "REVIEW" if warnings else "PASS"
    manifest = {
        "schema_version": "dd024_redoc_orchestrator_run_v0",
        "compat_schema_version": "dd022_redoc_orchestrator_run_v0",
        "run_id": run_id,
        "mode": "plan_only" if args.plan_only else "dry_run",
        "status": status,
        "boundary": "PROMOTION_BLOCKED",
        "profile_scope": args.profile,
        "repo_root": str(repo_root),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "exclusion_policy": exclusion_policy,
        "steps": steps,
        "gates": gates,
        "artifacts": artifacts,
        "warnings": warnings,
        "next_action": "Review stable scan output; do not promote or regenerate docs without explicit authorization.",
    }
    manifest_path = out_dir / "dd022_redoc_run_manifest.json"  # keep existing downstream path stable
    write_json(manifest_path, manifest)
    write_json(out_dir / "dd024_exclusion_policy_effective.json", exclusion_policy)
    print(f"DD-024 dry-run manifest: {manifest_path}")
    print(f"status: {status}; source_files_scanned: {len(source_rows)}; excluded: {len(excluded_rows)}; warnings: {len(warnings)}")
    print(f"aggregate_fingerprint: {exclusion_policy.get('aggregate_fingerprint', '')}")
    return 0 if status in {"PASS", "REVIEW"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
