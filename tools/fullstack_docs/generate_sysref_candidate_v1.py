#!/usr/bin/env python3
"""Build report-only SYSREF candidate rows from one immutable harvest manifest.

This is M3B of the dotref database-backed catalog lane.  It deliberately emits
CSV and JSON review artifacts only.  It does not read include/dotref.hpp, write
DBF/DTX files, generate C++, mutate HELP/META, or provide an apply mode.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MANIFEST_SCHEMA = "dottalk.sysref.harvest_manifest.v1"
POLICY_ID = "dottalk.sysref.report_only_assembly.v1"
REQUIRED_ROLES = {"SYSCMD", "SYSARGS", "SRCUSAGE", "REFVOICE"}
HARVEST_ROLES = {"SYSCMD", "SYSARGS", "SRCUSAGE", "SYSSUBCMD", "SYSFUNC", "REFALIASES"}
ALLOWED_ROLES = HARVEST_ROLES | {"REFVOICE"}
FORBIDDEN_SUFFIXES = {".dbf", ".dtx", ".fpt", ".hpp", ".h", ".inc", ".cpp"}
HEX64 = re.compile(r"^[0-9A-Fa-f]{64}$")
HEX_REV = re.compile(r"^[0-9A-Fa-f]{7,64}$")

# These statuses describe implementation/supporting-file evidence, not an
# independently published command contract. A source census legitimately
# contains both DOT|HELP (supported) and DOT|HELP_GROUPED_IMPL
# (implementation-helper), for example. Treating those as two competing HELP
# contracts makes the normalized join less accurate than its input.
AUXILIARY_USAGE_STATUSES = {
    "BACKEND-HELPER",
    "IMPLEMENTATION-HELPER",
    "IMPLEMENTATION-SHIM",
    "SUPPLEMENTAL",
}

# A contract can deliberately describe a planned or non-runtime surface. It
# remains evidence and receives a disposition, but it cannot mint a SYSCMD
# identity. Any other contract without a structural identity stays blocking.
NON_RUNTIME_DECLARATION_STATUSES = {
    "DEPRECATED",
    "DEPRECATED-COMPAT",
    "EXPERIMENTAL",
    "REJECTED",
    "REVIEW-NEEDED",
    "SAMPLE-EXTENSION",
    "STUB",
}

SYSREF_FIELDS = [
    "REF_ID", "RUN_ID", "NAMESPACE", "ENT_KIND", "CAN_NAME", "TOPICKEY",
    "VIS", "IMPLEMENT", "SUPPORTED", "ACTIVE", "DISP_ORD", "SRC_AUTH",
    "SRC_FILE", "SRC_HASH", "REVIEW_ST", "VER_AT",
]
SYSREFLINE_FIELDS = [
    "LINE_ID", "RUN_ID", "REF_ID", "LOCALE_ID", "VOICE", "KIND", "ROLE",
    "ORDINAL", "TEXT", "SRC_AUTH", "SRC_FILE", "SRC_HASH", "OVERRIDE",
    "REVIEW_ST", "ACTIVE",
]
SYSREFALIAS_FIELDS = [
    "ALIAS_ID", "RUN_ID", "REF_ID", "ALIAS", "ALIAS_KND", "DISP_STYL",
    "TARGET_ID", "SRC_AUTH", "SRC_FILE", "SRC_HASH", "ACTIVE",
]
SYSREFRUN_FIELDS = [
    "RUN_ID", "REPO_SHA", "START_UTC", "END_UTC", "COLLECTOR", "COLL_HASH",
    "POLICY_ID", "POL_HASH", "INPUT_HASH", "STATUS", "CREATED_BY", "DETAIL",
]
DISPOSITION_FIELDS = ["CAN_NAME", "CLASSIFICATION", "BLOCKING", "DETAIL", "SOURCE"]


class InputError(RuntimeError):
    """An immutable input or safety condition failed before assembly."""


@dataclass(frozen=True)
class BoundInput:
    role: str
    relative_path: str
    path: Path
    sha256: str
    producer_run_id: str


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_id(*parts: str) -> str:
    payload = "\0".join(part.strip().upper() for part in parts).encode("utf-8")
    return sha256_bytes(payload)


def canonical_row_hash(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return sha256_bytes(payload.encode("utf-8"))


def norm_identity(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def compact_identity(value: str) -> str:
    return re.sub(r"[\s_-]+", "", norm_identity(value))


def truthy(value: str) -> bool:
    return value.strip().upper() in {"1", "T", "TRUE", "Y", "YES"}


def usage_status(row: dict[str, str]) -> str:
    return row.get("STATUS", "").strip().upper()


def primary_usage_contracts(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Return command-surface contracts, excluding labeled helper evidence."""
    return [row for row in rows if usage_status(row) not in AUXILIARY_USAGE_STATUSES]


