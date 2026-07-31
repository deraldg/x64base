#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_DD080_STATUS = "DDICT_EVIDENCE_REPRESENTATION_PLAN_READY"
EVIDENCE_FUNCTION = '\nvoid print_evidence(std::istringstream& args) {\n    std::string token;\n    args >> token;\n    token = upper_copy(trim_copy(token));\n\n    if (token.empty()) {\n        std::cout << "DDICT EVIDENCE requires an object id or name.\\n";\n        return;\n    }\n\n    fs::path dir = find_catalog_dir();\n    std::vector<Row> objects = read_dbf_table(dir, "DDOBJECT");\n    std::vector<Row> attrs = read_dbf_table(dir, "DDATTR");\n    std::vector<Row> evids = read_dbf_table(dir, "DDEVID");\n    std::vector<Row> sources = read_dbf_table(dir, "DDSOURCE");\n    std::vector<Row> artifacts = read_dbf_table(dir, "DDARTIF");\n\n    const Row* obj = resolve_object(objects, token);\n\n    std::cout\n        << "DDICT EVIDENCE " << token << "\\n"\n        << "  Active catalog: " << dir.string() << "\\n"\n        << "  Read mode     : READ-ONLY\\n";\n\n    if (!obj) {\n        std::cout\n            << "  Result        : OBJECT_NOT_FOUND\\n"\n            << "  Note          : token was matched against OBJID and DDOBJECT NAME/OWNER.\\n";\n        return;\n    }\n\n    std::string objid = value_of(*obj, "OBJID");\n    std::string objtype = value_of(*obj, "OBJTYPE");\n    std::string name = value_of(*obj, "NAME");\n    std::string owner = value_of(*obj, "OWNER");\n\n    std::vector<const Row*> direct_evidence;\n    for (const auto& ev : evids) {\n        if (value_of(ev, "OBJID") == objid) {\n            direct_evidence.push_back(&ev);\n        }\n    }\n\n    std::vector<const Row*> object_attrs;\n    for (const auto& attr : attrs) {\n        if (value_of(attr, "OBJID") == objid) {\n            object_attrs.push_back(&attr);\n        }\n    }\n\n    std::unordered_map<std::string, const Row*> source_by_id;\n    for (const auto& src : sources) {\n        std::string srcid = value_of(src, "SRCID");\n        if (!srcid.empty()) {\n            source_by_id[srcid] = &src;\n        }\n    }\n\n    std::unordered_map<std::string, const Row*> artifact_by_id;\n    for (const auto& art : artifacts) {\n        std::string artid = value_of(art, "ARTID");\n        if (!artid.empty()) {\n            artifact_by_id[artid] = &art;\n        }\n    }\n\n    std::cout\n        << "  Object OBJID  : " << objid << "\\n"\n        << "  Object type   : " << objtype << "\\n"\n        << "  Object owner  : " << owner << "\\n"\n        << "  Object name   : " << name << "\\n"\n        << "  Direct evidence rows: " << direct_evidence.size() << "\\n"\n        << "  Attribute evidence rows: " << object_attrs.size() << "\\n"\n        << "  Rows shown    : bounded to 20 per section\\n";\n\n    std::cout\n        << "  Evidence rows\\n"\n        << "  EVID                  KIND                  SRCID                 SOURCE              ARTIFACT\\n"\n        << "  --------------------  --------------------  --------------------  ------------------  ------------------\\n";\n\n    std::size_t shown = 0;\n    for (const Row* ev : direct_evidence) {\n        if (shown++ >= 20) {\n            break;\n        }\n        std::string srcid = value_of(*ev, "SRCID");\n        std::string artid = value_of(*ev, "ARTID");\n        const Row* src = nullptr;\n        const Row* art = nullptr;\n        auto sit = source_by_id.find(srcid);\n        if (sit != source_by_id.end()) {\n            src = sit->second;\n        }\n        auto ait = artifact_by_id.find(artid);\n        if (ait != artifact_by_id.end()) {\n            art = ait->second;\n        }\n\n        std::string src_name = src ? (value_of(*src, "PATH").empty() ? value_of(*src, "NAME") : value_of(*src, "PATH")) : "";\n        std::string art_name = art ? (value_of(*art, "PATH").empty() ? value_of(*art, "NAME") : value_of(*art, "PATH")) : "";\n\n        std::cout\n            << "  " << std::left << std::setw(20) << short_text(value_of(*ev, "EVID"), 20)\n            << "  " << std::setw(20) << short_text(value_of(*ev, "KIND"), 20)\n            << "  " << std::setw(20) << short_text(srcid, 20)\n            << "  " << std::setw(18) << short_text(src_name, 18)\n            << "  " << short_text(art_name, 18)\n            << "\\n";\n    }\n\n    if (direct_evidence.empty()) {\n        std::cout << "  (none)\\n";\n    }\n\n    std::cout\n        << "  Attribute evidence\\n"\n        << "  ATTRNAME            ATTRVAL                         EVID\\n"\n        << "  ------------------  ------------------------------  --------------------\\n";\n\n    shown = 0;\n    for (const Row* attr : object_attrs) {\n        if (shown++ >= 20) {\n            break;\n        }\n        std::string attrval = value_of(*attr, "ATTRVAL");\n        if (attrval.empty()) {\n            attrval = value_of(*attr, "ATTRMEMO");\n        }\n        std::cout\n            << "  " << std::left << std::setw(18) << short_text(value_of(*attr, "ATTRNAME"), 18)\n            << "  " << std::setw(30) << short_text(attrval, 30)\n            << "  " << short_text(value_of(*attr, "EVID"), 20)\n            << "\\n";\n    }\n\n    if (object_attrs.empty()) {\n        std::cout << "  (none)\\n";\n    }\n}\n'

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

def stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}

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

def rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()

def diff_text(old: str, new: str, path: str) -> str:
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=path + ".before",
        tofile=path + ".after",
        lineterm="",
    ))

def patch_source(old: str) -> tuple[str, List[Dict[str, Any]]]:
    review: List[Dict[str, Any]] = []
    if "void print_rel(std::istringstream& args)" not in old:
        review.append({"issue": "REL_BASELINE_NOT_FOUND", "detail": "print_rel function not found; expected DD-078 baseline"})
    if "void print_evidence(std::istringstream& args)" in old:
        review.append({"issue": "EVIDENCE_ALREADY_PRESENT", "detail": "print_evidence already exists; no patch should be applied"})

    marker = "\n} // anonymous namespace\n\nvoid cmd_DDICT"
    if marker not in old:
        review.append({"issue": "NAMESPACE_MARKER_NOT_FOUND", "detail": "could not find anonymous namespace closing marker before cmd_DDICT"})
        return old, review

    new = old.replace(marker, "\n" + EVIDENCE_FUNCTION + "\n} // anonymous namespace\n\nvoid cmd_DDICT", 1)

    old_block = (
        '    if (sub == "OBJECTS" || sub == "EVIDENCE") {\n'
        '        print_pending(sub);\n'
        '        return;\n'
        '    }\n'
    )
    new_block = (
        '    if (sub == "EVIDENCE") {\n'
        '        print_evidence(args);\n'
        '        return;\n'
        '    }\n'
        '\n'
        '    if (sub == "OBJECTS") {\n'
        '        print_pending(sub);\n'
        '        return;\n'
        '    }\n'
    )
    if old_block not in new:
        review.append({"issue": "DISPATCH_BLOCK_NOT_FOUND", "detail": "could not find DD-078 OBJECTS/EVIDENCE pending dispatch block"})
        return new, review
    new = new.replace(old_block, new_block, 1)
    return new, review

