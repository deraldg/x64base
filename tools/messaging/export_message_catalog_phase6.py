#!/usr/bin/env python3
"""
DotTalk++ message catalog source export, Phase 6.

Report-only source-side exporter for the compiled message catalog in
src/help/helpdata_messages.*. This script writes review artifacts under
    docs/messaging/reports
and deliberately performs no DBF writes, no HELP DATA rebuild, no CMDHELPCHK
mutation, no source edits, and no runtime/catalog promotion.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class MessageRow:
    enum_name: str
    symbol: str
    owner: str
    category: str
    severity: str
    default_text: str


@dataclass(frozen=True)
class MessageTextRow:
    enum_name: str
    locale: str
    text: str


@dataclass(frozen=True)
class Issue:
    code: str
    message_key: str
    locale: str
    detail: str


_STRING = r'"(?:\\.|[^"\\])*"'
_CPP_STRING_RE = re.compile(_STRING)
_MESSAGE_DEF_RE = re.compile(
    r"\{\s*MessageId::(?P<enum>\w+)\s*,\s*"
    r"(?P<key>" + _STRING + r")\s*,\s*"
    r"(?P<owner>" + _STRING + r")\s*,\s*"
    r"(?P<category>" + _STRING + r")\s*,\s*"
    r"(?P<severity>" + _STRING + r")\s*,\s*"
    r"(?P<text>" + _STRING + r")\s*\}",
    re.DOTALL,
)
_MESSAGE_TEXT_RE = re.compile(
    r"\{\s*MessageId::(?P<enum>\w+)\s*,\s*"
    r"(?P<locale>" + _STRING + r")\s*,\s*"
    r"(?P<text>" + _STRING + r")\s*\}",
    re.DOTALL,
)
_PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def unquote_cpp_string(token: str) -> str:
    # The current catalog uses simple C++ string literals. unicode_escape is good
    # enough for escaped quotes/backslashes/newlines in this report-only exporter.
    inner = token[1:-1]
    return bytes(inner, "utf-8").decode("unicode_escape")


def csv_safe_text(text: str) -> str:
    return text.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def extract_section(source: str, function_name: str) -> str:
    marker = f"{function_name}()"
    pos = source.find(marker)
    if pos < 0:
        raise ValueError(f"Could not find {function_name}() in helpdata_messages.cpp")

    # Find the first "static const std::vector" after the function marker and
    # return through the matching "};". This avoids matching unrelated helpers.
    start = source.find("static const std::vector", pos)
    if start < 0:
        raise ValueError(f"Could not find static vector inside {function_name}()")
    end = source.find(";\n", start)
    if end < 0:
        raise ValueError(f"Could not find vector terminator inside {function_name}()")
    return source[start : end + 2]


def parse_messages(source: str) -> list[MessageRow]:
    section = extract_section(source, "all_messages")
    rows: list[MessageRow] = []
    for match in _MESSAGE_DEF_RE.finditer(section):
        rows.append(
            MessageRow(
                enum_name=match.group("enum"),
                symbol=unquote_cpp_string(match.group("key")),
                owner=unquote_cpp_string(match.group("owner")),
                category=unquote_cpp_string(match.group("category")),
                severity=unquote_cpp_string(match.group("severity")),
                default_text=unquote_cpp_string(match.group("text")),
            )
        )
    return rows


def parse_message_texts(source: str) -> list[MessageTextRow]:
    section = extract_section(source, "all_message_texts")
    rows: list[MessageTextRow] = []
    for match in _MESSAGE_TEXT_RE.finditer(section):
        rows.append(
            MessageTextRow(
                enum_name=match.group("enum"),
                locale=unquote_cpp_string(match.group("locale")),
                text=unquote_cpp_string(match.group("text")),
            )
        )
    return rows


def placeholders(text: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(text))


def validate(messages: list[MessageRow], texts: list[MessageTextRow]) -> list[Issue]:
    issues: list[Issue] = []
    by_enum: dict[str, MessageRow] = {}
    symbols: set[str] = set()

    for msg in messages:
        if not msg.enum_name:
            issues.append(Issue("EMPTY_MESSAGE_ENUM", msg.symbol, "", "Message has an empty enum name."))
        if not msg.symbol:
            issues.append(Issue("EMPTY_MESSAGE_SYMBOL", msg.symbol, "", "Message has an empty symbol."))
        if msg.enum_name in by_enum:
            issues.append(Issue("DUPLICATE_MESSAGE_ID", msg.symbol, "", f"Duplicate MessageId enum {msg.enum_name}."))
        by_enum[msg.enum_name] = msg
        if msg.symbol in symbols:
            issues.append(Issue("DUPLICATE_MESSAGE_SYMBOL", msg.symbol, "", "Duplicate SYSTEM_MESSAGES symbol."))
        symbols.add(msg.symbol)
        if not msg.category:
            issues.append(Issue("EMPTY_CATEGORY", msg.symbol, "", "Message category is empty."))
        if not msg.severity:
            issues.append(Issue("EMPTY_SEVERITY", msg.symbol, "", "Message severity is empty."))
        if not msg.default_text:
            issues.append(Issue("EMPTY_DEFAULT_TEXT", msg.symbol, "", "Default text is empty."))

    seen_text_pairs: set[tuple[str, str]] = set()
    texts_by_enum: dict[str, list[MessageTextRow]] = {}
    for text in texts:
        msg = by_enum.get(text.enum_name)
        key = msg.symbol if msg else text.enum_name
        if not msg:
            issues.append(Issue("ORPHAN_MESSAGE_TEXT", key, text.locale, "Text row references an unknown MessageId."))
        if not text.locale:
            issues.append(Issue("EMPTY_LOCALE", key, text.locale, "Text row has an empty locale."))
        if not text.text:
            issues.append(Issue("EMPTY_TEXT_TEMPLATE", key, text.locale, "Text template is empty."))
        pair = (text.enum_name, text.locale)
        if pair in seen_text_pairs:
            issues.append(Issue("DUPLICATE_TEXT_ROW", key, text.locale, "Duplicate MessageId + locale row."))
        seen_text_pairs.add(pair)
        texts_by_enum.setdefault(text.enum_name, []).append(text)

    locales = sorted({t.locale for t in texts if t.locale})
    for msg in messages:
        msg_texts = texts_by_enum.get(msg.enum_name, [])
        locales_for_msg = {t.locale for t in msg_texts}
        if "en-US" not in locales_for_msg:
            issues.append(Issue("MISSING_EN_US_TEXT", msg.symbol, "en-US", "Message has no en-US text row."))
        for locale in locales:
            if locale not in locales_for_msg:
                issues.append(Issue("MISSING_LOCALE_TEXT", msg.symbol, locale, "Message has no text row for this observed locale."))

        english = next((t for t in msg_texts if t.locale == "en-US"), None)
        if english is not None:
            expected = placeholders(english.text)
            for text in msg_texts:
                observed = placeholders(text.text)
                if observed != expected:
                    issues.append(
                        Issue(
                            "PLACEHOLDER_MISMATCH",
                            msg.symbol,
                            text.locale,
                            "Expected placeholders "
                            + ",".join(sorted(expected))
                            + "; observed "
                            + ",".join(sorted(observed))
                            + ".",
                        )
                    )
    return issues


def owner_to_facility(owner: str) -> str:
    if owner.startswith("SUBSYSTEM:"):
        return owner.split(":", 1)[1]
    if owner.startswith("COMMAND:"):
        return "COMMAND"
    return owner or "GLOBAL"


def write_csv(path: pathlib.Path, fieldnames: list[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_markdown_report(
    path: pathlib.Path,
    messages: list[MessageRow],
    texts: list[MessageTextRow],
    issues: list[Issue],
    locales: list[str],
) -> None:
    now = _dt.datetime.now().isoformat(timespec="seconds")
    status = "GREEN" if not issues else "REVIEW"
    lines: list[str] = []
    lines.append("# DotTalk++ Message Catalog Phase 6 Source Export")
    lines.append("")
    lines.append(f"Generated: `{now}`")
    lines.append("")
    lines.append(f"Status: `{status}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Messages: {len(messages)}")
    lines.append(f"- Text rows: {len(texts)}")
    lines.append(f"- Locales: {', '.join(locales)}")
    lines.append(f"- Validation issues: {len(issues)}")
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append("This export is source/report only. It writes review artifacts under `docs/messaging/reports` and performs no DBF writes, HELP DATA rebuild, CMDHELPCHK mutation, source-mining mutation, runtime execution, or catalog promotion.")
    lines.append("")
    lines.append("## SYSTEM_MESSAGES preview")
    lines.append("")
    lines.append("| SYMBOL | ENUM_NAME | OWNER_SUBSYSTEM | CATEGORY | SEVERITY |")
    lines.append("|---|---|---|---|---|")
    for msg in messages:
        lines.append(f"| {msg.symbol} | {msg.enum_name} | {msg.owner} | {msg.category} | {msg.severity} |")
    lines.append("")
    lines.append("## SYSTEM_MESSAGE_TEXT preview")
    lines.append("")
    lines.append("| SYMBOL | LOCALES |")
    lines.append("|---|---|")
    by_enum: dict[str, set[str]] = {}
    symbol_by_enum = {m.enum_name: m.symbol for m in messages}
    for text in texts:
        by_enum.setdefault(text.enum_name, set()).add(text.locale)
    for msg in messages:
        lines.append(f"| {msg.symbol} | {', '.join(sorted(by_enum.get(msg.enum_name, set())))} |")
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    if not issues:
        lines.append("No validation issues found.")
    else:
        lines.append("| CODE | MESSAGE_KEY | LOCALE | DETAIL |")
        lines.append("|---|---|---|---|")
        for issue in issues:
            lines.append(f"| {issue.code} | {issue.message_key} | {issue.locale} | {issue.detail} |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export DotTalk++ message catalog source reports.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    parser.add_argument("--out-dir", default="docs/messaging/reports", help="Output directory relative to repo root.")
    args = parser.parse_args(argv)

    repo = pathlib.Path(args.repo_root).resolve()
    src = repo / "src" / "help" / "helpdata_messages.cpp"
    if not src.exists():
        print(f"ERROR: missing source file: {src}", file=sys.stderr)
        return 2

    source = src.read_text(encoding="utf-8")
    messages = parse_messages(source)
    texts = parse_message_texts(source)
    issues = validate(messages, texts)
    locales = sorted({t.locale for t in texts if t.locale})
    out_dir = (repo / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    symbol_by_enum = {m.enum_name: m.symbol for m in messages}

    write_csv(
        out_dir / "message_catalog_phase6_system_messages_v1.csv",
        ["MESSAGE_ID", "SYMBOL", "ENUM_NAME", "FACILITY", "OWNER_SUBSYSTEM", "CATEGORY", "SEVERITY", "DEFAULT_LOCALE", "STATUS", "DEFAULT_TEXT"],
        (
            {
                "MESSAGE_ID": str(i + 1),
                "SYMBOL": msg.symbol,
                "ENUM_NAME": msg.enum_name,
                "FACILITY": owner_to_facility(msg.owner),
                "OWNER_SUBSYSTEM": msg.owner,
                "CATEGORY": msg.category,
                "SEVERITY": msg.severity,
                "DEFAULT_LOCALE": "en-US",
                "STATUS": "SOURCE_COMPILED",
                "DEFAULT_TEXT": csv_safe_text(msg.default_text),
            }
            for i, msg in enumerate(messages)
        ),
    )

    message_index = {msg.enum_name: str(i + 1) for i, msg in enumerate(messages)}
    write_csv(
        out_dir / "message_catalog_phase6_system_message_text_v1.csv",
        ["MESSAGE_ID", "SYMBOL", "ENUM_NAME", "LOCALE", "TEXT_TEMPLATE", "TRANSLATION_STATUS", "SOURCE"],
        (
            {
                "MESSAGE_ID": message_index.get(text.enum_name, ""),
                "SYMBOL": symbol_by_enum.get(text.enum_name, text.enum_name),
                "ENUM_NAME": text.enum_name,
                "LOCALE": text.locale,
                "TEXT_TEMPLATE": csv_safe_text(text.text),
                "TRANSLATION_STATUS": "SEED_REVIEW",
                "SOURCE": "src/help/helpdata_messages.cpp",
            }
            for text in texts
        ),
    )

    write_csv(
        out_dir / "message_catalog_phase6_validation_v1.csv",
        ["CODE", "MESSAGE_KEY", "LOCALE", "DETAIL"],
        (
            {"CODE": issue.code, "MESSAGE_KEY": issue.message_key, "LOCALE": issue.locale, "DETAIL": issue.detail}
            for issue in issues
        ),
    )

    write_csv(
        out_dir / "message_catalog_phase6_status_summary_v1.csv",
        ["STATUS", "MESSAGES", "TEXT_ROWS", "LOCALES", "VALIDATION_ISSUES", "BOUNDARY"],
        [
            {
                "STATUS": "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN" if not issues else "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_REVIEW",
                "MESSAGES": str(len(messages)),
                "TEXT_ROWS": str(len(texts)),
                "LOCALES": ";".join(locales),
                "VALIDATION_ISSUES": str(len(issues)),
                "BOUNDARY": "REPORT_ONLY_NO_DBF_NO_HELPDATA_NO_CMDHELPCHK_NO_SOURCE_MINING_NO_CATALOG_PROMOTION",
            }
        ],
    )

    write_csv(
        out_dir / "message_catalog_phase6_boundary_ledger_v1.csv",
        ["PROTECTED_SYSTEM", "MUTATION_ALLOWED", "OBSERVED_MUTATION", "DETAIL"],
        [
            {"PROTECTED_SYSTEM": "DBF_CATALOGS", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "No DBF tables created, opened for write, or promoted."},
            {"PROTECTED_SYSTEM": "HELP_DATA", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "No HELP DATA rebuild or mutation."},
            {"PROTECTED_SYSTEM": "CMDHELPCHK", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "No CMDHELPCHK mutation."},
            {"PROTECTED_SYSTEM": "SOURCE_MINING", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "No source-mining mutation."},
            {"PROTECTED_SYSTEM": "SOURCE_CODE", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "Script reads src/help/helpdata_messages.cpp only; no source edits."},
            {"PROTECTED_SYSTEM": "RUNTIME_EXECUTION", "MUTATION_ALLOWED": "0", "OBSERVED_MUTATION": "0", "DETAIL": "No DotTalk++ runtime execution required."},
        ],
    )

    write_markdown_report(
        out_dir / "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_REPORT.md",
        messages,
        texts,
        issues,
        locales,
    )

    print("MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_GREEN" if not issues else "MESSAGE_CATALOG_PHASE6_SOURCE_EXPORT_REVIEW")
    print(f"  messages: {len(messages)}")
    print(f"  text rows: {len(texts)}")
    print(f"  locales: {', '.join(locales)}")
    print(f"  validation issues: {len(issues)}")
    print(f"  reports: {out_dir}")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
