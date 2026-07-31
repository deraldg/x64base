#!/usr/bin/env python3
"""Review PHASE23K DotScript transcript and candidate artifacts.

Read-only reviewer. It checks the PHASE23K manifest, transcript markers, and
candidate DBF/CDX/LMDB artifacts. It does not mutate active or candidate data.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PHASE23K_SLUG = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
STAGING_STATUS = "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_STAGING_GREEN_MANUAL_DOTSCRIPT_REQUIRED"
GREEN_STATUS = "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_GREEN_CANDIDATE_ARTIFACTS_PROVEN"
REVIEW_STATUS = "PHASE23K_HELP_LOCALE_CANDIDATE_DBF_CDX_LMDB_BUILD_PROOF_REVIEW_REQUIRED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE23L_CMDHELP_LOCALE_READBACK_PROTOTYPE_PLAN"
TABLES = ["HELP_TOPIC_LOCALE", "HELP_SECTION_LOCALE", "HELP_LINE_LOCALE", "HELP_ARTIFACT_LOCALE"]
BAD_PATTERNS = [
    r"\bfailed\b",
    r"\bfail\b",
    r"\berror\b",
    r"unknown command",
    r"not recognized",
    r"syntax error",
    r"no table open",
    r"could not",
    r"exception",
]
ALLOW_PATTERNS = [
    r"0 failed",
    r"failures: 0",
    r"validation failures 0",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except ValueError:
        return str(path).replace("/", "\\")


def load_manifest(candidate_dir: Path) -> Dict[str, Any]:
    path = candidate_dir / "phase23k_manifest.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def clean_allowed(text: str) -> str:
    cleaned = text
    for pat in ALLOW_PATTERNS:
        cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE)
    return cleaned


def scan_bad_patterns(text: str) -> List[str]:
    cleaned = clean_allowed(text)
    hits: List[str] = []
    for pat in BAD_PATTERNS:
        if re.search(pat, cleaned, flags=re.IGNORECASE):
            hits.append(pat)
    return hits


def artifact_counts(candidate_dir: Path) -> Dict[str, Any]:
    dbf_dir = candidate_dir / "dbf"
    indexes_dir = candidate_dir / "indexes"
    lmdb_dir = candidate_dir / "lmdb"
    dbfs = [dbf_dir / f"{t}.dbf" for t in TABLES]
    cdxs = [indexes_dir / f"{t}.cdx" for t in TABLES]
    # LMDB dirs are normally <table>.cdx.d under the LMDB root.
    lmdbs = [lmdb_dir / f"{t}.cdx.d" for t in TABLES]
    return {
        "candidate_dbf_exists": sum(1 for p in dbfs if p.exists()),
        "candidate_cdx_exists": sum(1 for p in cdxs if p.exists()),
        "candidate_lmdb_exists": sum(1 for p in lmdbs if p.exists()),
        "missing_dbf": [rel(p, candidate_dir.parent.parent.parent.parent) for p in dbfs if not p.exists()],
        "missing_cdx": [rel(p, candidate_dir.parent.parent.parent.parent) for p in cdxs if not p.exists()],
        "missing_lmdb": [rel(p, candidate_dir.parent.parent.parent.parent) for p in lmdbs if not p.exists()],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Review PHASE23K candidate HELP locale DBF/CDX/LMDB proof transcript.")
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--transcript", default=None, help="Optional transcript path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    candidate_dir = repo_root / "docs" / "locale" / "candidates" / PHASE23K_SLUG
    manifest = load_manifest(candidate_dir)
    if not manifest:
        raise SystemExit(f"PHASE23K manifest not found under {candidate_dir}")

    transcript_path = Path(args.transcript).resolve() if args.transcript else repo_root / manifest.get("candidate_paths", {}).get("expected_transcript", "")
    if not transcript_path.exists():
        print(REVIEW_STATUS)
        print(f"candidate_dir: {rel(candidate_dir, repo_root)}")
        print(f"transcript_exists: 0")
        print(f"expected_transcript: {rel(transcript_path, repo_root)}")
        print("reason: run the generated DOTSCRIPT command and capture the transcript first")
        return 1

    text = transcript_path.read_text(encoding="utf-8", errors="ignore")
    marker_checks: Dict[str, int] = {}
    required_markers = ["PHASE23K_DOTSCRIPT_START", "PHASE23K_DOTSCRIPT_END", "PHASE23K_REOPEN_READBACK_START"]
    for table in TABLES:
        required_markers.extend([
            f"PHASE23K_CREATE_TABLE_{table}",
            f"PHASE23K_CREATE_CDX_{table}",
            f"PHASE23K_BUILD_LMDB_{table}",
            f"PHASE23K_READBACK_{table}",
        ])
    for marker in required_markers:
        marker_checks[marker] = 1 if marker in text else 0

    bad_hits = scan_bad_patterns(text)
    counts = artifact_counts(candidate_dir)
    table_count = len(TABLES)
    transcript_markers_ok = 1 if all(marker_checks.values()) else 0
    artifacts_ok = 1 if (
        counts["candidate_dbf_exists"] == table_count and
        counts["candidate_cdx_exists"] == table_count and
        counts["candidate_lmdb_exists"] == table_count
    ) else 0
    no_bad_hits = 1 if not bad_hits else 0
    final_green = 1 if transcript_markers_ok and artifacts_ok and no_bad_hits else 0
    status = GREEN_STATUS if final_green else REVIEW_STATUS

    review = {
        "status": status,
        "created_at": now_utc(),
        "candidate_dir": rel(candidate_dir, repo_root),
        "transcript": rel(transcript_path, repo_root),
        "manifest_status": manifest.get("status"),
        "transcript_markers_ok": transcript_markers_ok,
        "artifacts_ok": artifacts_ok,
        "no_bad_hits": no_bad_hits,
        "bad_pattern_hits": bad_hits,
        "artifact_counts": counts,
        "marker_checks": marker_checks,
        "boundary": {
            "source_files_written": 0,
            "active_help_dbf_written": 0,
            "active_help_cdx_written": 0,
            "active_help_lmdb_written": 0,
            "cmdhelp_behavior_changed": 0,
            "cmdhelpchk_behavior_changed": 0,
            "maint_behavior_changed": 0,
            "bbox_behavior_changed": 0,
            "runtime_execution_by_reviewer": 0,
        },
        "next_gate": NEXT_GATE if final_green else "FIX_OR_RERUN_PHASE23K_DOTSCRIPT",
    }
    out_path = candidate_dir / "phase23k_review_manifest.json"
    out_path.write_text(json.dumps(review, indent=2), encoding="utf-8")

    print(status)
    print(f"candidate_dir: {rel(candidate_dir, repo_root)}")
    print(f"transcript: {rel(transcript_path, repo_root)}")
    print(f"transcript_markers_ok: {transcript_markers_ok}")
    print(f"candidate_dbf_exists: {counts['candidate_dbf_exists']}/{table_count}")
    print(f"candidate_cdx_exists: {counts['candidate_cdx_exists']}/{table_count}")
    print(f"candidate_lmdb_exists: {counts['candidate_lmdb_exists']}/{table_count}")
    print(f"no_bad_hits: {no_bad_hits}")
    if bad_hits:
        print("bad_pattern_hits: " + ", ".join(bad_hits))
    print(f"next_gate: {review['next_gate']}")
    return 0 if final_green else 2


if __name__ == "__main__":
    raise SystemExit(main())
