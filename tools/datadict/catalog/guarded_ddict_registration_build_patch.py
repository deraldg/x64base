#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import difflib
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


EXPECTED_DD066R_STATUS = "DDICT_REGISTRATION_BUILD_TARGET_REFINEMENT_READY"


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unified_diff(old: str, new: str, fromfile: str, tofile: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
            lineterm="",
        )
    )


def get_accepted_target(rows: List[Dict[str, str]], kind: str) -> str:
    for row in rows:
        if row.get("target_kind") == kind:
            return row.get("accepted_path", "")
    return ""


def patch_cmake(cmake_text: str) -> Tuple[str, Dict[str, Any]]:
    if "cmd_ddict.cpp" in cmake_text:
        return cmake_text, {
            "patch_needed": 0,
            "patch_possible": 1,
            "reason": "cmd_ddict.cpp already present",
            "insert_after": "",
        }

    lines = cmake_text.splitlines()
    # Prefer active source list entries using cli/cmd_*.cpp, usually inside src/CMakeLists.txt.
    cmd_indices = []
    for idx, line in enumerate(lines):
        if re.search(r"(^|\s)(cli/)?cmd_[A-Za-z0-9_]+\.cpp(\s|$)", line):
            cmd_indices.append(idx)

    if not cmd_indices:
        return cmake_text, {
            "patch_needed": 1,
            "patch_possible": 0,
            "reason": "no cli/cmd_*.cpp source-list anchor found",
            "insert_after": "",
        }

    # Prefer inserting after cmd_catalogcanary.cpp when present, else after the last cmd_ entry.
    anchor_idx = None
    for idx in cmd_indices:
        if "cmd_catalogcanary.cpp" in lines[idx]:
            anchor_idx = idx
            break
    if anchor_idx is None:
        anchor_idx = cmd_indices[-1]

    anchor_line = lines[anchor_idx]
    leading = anchor_line[: len(anchor_line) - len(anchor_line.lstrip())]
    if "cli/" in anchor_line:
        new_entry = f"{leading}cli/cmd_ddict.cpp"
    else:
        new_entry = f"{leading}cmd_ddict.cpp"

    new_lines = lines[: anchor_idx + 1] + [new_entry] + lines[anchor_idx + 1 :]
    return "\n".join(new_lines) + ("\n" if cmake_text.endswith("\n") else ""), {
        "patch_needed": 1,
        "patch_possible": 1,
        "reason": "inserted cmd_ddict.cpp after active cmd source anchor",
        "insert_after": anchor_line.strip(),
        "new_entry": new_entry.strip(),
    }


def insert_include(reg_text: str) -> Tuple[str, Dict[str, Any]]:
    if "cmd_ddict.hpp" in reg_text:
        return reg_text, {
            "patch_needed": 0,
            "patch_possible": 1,
            "reason": "cmd_ddict.hpp include already present",
            "insert_after": "",
        }

    lines = reg_text.splitlines()
    include_indices = []
    for idx, line in enumerate(lines):
        if re.match(r'\s*#\s*include\s+[<"].*cmd_.*[>"]', line):
            include_indices.append(idx)

    if not include_indices:
        # Also allow a generic include block if present.
        for idx, line in enumerate(lines):
            if re.match(r'\s*#\s*include\s+', line):
                include_indices.append(idx)

    if not include_indices:
        return reg_text, {
            "patch_needed": 1,
            "patch_possible": 0,
            "reason": "no include anchor found in registry file",
            "insert_after": "",
        }

    anchor_idx = include_indices[-1]
    include_line = '#include "cli/cmd_ddict.hpp"'
    new_lines = lines[: anchor_idx + 1] + [include_line] + lines[anchor_idx + 1 :]
    return "\n".join(new_lines) + ("\n" if reg_text.endswith("\n") else ""), {
        "patch_needed": 1,
        "patch_possible": 1,
        "reason": "inserted cmd_ddict.hpp include after include anchor",
        "insert_after": lines[anchor_idx].strip(),
        "new_entry": include_line,
    }


