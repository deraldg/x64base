from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import textwrap
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DEFAULT_RUN = Path("docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260716-001")
DEFAULT_EXTENSIONS = ".c,.cc,.cpp,.cxx,.h,.hpp,.hxx,.inl,.ipp"
USAGE_RE = re.compile(r"^\s*@dottalk\.usage\s+v1\s*$", re.IGNORECASE)
OWNER_RE = re.compile(r"^\s*owner:\s*(.+?)\s*$", re.IGNORECASE)
COMMAND_RE = re.compile(r"^\s*(?:command|surface):\s*(.+?)\s*$", re.IGNORECASE)
FIELD_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")
CONTRACT_END_RE = re.compile(r"^\s*@dottalk\.(?:end|contract\.end)\s*$", re.IGNORECASE)
USAGE_FIELD_ALIASES = {
    "note": "notes",
    "notes": "notes",
    "example": "examples",
    "examples": "examples",
    "usage-access": "usage-access",
}
USAGE_FIELDS = {
    "owner", "command", "surface", "category", "status", "noargs", "effect",
    "mutates", "usage-access", "summary", "usage", "examples", "notes", "related",
}


@dataclass
class UsageContractBlock:
    start_line: int
    end_line: int
    lines: list[str]
    owner: str
    command: str
    fields: dict[str, str]

    @property
    def complete(self) -> bool:
        return bool(self.owner) and bool(self.command)


