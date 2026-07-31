from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from . import __version__
from .inventory import collect_inventory
from .paths import ManualgenPaths
from .reference_candidate import KIND_ORDER, _classify_unassigned_line, _int_value, _read_harvest, _render_text
from .runlog import RunLogger, utc_now_iso
from .util import relpath_posix, sha256_file, write_csv, write_json
from .validation import summarize_validation, validate_inventory


SHELVES = {
    "01_dot_supported_commands": ("DOT supported commands", "INCLUDE_COMMAND_REFERENCE_CANDIDATE"),
    "02_dot_command_review": ("DOT pending or partial commands", "REVIEW_BEFORE_SECTION_CURATION"),
    "03_fox_supported_commands": ("FOX supported compatibility commands", "INCLUDE_COMPATIBILITY_REFERENCE_CANDIDATE"),
    "04_fox_command_review": ("FOX pending or partial commands", "REVIEW_BEFORE_SECTION_CURATION"),
    "05_education_concepts": ("Education concepts", "INCLUDE_EDUCATION_APPENDIX_CANDIDATE"),
    "06_supplemental_public_candidates": ("Supplemental education, extension, and UI topics", "REVIEW_PUBLIC_SUPPLEMENT"),
    "07_developer_internal_topics": ("Developer and internal topics", "EXCLUDE_FROM_PUBLIC_MANUAL_BY_DEFAULT"),
    "08_system_message_catalog": ("System message catalog", "SEPARATE_SYSTEM_MESSAGE_APPENDIX"),
    "09_source_message_facts": ("Unscoped source message facts", "SEPARATE_SOURCE_FACT_APPENDIX"),
    "99_unclassified": ("Unclassified evidence", "BLOCK_CURATION"),
}


def classify_topic(topic: dict[str, str]) -> tuple[str, str]:
    catalog = topic.get("CATALOG", "")
    status = topic.get("STATUS", "")
    if catalog == "DOT":
        shelf = "01_dot_supported_commands" if status == "supported" else "02_dot_command_review"
    elif catalog == "FOX":
        shelf = "03_fox_supported_commands" if status == "supported" else "04_fox_command_review"
    elif catalog == "ED":
        shelf = "05_education_concepts"
    elif catalog in {"EDU", "EXT", "UI"}:
        shelf = "06_supplemental_public_candidates"
    elif catalog in {"DEV", "INTERNAL"}:
        shelf = "07_developer_internal_topics"
    elif catalog == "SYSTEM":
        shelf = "08_system_message_catalog"
    else:
        shelf = "99_unclassified"
    return shelf, SHELVES[shelf][1]


def classify_line(line: dict[str, str], topic_shelf: dict[str, str]) -> str:
    key = line.get("TOPICKEY", "")
    if key:
        return topic_shelf.get(key, "99_unclassified")
    classification = _classify_unassigned_line(line)
    if classification == "GLOBAL_SHARED_MESSAGE":
        return "08_system_message_catalog"
    if classification == "UNSCOPED_SOURCE_MESSAGE_FACT":
        return "09_source_message_facts"
    return "99_unclassified"