def find_registration_template(lines: List[str]) -> Optional[Tuple[int, str, str]]:
    # Look for a known command registration line and mirror it.
    known = [
        ("CATALOGCANARY", "cmd_CATALOGCANARY"),
        ("ABOUT", "cmd_ABOUT"),
        ("HELP", "cmd_HELP"),
        ("AREA", "cmd_AREA"),
        ("COUNT", "cmd_COUNT"),
        ("LIST", "cmd_LIST"),
        ("USE", "cmd_USE"),
        ("CALC", "cmd_CALC"),
    ]
    for idx, line in enumerate(lines):
        upper = line.upper()
        for cmd_name, fn_name in known:
            if cmd_name in upper and re.search(r"\bcmd_[A-Za-z0-9_]+\b", line):
                return idx, cmd_name, line
    # Fallback: any line with a cmd_ symbol inside command registry implementation.
    for idx, line in enumerate(lines):
        if re.search(r"\bcmd_[A-Za-z0-9_]+\b", line) and ("register" in line.lower() or '"' in line):
            return idx, "", line
    return None


def mirror_registration_line(template: str) -> Optional[str]:
    line = template

    # Replace the most likely command string token with DDICT.
    string_tokens = list(re.finditer(r'"([A-Za-z][A-Za-z0-9_ -]*)"', line))
    if not string_tokens:
        return None

    # Prefer command-looking tokens.
    chosen = None
    for m in string_tokens:
        token = m.group(1)
        if token.upper() in {"ABOUT", "HELP", "AREA", "COUNT", "LIST", "USE", "CALC", "CATALOGCANARY"}:
            chosen = m
            break
    if chosen is None:
        chosen = string_tokens[0]

    line = line[: chosen.start()] + '"DDICT"' + line[chosen.end() :]

    # Replace function symbol with cmd_DDICT.
    line2 = re.sub(r"\bcmd_[A-Za-z0-9_]+\b", "cmd_DDICT", line, count=1)
    if line2 == line:
        return None

    # Avoid creating duplicate semicolon issues; preserve indentation.
    return line2


def patch_registry(reg_text: str) -> Tuple[str, Dict[str, Any]]:
    if re.search(r'"DDICT"', reg_text) or "cmd_DDICT" in reg_text:
        return reg_text, {
            "patch_needed": 0,
            "patch_possible": 1,
            "reason": "DDICT registry reference already present",
            "insert_after": "",
        }

    lines = reg_text.splitlines()
    template = find_registration_template(lines)
    if template is None:
        return reg_text, {
            "patch_needed": 1,
            "patch_possible": 0,
            "reason": "no recognizable command registration template found",
            "insert_after": "",
        }

    anchor_idx, cmd_name, template_line = template
    new_line = mirror_registration_line(template_line)
    if not new_line:
        return reg_text, {
            "patch_needed": 1,
            "patch_possible": 0,
            "reason": "registration template could not be mirrored safely",
            "insert_after": template_line.strip(),
        }

    new_lines = lines[: anchor_idx + 1] + [new_line] + lines[anchor_idx + 1 :]
    return "\n".join(new_lines) + ("\n" if reg_text.endswith("\n") else ""), {
        "patch_needed": 1,
        "patch_possible": 1,
        "reason": "inserted mirrored DDICT registration line",
        "insert_after": template_line.strip(),
        "new_entry": new_line.strip(),
    }


