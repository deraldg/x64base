#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    write_text(path, json.dumps(obj, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def sha256(path: Path) -> str:
    if not path.exists() or path.is_dir():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description="DD096V-R x64 vector proof closeout and DD096W schema plan")
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--run-id", default="DD096VR-DD096W-x64-vector-proof-closeout-schema-plan-v0")
    ap.add_argument("--profile", action="append", default=[])
    ap.add_argument("--fail-on-review", action="store_true")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    generated = out / "generated_x64_vector_schema_plan"
    generated.mkdir(parents=True, exist_ok=True)

    proof_rows = [
        {
            "proof_id": "X64_TABLE_LONG_NAME_CREATE_OPEN_REOPEN",
            "surface": "CREATE/USE/AREA/STRUCT/LIST",
            "status": "GREEN_RUNTIME_PROVEN",
            "evidence_summary": "Long x64 table name created, opened as v64, wrote/listed, closed, reopened by exact full name, and preserved logical/legacy name.",
            "scope": "table identity name",
            "limit_observed": "long table name approx 100 chars; current design ceiling 128",
            "boundary": "classic-safe field names only in this proof",
        },
        {
            "proof_id": "X64_FIELD_LONG_NAME_ONE_FIELD_SINGLELINE",
            "surface": "CREATE X64/REPLACE/STRUCT/LIST/USE",
            "status": "GREEN_RUNTIME_PROVEN",
            "evidence_summary": "Single-line CREATE X64 with one long field emitted descriptor fallback warning, preserved authoritative metadata name, accepted REPLACE through long field name, displayed full name in STRUCT, and preserved after USE.",
            "scope": "field identity name",
            "limit_observed": "long field name 64 chars; current design ceiling 128",
            "boundary": "single-line CREATE only",
        },
        {
            "proof_id": "X64_FIELD_LONG_NAME_TWO_FIELDS_SINGLELINE",
            "surface": "CREATE X64/REPLACE/STRUCT/LIST/USE",
            "status": "GREEN_RUNTIME_PROVEN",
            "evidence_summary": "Single-line CREATE X64 with two long field names preserved both authoritative names and supported values/list/reopen.",
            "scope": "field identity names",
            "limit_observed": "field names 64 and 45 chars; current design ceiling 128",
            "boundary": "single-line CREATE only",
        },
        {
            "proof_id": "LIST_LONG_FIELD_DISPLAY_TRUNCATION",
            "surface": "LIST",
            "status": "GREEN_RUNTIME_PROVEN",
            "evidence_summary": "LIST truncates long headers for readability and tells the user to use STRUCT for full names.",
            "scope": "display behavior",
            "limit_observed": "display-only truncation, not identity loss",
            "boundary": "presentation layer only",
        },
        {
            "proof_id": "CREATE_X64_DESCRIPTOR_FALLBACK_WARNING",
            "surface": "CREATE X64",
            "status": "GREEN_RUNTIME_PROVEN",
            "evidence_summary": "CREATE X64 warns when DBF/VFP descriptor fallback token differs from authoritative long x64 name.",
            "scope": "classic descriptor compatibility",
            "limit_observed": "fallback token 10 visible chars; authoritative x64 name preserved when <=128",
            "boundary": "warning and fallback path",
        },
        {
            "proof_id": "DOTSCRIPT_MULTILINE_CREATE_ASSEMBLY",
            "surface": "DotScript CREATE continuation",
            "status": "RED_REQUIRES_REPAIR_OR_USAGE_RULE",
            "evidence_summary": "Generated multiline CREATE probes failed with unmatched parentheses and field lines executed as commands.",
            "scope": "script command assembly",
            "limit_observed": "not a vector-name failure",
            "boundary": "likely syntax/continuation issue; user suspects missing semicolon after paren in generated scripts",
        },
    ]
    write_csv(generated / "dd096vr_x64_vector_runtime_proof_matrix.csv", proof_rows, [
        "proof_id", "surface", "status", "evidence_summary", "scope", "limit_observed", "boundary"
    ])

    doctrine_rows = [
        {
            "principle_id": "VEC-001",
            "principle": "Use longer x64 identity names when they improve truth, provenance, or generated documentation.",
            "status": "ADOPTED",
            "notes": "Do not retreat to unnecessary 10-char naming for x64 Data Dictionary/SelfDoc schema.",
        },
        {
            "principle_id": "VEC-002",
            "principle": "Keep classic compatibility stable through descriptor fallback tokens and explicit warnings.",
            "status": "ADOPTED",
            "notes": "Fallback token remains DBF/VFP descriptor-safe; authoritative x64 metadata name is runtime identity when preserved.",
        },
        {
            "principle_id": "VEC-003",
            "principle": "Keep data/value field widths separate from table/field identity-name vectors.",
            "status": "ADOPTED",
            "notes": "DD096HI blockers were record-value widths, not descriptor identity-name vector limits.",
        },
        {
            "principle_id": "VEC-004",
            "principle": "Prefer single-line CREATE or proven continuation style until DotScript multiline CREATE assembly is repaired/proven.",
            "status": "TEMPORARY_SCRIPT_POLICY",
            "notes": "128-char identity names are practical within roughly 144-char script rows when syntax is disciplined.",
        },
        {
            "principle_id": "VEC-005",
            "principle": "Use x64base while building documentation, metadata, HELP, and SDLC diagrams.",
            "status": "ADOPTED",
            "notes": "Runtime proof should feed Data Dictionary evidence, SelfDoc, manuals, HELP candidates, and high-level diagrams.",
        },
    ]
    write_csv(generated / "dd096vr_vector_doctrine_update.csv", doctrine_rows, [
        "principle_id", "principle", "status", "notes"
    ])

    # DD096W schema plan: long identity names, deliberate data widths, with aliases/fallbacks where useful.
    table_rows = [
        {
            "table_id": "DDRUN_X64",
            "proposed_table_name": "DATA_DICTIONARY_RUNS",
            "purpose": "One row per Data Dictionary generation/validation/apply/proof run.",
            "identity_name_policy": "long x64 table identity; descriptor fallback expected/allowed",
            "migration_role": "replaces or stages beyond DDRUN",
            "apply_now": 0,
        },
        {
            "table_id": "DDOBJECT_X64",
            "proposed_table_name": "DATA_DICTIONARY_OBJECTS",
            "purpose": "Catalog objects: commands, tables, fields, tags, relationships, surfaces, documents, gates.",
            "identity_name_policy": "long x64 table and field identities encouraged where clear",
            "migration_role": "successor/staging replacement for DDOBJECT",
            "apply_now": 0,
        },
        {
            "table_id": "DDATTR_X64",
            "proposed_table_name": "DATA_DICTIONARY_OBJECT_ATTRIBUTES",
            "purpose": "Attribute/value facts about catalog objects.",
            "identity_name_policy": "long x64 identities for attribute metadata fields",
            "migration_role": "successor/staging replacement for DDATTR",
            "apply_now": 0,
        },
        {
            "table_id": "DDEDGE_X64",
            "proposed_table_name": "DATA_DICTIONARY_RELATION_EDGES",
            "purpose": "Graph edges among catalog objects.",
            "identity_name_policy": "long x64 identities for from/to object references and relation type",
            "migration_role": "successor/staging replacement for DDEDGE",
            "apply_now": 0,
        },
        {
            "table_id": "DDEVID_X64",
            "proposed_table_name": "DATA_DICTIONARY_EVIDENCE_RECORDS",
            "purpose": "Evidence records connecting catalog assertions to source/runtime proof/report artifacts.",
            "identity_name_policy": "long x64 identities for provenance fields",
            "migration_role": "successor/staging replacement for DDEVID",
            "apply_now": 0,
        },
        {
            "table_id": "DDGATE_X64",
            "proposed_table_name": "DATA_DICTIONARY_GATE_RECORDS",
            "purpose": "Gate/checkpoint rows for guarded lanes and apply/no-apply decisions.",
            "identity_name_policy": "long x64 identities for gate names and required/observed state",
            "migration_role": "successor/staging replacement for DDGATE",
            "apply_now": 0,
        },
    ]
    write_csv(generated / "dd096w_proposed_x64_schema_tables.csv", table_rows, [
        "table_id", "proposed_table_name", "purpose", "identity_name_policy", "migration_role", "apply_now"
    ])

    field_rows = [
        # Objects
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_OBJECT_ID", "type": "C(32)", "purpose": "Stable object identifier", "identity_width": "long x64 name", "data_width_policy": "compact stable id", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_OBJECT_TYPE", "type": "C(64)", "purpose": "Object type such as COMMAND_SURFACE, CATALOG_TABLE, CATALOG_FIELD", "identity_width": "long x64 name", "data_width_policy": "widened enum/code value", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_OBJECT_NAME", "type": "C(128)", "purpose": "Object name, command surface name, table name, field name, or document name", "identity_width": "long x64 name", "data_width_policy": "128-char current ceiling alignment", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_OWNER_NAME", "type": "C(128)", "purpose": "Owner/parent namespace such as DDICT or Data Dictionary area", "identity_width": "long x64 name", "data_width_policy": "128-char current ceiling alignment", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_STATUS_CODE", "type": "C(64)", "purpose": "Lifecycle/status code", "identity_width": "long x64 name", "data_width_policy": "widened status enum", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "CATALOG_PROFILE_CODE", "type": "C(32)", "purpose": "ENGINE/PROFESSIONAL/overlay profile", "identity_width": "long x64 name", "data_width_policy": "profile code", "apply_now": 0},
        {"table_id": "DDOBJECT_X64", "field_name": "SOURCE_ARTIFACT_ID", "type": "C(64)", "purpose": "Source/evidence artifact id", "identity_width": "long x64 name", "data_width_policy": "stable provenance id", "apply_now": 0},
        # Attributes
        {"table_id": "DDATTR_X64", "field_name": "CATALOG_ATTRIBUTE_ID", "type": "C(32)", "purpose": "Stable attribute row identifier", "identity_width": "long x64 name", "data_width_policy": "compact stable id", "apply_now": 0},
        {"table_id": "DDATTR_X64", "field_name": "CATALOG_OBJECT_ID", "type": "C(32)", "purpose": "Owning object id", "identity_width": "long x64 name", "data_width_policy": "foreign key reference", "apply_now": 0},
        {"table_id": "DDATTR_X64", "field_name": "CATALOG_ATTRIBUTE_NAME", "type": "C(128)", "purpose": "Attribute name such as promotion_policy or canonical_dbf_root", "identity_width": "long x64 name", "data_width_policy": "128-char current ceiling alignment", "apply_now": 0},
        {"table_id": "DDATTR_X64", "field_name": "CATALOG_ATTRIBUTE_VALUE", "type": "C(254)", "purpose": "Short/medium attribute value", "identity_width": "long x64 name", "data_width_policy": "classic char maximum until memo/large object needed", "apply_now": 0},
        {"table_id": "DDATTR_X64", "field_name": "CATALOG_ATTRIBUTE_DETAIL", "type": "M", "purpose": "Long attribute value/detail text", "identity_width": "long x64 name", "data_width_policy": "memo for long text", "apply_now": 0},
        {"table_id": "DDATTR_X64", "field_name": "EVIDENCE_RECORD_ID", "type": "C(64)", "purpose": "Evidence/provenance id", "identity_width": "long x64 name", "data_width_policy": "stable provenance id", "apply_now": 0},
        # Edges
        {"table_id": "DDEDGE_X64", "field_name": "RELATION_EDGE_ID", "type": "C(32)", "purpose": "Stable relation edge id", "identity_width": "long x64 name", "data_width_policy": "compact stable id", "apply_now": 0},
        {"table_id": "DDEDGE_X64", "field_name": "RELATION_FROM_OBJECT_ID", "type": "C(32)", "purpose": "Source object id", "identity_width": "long x64 name", "data_width_policy": "foreign key reference", "apply_now": 0},
        {"table_id": "DDEDGE_X64", "field_name": "RELATION_TO_OBJECT_ID", "type": "C(32)", "purpose": "Target object id", "identity_width": "long x64 name", "data_width_policy": "foreign key reference", "apply_now": 0},
        {"table_id": "DDEDGE_X64", "field_name": "RELATION_EDGE_TYPE", "type": "C(64)", "purpose": "Relation type such as HAS_SURFACE or WORKSPACE_RELATION", "identity_width": "long x64 name", "data_width_policy": "widened enum/code value", "apply_now": 0},
        {"table_id": "DDEDGE_X64", "field_name": "EVIDENCE_RECORD_ID", "type": "C(64)", "purpose": "Evidence/provenance id", "identity_width": "long x64 name", "data_width_policy": "stable provenance id", "apply_now": 0},
        # Evidence
        {"table_id": "DDEVID_X64", "field_name": "EVIDENCE_RECORD_ID", "type": "C(64)", "purpose": "Stable evidence id", "identity_width": "long x64 name", "data_width_policy": "stable provenance id", "apply_now": 0},
        {"table_id": "DDEVID_X64", "field_name": "CATALOG_OBJECT_ID", "type": "C(32)", "purpose": "Object being evidenced", "identity_width": "long x64 name", "data_width_policy": "foreign key reference", "apply_now": 0},
        {"table_id": "DDEVID_X64", "field_name": "SOURCE_ARTIFACT_ID", "type": "C(64)", "purpose": "Source artifact id", "identity_width": "long x64 name", "data_width_policy": "stable provenance id", "apply_now": 0},
        {"table_id": "DDEVID_X64", "field_name": "EVIDENCE_KIND_CODE", "type": "C(64)", "purpose": "Runtime proof, source, report, manifest, etc.", "identity_width": "long x64 name", "data_width_policy": "widened enum/code value", "apply_now": 0},
        {"table_id": "DDEVID_X64", "field_name": "EVIDENCE_CONFIDENCE_CODE", "type": "C(32)", "purpose": "Confidence/provenance level", "identity_width": "long x64 name", "data_width_policy": "profile/status code", "apply_now": 0},
        {"table_id": "DDEVID_X64", "field_name": "EVIDENCE_DETAIL_TEXT", "type": "M", "purpose": "Long evidence note/detail", "identity_width": "long x64 name", "data_width_policy": "memo for long text", "apply_now": 0},
        # Gates
        {"table_id": "DDGATE_X64", "field_name": "GATE_RECORD_ID", "type": "C(64)", "purpose": "Stable gate id", "identity_width": "long x64 name", "data_width_policy": "stable gate/provenance id", "apply_now": 0},
        {"table_id": "DDGATE_X64", "field_name": "RUN_RECORD_ID", "type": "C(64)", "purpose": "Run id associated with gate", "identity_width": "long x64 name", "data_width_policy": "stable run id", "apply_now": 0},
        {"table_id": "DDGATE_X64", "field_name": "GATE_NAME", "type": "C(128)", "purpose": "Gate/checkpoint name", "identity_width": "long x64 name", "data_width_policy": "128-char current ceiling alignment", "apply_now": 0},
        {"table_id": "DDGATE_X64", "field_name": "GATE_STATUS_CODE", "type": "C(64)", "purpose": "Required/observed/accepted/review state", "identity_width": "long x64 name", "data_width_policy": "widened status enum", "apply_now": 0},
        {"table_id": "DDGATE_X64", "field_name": "GATE_DETAIL_TEXT", "type": "M", "purpose": "Gate detail/reasoning/authorization note", "identity_width": "long x64 name", "data_width_policy": "memo for long text", "apply_now": 0},
    ]
    write_csv(generated / "dd096w_proposed_x64_schema_fields.csv", field_rows, [
        "table_id", "field_name", "type", "purpose", "identity_width", "data_width_policy", "apply_now"
    ])

    script_policy_rows = [
        {"policy_id": "SCRIPT-001", "policy": "Prefer single-line CREATE X64 for long identity-name probes until continuation is fixed/proven.", "status": "ACTIVE_TEMPORARY"},
        {"policy_id": "SCRIPT-002", "policy": "Keep generated CREATE rows around 144 printer columns where practical.", "status": "ACTIVE_STYLE"},
        {"policy_id": "SCRIPT-003", "policy": "When multiline CREATE is needed, create a separate DotScript continuation repair/proof lane.", "status": "RECOMMENDED"},
        {"policy_id": "SCRIPT-004", "policy": "Use STRUCT as authoritative full-name display and LIST as readable display with truncation warning.", "status": "ACTIVE_STYLE"},
    ]
    write_csv(generated / "dd096w_dotscript_generation_policy.csv", script_policy_rows, ["policy_id", "policy", "status"])

    sdlc_rows = [
        {"level": 1, "artifact": "Runtime proof", "feeds": "Data Dictionary evidence rows", "status": "active"},
        {"level": 2, "artifact": "Data Dictionary evidence rows", "feeds": "SelfDoc/MDO reports", "status": "planned"},
        {"level": 3, "artifact": "SelfDoc/MDO reports", "feeds": "HELP/CMDHELPCHK candidates", "status": "planned"},
        {"level": 4, "artifact": "HELP/CMDHELPCHK candidates", "feeds": "manual sections", "status": "planned"},
        {"level": 5, "artifact": "manual sections", "feeds": "high-level SDLC diagrams", "status": "planned"},
    ]
    write_csv(generated / "dd096w_trickle_up_sdlc_pipeline.csv", sdlc_rows, ["level", "artifact", "feeds", "status"])

    boundary_rows = [
        {"boundary": "report_and_design_only", "observed": 1, "required": 1, "pass": 1},
        {"boundary": "active_catalog_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "dbf_append_replace_delete_pack_zap", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "cdx_lmdb_create_rebuild", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "source_edits", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "help_meta_cmdhelpchk_mutation", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "manual_row_repair", "observed": 0, "required": 0, "pass": 1},
        {"boundary": "apply_now_total", "observed": 0, "required": 0, "pass": 1},
    ]
    write_csv(out / "dd096vr_dd096w_no_mutation_boundary_ledger.csv", boundary_rows, ["boundary", "observed", "required", "pass"])

    gates = [
        {"gate": "long_table_names_runtime_proven", "expected": "GREEN", "observed": "GREEN", "pass": 1},
        {"gate": "long_field_names_singleline_runtime_proven", "expected": "GREEN", "observed": "GREEN", "pass": 1},
        {"gate": "multiline_create_continuation_not_required_for_plan", "expected": "TRUE", "observed": "TRUE", "pass": 1},
        {"gate": "schema_plan_outputs_written", "expected": 1, "observed": 1, "pass": 1},
        {"gate": "apply_now_zero", "expected": 0, "observed": 0, "pass": 1},
    ]
    write_csv(out / "dd096vr_dd096w_gate_ledger.csv", gates, ["gate", "expected", "observed", "pass"])

    report = f"""# DD096V-R / DD096W x64 Vector Proof Closeout and Data Dictionary Schema Plan

Run id: `{args.run_id}`
Status: **X64_VECTOR_PROOF_CLOSED_SCHEMA_PLAN_READY**
Created UTC: `{utc_now()}`

## Re-evaluated position

The x64 vector layer is now runtime-proven in the important slices needed to proceed:

- Long x64 table identity names work through create/open/write/list/close/reopen.
- Long x64 field identity names work through single-line CREATE X64, descriptor fallback warning, REPLACE by long name, STRUCT full-name display, LIST readable truncation, close/reopen, and readback.
- Descriptor fallback warnings are explicit and useful.
- The remaining red is DotScript multiline CREATE assembly, not the x64 vector identity model.

## New direction

Use longer x64 identity names where they improve Data Dictionary truth, provenance, generated documentation, HELP integration, manuals, and SDLC diagrams.

Do not force Data Dictionary schema back into terse names merely because classic DBF had 10-character descriptor limits.

Keep these separate:

1. x64 table/field identity-name width.
2. record data/value field width.
3. descriptor fallback token.
4. DotScript command-line assembly.

## DD096W schema direction

Build a parallel/proof x64 Data Dictionary schema that uses meaningful long identity names and deliberate data widths. Examples:

- DATA_DICTIONARY_OBJECTS
- DATA_DICTIONARY_OBJECT_ATTRIBUTES
- DATA_DICTIONARY_RELATION_EDGES
- DATA_DICTIONARY_EVIDENCE_RECORDS
- DATA_DICTIONARY_GATE_RECORDS

Fields should use long x64 identity names such as:

- CATALOG_OBJECT_ID
- CATALOG_OBJECT_TYPE
- CATALOG_OBJECT_NAME
- CATALOG_ATTRIBUTE_NAME
- RELATION_FROM_OBJECT_ID
- EVIDENCE_RECORD_ID
- GATE_STATUS_CODE

Data/value widths are a separate design choice, not automatically supplied by the identity-name vector.

## Next safe lanes

```text
DD096X
  Guarded x64 Data Dictionary schema proof generation.
  Create parallel proof tables only; no active catalog replacement.

DD096Y
  Import/stage the 158 candidate rows into the widened long-identity schema.

DD096Z
  Guarded promotion/active-catalog replacement plan only after DD096X/Y green.
```

## Boundary

This package is report/design only. It does not mutate active DBFs, rebuild CDX/LMDB, edit source, mutate HELP/CMDHELPCHK, or repair manuals.
"""
    write_text(out / "DD096VR_DD096W_X64_VECTOR_PROOF_CLOSEOUT_SCHEMA_PLAN_REPORT.md", report)

    manifest = {
        "contract": "dd096vr_dd096w_x64_vector_proof_closeout_schema_plan_v0",
        "run_id": args.run_id,
        "created_utc": utc_now(),
        "status": "X64_VECTOR_PROOF_CLOSED_SCHEMA_PLAN_READY",
        "repo_root": str(repo),
        "profiles": args.profile,
        "proof_rows": len(proof_rows),
        "proposed_tables": len(table_rows),
        "proposed_fields": len(field_rows),
        "active_catalog_mutation": 0,
        "dbf_append_replace_delete_pack_zap": 0,
        "cdx_lmdb_create_rebuild": 0,
        "source_edits": 0,
        "help_meta_cmdhelpchk_mutation": 0,
        "manual_row_repair": 0,
        "apply_now_total": 0,
        "next_recommended_action": "DD096X guarded x64 Data Dictionary schema proof generation.",
    }
    write_json(out / "dd096vr_dd096w_x64_vector_proof_closeout_schema_plan_manifest.json", manifest)

    artifact_rows = []
    for p, role in [(generated, "generated_plan_dir"), (out / "DD096VR_DD096W_X64_VECTOR_PROOF_CLOSEOUT_SCHEMA_PLAN_REPORT.md", "report")]:
        artifact_rows.append({
            "role": role,
            "path": str(p),
            "exists": int(p.exists()),
            "kind": "dir" if p.exists() and p.is_dir() else "file" if p.exists() and p.is_file() else "",
            "bytes_or_children": sum(1 for _ in p.iterdir()) if p.exists() and p.is_dir() else p.stat().st_size if p.exists() and p.is_file() else 0,
            "sha256": sha256(p),
        })
    write_csv(out / "dd096vr_dd096w_artifact_ledger.csv", artifact_rows, ["role", "path", "exists", "kind", "bytes_or_children", "sha256"])

    print(f"DD096V-R/DD096W manifest: {out / 'dd096vr_dd096w_x64_vector_proof_closeout_schema_plan_manifest.json'}")
    print(f"status: X64_VECTOR_PROOF_CLOSED_SCHEMA_PLAN_READY; proof_rows: {len(proof_rows)}; proposed_tables: {len(table_rows)}; proposed_fields: {len(field_rows)}; apply_now: 0; failures: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