def build_curation_candidate(paths: ManualgenPaths, logger: RunLogger | None = None) -> tuple[dict[str, Any], dict[str, int]]:
    inv = collect_inventory(paths)
    validation = summarize_validation(validate_inventory(paths, inv))
    if validation["validation_fail_rows"]:
        return {"created": 0}, {**validation, "boundary_fail_rows": 0}

    topics = _read_harvest(paths, inv, "HELP_HELP_TOPIC.csv")
    lines = _read_harvest(paths, inv, "HELP_HELP_LINE.csv")
    topics.sort(key=lambda row: (_int_value(row, "TOPICID"), row.get("TOPICKEY", "")))
    lines.sort(key=lambda row: (_int_value(row, "LINEID"), _int_value(row, "PART_NO")))

    topic_rows: list[dict[str, Any]] = []
    topic_shelf: dict[str, str] = {}
    topics_by_shelf: dict[str, list[dict[str, str]]] = defaultdict(list)
    for topic in topics:
        shelf, disposition = classify_topic(topic)
        key = topic.get("TOPICKEY", "")
        topic_shelf[key] = shelf
        topics_by_shelf[shelf].append(topic)
        topic_rows.append({
            "topic_id": topic.get("TOPICID", ""),
            "topic_key": key,
            "catalog": topic.get("CATALOG", ""),
            "topic": topic.get("TOPIC", ""),
            "topic_type": topic.get("TOPICTYPE", ""),
            "status": topic.get("STATUS", ""),
            "implemented": topic.get("IMPLEMENT", ""),
            "supported": topic.get("SUPPORTED", ""),
            "primary": topic.get("PRIMARY", ""),
            "confidence": topic.get("CONFID", ""),
            "shelf": shelf,
            "disposition": disposition,
            "reported_line_count": topic.get("LINES", ""),
        })

    line_rows: list[dict[str, Any]] = []
    lines_by_shelf: dict[str, list[dict[str, str]]] = defaultdict(list)
    lines_by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for line in lines:
        shelf = classify_line(line, topic_shelf)
        lines_by_shelf[shelf].append(line)
        if line.get("TOPICKEY", ""):
            lines_by_topic[line["TOPICKEY"]].append(line)
        line_rows.append({
            "line_id": line.get("LINEID", ""),
            "artifact_id": line.get("ARTID", ""),
            "topic_key": line.get("TOPICKEY", ""),
            "catalog": line.get("CATALOG", ""),
            "topic": line.get("TOPIC", ""),
            "kind": line.get("KIND", ""),
            "source": line.get("SOURCE", ""),
            "confidence": line.get("CONFID", ""),
            "shelf": shelf,
            "disposition": SHELVES[shelf][1],
        })

    run_id = logger.run_id if logger else "MANRUN-CURATION-CANDIDATE"
    output_dir = paths.manualgen_root / "generated" / "manualgen_curation_candidates" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    topic_ledger = output_dir / "manual_topic_curation_ledger.csv"
    line_ledger = output_dir / "manual_line_curation_ledger.csv"
    manifest_path = output_dir / "manual_curation_manifest.json"
    write_csv(topic_ledger, topic_rows)
    write_csv(line_ledger, line_rows)

    packet_artifacts: list[dict[str, Any]] = []
    for shelf, (title, disposition) in SHELVES.items():
        if shelf == "99_unclassified" and not topics_by_shelf[shelf] and not lines_by_shelf[shelf]:
            continue
        packet_path = output_dir / f"{shelf}.md"
        packet = [
            "<!-- Candidate-only manual curation packet. Not publication. -->",
            f"<!-- harvest_workspace: {inv['harvest'].get('workspace_posix', '')} -->",
            f"<!-- shelf: {shelf} -->",
            "",
            f"# {title}",
            "",
            f"Disposition: `{disposition}`.",
            "",
            f"Topics: {len(topics_by_shelf[shelf])}. Lines: {len(lines_by_shelf[shelf])}.",
            "",
        ]
        for topic in topics_by_shelf[shelf]:
            key = topic.get("TOPICKEY", "")
            packet.extend([
                f"## {_render_text(topic.get('CATALOG', ''))}: {_render_text(topic.get('TITLE') or topic.get('TOPIC') or key)}",
                "",
                f"- Key/type: `{_render_text(key)}` / `{_render_text(topic.get('TOPICTYPE', ''))}`",
                f"- Status: `{_render_text(topic.get('STATUS', ''))}`; implemented `{_render_text(topic.get('IMPLEMENT', ''))}`; supported `{_render_text(topic.get('SUPPORTED', ''))}`",
                f"- Primary/confidence: `{_render_text(topic.get('PRIMARY', ''))}` / `{_render_text(topic.get('CONFID', ''))}`",
                "",
            ])
            by_kind: dict[str, list[dict[str, str]]] = defaultdict(list)
            for line in lines_by_topic.get(key, []):
                by_kind[line.get("KIND", "")].append(line)
            ordered = [kind for kind in KIND_ORDER if kind in by_kind]
            ordered.extend(sorted(set(by_kind) - set(ordered)))
            for kind in ordered:
                packet.extend([f"### {kind.replace('_', ' ').title()}", ""])
                for line in by_kind[kind]:
                    packet.append(f"- {_render_text(line.get('TEXT', ''))} <small>({_render_text(line.get('SOURCE', ''))}/{_render_text(line.get('CONFID', ''))}; line {_render_text(line.get('LINEID', ''))})</small>")
                packet.append("")
        non_topic = [line for line in lines_by_shelf[shelf] if not line.get("TOPICKEY", "")]
        if non_topic:
            packet.extend(["## Non-topic evidence", ""])
            for line in non_topic:
                packet.append(f"- {_render_text(line.get('TEXT', ''))} <small>({_render_text(line.get('SOURCE', ''))}/{_render_text(line.get('CONFID', ''))}; line {_render_text(line.get('LINEID', ''))}; kind {_render_text(line.get('KIND', ''))})</small>")
            packet.append("")
        packet_path.write_text("\n".join(packet).rstrip() + "\n", encoding="utf-8")
        packet_artifacts.append({
            "shelf": shelf,
            "title": title,
            "disposition": disposition,
            "topic_count": len(topics_by_shelf[shelf]),
            "line_count": len(lines_by_shelf[shelf]),
            "path": relpath_posix(packet_path, paths.repo_root),
            "sha256": sha256_file(packet_path),
        })

    duplicate_topic_keys = len(topics) - len(set(row.get("TOPICKEY", "") for row in topics))
    duplicate_line_ids = len(lines) - len(set(row.get("LINEID", "") for row in lines))
    unclassified_topics = len(topics_by_shelf["99_unclassified"])
    unclassified_lines = len(lines_by_shelf["99_unclassified"])
    status = "PASS" if not duplicate_topic_keys and not duplicate_line_ids and not unclassified_topics and not unclassified_lines and len(topic_rows) == len(topics) and len(line_rows) == len(lines) else "FAIL"
    manifest = {
        "schema": "dottalk.manualgen.curation_candidate.v1",
        "created_utc": utc_now_iso(),
        "manualgen_version": __version__,
        "run_id": run_id,
        "status": status,
        "candidate_only": 1,
        "publication_authority_claimed": 0,
        "canonical_harvest_replaced": 0,
        "harvest": inv["harvest"],
        "counts": {
            "topics": len(topics),
            "topic_ledger_rows": len(topic_rows),
            "lines": len(lines),
            "line_ledger_rows": len(line_rows),
            "shelf_packets": len(packet_artifacts),
            "duplicate_topic_keys": duplicate_topic_keys,
            "duplicate_line_ids": duplicate_line_ids,
            "unclassified_topics": unclassified_topics,
            "unclassified_lines": unclassified_lines,
        },
        "shelves": packet_artifacts,
        "artifacts": {
            "topic_ledger": relpath_posix(topic_ledger, paths.repo_root),
            "topic_ledger_sha256": sha256_file(topic_ledger),
            "line_ledger": relpath_posix(line_ledger, paths.repo_root),
            "line_ledger_sha256": sha256_file(line_ledger),
        },
    }
    write_json(manifest_path, manifest)
    if logger:
        logger.artifact("manual_topic_curation_ledger", topic_ledger, "One-row-per-topic curation shelf ledger.")
        logger.artifact("manual_line_curation_ledger", line_ledger, "One-row-per-line curation shelf ledger.")
        logger.artifact("manual_curation_manifest", manifest_path, "Candidate-only curation manifest.")
        for artifact in packet_artifacts:
            logger.artifact(f"curation_packet_{artifact['shelf']}", paths.repo_root / artifact["path"], artifact["title"])
    state = {"created": 1, "status": status, "output_dir": relpath_posix(output_dir, paths.repo_root), "manifest": relpath_posix(manifest_path, paths.repo_root)}
    counts = {**validation, "boundary_fail_rows": 0, **manifest["counts"]}
    return state, counts
