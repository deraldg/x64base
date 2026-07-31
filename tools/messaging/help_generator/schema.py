"""Machine-readable generated HELP schema contract."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence, Any


@dataclass(frozen=True)
class FieldRule:
    name: str
    required: bool = True
    numeric: bool = False
    logical: bool = False


HELP_SCHEMA: dict[str, tuple[FieldRule, ...]] = {
    "HELP_TOPIC": (
        FieldRule("TOPICID", numeric=True), FieldRule("TOPICKEY"), FieldRule("CATALOG"), FieldRule("TOPIC"),
        FieldRule("TOPICTYPE"), FieldRule("STATUS"), FieldRule("IMPLEMENT", logical=True), FieldRule("SUPPORTED", logical=True),
        FieldRule("PRIMARY"), FieldRule("CONFID"), FieldRule("TITLE"), FieldRule("SUMMARY"),
        FieldRule("SECTIONS", numeric=True), FieldRule("LINES", numeric=True),
    ),
    "HELP_ARTIFACTS": (
        FieldRule("ID", numeric=True), FieldRule("CATALOG"), FieldRule("COMMAND"), FieldRule("CMDKEY"),
        FieldRule("OWNER"), FieldRule("KIND"), FieldRule("SOURCE"), FieldRule("CONFID"), FieldRule("SEVERITY"),
        FieldRule("NAME"), FieldRule("ORD", numeric=True), FieldRule("TEXT"),
    ),
    "HELP_SECTION": (
        FieldRule("SECTID", numeric=True), FieldRule("ARTID", numeric=True), FieldRule("TOPICID", numeric=True),
        FieldRule("TOPICKEY"), FieldRule("KIND"), FieldRule("SOURCE"), FieldRule("CONFID"), FieldRule("SEVERITY"),
        FieldRule("NAME"), FieldRule("ORD", numeric=True), FieldRule("NLINES", numeric=True),
    ),
    "HELP_LINE": (
        FieldRule("LINEID", numeric=True), FieldRule("ARTID", numeric=True), FieldRule("TOPICKEY"), FieldRule("CATALOG"),
        FieldRule("TOPIC"), FieldRule("KIND"), FieldRule("SOURCE"), FieldRule("CONFID"), FieldRule("SEVERITY"),
        FieldRule("NAME"), FieldRule("ROLE"), FieldRule("LINE_NO", numeric=True), FieldRule("PART_NO", numeric=True), FieldRule("TEXT"),
    ),
}


def _blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _is_numeric(value: Any) -> bool:
    try:
        int(str(value).strip())
        return True
    except Exception:
        return False


def _is_logical(value: Any) -> bool:
    return str(value).strip().upper() in {"T", "F", "TRUE", "FALSE", "1", "0"}


def validate_rows_by_table(rows_by_table: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for table, rules in HELP_SCHEMA.items():
        rows = list(rows_by_table.get(table, []))
        if not rows:
            issues.append({"table": table, "field": "*", "issue": "missing_table_rows"})
            continue
        for idx, row in enumerate(rows, start=1):
            for rule in rules:
                value = row.get(rule.name)
                if rule.required and _blank(value):
                    issues.append({"table": table, "row": str(idx), "field": rule.name, "issue": "required_blank"})
                    continue
                if rule.numeric and not _is_numeric(value):
                    issues.append({"table": table, "row": str(idx), "field": rule.name, "issue": "required_numeric"})
                if rule.logical and not _is_logical(value):
                    issues.append({"table": table, "row": str(idx), "field": rule.name, "issue": "required_logical"})
    return issues
