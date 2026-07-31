"""Generated HELP candidate row builder."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Any

from .schema import validate_rows_by_table


@dataclass(frozen=True)
class CommandCandidate:
    command: str
    dotted_name: str
    summary: str
    catalog: str = "DOT"
    source: str = "MSG22AE"
    confidence: str = "CANDIDATE"


def build_generated_candidate_rows(
    candidates: Iterable[CommandCandidate],
    *,
    first_topic_id: int,
    first_artifact_id: int,
    first_line_id: int,
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {"HELP_TOPIC": [], "HELP_ARTIFACTS": [], "HELP_SECTION": [], "HELP_LINE": []}
    for offset, cand in enumerate(candidates):
        topic_id = first_topic_id + offset
        art_id = first_artifact_id + offset
        line_id = first_line_id + offset
        topic_key = f"{cand.catalog}|{cand.command}"
        text = cand.summary
        rows["HELP_TOPIC"].append({
            "TOPICID": topic_id, "TOPICKEY": topic_key, "CATALOG": cand.catalog, "TOPIC": cand.command,
            "TOPICTYPE": "COMMAND_OR_T", "STATUS": "candidate_dry_run", "IMPLEMENT": "F", "SUPPORTED": "F",
            "PRIMARY": cand.source, "CONFID": cand.confidence, "TITLE": cand.command, "SUMMARY": text,
            "SECTIONS": 1, "LINES": 1,
        })
        rows["HELP_ARTIFACTS"].append({
            "ID": art_id, "CATALOG": cand.catalog, "COMMAND": cand.command, "CMDKEY": topic_key,
            "OWNER": f"COMMAND:{cand.command}", "KIND": "HELP_TEXT", "SOURCE": cand.source,
            "CONFID": cand.confidence, "SEVERITY": "INFO", "NAME": "GENERATED_SOURCE_LOCALE_HELP",
            "ORD": 1, "TEXT": text,
        })
        rows["HELP_SECTION"].append({
            "SECTID": art_id, "ARTID": art_id, "TOPICID": topic_id, "TOPICKEY": topic_key,
            "KIND": "GENERATED", "SOURCE": cand.source, "CONFID": cand.confidence, "SEVERITY": "INFO",
            "NAME": "Generated candidate help", "ORD": 1, "NLINES": 1,
        })
        rows["HELP_LINE"].append({
            "LINEID": line_id, "ARTID": art_id, "TOPICKEY": topic_key, "CATALOG": cand.catalog,
            "TOPIC": cand.command, "KIND": "GENERATED", "SOURCE": cand.source, "CONFID": cand.confidence,
            "SEVERITY": "INFO", "NAME": "Generated candidate help", "ROLE": "BODY",
            "LINE_NO": 1, "PART_NO": 1, "TEXT": text,
        })
    issues = validate_rows_by_table(rows)
    if issues:
        raise ValueError(f"Generated HELP candidate rows failed validation: {issues}")
    return rows