@dataclass
class HarvestedFile:
    path: Path
    relpath: str
    extension: str
    sha256: str
    line_count: int
    header_start: int
    header_end: int
    first_code: int
    header_lines: list[str]
    usage_ord: int
    owner: str
    command: str
    usage_fields: dict[str, str]
    usage_contracts: list[UsageContractBlock]

    @property
    def has_header(self) -> bool:
        return bool(self.header_lines)

    @property
    def has_usage(self) -> bool:
        return bool(self.usage_contracts)

    @property
    def complete_usage(self) -> bool:
        return self.has_usage and all(contract.complete for contract in self.usage_contracts)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Reharvest complete leading-comment and @dottalk.usage slices into isolated SRC* candidate CSVs."
    )
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_RUN / "comments_reharvest/post_messaging_20260716",
    )
    ap.add_argument("--roots", nargs="+", default=["src", "include", "bindings"])
    ap.add_argument("--extensions", default=DEFAULT_EXTENSIONS)
    ap.add_argument(
        "--allow-untracked",
        action="store_true",
        help="Harvest files that are on disk but NOT known to git. Off by default: "
             "the catalog documents the repository, not the working tree. See "
             "discover() for why this matters.",
    )
    ap.add_argument("--updated", default="20260716")
    ap.add_argument(
        "--policy-source",
        type=Path,
        default=Path("dottalkpp/docs/generated/staging/source_comment_metadata_import_v1"),
    )
    return ap.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def decode_source(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def clean_line_comment(line: str) -> str | None:
    match = re.match(r"^\s*//(?:\s?)(.*)$", line)
    return match.group(1) if match else None


def clean_block_line(line: str, first: bool, last: bool) -> str:
    value = line.strip()
    if first:
        value = re.sub(r"^/\*+\s?", "", value)
    if last:
        value = re.sub(r"\s?\*/\s*$", "", value)
    value = re.sub(r"^\*\s?", "", value)
    return value


def parse_leading_comment(raw_lines: list[str]) -> tuple[int, int, int, list[str]]:
    start = 0
    while start < len(raw_lines) and not raw_lines[start].strip():
        start += 1
    if start >= len(raw_lines):
        return 0, 0, 0, []

    header: list[str] = []
    end = start
    first_clean = clean_line_comment(raw_lines[start])
    if first_clean is not None:
        i = start
        while i < len(raw_lines):
            cleaned = clean_line_comment(raw_lines[i])
            if cleaned is not None:
                header.append(cleaned)
                end = i
                i += 1
                continue
            if not raw_lines[i].strip() and header:
                header.append("")
                end = i
                i += 1
                continue
            break
    elif raw_lines[start].lstrip().startswith("/*"):
        i = start
        block: list[str] = []
        closed = False
        while i < len(raw_lines):
            block.append(raw_lines[i])
            end = i
            if "*/" in raw_lines[i]:
                closed = True
                break
            i += 1
        if not closed:
            return 0, 0, start + 1, []
        header = [
            clean_block_line(line, idx == 0, idx == len(block) - 1)
            for idx, line in enumerate(block)
        ]
    else:
        return 0, 0, start + 1, []

    first_code_idx = end + 1
    while first_code_idx < len(raw_lines) and not raw_lines[first_code_idx].strip():
        first_code_idx += 1
    first_code = first_code_idx + 1 if first_code_idx < len(raw_lines) else 0
    return start + 1, end + 1, first_code, header


def parse_usage_fields(header_lines: list[str], usage_ord: int) -> dict[str, str]:
    """Project one usage contract into the fields supported by SRCUSAGE."""
    if usage_ord <= 0:
        return {}

    values: dict[str, list[str]] = {field: [] for field in USAGE_FIELDS}
    current_key = ""
    for raw in header_lines[usage_ord:]:
        line = raw.strip()
        if CONTRACT_END_RE.match(line):
            break
        if not line:
            continue
        match = FIELD_RE.match(line)
        if match:
            source_key = match.group(1).strip().lower()
            key = USAGE_FIELD_ALIASES.get(source_key, source_key)
            current_key = key if key in USAGE_FIELDS else ""
            value = match.group(2).strip()
            if current_key and value:
                values[current_key].append(value)
            continue
        if current_key:
            values[current_key].append(line)

    projected: dict[str, str] = {}
    for key, parts in values.items():
        if not parts:
            continue
        if key in {"usage", "examples", "notes"}:
            projected[key] = "\n".join(parts)
        elif key == "related":
            projected[key] = "; ".join(parts)
        else:
            projected[key] = " ".join(parts)
    return projected


def usage_contract_block(start_line: int, contract_lines: list[str]) -> UsageContractBlock:
    """Build one semantic contract from already-cleaned comment lines."""
    owner = ""
    command = ""
    for line in contract_lines:
        if not owner:
            match = OWNER_RE.match(line)
            if match:
                owner = match.group(1).strip()
        if not command:
            match = COMMAND_RE.match(line)
            if match:
                command = match.group(1).strip()
    return UsageContractBlock(
        start_line=start_line,
        end_line=start_line + len(contract_lines) - 1,
        lines=contract_lines,
        owner=owner,
        command=command,
        fields=parse_usage_fields(contract_lines, 1),
    )


def extract_usage_contracts(raw_lines: list[str]) -> list[UsageContractBlock]:
    """Extract every line-comment usage contract, including mid-file contracts."""
    contracts: list[UsageContractBlock] = []
    index = 0
    while index < len(raw_lines):
        cleaned = clean_line_comment(raw_lines[index])
        if cleaned is None or not USAGE_RE.match(cleaned):
            index += 1
            continue

        start = index
        contract_lines: list[str] = []
        while index < len(raw_lines):
            cleaned = clean_line_comment(raw_lines[index])
            if cleaned is None:
                break
            # Adjacent contracts may be separated only by a line-comment marker.
            # Leave the next marker for the outer loop instead of merging its
            # fields into the current semantic row.
            if index > start and USAGE_RE.match(cleaned):
                break
            contract_lines.append(cleaned)
            index += 1
            if CONTRACT_END_RE.match(cleaned):
                break
        contracts.append(usage_contract_block(start + 1, contract_lines))
    return contracts


def harvest_file(repo: Path, path: Path) -> HarvestedFile:
    data = path.read_bytes()
    text = decode_source(data)
    raw_lines = text.splitlines()
    start, end, first_code, header = parse_leading_comment(raw_lines)
    usage_contracts = extract_usage_contracts(raw_lines)
    usage_ord = 0
    owner = ""
    command = ""
    for ord_no, line in enumerate(header, start=1):
        if not usage_ord and USAGE_RE.match(line):
            usage_ord = ord_no
        if not owner:
            match = OWNER_RE.match(line)
            if match:
                owner = match.group(1).strip()
        if not command:
            match = COMMAND_RE.match(line)
            if match:
                command = match.group(1).strip()
    usage_fields = parse_usage_fields(header, usage_ord)
    if usage_ord:
        header_contract_start = start + usage_ord - 1
        if not any(contract.start_line == header_contract_start for contract in usage_contracts):
            usage_contracts.insert(0, usage_contract_block(
                header_contract_start, header[usage_ord - 1 :]
            ))
    if usage_contracts:
        owner = usage_contracts[0].owner
        command = usage_contracts[0].command
        usage_fields = usage_contracts[0].fields
    return HarvestedFile(
        path=path,
        relpath=path.relative_to(repo).as_posix(),
        extension=path.suffix.lower(),
        sha256=sha256_bytes(data),
        line_count=len(raw_lines),
        header_start=start,
        header_end=end,
        first_code=first_code,
        header_lines=header,
        usage_ord=usage_ord,
        owner=owner,
        command=command,
        usage_fields=usage_fields,
        usage_contracts=usage_contracts,
    )


def usage_row_for_block(
    item: HarvestedFile,
    block_type: str,
    usage_id: int,
    block_id: int,
    file_id: int,
    fallback_status: str,
) -> dict[str, str] | None:
    """Emit exactly one semantic usage row, owned by the nested usage block."""
    if block_type != "DOTTALK_USAGE":
        return None
    fields = item.usage_fields
    source_status = fields.get("status", "").upper()
    return {
        "USAGEID": str(usage_id),
        "BLOCKID": str(block_id),
        "FILEID": str(file_id),
        "OWNER": item.owner,
        "COMMAND": item.command,
        "CATEGORY": fields.get("category", ""),
        "STATUS": source_status or fallback_status,
        "NOARGS": fields.get("noargs", ""),
        "EFFECT": fields.get("effect", ""),
        "MUTATES": fields.get("mutates", ""),
        "USGACC": fields.get("usage-access", ""),
        "SUMMARY": fields.get("summary", ""),
        "USAGE": fields.get("usage", ""),
        "EXAMPLES": fields.get("examples", ""),
        "NOTES": fields.get("notes", ""),
        "RELATED": fields.get("related", ""),
    }


def usage_row_for_contract(
    contract: UsageContractBlock,
    usage_id: int,
    block_id: int,
    file_id: int,
    fallback_status: str,
) -> dict[str, str]:
    fields = contract.fields
    source_status = fields.get("status", "").upper()
    return {
        "USAGEID": str(usage_id),
        "BLOCKID": str(block_id),
        "FILEID": str(file_id),
        "OWNER": contract.owner,
        "COMMAND": contract.command,
        "CATEGORY": fields.get("category", ""),
        "STATUS": source_status or fallback_status,
        "NOARGS": fields.get("noargs", ""),
        "EFFECT": fields.get("effect", ""),
        "MUTATES": fields.get("mutates", ""),
        "USGACC": fields.get("usage-access", ""),
        "SUMMARY": fields.get("summary", ""),
        "USAGE": fields.get("usage", ""),
        "EXAMPLES": fields.get("examples", ""),
        "NOTES": fields.get("notes", ""),
        "RELATED": fields.get("related", ""),
    }


def git_tracked(repo: Path, roots: list[str]) -> set[Path] | None:
    """Paths git knows about, resolved absolute. None if git is unavailable.

    The catalog's membership rule. See discover() for why it is git and not
    the filesystem.
    """
    try:
        out = subprocess.check_output(
            ["git", "--no-optional-locks", "-C", str(repo), "ls-files", *roots],
            text=True, stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    return {(repo / line).resolve() for line in out.splitlines() if line.strip()}


def discover(repo: Path, roots: list[str], extensions: set[str],
             allow_untracked: bool = False) -> list[Path]:
    """Enumerate the source set the SRC* catalog describes.

    MEMBERSHIP IS GIT, NOT THE FILESYSTEM (decided 2026-07-26, member.derald).
    A walk sees whatever happens to be lying in the working tree; a clone
    cannot reproduce that, so a catalog built from it documents one machine's
    scratch state rather than the project. The 2026-07-26 reload loaded 10
    never-committed files -- five src/tests/test_*.cpp, the include/reference
    + src/reference pair, and src/cli/cmd_transaction.cpp -- and stack_audit
    correctly reported all ten as PHANTOM rows. The walk was not wrong about
    what was on disk; it was answering a different question than the guard.

    The walk is still what enumerates, because its exclusion rules matter and
    because git ls-files happily lists files deleted from disk but not from
    the index. Git is applied as an intersection, not a replacement.

    EXCLUSION BUG, fixed here (2026-07-26):
        any(part.lower().startswith("build") for part in path.parts)
    path.parts includes the FILENAME. The rule was meant to skip build/ and
    build-wsl/ output trees; it also silently swallowed every source file
    whose NAME begins with "build". Repo-wide that was exactly one file --
    include/cli/build_vectors_report.hpp, committed in d58851656, carrying a
    valid 8-line @dottalk.file banner -- which is why stack_audit reported
    UNCOLLECTED for it while every in-scope test it could be given passed.
    A filter that drops a documented file for matching a directory rule is
    worse than no filter: it fails silently and the count still looks round.
    Directory parts only now.
    """
    tracked = None if allow_untracked else git_tracked(repo, roots)
    found: set[Path] = set()
    skipped_untracked: list[str] = []
    for root_name in roots:
        root = (repo / root_name).resolve()
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in extensions:
                continue
            dir_parts = {part.lower() for part in path.parts[:-1]}
            if dir_parts.intersection({".git", ".vs", "packages", "_stage"}) or any(
                part.lower().startswith("build") for part in path.parts[:-1]
            ):
                continue
            resolved = path.resolve()
            if tracked is not None and resolved not in tracked:
                skipped_untracked.append(resolved.relative_to(repo).as_posix())
                continue
            found.add(resolved)
    if skipped_untracked:
        print(f"discover: {len(skipped_untracked)} on-disk file(s) skipped -- not known to git")
        for rel in sorted(skipped_untracked):
            print(f"    {rel}")
        print("  (commit them, or re-run with --allow-untracked, to include them)")
    return sorted(found, key=lambda p: p.relative_to(repo).as_posix().lower())


def read_fieldnames(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise RuntimeError(f"CSV has no header: {path}")
        return list(reader.fieldnames)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def chunks(text: str, width: int = 1000) -> list[str]:
    if not text:
        return [""]
    return [text[pos : pos + width] for pos in range(0, len(text), width)]


def physical_chunks(lines: list[str], width: int = 1000) -> list[str]:
    flattened = " ".join(part for part in (line.strip() for line in lines) if part)
    return textwrap.wrap(flattened, width=width, break_long_words=True, break_on_hyphens=False) or [""]


def main() -> int:
    args = parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    policy_source = args.policy_source if args.policy_source.is_absolute() else repo / args.policy_source
    candidate = output / "candidate_source_comment_metadata_import_v2"
    extensions = {value.strip().lower() for value in args.extensions.split(",") if value.strip()}
    paths = discover(repo, args.roots, extensions, allow_untracked=args.allow_untracked)
    harvested = [harvest_file(repo, path) for path in paths]

    table_names = [
        "SRCFILE_IMPORT.csv",
        "SRCBLOCK_IMPORT.csv",
        "SRCLINE_IMPORT.csv",
        "SRCUSAGE_IMPORT.csv",
        "SRCCLASS_IMPORT.csv",
        "MEMO_LINES_IMPORT.csv",
        "MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv",
    ]
    fields = {name: read_fieldnames(policy_source / name) for name in table_names}
    rows: dict[str, list[dict[str, str]]] = {name: [] for name in table_names}
    issues: list[dict[str, str]] = []
    block_id = 0
    line_id = 0
    usage_id = 0

    for file_id, item in enumerate(harvested, start=1):
        det_kind = "USAGE_CONTRACT" if item.has_usage else "HEADER_COMMENT"
        status = "ACTIVE" if not item.has_usage or item.complete_usage else "REVIEW"
        rows["SRCFILE_IMPORT.csv"].append({
            "FILEID": str(file_id),
            "RELPATH": item.relpath,
            "ROOT": item.relpath.split("/", 1)[0],
            "EXT": item.extension.lstrip("."),
            "HASH": item.sha256,
            "HAS_HDR": "T" if item.has_header else "F",
            "HDR_LINES": str(len(item.header_lines)),
            "FIRST_HDR": str(item.header_start) if item.has_header else "",
            "LAST_HDR": str(item.header_end) if item.has_header else "",
            "FIRST_CODE": str(item.first_code or 0),
            "DET_KIND": det_kind,
            "DET_OWNER": item.owner,
            "DET_CMD": item.command,
            "STATUS": status,
            "UPDATED": args.updated,
        })
        for contract in item.usage_contracts:
            if contract.complete:
                continue
            missing = ",".join(
                name for name, value in (("owner", contract.owner), ("command", contract.command)) if not value
            )
            issues.append({
                "priority": "P1", "path": item.relpath,
                "issue": "INCOMPLETE_USAGE_CONTRACT",
                "detail": f"line:{contract.start_line};missing:{missing}",
            })
        if not item.has_header and not item.has_usage:
            continue

        block_specs: list[tuple[str, int, int, list[str], str, str, UsageContractBlock | None]] = []
        if item.has_header:
            block_specs.append((
                "LEADING_HEADER", item.header_start, item.header_end, item.header_lines,
                item.owner, item.command, None,
            ))
        for contract in item.usage_contracts:
            block_specs.append((
                "DOTTALK_USAGE", contract.start_line, contract.end_line, contract.lines,
                contract.owner, contract.command, contract,
            ))
        for block_type, source_start, source_end, block_lines, block_owner, block_command, contract in block_specs:
            block_id += 1
            kind = "USAGE_CONTRACT" if block_type == "DOTTALK_USAGE" else "HEADER_COMMENT"
            memo_key = f"SRCBLOCK:{block_id:012d}:TEXTMEMO"
            rows["SRCBLOCK_IMPORT.csv"].append({
                "BLOCKID": str(block_id), "FILEID": str(file_id), "RELPATH": item.relpath,
                "BTYPE": block_type, "STARTLN": str(source_start), "ENDLN": str(source_end),
                "NLINES": str(len(block_lines)), "KIND": kind, "OWNER": block_owner,
                "COMMAND": block_command, "NAME": "", "SUMMARY": "", "TEXTMEMO": memo_key,
                "CONFID": "REHARVESTED", "SEVERITY": "INFO",
            })
            for ord_no, text in enumerate(block_lines, start=1):
                line_id += 1
                rows["SRCLINE_IMPORT.csv"].append({
                    "LINEID": str(line_id), "BLOCKID": str(block_id), "FILEID": str(file_id),
                    "RELPATH": item.relpath, "LINENO": str(source_start + ord_no - 1),
                    "ORD": str(ord_no), "ROLE": "USAGE" if block_type == "DOTTALK_USAGE" else "HEADER",
                    "TEXT": text[:240], "TEXTMEMO": "",
                })
                if len(text) > 240:
                    issues.append({"priority": "P2", "path": item.relpath, "issue": "SRCLINE_TEXT_TRUNCATED", "detail": f"source_line:{source_start + ord_no - 1};length:{len(text)}"})
            logical_text = "\n".join(block_lines)
            for memo_line, text in enumerate(chunks(logical_text), start=1):
                rows["MEMO_LINES_IMPORT.csv"].append({"MEMOKEY": memo_key, "LINENO": str(memo_line), "LINECONT": text})
            for memo_line, text in enumerate(physical_chunks(block_lines), start=1):
                rows["MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv"].append(
                    {"MEMOKEY": memo_key, "LINENO": str(memo_line), "LINECONT": text}
                )
            rows["SRCCLASS_IMPORT.csv"].append({
                "CLASSID": str(block_id), "FILEID": str(file_id), "BLOCKID": str(block_id),
                "COMMAND": block_command, "NORMCMD": block_command.upper(), "CMDKEY": block_owner,
                "STATUS": "UNREVIEWED", "RULEID": "REHARVEST_V1", "POLICY": "PRESERVE_AND_REVIEW",
                "REASON": "Post-messaging source-comment reharvest candidate.",
                "ACTION": "REVIEW_BEFORE_IMPORT",
            })
            if contract is not None:
                usage_id += 1
                rows["SRCUSAGE_IMPORT.csv"].append(usage_row_for_contract(
                    contract, usage_id, block_id, file_id, status
                ))

    for name in table_names:
        write_rows(candidate / name, fields[name], rows[name])
    for policy_name in ("SRCALIAS_IMPORT.csv", "SRCDISP_IMPORT.csv"):
        (candidate / policy_name).write_bytes((policy_source / policy_name).read_bytes())

    issue_fields = ["priority", "path", "issue", "detail"]
    write_rows(output / "source_comment_reharvest_review_queue_v1.csv", issue_fields, issues)
    inventory_fields = [
        "path", "extension", "sha256", "line_count", "has_header", "header_start", "header_end",
        "first_code", "has_usage", "usage_contract_count", "usage_complete", "owner", "command",
    ]
    inventory = [{
        "path": item.relpath, "extension": item.extension, "sha256": item.sha256,
        "line_count": str(item.line_count), "has_header": str(item.has_header),
        "header_start": str(item.header_start), "header_end": str(item.header_end),
        "first_code": str(item.first_code), "has_usage": str(item.has_usage),
        "usage_contract_count": str(len(item.usage_contracts)),
        "usage_complete": str(item.complete_usage), "owner": item.owner, "command": item.command,
    } for item in harvested]
    write_rows(output / "source_comment_reharvest_inventory_v1.csv", inventory_fields, inventory)

    previous_by_path = {
        row["RELPATH"]: row for row in read_rows(policy_source / "SRCFILE_IMPORT.csv")
    }
    current_by_path = {
        row["RELPATH"]: row for row in rows["SRCFILE_IMPORT.csv"]
    }
    delta_fields = [
        "path", "delta", "previous_fileid", "current_fileid", "previous_has_header",
        "current_has_header", "previous_header_lines", "current_header_lines", "previous_kind",
        "current_kind", "previous_owner", "current_owner", "previous_command", "current_command",
        "current_sha256", "review_disposition",
    ]
    delta_rows: list[dict[str, str]] = []
    for relpath in sorted(previous_by_path.keys() | current_by_path.keys()):
        previous = previous_by_path.get(relpath, {})
        current = current_by_path.get(relpath, {})
        if not previous:
            delta = "PATH_ADDED"
        elif not current:
            delta = "PATH_REMOVED"
        elif any(
            previous.get(field, "") != current.get(field, "")
            for field in ("HAS_HDR", "HDR_LINES", "DET_KIND", "DET_OWNER", "DET_CMD")
        ):
            delta = "COMMENT_METADATA_CHANGED"
        else:
            delta = "COMMENT_METADATA_STABLE"
        delta_rows.append({
            "path": relpath, "delta": delta,
            "previous_fileid": previous.get("FILEID", ""), "current_fileid": current.get("FILEID", ""),
            "previous_has_header": previous.get("HAS_HDR", ""), "current_has_header": current.get("HAS_HDR", ""),
            "previous_header_lines": previous.get("HDR_LINES", ""), "current_header_lines": current.get("HDR_LINES", ""),
            "previous_kind": previous.get("DET_KIND", ""), "current_kind": current.get("DET_KIND", ""),
            "previous_owner": previous.get("DET_OWNER", ""), "current_owner": current.get("DET_OWNER", ""),
            "previous_command": previous.get("DET_CMD", ""), "current_command": current.get("DET_CMD", ""),
            "current_sha256": current.get("HASH", ""),
            "review_disposition": "REVIEW" if delta != "COMMENT_METADATA_STABLE" else "SNAPSHOT_REFRESH",
        })
    delta_path = output / "source_comment_reharvest_delta_v1.csv"
    write_rows(delta_path, delta_fields, delta_rows)

    candidate_files = {}
    for path in sorted(candidate.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            count = sum(1 for _ in csv.DictReader(fh))
        candidate_files[path.name] = {"rows": count, "sha256": sha256_file(path), "bytes": path.stat().st_size}
    summary = {
        "contract": "source-comment-full-reharvest-v1",
        "candidate_only": True,
        "live_dbf_mutation": False,
        "repo_root": str(repo),
        "roots": args.roots,
        "membership": "git-ls-files" if not args.allow_untracked else "filesystem-walk",
        "extensions": sorted(extensions),
        "updated": args.updated,
        "files": len(harvested),
        "files_with_header": sum(item.has_header for item in harvested),
        "files_with_usage": sum(item.has_usage for item in harvested),
        "complete_usage_contracts": sum(
            contract.complete for item in harvested for contract in item.usage_contracts
        ),
        "incomplete_usage_contracts": sum(
            not contract.complete for item in harvested for contract in item.usage_contracts
        ),
        "issue_counts": dict(sorted(Counter(item["issue"] for item in issues).items())),
        "delta_counts": dict(sorted(Counter(item["delta"] for item in delta_rows).items())),
        "candidate_files": candidate_files,
        "inventory_sha256": sha256_file(output / "source_comment_reharvest_inventory_v1.csv"),
        "review_queue_sha256": sha256_file(output / "source_comment_reharvest_review_queue_v1.csv"),
        "delta_sha256": sha256_file(delta_path),
        "policy_source": str(policy_source),
        "policy_tables_preserved": ["SRCALIAS_IMPORT.csv", "SRCDISP_IMPORT.csv"],
    }
    (output / "source_comment_reharvest_manifest_v1.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = [
        "# Source Comment Full Reharvest v1", "",
        "Status: CANDIDATE_ONLY / NOT_LOADED", "",
        f"- Files scanned: `{summary['files']}`",
        f"- Files with leading headers: `{summary['files_with_header']}`",
        f"- Files with usage markers: `{summary['files_with_usage']}`",
        f"- Complete usage contracts: `{summary['complete_usage_contracts']}`",
        f"- Incomplete usage contracts: `{summary['incomplete_usage_contracts']}`",
        "- Live COMMENTS DBF writes: `0`", "",
        "## Candidate tables", "",
    ]
    md += [f"- `{name}`: {data['rows']} rows, `{data['sha256']}`" for name, data in sorted(candidate_files.items())]
    md += ["", "The candidate is a full replacement package and requires review plus a separately authorized DBF reload."]
    (output / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in (
        "files", "files_with_header", "files_with_usage", "complete_usage_contracts",
        "incomplete_usage_contracts", "issue_counts", "delta_counts", "candidate_files",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
