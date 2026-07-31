#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
PHASE23U_NAME = "PHASE23U-CMDHELP-LOCALE-PREVIEW-SOURCE-CONTRACT-BUILD-SMOKE"

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args()
    repo = Path(args.repo_root).resolve()
    cand = repo / "docs/locale/candidates" / PHASE23U_NAME
    log = cand / "reports/PHASE23U_BUILD_SMOKE_LOG.txt"
    transcript = cand / "transcripts/phase23u_cmdhelp_default_behavior_smoke_probe_transcript.txt"
    src = repo / "src/cli/cmdhelp.cpp"
    log_text = read(log)
    tr = read(transcript)
    src_text = read(src)
    build_started = "PHASE23U_BUILD_SMOKE_START" in log_text
    build_ended = "PHASE23U_BUILD_SMOKE_END" in log_text
    source_contract_marker_present = (("CMDHELP locale preview" in src_text and "PREVIEW LOCALE" in src_text) or ("PHASE23T" in src_text and "CMDHELP" in src_text and "locale" in src_text))
    transcript_exists = transcript.exists()
    transcript_markers_ok = all(x in tr for x in ["PHASE23U_DOTSCRIPT_START", "PHASE23U_SCOPE_DEFAULT_CMDHELP_BEHAVIOR_UNCHANGED_SMOKE", "PHASE23U_DOTSCRIPT_END"])
    cmdhelp_area_seen = "CMDHELP AREA" in tr and ("AREA" in tr or "DOT|AREA" in tr)
    usage_area_seen = "CMDHELP USAGE AREA" in tr or "USAGE AREA" in tr
    bad_patterns = ["not recognized", "fatal error", "error C", "cmake build failed"]
    bad_hits = [p for p in bad_patterns if p.lower() in (log_text + tr).lower()]
    green = build_started and build_ended and source_contract_marker_present and transcript_markers_ok and cmdhelp_area_seen and usage_area_seen and not bad_hits
    print("PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_GREEN" if green else "PHASE23U_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT_BUILD_SMOKE_REVIEW_REQUIRED")
    print(f"candidate_dir: docs\\locale\\candidates\\{PHASE23U_NAME}")
    print(f"build_log_exists: {1 if log.exists() else 0}")
    print(f"build_started: {1 if build_started else 0}")
    print(f"build_ended: {1 if build_ended else 0}")
    print(f"source_contract_marker_present: {1 if source_contract_marker_present else 0}")
    print(f"transcript_exists: {1 if transcript_exists else 0}")
    print(f"transcript_markers_ok: {1 if transcript_markers_ok else 0}")
    print(f"cmdhelp_area_seen: {1 if cmdhelp_area_seen else 0}")
    print(f"usage_area_seen: {1 if usage_area_seen else 0}")
    print(f"bad_hits_count: {len(bad_hits)}")
    print("source_files_written_by_review: 0")
    print("cmdhelp_behavior_changed_by_review: 0")
    print("active_help_dbf_written_by_review: 0")
    print("active_help_cdx_written_by_review: 0")
    print("active_help_lmdb_written_by_review: 0")
    print("next_gate: HOLD_OR_AUTHORIZE_PHASE23V_CMDHELP_LOCALE_PREVIEW_BEHAVIOR_PATCH_PLAN" if green else "FIX_OR_RERUN_PHASE23U_BUILD_OR_DOTSCRIPT_SMOKE")
    return 0 if green else 1
if __name__ == "__main__":
    raise SystemExit(main())
