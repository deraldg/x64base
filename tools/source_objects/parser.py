from __future__ import annotations

import hashlib
import re
from pathlib import Path, PurePosixPath

from .model import ContractBlock, SourceObject, SourceSection


MARKER_RE = re.compile(
    r"^@dottalk\.(usage|location)\s+(v\d+)\s*$", re.IGNORECASE
)
END_RE = re.compile(r"^@dottalk\.(?:end|contract\.end)\s*$", re.IGNORECASE)
FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*?)\s*$")


def _normal_path(value: str) -> str:
    value = value.strip().replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value)) if value else ""


def _comment_payloads(lines: list[str]) -> tuple[list[tuple[int, str]], list[str]]:
    """Return standalone comment payloads and a per-line comment/code classification.

    Inline trailing comments remain part of the code section. This keeps the split
    lossless and avoids pretending a lightweight scanner is a language parser.
    """
    payloads: list[tuple[int, str]] = []
    classes: list[str] = []
    in_block = False
    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.lstrip()
        if in_block:
            value = stripped
            closes = "*/" in value
            if closes:
                value = value.split("*/", 1)[0]
            value = re.sub(r"^\*\s?", "", value)
            payloads.append((line_no, value.rstrip()))
            classes.append("comment")
            in_block = not closes
            continue
        if stripped.startswith("//"):
            payloads.append((line_no, re.sub(r"^//\s?", "", stripped).rstrip()))
            classes.append("comment")
            continue
        if stripped.startswith("/*"):
            value = stripped[2:]
            closes = "*/" in value
            if closes:
                value = value.split("*/", 1)[0]
            payloads.append((line_no, re.sub(r"^\*\s?", "", value).rstrip()))
            classes.append("comment")
            in_block = not closes
            continue
        classes.append("code")
    return payloads, classes


def _parse_fields(lines: list[str]) -> dict[str, str]:
    collected: dict[str, list[str]] = {}
    current = ""
    for raw in lines:
        value = raw.strip()
        if not value:
            continue
        if END_RE.match(value):
            break
        match = FIELD_RE.match(value)
        if match:
            current = match.group(1).lower().replace("_", "-")
            collected.setdefault(current, [])
            if match.group(2):
                collected[current].append(match.group(2).strip())
        elif current:
            collected[current].append(value)
    return {key: "\n".join(parts) for key, parts in collected.items()}


def _contracts(payloads: list[tuple[int, str]]) -> list[ContractBlock]:
    result: list[ContractBlock] = []
    index = 0
    while index < len(payloads):
        line_no, payload = payloads[index]
        marker = MARKER_RE.match(payload.strip())
        if not marker:
            index += 1
            continue
        kind, version = marker.group(1).lower(), marker.group(2).lower()
        raw_lines = [payload]
        end_line = line_no
        index += 1
        while index < len(payloads):
            next_line, next_payload = payloads[index]
            # A code line or a new contract terminates an unterminated block.
            if next_line != end_line + 1 or MARKER_RE.match(next_payload.strip()):
                break
            raw_lines.append(next_payload)
            end_line = next_line
            index += 1
            if END_RE.match(next_payload.strip()):
                break
        result.append(
            ContractBlock(
                kind=kind,
                version=version,
                start_line=line_no,
                end_line=end_line,
                fields=_parse_fields(raw_lines[1:]),
                raw_lines=raw_lines,
            )
        )
    return result


def _sections(lines: list[str], classes: list[str], wanted: str) -> list[SourceSection]:
    result: list[SourceSection] = []
    start: int | None = None
    buffer: list[str] = []
    for line_no, (raw, kind) in enumerate(zip(lines, classes), start=1):
        if kind == wanted:
            if start is None:
                start = line_no
            buffer.append(raw)
        elif start is not None:
            result.append(SourceSection(wanted, start, line_no - 1, "\n".join(buffer)))
            start, buffer = None, []
    if start is not None:
        result.append(SourceSection(wanted, start, len(lines), "\n".join(buffer)))
    return result


