#!/usr/bin/env python3
"""Emit the hash-bound, report-only DOTREF M3D candidate package.

This tool has no apply mode. It refuses an unapproved gate, a changed live
header, an unknown support status, an unresolved scope member, or an existing
output directory. It emits CSV inputs, a generated C++ row include, reports,
and a DotTalk++ CREATE X64/IMPORT script for an isolated candidate directory.
It never writes include/dotref.hpp or a live HELP/META store.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "dottalk.dotref.m3d_candidate.v1"
APPROVED_GATE_SHA256 = "DEEC42244DC5FC2A193F8E53F5348750DBAB86234458F5DC4A06C26FC2C9035B"
APPROVED_HEADER_SHA256 = "F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5"
RUN_ID = "DOCFLUSH-20261013-002"
VERIFIED_AT = "2026-10-13T00:00:00Z"

AUXILIARY_STATUSES = {
    "implementation-helper", "implementation-shim", "backend-helper", "supplemental"
}

SYSREF_FIELDS = [
    "REF_ID", "RUN_ID", "NAMESPACE", "ENT_KIND", "CAN_NAME", "TOPICKEY",
    "VIS", "IMPLEMENT", "SUPPORTED", "SUPPORT_ST", "MATURITY", "AUDIENCE",
    "ACTIVE", "DISP_ORD", "SRC_AUTH", "SRC_FILE", "SRC_HASH", "REVIEW_ST",
    "VER_AT",
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
REFVOICE_FIELDS = [
    "OVR_ID", "NAMESPACE", "ENT_KIND", "CAN_NAME", "LOCALE_ID", "VOICE",
    "KIND", "ORDINAL", "TEXT", "RATIONALE", "OWNER", "RULING_ID",
    "REVIEW_ST", "SRC_HASH", "ACTIVE", "VER_AT",
]
DOTREF_FIELDS = [
    "REF_ID", "RUN_ID", "NAME", "SYNTAX", "SUMMARY", "SUPPORTED", "SRC_HASH",
    "REVIEW_ST", "ACTIVE",
]
SYSREFRUN_FIELDS = [
    "RUN_ID", "REPO_SHA", "START_UTC", "END_UTC", "COLLECTOR", "COLL_HASH",
    "POLICY_ID", "POL_HASH", "INPUT_HASH", "STATUS", "CREATED_BY", "DETAIL",
]


class EmissionError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    return sha256_bytes(json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8"))


def stable_id(*parts: str) -> str:
    return sha256_bytes("\0".join(part.strip().upper() for part in parts).encode("utf-8"))


def truth(value: str) -> bool:
    return value.strip().upper() in {"T", "TRUE", "1", "YES"}


def tf(value: bool) -> str:
    return "T" if value else "F"


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{(key or "").strip().upper(): (value or "")
                 for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8", newline="\n",
    )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise EmissionError(f"MODULE_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def require_file(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise EmissionError(f"PATH_OUTSIDE_REPOSITORY:{path}") from exc
    if not path.is_file():
        raise EmissionError(f"INPUT_MISSING:{path}")
    return path


def load_support_policy(path: Path) -> dict[str, dict[str, str]]:
    policy: dict[str, dict[str, str]] = {}
    for row in read_csv(path):
        status = row.get("STATUS", "").strip().lower()
        if not status or status in policy:
            raise EmissionError(f"INVALID_OR_DUPLICATE_SUPPORT_STATUS:{status}")
        if row.get("REVIEW_ST", "").upper() != "APPROVED" or not truth(row.get("ACTIVE", "")):
            raise EmissionError(f"SUPPORT_STATUS_NOT_APPROVED:{status}")
        policy[status] = row
    return policy


def primary_contract_statuses(inventory_path: Path) -> tuple[dict[str, str], list[dict[str, str]]]:
    payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for contract in payload.get("contracts", []):
        command = norm(str(contract.get("command", "")))
        if command:
            grouped[command].append(contract)

    statuses: dict[str, str] = {}
    audit: list[dict[str, str]] = []
    for command, rows in sorted(grouped.items()):
        usable = [row for row in rows
                  if str(row.get("status", "")).strip().lower() not in AUXILIARY_STATUSES]
        nonempty = {str(row.get("status", "")).strip().lower() for row in usable
                    if str(row.get("status", "")).strip()}
        if len(nonempty) > 1:
            raise EmissionError(f"CONFLICTING_PRIMARY_CONTRACT_STATUS:{command}:{sorted(nonempty)}")
        if nonempty:
            statuses[command] = next(iter(nonempty))
        for row in rows:
            status = str(row.get("status", "")).strip().lower()
            audit.append({
                "CAN_NAME": command,
                "STATUS": status,
                "SOURCE": str(row.get("file", "")),
                "DISPOSITION": "AUXILIARY_IGNORED" if status in AUXILIARY_STATUSES else "PRIMARY_CONSIDERED",
            })
    return statuses, audit


def cpp_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "\\r").replace("\n", "\\n") + '"'


def render_cpp_rows(rows: list[dict[str, str]]) -> str:
    lines = [
        "// Generated report-only M3D DOTREF candidate rows.",
        "// Do not include or apply without separate M3E authorization.",
        f"// run: {RUN_ID}",
        "",
    ]
    for row in rows:
        lines.append(
            "        {" + ", ".join([
                cpp_string(row["NAME"]), cpp_string(row["SYNTAX"]),
                cpp_string(row["SUMMARY"]), "true" if truth(row["SUPPORTED"]) else "false",
            ]) + "},"
        )
    return "\n".join(lines) + "\n"


def parse_generated_rows(parser_module: Any, generated: str) -> list[Any]:
    blob = generated.split("\n\n", 1)[-1]
    return [parser_module._parse_entry(entry) for entry in parser_module._iter_entries(blob)]


def choose_support(
    scope: dict[str, str], base: dict[str, str] | None,
    contract_status: dict[str, str], policy: dict[str, dict[str, str]],
) -> tuple[str, dict[str, str], str]:
    kind = scope["ENT_KIND"].upper()
    target = norm(scope["TARGET_NAME"])
    if kind == "ALIAS":
        status = "compatibility-alias"
        authority = "APPROVED_ALIAS_POLICY"
    elif kind == "FUNCTION":
        status = "implementation-present"
        authority = "IMPLEMENTED_EXTENSION_FUNCTION"
    elif target in contract_status:
        status = contract_status[target]
        authority = "PRIMARY_SOURCE_CONTRACT"
    elif base is not None:
        status = "supported" if truth(base.get("SUPPORTED", "")) else "review-needed"
        authority = "M3B_SOURCE_RESOLUTION_NO_DIRECT_CONTRACT"
    else:
        raise EmissionError(f"SUPPORT_SOURCE_UNRESOLVED:{scope['NAME']}")
    if status not in policy:
        raise EmissionError(f"UNKNOWN_SUPPORT_STATUS:{scope['NAME']}:{status}")
    return status, policy[status], authority


def dbf_create_specs() -> dict[str, str]:
    return {
        "SYSREFRUN": "RUN_ID C(48), REPO_SHA C(64), START_UTC C(32), END_UTC C(32), COLLECTOR C(64), COLL_HASH C(64), POLICY_ID C(64), POL_HASH C(64), INPUT_HASH C(64), STATUS C(24), CREATED_BY C(64), DETAIL M",
        "SYSREF": "REF_ID C(64), RUN_ID C(48), NAMESPACE C(16), ENT_KIND C(16), CAN_NAME C(80), TOPICKEY C(96), VIS C(20), IMPLEMENT L, SUPPORTED L, SUPPORT_ST C(32), MATURITY C(24), AUDIENCE C(24), ACTIVE L, DISP_ORD N(10,0), SRC_AUTH C(32), SRC_FILE C(180), SRC_HASH C(64), REVIEW_ST C(24), VER_AT C(32)",
        "SYSREFLINE": "LINE_ID C(64), RUN_ID C(48), REF_ID C(64), LOCALE_ID C(16), VOICE C(16), KIND C(32), ROLE C(32), ORDINAL N(6,0), TEXT M, SRC_AUTH C(32), SRC_FILE C(180), SRC_HASH C(64), OVERRIDE L, REVIEW_ST C(24), ACTIVE L",
        "SYSREFALIAS": "ALIAS_ID C(64), RUN_ID C(48), REF_ID C(64), ALIAS C(80), ALIAS_KND C(24), DISP_STYL C(24), TARGET_ID C(64), SRC_AUTH C(32), SRC_FILE C(180), SRC_HASH C(64), ACTIVE L",
        "REFVOICE": "OVR_ID C(64), NAMESPACE C(16), ENT_KIND C(16), CAN_NAME C(80), LOCALE_ID C(16), VOICE C(16), KIND C(32), ORDINAL N(6,0), TEXT M, RATIONALE M, OWNER C(64), RULING_ID C(64), REVIEW_ST C(24), SRC_HASH C(64), ACTIVE L, VER_AT C(32)",
        "REFSUPPORT": "STATUS C(32), SUPPORTED L, MATURITY C(24), AUDIENCE C(24), RATIONALE M, OWNER C(64), RULING_ID C(64), REVIEW_ST C(24), ACTIVE L, VER_AT C(32)",
        "DOTREF": "REF_ID C(64), RUN_ID C(48), NAME C(80), SYNTAX M, SUMMARY M, SUPPORTED L, SRC_HASH C(64), REVIEW_ST C(24), ACTIVE L",
    }


def emit_runtime_script(out: Path, csv_paths: dict[str, Path]) -> Path:
    dbf_dir = (out / "candidate/dbf").resolve()
    lines = [
        "* Report-only M3D candidate load. No live metadata path is used.",
        f"setpath dbf {dbf_dir}",
        "",
    ]
    for table, spec in dbf_create_specs().items():
        lines.extend([
            f"CREATE X64 {table} ({spec})",
            f"IMPORT {csv_paths[table].resolve()}",
            "COUNT",
            "CLOSE",
            "",
        ])
    lines.append("QUIT")
    script = out / "candidate/load_m3d_candidate.dts"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return script


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--gate", required=True)
    ap.add_argument("--approval-record", required=True)
    ap.add_argument("--header", default="include/dotref.hpp")
    ap.add_argument("--fox-header", default="include/foxref.hpp")
    ap.add_argument("--closure", required=True)
    ap.add_argument("--assembly", required=True)
    ap.add_argument("--contract-inventory", required=True)
    ap.add_argument("--support-policy", required=True)
    ap.add_argument("--schema-contract", required=True)
    ap.add_argument("--repo-sha", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    out = (root / args.out).resolve()
    try:
        out.relative_to(root)
        if not args.report_only:
            raise EmissionError("REPORT_ONLY_FLAG_REQUIRED")
        if out.exists():
            raise EmissionError(f"OUTPUT_ALREADY_EXISTS:{out}")

        gate = require_file(root, args.gate)
        approval = require_file(root, args.approval_record)
        header = require_file(root, args.header)
        fox_header = require_file(root, args.fox_header)
        inventory = require_file(root, args.contract_inventory)
        support_path = require_file(root, args.support_policy)
        schema_path = require_file(root, args.schema_contract)
        closure = (root / args.closure).resolve()
        assembly = (root / args.assembly).resolve()
        for directory in (closure, assembly):
            directory.relative_to(root)
            if not directory.is_dir():
                raise EmissionError(f"INPUT_DIRECTORY_MISSING:{directory}")

        if sha256_file(gate) != APPROVED_GATE_SHA256:
            raise EmissionError("APPROVED_GATE_HASH_MISMATCH")
        if APPROVED_GATE_SHA256 not in approval.read_text(encoding="utf-8"):
            raise EmissionError("APPROVAL_RECORD_DOES_NOT_BIND_GATE")
        if sha256_file(header) != APPROVED_HEADER_SHA256:
            raise EmissionError("MIGRATION_HEADER_HASH_MISMATCH")

        scope_path = closure / "candidate/refscope_candidate.csv"
        aliases_path = closure / "candidate/refaliases_candidate.csv"
        proposed_voice_path = closure / "candidate/refvoice_proposed.csv"
        closure_summary_path = closure / "reports/closure_summary.json"
        base_ref_path = assembly / "candidate/sysref_candidate.csv"
        base_lines_path = assembly / "candidate/sysrefline_candidate.csv"
        base_run_path = assembly / "candidate/sysrefrun_candidate.csv"
        for path in (scope_path, aliases_path, proposed_voice_path, closure_summary_path,
                     base_ref_path, base_lines_path, base_run_path):
            if not path.is_file():
                raise EmissionError(f"INPUT_MISSING:{path}")

        scope = read_csv(scope_path)
        alias_input = read_csv(aliases_path)
        proposed_voice = read_csv(proposed_voice_path)
        base_refs = read_csv(base_ref_path)
        base_lines = read_csv(base_lines_path)
        base_runs = read_csv(base_run_path)
        if len(scope) != 268 or len(alias_input) != 23 or len(proposed_voice) != 536:
            raise EmissionError(
                f"APPROVED_COUNT_MISMATCH:scope={len(scope)} aliases={len(alias_input)} voice={len(proposed_voice)}"
            )
        if len({row["NAME"] for row in scope}) != len(scope):
            raise EmissionError("DUPLICATE_SCOPE_NAME")
        if len(base_runs) != 1 or base_runs[0].get("RUN_ID") != RUN_ID:
            raise EmissionError("ASSEMBLY_RUN_MISMATCH")

        parser_module = load_module(
            "dotref_metadata_parser_for_m3d_v1",
            root / "dottalkpp/tools/help/generate_dotref_from_metadata_v1.py",
        )
        _prefix, header_items, _suffix = parser_module.parse_header(header.read_text(encoding="utf-8"))
        if [norm(item.name) for item in header_items] != [norm(row["NAME"]) for row in scope]:
            raise EmissionError("SCOPE_ORDER_OR_MEMBERSHIP_DIFFERS_FROM_APPROVED_HEADER")

        voice_by_key: dict[tuple[str, str], dict[str, str]] = {}
        approved_voice: list[dict[str, str]] = []
        ruling = f"{RUN_ID}:{APPROVED_GATE_SHA256}"
        for row in proposed_voice:
            key = (norm(row["CAN_NAME"]), row["KIND"].upper())
            if key in voice_by_key or key[1] not in {"SYNTAX", "SUMMARY"}:
                raise EmissionError(f"INVALID_OR_DUPLICATE_VOICE:{key}")
            if row.get("SRC_HASH", "").upper() != APPROVED_HEADER_SHA256:
                raise EmissionError(f"STALE_VOICE_SOURCE:{key}")
            approved = dict(row)
            approved.update({
                "OVR_ID": stable_id("DOT", row["ENT_KIND"], row["CAN_NAME"], "en-US", "NATIVE", row["KIND"], "1"),
                "VOICE": "NATIVE", "RATIONALE": "Owner-approved initial DOT migration baseline.",
                "RULING_ID": ruling, "REVIEW_ST": "APPROVED", "ACTIVE": "T",
                "VER_AT": VERIFIED_AT,
            })
            voice_by_key[key] = approved
            approved_voice.append(approved)
        for row in scope:
            for kind in ("SYNTAX", "SUMMARY"):
                if (norm(row["NAME"]), kind) not in voice_by_key:
                    raise EmissionError(f"MISSING_APPROVED_VOICE:{row['NAME']}:{kind}")

        support_policy = load_support_policy(support_path)
        contract_status, contract_audit = primary_contract_statuses(inventory)
        base_by_name = {norm(row["CAN_NAME"]): row for row in base_refs}

        sysref: list[dict[str, str]] = []
        support_audit: list[dict[str, str]] = []
        ref_by_name: dict[str, dict[str, str]] = {}
        for ordinal, member in enumerate(scope, 1):
            name = norm(member["NAME"])
            target = norm(member["TARGET_NAME"])
            base = base_by_name.get(target)
            kind = member["ENT_KIND"].upper()
            status, support, support_auth = choose_support(member, base, contract_status, support_policy)
            implemented = True if kind in {"ALIAS", "SUBCOMMAND", "FUNCTION"} else truth((base or {}).get("IMPLEMENT", ""))
            visibility = (base or {}).get("VIS", "developer" if kind == "FUNCTION" else "public")
            ref_id = stable_id("DOT", kind, name)
            source_payload = {
                "scope": member, "base": base or {}, "support_status": status,
                "support_policy_sha256": sha256_file(support_path),
            }
            row = {
                "REF_ID": ref_id, "RUN_ID": RUN_ID, "NAMESPACE": "DOT", "ENT_KIND": kind,
                "CAN_NAME": name, "TOPICKEY": f"DOT|{name}", "VIS": visibility,
                "IMPLEMENT": tf(implemented), "SUPPORTED": tf(truth(support["SUPPORTED"])),
                "SUPPORT_ST": status, "MATURITY": support["MATURITY"], "AUDIENCE": support["AUDIENCE"],
                "ACTIVE": "T", "DISP_ORD": str(ordinal), "SRC_AUTH": member["SRC_AUTH"],
                "SRC_FILE": member["SRC_FILE"], "SRC_HASH": canonical_hash(source_payload),
                "REVIEW_ST": "APPROVED_M3D_CANDIDATE", "VER_AT": VERIFIED_AT,
            }
            sysref.append(row)
            ref_by_name[name] = row
            support_audit.append({
                "NAME": name, "ENT_KIND": kind, "TARGET_NAME": target,
                "SOURCE_STATUS": status, "SUPPORTED": row["SUPPORTED"],
                "MATURITY": row["MATURITY"], "AUDIENCE": row["AUDIENCE"],
                "STATUS_AUTHORITY": support_auth,
            })

        sysref_aliases: list[dict[str, str]] = []
        alias_by_name = {norm(row["ALIAS"]): row for row in alias_input}
        for member in scope:
            if member["ENT_KIND"].upper() != "ALIAS":
                continue
            name = norm(member["NAME"])
            edge = alias_by_name.get(name)
            target = ref_by_name.get(norm(member["TARGET_NAME"]))
            alias_ref = ref_by_name[name]
            if edge is None or target is None:
                raise EmissionError(f"ALIAS_EDGE_UNRESOLVED:{name}")
            alias_kind = edge["ALIAS_KND"].upper() or "DISPLAY"
            sysref_aliases.append({
                "ALIAS_ID": stable_id(alias_ref["REF_ID"], name, alias_kind),
                "RUN_ID": RUN_ID, "REF_ID": alias_ref["REF_ID"], "ALIAS": name,
                "ALIAS_KND": alias_kind, "DISP_STYL": edge["DISP_STYL"].upper(),
                "TARGET_ID": target["REF_ID"], "SRC_AUTH": edge["SRC_AUTH"],
                "SRC_FILE": edge["SRC_FILE"], "SRC_HASH": member["SRC_HASH"], "ACTIVE": "T",
            })
        if len(sysref_aliases) != 23:
            raise EmissionError(f"ALIAS_OUTPUT_COUNT_MISMATCH:{len(sysref_aliases)}")

        canonical_ref_ids = {row["REF_ID"] for row in base_refs}
        sysref_lines = [dict(row) for row in base_lines
                        if not (row.get("REF_ID") in canonical_ref_ids
                                and row.get("VOICE", "").upper() == "NATIVE"
                                and row.get("KIND", "").upper() in {"SYNTAX", "SUMMARY"})]
        for voice in approved_voice:
            ref = ref_by_name[norm(voice["CAN_NAME"])]
            kind = voice["KIND"].upper()
            sysref_lines.append({
                "LINE_ID": stable_id(ref["REF_ID"], "en-US", "NATIVE", kind, "1"),
                "RUN_ID": RUN_ID, "REF_ID": ref["REF_ID"], "LOCALE_ID": "en-US",
                "VOICE": "NATIVE", "KIND": kind, "ROLE": kind, "ORDINAL": "1",
                "TEXT": voice["TEXT"], "SRC_AUTH": "REFVOICE_APPROVED_MIGRATION",
                "SRC_FILE": args.approval_record, "SRC_HASH": APPROVED_HEADER_SHA256,
                "OVERRIDE": "T", "REVIEW_ST": "APPROVED_M3D_CANDIDATE", "ACTIVE": "T",
            })
        line_keys = [(row["REF_ID"], row["LOCALE_ID"], row["VOICE"], row["KIND"], row["ORDINAL"])
                     for row in sysref_lines]
        if len(set(line_keys)) != len(line_keys):
            raise EmissionError("DUPLICATE_SYSREFLINE_KEY")

        projection: list[dict[str, str]] = []
        fields_diff: list[dict[str, str]] = []
        header_by_name = {norm(item.name): item for item in header_items}
        for ref in sysref:
            name = ref["CAN_NAME"]
            syntax = voice_by_key[(name, "SYNTAX")]["TEXT"]
            summary = voice_by_key[(name, "SUMMARY")]["TEXT"]
            source_hash = canonical_hash({
                "ref": ref, "syntax": syntax, "summary": summary,
                "approval": APPROVED_GATE_SHA256,
            })
            row = {
                "REF_ID": ref["REF_ID"], "RUN_ID": RUN_ID, "NAME": name,
                "SYNTAX": syntax, "SUMMARY": summary, "SUPPORTED": ref["SUPPORTED"],
                "SRC_HASH": source_hash, "REVIEW_ST": "APPROVED_M3D_CANDIDATE", "ACTIVE": "T",
            }
            projection.append(row)
            old = header_by_name[name]
            comparisons = {
                "NAME": (old.name, name), "SYNTAX": (old.syntax, syntax),
                "SUMMARY": (old.summary, summary),
                "SUPPORTED": (tf(old.supported), ref["SUPPORTED"]),
            }
            for field, (before, after) in comparisons.items():
                if before != after:
                    fields_diff.append({
                        "NAME": name, "FIELD": field, "CURRENT": before,
                        "CANDIDATE": after, "DISPOSITION": "APPROVED_M3D_CANDIDATE",
                    })

        generated = render_cpp_rows(projection)
        parsed = parse_generated_rows(parser_module, generated)
        roundtrip_ok = len(parsed) == len(projection) and all(
            item.name == row["NAME"] and item.syntax == row["SYNTAX"]
            and item.summary == row["SUMMARY"] and item.supported == truth(row["SUPPORTED"])
            for item, row in zip(parsed, projection)
        )
        if not roundtrip_ok:
            raise EmissionError("GENERATED_CPP_ROUNDTRIP_FAILED")

        _fp, fox_items, _fs = parser_module.parse_header(fox_header.read_text(encoding="utf-8"))
        fox_by_name = {norm(item.name): item for item in fox_items}
        shared = [row for row in projection if row["NAME"] in fox_by_name]
        distinct = [row for row in shared if row["SYNTAX"] != fox_by_name[row["NAME"]].syntax
                    or row["SUMMARY"] != fox_by_name[row["NAME"]].summary]
        if not shared or not distinct:
            raise EmissionError("DOT_FOX_VOICE_PRESERVATION_NOT_PROVEN")

        out.mkdir(parents=True)
        csv_dir = out / "candidate/csv"
        csv_paths = {
            "SYSREFRUN": csv_dir / "sysrefrun_candidate.csv",
            "SYSREF": csv_dir / "sysref_candidate.csv",
            "SYSREFLINE": csv_dir / "sysrefline_candidate.csv",
            "SYSREFALIAS": csv_dir / "sysrefalias_candidate.csv",
            "REFVOICE": csv_dir / "refvoice_approved_migration.csv",
            "REFSUPPORT": csv_dir / "refsupport_approved.csv",
            "DOTREF": csv_dir / "dotref_candidate.csv",
        }
        input_hashes = {
            "gate": sha256_file(gate), "approval_record": sha256_file(approval),
            "header": sha256_file(header), "fox_header": sha256_file(fox_header),
            "scope": sha256_file(scope_path), "aliases": sha256_file(aliases_path),
            "voice": sha256_file(proposed_voice_path), "assembly_ref": sha256_file(base_ref_path),
            "assembly_lines": sha256_file(base_lines_path), "inventory": sha256_file(inventory),
            "support_policy": sha256_file(support_path), "schema_contract": sha256_file(schema_path),
        }
        run_row = {
            "RUN_ID": RUN_ID, "REPO_SHA": args.repo_sha.upper(), "START_UTC": VERIFIED_AT,
            "END_UTC": VERIFIED_AT, "COLLECTOR": "dotref-m3d-report-only-emitter-v1",
            "COLL_HASH": sha256_file(Path(__file__).resolve()),
            "POLICY_ID": "AIF-171-M3C-APPROVED-SUPPORT-MAPPING",
            "POL_HASH": sha256_file(support_path), "INPUT_HASH": canonical_hash(input_hashes),
            "STATUS": "M3D_CANDIDATE", "CREATED_BY": "member.ai.codex",
            "DETAIL": json.dumps({"scope": 268, "aliases": 23, "voice": 536}, sort_keys=True),
        }
        write_csv(csv_paths["SYSREFRUN"], SYSREFRUN_FIELDS, [run_row])
        write_csv(csv_paths["SYSREF"], SYSREF_FIELDS, sysref)
        write_csv(csv_paths["SYSREFLINE"], SYSREFLINE_FIELDS, sysref_lines)
        write_csv(csv_paths["SYSREFALIAS"], SYSREFALIAS_FIELDS, sysref_aliases)
        write_csv(csv_paths["REFVOICE"], REFVOICE_FIELDS, approved_voice)
        policy_rows = read_csv(support_path)
        write_csv(csv_paths["REFSUPPORT"], list(policy_rows[0]), policy_rows)
        write_csv(csv_paths["DOTREF"], DOTREF_FIELDS, projection)
        include_path = out / "candidate/include/dotref_catalog.generated.inc"
        include_path.parent.mkdir(parents=True, exist_ok=True)
        include_path.write_text(generated, encoding="utf-8", newline="\n")
        runtime_script = emit_runtime_script(out, csv_paths)

        write_csv(out / "reports/field_diff.csv",
                  ["NAME", "FIELD", "CURRENT", "CANDIDATE", "DISPOSITION"], fields_diff)
        write_csv(out / "reports/support_resolution.csv",
                  ["NAME", "ENT_KIND", "TARGET_NAME", "SOURCE_STATUS", "SUPPORTED",
                   "MATURITY", "AUDIENCE", "STATUS_AUTHORITY"], support_audit)
        write_csv(out / "reports/contract_status_audit.csv",
                  ["CAN_NAME", "STATUS", "SOURCE", "DISPOSITION"], contract_audit)
        write_csv(out / "reports/dot_fox_voice_preservation.csv",
                  ["NAME", "DOT_SYNTAX", "FOX_SYNTAX", "DOT_SUMMARY", "FOX_SUMMARY", "DISTINCT"], [
                      {
                          "NAME": row["NAME"], "DOT_SYNTAX": row["SYNTAX"],
                          "FOX_SYNTAX": fox_by_name[row["NAME"]].syntax,
                          "DOT_SUMMARY": row["SUMMARY"], "FOX_SUMMARY": fox_by_name[row["NAME"]].summary,
                          "DISTINCT": tf(row in distinct),
                      } for row in shared
                  ])

        artifact_hashes = {
            str(path.relative_to(out)).replace("\\", "/"): sha256_file(path)
            for path in sorted(out.rglob("*")) if path.is_file()
        }
        gates = {
            "G0_IMMUTABLE_INPUT_PACKAGE": "PASS",
            "G1_SCHEMA_AND_KEY_INTEGRITY": "PASS",
            "G2_AUTHORITY_RESOLUTION": "PASS",
            "G3_COMPLETE_FIELD_REFRESH": "PASS",
            "G4_NO_SILENT_LEGACY_CARRY": "PASS",
            "G5_NATIVE_COMPATIBILITY_VOICE": "PASS",
            "G6_DETERMINISM_PENDING_SECOND_RUN": "PENDING",
            "G7_CPP_ROUNDTRIP": "PASS",
        }
        summary = {
            "schema": SCHEMA, "run_id": RUN_ID, "mode": "REPORT_ONLY",
            "status": "M3D_CANDIDATE_EMITTED_G6_PENDING", "live_mutation": False,
            "approved_gate_sha256": APPROVED_GATE_SHA256,
            "counts": {
                "sysref": len(sysref), "sysrefline": len(sysref_lines),
                "sysrefalias": len(sysref_aliases), "refvoice": len(approved_voice),
                "refsupport": len(policy_rows), "dotref": len(projection),
                "field_differences": len(fields_diff), "dot_fox_shared": len(shared),
                "dot_fox_distinct_voice": len(distinct),
            },
            "inputs": input_hashes, "artifacts": artifact_hashes, "gates": gates,
            "runtime_load_script": str(runtime_script.relative_to(out)).replace("\\", "/"),
            "forbidden_mutations": [
                "include/dotref.hpp", "HELP", "META", "manuals", "website",
                "publication staging", "commit", "push",
            ],
        }
        write_json(out / "reports/m3d_emission_summary.json", summary)
        print(
            f"DOTREF M3D: {summary['status']} -- refs={len(sysref)} aliases={len(sysref_aliases)} "
            f"voice={len(approved_voice)} diffs={len(fields_diff)}"
        )
        print(f"REPORT-ONLY: {out}")
        return 0
    except (EmissionError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
