#!/usr/bin/env python3
"""
Generate canonical runtime messaging catalog seed CSVs from the compiled
message registry.

Inputs:
  - src/help/helpdata_messages.cpp
  - src/help/message_catalog.cpp

Outputs:
  - dottalkpp/data/scripts/messaging/SYSTEM_MESSAGES_IMPORT_v1.csv
  - dottalkpp/data/scripts/messaging/SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv

Boundary:
  - Reads compiled MessageDef / MessageTextDef registries from source.
  - Preserves already-seeded runtime MSGIDs declared in message_catalog.cpp.
  - Allocates new stable numeric MSGIDs after the current seeded maximum.
  - Emits a full runtime-catalog snapshot for reviewed import/reset workflows.
  - Does not mutate DBF/CDX/LMDB artifacts directly.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import Iterable
from typing import List
from typing import Sequence
from typing import Tuple


MESSAGE_BLOCK_RE = re.compile(
    r"const std::vector<MessageDef>& all_messages\(\)\s*\{\s*"
    r"static const std::vector<MessageDef> messages = \{(?P<body>.*?)\n\s*\};\s*"
    r"return messages;\s*\}",
    re.DOTALL,
)

MESSAGE_ENTRY_RE = re.compile(
    r"\{\s*"
    r"MessageId::(?P<enum>[A-Za-z0-9_]+)\s*,\s*"
    r"\"(?P<key>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"\"(?P<owner>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"\"(?P<category>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"\"(?P<severity>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"(?P<text_literals>(?:\"(?:[^\"\\]|\\.)*\"\s*)+)"
    r"\}",
    re.DOTALL,
)

TEXT_BLOCK_RE = re.compile(
    r"const std::vector<MessageTextDef>& all_message_texts\(\)\s*\{\s*"
    r"static const std::vector<MessageTextDef> texts = \{(?P<body>.*?)\n\s*\};\s*"
    r"return texts;\s*\}",
    re.DOTALL,
)

TEXT_ENTRY_RE = re.compile(
    r"\{\s*"
    r"MessageId::(?P<enum>[A-Za-z0-9_]+)\s*,\s*"
    r"\"(?P<locale>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"(?P<text_literals>(?:\"(?:[^\"\\]|\\.)*\"\s*)+)"
    r"\}",
    re.DOTALL,
)

SEEDED_MESSAGE_ROW_RE = re.compile(
    r'\{\s*"(?P<msgid>\d+)"\s*,\s*"(?P<symbol>[A-Z0-9_]+)"\s*,\s*"(?P<enum>[A-Za-z0-9_]+)"\s*,',
    re.DOTALL,
)

MESSAGES_FIELDS = [
    "MSGID",
    "SYMBOL",
    "ENUMNAME",
    "FACILITY",
    "OWNER",
    "CATEGORY",
    "SEVERITY",
    "STATUS",
    "SRC",
]

TEXT_FIELDS = [
    "MSGID",
    "SYMBOL",
    "ENUMNAME",
    "LOCALE",
    "MSGLOCALE",
    "SYMBOLLOC",
    "TEXT",
    "TXTHASH",
    "STATUS",
    "SRC",
]

DEFAULT_STATUS = "ACTIVE"
DEFAULT_SRC = "src/help/helpdata_messages.cpp"
DEFAULT_LOCALE = "en-US"


@dataclass(frozen=True)
class MessageRow:
    enum_name: str
    key: str
    owner: str
    category: str
    severity: str
    text: str


@dataclass(frozen=True)
class MessageTextRow:
    enum_name: str
    locale: str
    text: str


def decode_cpp_string(raw: str) -> str:
    return bytes(raw, "utf-8").decode("unicode_escape")


def decode_concatenated_cpp_strings(raw: str) -> str:
    parts = re.findall(r"\"((?:[^\"\\]|\\.)*)\"", raw, re.DOTALL)
    return "".join(decode_cpp_string(part) for part in parts)


def extract_messages(source_text: str) -> List[MessageRow]:
    block_match = MESSAGE_BLOCK_RE.search(source_text)
    if not block_match:
        raise RuntimeError("Unable to locate all_messages() registry block.")

    body = block_match.group("body")
    rows: List[MessageRow] = []
    for match in MESSAGE_ENTRY_RE.finditer(body):
        rows.append(
            MessageRow(
                enum_name=match.group("enum"),
                key=decode_cpp_string(match.group("key")),
                owner=decode_cpp_string(match.group("owner")),
                category=decode_cpp_string(match.group("category")),
                severity=decode_cpp_string(match.group("severity")),
                text=decode_concatenated_cpp_strings(match.group("text_literals")),
            )
        )

    if not rows:
        raise RuntimeError("No MessageDef rows parsed from all_messages().")

    declared = len(re.findall(r"MessageId::[A-Za-z0-9_]+", body))
    if declared != len(rows):
        raise RuntimeError(
            f"Parsed {len(rows)} MessageDef rows but found {declared} MessageId tokens; parser drift suspected."
        )
    return rows


def extract_message_texts(source_text: str) -> List[MessageTextRow]:
    block_match = TEXT_BLOCK_RE.search(source_text)
    if not block_match:
        raise RuntimeError("Unable to locate all_message_texts() registry block.")

    body = block_match.group("body")
    rows: List[MessageTextRow] = []
    for match in TEXT_ENTRY_RE.finditer(body):
        rows.append(
            MessageTextRow(
                enum_name=match.group("enum"),
                locale=decode_cpp_string(match.group("locale")),
                text=decode_concatenated_cpp_strings(match.group("text_literals")),
            )
        )

    if not rows:
        raise RuntimeError("No MessageTextDef rows parsed from all_message_texts().")

    declared = len(re.findall(r"\{\s*MessageId::[A-Za-z0-9_]+", body))
    if declared != len(rows):
        raise RuntimeError(
            f"Parsed {len(rows)} MessageTextDef rows but found {declared} entry starts; parser drift suspected."
        )
    return rows


def extract_seeded_ids(message_catalog_text: str) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for match in SEEDED_MESSAGE_ROW_RE.finditer(message_catalog_text):
        symbol = match.group("symbol")
        msgid = int(match.group("msgid"))
        prior = mapping.get(symbol)
        if prior is not None and prior != msgid:
            raise RuntimeError(f"Conflicting seeded MSGID for {symbol}: {prior} vs {msgid}")
        mapping[symbol] = msgid

    if not mapping:
        raise RuntimeError("No seeded runtime MSGIDs found in message_catalog.cpp.")
    return mapping


def allocate_msgids(messages: Sequence[MessageRow],
                    seeded_ids: Dict[str, int]) -> Dict[str, int]:
    assigned = dict(seeded_ids)
    used = set(assigned.values())
    next_id = max(used) + 1 if used else 1

    for row in messages:
        if row.key in assigned:
            continue
        while next_id in used:
            next_id += 1
        assigned[row.key] = next_id
        used.add(next_id)
        next_id += 1

    return assigned


def ensure_default_locale_rows(messages: Sequence[MessageRow],
                               texts: Sequence[MessageTextRow]) -> List[MessageTextRow]:
    rows = list(texts)
    existing = {(row.enum_name, row.locale) for row in rows}
    for msg in messages:
        key = (msg.enum_name, DEFAULT_LOCALE)
        if key not in existing:
            rows.append(MessageTextRow(msg.enum_name, DEFAULT_LOCALE, msg.text))
            existing.add(key)
    return rows


def build_runtime_rows(messages: Sequence[MessageRow],
                       texts: Sequence[MessageTextRow],
                       msgids: Dict[str, int]) -> Tuple[List[dict], List[dict], Dict[str, List[str]]]:
    message_by_enum = {row.enum_name: row for row in messages}
    text_rows = ensure_default_locale_rows(messages, texts)

    runtime_messages: List[dict] = []
    for row in messages:
        msgid = msgids[row.key]
        runtime_messages.append(
            {
                "MSGID": msgid,
                "SYMBOL": row.key,
                "ENUMNAME": row.enum_name,
                "FACILITY": row.owner,
                "OWNER": row.owner,
                "CATEGORY": row.category,
                "SEVERITY": row.severity,
                "STATUS": DEFAULT_STATUS,
                "SRC": DEFAULT_SRC,
            }
        )

    runtime_texts: List[dict] = []
    locales_by_symbol: Dict[str, List[str]] = {}
    seen_text_keys = set()
    for row in text_rows:
        message = message_by_enum.get(row.enum_name)
        if message is None:
            raise RuntimeError(f"Text row references unknown MessageId enum: {row.enum_name}")

        key = (message.key, row.locale)
        if key in seen_text_keys:
            raise RuntimeError(f"Duplicate text row for symbol={message.key} locale={row.locale}")
        seen_text_keys.add(key)

        msgid = msgids[message.key]
        runtime_texts.append(
            {
                "MSGID": msgid,
                "SYMBOL": message.key,
                "ENUMNAME": row.enum_name,
                "LOCALE": row.locale,
                "MSGLOCALE": f"{msgid:010d}|{row.locale}",
                "SYMBOLLOC": f"{message.key}|{row.locale}",
                "TEXT": row.text,
                "TXTHASH": hashlib.sha256(row.text.encode("utf-8")).hexdigest(),
                "STATUS": DEFAULT_STATUS,
                "SRC": DEFAULT_SRC,
            }
        )
        locales_by_symbol.setdefault(message.key, []).append(row.locale)

    runtime_messages.sort(key=lambda row: int(row["MSGID"]))
    runtime_texts.sort(key=lambda row: (int(row["MSGID"]), row["LOCALE"]))
    for symbol in locales_by_symbol:
        locales_by_symbol[symbol] = sorted(set(locales_by_symbol[symbol]))

    return runtime_messages, runtime_texts, locales_by_symbol


def validate_lengths(runtime_messages: Sequence[dict], runtime_texts: Sequence[dict]) -> None:
    def check(field: str, value: str, limit: int, row_label: str) -> None:
        if len(value) > limit:
            raise RuntimeError(
                f"{row_label} field {field} exceeds limit {limit}: {len(value)}"
            )

    for row in runtime_messages:
        label = f"SYSTEM_MESSAGES[{row['SYMBOL']}]"
        check("SYMBOL", str(row["SYMBOL"]), 64, label)
        check("ENUMNAME", str(row["ENUMNAME"]), 64, label)
        check("FACILITY", str(row["FACILITY"]), 32, label)
        check("OWNER", str(row["OWNER"]), 64, label)
        check("CATEGORY", str(row["CATEGORY"]), 32, label)
        check("SEVERITY", str(row["SEVERITY"]), 16, label)
        check("STATUS", str(row["STATUS"]), 16, label)
        check("SRC", str(row["SRC"]), 32, label)

    for row in runtime_texts:
        label = f"SYSTEM_MESSAGE_TEXT[{row['SYMBOL']}|{row['LOCALE']}]"
        check("SYMBOL", str(row["SYMBOL"]), 64, label)
        check("ENUMNAME", str(row["ENUMNAME"]), 64, label)
        check("LOCALE", str(row["LOCALE"]), 16, label)
        check("MSGLOCALE", str(row["MSGLOCALE"]), 32, label)
        check("SYMBOLLOC", str(row["SYMBOLLOC"]), 96, label)
        check("TXTHASH", str(row["TXTHASH"]), 64, label)
        check("STATUS", str(row["STATUS"]), 16, label)
        check("SRC", str(row["SRC"]), 32, label)


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    helpdata_path = repo_root / "src" / "help" / "helpdata_messages.cpp"
    message_catalog_path = repo_root / "src" / "help" / "message_catalog.cpp"
    out_dir = repo_root / "dottalkpp" / "data" / "scripts" / "messaging"

    helpdata_text = helpdata_path.read_text(encoding="utf-8")
    message_catalog_text = message_catalog_path.read_text(encoding="utf-8")

    messages = extract_messages(helpdata_text)
    texts = extract_message_texts(helpdata_text)
    seeded_ids = extract_seeded_ids(message_catalog_text)
    msgids = allocate_msgids(messages, seeded_ids)
    runtime_messages, runtime_texts, locales_by_symbol = build_runtime_rows(messages, texts, msgids)
    validate_lengths(runtime_messages, runtime_texts)

    write_csv(out_dir / "SYSTEM_MESSAGES_IMPORT_v1.csv", MESSAGES_FIELDS, runtime_messages)
    write_csv(out_dir / "SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv", TEXT_FIELDS, runtime_texts)

    locale_counts: Dict[str, int] = {}
    for row in runtime_texts:
        locale = str(row["LOCALE"])
        locale_counts[locale] = locale_counts.get(locale, 0) + 1

    localized_symbols = sum(1 for values in locales_by_symbol.values() if len(values) > 1)
    print(
        "Generated runtime message catalog seed: "
        f"{len(runtime_messages)} message rows, "
        f"{len(runtime_texts)} text rows, "
        f"{localized_symbols} localized symbols, "
        f"locales={','.join(sorted(locale_counts))}"
    )
    for locale in sorted(locale_counts):
        print(f"  {locale}: {locale_counts[locale]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
