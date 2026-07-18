from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .inventory import collect_inventory
from .paths import ManualgenPaths
from .runlog import RunLogger, utc_now_iso
from .util import read_csv, relpath_posix, sha256_file, write_csv, write_json
from .validation import summarize_validation, validate_inventory


KIND_ORDER = (
    "STATUS", "SUMMARY", "SYNTAX", "USAGE", "ARGUMENT", "EXAMPLE",
    "NOTE", "WARNING", "ERROR", "MESSAGE", "HINT", "ALIAS",
    "RELATED", "SOURCE_FACT", "DEPRECATION",
)


def _int_value(row: dict[str, str], key: str) -> int:
    try:
        return int(row.get(key, ""))
    except ValueError:
        return 0


def _read_harvest(paths: ManualgenPaths, inv: dict[str, Any], name: str) -> list[dict[str, str]]:
    row = next((item for item in inv["harvest"]["files"] if item["file_name"] == name), None)
    if not row or not row.get("relative_path_posix"):
        return []
    return read_csv(paths.repo_root / row["relative_path_posix"])


def _render_text(value: str) -> str:
    return html.escape((value or "").replace("\r\n", "\n").replace("\r", "\n")).replace("\n", "<br>")


def _resolve_command_topic_key(command: dict[str, str], topic_keys: set[str]) -> tuple[str, str]:
    key = command.get("CMDKEY", "")
    if key in topic_keys:
        return key, "EXACT_CMDKEY"
    name = command.get("COMMAND", "")
    if command.get("CATALOG") == "FOX" and name.startswith("SET") and not name.startswith("SET ") and len(name) > 3:
        spaced = f"FOX|SET {name[3:]}"
        if spaced in topic_keys:
            return spaced, "FOX_COMPACT_SET_TO_SPACED_TOPIC"
    return "", "UNRESOLVED"


def _classify_unassigned_line(line: dict[str, str]) -> str:
    if line.get("CATALOG") == "SYSTEM" and line.get("SOURCE") == "SHARED_MSG":
        return "GLOBAL_SHARED_MESSAGE"
    if line.get("SOURCE") == "SOURCE_MINER" and line.get("KIND") == "SOURCE_FACT":
        return "UNSCOPED_SOURCE_MESSAGE_FACT"
    return "UNCLASSIFIED_UNASSIGNED_LINE"


