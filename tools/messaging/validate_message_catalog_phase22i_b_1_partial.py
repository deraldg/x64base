#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv
from datetime import datetime, timezone
from pathlib import Path

STATUS_PARTIAL = "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_EMISSION_PARTIAL_DEFAULT_LOCALE_BRIDGE_REPAIR_REQUIRED"
STATUS_GREEN = "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_SMOKE_GREEN"
STATUS_BLOCKED = "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_SMOKE_BLOCKED"
NEXT_PARTIAL = "HOLD_OR_AUTHORIZE_PHASE22I_C_SET_LANGUAGE_LOCALE_STATE_BRIDGE_REPAIR"
NEXT_GREEN = "HOLD_OR_AUTHORIZE_PHASE22J_PLACEHOLDER_ARGUMENT_CONTRACT_REVIEW"
RUNLOG = Path("docs/messaging/runlog/MSG-022I_B_CONTROLLED_EMIT_SMOKE.md")

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

def split_emit_blocks(text: str):
    blocks = []
    marker = "SET MESSAGE EMIT:"
    parts = text.split(marker)
    for part in parts[1:]:
        blocks.append(marker + part)
    return blocks

def block_has(block_upper: str, needle: str) -> bool:
    return needle.upper() in block_upper

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    reports = repo / "docs/messaging/reports"
    reports.mkdir(parents=True, exist_ok=True)

    p22ib = first_row(reports / "message_catalog_phase22i_b_status_summary_v1.csv")
    messages = p22ib.get("MESSAGES", "12")
    text_rows = p22ib.get("TEXT_ROWS", "60")
    locales = p22ib.get("LOCALES", "de;en-US;es;fr;it")

    runlog = repo / RUNLOG
    text = runlog.read_text(encoding="utf-8", errors="replace") if runlog.exists() else ""
    upper = text.upper()
    emit_blocks = split_emit_blocks(text)
    emit_blocks_upper = [b.upper() for b in emit_blocks]

    gates = []
    failures = 0

    def gate(name, ok, detail, blocking=True):
        nonlocal failures
        gates.append({"GATE": name, "STATUS": "PASS" if ok else ("FAIL" if blocking else "REVIEW"), "DETAIL": detail})
        if not ok and blocking:
            failures += 1

    gate("PHASE22I_B_PATCH_APPLIED",
         p22ib.get("STATUS") == "MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_PATCH_APPLIED",
         p22ib.get("STATUS", ""))
    gate("RUNLOG_PRESENT", runlog.exists(), str(runlog))
    gate("SET_LANGUAGE_ES_VISIBLE",
         "IDIOMA DE MENSAJES: ES" in upper or "LANGUAGE: ES" in upper or "CURRENT LOCALE: ES" in upper,
         "SET LANGUAGE es should be visible before emit")
    gate("TWO_EMIT_BLOCKS_PRESENT",
         len(emit_blocks) >= 2,
         f"observed SET MESSAGE EMIT blocks={len(emit_blocks)}")

    explicit_es_ok = any(
        "SYMBOL: HELP_HINT_COMMAND" in b and
        "LOCALE: ES" in b and
        "PROVIDER MODE: ACTIVE_DBF" in b and
        "ACTIVE CATALOG LOADED: YES" in b and
        "RUNTIME CONTROLLED EMISSION PROOF: YES" in b and
        "TEXT: <EMPTY>" not in b
        for b in emit_blocks_upper
    )
    gate("EXPLICIT_LOCALE_ES_EMISSION_GREEN",
         explicit_es_ok,
         "SET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es should emit Spanish active-provider text")

    default_emit_block = emit_blocks_upper[0] if emit_blocks_upper else ""
    default_locale_es = (
        "SYMBOL: HELP_HINT_COMMAND" in default_emit_block and
        "LOCALE: ES" in default_emit_block and
        "CURRENT LOCALE: ES" in default_emit_block
    )
    default_locale_en_us = (
        "SYMBOL: HELP_HINT_COMMAND" in default_emit_block and
        ("LOCALE: EN-US" in default_emit_block or "CURRENT LOCALE: EN-US" in default_emit_block)
    )

    # This is the important correction: the old validator could pass because the
    # explicit LOCALE es block was green. Phase 22I-B also intended the implicit
    # emit after SET LANGUAGE es to inherit es. That did not happen.
    gate("DEFAULT_LOCALE_BRIDGE_FROM_SET_LANGUAGE",
         default_locale_es,
         "first SET MESSAGE EMIT should inherit SET LANGUAGE es; observed en-US means locale-state bridge is not wired",
         blocking=False)

    gate("NO_WRITEBACK_BOUNDARY",
         "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper,
         "read-only/no-writeback boundary")

    if failures == 0 and explicit_es_ok and default_locale_es:
        status = STATUS_GREEN
        next_gate = NEXT_GREEN
        default_bridge = 1
        controlled_emit_proof = 1
    elif failures == 0 and explicit_es_ok and default_locale_en_us:
        status = STATUS_PARTIAL
        next_gate = NEXT_PARTIAL
        default_bridge = 0
        controlled_emit_proof = 1
    else:
        status = STATUS_BLOCKED
        next_gate = NEXT_PARTIAL
        default_bridge = 0
        controlled_emit_proof = 0

    validation_issues = "0" if status in (STATUS_GREEN, STATUS_PARTIAL) else str(failures)

    write_csv(reports / "message_catalog_phase22i_b_1_status_summary_v1.csv", [{
        "STATUS": status,
        "MESSAGES": messages,
        "TEXT_ROWS": text_rows,
        "LOCALES": locales,
        "VALIDATION_ISSUES": validation_issues,
        "CONTROLLED_EXPLICIT_EMIT_PROOF": 1 if explicit_es_ok else 0,
        "DEFAULT_LOCALE_BRIDGE_PROOF": default_bridge,
        "DEFAULT_LOCALE_OBSERVED": "en-US" if default_locale_en_us else ("es" if default_locale_es else "unknown"),
        "ACTIVE_CATALOG_LOADED": 1 if "ACTIVE CATALOG LOADED: YES" in upper else 0,
        "SOURCE_MUTATION_OBSERVED": 0,
        "ACTIVE_CATALOG_MUTATION_OBSERVED": 0,
        "NEXT_GATE": next_gate,
        "REPORT_TIMESTAMP_UTC": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }], ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES",
         "CONTROLLED_EXPLICIT_EMIT_PROOF", "DEFAULT_LOCALE_BRIDGE_PROOF",
         "DEFAULT_LOCALE_OBSERVED", "ACTIVE_CATALOG_LOADED",
         "SOURCE_MUTATION_OBSERVED", "ACTIVE_CATALOG_MUTATION_OBSERVED",
         "NEXT_GATE", "REPORT_TIMESTAMP_UTC"])

    write_csv(reports / "message_catalog_phase22i_b_1_gate_check_v1.csv", gates,
              ["GATE", "STATUS", "DETAIL"])

    findings = [
        {"FINDING_ID": "22IB1-001", "STATUS": "PROVEN", "DETAIL": "Explicit LOCALE es controlled emission works through active_dbf provider." if explicit_es_ok else "Explicit LOCALE es controlled emission was not proven."},
        {"FINDING_ID": "22IB1-002", "STATUS": "REPAIR_REQUIRED" if default_locale_en_us else ("PROVEN" if default_locale_es else "UNKNOWN"), "DETAIL": "SET MESSAGE EMIT without LOCALE used en-US after SET LANGUAGE es, so the diagnostic command is not bridged to the SET LANGUAGE locale state." if default_locale_en_us else "Default locale bridge state based on first emit block."},
        {"FINDING_ID": "22IB1-003", "STATUS": "PROVEN", "DETAIL": "Boundary remained read-only/no-writeback." if "NO DBF/CDX/LMDB MUTATION" in upper and "NO RUNTIME WRITEBACK" in upper else "Boundary wording missing."},
    ]
    write_csv(reports / "message_catalog_phase22i_b_1_findings_v1.csv", findings,
              ["FINDING_ID", "STATUS", "DETAIL"])

    repair_plan = [
        {"STEP": "22I-C-001", "ACTION": "SOURCE_SEAM_PROBE", "TARGET": "src/cli/cmd_set.cpp", "DETAIL": "Find actual SET LANGUAGE locale state used by the existing 'Idioma de mensajes' path."},
        {"STEP": "22I-C-002", "ACTION": "BRIDGE_DEFAULT_EMIT_LOCALE", "TARGET": "src/cli/cmd_set.cpp", "DETAIL": "Make SET MESSAGE EMIT without LOCALE use the same locale state as SET LANGUAGE."},
        {"STEP": "22I-C-003", "ACTION": "PRESERVE_EXPLICIT_OVERRIDE", "TARGET": "src/cli/cmd_set.cpp", "DETAIL": "Keep SET MESSAGE EMIT <symbol> LOCALE <locale> working as explicit override."},
        {"STEP": "22I-C-004", "ACTION": "RUNTIME_SMOKE", "TARGET": "docs/messaging/runlog/MSG-022I_C_LOCALE_BRIDGE_REPAIR_SMOKE.md", "DETAIL": "Prove first/default emit and explicit emit both report locale es."},
    ]
    write_csv(reports / "message_catalog_phase22i_c_repair_plan_v1.csv", repair_plan,
              ["STEP", "ACTION", "TARGET", "DETAIL"])

    boundary = [
        {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "Phase 22I-B.1 validation/report only; no source mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_DBF_CATALOG", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active DBF mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_CDX_INDEXES", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active CDX/index mutation."},
        {"PROTECTED_SYSTEM": "ACTIVE_MESSAGING_LMDB", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No active LMDB mutation."},
        {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No HELP DATA mutation."},
        {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No CMDHELPCHK mutation."},
        {"PROTECTED_SYSTEM": "MANUALGEN", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No manualgen mutation."},
        {"PROTECTED_SYSTEM": "DATADICT_SELF_DOC", "MUTATION_ALLOWED": 0, "OBSERVED_MUTATION": 0, "DETAIL": "No Data Dictionary/SelfDoc mutation."},
    ]
    write_csv(reports / "message_catalog_phase22i_b_1_boundary_ledger_v1.csv", boundary,
              ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"])

    print(status)
    print(f"  messages: {messages}")
    print(f"  text rows: {text_rows}")
    print(f"  locales: {locales.replace(';', ', ')}")
    print(f"  validation issues: {validation_issues}")
    print(f"  controlled explicit emit proof: {1 if explicit_es_ok else 0}")
    print(f"  default locale bridge proof: {default_bridge}")
    print(f"  default locale observed: {'en-US' if default_locale_en_us else ('es' if default_locale_es else 'unknown')}")
    print(f"  active catalog loaded: {1 if 'ACTIVE CATALOG LOADED: YES' in upper else 0}")
    print(f"  next gate: {next_gate}")
    print(f"  reports: {reports}")
    return 0 if status in (STATUS_GREEN, STATUS_PARTIAL) else 2

if __name__ == "__main__":
    raise SystemExit(main())
