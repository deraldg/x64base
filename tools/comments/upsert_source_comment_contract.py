from __future__ import annotations

import argparse
import csv
import hashlib
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path


COMMENT_LINE_RE = re.compile(r"^\s*//\s?(.*)$")
BLOCK_COMMENT_START_RE = re.compile(r"^\s*/\*\s*$")
BLOCK_COMMENT_END_RE = re.compile(r"^\s*\*/\s*$")
BLOCK_COMMENT_BODY_RE = re.compile(r"^\s*\*?\s?(.*)$")
OWNER_RE = re.compile(r"^owner:\s*(.+)$", re.IGNORECASE)
COMMAND_RE = re.compile(r"^command:\s*(.+)$", re.IGNORECASE)
SURFACE_RE = re.compile(r"^surface:\s*(.+)$", re.IGNORECASE)


@dataclass
class HeaderContract:
    relpath: str
    owner: str
    command: str
    header_lines: list[str]
    usage_start_ord: int
    first_code_line: int
    file_sha256: str


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Upsert one command header contract into staged source-comment import CSVs."
    )
    ap.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to this script's repo root.",
    )
    ap.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Source file to harvest, e.g. src/cli/cmd_bbox.cpp",
    )
    ap.add_argument(
        "--updated",
        default="20260625",
        help="YYYYMMDD stamp to write into SRCFILE.UPDATED",
    )
    ap.add_argument(
        "--staging-root",
        type=Path,
        help="Import CSV directory. Defaults to the repository staging directory.",
    )
    ap.add_argument(
        "--allow-replace-existing",
        action="store_true",
        help="Explicitly permit replacement of an existing file/command slice (header-only and potentially lossy).",
    )
    return ap.parse_args()


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        if reader.fieldnames is None:
            raise RuntimeError(f"CSV has no header: {path}")
        return rows, list(reader.fieldnames)


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def max_numeric(rows: list[dict[str, str]], field: str) -> int:
    vals = [int(r[field]) for r in rows if r.get(field, "").strip()]
    return max(vals) if vals else 0


def normalize_relpath(repo_root: Path, source: Path) -> str:
    full = source.resolve()
    return full.relative_to(repo_root.resolve()).as_posix()


def parse_line_comment_header(raw_lines: list[str]) -> tuple[list[str], int]:
    header_lines: list[str] = []
    i = 0
    while i < len(raw_lines):
        if raw_lines[i].strip() == "":
            if header_lines:
                header_lines.append("")
                i += 1
                continue
            break
        m = COMMENT_LINE_RE.match(raw_lines[i])
        if not m:
            break
        header_lines.append(m.group(1))
        i += 1
    return header_lines, i


def parse_block_comment_header(raw_lines: list[str]) -> tuple[list[str], int]:
    if not raw_lines or not BLOCK_COMMENT_START_RE.match(raw_lines[0]):
        return [], 0

    header_lines: list[str] = []
    i = 1
    while i < len(raw_lines):
        if BLOCK_COMMENT_END_RE.match(raw_lines[i]):
            return header_lines, i + 1
        m = BLOCK_COMMENT_BODY_RE.match(raw_lines[i])
        header_lines.append(m.group(1) if m else raw_lines[i].strip())
        i += 1

    raise RuntimeError("Unterminated leading block comment header")


def parse_header_contract(repo_root: Path, source: Path) -> HeaderContract:
    source_bytes = source.read_bytes()
    text = source_bytes.decode("utf-8")
    raw_lines = text.splitlines()

    while raw_lines and raw_lines[0].strip() == "":
        raw_lines.pop(0)

    header_lines, header_end_line = parse_line_comment_header(raw_lines)
    if not header_lines:
        header_lines, header_end_line = parse_block_comment_header(raw_lines)

    if not header_lines:
        raise RuntimeError(f"No leading usage-contract header block found in {source}")

    usage_start_ord = -1
    owner = ""
    command = ""
    for ord_idx, line in enumerate(header_lines, start=1):
        stripped = line.strip()
        if stripped.lower() == "@dottalk.usage v1":
            usage_start_ord = ord_idx
        if not owner:
            m = OWNER_RE.match(stripped)
            if m:
                owner = m.group(1).strip()
        if not command:
            m = COMMAND_RE.match(stripped)
            if m:
                command = m.group(1).strip()
        if not command:
            m = SURFACE_RE.match(stripped)
            if m:
                command = m.group(1).strip()

    if usage_start_ord < 0:
        raise RuntimeError(f"No @dottalk.usage v1 marker found in {source}")
    if not owner:
        raise RuntimeError(f"No owner: line found in {source}")
    if not command:
        raise RuntimeError(f"No command: or surface: line found in {source}")

    first_code_line = header_end_line + 1
    while first_code_line <= len(raw_lines) and raw_lines[first_code_line - 1].strip() == "":
        first_code_line += 1

    relpath = normalize_relpath(repo_root, source)
    if header_lines and header_lines[0].strip().lower() == source.name.lower():
        header_lines[0] = relpath

    return HeaderContract(
        relpath=relpath,
        owner=owner,
        command=command,
        header_lines=header_lines,
        usage_start_ord=usage_start_ord,
        first_code_line=first_code_line,
        file_sha256=hashlib.sha256(source_bytes).hexdigest().upper(),
    )


