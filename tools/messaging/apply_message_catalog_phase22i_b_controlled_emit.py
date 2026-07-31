#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path

GREEN="MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_PATCH_APPLIED"
BLOCKED="MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_RUNTIME_EMISSION_PATCH_BLOCKED"
NEXT="BUILD_AND_RUN_PHASE22I_B_CONTROLLED_EMIT_SMOKE_THEN_VALIDATE"

HELPER_BEGIN="// MSG-022I-B BEGIN controlled message emit helper"
HELPER_END="// MSG-022I-B END controlled message emit helper"
MSG_BEGIN="    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK"
MSG_END="    // MSG-022E END SET MESSAGE CATALOG CHECK"

HELPER=r'''
// MSG-022I-B BEGIN controlled message emit helper
static void print_message_emit_usage() {
    auto& out = cli::OutputRouter::instance().out();
    out << "Usage:\n";
    out << "  SET MESSAGE CATALOG CHECK\n";
    out << "  SET MESSAGE EMIT <symbol> [LOCALE <locale>]\n";
}

static void handle_set_message_emit(std::istringstream& args) {
    auto& out = cli::OutputRouter::instance().out();

    std::string symbol;
    args >> symbol;
    if (symbol.empty()) {
        print_message_emit_usage();
        return;
    }

    std::string locale = message_catalog_current_locale();
    std::string tok;
    while (args >> tok) {
        const std::string up = up_copy(tok);
        if (up == "LOCALE" || up == "LANGUAGE" || up == "TO") {
            std::string value;
            args >> value;
            if (!value.empty()) {
                locale = value;
            }
        }
    }

    const auto status = dottalk::helpdata::active_message_catalog_status();
    const std::string text = dottalk::helpdata::format_message_catalog(locale, symbol);

    out << "SET MESSAGE EMIT:\n";
    out << "  current locale: " << locale << "\n";
    out << "  provider mode: " << message_catalog_mode_name(status.mode) << "\n";
    out << "  active catalog present: " << (status.active_catalog_present ? "yes" : "no") << "\n";
    out << "  active catalog loaded: " << (status.active_catalog_loaded ? "yes" : "no") << "\n";
    out << "  message count: " << status.message_count << "\n";
    out << "  text row count: " << status.text_row_count << "\n";
    out << "  symbol: " << symbol << "\n";
    out << "  locale: " << locale << "\n";
    out << "  text: " << (text.empty() ? "<empty>" : text) << "\n";
    out << "  runtime controlled emission proof: "
        << ((status.active_catalog_loaded && !text.empty()) ? "yes" : "no") << "\n";
    out << "  boundary: explicit diagnostic emission; no DBF/CDX/LMDB mutation; no runtime writeback\n";
}
// MSG-022I-B END controlled message emit helper
'''

MSG_BRANCH=r'''
    // MSG-022E BEGIN SET MESSAGE CATALOG CHECK
    if (opt == "MESSAGE") {
        std::string sub1;
        args >> sub1;
        sub1 = up_copy(sub1);

        if (sub1 == "CATALOG") {
            std::string sub2;
            args >> sub2;
            sub2 = up_copy(sub2);

            if (sub2 == "CHECK" || sub2 == "STATUS") {
                print_message_catalog_provider_status();
                return;
            }

            print_message_emit_usage();
            return;
        }

        if (sub1 == "EMIT") {
            handle_set_message_emit(args);
            return;
        }

        print_message_emit_usage();
        return;
    }
    // MSG-022E END SET MESSAGE CATALOG CHECK
'''

def rows(path):
    if not path.exists(): return []
    with path.open("r", encoding="utf-8-sig", newline="") as f: return list(csv.DictReader(f))
def first(path): 
    r=rows(path); return r[0] if r else {}