def notes_fields(value: str) -> dict[str, str]:
    """Parse the generated ``key=value ; key=value`` SYSSUBCMD notes shape."""
    fields: dict[str, str] = {}
    for part in value.split(" ; "):
        key, separator, item = part.partition("=")
        if separator and key.strip():
            fields[key.strip().lower()] = item.strip()
    return fields


def csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise InputError(f"CSV_HEADER_MISSING:{path}")
        fields = [field.strip().upper() for field in reader.fieldnames]
        rows = []
        for raw in reader:
            rows.append({(key or "").strip().upper(): (value or "") for key, value in raw.items()})
    return fields, rows


def require_columns(role: str, fields: list[str], required: set[str]) -> None:
    missing = sorted(required - set(fields))
    if missing:
        raise InputError(f"{role}_COLUMNS_MISSING:{','.join(missing)}")


def ensure_within(root: Path, path: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise InputError(f"{label}_OUTSIDE_REPO:{resolved}") from exc
    return resolved


def resolve_manifest(root: Path, manifest_path: Path) -> tuple[dict[str, Any], list[BoundInput], str]:
    manifest_path = ensure_within(root, manifest_path, "MANIFEST")
    raw = manifest_path.read_bytes()
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"MANIFEST_INVALID_JSON:{manifest_path}:{exc}") from exc

    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise InputError(f"MANIFEST_SCHEMA:{manifest.get('schema', '')}")
    for field in ("harvest_run_id", "repo_sha", "created_utc", "created_by", "collector", "inputs"):
        if not manifest.get(field):
            raise InputError(f"MANIFEST_FIELD_MISSING:{field}")
    if not HEX_REV.fullmatch(str(manifest["repo_sha"])):
        raise InputError("MANIFEST_REPO_SHA_INVALID")
    collector = manifest["collector"]
    if not isinstance(collector, dict) or not collector.get("id") or not HEX64.fullmatch(str(collector.get("sha256", ""))):
        raise InputError("MANIFEST_COLLECTOR_INVALID")
    if not isinstance(manifest["inputs"], list):
        raise InputError("MANIFEST_INPUTS_NOT_LIST")

    seen: set[str] = set()
    bound: list[BoundInput] = []
    for item in manifest["inputs"]:
        if not isinstance(item, dict):
            raise InputError("MANIFEST_INPUT_NOT_OBJECT")
        role = str(item.get("role", "")).strip().upper()
        if role not in ALLOWED_ROLES:
            raise InputError(f"MANIFEST_ROLE_UNKNOWN:{role}")
        if role in seen:
            raise InputError(f"MANIFEST_ROLE_DUPLICATE:{role}")
        seen.add(role)
        declared_hash = str(item.get("sha256", "")).strip().upper()
        if not HEX64.fullmatch(declared_hash):
            raise InputError(f"MANIFEST_HASH_INVALID:{role}")
        producer_run_id = str(item.get("producer_run_id", "")).strip()
        if not producer_run_id:
            raise InputError(f"MANIFEST_PRODUCER_RUN_MISSING:{role}")
        if role in HARVEST_ROLES and producer_run_id != manifest["harvest_run_id"]:
            raise InputError(
                f"MIXED_RUN_INPUT:{role}:{producer_run_id}!={manifest['harvest_run_id']}"
            )
        rel = str(item.get("path", "")).strip().replace("\\", "/")
        if not rel:
            raise InputError(f"MANIFEST_PATH_MISSING:{role}")
        path = ensure_within(root, root / rel, f"INPUT_{role}")
        if not path.is_file():
            raise InputError(f"INPUT_MISSING:{role}:{rel}")
        actual_hash = sha256_file(path)
        if actual_hash != declared_hash:
            raise InputError(f"INPUT_HASH_MISMATCH:{role}:{declared_hash}!={actual_hash}")
        bound.append(BoundInput(role, path.relative_to(root).as_posix(), path, actual_hash, producer_run_id))

    missing = sorted(REQUIRED_ROLES - seen)
    if missing:
        raise InputError(f"MANIFEST_ROLES_MISSING:{','.join(missing)}")
    return manifest, sorted(bound, key=lambda item: item.role), sha256_bytes(raw)


