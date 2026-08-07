#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MARKER = "@dottalk.usage v1"
REPORT_DIR = Path("dottalkpp") / "docs" / "generated" / "reports"
INV_CSV = REPORT_DIR / "source_contracts_inventory_v1_1.csv"
SOURCE = Path("src") / "cli" / "cmd_help.cpp"
OUT_MD = REPORT_DIR / "source_contract_cmd_help_hash_recheck_v0.md"
OUT_JSON = REPORT_DIR / "source_contract_cmd_help_hash_recheck_v0.json"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc, errors="strict")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="surrogateescape")


def sha(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="surrogateescape")).hexdigest()


def line_bounds(text: str, offset: int) -> tuple[int, int, str]:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end == -1:
        end = len(text)
    return start, end, text[start:end]


def marker_anchored_capture(text: str) -> str:
    match = re.search(re.escape(MARKER), text)
    if not match:
        return ""

    line_start, line_end, _line = line_bounds(text, match.start())
    end = line_end

    while end < len(text):
        next_start = end + 1
        if next_start >= len(text):
            break
        next_end = text.find("\n", next_start)
        if next_end == -1:
            next_end = len(text)
        next_line = text[next_start:next_end]
        if next_line.lstrip().startswith("//"):
            end = next_end
            if next_end == len(text):
                break
            continue
        if next_line.strip() == "":
            after_blank_start = next_end + 1
            if after_blank_start >= len(text):
                break
            after_blank_end = text.find("\n", after_blank_start)
            if after_blank_end == -1:
                after_blank_end = len(text)
            after_blank_line = text[after_blank_start:after_blank_end]
            if after_blank_line.lstrip().startswith("//"):
                end = next_end
                continue
        break

    return text[line_start:end]


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_csv_rows(INV_CSV)
    inv = next((row for row in rows if row.get("path", "").replace("\\", "/") == "src/cli/cmd_help.cpp"), {})
    inventory_hash = inv.get("header_hash", "")

    source_exists = SOURCE.is_file()
    current_hash = ""
    marker_count = 0
    if source_exists:
        text = read_text(SOURCE)
        marker_count = len(re.findall(re.escape(MARKER), text))
        current_hash = sha(marker_anchored_capture(text))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(SOURCE),
        "source_exists": source_exists,
        "marker_count": marker_count,
        "inventory_hash": inventory_hash,
        "current_marker_anchored_hash": current_hash,
        "hash_matches_inventory": bool(inventory_hash) and inventory_hash == current_hash,
        "inventory_row_present": bool(inv),
        "recommendation": (
            "cmd_help.cpp evidence refreshed and hash matches current marker-anchored capture"
            if bool(inventory_hash) and inventory_hash == current_hash
            else "hash mismatch remains; compare source timestamp/history before any patch path"
        ),
        "non_mutation_guards": [
            "did_not_edit_source",
            "did_not_write_dbfs",
            "did_not_modify_cmdhelpchk",
            "did_not_rebuild_help_data",
            "did_not_repair_headers",
        ],
    }

    OUT_JSON.write_text(json.dumps({"summary": summary}, indent=2), encoding="utf-8")

    lines = [
        "# source_contract_cmd_help_hash_recheck_v0",
        "",
        f"Generated UTC: `{summary['generated_at_utc']}`",
        "",
        "Safety class: `REPORT_ONLY`",
        "",
        "## Result",
        "",
        f"- source_exists: `{source_exists}`",
        f"- marker_count: `{marker_count}`",
        f"- inventory_row_present: `{bool(inv)}`",
        f"- inventory_hash: `{inventory_hash}`",
        f"- current_marker_anchored_hash: `{current_hash}`",
        f"- hash_matches_inventory: `{summary['hash_matches_inventory']}`",
        f"- recommendation: `{summary['recommendation']}`",
        "",
        "## Non-mutation confirmation",
        "",
    ]
    lines.extend(f"- `{guard}`" for guard in summary["non_mutation_guards"])
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("cmd_help.cpp hash recheck complete.")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"hash_matches_inventory: {summary['hash_matches_inventory']}")
    print("No source files were edited.")
    print("No DBFs were written.")
    print("CMDHELPCHK was not modified.")
    print("HELP DATA was not rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
