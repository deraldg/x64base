#!/usr/bin/env python3
"""command_catalog_sync.py — keep the website command catalog honest to source.

The website page `content/docs/dottalk/command-catalog.mdx` is a *derivative* of
the engine's central shell command registry (`src/cli/shell_commands.cpp`) plus
the per-command `@dottalk.usage v1` blocks. It drifts whenever commands are
registered, renamed, or removed and the page is not regenerated — which is
exactly what happened when REGRESSION/EXPORTFUNCTIONS/SCX (added 2026-07-16) and
CONCAT/STRCAT/EXITS/HANUKKAH never reached the page, while REPLACE_MULTI/SNX
lingered after removal.

This tool has two modes:

  check  Validate an existing catalog page against current source. Fails (exit 2)
         if the catalog's command set != the registry, if the snapshot counts do
         not match the table, or if any two rows are joined onto one physical
         line (a `||` rendering defect). This is the push-checklist drift gate;
         its correctness does NOT depend on reproducing summary text.

  emit   Re-derive a full catalog page from source (best-effort: names are
         authoritative from the registry; category/status/summary come from the
         matched `@dottalk.usage` block, else a registered-only fallback row).

Anchor contract: the maintained page is identified by the marker line
`Diagram attachment: \`DIAG-CMDAUTH-004\`` and the `Source extraction snapshot:`
line. `check` requires both to be present so the tool refuses to validate the
wrong file.

Usage:
  python command_catalog_sync.py check --source-root D:/code/ccode \
      --catalog D:/dev/x64base-site/content/docs/dottalk/command-catalog.mdx
  python command_catalog_sync.py emit  --source-root D:/code/ccode --out <path>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)
ANCHOR_DIAGRAM = "DIAG-CMDAUTH-004"
SNAPSHOT_RE = re.compile(
    r"Source extraction snapshot: `(?P<keys>\d+)` registered command keys "
    r"and `(?P<parsed>\d+)` parsed usage contract blocks\."
)
REGISTRY_ADD_RE = re.compile(r'registry\(\)\.add\("([^"]+)"')
ROW_RE = re.compile(r"^\| `(?P<cmd>[^`]+)` \|")
FALLBACK_TEXT = (
    "Registered in the central shell command registry; no parsed "
    "@dottalk.usage block was matched by this website extraction pass."
)
FALLBACK_SOURCE = "src/cli/shell_commands.cpp"

# Function catalog (parallel surface): core functions come from the FunctionDoc
# table in src/cli/expr/function_catalog.cpp; student/extension functions
# self-register from src/ext/fn via register_builtin_fn(...).
FN_DOC_RE = re.compile(r'FunctionDoc\{\s*"([^"]+)"\s*,\s*\{([^}]*)\}', re.S)
FN_SELFREG_RE = re.compile(r'register_builtin_fn\(\{\s*"([^"]+)"')
FN_SNAPSHOT_RE = re.compile(
    r"`(\d+)` core documented expression functions"
    r"(?:, plus `(\d+)` self-registering)?"
)


# --------------------------------------------------------------------------- #
# source extraction
# --------------------------------------------------------------------------- #
def registry_keys(source_root: Path) -> list[str]:
    text = (source_root / "src/cli/shell_commands.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    return sorted(set(REGISTRY_ADD_RE.findall(text)))


def _norm(name: str) -> str:
    return name.upper().replace(" ", "").replace("_", "")


def _md_cell(text: str) -> str:
    """Make free text safe inside a Markdown table cell: escape the pipe and the
    angle brackets that appear in usage placeholders like `<table>`/`<expr>`
    (raw `<...>` is rejected by the website's public-content guard)."""
    return text.replace("|", r"\|").replace("<", "&lt;").replace(">", "&gt;")


def usage_blocks(source_root: Path) -> dict[str, dict[str, str]]:
    """Map normalized command name -> {category,status,summary,source}."""
    out: dict[str, dict[str, str]] = {}
    src = source_root / "src"
    for path in sorted(src.rglob("*.cpp")) + sorted(src.rglob("*.hpp")):
        # utf-8-sig strips a leading BOM (present on some files, which otherwise
        # hides the first @dottalk.usage block); normalize CRLF/CR to LF so the
        # line-anchored regexes match regardless of line endings.
        text = path.read_text(encoding="utf-8-sig", errors="replace").replace(
            "\r\n", "\n"
        ).replace("\r", "\n")
        # Stop each block at the NEXT usage marker too, so adjacent blocks
        # separated only by comment/blank lines (e.g. LOOP then ENDLOOP) are not
        # merged into one (which would hide the second command).
        for block in re.finditer(
            r"(?ms)^// @dottalk\.usage.*?(?=^// @dottalk\.usage|^\s*(?!//)\S|\Z)",
            text,
        ):
            b = block.group(0)
            cmd = _field(b, "command")
            if not cmd:
                continue
            category = _field(b, "category")
            status = _field(b, "status")
            summary = _summary(b)
            if not (category and status and summary):
                continue
            rel = path.relative_to(source_root).as_posix().replace("/", "\\")
            # a block may own several names: "A / B"
            for name in (n.strip() for n in cmd.split("/")):
                if name:
                    out.setdefault(_norm(name), {
                        "category": category,
                        "status": status,
                        "summary": summary,
                        "source": rel,
                    })
    return out


def syscmd_commands(path: Path) -> tuple[set[str], dict[str, str]]:
    """Parse a SYSCMD DBF export (CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE).

    Returns (normalized active-command names, {normalized: raw CAN_NAME}). Only
    TYPE==command and ACTIVE truthy rows count; the website catalog is a superset
    of the registry, so every ACTIVE documented command must appear in it.
    """
    import csv

    active: set[str] = set()
    raw: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("TYPE") or "").strip().lower() != "command":
                continue
            if (row.get("ACTIVE") or "").strip().lower() not in ("t", "true", "1", "yes"):
                continue
            name = (row.get("CAN_NAME") or "").strip()
            if name:
                active.add(_norm(name))
                raw[_norm(name)] = name
    return active, raw