def write_csv(path, data, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for row in data: w.writerow({k:row.get(k,"") for k in fields})
def sha(path):
    h=hashlib.sha256()
    if path.exists():
        with path.open("rb") as f:
            for b in iter(lambda:f.read(1048576), b""): h.update(b)
    return h.hexdigest()
def rel(path, root):
    try: return str(path.relative_to(root)).replace("\\","/")
    except ValueError: return str(path)
def replace_block(text, a, b, repl):
    i=text.find(a); j=text.find(b)
    if i < 0 or j < 0 or j < i: return None
    return text[:i] + repl.strip() + text[j+len(b):]
def insert_before(text, needles, block):
    for n in needles:
        p=text.find(n)
        if p >= 0: return text[:p] + block + text[p:]
    raise RuntimeError("required insertion anchor not found")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    ap.add_argument("--allow-source-mutation", action="store_true")
    args=ap.parse_args()
    repo=Path(args.repo_root).resolve()
    reports=repo/"docs/messaging/reports"; reports.mkdir(parents=True, exist_ok=True)
    p22ia=first(reports/"message_catalog_phase22i_a_status_summary_v1.csv")
    msg=p22ia.get("MESSAGES","12"); txt=p22ia.get("TEXT_ROWS","60"); loc=p22ia.get("LOCALES","de;en-US;es;fr;it")
    cmd=repo/"src/cli/cmd_set.cpp"
    gates=[]; fail=0
    def gate(name, ok, detail):
        nonlocal fail
        gates.append({"GATE":name,"STATUS":"PASS" if ok else "FAIL","DETAIL":detail})
        if not ok: fail += 1
    gate("OPERATOR_AUTHORIZED_SOURCE_MUTATION", args.allow_source_mutation, "requires --allow-source-mutation")
    gate("PHASE22I_A_PLAN_GREEN", p22ia.get("STATUS")=="MESSAGE_CATALOG_PHASE22I_A_CONTROLLED_RUNTIME_EMISSION_EXPANSION_PLAN_GREEN_SOURCE_HELD", p22ia.get("STATUS",""))
    gate("CMD_SET_CPP_PRESENT", cmd.exists(), rel(cmd, repo))
    muts=[]; backups=[]; actions=[]; errors=[]; status=BLOCKED
    if fail == 0:
        try:
            stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            bdir=repo/"docs/messaging/backups"/f"MSG-022I-B_CONTROLLED_EMIT_BACKUP_{stamp}"
            dst=bdir/rel(cmd,repo); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(cmd,dst)
            backups.append({"TARGET_PATH":rel(cmd,repo),"BACKUP_PATH":rel(dst,repo),"BYTES":dst.stat().st_size,"SHA256":sha(dst),"ROLE":"pre_patch_source_backup"})
            s=cmd.read_text(encoding="utf-8", errors="replace")
            for needle in ["message_catalog_current_locale()","message_catalog_mode_name(","print_message_catalog_provider_status()"]:
                if needle not in s: raise RuntimeError(f"required prior helper missing: {needle}")
            if "SET MESSAGE EMIT <symbol> [LOCALE <locale>]" not in s:
                anchor='        << "  SET MESSAGE CATALOG CHECK\\n"'
                if anchor in s:
                    s=s.replace(anchor, anchor+'\n        << "  SET MESSAGE EMIT <symbol> [LOCALE <locale>]\\n"', 1)
                    actions.append({"TARGET_PATH":rel(cmd,repo),"ACTION":"INSERT_USAGE_LINE","DETAIL":"SET MESSAGE EMIT"})
            rb=replace_block(s, HELPER_BEGIN, HELPER_END, HELPER)
            if rb is None:
                s=insert_before(s, ["static void print_set_usage() {"], HELPER+"\n")
                actions.append({"TARGET_PATH":rel(cmd,repo),"ACTION":"INSERT_EMIT_HELPER","DETAIL":"controlled emit helper"})
            else:
                s=rb; actions.append({"TARGET_PATH":rel(cmd,repo),"ACTION":"REPLACE_EMIT_HELPER","DETAIL":"controlled emit helper"})
            rb=replace_block(s, MSG_BEGIN, MSG_END, MSG_BRANCH)
            if rb is None: raise RuntimeError("SET MESSAGE branch markers not found")
            s=rb; actions.append({"TARGET_PATH":rel(cmd,repo),"ACTION":"REPLACE_SET_MESSAGE_BRANCH","DETAIL":"catalog check plus emit branch"})
            cmd.write_text(s, encoding="utf-8")
            muts.append({"TARGET_PATH":rel(cmd,repo),"ACTION":"UPDATE","BYTES":cmd.stat().st_size,"SHA256":sha(cmd),"DETAIL":"added explicit SET MESSAGE EMIT diagnostic branch"})
            status=GREEN
        except Exception as e:
            fail += 1; errors.append(str(e)); gates.append({"GATE":"PATCH_CMD_SET_CPP","STATUS":"FAIL","DETAIL":str(e)})
    val="0" if status==GREEN else str(fail)
    write_csv(reports/"message_catalog_phase22i_b_status_summary_v1.csv", [{"STATUS":status,"MESSAGES":msg,"TEXT_ROWS":txt,"LOCALES":loc,"VALIDATION_ISSUES":val,"SOURCE_MUTATION_AUTHORIZED":1 if args.allow_source_mutation else 0,"SOURCE_FILES_MUTATED":len(muts),"SOURCE_BACKUP_ROWS":len(backups),"CONTROLLED_EMIT_PATCH_APPLIED":1 if status==GREEN else 0,"BUILD_EXECUTED":0,"RUNTIME_SMOKE_EXECUTED":0,"ERRORS":"; ".join(errors),"NEXT_GATE":NEXT,"REPORT_TIMESTAMP_UTC":datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")}], ["STATUS","MESSAGES","TEXT_ROWS","LOCALES","VALIDATION_ISSUES","SOURCE_MUTATION_AUTHORIZED","SOURCE_FILES_MUTATED","SOURCE_BACKUP_ROWS","CONTROLLED_EMIT_PATCH_APPLIED","BUILD_EXECUTED","RUNTIME_SMOKE_EXECUTED","ERRORS","NEXT_GATE","REPORT_TIMESTAMP_UTC"])
    write_csv(reports/"message_catalog_phase22i_b_gate_check_v1.csv", gates, ["GATE","STATUS","DETAIL"])
    write_csv(reports/"message_catalog_phase22i_b_patch_actions_v1.csv", actions, ["TARGET_PATH","ACTION","DETAIL"])
    write_csv(reports/"message_catalog_phase22i_b_source_mutation_inventory_v1.csv", muts, ["TARGET_PATH","ACTION","BYTES","SHA256","DETAIL"])
    write_csv(reports/"message_catalog_phase22i_b_source_backup_inventory_v1.csv", backups, ["TARGET_PATH","BACKUP_PATH","BYTES","SHA256","ROLE"])
    boundary=[{"PROTECTED_SYSTEM":"SOURCE_CODE","MUTATION_ALLOWED":1,"OBSERVED_MUTATION":len(muts),"DETAIL":"Authorized source mutation limited to src/cli/cmd_set.cpp explicit diagnostic SET MESSAGE EMIT branch."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_DBF_CATALOG","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active DBF mutation."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_CDX_INDEXES","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active CDX/index mutation."},{"PROTECTED_SYSTEM":"ACTIVE_MESSAGING_LMDB","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No active LMDB mutation."},{"PROTECTED_SYSTEM":"HELP_DATA","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No HELP DATA mutation."},{"PROTECTED_SYSTEM":"CMDHELPCHK","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No CMDHELPCHK mutation."},{"PROTECTED_SYSTEM":"MANUALGEN","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No manualgen mutation."},{"PROTECTED_SYSTEM":"DATADICT_SELF_DOC","MUTATION_ALLOWED":0,"OBSERVED_MUTATION":0,"DETAIL":"No Data Dictionary/SelfDoc mutation."}]
    write_csv(reports/"message_catalog_phase22i_b_boundary_ledger_v1.csv", boundary, ["PROTECTED_SYSTEM","MUTATION_ALLOWED","OBSERVED_MUTATION","DETAIL"])
    smoke=repo/"docs/messaging/scripts/MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_EMIT_SMOKE.dts"; smoke.parent.mkdir(parents=True, exist_ok=True)
    smoke.write_text("* MESSAGE_CATALOG_PHASE22I_B_CONTROLLED_EMIT_SMOKE.dts\nSET LANGUAGE es\nSET MESSAGE EMIT HELP_HINT_COMMAND\nSET MESSAGE EMIT HELP_HINT_COMMAND LOCALE es\n\n", encoding="utf-8")
    print(status); print(f"  messages: {msg}"); print(f"  text rows: {txt}"); print(f"  locales: {loc.replace(';', ', ')}"); print(f"  validation issues: {val}"); print(f"  source mutation authorized: {1 if args.allow_source_mutation else 0}"); print(f"  source files mutated: {len(muts)}"); print(f"  source backup rows: {len(backups)}"); print("  build executed: 0"); print("  runtime smoke executed: 0"); print(f"  next gate: {NEXT}"); print(f"  reports: {reports}")
    return 0 if status==GREEN else 2
if __name__ == "__main__": raise SystemExit(main())