def split_memo(value: str) -> list[str]:
    return [line.strip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def row_source(row: dict[str, str], fallback: str) -> str:
    return row.get("SRC_FILE", "") or row.get("RELPATH", "") or fallback


def source_lines(
    run_id: str,
    ref_id: str,
    usage: dict[str, str],
    source_file: str,
    source_authority: str = "SRCUSAGE",
) -> list[dict[str, Any]]:
    definitions = [
        ("SUMMARY", "PRIMARY", [usage.get("SUMMARY", "").strip()]),
        ("SYNTAX", "FORM", split_memo(usage.get("USAGE", ""))),
        ("EXAMPLE", "EXAMPLE", split_memo(usage.get("EXAMPLES", ""))),
        ("NOTE", "NOTE", split_memo(usage.get("NOTES", ""))),
        ("RELATED", "RELATED", split_memo(usage.get("RELATED", ""))),
    ]
    rows: list[dict[str, Any]] = []
    for kind, role, values in definitions:
        ordinal = 0
        for value in values:
            if not value:
                continue
            ordinal += 1
            fragment_hash = sha256_bytes(value.encode("utf-8"))
            rows.append({
                "LINE_ID": stable_id(ref_id, "en-US", "NATIVE", kind, str(ordinal)),
                "RUN_ID": run_id,
                "REF_ID": ref_id,
                "LOCALE_ID": "en-US",
                "VOICE": "NATIVE",
                "KIND": kind,
                "ROLE": role,
                "ORDINAL": ordinal,
                "TEXT": value,
                "SRC_AUTH": source_authority,
                "SRC_FILE": source_file,
                "SRC_HASH": fragment_hash,
                "OVERRIDE": "F",
                "REVIEW_ST": "CANDIDATE",
                "ACTIVE": "T",
            })
    return rows


def apply_voice_overrides(
    rows: list[dict[str, Any]],
    refs_by_key: dict[tuple[str, str], dict[str, Any]],
    voice_rows: list[dict[str, str]],
    voice_source: str,
    diagnostics: list[dict[str, str]],
) -> int:
    line_by_key = {
        (
            row["REF_ID"], row["LOCALE_ID"].upper(), row["VOICE"].upper(),
            row["KIND"].upper(), int(row["ORDINAL"]),
        ): row
        for row in rows
    }
    seen_ids: set[str] = set()
    seen_targets: set[tuple[str, str, str, str, int]] = set()
    applied = 0
    for position, override in enumerate(voice_rows, start=2):
        override_id = override.get("OVR_ID", "").strip()
        if override_id in seen_ids:
            diagnostics.append({"code": "REFVOICE_DUPLICATE_ID", "detail": override_id, "blocking": "true"})
            continue
        seen_ids.add(override_id)
        if not truthy(override.get("ACTIVE", "")) or override.get("REVIEW_ST", "").strip().upper() != "APPROVED":
            continue
        if not override.get("RULING_ID", "").strip():
            diagnostics.append({"code": "REFVOICE_APPROVAL_MISSING", "detail": f"row {position}", "blocking": "true"})
            continue
        namespace = override.get("NAMESPACE", "").strip().upper()
        entity = override.get("ENT_KIND", "").strip().upper()
        can_name = norm_identity(override.get("CAN_NAME", ""))
        ref = refs_by_key.get((entity, can_name))
        if namespace != "DOT" or ref is None:
            diagnostics.append({"code": "REFVOICE_TARGET_UNRESOLVED", "detail": f"row {position}:{namespace}:{entity}:{can_name}", "blocking": "true"})
            continue
        try:
            ordinal = int(override.get("ORDINAL", ""))
        except ValueError:
            diagnostics.append({"code": "REFVOICE_ORDINAL_INVALID", "detail": f"row {position}", "blocking": "true"})
            continue
        target_key = (
            ref["REF_ID"], override.get("LOCALE_ID", "").strip().upper(),
            override.get("VOICE", "").strip().upper(), override.get("KIND", "").strip().upper(), ordinal,
        )
        if target_key in seen_targets:
            diagnostics.append({"code": "REFVOICE_TARGET_DUPLICATE", "detail": f"row {position}", "blocking": "true"})
            continue
        seen_targets.add(target_key)
        target = line_by_key.get(target_key)
        if target is None:
            diagnostics.append({"code": "REFVOICE_LINE_UNRESOLVED", "detail": f"row {position}", "blocking": "true"})
            continue
        reviewed_hash = override.get("SRC_HASH", "").strip().upper()
        if reviewed_hash != target["SRC_HASH"]:
            diagnostics.append({"code": "REFVOICE_SOURCE_STALE", "detail": f"row {position}:{reviewed_hash}!={target['SRC_HASH']}", "blocking": "true"})
            continue
        replacement = override.get("TEXT", "")
        if not replacement.strip():
            diagnostics.append({"code": "REFVOICE_TEXT_EMPTY", "detail": f"row {position}", "blocking": "true"})
            continue
        target["TEXT"] = replacement
        target["SRC_AUTH"] = "REFVOICE"
        target["SRC_FILE"] = voice_source
        target["SRC_HASH"] = sha256_bytes(replacement.encode("utf-8"))
        target["OVERRIDE"] = "T"
        target["REVIEW_ST"] = "APPROVED_OVERRIDE"
        applied += 1
    return applied


def assemble(
    root: Path,
    run_id: str,
    namespace: str,
    manifest: dict[str, Any],
    inputs: list[BoundInput],
    manifest_hash: str,
    schema_path: Path,
    tool_path: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    by_role = {item.role: item for item in inputs}
    syscmd_fields, syscmd_rows = csv_rows(by_role["SYSCMD"].path)
    sysargs_fields, sysargs_rows = csv_rows(by_role["SYSARGS"].path)
    usage_fields, usage_rows = csv_rows(by_role["SRCUSAGE"].path)
    voice_fields, voice_rows = csv_rows(by_role["REFVOICE"].path)
    require_columns("SYSCMD", syscmd_fields, {"CAN_NAME", "TYPE", "VIS", "HANDLER", "ACTIVE"})
    require_columns("SYSARGS", sysargs_fields, {"OWNER_NAM", "ARG_NAME", "ACTIVE", "SRC_AUTH", "SRC_FILE"})
    require_columns("SRCUSAGE", usage_fields, {"COMMAND", "STATUS", "SUMMARY", "USAGE"})
    require_columns("REFVOICE", voice_fields, {
        "OVR_ID", "NAMESPACE", "ENT_KIND", "CAN_NAME", "LOCALE_ID", "VOICE",
        "KIND", "ORDINAL", "TEXT", "RATIONALE", "OWNER", "RULING_ID",
        "REVIEW_ST", "SRC_HASH", "ACTIVE", "VER_AT",
    })

    diagnostics: list[dict[str, str]] = []
    dispositions: list[dict[str, str]] = []
    cmd_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    usage_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in syscmd_rows:
        cmd_groups[norm_identity(row.get("CAN_NAME", ""))].append(row)
    for row in usage_rows:
        usage_groups[norm_identity(row.get("COMMAND", ""))].append(row)

    active_command_args = [
        row for row in sysargs_rows
        if truthy(row.get("ACTIVE", ""))
        and row.get("OWNER_KND", "COMMAND").strip().upper() in {"COMMAND", "CMD"}
    ]

    subusage_by_compact: dict[str, list[dict[str, str]]] = defaultdict(list)
    if "SYSSUBCMD" in by_role:
        sub_fields, sub_rows = csv_rows(by_role["SYSSUBCMD"].path)
        require_columns("SYSSUBCMD", sub_fields, {
            "QUAL_NAME", "IMPL_STAT", "VIS_TIER", "SRC_AUTH", "SRC_FILE",
            "HANDLER", "ACTIVE", "NOTES",
        })
        for row in sub_rows:
            if truthy(row.get("ACTIVE", "")):
                subusage_by_compact[compact_identity(row.get("QUAL_NAME", ""))].append(row)

    duplicates = {name for name, group in cmd_groups.items() if not name or len(group) != 1}
    for name in sorted(duplicates):
        diagnostics.append({"code": "SYSCMD_IDENTITY_INVALID", "detail": f"{name or '<blank>'}:{len(cmd_groups[name])}", "blocking": "true"})

    refs: list[dict[str, Any]] = []
    lines: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    refs_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    display_order = 0
    for can_name in sorted(cmd_groups):
        if can_name in duplicates:
            dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "DUPLICATE_STRUCTURAL_IDENTITY", "BLOCKING": "T", "DETAIL": "SYSCMD identity is not unique", "SOURCE": by_role["SYSCMD"].relative_path})
            continue
        cmd = cmd_groups[can_name][0]
        implemented = truthy(cmd.get("ACTIVE", ""))
        all_contracts = usage_groups.get(can_name, [])
        contracts = primary_usage_contracts(all_contracts)
        semantic_authority = "SRCUSAGE"
        semantic_source = by_role["SRCUSAGE"].relative_path
        semantic_classification = "DIRECT_USAGE_CONTRACT"
        auxiliary_count = len(all_contracts) - len(contracts)
        if auxiliary_count:
            dispositions.append({
                "CAN_NAME": can_name,
                "CLASSIFICATION": "AUXILIARY_USAGE_IGNORED",
                "BLOCKING": "F",
                "DETAIL": f"{auxiliary_count} explicitly auxiliary source contract(s)",
                "SOURCE": by_role["SRCUSAGE"].relative_path,
            })
        if len(contracts) > 1:
            diagnostics.append({"code": "SRCUSAGE_DUPLICATE_COMMAND", "detail": f"{can_name}:{len(contracts)}", "blocking": "true"})
            dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "DUPLICATE_USAGE_CONTRACT", "BLOCKING": "T", "DETAIL": "SRCUSAGE command is not unique", "SOURCE": by_role["SRCUSAGE"].relative_path})
            continue

        if not contracts and subusage_by_compact:
            sub_matches = subusage_by_compact.get(compact_identity(can_name), [])
            if len(sub_matches) > 1:
                diagnostics.append({"code": "SYSSUBCMD_IDENTITY_AMBIGUOUS", "detail": f"{can_name}:{len(sub_matches)}", "blocking": "true"})
                dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "AMBIGUOUS_SUBCOMMAND_CONTRACT", "BLOCKING": "T", "DETAIL": "Compact command identity resolves to multiple SYSSUBCMD rows", "SOURCE": by_role["SYSSUBCMD"].relative_path})
                continue
            if sub_matches:
                sub = sub_matches[0]
                fields = notes_fields(sub.get("NOTES", ""))
                contracts = [{
                    "STATUS": "SUPPORTED" if sub.get("IMPL_STAT", "").strip().upper() == "IMPLEMENTED" else sub.get("IMPL_STAT", ""),
                    "SUMMARY": fields.get("summary", ""),
                    "USAGE": fields.get("syntax", "").replace(" | ", "\n"),
                    "EXAMPLES": "",
                    "NOTES": "",
                    "RELATED": "",
                    "SRC_FILE": sub.get("SRC_FILE", ""),
                }]
                semantic_authority = "SYSSUBCMD"
                semantic_source = by_role["SYSSUBCMD"].relative_path
                semantic_classification = "SUBCOMMAND_CONTRACT"

        if not contracts and cmd.get("TYPE", "").strip().lower() == "syntax-command":
            owners = {
                norm_identity(row.get("OWNER_NAM", ""))
                for row in active_command_args
                if row.get("ARG_KIND", "").strip().lower() == "keyword"
                and norm_identity(row.get("ARG_NAME", "")) == can_name
            }
            owner_contracts = [
                (owner, primary_usage_contracts(usage_groups.get(owner, [])))
                for owner in sorted(owners)
            ]
            owner_contracts = [(owner, rows) for owner, rows in owner_contracts if len(rows) == 1]
            if len(owner_contracts) == 1:
                owner, rows = owner_contracts[0]
                contracts = rows
                semantic_authority = "SRCUSAGE_VIA_SYSARGS"
                semantic_classification = f"SYNTAX_COMMAND_OF_{owner}"

        if not contracts:
            handler = cmd.get("HANDLER", "").strip()
            routed: list[tuple[str, dict[str, str]]] = []
            if handler:
                for sibling_name, sibling_rows in cmd_groups.items():
                    if sibling_name == can_name or len(sibling_rows) != 1:
                        continue
                    sibling = sibling_rows[0]
                    sibling_contracts = primary_usage_contracts(usage_groups.get(sibling_name, []))
                    if sibling.get("HANDLER", "").strip() != handler or len(sibling_contracts) != 1:
                        continue
                    has_syntax_evidence = any(
                        norm_identity(arg.get("OWNER_NAM", "")) == sibling_name
                        and norm_identity(arg.get("ARG_NAME", "")) == can_name
                        for arg in active_command_args
                    )
                    if has_syntax_evidence:
                        routed.append((sibling_name, sibling_contracts[0]))
            if len(routed) == 1:
                owner, contract = routed[0]
                contracts = [contract]
                semantic_authority = "SRCUSAGE_ROUTED_ALIAS"
                semantic_classification = f"ROUTED_ALIAS_OF_{owner}"
            elif len(routed) > 1:
                diagnostics.append({"code": "ROUTED_ALIAS_AMBIGUOUS", "detail": f"{can_name}:{','.join(owner for owner, _ in routed)}", "blocking": "true"})
                dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "AMBIGUOUS_ROUTED_ALIAS", "BLOCKING": "T", "DETAIL": "Handler and syntax evidence resolve to multiple owners", "SOURCE": by_role["SYSCMD"].relative_path})
                continue

        if implemented and not contracts:
            diagnostics.append({"code": "MISSING_USAGE_CONTRACT", "detail": can_name, "blocking": "true"})
            dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "IMPLEMENTED_MISSING_USAGE", "BLOCKING": "T", "DETAIL": "Implemented identity lacks SRCUSAGE", "SOURCE": by_role["SYSCMD"].relative_path})
            continue

        contract = contracts[0] if contracts else {}
        summary = contract.get("SUMMARY", "").strip()
        syntax = split_memo(contract.get("USAGE", ""))
        if implemented and (not summary or not syntax):
            missing_parts = ",".join(part for part, present in (("SUMMARY", bool(summary)), ("SYNTAX", bool(syntax))) if not present)
            diagnostics.append({"code": "REQUIRED_PROSE_MISSING", "detail": f"{can_name}:{missing_parts}", "blocking": "true"})
            dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "REQUIRED_PROSE_MISSING", "BLOCKING": "T", "DETAIL": missing_parts, "SOURCE": by_role["SRCUSAGE"].relative_path})
            continue

        display_order += 1
        entity_kind = "COMMAND"
        ref_id = stable_id(namespace, entity_kind, can_name)
        source_file = row_source(cmd, by_role["SYSCMD"].relative_path)
        ref = {
            "REF_ID": ref_id,
            "RUN_ID": run_id,
            "NAMESPACE": namespace,
            "ENT_KIND": entity_kind,
            "CAN_NAME": can_name,
            "TOPICKEY": f"{namespace}|{can_name}",
            "VIS": cmd.get("VIS", "").strip().lower(),
            "IMPLEMENT": "T" if implemented else "F",
            "SUPPORTED": "T" if contract.get("STATUS", "").strip().upper() == "SUPPORTED" else "F",
            "ACTIVE": "T" if implemented else "F",
            "DISP_ORD": display_order,
            "SRC_AUTH": "SYSCMD",
            "SRC_FILE": source_file,
            "SRC_HASH": canonical_row_hash(cmd),
            "REVIEW_ST": "CANDIDATE" if implemented else "INACTIVE_SOURCE",
            "VER_AT": manifest["created_utc"],
        }
        refs.append(ref)
        refs_by_key[(entity_kind, can_name)] = ref
        if contract:
            lines.extend(source_lines(
                run_id,
                ref_id,
                contract,
                row_source(contract, semantic_source),
                semantic_authority,
            ))
        dispositions.append({"CAN_NAME": can_name, "CLASSIFICATION": "ASSEMBLED", "BLOCKING": "F", "DETAIL": f"implemented={implemented};supported={ref['SUPPORTED'] == 'T'};semantic={semantic_classification}", "SOURCE": source_file})

    known_commands = set(cmd_groups)
    for owner in sorted({norm_identity(row.get("OWNER_NAM", "")) for row in active_command_args}):
        if owner and owner not in known_commands:
            diagnostics.append({"code": "SYSARGS_ORPHAN_OWNER", "detail": owner, "blocking": "true"})
    for usage_name in sorted(set(usage_groups) - known_commands):
        if not usage_name:
            continue
        rows = usage_groups[usage_name]
        contracts = primary_usage_contracts(rows)
        if not contracts:
            dispositions.append({
                "CAN_NAME": usage_name,
                "CLASSIFICATION": "AUXILIARY_USAGE_WITHOUT_STRUCTURAL_IDENTITY",
                "BLOCKING": "F",
                "DETAIL": "Helper/supplemental prose cannot mint an identity",
                "SOURCE": by_role["SRCUSAGE"].relative_path,
            })
            continue
        statuses = {usage_status(row) for row in contracts}
        if statuses and statuses <= NON_RUNTIME_DECLARATION_STATUSES:
            dispositions.append({
                "CAN_NAME": usage_name,
                "CLASSIFICATION": "DECLARED_WITHOUT_RUNTIME_IDENTITY",
                "BLOCKING": "F",
                "DETAIL": "Non-runtime declaration excluded; prose cannot mint an identity",
                "SOURCE": by_role["SRCUSAGE"].relative_path,
            })
            continue
        diagnostics.append({"code": "SRCUSAGE_UNRESOLVED_IDENTITY", "detail": usage_name, "blocking": "true"})
        dispositions.append({"CAN_NAME": usage_name, "CLASSIFICATION": "USAGE_WITHOUT_STRUCTURAL_IDENTITY", "BLOCKING": "T", "DETAIL": "Prose cannot mint an identity", "SOURCE": by_role["SRCUSAGE"].relative_path})

    if "REFALIASES" in by_role:
        alias_fields, alias_rows = csv_rows(by_role["REFALIASES"].path)
        require_columns("REFALIASES", alias_fields, {"CAN_NAME", "ALIAS", "ALIAS_KND", "DISP_STYL", "SRC_AUTH", "SRC_FILE", "ACTIVE"})
        alias_keys: set[tuple[str, str, str]] = set()
        for position, row in enumerate(alias_rows, start=2):
            if not truthy(row.get("ACTIVE", "")):
                continue
            can_name = norm_identity(row.get("CAN_NAME", ""))
            ref = refs_by_key.get(("COMMAND", can_name))
            alias = norm_identity(row.get("ALIAS", ""))
            alias_kind = row.get("ALIAS_KND", "").strip().lower()
            key = (can_name, alias, alias_kind)
            if ref is None or not alias or key in alias_keys:
                diagnostics.append({"code": "REFALIAS_INVALID", "detail": f"row {position}:{key}", "blocking": "true"})
                continue
            alias_keys.add(key)
            aliases.append({
                "ALIAS_ID": stable_id(ref["REF_ID"], alias, alias_kind),
                "RUN_ID": run_id,
                "REF_ID": ref["REF_ID"],
                "ALIAS": alias,
                "ALIAS_KND": alias_kind,
                "DISP_STYL": row.get("DISP_STYL", "").strip().lower(),
                "TARGET_ID": ref["REF_ID"],
                "SRC_AUTH": row.get("SRC_AUTH", "").strip(),
                "SRC_FILE": row_source(row, by_role["REFALIASES"].relative_path),
                "SRC_HASH": canonical_row_hash(row),
                "ACTIVE": "T",
            })

    overrides_applied = apply_voice_overrides(
        lines, refs_by_key, voice_rows, by_role["REFVOICE"].relative_path, diagnostics
    )
    blocking = [item for item in diagnostics if item["blocking"] == "true"]
    status = "BLOCKED" if blocking else "CANDIDATE"
    policy_hash = sha256_bytes((sha256_file(tool_path) + sha256_file(schema_path)).encode("ascii"))
    detail = {
        "assembled_identities": len(refs),
        "assembled_lines": len(lines),
        "assembled_aliases": len(aliases),
        "blocked_findings": len(blocking),
        "overrides_applied": overrides_applied,
    }
    run_row = {
        "RUN_ID": run_id,
        "REPO_SHA": manifest["repo_sha"].upper(),
        "START_UTC": manifest["created_utc"],
        "END_UTC": manifest["created_utc"],
        "COLLECTOR": manifest["collector"]["id"],
        "COLL_HASH": manifest["collector"]["sha256"].upper(),
        "POLICY_ID": POLICY_ID,
        "POL_HASH": policy_hash,
        "INPUT_HASH": manifest_hash,
        "STATUS": status,
        "CREATED_BY": manifest["created_by"],
        "DETAIL": json.dumps(detail, sort_keys=True, separators=(",", ":")),
    }
    report = {
        "schema": "dottalk.sysref.authority_join_report.v1",
        "mode": "REPORT_ONLY",
        "run_id": run_id,
        "namespace": namespace,
        "status": status,
        "counts": detail,
        "diagnostics": sorted(diagnostics, key=lambda row: (row["code"], row["detail"])),
        "support_policy": "SUPPORTED iff SRCUSAGE.STATUS equals SUPPORTED; never inferred from implementation",
        "identity_policy": "SYSCMD mints command identities; prose never mints identities",
        "legacy_header_read": False,
    }
    artifacts = {
        "sysrefrun": [run_row],
        "sysref": sorted(refs, key=lambda row: (row["NAMESPACE"], row["CAN_NAME"])),
        "sysrefline": sorted(lines, key=lambda row: (row["REF_ID"], row["LOCALE_ID"], row["VOICE"], row["KIND"], int(row["ORDINAL"]))),
        "sysrefalias": sorted(aliases, key=lambda row: (row["REF_ID"], row["ALIAS"], row["ALIAS_KND"])),
        "dispositions": sorted(dispositions, key=lambda row: (row["CAN_NAME"], row["CLASSIFICATION"])),
    }
    return artifacts, report