def _field(block: str, key: str) -> str:
    m = re.search(rf"(?m)^// {key}:\s*(.+?)\s*$", block)
    return m.group(1).strip() if m else ""


def _summary(block: str) -> str:
    # Handles both the inline form (`// summary: text`) and the multi-line form
    # (`// summary:` followed by indented `//   text` continuation lines).
    lines = block.splitlines()
    grab = False
    parts: list[str] = []
    for ln in lines:
        if not grab:
            head = re.match(r"^// summary:\s*(.*?)\s*$", ln)
            if head:
                grab = True
                if head.group(1):
                    parts.append(head.group(1))
            continue
        if re.match(r"^//\s*$", ln) or re.match(r"^// [a-z-]+:", ln):
            break
        parts.append(re.sub(r"^//\s+", "", ln).rstrip())
    return " ".join(p for p in parts if p).strip()


# --------------------------------------------------------------------------- #
# catalog parsing
# --------------------------------------------------------------------------- #
def parse_catalog(catalog: Path) -> dict:
    text = catalog.read_text(encoding="utf-8", errors="replace")
    snap = SNAPSHOT_RE.search(text)
    rows: list[str] = []
    joined: list[int] = []
    fallback = 0
    for i, ln in enumerate(text.splitlines(), 1):
        if not ln.startswith("| `"):
            continue
        m = ROW_RE.match(ln)
        if m:
            rows.append(m.group("cmd"))
        # a second "| `NAME` |" later on the same physical line == joined rows
        if ln.count("| `") > 1 and "||" in ln:
            joined.append(i)
        if FALLBACK_TEXT in ln:
            fallback += 1
    return {
        "has_anchor": ANCHOR_DIAGRAM in text,
        "has_snapshot": snap is not None,
        "snap_keys": int(snap.group("keys")) if snap else None,
        "snap_parsed": int(snap.group("parsed")) if snap else None,
        "rows": rows,
        "joined_lines": joined,
        "fallback": fallback,
    }


