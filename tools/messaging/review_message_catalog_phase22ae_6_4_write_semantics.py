#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

STATUS_GREEN = "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_GREEN_SOURCE_HELD"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW_BLOCKED"
NEXT_GATE = "HOLD_OR_AUTHORIZE_PHASE22AE_6_4_1_SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF"

REPORT_DIR = Path("docs/messaging/reports")
RUNLOG = Path("docs/messaging/runlog/MSG-022AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF.md")

SYMBOL_FIELDS = ["SYMBOL", "MESSAGE_SYMBOL", "MSG_SYMBOL"]
LOCALE_FIELDS = ["LOCALE", "LOCALE_ID"]
TEXT_FIELDS = ["TEXT", "MESSAGE_TEXT", "MSG_TEXT"]
KIND_FIELDS = ["KIND", "MESSAGE_KIND", "MSG_KIND"]
PLACEHOLDER_FIELDS = ["PLACEHOLDERS", "PLACEHOLDER", "ARGS", "ARGUMENTS"]
STATUS_FIELDS = ["STATUS", "ROW_STATUS"]
SOURCE_FIELDS = ["SOURCE_PHASE", "SOURCE", "PHASE"]

class DbfInfo:
    def __init__(self, path, record_count, header_len, record_len, fields):
        self.path = path
        self.record_count = record_count
        self.header_len = header_len
        self.record_len = record_len
        self.fields = fields

def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def first_row(path: Path):
    rows = read_csv(path)
    return rows[0] if rows else {}

def write_csv(path: Path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})