def emit(
    out: Path,
    artifacts: dict[str, list[dict[str, Any]]],
    report: dict[str, Any],
    manifest: dict[str, Any],
    inputs: list[BoundInput],
    manifest_hash: str,
) -> None:
    out.mkdir(parents=True, exist_ok=False)
    write_csv(out / "candidate/sysrefrun_candidate.csv", SYSREFRUN_FIELDS, artifacts["sysrefrun"])
    write_csv(out / "candidate/sysref_candidate.csv", SYSREF_FIELDS, artifacts["sysref"])
    write_csv(out / "candidate/sysrefline_candidate.csv", SYSREFLINE_FIELDS, artifacts["sysrefline"])
    write_csv(out / "candidate/sysrefalias_candidate.csv", SYSREFALIAS_FIELDS, artifacts["sysrefalias"])
    write_csv(out / "reports/dispositions.csv", DISPOSITION_FIELDS, artifacts["dispositions"])
    write_json(out / "reports/authority_join_report.json", report)
    write_json(out / "reports/input_manifest.json", {
        "schema": MANIFEST_SCHEMA,
        "manifest_sha256": manifest_hash,
        "harvest_run_id": manifest["harvest_run_id"],
        "repo_sha": manifest["repo_sha"].upper(),
        "created_utc": manifest["created_utc"],
        "collector": manifest["collector"],
        "inputs": [
            {"role": item.role, "path": item.relative_path, "sha256": item.sha256, "producer_run_id": item.producer_run_id}
            for item in inputs
        ],
    })
    write_json(out / "reports/gate_results.json", {
        "schema": "dottalk.sysref.m3b_gate_results.v1",
        "run_id": report["run_id"],
        "mode": "REPORT_ONLY",
        "gates": {
            "G0_IMMUTABLE_INPUT_PACKAGE": "PASS",
            "G1_SCHEMA_AND_KEY_INTEGRITY": "PASS" if report["status"] == "CANDIDATE" else "BLOCKED",
            "G2_AUTHORITY_RESOLUTION": "PASS" if report["status"] == "CANDIDATE" else "BLOCKED",
            "G3_TO_G9": "NOT_RUN_IN_M3B",
        },
        "live_mutation": False,
    })
    forbidden = [path for path in out.rglob("*") if path.is_file() and path.suffix.lower() in FORBIDDEN_SUFFIXES]
    if forbidden:
        raise RuntimeError(f"REPORT_ONLY_FORBIDDEN_OUTPUT:{','.join(str(path) for path in forbidden)}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble hash-bound report-only SYSREF candidate rows.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--harvest-manifest", type=Path, required=True)
    parser.add_argument("--voice-catalog", type=Path, required=True)
    parser.add_argument("--namespace", default="DOT", choices=["DOT"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report-only", action="store_true", default=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    try:
        out = ensure_within(root, args.out if args.out.is_absolute() else root / args.out, "OUTPUT")
        if out.exists():
            raise InputError(f"OUTPUT_ALREADY_EXISTS:{out}")
        manifest_path = args.harvest_manifest if args.harvest_manifest.is_absolute() else root / args.harvest_manifest
        voice_path = ensure_within(root, args.voice_catalog if args.voice_catalog.is_absolute() else root / args.voice_catalog, "VOICE_CATALOG")
        schema_path = root / "dottalkpp/data/schemas/metadata/sysref_catalog.dtschema"
        manifest, inputs, manifest_hash = resolve_manifest(root, manifest_path)
        voice_input = next(item for item in inputs if item.role == "REFVOICE")
        if voice_input.path != voice_path:
            raise InputError(f"VOICE_CATALOG_MANIFEST_MISMATCH:{voice_path}!={voice_input.path}")
        artifacts, report = assemble(
            root, args.run_id, args.namespace, manifest, inputs, manifest_hash,
            schema_path, Path(__file__).resolve(),
        )
        emit(out, artifacts, report, manifest, inputs, manifest_hash)
    except (InputError, OSError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(f"SYSREF M3B: {report['status']} -- {report['counts']['assembled_identities']} assembled, "
          f"{report['counts']['blocked_findings']} blocking finding(s)")
    print(f"REPORT-ONLY: {out}")
    return 0 if report["status"] == "CANDIDATE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