def build_reference_candidate(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    """Transform an explicit harvest into a candidate-only human reference."""
    inv = collect_inventory(paths)
    checks = validate_inventory(paths, inv)
    validation = summarize_validation(checks)
    if validation["validation_fail_rows"]:
        return {"created": 0}, {**validation, "boundary_fail_rows": 0}

    topics = _read_harvest(paths, inv, "HELP_HELP_TOPIC.csv")
    lines = _read_harvest(paths, inv, "HELP_HELP_LINE.csv")
    commands = _read_harvest(paths, inv, "HELP_COMMANDS.csv")
    args = _read_harvest(paths, inv, "HELP_CMD_ARGS.csv")
    syscmd = _read_harvest(paths, inv, "META_SYSCMD.csv")

    topics.sort(key=lambda row: (_int_value(row, "TOPICID"), row.get("TOPICKEY", "")))
    lines.sort(key=lambda row: (_int_value(row, "LINEID"), _int_value(row, "PART_NO")))
    topic_keys = [row.get("TOPICKEY", "") for row in topics]
    duplicate_topic_keys = len(topic_keys) - len(set(topic_keys))

    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in lines:
        lines_by_topic[row.get("TOPICKEY", "")].append(row)
    args_by_key: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in args:
        args_by_key[row.get("CMDKEY", "")].append(row)
    syscmd_by_name: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in syscmd:
        syscmd_by_name[row.get("CAN_NAME", "").upper()].append(row)

    topic_key_set = set(topic_keys)
    commands_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    command_resolution_rows: list[dict[str, str]] = []
    for command in commands:
        resolved_key, rule = _resolve_command_topic_key(command, topic_key_set)
        if resolved_key:
            commands_by_topic[resolved_key].append(command)
        command_resolution_rows.append({
            "command_id": command.get("ID", ""),
            "catalog": command.get("CATALOG", ""),
            "command": command.get("COMMAND", ""),
            "original_cmdkey": command.get("CMDKEY", ""),
            "resolved_topic_key": resolved_key,
            "resolution_rule": rule,
            "status": "RESOLVED" if resolved_key else "UNRESOLVED",
        })

    run_id = logger.run_id if logger else "MANRUN-REFERENCE-CANDIDATE"
    output_dir = paths.manualgen_root / "generated" / "manualgen_reference_candidates" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "help_topic_reference_candidate.md"
    lineage_path = output_dir / "help_topic_reference_lineage.csv"
    resolution_path = output_dir / "help_topic_command_resolution.csv"
    manifest_path = output_dir / "help_topic_reference_manifest.json"

    md = [
        "<!-- Candidate-only HELP topic reference. Not publication. -->",
        f"<!-- harvest_workspace: {inv['harvest'].get('workspace_posix', '')} -->",
        f"<!-- created_utc: {utc_now_iso()} -->",
        "",
        "# DotTalk++ HELP Topic Reference Candidate",
        "",
        "This human-view artifact is a mechanical projection of the selected HELP/META snapshot. It has not been accepted or published.",
        "",
        f"- Topics: {len(topics)}",
        f"- HELP lines: {len(lines)}",
        f"- Commands: {len(commands)}",
        f"- Command arguments: {len(args)}",
        f"- SYSCMD rows: {len(syscmd)}",
        "",
    ]
    lineage_rows: list[dict[str, Any]] = []
    included_line_ids: set[str] = set()
    for topic in topics:
        key = topic.get("TOPICKEY", "")
        title = topic.get("TITLE") or topic.get("TOPIC") or key
        topic_lines = lines_by_topic.get(key, [])
        topic_commands = commands_by_topic.get(key, [])
        meta_matches = syscmd_by_name.get(topic.get("TOPIC", "").upper(), []) if topic.get("CATALOG") == "DOT" else []
        md.extend([
            f"## {_render_text(topic.get('CATALOG', ''))}: {_render_text(title)}",
            "",
            f"- Topic key: `{_render_text(key)}`",
            f"- Type/status: `{_render_text(topic.get('TOPICTYPE', ''))}` / `{_render_text(topic.get('STATUS', ''))}`",
            f"- Primary/confidence: `{_render_text(topic.get('PRIMARY', ''))}` / `{_render_text(topic.get('CONFID', ''))}`",
            f"- Implemented/supported: `{_render_text(topic.get('IMPLEMENT', ''))}` / `{_render_text(topic.get('SUPPORTED', ''))}`",
        ])
        if topic_commands:
            rendered_commands = ", ".join(
                f"{command.get('COMMAND', '')} (ID {command.get('ID', '').strip()}, args {len(args_by_key.get(command.get('CMDKEY', ''), []))})"
                for command in topic_commands
            )
            md.append(f"- Command inventory: `{_render_text(rendered_commands)}`")
        if meta_matches:
            rendered = ", ".join(f"{row.get('CMD_ID', '')}:{row.get('HANDLER', '')}" for row in meta_matches)
            md.append(f"- SYSCMD: `{_render_text(rendered)}`")
        md.append("")

        by_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
        for line in topic_lines:
            by_kind[line.get("KIND", "")].append(line)
        ordered_kinds = [kind for kind in KIND_ORDER if kind in by_kind]
        ordered_kinds.extend(sorted(set(by_kind) - set(ordered_kinds)))
        for kind in ordered_kinds:
            md.extend([f"### {kind.replace('_', ' ').title()}", ""])
            for line in by_kind[kind]:
                line_id = line.get("LINEID", "")
                included_line_ids.add(line_id)
                text = _render_text(line.get("TEXT", ""))
                provenance = f"{line.get('SOURCE', '')}/{line.get('CONFID', '')}; line {line_id}"
                md.append(f"- {text} <small>({_render_text(provenance)})</small>")
                lineage_rows.append({
                    "line_id": line_id,
                    "topic_key": key,
                    "catalog": topic.get("CATALOG", ""),
                    "topic": topic.get("TOPIC", ""),
                    "topic_type": topic.get("TOPICTYPE", ""),
                    "kind": kind,
                    "source": line.get("SOURCE", ""),
                    "confidence": line.get("CONFID", ""),
                    "name": line.get("NAME", ""),
                    "included": 1,
                })
            md.append("")

    unassigned_lines = [row for row in lines if row.get("TOPICKEY", "") not in topic_key_set]
    if unassigned_lines:
        md.extend([
            "# Non-Topic Evidence Appendices",
            "",
            "These harvested rows intentionally sit outside HELP topic identity. They are classified and retained without being silently attached to commands.",
            "",
        ])
        for classification in ("GLOBAL_SHARED_MESSAGE", "UNSCOPED_SOURCE_MESSAGE_FACT", "UNCLASSIFIED_UNASSIGNED_LINE"):
            class_lines = [line for line in unassigned_lines if _classify_unassigned_line(line) == classification]
            if not class_lines:
                continue
            md.extend([f"## {classification.replace('_', ' ').title()}", ""])
            for line in class_lines:
                line_id = line.get("LINEID", "")
                included_line_ids.add(line_id)
                md.append(f"- {_render_text(line.get('TEXT', ''))} <small>({_render_text(line.get('SOURCE', ''))}/{_render_text(line.get('CONFID', ''))}; line {_render_text(line_id)}; kind {_render_text(line.get('KIND', ''))})</small>")
                lineage_rows.append({
                    "line_id": line_id,
                    "topic_key": line.get("TOPICKEY", ""),
                    "catalog": line.get("CATALOG", ""),
                    "topic": line.get("TOPIC", ""),
                    "topic_type": classification,
                    "kind": line.get("KIND", ""),
                    "source": line.get("SOURCE", ""),
                    "confidence": line.get("CONFID", ""),
                    "name": line.get("NAME", ""),
                    "included": 1,
                })
            md.append("")

    missing_commands = [row for row in command_resolution_rows if row["status"] == "UNRESOLVED"]
    if missing_commands:
        md.extend([
            "# Review Appendix: Commands Without Topic Rows",
            "",
            "These command-inventory rows have no matching HELP_HELP_TOPIC row. They remain review findings rather than inferred topics.",
            "",
        ])
        for command in missing_commands:
            md.append(f"- `{_render_text(command.get('original_cmdkey', ''))}` (ID {_render_text(command.get('command_id', ''))})")
        md.append("")

    markdown_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")
    write_csv(lineage_path, lineage_rows)
    write_csv(resolution_path, command_resolution_rows)
    orphan_line_rows = sum(1 for row in lines if row.get("TOPICKEY", "") not in topic_key_set)
    unassigned_class_counts = {
        classification: sum(_classify_unassigned_line(row) == classification for row in unassigned_lines)
        for classification in ("GLOBAL_SHARED_MESSAGE", "UNSCOPED_SOURCE_MESSAGE_FACT", "UNCLASSIFIED_UNASSIGNED_LINE")
    }
    command_without_topic = len(missing_commands)
    compact_aliases_resolved = sum(row["resolution_rule"] == "FOX_COMPACT_SET_TO_SPACED_TOPIC" for row in command_resolution_rows)
    transform_status = "PASS" if not duplicate_topic_keys and not unassigned_class_counts["UNCLASSIFIED_UNASSIGNED_LINE"] and not command_without_topic and len(included_line_ids) == len(lines) else "FAIL"
    manifest = {
        "schema": "dottalk.manualgen.help_topic_reference_candidate.v1",
        "created_utc": utc_now_iso(),
        "run_id": run_id,
        "manualgen_version": __version__,
        "transform_status": transform_status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "canonical_harvest_replaced": 0,
        "harvest": inv["harvest"],
        "counts": {
            "topics": len(topics),
            "help_lines": len(lines),
            "included_help_lines": len(included_line_ids),
            "commands": len(commands),
            "command_arguments": len(args),
            "syscmd_rows": len(syscmd),
            "duplicate_topic_keys": duplicate_topic_keys,
            "unassigned_line_rows": orphan_line_rows,
            "global_shared_message_lines": unassigned_class_counts["GLOBAL_SHARED_MESSAGE"],
            "unscoped_source_message_fact_lines": unassigned_class_counts["UNSCOPED_SOURCE_MESSAGE_FACT"],
            "unclassified_unassigned_lines": unassigned_class_counts["UNCLASSIFIED_UNASSIGNED_LINE"],
            "compact_command_aliases_resolved": compact_aliases_resolved,
            "command_without_topic": command_without_topic,
        },
        "artifacts": {
            "markdown": relpath_posix(markdown_path, paths.repo_root),
            "markdown_sha256": sha256_file(markdown_path),
            "lineage": relpath_posix(lineage_path, paths.repo_root),
            "lineage_sha256": sha256_file(lineage_path),
            "command_resolution": relpath_posix(resolution_path, paths.repo_root),
            "command_resolution_sha256": sha256_file(resolution_path),
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("help_topic_reference_candidate", markdown_path, "Candidate-only human HELP topic reference.")
        logger.artifact("help_topic_reference_lineage", lineage_path, "Row-level HELP line provenance.")
        logger.artifact("help_topic_command_resolution", resolution_path, "Command-to-topic resolution ledger.")
        logger.artifact("help_topic_reference_manifest", manifest_path, "Candidate transform manifest.")
    state = {
        "created": 1,
        "reference_markdown": relpath_posix(markdown_path, paths.repo_root),
        "reference_manifest": relpath_posix(manifest_path, paths.repo_root),
        **manifest["counts"],
    }
    counts = {**validation, "boundary_fail_rows": 0, **manifest["counts"]}
    return state, counts