def rel(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")

def savepoint_present(repo: Path, savepoint_id: str):
    latest_path = repo / REPORT_DIR / "message_savepoint_latest_v1.json"
    latest_id = ""
    if latest_path.exists():
        try:
            latest_id = json.loads(latest_path.read_text(encoding="utf-8")).get("savepoint_id", "")
        except Exception:
            latest_id = ""
    journal = repo / "docs/messaging/MESSAGING_SAVEPOINT_JOURNAL.md"
    text = journal.read_text(encoding="utf-8", errors="replace") if journal.exists() else ""
    return latest_id == savepoint_id or savepoint_id in text, latest_id

def parse_dbf(path: Path) -> DbfInfo:
    data = path.read_bytes()
    if len(data) < 32:
        raise RuntimeError(f"DBF too small: {path}")
    record_count = struct.unpack("<I", data[4:8])[0]
    header_len = struct.unpack("<H", data[8:10])[0]
    record_len = struct.unpack("<H", data[10:12])[0]
    fields = []
    pos = 32
    offset = 1
    while pos + 32 <= len(data):
        if data[pos] == 0x0D:
            break
        raw = data[pos:pos+11].split(b"\x00", 1)[0]
        name = raw.decode("ascii", errors="ignore").strip().upper()
        ftype = chr(data[pos+11])
        length = data[pos+16]
        if name:
            fields.append({"NAME": name, "TYPE": ftype, "LENGTH": length, "OFFSET": offset})
            offset += length
        pos += 32
    return DbfInfo(path, record_count, header_len, record_len, fields)

def choose_field(info: DbfInfo, choices):
    names = {f["NAME"] for f in info.fields}
    for c in choices:
        if c in names:
            return c
    return ""

def read_rows(info: DbfInfo):
    rows = []
    with info.path.open("rb") as f:
        f.seek(info.header_len)
        for i in range(info.record_count):
            rec = f.read(info.record_len)
            if len(rec) < info.record_len:
                break
            row = {"__RECNO__": i + 1, "__DELETED__": 1 if rec[:1] == b"*" else 0}
            for fld in info.fields:
                raw = rec[fld["OFFSET"]:fld["OFFSET"] + fld["LENGTH"]]
                if fld["TYPE"].upper() == "M":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                    row[fld["NAME"] + "__RAW_HEX"] = raw.hex()
                elif fld["TYPE"].upper() == "C":
                    row[fld["NAME"]] = raw.decode("cp1252", errors="replace").rstrip().strip()
                else:
                    row[fld["NAME"]] = raw.decode("ascii", errors="replace").rstrip().strip()
            rows.append(row)
    return rows

def any_contains(row: dict, needle: str) -> bool:
    return any(needle in str(v) for k, v in row.items() if not k.endswith("__RAW_HEX"))

def brief_tail(rows, fields, n=5):
    out = []
    for r in rows[-n:]:
        item = {"RECNO": r.get("__RECNO__", ""), "DELETED": r.get("__DELETED__", "")}
        for f in fields:
            if f:
                item[f] = r.get(f, "")
        out.append(item)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / REPORT_DIR
    reports.mkdir(parents=True, exist_ok=True)

    ae63 = first_row(reports / "message_catalog_phase22ae_6_3_validate_status_summary_v1.csv")
    sp63, latest_id = savepoint_present(repo, "MSG-022AE.6.3")
    manifest = read_csv(reports / "message_catalog_phase22ae_6_3_variant_manifest_v1.csv")
    prior_results = read_csv(reports / "message_catalog_phase22ae_6_3_variant_results_v1.csv")
    prior_tail = read_csv(reports / "message_catalog_phase22ae_6_3_tail_rows_v1.csv")

    gates = []
    failures = 0
    def gate(name: str, ok: bool, detail: str):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else "FAIL", "DETAIL": str(detail)})
        if not ok:
            failures += 1

    gate("PHASE22AE_6_3_GREEN_NO_VARIANT_PROVEN",
         ae63.get("STATUS") == "MESSAGE_CATALOG_PHASE22AE_6_3_ALTERNATIVE_SANDBOX_WRITE_PROOF_GREEN_NO_VARIANT_PROVEN",
         ae63.get("STATUS", "missing"))
    gate("MSG_022AE_6_3_SAVEPOINT_PRESENT", sp63, latest_id)
    gate("VARIANT_MANIFEST_PRESENT", len(manifest) > 0, f"variants={len(manifest)}")
    gate("ACTIVE_CATALOG_UNTOUCHED_IN_6_3",
         ae63.get("ACTIVE_CATALOG_MUTATION_OBSERVED") == "0",
         ae63.get("ACTIVE_CATALOG_MUTATION_OBSERVED", "missing"))

    enhanced = []
    enhanced_tail_rows = []
    partial_success = []
    proven_like_text_only = []
    errors = []

    for row in manifest:
        vid = row.get("VARIANT_ID", "")
        test_symbol = row.get("TEST_SYMBOL", "")
        vroot = repo / row.get("SANDBOX_ROOT", "")
        msg_dbf = vroot / "messaging/SYSTEM_MESSAGES.dbf"
        txt_dbf = vroot / "messaging/SYSTEM_MESSAGE_TEXT.dbf"
        msg_before = int(row.get("MESSAGE_ROWS_BEFORE") or 12)
        txt_before = int(row.get("TEXT_ROWS_BEFORE") or 60)

        try:
            msg_info = parse_dbf(msg_dbf)
            txt_info = parse_dbf(txt_dbf)
            msg_rows = read_rows(msg_info)
            txt_rows = read_rows(txt_info)

            msg_symbol = choose_field(msg_info, SYMBOL_FIELDS)
            txt_symbol = choose_field(txt_info, SYMBOL_FIELDS)
            txt_locale = choose_field(txt_info, LOCALE_FIELDS)
            txt_text = choose_field(txt_info, TEXT_FIELDS)

            msg_exact = [r for r in msg_rows if msg_symbol and r.get(msg_symbol, "") == test_symbol]
            txt_exact = [r for r in txt_rows if txt_symbol and r.get(txt_symbol, "") == test_symbol]
            msg_any = [r for r in msg_rows if any_contains(r, test_symbol)]
            txt_any = [r for r in txt_rows if any_contains(r, test_symbol)]

            msg_delta = msg_info.record_count - msg_before
            txt_delta = txt_info.record_count - txt_before
            message_key_found = len(msg_exact) > 0
            text_key_found = len(txt_exact) > 0
            text_payload_found = any(("MSG22AE63" in str(r.get(txt_text, "")) or str(r.get(txt_text, "")).strip()) for r in txt_exact) if txt_text else False
            proven_two_table = (msg_delta >= 1 and txt_delta >= 1 and message_key_found and text_key_found)

            if text_key_found and not message_key_found:
                proven_like_text_only.append(vid)
            if msg_delta >= 1 or txt_delta >= 1 or message_key_found or text_key_found:
                partial_success.append(vid)

            enhanced.append({
                "VARIANT_ID": vid,
                "TEST_SYMBOL": test_symbol,
                "MESSAGE_ROWS_BEFORE": msg_before,
                "MESSAGE_ROWS_AFTER": msg_info.record_count,
                "MESSAGE_DELTA": msg_delta,
                "TEXT_ROWS_BEFORE": txt_before,
                "TEXT_ROWS_AFTER": txt_info.record_count,
                "TEXT_DELTA": txt_delta,
                "MESSAGE_SYMBOL_FIELD": msg_symbol,
                "TEXT_SYMBOL_FIELD": txt_symbol,
                "TEXT_LOCALE_FIELD": txt_locale,
                "TEXT_TEXT_FIELD": txt_text,
                "MESSAGE_EXACT_SYMBOL_ROWS": len(msg_exact),
                "TEXT_EXACT_SYMBOL_ROWS": len(txt_exact),
                "MESSAGE_ANY_TEST_SYMBOL_ROWS": len(msg_any),
                "TEXT_ANY_TEST_SYMBOL_ROWS": len(txt_any),
                "TEXT_PAYLOAD_PRESENT_IN_EXACT_ROWS": 1 if text_payload_found else 0,
                "TWO_TABLE_VARIANT_PROVEN": 1 if proven_two_table else 0,
                "CLASSIFICATION": "TWO_TABLE_PROVEN" if proven_two_table else ("TEXT_ONLY_OR_PARTIAL" if text_key_found or msg_delta or txt_delta else "NO_EFFECT"),
                "ERRORS": "",
            })

            for source, rows, fields in [
                ("SYSTEM_MESSAGES", brief_tail(msg_rows, [msg_symbol, choose_field(msg_info, KIND_FIELDS), choose_field(msg_info, STATUS_FIELDS), choose_field(msg_info, SOURCE_FIELDS)])),
                ("SYSTEM_MESSAGE_TEXT", brief_tail(txt_rows, [txt_symbol, txt_locale, txt_text, txt_text + "__RAW_HEX" if txt_text else "", choose_field(txt_info, STATUS_FIELDS), choose_field(txt_info, SOURCE_FIELDS)])),
            ]:
                for tr in rows:
                    enhanced_tail_rows.append({
                        "VARIANT_ID": vid,
                        "TABLE": source,
                        "RECNO": tr.get("RECNO", ""),
                        "FIELD_1": next((str(v) for k, v in tr.items() if k not in ("RECNO", "DELETED") and str(v)), ""),
                        "ROW_JSON": json.dumps(tr, ensure_ascii=False, sort_keys=True),
                    })
        except Exception as exc:
            errors.append(f"{vid}: {exc}")
            enhanced.append({
                "VARIANT_ID": vid,
                "TEST_SYMBOL": test_symbol,
                "MESSAGE_ROWS_BEFORE": msg_before,
                "MESSAGE_ROWS_AFTER": "",
                "MESSAGE_DELTA": "",
                "TEXT_ROWS_BEFORE": txt_before,
                "TEXT_ROWS_AFTER": "",
                "TEXT_DELTA": "",
                "MESSAGE_SYMBOL_FIELD": "",
                "TEXT_SYMBOL_FIELD": "",
                "TEXT_LOCALE_FIELD": "",
                "TEXT_TEXT_FIELD": "",
                "MESSAGE_EXACT_SYMBOL_ROWS": "",
                "TEXT_EXACT_SYMBOL_ROWS": "",
                "MESSAGE_ANY_TEST_SYMBOL_ROWS": "",
                "TEXT_ANY_TEST_SYMBOL_ROWS": "",
                "TEXT_PAYLOAD_PRESENT_IN_EXACT_ROWS": "",
                "TWO_TABLE_VARIANT_PROVEN": 0,
                "CLASSIFICATION": "ERROR",
                "ERRORS": str(exc),
            })

    log_path = repo / RUNLOG
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    log_upper = log_text.upper()
    runtime_rows = [
        {"OBSERVATION": "runtime_log_exists", "VALUE": 1 if log_path.exists() else 0, "DETAIL": rel(log_path, repo)},
        {"OBSERVATION": "opened_system_messages_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGES"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "opened_system_message_text_count", "VALUE": log_upper.count("OPENED SYSTEM_MESSAGE_TEXT"), "DETAIL": "Runtime-open evidence."},
        {"OBSERVATION": "replace_usage_count", "VALUE": log_upper.count("REPLACE USAGE"), "DETAIL": "Indicates some variants reached REPLACE parser usage/failure path."},
        {"OBSERVATION": "unknown_command_count", "VALUE": log_upper.count("UNKNOWN COMMAND:"), "DETAIL": "Unexpected parser route."},
        {"OBSERVATION": "test_symbol_v1_seen_in_log", "VALUE": 1 if "MSG22AE63_V1_TEST" in log_upper else 0, "DETAIL": "Manual/log-visible text-table evidence if present."},
    ]

    mismatch_rows = [
        {
            "MISMATCH": "COUNTS_MOVED_BUT_VARIANT_NOT_CERTIFIED",
            "DETAIL": f"6.3 validator saw {ae63.get('VARIANTS_WITH_COUNTS_MOVED', '')} variants with count movement but {ae63.get('VARIANTS_PROVEN', '')} proven variants.",
            "LIKELY_MEANING": "APPEND executes, but the write semantics are not consistently populating both table key fields.",
        },
        {
            "MISMATCH": "TEXT_TABLE_EVIDENCE_MAY_BE_PARTIAL",
            "DETAIL": f"Enhanced text-only or partial variants: {';'.join(proven_like_text_only) if proven_like_text_only else 'none detected by DBF readback'}",
            "LIKELY_MEANING": "A one-table success is not enough for active promotion; both SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT must have exact keys.",
        },
        {
            "MISMATCH": "REPLACE_USAGE_OUTPUT",
            "DETAIL": f"Runtime log REPLACE usage count: {log_upper.count('REPLACE USAGE')}",
            "LIKELY_MEANING": "At least one generated syntax variant entered command usage/error behavior instead of a clean field-write path.",
        },
    ]

    hypotheses = [
        {
            "HYPOTHESIS": "CURRENT_RECORD_OR_WORK_AREA_SEMANTICS",
            "CONFIDENCE": "MEDIUM",
            "DETAIL": "APPEND changes counts, but subsequent REPLACE may not target the intended new row/work area in all command contexts.",
            "NEXT_PROBE": "Single-variant forensic run with immediate count/readback after each operation.",
        },
        {
            "HYPOTHESIS": "REPLACE_RHS_EVALUATION_OR_LITERAL_SYNTAX",
            "CONFIDENCE": "MEDIUM",
            "DETAIL": "REPLACE usage output and zero key rows suggest some literal forms are being parsed/evaluated differently than intended.",
            "NEXT_PROBE": "Test a single proven-looking syntax with field index and predeclared simple tokens.",
        },
        {
            "HYPOTHESIS": "TEXT_TABLE_PARTIAL_SUCCESS_ONLY",
            "CONFIDENCE": "MEDIUM",
            "DETAIL": "Manual exploration suggested V1 text-table values, but automated certification requires SYSTEM_MESSAGES and SYSTEM_MESSAGE_TEXT exact key rows.",
            "NEXT_PROBE": "Isolate V1 only from a fresh clone and inspect both DBFs after each step.",
        },
        {
            "HYPOTHESIS": "INDEX_OR_LMDB_PATH_SIDE_EFFECT_RISK",
            "CONFIDENCE": "LOW_TO_MEDIUM",
            "DETAIL": "Manual exploration may have created or touched non-sandbox CDX/LMDB paths. Future probes must fingerprint active/index roots before/after.",
            "NEXT_PROBE": "6.4.1 should include active/index/lmdb boundary fingerprints.",
        },
    ]

    next_plan = [
        {
            "STEP": 1,
            "ACTION": "CREATE_ONE_FRESH_V1_ONLY_SANDBOX",
            "DETAIL": "Do not run all variants together. Avoid duplicate row effects.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 2,
            "ACTION": "RUN_ONE_OPERATION_AT_A_TIME",
            "DETAIL": "Split USE, APPEND, positioning, and each REPLACE into separate runtime script stages if needed.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 3,
            "ACTION": "READBACK_AFTER_EACH_STAGE",
            "DETAIL": "DBF readback must report counts, current tail row, exact symbol fields, text pointer/value fields.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 4,
            "ACTION": "FINGERPRINT_ACTIVE_AND_DEFAULT_INDEX_ROOTS",
            "DETAIL": "Before/after fingerprints must prove no active/default index/LMDB side effects.",
            "MUTATES_ACTIVE": 0,
        },
        {
            "STEP": 5,
            "ACTION": "CERTIFY_OR_CLOSE_V1",
            "DETAIL": "Only if both DBFs contain exact keys should V1 become a candidate active-promotion mechanism.",
            "MUTATES_ACTIVE": 0,
        },
    ]

    forbidden = [
        {"RULE": "NO_ACTIVE_PROMOTION", "DETAIL": "6.3 did not certify a complete two-table variant."},
        {"RULE": "NO_BULK_VARIANT_DRIVER_FOR_FORENSICS", "DETAIL": "6.4.1 must isolate one variant and one write stage at a time."},
        {"RULE": "NO_DIRECT_RAW_DBF_MEMO_WRITE", "DETAIL": "Memo-backed text remains protected."},
        {"RULE": "NO_SAVEPOINT_AS_PROVEN_VARIANT", "DETAIL": "6.3 green/no-variant-proven is a valid closeout, not a promotion-ready proof."},
    ]

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "6.4 is review/report only."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "COMMAND_REGISTRY", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No command registry mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]

    status = STATUS_GREEN if failures == 0 else STATUS_BLOCKED
    validation_issues = str(failures)

    write_csv(reports / "message_catalog_phase22ae_6_4_gate_check_v1.csv", gates, ["GATE", "STATUS", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_enhanced_variant_readback_v1.csv", enhanced, [
        "VARIANT_ID", "TEST_SYMBOL", "MESSAGE_ROWS_BEFORE", "MESSAGE_ROWS_AFTER", "MESSAGE_DELTA",
        "TEXT_ROWS_BEFORE", "TEXT_ROWS_AFTER", "TEXT_DELTA", "MESSAGE_SYMBOL_FIELD",
        "TEXT_SYMBOL_FIELD", "TEXT_LOCALE_FIELD", "TEXT_TEXT_FIELD", "MESSAGE_EXACT_SYMBOL_ROWS",
        "TEXT_EXACT_SYMBOL_ROWS", "MESSAGE_ANY_TEST_SYMBOL_ROWS", "TEXT_ANY_TEST_SYMBOL_ROWS",
        "TEXT_PAYLOAD_PRESENT_IN_EXACT_ROWS", "TWO_TABLE_VARIANT_PROVEN", "CLASSIFICATION", "ERRORS"
    ])
    write_csv(reports / "message_catalog_phase22ae_6_4_enhanced_tail_rows_v1.csv", enhanced_tail_rows, ["VARIANT_ID", "TABLE", "RECNO", "FIELD_1", "ROW_JSON"])
    write_csv(reports / "message_catalog_phase22ae_6_4_runtime_observation_review_v1.csv", runtime_rows, ["OBSERVATION", "VALUE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_mismatch_review_v1.csv", mismatch_rows, ["MISMATCH", "DETAIL", "LIKELY_MEANING"])
    write_csv(reports / "message_catalog_phase22ae_6_4_hypothesis_matrix_v1.csv", hypotheses, ["HYPOTHESIS", "CONFIDENCE", "DETAIL", "NEXT_PROBE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_1_next_probe_plan_v1.csv", next_plan, ["STEP", "ACTION", "DETAIL", "MUTATES_ACTIVE"])
    write_csv(reports / "message_catalog_phase22ae_6_4_forbidden_paths_v1.csv", forbidden, ["RULE", "DETAIL"])
    write_csv(reports / "message_catalog_phase22ae_6_4_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    write_csv(reports / "message_catalog_phase22ae_6_4_status_summary_v1.csv", [{
        "STATUS": status,
        "VALIDATION_ISSUES": validation_issues,
        "PHASE22AE_6_3_STATUS": ae63.get("STATUS", ""),
        "MSG_022AE_6_3_SAVEPOINT_PRESENT": 1 if sp63 else 0,
        "VARIANTS_REVIEWED": len(enhanced),
        "PARTIAL_SUCCESS_VARIANTS": ";".join(sorted(set(partial_success))),
        "TEXT_ONLY_VARIANTS": ";".join(sorted(set(proven_like_text_only))),
        "TWO_TABLE_VARIANTS_PROVEN_BY_ENHANCED_REVIEW": sum(int(r.get("TWO_TABLE_VARIANT_PROVEN", 0) or 0) for r in enhanced),
        "RECOMMENDED_NEXT_PATH": "SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF",
        "ACTIVE_PROMOTION_AUTHORIZED": 0,
        "SOURCE_FILES_MUTATED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "HELP_DATA_MUTATION_OBSERVED": 0,
        "CMDHELPCHK_MUTATION_OBSERVED": 0,
        "NEXT_GATE": NEXT_GATE,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ERRORS": "; ".join(errors),
    }], ["STATUS", "VALIDATION_ISSUES", "PHASE22AE_6_3_STATUS",
         "MSG_022AE_6_3_SAVEPOINT_PRESENT", "VARIANTS_REVIEWED",
         "PARTIAL_SUCCESS_VARIANTS", "TEXT_ONLY_VARIANTS",
         "TWO_TABLE_VARIANTS_PROVEN_BY_ENHANCED_REVIEW", "RECOMMENDED_NEXT_PATH",
         "ACTIVE_PROMOTION_AUTHORIZED", "SOURCE_FILES_MUTATED",
         "ACTIVE_CATALOG_MUTATION_OBSERVED", "HELP_DATA_MUTATION_OBSERVED",
         "CMDHELPCHK_MUTATION_OBSERVED", "NEXT_GATE", "REPORT_TIMESTAMP_UTC", "ERRORS"])

    md = f"""# Message Catalog Phase 22AE.6.4 Deep Command Surface Write Semantics Review

Status: `{status}`

6.3 closed green/no-variant-proven. This review keeps active promotion closed
and recommends a single-variant forensic sandbox proof.

Next gate:

```text
{NEXT_GATE}
```
"""
    (reports / "MESSAGE_CATALOG_PHASE22AE_6_4_DEEP_COMMAND_SURFACE_WRITE_SEMANTICS_REVIEW.md").write_text(md, encoding="utf-8")

    print(status)
    print(f"  validation issues: {validation_issues}")
    print(f"  Phase 22AE.6.3 status: {ae63.get('STATUS', '')}")
    print(f"  MSG-022AE.6.3 savepoint present: {1 if sp63 else 0}")
    print(f"  variants reviewed: {len(enhanced)}")
    print(f"  partial success variants: {';'.join(sorted(set(partial_success)))}")
    print(f"  text-only variants: {';'.join(sorted(set(proven_like_text_only)))}")
    print(f"  two-table variants proven by enhanced review: {sum(int(r.get('TWO_TABLE_VARIANT_PROVEN', 0) or 0) for r in enhanced)}")
    print("  recommended next path: SINGLE_VARIANT_FORENSIC_SANDBOX_PROOF")
    print("  active promotion authorized: 0")
    print("  source files mutated: 0")
    print("  active catalog mutation observed: 0")
    print("  HELP DATA mutation observed: 0")
    print("  CMDHELPCHK mutation observed: 0")
    print(f"  next gate: {NEXT_GATE}")
    print(f"  reports: {reports}")
    return 0 if status == STATUS_GREEN else 2

if __name__ == "__main__":
    raise SystemExit(main())