def patch_registry_file(reg_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    after_include, include_info = insert_include(reg_text)
    include_info["patch_part"] = "include"
    rows.append(include_info)

    after_reg, reg_info = patch_registry(after_include)
    reg_info["patch_part"] = "registration"
    rows.append(reg_info)
    return after_reg, rows


def backup_file(repo: Path, backup_dir: Path, path: Path) -> Path:
    rel = path.resolve().relative_to(repo.resolve())
    dest = backup_dir / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-067 guarded DDICT registration/build patch")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD067-guarded-ddict-registration-build-patch-v0")
    ap.add_argument("--dd066r-dir", default="docs/datadict/reports/DD066R-ddict-registration-build-target-refinement-final-v0")
    ap.add_argument("--fallback-dd066r-dir", default="docs/datadict/reports/DD066R-ddict-registration-build-target-refinement-v0")
    ap.add_argument("--apply-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd066r_dir = (repo / args.dd066r_dir).resolve()
    if not dd066r_dir.exists():
        dd066r_dir = (repo / args.fallback_dd066r_dir).resolve()
    backup_root = (repo / args.backup_root).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd066r_manifest = read_json(dd066r_dir / "dd066r_ddict_registration_build_target_refinement_manifest.json")
    targets = read_csv_dict(dd066r_dir / "dd066r_accepted_patch_targets.csv")

    reg_target = get_accepted_target(targets, "registration")
    build_target = get_accepted_target(targets, "build")
    smoke_target = get_accepted_target(targets, "smoke")

    reg_path = (repo / reg_target).resolve() if reg_target else repo / "MISSING_REGISTRATION_TARGET"
    build_path = (repo / build_target).resolve() if build_target else repo / "MISSING_BUILD_TARGET"
    smoke_path = (repo / smoke_target).resolve() if smoke_target else repo / "MISSING_SMOKE_TARGET"

    dd066r_ready = dd066r_manifest.get("status") == EXPECTED_DD066R_STATUS

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if not dd066r_ready:
        failures += 1
        review_rows.append({"issue": "DD066R_NOT_READY", "detail": dd066r_manifest.get("status", "")})
    for label, path in [("registration", reg_path), ("build", build_path), ("smoke", smoke_path)]:
        if not path.exists():
            failures += 1
            review_rows.append({"issue": f"{label.upper()}_TARGET_MISSING", "detail": str(path)})

    patch_rows: List[Dict[str, Any]] = []
    diff_texts: List[str] = []
    reg_new = ""
    build_new = ""
    reg_old = ""
    build_old = ""

    if failures == 0:
        reg_old = read_text(reg_path)
        build_old = read_text(build_path)
        reg_new, reg_patch_rows = patch_registry_file(reg_old)
        build_new, build_info = patch_cmake(build_old)
        build_info["patch_part"] = "build_source_entry"

        for row in reg_patch_rows:
            row["target"] = safe_rel(repo, reg_path)
            patch_rows.append(row)
        build_info["target"] = safe_rel(repo, build_path)
        patch_rows.append(build_info)

        for row in patch_rows:
            if int(row.get("patch_needed", 0)) == 1 and int(row.get("patch_possible", 0)) != 1:
                failures += 1
                review_rows.append({
                    "issue": "PATCH_NOT_POSSIBLE",
                    "detail": f"{row.get('patch_part')} {row.get('target')} {row.get('reason')}",
                })

        if reg_new != reg_old:
            diff_texts.append(unified_diff(reg_old, reg_new, safe_rel(repo, reg_path) + ".before", safe_rel(repo, reg_path) + ".after"))
        if build_new != build_old:
            diff_texts.append(unified_diff(build_old, build_new, safe_rel(repo, build_path) + ".before", safe_rel(repo, build_path) + ".after"))

    preview_diff = "\n".join(diff_texts)
    (out / "dd067_patch_preview.diff").write_text(preview_diff, encoding="utf-8")

    backup_dir = ""
    files_patched = 0
    if args.apply_patch and failures == 0:
        backup_dir_path = backup_root / f"{args.run_id}_{stamp()}"
        backup_file(repo, backup_dir_path, reg_path)
        backup_file(repo, backup_dir_path, build_path)
        backup_dir = str(backup_dir_path)

        if reg_new != reg_old:
            write_text(reg_path, reg_new)
            files_patched += 1
        if build_new != build_old:
            write_text(build_path, build_new)
            files_patched += 1

    applied = int(args.apply_patch and failures == 0)
    if args.apply_patch:
        status = "DDICT_REGISTRATION_BUILD_PATCH_APPLIED_BUILD_REQUIRED" if failures == 0 else "DDICT_REGISTRATION_BUILD_PATCH_REVIEW"
    else:
        status = "DDICT_REGISTRATION_BUILD_PATCH_READY" if failures == 0 else "DDICT_REGISTRATION_BUILD_PATCH_REVIEW"

    gate_rows = [
        {"gate": "dd066r_target_refinement_ready", "expected": EXPECTED_DD066R_STATUS, "observed": dd066r_manifest.get("status", ""), "pass": int(dd066r_ready)},
        {"gate": "registration_target_exists", "expected": 1, "observed": int(reg_path.exists()), "pass": int(reg_path.exists())},
        {"gate": "build_target_exists", "expected": 1, "observed": int(build_path.exists()), "pass": int(build_path.exists())},
        {"gate": "smoke_target_exists", "expected": 1, "observed": int(smoke_path.exists()), "pass": int(smoke_path.exists())},
        {"gate": "patch_preview_written", "expected": 1, "observed": int((out / "dd067_patch_preview.diff").exists()), "pass": int((out / "dd067_patch_preview.diff").exists())},
        {"gate": "patch_parts_possible", "expected": 1, "observed": int(failures == 0), "pass": int(failures == 0)},
        {"gate": "patch_applied_when_requested", "expected": int(args.apply_patch), "observed": applied, "pass": int((not args.apply_patch) or applied == 1)},
    ]

    boundary_rows = [
        {"boundary": "guarded_registration_build_patch", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cxx_source_or_build_edits", "observed": files_patched, "required": files_patched if args.apply_patch else 0, "pass": int((args.apply_patch and files_patched >= 0) or (not args.apply_patch and files_patched == 0))},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "catalog_regeneration", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd067_patch_part_ledger.csv", patch_rows, ["patch_part", "target", "patch_needed", "patch_possible", "reason", "insert_after", "new_entry"])
    write_csv(out / "dd067_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd067_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd067_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    build_next = "\n".join([
        "# DD-067 Build / Smoke Next Steps",
        "",
        "After apply is green:",
        "",
        "```powershell",
        "cmake --build D:\\code\\ccode\\build\\x64-windows-rel --config Release",
        "# or the local build command currently used for DotTalk++",
        "```",
        "",
        "Then run DotTalk++ and test:",
        "",
        "```text",
        "ddict help",
        "```",
        "",
        "If build fails, do not continue to HELP/CMDHELPCHK. Inspect compiler diagnostics first.",
        "",
    ])
    (out / "DD067_BUILD_AND_SMOKE_NEXT_STEPS.md").write_text(build_next, encoding="utf-8")

    report = "\n".join([
        "# DD-067 Guarded DDICT Registration / Build Patch",
        "",
        f"Run id: `{args.run_id}`",
        f"Status: **{status}**",
        f"Created UTC: `{utc_now()}`",
        "",
        "## Purpose",
        "",
        "DD-067 patches the accepted active registration/build targets for the DDICT command only when `--apply-patch` is used.",
        "",
        "## Targets",
        "",
        f"- Registration: `{safe_rel(repo, reg_path)}`",
        f"- Build: `{safe_rel(repo, build_path)}`",
        f"- Smoke: `{safe_rel(repo, smoke_path)}`",
        "",
        "## Result",
        "",
        f"- Apply requested: **{int(args.apply_patch)}**",
        f"- Applied: **{applied}**",
        f"- Files patched: **{files_patched}**",
        f"- Backup dir: `{backup_dir}`",
        "",
        "## Boundary",
        "",
        "DD-067 does not mutate the active catalog, DBF/CDX/LMDB artifacts, HELP/META/CMDHELPCHK, catalog content, or manual rows.",
        "",
    ])
    (out / "DD067_GUARDED_DDICT_REGISTRATION_BUILD_PATCH_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd067_guarded_ddict_registration_build_patch_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd066r_status": dd066r_manifest.get("status", ""),
        "registration_target": safe_rel(repo, reg_path),
        "build_target": safe_rel(repo, build_path),
        "smoke_target": safe_rel(repo, smoke_path),
        "apply_patch": int(args.apply_patch),
        "applied": applied,
        "files_patched": files_patched,
        "backup_dir": backup_dir,
        "failures": failures,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Build DotTalk++ and run DDICT HELP smoke; then DD-068 runtime smoke closure.",
    }
    write_json(out / "dd067_guarded_ddict_registration_build_patch_manifest.json", manifest)

    print(f"DD-067 guarded DDICT registration/build patch manifest: {out / 'dd067_guarded_ddict_registration_build_patch_manifest.json'}")
    print(f"status: {status}; applied: {applied}; files_patched: {files_patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
