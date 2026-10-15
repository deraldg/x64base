#!/usr/bin/env python3
"""Build the report-only DOTREF migration closure for M3C.

The M3B assembler intentionally starts with canonical SYSCMD command rows.
This tool resolves every additional member of the current compiled DOT catalog
through source authority and records why it belongs to the DOT projection.

The current header supplies migration membership and proposed DOT wording only.
It never mints an identity: aliases must resolve to a canonical SYSCMD command,
subcommands must resolve to SYSSUBCMD or explicit source syntax, and functions
must resolve to an implemented extension function.  Unresolved members block.
No live header, DBF/DTX, HELP, META, manual, or website file is written.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "dottalk.dotref.m3c_migration_closure.v1"
SCOPE_FIELDS = [
    "NAME", "ENT_KIND", "TARGET_NAME", "SRC_AUTH", "SRC_FILE", "SRC_HASH",
    "REVIEW_ST", "ACTIVE",
]
ALIAS_FIELDS = [
    "CAN_NAME", "ALIAS", "ALIAS_KND", "DISP_STYL", "SRC_AUTH", "SRC_FILE",
    "ACTIVE",
]
VOICE_FIELDS = [
    "NAMESPACE", "ENT_KIND", "CAN_NAME", "LOCALE_ID", "VOICE", "KIND",
    "ORDINAL", "TEXT", "RATIONALE", "OWNER", "RULING_ID", "REVIEW_ST",
    "SRC_HASH", "ACTIVE", "VER_AT",
]
REPORT_FIELDS = [
    "NAME", "ENT_KIND", "TARGET_NAME", "CLASSIFICATION", "BLOCKING",
    "SRC_AUTH", "SRC_FILE", "DETAIL",
]


class ClosureError(RuntimeError):
    pass


@dataclass(frozen=True)
class Evidence:
    target: str
    authority: str
    source: str
    kind: str = "ALIAS"


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).upper()


def compact(value: str) -> str:
    return re.sub(r"[\s_-]+", "", norm(value))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    return sha256_bytes(json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":")
    ).encode("utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [{(key or "").strip().upper(): (value or "")
                 for key, value in row.items()} for row in csv.DictReader(handle)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ClosureError(f"MODULE_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def contract_alias_evidence(path: Path) -> dict[str, list[Evidence]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[Evidence]] = defaultdict(list)
    for contract in data.get("contracts", []):
        target = norm(str(contract.get("command", "")))
        source = str(contract.get("file", ""))
        sections = contract.get("sections", {})
        if not target or not isinstance(sections, dict):
            continue
        for alias_field in sections.get("ALIASES", []):
            # The contract grammar permits a comma- or semicolon-separated
            # aliases field. contract_inventory preserves the source line as a
            # single section value, so split that grammar here rather than
            # mistaking "BUILD VECTORS, BUILD INFO" for one alias.
            for alias in re.split(r"\s*[,;]\s*", str(alias_field)):
                alias_name = norm(alias)
                if alias_name:
                    out[alias_name].append(Evidence(
                        target, "SRCUSAGE_ALIAS", source, "ALIAS"
                    ))
    return out


def shortcut_evidence(path: Path) -> dict[str, list[Evidence]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, list[Evidence]] = defaultdict(list)
    for match in re.finditer(r'\{\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\}', text):
        out[norm(match.group(1))].append(Evidence(
            norm(match.group(2)), "SHORTCUT_RESOLVER", path.as_posix(), "SHORTCUT"
        ))
    return out


def reference_alias_evidence(path: Path) -> dict[str, list[Evidence]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, list[Evidence]] = defaultdict(list)
    pattern = re.compile(
        r'add\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*'
        r'"(alias|shortcut|reexpression)"', re.IGNORECASE
    )
    for match in pattern.finditer(text):
        out[norm(match.group(1))].append(Evidence(
            norm(match.group(2)), "REFERENCE_COLLECTION", path.as_posix(),
            match.group(3).upper(),
        ))
    return out


def extension_functions(root: Path) -> dict[str, Evidence]:
    out: dict[str, Evidence] = {}
    pattern = re.compile(r'\bstatic\s+std::string\s+fn_([A-Z_][A-Z0-9_]*)\s*\(')
    for path in sorted((root / "src/ext/fn").glob("*.cpp")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in pattern.finditer(text):
            name = norm(match.group(1))
            out[name] = Evidence(name, "EXT_FUNCTION_SOURCE", path.relative_to(root).as_posix(), "FUNCTION")
    return out


def merge_evidence(*maps: dict[str, list[Evidence]]) -> dict[str, list[Evidence]]:
    out: dict[str, list[Evidence]] = defaultdict(list)
    for mapping in maps:
        for name, evidence in mapping.items():
            out[name].extend(evidence)
    return out


def unique_target(evidence: list[Evidence], canonical: set[str]) -> Evidence | None:
    usable = [item for item in evidence if item.target in canonical]
    targets = {item.target for item in usable}
    if len(targets) != 1:
        return None
    target = next(iter(targets))
    return next(item for item in usable if item.target == target)


def resolve_members(
    names: list[str],
    canonical_rows: dict[str, dict[str, str]],
    subcommands: dict[str, dict[str, str]],
    aliases: dict[str, list[Evidence]],
    functions: dict[str, Evidence],
    registry_handlers: dict[str, str],
    explicit_subforms: dict[str, Evidence],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    canonical = set(canonical_rows)
    by_handler: dict[str, list[str]] = defaultdict(list)
    for name, row in canonical_rows.items():
        handler = row.get("HANDLER", "").strip()
        if handler:
            by_handler[handler].append(name)

    scope: list[dict[str, str]] = []
    alias_rows: list[dict[str, str]] = []
    report: list[dict[str, str]] = []
    for raw_name in names:
        name = norm(raw_name)
        kind = ""
        target = ""
        authority = ""
        source = ""
        classification = ""
        detail = ""

        if name in canonical:
            kind, target = "COMMAND", name
            authority = "SYSCMD"
            source = canonical_rows[name].get("SRC_FILE", "")
            classification = "CANONICAL_COMMAND"
        elif name in functions:
            item = functions[name]
            kind, target = "FUNCTION", name
            authority, source = item.authority, item.source
            classification = "IMPLEMENTED_EXTENSION_FUNCTION"
        elif compact(name) in subcommands:
            row = subcommands[compact(name)]
            kind, target = "SUBCOMMAND", norm(
                row.get("PARENT", "") or row.get("PARENT_CMD", "")
            )
            authority = "SYSSUBCMD"
            source = row.get("SRC_FILE", "")
            classification = "NORMALIZED_SUBCOMMAND"
        else:
            item = unique_target(aliases.get(name, []), canonical)
            if item is None:
                handler = registry_handlers.get(name, "")
                candidates = by_handler.get(handler, []) if handler else []
                if len(candidates) == 1:
                    item = Evidence(
                        candidates[0], "REGISTRY_HANDLER_EQUIVALENCE",
                        "source command registry", "ALIAS",
                    )
            if item is not None:
                kind, target = "ALIAS", item.target
                authority, source = item.authority, item.source
                classification = "SOURCE_RESOLVED_ALIAS"
            elif name in explicit_subforms:
                item = explicit_subforms[name]
                kind, target = "SUBCOMMAND", item.target
                authority, source = item.authority, item.source
                classification = "SOURCE_RESOLVED_SUBCOMMAND"

        blocking = not bool(kind and target and authority)
        if blocking:
            classification = "UNRESOLVED_HEADER_MEMBER"
            detail = "Current member did not resolve through canonical command, alias, subcommand, or function authority."
        else:
            evidence_payload = {
                "name": name, "kind": kind, "target": target,
                "authority": authority, "source": source,
            }
            scope.append({
                "NAME": name,
                "ENT_KIND": kind,
                "TARGET_NAME": target,
                "SRC_AUTH": authority,
                "SRC_FILE": source,
                "SRC_HASH": canonical_hash(evidence_payload),
                "REVIEW_ST": "MIGRATION_CANDIDATE",
                "ACTIVE": "T",
            })
            if kind == "ALIAS":
                alias_rows.append({
                    "CAN_NAME": target,
                    "ALIAS": name,
                    "ALIAS_KND": aliases.get(name, [Evidence(target, authority, source)])[0].kind.lower(),
                    "DISP_STYL": "row",
                    "SRC_AUTH": authority,
                    "SRC_FILE": source,
                    "ACTIVE": "T",
                })
            detail = "Identity resolved from source; current header contributes migration membership only."
        report.append({
            "NAME": name,
            "ENT_KIND": kind,
            "TARGET_NAME": target,
            "CLASSIFICATION": classification,
            "BLOCKING": "T" if blocking else "F",
            "SRC_AUTH": authority,
            "SRC_FILE": source,
            "DETAIL": detail,
        })
    return scope, alias_rows, report


def explicit_subform_evidence(root: Path, canonical: set[str]) -> dict[str, Evidence]:
    """Resolve source-declared multiword forms outside the SET subusage lane."""
    out: dict[str, Evidence] = {}
    sources = [
        root / "src/cli/command_catalog.cpp",
        root / "src/cli/reference_collection.cpp",
        root / "src/cli/shell_var_utils.cpp",
    ]
    for source in sources:
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(
            r'"([A-Z][A-Z0-9_!]+\s+[A-Z][A-Z0-9_!]*)(?![A-Z0-9_!])', text
        ):
            name = norm(match.group(1))
            parent = name.split()[0]
            if parent not in canonical:
                continue
            out.setdefault(name, Evidence(
                parent, "SOURCE_SYNTAX_LITERAL", source.relative_to(root).as_posix(), "SUBCOMMAND"
            ))
    return out


def proposed_voice(items: list[Any], scope: list[dict[str, str]], header_hash: str) -> list[dict[str, str]]:
    by_name = {row["NAME"]: row for row in scope}
    rows: list[dict[str, str]] = []
    for item in items:
        name = norm(item.name)
        member = by_name.get(name)
        if member is None:
            continue
        for kind, text in (("SYNTAX", item.syntax), ("SUMMARY", item.summary)):
            rows.append({
                "NAMESPACE": "DOT",
                "ENT_KIND": member["ENT_KIND"],
                "CAN_NAME": name,
                "LOCALE_ID": "en-US",
                "VOICE": "native",
                "KIND": kind,
                "ORDINAL": "1",
                "TEXT": text,
                "RATIONALE": "One-time migration of current DOT projection wording; requires field review.",
                "OWNER": "member.derald",
                "RULING_ID": "AIF-171-M3C",
                "REVIEW_ST": "PROPOSED",
                "SRC_HASH": header_hash,
                "ACTIVE": "F",
                "VER_AT": "",
            })
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--header", default="include/dotref.hpp")
    parser.add_argument("--syscmd", required=True)
    parser.add_argument("--syssubcmd", required=True)
    parser.add_argument("--contract-inventory", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    header = (root / args.header).resolve()
    syscmd = (root / args.syscmd).resolve()
    syssubcmd = (root / args.syssubcmd).resolve()
    inventory = (root / args.contract_inventory).resolve()
    out = (root / args.out).resolve()
    try:
        for path in (header, syscmd, syssubcmd, inventory, out):
            path.relative_to(root)
        if out.exists():
            raise ClosureError(f"OUTPUT_ALREADY_EXISTS:{out}")
        for path in (header, syscmd, syssubcmd, inventory):
            if not path.is_file():
                raise ClosureError(f"INPUT_MISSING:{path}")

        parser_module = load_module(
            "dotref_metadata_parser_for_closure_v1",
            root / "dottalkpp/tools/help/generate_dotref_from_metadata_v1.py",
        )
        syscmd_module = load_module(
            "generate_syscmd_for_closure_v1",
            root / "tools/fullstack_docs/generate_syscmd.py",
        )
        _prefix, items, _suffix = parser_module.parse_header(header.read_text(encoding="utf-8"))
        command_rows = read_csv(syscmd)
        canonical_rows = {norm(row.get("CAN_NAME", "")): row for row in command_rows if norm(row.get("CAN_NAME", ""))}
        sub_rows = read_csv(syssubcmd)
        subcommands = {
            compact(row.get("QUAL_NAME", "")): row
            for row in sub_rows if row.get("ACTIVE", "").strip().upper() in {"T", "TRUE", "1", "YES"}
        }
        alias_evidence = merge_evidence(
            contract_alias_evidence(inventory),
            shortcut_evidence(root / "src/cli/shortcut_resolver.hpp"),
            reference_alias_evidence(root / "src/cli/reference_collection.cpp"),
        )
        functions = extension_functions(root)
        registry_handlers = syscmd_module.registry_map(root)
        explicit_subforms = explicit_subform_evidence(root, set(canonical_rows))
        scope, aliases, report = resolve_members(
            [item.name for item in items], canonical_rows, subcommands,
            alias_evidence, functions, registry_handlers, explicit_subforms,
        )
        blockers = [row for row in report if row["BLOCKING"] == "T"]
        header_hash = sha256_file(header)
        voice = proposed_voice(items, scope, header_hash)

        out.mkdir(parents=True)
        write_csv(out / "candidate/refscope_candidate.csv", SCOPE_FIELDS, scope)
        write_csv(out / "candidate/refaliases_candidate.csv", ALIAS_FIELDS, aliases)
        write_csv(out / "candidate/refvoice_proposed.csv", VOICE_FIELDS, voice)
        write_csv(out / "reports/member_resolution.csv", REPORT_FIELDS, report)
        summary = {
            "schema": SCHEMA,
            "mode": "REPORT_ONLY",
            "live_mutation": False,
            "header": Path(args.header).as_posix(),
            "header_sha256": header_hash,
            "inputs": {
                "syscmd": {"path": Path(args.syscmd).as_posix(), "sha256": sha256_file(syscmd)},
                "syssubcmd": {"path": Path(args.syssubcmd).as_posix(), "sha256": sha256_file(syssubcmd)},
                "contract_inventory": {"path": Path(args.contract_inventory).as_posix(), "sha256": sha256_file(inventory)},
            },
            "counts": {
                "header_members": len(items),
                "resolved_members": len(scope),
                "canonical_commands": sum(row["ENT_KIND"] == "COMMAND" for row in scope),
                "display_aliases": sum(row["ENT_KIND"] == "ALIAS" for row in scope),
                "subcommands": sum(row["ENT_KIND"] == "SUBCOMMAND" for row in scope),
                "functions": sum(row["ENT_KIND"] == "FUNCTION" for row in scope),
                "proposed_voice_rows": len(voice),
                "blocking_members": len(blockers),
            },
            "status": "RESOLVED_REVIEW_REQUIRED" if not blockers else "BLOCKED",
            "current_header_role": "migration membership and proposed wording only; never identity authority",
            "generated_header": False,
        }
        (out / "reports/closure_summary.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n",
        )
        print(
            f"DOTREF M3C closure: {summary['status']} -- "
            f"resolved={len(scope)}/{len(items)} blockers={len(blockers)}"
        )
        print(f"REPORT-ONLY: {out}")
        return 0 if not blockers else 2
    except (ClosureError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