# --------------------------------------------------------------------------- #
# modes
# --------------------------------------------------------------------------- #
def check(source_root: Path, catalog: Path, syscmd: Path | None = None) -> int:
    keys = registry_keys(source_root)
    cat = parse_catalog(catalog)
    findings: list[str] = []

    if not cat["has_anchor"]:
        findings.append(f"MISSING_ANCHOR: `{ANCHOR_DIAGRAM}` not found — wrong file?")
    if not cat["has_snapshot"]:
        findings.append("MISSING_SNAPSHOT_LINE")
    if cat["joined_lines"]:
        findings.append(f"JOINED_ROWS at lines {cat['joined_lines']} (|| rendering defect)")

    # Registry membership uses case-only equality (preserves the distinct
    # `ERROR STATUS` vs `ERROR_STATUS` keys); the SYSCMD cross-check uses the
    # space/underscore-insensitive _norm because SYSCMD spells e.g. `SET CASE`
    # where the registry/catalog write `SETCASE`.
    rows = cat["rows"]
    keys_ci = {k.upper() for k in keys}
    rows_ci = {c.upper() for c in rows}
    rows_norm = {_norm(c) for c in rows}

    # Optional second documentation surface: the SYSCMD DBF export. The catalog
    # should be a superset of both the central registry AND every ACTIVE command
    # SYSCMD documents (that is what caught REGRESSION — SYSCMD had it, the
    # website did not; and PREDHELP/STUDENT* — self-registered commands the
    # registry-only extraction cannot see but the DBF documents).
    documented: set[str] = set()
    raw: dict[str, str] = {}
    if syscmd is not None:
        documented, raw = syscmd_commands(syscmd)

    missing = sorted(k for k in keys if k.upper() not in rows_ci)
    if missing:
        findings.append(f"MISSING_FROM_CATALOG ({len(missing)}): {', '.join(missing)}")

    # Catalog entries not in the central registry are legitimate when the runtime
    # SYSCMD catalog documents them (self-registered extension/student commands);
    # an entry in neither is a true orphan defect.
    extra = sorted({c for c in rows if c.upper() not in keys_ci})
    self_registered = [c for c in extra if _norm(c) in documented]
    orphan = [c for c in extra if _norm(c) not in documented]
    if orphan:
        findings.append(f"NOT_IN_REGISTRY ({len(orphan)}): {', '.join(orphan)}")

    # Counts. The catalog is registry rows + any self-registered rows; the
    # snapshot's "registered command keys" number tracks the registry rows only.
    total = len(rows)
    registry_rows = sum(1 for c in rows if c.upper() in keys_ci)
    parsed = total - cat["fallback"]
    if cat["snap_keys"] is not None and cat["snap_keys"] != registry_rows:
        findings.append(f"SNAPSHOT_KEYS {cat['snap_keys']} != registry rows {registry_rows}")
    if cat["snap_parsed"] is not None and cat["snap_parsed"] != parsed:
        findings.append(f"SNAPSHOT_PARSED {cat['snap_parsed']} != non-fallback rows {parsed}")

    xcheck_line = ""
    if syscmd is not None:
        doc_missing = sorted(raw[n] for n in documented - rows_norm)
        if doc_missing:
            findings.append(
                f"DOCUMENTED_NOT_IN_CATALOG ({len(doc_missing)}): {', '.join(doc_missing)} "
                "— SYSCMD DBF documents these active commands but the website omits them"
            )
        xcheck_line = f" syscmd_active={len(documented)} self_registered={len(self_registered)}"

    status = "PASS" if not findings else "FAIL"
    print(f"command_catalog check={status} registry_keys={len(keys)} "
          f"catalog_rows={total} parsed={parsed} fallback={cat['fallback']}{xcheck_line}")
    for f in findings:
        print(f"  - {f}")
    return 0 if status == "PASS" else 2


def emit(source_root: Path, out: Path) -> int:
    keys = registry_keys(source_root)
    blocks = usage_blocks(source_root)
    rows: list[str] = []
    parsed = 0
    for key in sorted(keys):
        b = blocks.get(_norm(key))
        if b:
            parsed += 1
            rows.append(
                f"| `{key}` | {_md_cell(b['category'])} | {_md_cell(b['status'])} | "
                f"{_md_cell(b['summary'])} | `{b['source']}` |"
            )
        else:
            rows.append(
                f"| `{key}` | registered | registered | {FALLBACK_TEXT} | `{FALLBACK_SOURCE}` |"
            )
    header = _HEADER.format(keys=len(keys), parsed=parsed)
    table = "| Command | Category | Status | Summary | Source |\n| --- | --- | --- | --- | --- |\n" + "\n".join(rows) + "\n"
    out.write_text(header + table, encoding="utf-8")
    print(f"command_catalog emit -> {out} keys={len(keys)} parsed={parsed} fallback={len(keys)-parsed}")
    return 0


