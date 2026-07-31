#!/usr/bin/env python3
"""Validate MAINT source-contract, DOTREF, and compiled usage parity."""

from __future__ import annotations

import json
import re
from pathlib import Path


REQUIRED_CONTRACT_FIELDS = ("noargs", "effect", "mutates", "risk", "usage-access")
BANNED_SOURCE_FRAGMENTS = (
    "docs/ai-friendly",
    "seed rows     : AIF-001 through AIF-004",
    "contract-like docs   : 144",
    "current unregistered  : 133",
    "registered not found  : 9",
)


def validate(repo_root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    command_path = repo_root / "src/cli/cmd_maint.cpp"
    dotref_path = repo_root / "include/dotref.hpp"
    messages_path = repo_root / "src/help/helpdata_messages.cpp"
    command = command_path.read_text(encoding="utf-8")
    dotref = dotref_path.read_text(encoding="utf-8")
    messages = messages_path.read_text(encoding="utf-8")

    def add(code: str, subject: str, detail: str) -> None:
        findings.append({"code": code, "subject": subject, "detail": detail})

    forms = re.findall(r"^// usage:[ \t]*(MAINT(?:[ \t]+.*)?)[ \t]*$", command, re.MULTILINE)
    if not forms:
        add("SOURCE_FORMS", "cmd_maint.cpp", "no MAINT usage forms found")
    for form in forms:
        if form not in dotref:
            add("DOTREF_FORM", form, "source form missing from DOTREF")
        if messages.count(f'"  {form}\\n"') < 2:
            add("MESSAGE_FORM", form, "source form is not present in both compiled usage bodies")

    for field in REQUIRED_CONTRACT_FIELDS:
        if not re.search(rf"^// {re.escape(field)}:\s*\S", command, re.MULTILINE):
            add("CONTRACT_FIELD", field, "required MAINT maturity field is absent")

    for fragment in BANNED_SOURCE_FRAGMENTS:
        if fragment in command:
            add("STALE_SOURCE_FACT", fragment, "stale fact or path remains in MAINT source")

    if command.count("contract_scan.py --summary") < 2:
        add("SCANNER_POINTER", "cmd_maint.cpp", "SCAN and DRIFT must point to generated current counts")
    for lane in ("gui", "contracts"):
        marker = f'"  {lane}'
        if messages.count(marker) < 2:
            add("LANE_TEXT_PARITY", lane, "lane is not present in both default and en-US text")
    return findings


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    findings = validate(root)
    print(json.dumps({"status": "PASS" if not findings else "FAIL", "findings": findings}, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