def wrap_memo_lines(lines: list[str], width: int = 1000) -> list[str]:
    joined = " ".join(lines).strip()
    if not joined:
        return [""]
    return textwrap.wrap(joined, width=width, break_long_words=False, break_on_hyphens=False)


def build_rows(
    contract: HeaderContract,
    updated: str,
    next_fileid: int,
    next_blockid: int,
    next_usageid: int,
    next_lineid: int,
) -> dict[str, list[dict[str, str]]]:
    fileid = next_fileid
    leading_blockid = next_blockid
    usage_blockid = next_blockid + 1
    leading_usageid = next_usageid
    usage_usageid = next_usageid + 1

    root = contract.relpath.split("/", 1)[0]
    ext = Path(contract.relpath).suffix.lstrip(".")
    last_hdr = len(contract.header_lines)

    srcfile = [{
        "FILEID": str(fileid),
        "RELPATH": contract.relpath,
        "ROOT": root,
        "EXT": ext,
        "HASH": contract.file_sha256,
        "HAS_HDR": "T",
        "HDR_LINES": str(last_hdr),
        "FIRST_HDR": "1",
        "LAST_HDR": str(last_hdr),
        "FIRST_CODE": str(contract.first_code_line),
        "DET_KIND": "USAGE_CONTRACT",
        "DET_OWNER": contract.owner,
        "DET_CMD": contract.command,
        "STATUS": "ACTIVE",
        "UPDATED": updated,
    }]

    srcblock = [
        {
            "BLOCKID": str(leading_blockid),
            "FILEID": str(fileid),
            "RELPATH": contract.relpath,
            "BTYPE": "LEADING_HEADER",
            "STARTLN": "1",
            "ENDLN": str(last_hdr),
            "NLINES": "0",
            "KIND": "USAGE_CONTRACT",
            "OWNER": contract.owner,
            "COMMAND": contract.command,
            "NAME": "",
            "SUMMARY": "",
            "TEXTMEMO": f"SRCBLOCK:{leading_blockid:012d}:TEXTMEMO",
            "CONFID": "IMPORTED",
            "SEVERITY": "INFO",
        },
        {
            "BLOCKID": str(usage_blockid),
            "FILEID": str(fileid),
            "RELPATH": contract.relpath,
            "BTYPE": "DOTTALK_USAGE",
            "STARTLN": str(contract.usage_start_ord),
            "ENDLN": str(last_hdr),
            "NLINES": "0",
            "KIND": "USAGE_CONTRACT",
            "OWNER": contract.owner,
            "COMMAND": contract.command,
            "NAME": "",
            "SUMMARY": "",
            "TEXTMEMO": f"SRCBLOCK:{usage_blockid:012d}:TEXTMEMO",
            "CONFID": "IMPORTED",
            "SEVERITY": "INFO",
        },
    ]

    srcusage = [
        {
            "USAGEID": str(leading_usageid),
            "BLOCKID": "0",
            "FILEID": str(fileid),
            "OWNER": contract.owner,
            "COMMAND": contract.command,
            "CATEGORY": "",
            "STATUS": "ACTIVE",
            "NOARGS": "",
            "EFFECT": "",
            "MUTATES": "",
            "USGACC": "",
            "SUMMARY": "",
            "USAGE": "",
            "EXAMPLES": "",
            "NOTES": "",
            "RELATED": "",
        },
        {
            "USAGEID": str(usage_usageid),
            "BLOCKID": "0",
            "FILEID": str(fileid),
            "OWNER": contract.owner,
            "COMMAND": contract.command,
            "CATEGORY": "",
            "STATUS": "ACTIVE",
            "NOARGS": "",
            "EFFECT": "",
            "MUTATES": "",
            "USGACC": "",
            "SUMMARY": "",
            "USAGE": "",
            "EXAMPLES": "",
            "NOTES": "",
            "RELATED": "",
        },
    ]

    srcclass = [
        {
            "CLASSID": str(leading_blockid),
            "FILEID": str(fileid),
            "BLOCKID": "0",
            "COMMAND": contract.command,
            "NORMCMD": contract.command,
            "CMDKEY": contract.owner,
            "STATUS": "UNCHANGED",
            "RULEID": "",
            "POLICY": "",
            "REASON": "",
            "ACTION": "",
        },
        {
            "CLASSID": str(usage_blockid),
            "FILEID": str(fileid),
            "BLOCKID": "0",
            "COMMAND": contract.command,
            "NORMCMD": contract.command,
            "CMDKEY": contract.owner,
            "STATUS": "UNCHANGED",
            "RULEID": "",
            "POLICY": "",
            "REASON": "",
            "ACTION": "",
        },
    ]

    srcline: list[dict[str, str]] = []
    for ord_idx, line in enumerate(contract.header_lines, start=1):
        srcline.append(
            {
                "LINEID": str(next_lineid + ord_idx - 1),
                "BLOCKID": "0",
                "FILEID": str(fileid),
                "RELPATH": contract.relpath,
                "LINENO": "0",
                "ORD": str(ord_idx),
                "ROLE": "HEADER",
                "TEXT": line,
                "TEXTMEMO": "",
            }
        )

    memo_lines: list[dict[str, str]] = []
    leading_memo = wrap_memo_lines(contract.header_lines)
    usage_memo = wrap_memo_lines(contract.header_lines[contract.usage_start_ord - 1 :])
    for idx, text_line in enumerate(leading_memo, start=1):
        memo_lines.append(
            {
                "MEMOKEY": f"SRCBLOCK:{leading_blockid:012d}:TEXTMEMO",
                "LINENO": str(idx),
                "LINECONT": text_line,
            }
        )
    for idx, text_line in enumerate(usage_memo, start=1):
        memo_lines.append(
            {
                "MEMOKEY": f"SRCBLOCK:{usage_blockid:012d}:TEXTMEMO",
                "LINENO": str(idx),
                "LINECONT": text_line,
            }
        )

    return {
        "SRCFILE_IMPORT.csv": srcfile,
        "SRCBLOCK_IMPORT.csv": srcblock,
        "SRCUSAGE_IMPORT.csv": srcusage,
        "SRCCLASS_IMPORT.csv": srcclass,
        "SRCLINE_IMPORT.csv": srcline,
        "MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv": memo_lines,
    }


