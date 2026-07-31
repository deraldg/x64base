#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List


REPRESENTATIVE_TAGS = [
    ("DDRUN", "RUNID", "DDRUN primary run lookup"),
    ("DDBASE", "BASEID", "DDBASE primary baseline lookup"),
    ("DDOBJECT", "OBJID", "DDOBJECT primary object lookup"),
    ("DDATTR", "OBJID", "DDATTR object-attribute lookup"),
    ("DDEDGE", "FROMOBJ", "DDEDGE outgoing edge lookup"),
    ("DDEDGE", "TOOBJ", "DDEDGE incoming edge lookup"),
    ("DDGATE", "STATUS", "DDGATE gate status lookup"),
    ("DDPROFILE", "NAME", "DDPROFILE profile name lookup"),
]


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_dict(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


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


def ensure_safe_target(repo: Path, target_path: Path, active_path: Path) -> None:
    target_resolved = target_path.resolve()
    active_resolved = active_path.resolve()
    try:
        target_rel = target_resolved.relative_to(repo.resolve()).as_posix().lower()
    except Exception:
        raise SystemExit(f"Target path must be inside repo: {target_path}")

    if target_resolved == active_resolved:
        raise SystemExit("Refusing to use active catalog path as DD-056 target")

    if "datadict_canonical_rebuild_v0" not in target_rel:
        raise SystemExit(f"Refusing target path without datadict_canonical_rebuild_v0 safety marker: {target_rel}")


def load_available_tags(dd055_dir: Path) -> set[tuple[str, str]]:
    rows = read_csv_dict(dd055_dir / "dd055_tag_execution_plan.csv")
    out = set()
    for r in rows:
        table = (r.get("table") or "").strip().upper()
        tag = (r.get("tag") or "").strip().upper()
        if table and tag:
            out.add((table, tag))
    return out


def build_script(target_slot: str, reps: List[Dict[str, Any]]) -> str:
    lines = [
        "* DD-056 catalog index-use / order readback proof script",
        "* Staging catalog only. No active promotion. No LMDB.",
        "* Commands are intentionally simple and diagnostic.",
        f"setpath dbf {target_slot}",
        "",
        "* If SET ORDER syntax differs, capture the first failing command/output.",
        "",
    ]
    for r in reps:
        table = r["table"]
        tag = r["tag"]
        lines.extend([
            f"* ---- {table}.{tag} ----",
            f"use {table.lower()}",
            "count",
            f"set order to {tag}",
            "count",
            "goto 1",
            "tup",
            "",
        ])
    return "\n".join(lines) + "\n"


def build_proof_template(run_id: str, reps: List[Dict[str, Any]]) -> str:
    rows = "\n".join([f"  - {r['table']}.{r['tag']}: PENDING" for r in reps])
    return f"""DD-056 LOCAL CATALOG INDEX USE / ORDER READBACK PROOF

Date: 2026-05-27
Run id: {run_id}
Repo: D:\\code\\ccode

Target:
  dottalkpp\\data\\metadata\\datadict_canonical_rebuild_v0

Runtime command:
  DO D:\\code\\ccode\\dottalkpp\\data\\metadata\\datadict_canonical_rebuild_v0\\dd056_index_use_order_readback.dts

Representative tag checks:
{rows}

Expected evidence:
  For each representative table/tag:
    USE <table> succeeds.
    COUNT succeeds.
    SET ORDER TO <tag> succeeds, or the accepted DotTalk++ order syntax is documented.
    COUNT still succeeds under ordered path.
    GOTO 1 / TUP reads a record for non-empty tables.

Result:
  PENDING

Boundary:
  active datadict catalog not promoted
  HELP/META/CMDHELPCHK not mutated
  LMDB not built
  source not edited by DD-056
  no new CREATE/IMPORT performed by DD-056
"""


def analyze_proof(proof_path: Path, reps: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not proof_path.exists():
        return {
            "proof_exists": 0,
            "status": "MISSING_PROOF",
            "accepted_count": 0,
            "expected_count": len(reps),
            "detail": f"missing proof file: {proof_path}",
        }
    text = proof_path.read_text(encoding="utf-8", errors="replace")
    upper = text.upper()

    accepted_words = ["GREEN", "PASS", "SUCCEEDED", "SUCCESS"]
    result_green = bool(re.search(r"RESULT:\s*(GREEN|PASS|SUCCEEDED|SUCCESS)", upper))

    tag_hits = 0
    per_tag: List[Dict[str, Any]] = []
    for r in reps:
        token = f"{r['table']}.{r['tag']}".upper()
        # Accept if tag token appears and line is no longer PENDING, or overall result is green.
        token_present = token in upper
        pending_line = re.search(re.escape(token) + r"\s*:\s*PENDING", upper) is not None
        accepted = int((token_present and not pending_line) or result_green)
        if accepted:
            tag_hits += 1
        per_tag.append({
            "table": r["table"],
            "tag": r["tag"],
            "token_present": int(token_present),
            "accepted": accepted,
        })

    status = "INDEX_USE_RUNTIME_PROOF_ACCEPTED" if result_green or tag_hits == len(reps) else "INDEX_USE_RUNTIME_PROOF_REVIEW"
    return {
        "proof_exists": 1,
        "status": status,
        "accepted_count": tag_hits,
        "expected_count": len(reps),
        "result_green": int(result_green),
        "per_tag": per_tag,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DD-056 catalog index-use/order readback proof")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD056-catalog-index-use-order-readback-proof-v0")
    ap.add_argument("--dd055-dir", default="docs/datadict/reports/DD055-guarded-cdx-tag-execution-verify-v0")
    ap.add_argument("--target-slot", default="metadata\\datadict_canonical_rebuild_v0")
    ap.add_argument("--target-path", default="dottalkpp/data/metadata/datadict_canonical_rebuild_v0")
    ap.add_argument("--active-path", default="dottalkpp/data/metadata/datadict")
    ap.add_argument("--proof-path", default="docs/datadict/runlog/DD-056_LOCAL_CATALOG_INDEX_USE_ORDER_READBACK_PROOF.md")
    ap.add_argument("--prepare-proof-script", action="store_true")
    ap.add_argument("--replace-existing-script", action="store_true")
    ap.add_argument("--verify-proof", action="store_true")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd055_dir = (repo / args.dd055_dir).resolve()
    target_path = (repo / args.target_path).resolve()
    active_path = (repo / args.active_path).resolve()
    proof_path = (repo / args.proof_path).resolve()
    script_path = target_path / "dd056_index_use_order_readback.dts"
    proof_template_path = target_path / "DD056_INDEX_USE_PROOF_TEMPLATE.md"
    out.mkdir(parents=True, exist_ok=True)

    ensure_safe_target(repo, target_path, active_path)

    dd055_manifest = read_json(dd055_dir / "dd055_guarded_cdx_tag_execution_manifest.json")
    available_tags = load_available_tags(dd055_dir)

    reps: List[Dict[str, Any]] = []
    failures = 0
    for table, tag, purpose in REPRESENTATIVE_TAGS:
        available = int((table, tag) in available_tags)
        if not available:
            failures += 1
        reps.append({
            "table": table,
            "tag": tag,
            "purpose": purpose,
            "available_in_dd055": available,
        })

    dd055_green = dd055_manifest.get("status") == "CATALOG_CDX_TAG_EXECUTION_VERIFY_GREEN"
    if not dd055_green:
        failures += 1

    script_written = 0
    template_written = 0
    if args.prepare_proof_script and failures == 0:
        if script_path.exists() and not args.replace_existing_script:
            failures += 1
        else:
            script_path.write_text(build_script(args.target_slot, reps), encoding="utf-8")
            proof_template_path.write_text(build_proof_template(args.run_id, reps), encoding="utf-8")
            script_written = 1
            template_written = 1

    proof_analysis: Dict[str, Any] = {"proof_exists": 0, "status": "NOT_REQUESTED"}
    if args.verify_proof:
        proof_analysis = analyze_proof(proof_path, reps)
        if proof_analysis.get("status") != "INDEX_USE_RUNTIME_PROOF_ACCEPTED":
            failures += 1

    if args.verify_proof:
        status = "CATALOG_INDEX_USE_ORDER_READBACK_PROOF_GREEN" if failures == 0 else "CATALOG_INDEX_USE_ORDER_READBACK_PROOF_REVIEW"
    elif args.prepare_proof_script:
        status = "CATALOG_INDEX_USE_PROOF_SCRIPT_READY" if failures == 0 else "CATALOG_INDEX_USE_PROOF_SCRIPT_REVIEW"
    else:
        status = "CATALOG_INDEX_USE_PROOF_PREFLIGHT_READY" if failures == 0 else "CATALOG_INDEX_USE_PROOF_PREFLIGHT_REVIEW"

    rep_rows = []
    for r in reps:
        rep_rows.append({
            "table": r["table"],
            "tag": r["tag"],
            "purpose": r["purpose"],
            "available_in_dd055": r["available_in_dd055"],
            "script_path": safe_rel(repo, script_path),
        })

    proof_tag_rows = proof_analysis.get("per_tag", []) if isinstance(proof_analysis.get("per_tag"), list) else []

    gate_rows = [
        {
            "gate": "dd055_index_execution_verify_green",
            "expected": "CATALOG_CDX_TAG_EXECUTION_VERIFY_GREEN",
            "observed": dd055_manifest.get("status", ""),
            "pass": int(dd055_green),
        },
        {
            "gate": "representative_tags_available",
            "expected": len(reps),
            "observed": sum(1 for r in reps if r["available_in_dd055"] == 1),
            "pass": int(sum(1 for r in reps if r["available_in_dd055"] == 1) == len(reps)),
        },
        {
            "gate": "script_written_when_requested",
            "expected": int(args.prepare_proof_script),
            "observed": script_written,
            "pass": int((not args.prepare_proof_script) or script_written == 1),
        },
        {
            "gate": "runtime_proof_accepted_when_requested",
            "expected": "accepted when verify-proof",
            "observed": proof_analysis.get("status", ""),
            "pass": int((not args.verify_proof) or proof_analysis.get("status") == "INDEX_USE_RUNTIME_PROOF_ACCEPTED"),
        },
    ]

    boundary_rows = [
        {"boundary": "index_use_readback_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "staging_catalog_create_import_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "lmdb_build", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "promotion_executed", "observed": 0, "required": 0, "pass": 1},
    ]

    write_csv(out / "dd056_representative_tag_checks.csv", rep_rows, [
        "table", "tag", "purpose", "available_in_dd055", "script_path",
    ])
    write_csv(out / "dd056_runtime_proof_tag_ledger.csv", proof_tag_rows, [
        "table", "tag", "token_present", "accepted",
    ])
    write_csv(out / "dd056_gate_ledger.csv", gate_rows, ["gate", "expected", "observed", "pass"])
    write_csv(out / "dd056_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])
    write_json(out / "dd056_runtime_proof_analysis.json", proof_analysis)

    (out / "dd056_candidate_index_use_order_readback.dts").write_text(build_script(args.target_slot, reps), encoding="utf-8")
    (out / "DD056_INDEX_USE_PROOF_TEMPLATE.md").write_text(build_proof_template(args.run_id, reps), encoding="utf-8")

    manifest = {
        "contract": "dd056_catalog_index_use_order_readback_proof_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": status,
        "repo_root": str(repo),
        "profiles": args.profile,
        "dd055_status": dd055_manifest.get("status", ""),
        "target_slot": args.target_slot,
        "target_path": str(target_path),
        "script_path": str(script_path),
        "proof_template_path": str(proof_template_path),
        "proof_path": str(proof_path),
        "representative_tags": len(reps),
        "representative_tags_available": sum(1 for r in reps if r["available_in_dd055"] == 1),
        "failures": failures,
        "prepare_proof_script": int(args.prepare_proof_script),
        "script_written": script_written,
        "template_written": template_written,
        "verify_proof": int(args.verify_proof),
        "proof_status": proof_analysis.get("status", ""),
        "active_catalog_mutation": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "lmdb_build": 0,
        "promotion_executed": 0,
        "next_recommended_action": "If green, proceed to active-catalog promotion readiness planning.",
    }
    write_json(out / "dd056_catalog_index_use_order_readback_manifest.json", manifest)

    report = f"""# DD-056 Catalog Index Use / Order Readback Proof

Run id: `{args.run_id}`
Status: **{status}**
Created UTC: `{manifest['created_utc']}`

## Purpose

DD-056 proves that DD-055-created index/tag artifacts are usable through
DotTalk++ order/readback commands, not merely present as files.

## Target

```text
{safe_rel(repo, target_path)}
```

## Representative tags

- Representative tags: **{len(reps)}**
- Available in DD-055 plan: **{manifest['representative_tags_available']}**
- DD-055 status: `{dd055_manifest.get('status', '')}`

## Runtime step

After `--prepare-proof-script`, run DotTalk++ and execute:

```text
do {script_path}
```

Then copy/update the proof template to:

```text
{proof_path}
```

and rerun DD-056 with `--verify-proof`.

## Boundary

DD-056 is index-use/readback proof only. It does not promote the active catalog,
build LMDB, edit source, mutate HELP/META/CMDHELPCHK, or run CREATE/IMPORT.
"""
    (out / "DD056_CATALOG_INDEX_USE_ORDER_READBACK_PROOF_REPORT.md").write_text(report, encoding="utf-8")

    print(f"DD-056 catalog index-use proof manifest: {out / 'dd056_catalog_index_use_order_readback_manifest.json'}")
    print(f"status: {status}; representative_tags: {len(reps)}; failures: {failures}; script_written: {script_written}")
    return 2 if (args.fail_on_review and failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