def main() -> int:
    ap = argparse.ArgumentParser(description="DD-081 guarded DDICT EVIDENCE implementation")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD081-guarded-ddict-evidence-implementation-v0")
    ap.add_argument("--dd080-dir", default="docs/datadict/reports/DD080-ddict-evidence-representation-plan-v0")
    ap.add_argument("--source-path", default="src/cli/cmd_ddict.cpp")
    ap.add_argument("--apply-source-patch", action="store_true")
    ap.add_argument("--backup-root", default="docs/datadict/backups")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd080_dir = (repo / args.dd080_dir).resolve()
    dd080_manifest = read_json(dd080_dir / "dd080_ddict_evidence_representation_plan_manifest.json")
    source = (repo / args.source_path).resolve()
    backup_root = (repo / args.backup_root).resolve()

    old = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    generated, review_rows = patch_source(old)

    generated_dir = out / "generated_source"
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_source = generated_dir / "cmd_ddict.cpp"
    generated_source.write_text(generated, encoding="utf-8")

    preview = diff_text(old, generated, rel(repo, source))
    (out / "dd081_cmd_ddict_evidence_patch_preview.diff").write_text(preview, encoding="utf-8")

    dd080_green = int(dd080_manifest.get("status") == EXPECTED_DD080_STATUS)
    source_exists = int(source.exists())
    existing_has_rel = int("void print_rel" in old and 'sub == "REL"' in old)
    generated_has_evidence = int("void print_evidence" in generated and 'sub == "EVIDENCE"' in generated)
    generated_preserves_rel = int("void print_rel" in generated and 'sub == "REL"' in generated)
    generated_readonly = int("READ-ONLY" in generated and "BUILDLMDB" not in generated and "CDX ADDTAG" not in generated and "REPLACE" not in generated)

    if not dd080_green:
        review_rows.append({"issue": "DD080_NOT_READY", "detail": dd080_manifest.get("status", "")})
    if not source_exists:
        review_rows.append({"issue": "SOURCE_MISSING", "detail": str(source)})
    if not existing_has_rel:
        review_rows.append({"issue": "REL_BASELINE_NOT_DETECTED", "detail": "existing cmd_ddict.cpp does not appear to contain DD-078 REL baseline"})

    failures = len(review_rows)
    patched = 0
    backup_path = ""
    if args.apply_source_patch and failures == 0:
        backup_dir = backup_root / f"{args.run_id}_{stamp()}"
        backup_target = backup_dir / rel(repo, source)
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, backup_target)
        backup_path = str(backup_target)
        source.write_text(generated, encoding="utf-8")
        patched = 1

    if args.apply_source_patch and patched and failures == 0:
        status = "DDICT_EVIDENCE_SOURCE_PATCH_APPLIED_BUILD_REQUIRED"
    elif failures == 0:
        status = "DDICT_EVIDENCE_SOURCE_PATCH_READY"
    else:
        status = "DDICT_EVIDENCE_SOURCE_PATCH_REVIEW"

    gate_rows = [
        {"gate": "dd080_representation_plan_ready", "expected": EXPECTED_DD080_STATUS, "observed": dd080_manifest.get("status", ""), "pass": dd080_green},
        {"gate": "cmd_ddict_source_exists", "expected": 1, "observed": source_exists, "pass": source_exists},
        {"gate": "rel_baseline_detected", "expected": 1, "observed": existing_has_rel, "pass": existing_has_rel},
        {"gate": "generated_evidence_surface", "expected": 1, "observed": generated_has_evidence, "pass": generated_has_evidence},
        {"gate": "generated_rel_preserved", "expected": 1, "observed": generated_preserves_rel, "pass": generated_preserves_rel},
        {"gate": "generated_readonly_surface", "expected": 1, "observed": generated_readonly, "pass": generated_readonly},
        {"gate": "source_patch_applied_when_requested", "expected": int(args.apply_source_patch), "observed": patched, "pass": int((not args.apply_source_patch) or patched == 1)},
    ]

    boundary_rows = [
        {"boundary": "guarded_evidence_source_patch", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "cmd_ddict_cpp_edit", "observed": patched, "required": int(args.apply_source_patch), "pass": int((not args.apply_source_patch) or patched == 1)},
        {"boundary": "registry_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "build_file_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd081_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd081_review_rows.csv", review_rows, ["issue", "detail"])
    write_csv(out / "dd081_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    report = f"""# DD-081 Guarded DDICT EVIDENCE Implementation

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{utc_now()}`

## Purpose

DD-081 implements:

```text
DDICT EVIDENCE <object-id-or-name>
```

The implementation is read-only. It resolves a catalog object and reports bounded
DDEVID and DDATTR evidence rows, with DDSOURCE/DDARTIF decoration when catalog
references are available.

## Target

- Source: `{rel(repo, source)}`
- Generated candidate: `{rel(repo, generated_source)}`
- Patch preview: `{rel(repo, out / 'dd081_cmd_ddict_evidence_patch_preview.diff')}`

## Result

- Apply requested: **{int(args.apply_source_patch)}**
- Source patched: **{patched}**
- Backup path: `{backup_path}`

## Boundary

DD-081 edits only `cmd_ddict.cpp` when `--apply-source-patch` is supplied.
It does not edit registry/build files, mutate active catalog data, append/replace/delete/pack/zap DBFs,
create/rebuild CDX/LMDB, mutate HELP/META/CMDHELPCHK, regenerate catalog content, or repair rows.
"""
    (out / "DD081_GUARDED_DDICT_EVIDENCE_IMPLEMENTATION_REPORT.md").write_text(report, encoding="utf-8")

    manifest = {
        "contract": "dd081_guarded_ddict_evidence_impl_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd080_status": dd080_manifest.get("status", ""),
        "source_path": rel(repo, source),
        "apply_source_patch": int(args.apply_source_patch),
        "patched": patched,
        "backup_path": backup_path,
        "failures": failures,
        "registry_edits": 0,
        "build_file_edits": 0,
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "next_recommended_action": "Build DotTalk++ and run DDICT EVIDENCE DDOBJECT/DDATTR plus REL smoke; then DD-082 closure.",
    }
    write_json(out / "dd081_guarded_ddict_evidence_impl_manifest.json", manifest)

    print(f"DD-081 guarded DDICT EVIDENCE manifest: {out / 'dd081_guarded_ddict_evidence_impl_manifest.json'}")
    print(f"status: {status}; patched: {patched}; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == "__main__":
    raise SystemExit(main())
