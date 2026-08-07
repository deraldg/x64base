#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py"
BACKUP = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.py.bak_hotfix_001"
PAYLOAD = Path("selfdoc") / "probes" / "source_contract_inventory_probe_v1_1.hotfix_001.py"


def main() -> int:
    if not PAYLOAD.is_file():
        raise SystemExit(f"Missing payload: {PAYLOAD}")
    if not TARGET.parent.is_dir():
        TARGET.parent.mkdir(parents=True, exist_ok=True)

    payload = PAYLOAD.read_text(encoding="utf-8")

    if TARGET.is_file():
        existing = TARGET.read_text(encoding="utf-8")
        if existing == payload:
            print(f"No changes needed: {TARGET} already matches hotfix_001.")
        else:
            BACKUP.write_text(existing, encoding="utf-8")
            TARGET.write_text(payload, encoding="utf-8", newline="\n")
            print(f"Updated: {TARGET}")
            print(f"Backup written to: {BACKUP}")
    else:
        TARGET.write_text(payload, encoding="utf-8", newline="\n")
        print(f"Created: {TARGET}")

    try:
        PAYLOAD.unlink()
    except OSError:
        pass

    print("Hotfix 001 applied to v1.1 candidate probe only.")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    print("No source contracts were repaired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
