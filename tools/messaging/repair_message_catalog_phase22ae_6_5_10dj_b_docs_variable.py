from __future__ import annotations
import argparse
from pathlib import Path

TARGET_REL = "tools/messaging/stage_message_catalog_phase22ae_6_5_10dj_b_active_help_cmdhelpchk_target_verification_probe.py"

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    target = repo / TARGET_REL
    if not target.exists():
        print(f"DJ_B_V1_1_REPAIR_RED_TARGET_SCRIPT_MISSING: {target}")
        return 1

    text = target.read_text(encoding="utf-8", errors="replace")
    if 'docs = repo / "docs/messaging"' in text:
        print("DJ_B_V1_1_REPAIR_GREEN_DOCS_VARIABLE_ALREADY_PRESENT")
        print(f"  target: {target}")
        return 0

    needle = 'reports = repo / "docs/messaging/reports"'
    if needle not in text:
        print("DJ_B_V1_1_REPAIR_RED_ANCHOR_NOT_FOUND")
        print(f"  target: {target}")
        return 1

    repaired = text.replace(needle, 'docs = repo / "docs/messaging"\n    ' + needle, 1)
    backup = target.with_suffix(target.suffix + ".pre_dj_b_v1_1_docs_variable_repair.bak")
    backup.write_text(text, encoding="utf-8", newline="\n")
    target.write_text(repaired, encoding="utf-8", newline="\n")

    print("DJ_B_V1_1_REPAIR_GREEN_DOCS_VARIABLE_INSERTED")
    print(f"  target: {target}")
    print(f"  backup: {backup}")
    print("  protected system mutation: 0")
    print("  HELP DATA apply executed: 0")
    print("  CMDHELPCHK apply executed: 0")
    print("  active target selected now: 0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