_HEADER = """---
title: "Command Catalog"
description: "Source-derived DotTalk++ command catalog produced from the central registry and @dottalk.usage contracts."
---

This page is a website derivative of the vertical documentation system. The command names come from `src/cli/shell_commands.cpp`; summaries and status fields come from parsed `@dottalk.usage v1` blocks when available.

Publication rule: runtime/source truth wins over this page. This page should be regenerated or reviewed when command registration, HELP, CMDHELP, or usage contracts change.

## Canonical diagram

Diagram attachment: `DIAG-CMDAUTH-004`

![Command reference harvest](/images/dottalk/command_reference_harvest_v1.svg)

Canonical source:
`docs/manuals/assets/diagrams/command_reference_harvest_v1.svg`

Source extraction snapshot: `{keys}` registered command keys and `{parsed}` parsed usage contract blocks.

## Source-Derived Commands

"""


def function_core(source_root: Path) -> dict[str, list[str]]:
    """Core expression functions from function_catalog.cpp -> {NAME: [aliases]}."""
    text = (source_root / "src/cli/expr/function_catalog.cpp").read_text(
        encoding="utf-8", errors="replace"
    )
    core: dict[str, list[str]] = {}
    for m in FN_DOC_RE.finditer(text):
        aliases = [a.strip().strip('"') for a in m.group(2).split(",") if a.strip()]
        core[m.group(1).upper()] = [a.upper() for a in aliases]
    return core


def function_self_registered(source_root: Path) -> set[str]:
    """Student/extension functions that self-register from src/ext/fn."""
    names: set[str] = set()
    fn_dir = source_root / "src/ext/fn"
    if fn_dir.is_dir():
        for path in sorted(fn_dir.rglob("*.cpp")):
            text = path.read_text(encoding="utf-8", errors="replace")
            names.update(n.upper() for n in FN_SELFREG_RE.findall(text))
    return names


def sysfunc_names(path: Path) -> set[str]:
    import csv

    out: set[str] = set()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            name = (row.get("CAN_NAME") or "").strip().strip('"')
            if name:
                out.add(name.upper())
    return out


def parse_function_catalog(catalog: Path) -> dict:
    text = catalog.read_text(encoding="utf-8", errors="replace")
    snap = FN_SNAPSHOT_RE.search(text)
    functions: dict[str, set[str]] = {}
    for ln in text.splitlines():
        if not ln.startswith("| `"):
            continue
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        name = parts[0].strip("`").strip().upper()
        aliases = set()
        if len(parts) > 1 and parts[1].replace("`", "").strip():
            aliases = {a.upper() for a in re.split(r"[ ,]+", parts[1].replace("`", "").strip()) if a}
        functions[name] = aliases
    return {
        "functions": functions,
        "snap_core": int(snap.group(1)) if snap else None,
        "snap_self": int(snap.group(2)) if snap and snap.group(2) else None,
    }


def fn_check(source_root: Path, catalog: Path, sysfunc: Path | None = None) -> int:
    core = function_core(source_root)
    self_reg = function_self_registered(source_root)
    fc = parse_function_catalog(catalog)
    web = fc["functions"]
    web_aliases = {a for al in web.values() for a in al}
    core_aliases = {a for al in core.values() for a in al}
    findings: list[str] = []

    core_missing = sorted(n for n in core if n not in web)
    if core_missing:
        findings.append(f"CORE_MISSING ({len(core_missing)}): {', '.join(core_missing)}")
    self_missing = sorted(n for n in self_reg if n not in web)
    if self_missing:
        findings.append(f"SELF_REGISTERED_MISSING ({len(self_missing)}): {', '.join(self_missing)}")
    orphan = sorted(
        n for n in web if n not in core and n not in self_reg and n not in core_aliases
    )
    if orphan:
        findings.append(f"NOT_IN_SOURCE ({len(orphan)}): {', '.join(orphan)}")

    if fc["snap_core"] is not None and fc["snap_core"] != len(core):
        findings.append(f"SNAPSHOT_CORE {fc['snap_core']} != function_catalog.cpp core {len(core)}")
    if fc["snap_self"] is not None and fc["snap_self"] != len(self_reg):
        findings.append(f"SNAPSHOT_SELF {fc['snap_self']} != self-registered fns {len(self_reg)}")

    xline = ""
    if sysfunc is not None:
        sysnames = sysfunc_names(sysfunc)
        documented = set(web) | web_aliases
        undoc = sorted(sysnames - documented)
        if undoc:
            findings.append(
                f"SYSFUNC_NOT_ON_SITE ({len(undoc)}): {', '.join(undoc)} "
                "— SYSFUNC DBF lists these but the website function catalog omits them"
            )
        xline = f" sysfunc={len(sysnames)}"

    status = "PASS" if not findings else "FAIL"
    print(f"function_catalog check={status} core={len(core)} "
          f"self_registered={len(self_reg)} website_rows={len(web)}{xline}")
    for f in findings:
        print(f"  - {f}")
    return 0 if status == "PASS" else 2


