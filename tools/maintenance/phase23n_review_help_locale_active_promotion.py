#!/usr/bin/env python3
"""Review PHASE23N active HELP locale promotion after the local apply script has run."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

CANDIDATE_NAME = "PHASE23N-HELP-LOCALE-ACTIVE-PROMOTION-EXECUTION-STAGING"
PHASE23K_NAME = "PHASE23K-HELP-LOCALE-CANDIDATE-DBF-CDX-LMDB-BUILD-PROOF"
TABLES = ["HELP_TOPIC_LOCALE", "HELP_SECTION_LOCALE", "HELP_LINE_LOCALE", "HELP_ARTIFACT_LOCALE"]
GREEN = "PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_REVIEW_GREEN_ACTIVE_ARTIFACTS_MATCH_CANDIDATE"
REQUIRED = "PHASE23N_HELP_LOCALE_ACTIVE_PROMOTION_REVIEW_REQUIRED"


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def norm(s: str) -> str:
    return s.replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        return ""
    for p in sorted([x for x in path.rglob("*") if x.is_file()]):
        rp = str(p.relative_to(path)).replace("\\", "/")
        h.update(rp.encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\0")
    return h.hexdigest()


def artifact_hash(path: Path) -> str:
    if path.is_dir():
        return sha256_dir(path)
    if path.is_file():
        return sha256_file(path)
    return ""


def artifact_pairs(repo: Path):
    kroot = repo / "docs" / "locale" / "candidates" / PHASE23K_NAME
    for table in TABLES:
        yield table, "DBF", kroot / "dbf" / f"{table}.dbf", repo / "dottalkpp" / "data" / "HELP" / f"{table}.dbf"
        yield table, "CDX", kroot / "indexes" / f"{table}.cdx", repo / "dottalkpp" / "data" / "INDEXES" / "HELP" / f"{table}.cdx"
        yield table, "LMDB", kroot / "lmdb" / f"{table}.cdx.d", repo / "dottalkpp" / "data" / "LMDB" / "HELP" / f"{table}.cdx.d"


def read_apply_log(cdir: Path) -> str:
    p = cdir / "reports" / "PHASE23N_APPLY_ACTIVE_PROMOTION_LOG.txt"
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    cdir = repo / "docs" / "locale" / "candidates" / CANDIDATE_NAME

    rows: List[Dict[str, Any]] = []
    match_count = 0
    cand_dbf = cand_cdx = cand_lmdb = 0
    active_dbf = active_cdx = active_lmdb = 0
    for table, kind, src, dst in artifact_pairs(repo):
        se = src.exists()
        de = dst.exists()
        if kind == "DBF" and se: cand_dbf += 1
        if kind == "CDX" and se: cand_cdx += 1
        if kind == "LMDB" and se: cand_lmdb += 1
        if kind == "DBF" and de: active_dbf += 1
        if kind == "CDX" and de: active_cdx += 1
        if kind == "LMDB" and de: active_lmdb += 1
        sh = artifact_hash(src)
        dh = artifact_hash(dst)
        ok = bool(se and de and sh and sh == dh)
        if ok:
            match_count += 1
        rows.append({"table": table, "kind": kind, "source": rel(src, repo), "target": rel(dst, repo), "source_exists": se, "target_exists": de, "hash_match": ok})

    apply_log = read_apply_log(cdir)
    apply_started = int("PHASE23N_APPLY_ACTIVE_PROMOTION_START" in apply_log)
    apply_ended = int("PHASE23N_APPLY_ACTIVE_PROMOTION_END" in apply_log)
    copied_match = re.search(r"copied_artifacts=(\d+)", apply_log)
    copied_artifacts = int(copied_match.group(1)) if copied_match else 0
    active_promotion_executed = int(match_count == 12 and apply_started and apply_ended and copied_artifacts >= 12)

    reports = cdir / "reports"
    manifests = cdir / "manifests"
    reports.mkdir(parents=True, exist_ok=True)
    manifests.mkdir(parents=True, exist_ok=True)
    manifest = {
        "phase": "PHASE23N",
        "status": GREEN if active_promotion_executed else REQUIRED,
        "candidate_dir": str(cdir),
        "candidate_dbf_exists": f"{cand_dbf}/4",
        "candidate_cdx_exists": f"{cand_cdx}/4",
        "candidate_lmdb_exists": f"{cand_lmdb}/4",
        "active_dbf_exists": f"{active_dbf}/4",
        "active_cdx_exists": f"{active_cdx}/4",
        "active_lmdb_exists": f"{active_lmdb}/4",
        "hash_match_count": f"{match_count}/12",
        "apply_log_exists": int(bool(apply_log)),
        "apply_started": apply_started,
        "apply_ended": apply_ended,
        "copied_artifacts": copied_artifacts,
        "active_promotion_executed": active_promotion_executed,
        "artifacts": rows,
        "source_files_written": 0,
        "cmdhelp_behavior_changed": 0,
        "cmdhelpchk_behavior_changed": 0,
        "maint_behavior_changed": 0,
        "bbox_behavior_changed": 0,
        "next_gate": "HOLD_OR_AUTHORIZE_PHASE23O_ACTIVE_HELP_LOCALE_READBACK_PROOF" if active_promotion_executed else "RUN_PHASE23N_APPLY_SCRIPT_OR_FIX_ACTIVE_ARTIFACTS",
    }
    (manifests / "phase23n_help_locale_active_promotion_review_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(manifest["status"])
    print(f"candidate_dir: {norm(rel(cdir, repo))}")
    print(f"candidate_dbf_exists: {cand_dbf}/4")
    print(f"candidate_cdx_exists: {cand_cdx}/4")
    print(f"candidate_lmdb_exists: {cand_lmdb}/4")
    print(f"active_dbf_exists: {active_dbf}/4")
    print(f"active_cdx_exists: {active_cdx}/4")
    print(f"active_lmdb_exists: {active_lmdb}/4")
    print(f"hash_match_count: {match_count}/12")
    print(f"apply_log_exists: {int(bool(apply_log))}")
    print(f"apply_started: {apply_started}")
    print(f"apply_ended: {apply_ended}")
    print(f"copied_artifacts: {copied_artifacts}")
    print("active_help_dbf_written_by_review: 0")
    print("active_help_cdx_written_by_review: 0")
    print("active_help_lmdb_written_by_review: 0")
    print("source_files_written: 0")
    print("cmdhelp_behavior_changed: 0")
    print("cmdhelpchk_behavior_changed: 0")
    print("maint_behavior_changed: 0")
    print("bbox_behavior_changed: 0")
    print(f"active_promotion_executed: {active_promotion_executed}")
    print(f"next_gate: {manifest['next_gate']}")
    return 0 if active_promotion_executed else 1


if __name__ == "__main__":
    raise SystemExit(main())