def parse_source_text(
    text: str,
    relpath: str,
    history: dict[str, str] | None = None,
) -> SourceObject:
    relpath = _normal_path(relpath)
    lines = text.splitlines()
    payloads, classes = _comment_payloads(lines)
    contracts = _contracts(payloads)
    usage = [item for item in contracts if item.kind == "usage"]
    locations = [item for item in contracts if item.kind == "location"]
    location = locations[0] if locations else None
    fields = location.fields if location else {}
    history = history or {}
    declared_home = _normal_path(fields.get("home", "")) or None
    canonical_path = _normal_path(fields.get("canonical-path", "")) or None
    actual_home = str(PurePosixPath(relpath).parent)
    if actual_home == ".":
        actual_home = ""

    findings: list[str] = []
    if len(locations) > 1:
        findings.append("MULTIPLE_LOCATION_CONTRACTS")
    if location is None:
        location_status = "UNDECLARED"
        findings.append("LOCATION_CONTRACT_MISSING")
    elif not declared_home:
        location_status = "INCOMPLETE"
        findings.append("LOCATION_HOME_MISSING")
    elif declared_home != actual_home:
        location_status = "MISMATCH"
        findings.append("DECLARED_HOME_MISMATCH")
    elif canonical_path and canonical_path != relpath:
        location_status = "MISMATCH"
        findings.append("CANONICAL_PATH_MISMATCH")
    else:
        location_status = "MATCH"

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest().upper()
    declared_id = fields.get("id", "").strip()
    source_id = declared_id or (
        "PATH-" + hashlib.sha256(relpath.encode("utf-8")).hexdigest()[:16].upper()
    )
    identity_status = "DECLARED" if declared_id else "PATH_DERIVED"
    if location and not declared_id:
        findings.append("LOCATION_ID_MISSING")

    def tracked(field: str, history_field: str) -> tuple[str | None, str]:
        if fields.get(field):
            return fields[field], "location-contract"
        if history.get(history_field):
            return history[history_field], "git-history"
        return None, "unavailable"

    author, author_source = tracked("author", "author")
    source_date, date_source = tracked("created", "created_date")
    last_modified_by, modifier_source = tracked("last-modified-by", "last_modified_by")
    last_modified_date, modified_source = tracked("last-modified", "last_modified_date")
    working_tree_state = history.get("working_tree_state", "not-checked")
    if working_tree_state == "modified":
        for key, source in (
            ("author", author_source),
            ("date", date_source),
            ("last_modified_by", modifier_source),
            ("last_modified_date", modified_source),
        ):
            if source == "git-history" and key.startswith("last_modified"):
                findings.append("UNCOMMITTED_CHANGE_AFTER_GIT_HISTORY")
                break
    return SourceObject(
        schema="dottalk.source-object/v1",
        source_id=source_id,
        identity_status=identity_status,
        path=relpath,
        extension=PurePosixPath(relpath).suffix.lower(),
        content_sha256=digest,
        line_count=len(lines),
        usage_contracts=usage,
        location_contract=location,
        declared_home=declared_home,
        actual_home=actual_home,
        canonical_path=canonical_path,
        location_status=location_status,
        project=fields.get("project") or None,
        role=fields.get("role") or None,
        date=source_date,
        author=author,
        last_modified_by=last_modified_by,
        last_modified_date=last_modified_date,
        working_tree_state=working_tree_state,
        metadata_provenance={
            "author": author_source,
            "date": date_source,
            "last_modified_by": (
                "git-history-committed-baseline"
                if working_tree_state == "modified" and modifier_source == "git-history"
                else modifier_source
            ),
            "last_modified_date": (
                "git-history-committed-baseline"
                if working_tree_state == "modified" and modified_source == "git-history"
                else modified_source
            ),
        },
        comment_sections=_sections(lines, classes, "comment"),
        code_sections=_sections(lines, classes, "code"),
        findings=findings,
    )


def parse_source_file(
    path: Path,
    repo_root: Path,
    history: dict[str, str] | None = None,
) -> SourceObject:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = data.decode("utf-8", errors="replace")
    return parse_source_text(
        text,
        path.resolve().relative_to(repo_root.resolve()).as_posix(),
        history=history,
    )