def remove_existing(
    csv_rows: dict[str, list[dict[str, str]]],
    contract: HeaderContract,
) -> tuple[dict[str, list[dict[str, str]]], set[str], set[str]]:
    existing_fileids = {
        row["FILEID"]
        for row in csv_rows["SRCFILE_IMPORT.csv"]
        if row["RELPATH"] == contract.relpath or row["DET_CMD"] == contract.command
    }
    existing_memokeys = {
        row["TEXTMEMO"]
        for row in csv_rows["SRCBLOCK_IMPORT.csv"]
        if row["FILEID"] in existing_fileids or row["COMMAND"] == contract.command
    }

    cleaned = {
        "SRCFILE_IMPORT.csv": [
            row
            for row in csv_rows["SRCFILE_IMPORT.csv"]
            if row["FILEID"] not in existing_fileids
            and row["RELPATH"] != contract.relpath
            and row["DET_CMD"] != contract.command
        ],
        "SRCBLOCK_IMPORT.csv": [
            row
            for row in csv_rows["SRCBLOCK_IMPORT.csv"]
            if row["FILEID"] not in existing_fileids and row["COMMAND"] != contract.command
        ],
        "SRCUSAGE_IMPORT.csv": [
            row
            for row in csv_rows["SRCUSAGE_IMPORT.csv"]
            if row["FILEID"] not in existing_fileids and row["COMMAND"] != contract.command
        ],
        "SRCCLASS_IMPORT.csv": [
            row
            for row in csv_rows["SRCCLASS_IMPORT.csv"]
            if row["FILEID"] not in existing_fileids and row["COMMAND"] != contract.command
        ],
        "SRCLINE_IMPORT.csv": [
            row
            for row in csv_rows["SRCLINE_IMPORT.csv"]
            if row["FILEID"] not in existing_fileids and row["RELPATH"] != contract.relpath
        ],
        "MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv": [
            row
            for row in csv_rows["MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv"]
            if row["MEMOKEY"] not in existing_memokeys
        ],
    }
    return cleaned, existing_fileids, existing_memokeys