# --------------------------------------------------------------------------- #
# error-codes + messaging/localization surfaces
# --------------------------------------------------------------------------- #
ERR_CODE_RE = re.compile(
    r"code\s+(\w+)\s*\(\s*\)[^{]*\{\s*return\s+make_code\(\s*"
    r"severity::(\w+)\s*,\s*facility::(\w+)\s*,\s*(0x[0-9A-Fa-f]+)\s*\)",
    re.S,
)
ERR_MSG_RE = re.compile(r'case\s+(\w+)\(\)\.value\s*:\s*return\s+"([^"]*)"')
ERR_ROW_RE = re.compile(
    r"^\|\s*`([a-z0-9]+/0x[0-9A-Fa-f]+)`\s*\|\s*`([A-Za-z0-9_]+)`[^|]*\|\s*"
    r"(success|warning|error)\s*\|\s*(.+?)\s*\|\s*$"
)


def error_codes_source(source_root: Path) -> dict[str, dict[str, str]]:
    """Canonical codes from the error header/impl -> {identity: {symbol,severity,message}}."""
    codes: dict[str, dict[str, str]] = {}
    messages: dict[str, str] = {}
    for rel in ("include/xbase_error_codes.hpp", "src/cli/xbase_error_codes.cpp"):
        p = source_root / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace").replace("\r\n", "\n")
        for sym, sev, fac, num in ERR_CODE_RE.findall(text):
            identity = f"{fac}/0x{int(num, 16):04X}"
            codes.setdefault(identity, {"symbol": sym, "severity": sev, "message": ""})
        for sym, msg in ERR_MSG_RE.findall(text):
            # the header/impl has two switches keyed by the same case labels: the
            # human-message switch (kept) and the symbol-name switch that returns
            # tokens like "E_NO_TABLE_OPEN" (skipped). First human text wins.
            if re.fullmatch(r"[EW]_[A-Z0-9_]+", msg):
                continue
            messages.setdefault(sym, msg)
    for identity, rec in codes.items():
        rec["message"] = messages.get(rec["symbol"], "")
    return codes


def err_check(source_root: Path, page: Path) -> int:
    src = error_codes_source(source_root)
    text = page.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    if "DIAG-ERRCODE-010" not in text:
        findings.append("MISSING_ANCHOR: `DIAG-ERRCODE-010` not found — wrong file?")
    page_rows: dict[str, dict[str, str]] = {}
    for ln in text.splitlines():
        m = ERR_ROW_RE.match(ln)
        if m:
            ident, sym, sev, msg = m.groups()
            page_rows[ident.lower()] = {"symbol": sym, "severity": sev, "message": msg.strip()}

    src_ci = {k.lower(): v for k, v in src.items()}
    missing = sorted(k for k in src_ci if k not in page_rows)
    extra = sorted(k for k in page_rows if k not in src_ci)
    if missing:
        findings.append(f"MISSING_FROM_PAGE ({len(missing)}): {', '.join(missing)}")
    if extra:
        findings.append(f"NOT_IN_SOURCE ({len(extra)}): {', '.join(extra)}")
    for ident in sorted(src_ci.keys() & page_rows.keys()):
        s, pg = src_ci[ident], page_rows[ident]
        if s["severity"] != pg["severity"]:
            findings.append(f"SEVERITY_MISMATCH {ident}: source={s['severity']} page={pg['severity']}")
        if s["message"] and s["message"] != pg["message"]:
            findings.append(f"MESSAGE_MISMATCH {ident}: source={s['message']!r} page={pg['message']!r}")

    status = "PASS" if not findings else "FAIL"
    print(f"error_codes check={status} source_codes={len(src)} page_rows={len(page_rows)}")
    for f in findings:
        print(f"  - {f}")
    return 0 if status == "PASS" else 2