def sort_rows(name: str, rows: list[dict[str, str]]) -> list[dict[str, str]]:
    key_fields = {
        "SRCFILE_IMPORT.csv": ("FILEID",),
        "SRCBLOCK_IMPORT.csv": ("BLOCKID",),
        "SRCUSAGE_IMPORT.csv": ("USAGEID",),
        "SRCCLASS_IMPORT.csv": ("CLASSID",),
        "SRCLINE_IMPORT.csv": ("LINEID",),
        "MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv": ("MEMOKEY", "LINENO"),
    }[name]

    def keyfunc(row: dict[str, str]):
        out: list[object] = []
        for field in key_fields:
            val = row.get(field) or ""
            if field in {"MEMOKEY"}:
                out.append(val)
            else:
                try:
                    out.append(int(val))
                except ValueError:
                    out.append(val)
        return tuple(out)

    return sorted(rows, key=keyfunc)


def upsert_contracts(
    repo_root: Path,
    sources: list[Path],
    staging_root: Path,
    updated: str,
    allow_replace_existing: bool = False,
) -> list[HeaderContract]:
    file_order = [
        "SRCFILE_IMPORT.csv",
        "SRCBLOCK_IMPORT.csv",
        "SRCLINE_IMPORT.csv",
        "SRCUSAGE_IMPORT.csv",
        "SRCCLASS_IMPORT.csv",
        "MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv",
    ]

    csv_rows: dict[str, list[dict[str, str]]] = {}
    fieldnames: dict[str, list[str]] = {}
    for name in file_order:
        path = staging_root / name
        rows, names = read_csv_rows(path)
        csv_rows[name] = rows
        fieldnames[name] = names

    contracts: list[HeaderContract] = []
    for source in sources:
        if not source.is_absolute():
            source = repo_root / source
        contract = parse_header_contract(repo_root, source.resolve())
        existing = [
            row for row in csv_rows["SRCFILE_IMPORT.csv"]
            if row["RELPATH"] == contract.relpath or row["DET_CMD"] == contract.command
        ]
        if existing and not allow_replace_existing:
            raise RuntimeError(
                f"Refusing header-only replacement of existing metadata for {contract.relpath}; "
                "use a full-comment harvester or pass --allow-replace-existing after review."
            )
        csv_rows, _, _ = remove_existing(csv_rows, contract)
        additions = build_rows(
            contract=contract,
            updated=updated,
            next_fileid=max_numeric(csv_rows["SRCFILE_IMPORT.csv"], "FILEID") + 1,
            next_blockid=max_numeric(csv_rows["SRCBLOCK_IMPORT.csv"], "BLOCKID") + 1,
            next_usageid=max_numeric(csv_rows["SRCUSAGE_IMPORT.csv"], "USAGEID") + 1,
            next_lineid=max_numeric(csv_rows["SRCLINE_IMPORT.csv"], "LINEID") + 1,
        )
        for name in file_order:
            csv_rows[name] = csv_rows[name] + additions[name]
        contracts.append(contract)

    for name in file_order:
        write_csv_rows(staging_root / name, fieldnames[name], sort_rows(name, csv_rows[name]))
    return contracts


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    staging_root = (
        args.staging_root.resolve()
        if args.staging_root
        else repo_root / "dottalkpp" / "docs" / "generated" / "staging" / "source_comment_metadata_import_v1"
    )
    contracts = upsert_contracts(
        repo_root,
        [args.source],
        staging_root,
        args.updated,
        allow_replace_existing=args.allow_replace_existing,
    )
    contract = contracts[0]

    print(f"Updated staged source-comment CSVs for {contract.command} from {contract.relpath}")
    print(f"  owner      : {contract.owner}")
    print(f"  header rows: {len(contract.header_lines)}")
    print(f"  usage start: {contract.usage_start_ord}")
    print(f"  first code : {contract.first_code_line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