def locale_source(source_root: Path) -> set[str]:
    """Authoritative locale set: the REGRESSION LANGUAGE proof list + en-US base."""
    locales = {"en-US"}
    p = source_root / "src/cli/cmd_regression.cpp"
    if p.exists():
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        for m in re.finditer(r"\b([a-z]{2}(?:/[a-z]{2}){2,})\b", text):
            locales.update(m.group(1).split("/"))
    return locales


def loc_check(source_root: Path, page: Path) -> int:
    src = locale_source(source_root)
    text = page.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    if "DIAG-MSGLOC-011" not in text:
        findings.append("MISSING_ANCHOR: `DIAG-MSGLOC-011` not found — wrong file?")
    page_locales = {
        m.group(1) for m in re.finditer(r"^\|\s*`([A-Za-z]{2}(?:-[A-Za-z]{2})?)`\s*\|", text, re.M)
    }
    missing = sorted(src - page_locales)
    extra = sorted(page_locales - src)
    if missing:
        findings.append(f"LOCALE_MISSING_FROM_PAGE ({len(missing)}): {', '.join(missing)}")
    if extra:
        findings.append(f"LOCALE_NOT_IN_SOURCE ({len(extra)}): {', '.join(extra)}")
    status = "PASS" if not findings else "FAIL"
    print(f"locale check={status} source_locales={sorted(src)} page_locales={sorted(page_locales)}")
    for f in findings:
        print(f"  - {f}")
    return 0 if status == "PASS" else 2


def main() -> int:
    if sys.version_info < MIN_PYTHON:
        print("Python 3.12+ required")
        return 2
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("check", help="validate an existing catalog page against source")
    c.add_argument("--source-root", type=Path, required=True)
    c.add_argument("--catalog", type=Path, required=True)
    c.add_argument("--syscmd", type=Path, default=None,
                   help="optional SYSCMD DBF export CSV to cross-check the catalog against")
    e = sub.add_parser("emit", help="re-derive a full catalog page from source")
    e.add_argument("--source-root", type=Path, required=True)
    e.add_argument("--out", type=Path, required=True)
    fc = sub.add_parser("fn-check", help="validate the website function catalog against source")
    fc.add_argument("--source-root", type=Path, required=True)
    fc.add_argument("--catalog", type=Path, required=True,
                    help="path to content/docs/dottalk/function-catalog.mdx")
    fc.add_argument("--sysfunc", type=Path, default=None,
                    help="optional SYSFUNC DBF export CSV to cross-check against")
    ec = sub.add_parser("err-check", help="validate the website error-codes page against source")
    ec.add_argument("--source-root", type=Path, required=True)
    ec.add_argument("--page", type=Path, required=True,
                    help="path to content/docs/engine/error-codes.mdx")
    lc = sub.add_parser("loc-check", help="validate the messaging/localization locale table against source")
    lc.add_argument("--source-root", type=Path, required=True)
    lc.add_argument("--page", type=Path, required=True,
                    help="path to content/docs/engine/messaging-and-localization.mdx")
    args = p.parse_args()
    if args.mode == "check":
        syscmd = args.syscmd.resolve() if args.syscmd else None
        return check(args.source_root.resolve(), args.catalog.resolve(), syscmd)
    if args.mode == "fn-check":
        sysfunc = args.sysfunc.resolve() if args.sysfunc else None
        return fn_check(args.source_root.resolve(), args.catalog.resolve(), sysfunc)
    if args.mode == "err-check":
        return err_check(args.source_root.resolve(), args.page.resolve())
    if args.mode == "loc-check":
        return loc_check(args.source_root.resolve(), args.page.resolve())
    return emit(args.source_root.resolve(), args.out.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
