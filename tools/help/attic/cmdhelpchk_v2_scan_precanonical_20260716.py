#!/usr/bin/env python3
"""
CMDHELPCHK v2 external scanner/report generator.

Precise static audit mode for the DotTalk++ / x64base layered HELP and
metadata system. The scanner is read-only with respect to source, DBF/DBT,
CDX/LMDB, docs, diagrams, workspaces, and scripts. It writes only its own
reports.

Design rule: a broad text mention is not proof. Runtime/source proof is based
on exact command handler definitions, exact shell registry entries, and exact
command-local @dottalk.usage blocks where available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence
import argparse
import csv
import re
import sys

REPORT_MD = "cmdhelpchk_v2_report.md"
REPORT_CSV = "cmdhelpchk_v2_report.csv"

CSV_COLUMNS: tuple[str, ...] = (
    "command", "canonical_id", "layer", "check", "status", "proof_level",
    "evidence_path", "evidence_key", "evidence_summary", "notes",
)

LAYER_COLUMNS: tuple[str, ...] = (
    "REGISTRY", "HANDLER", "RUNTIME", "SOURCE_USAGE", "PRINT_USAGE",
    "SYSCMD", "SYSHELP", "SYSARGS", "SYSENTVAR", "SYSSUBCMD",
    "DATA_HELP", "DOCS", "DIAGRAM", "TESTS", "RUNTIME_HELP",
)

TEXT_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".md", ".txt",
    ".json", ".jsonl", ".dts", ".meta", ".drawio", ".xml", ".py",
    ".bat", ".cmd", ".ps1", ".sh", ".log", ".dtx",
}

SKIP_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
    "build", "cmake-build-debug", "cmake-build-release", "dist", "out",
    "bin", "obj",
}

LEGACY_HINTS = ("legacy", "archive", "old", "backup", "obsolete", "deprecated", "save")
MAX_TEXT_BYTES = 2_000_000

COMPACT_METADATA_FILES: dict[str, tuple[str, ...]] = {
    "SYSCMD": ("SYSCMD.dbf", "SYSCMD.dtx", "SYSTEM_COMMANDS.dbf", "SYSTEM_COMMANDS.dtx"),
    "SYSHELP": ("SYSHELP.dbf", "SYSHELP.dtx", "SYSTEM_HELP_TEXT.dbf", "SYSTEM_HELP_TEXT.dtx"),
    "SYSARGS": ("SYSARGS.dbf", "SYSARGS.dtx", "SYSTEM_ARGUMENTS.dbf", "SYSTEM_ARGUMENTS.dtx"),
    "SYSENTVAR": ("SYSENTVAR.dbf", "SYSENTVAR.dtx", "SYSTEM_ENTRY_VARIANTS.dbf", "SYSTEM_ENTRY_VARIANTS.dtx"),
    "SYSSUBCMD": ("SYSSUBCMD.dbf", "SYSSUBCMD.dtx", "SYSTEM_SUBCOMMANDS.dbf", "SYSTEM_SUBCOMMANDS.dtx"),
}

DATA_HELP_FILES: tuple[str, ...] = (
    "commands.dbf", "commands.dbt", "cmd_args.dbf", "cmd_args.dbt",
    "help_artifacts.dbf", "help_artifacts.dbt", "help_topic.dbf",
    "help_section.dbf", "help_line.dbf", "FULL/help_artifacts.dbf",
    "FULL/help_artifacts.dbt", "MINEALL/help_artifacts.dbf",
    "MINEALL/help_artifacts.dbt",
)

DOC_PATTERNS = ("docs/**/*.md", "docs/**/*.txt", "docs/**/*.json", "docs/**/*.jsonl")
DIAGRAM_PATTERNS = ("tools/diagram/**/*.meta", "tools/diagram/**/*.drawio", "data/**/*.drawio")
TEST_PATTERNS = ("data/scripts/**/*.dts", "data/scripts/**/*.txt", "data/tests/**/*", "tests/**/*")
RUNTIME_PATTERNS = ("data/logs/**/*.log", "data/logs/**/*.txt", "data/scripts/**/*.dts", "data/scripts/**/*.txt")


@dataclass(frozen=True)
class CommandSpec:
    command: str
    canonical_id: str
    aliases: tuple[str, ...]
    handlers: tuple[str, ...]
    registry_keys: tuple[str, ...]
    source_files: tuple[str, ...]
    route_notes: tuple[str, ...] = ()


@dataclass
class Evidence:
    command: str
    canonical_id: str
    layer: str
    check: str
    status: str
    proof_level: str = "unknown"
    evidence_path: str = ""
    evidence_key: str = ""
    evidence_summary: str = ""
    notes: str = ""


@dataclass
class ScanResult:
    repo_root: Path
    generated_at: str
    tree_file: Path | None = None
    tree_text: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    layer_presence: list[Evidence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class FileHit:
    path: Path
    rel_path: str
    key: str
    summary: str
    legacy: bool = False


def build_command_specs() -> list[CommandSpec]:
    return [
        CommandSpec("HELP", "CMD_HELP", ("HELP",), ("cmd_HELP",), ("HELP",), ("src/cli/cmd_help.cpp",)),
        CommandSpec("CMDHELPCHK", "CMD_CMDHELPCHK", ("CMDHELPCHK", "CHK"), ("cmd_CMDHELPCHK",), ("CMDHELPCHK",), ("src/cli/command_helpchk.cpp",)),
        CommandSpec("DRAWIO", "CMD_DRAWIO", ("DRAWIO",), ("cmd_DRAWIO",), ("DRAWIO",), ("src/cli/cmd_drawio.cpp",)),
        CommandSpec("TUPLE", "CMD_TUPLE", ("TUPLE", "TUP"), ("cmd_TUPLE",), ("TUPLE",), ("src/cli/cmd_tuple.cpp",)),
        CommandSpec("TUPLEDELTA", "CMD_TUPLEDELTA", ("TUPLEDELTA",), ("cmd_TUPLEDELTA",), ("TUPLEDELTA",), ("src/cli/cmd_tupledelta.cpp",)),
        CommandSpec("LIST", "CMD_LIST", ("LIST",), ("cmd_LIST",), ("LIST",), ("src/cli/cmd_list.cpp",)),
        CommandSpec("SMARTLIST", "CMD_SMARTLIST", ("SMARTLIST",), ("cmd_SMARTLIST",), ("SMARTLIST",), ("src/cli/cmd_smartlist.cpp",)),
        CommandSpec("WORKSPACE", "CMD_WORKSPACE", ("WORKSPACE", "WS"), ("cmd_WORKSPACE",), ("WORKSPACE",), ("src/cli/cmd_workspace.cpp",)),
        CommandSpec(
            "SET INDEX", "CMD_SETINDEX", ("SET INDEX", "SETINDEX"), ("cmd_SETINDEX",), ("SETINDEX", "SET"),
            ("src/cli/cmd_setindex.cpp", "src/cli/cmd_set.cpp"),
            ("SET INDEX is routed through SET plus the SETINDEX compatibility command.",),
        ),
        CommandSpec(
            "SET ORDER", "CMD_SETORDER", ("SET ORDER", "SETORDER"), ("cmd_SETORDER",), ("SETORDER", "SET"),
            ("src/cli/cmd_setorder.cpp", "src/cli/cmd_set.cpp"),
            ("SET ORDER is routed through SET plus the SETORDER compatibility command.",),
        ),
    ]


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def is_probably_legacy(path: Path) -> bool:
    return any(any(hint in part.lower() for hint in LEGACY_HINTS) for part in path.parts)


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def read_text_limited(path: Path) -> str | None:
    if not path.is_file() or not is_text_candidate(path):
        return None
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def line_summary(text: str, match_start: int, max_len: int = 190) -> str:
    line_start = text.rfind("\n", 0, match_start) + 1
    line_end = text.find("\n", match_start)
    if line_end < 0:
        line_end = len(text)
    line = re.sub(r"\s+", " ", text[line_start:line_end].strip())
    if len(line) > max_len:
        return line[: max_len - 3] + "..."
    return line


def add_layer_presence(result: ScanResult, layer: str, path: Path, check: str, present: bool, notes: str = "") -> None:
    if present:
        status = "OK"
        proof = "path-present"
        key = "path-present"
        summary = "present"
    else:
        status = "UNVERIFIED"
        proof = "unknown"
        key = "path-missing"
        summary = "missing or unavailable in scan root"
        if result.tree_text and tree_mentions(result, relpath(path, result.repo_root)):
            status = "TREE_PRESENT_UNREAD"
            proof = "tree-listing"
            key = "tree-listed"
            summary = "listed in uploaded tree, but content unavailable in source scan root"
    result.layer_presence.append(Evidence("__layer__", "", layer, check, status, proof, relpath(path, result.repo_root), key, summary, notes))


def tree_mentions(result: ScanResult, fragment: str) -> bool:
    if not result.tree_text:
        return False
    f = fragment.replace("/", "\\").lower()
    alt = fragment.replace("\\", "/").lower()
    text = result.tree_text.lower()
    # The uploaded tree is a Windows tree listing, so exact paths are not always contiguous.
    # Also fall back to basename matching for catalog files.
    base = Path(fragment).name.lower()
    return f in text or alt in text or (bool(base) and base in text)


def target_source_files(root: Path, spec: CommandSpec) -> list[Path]:
    out: list[Path] = []
    for rel in spec.source_files:
        p = root / rel
        if p.exists() and p.is_file():
            out.append(p)
    if out:
        return out
    # Fallback only when expected files are absent: search by handler name.
    candidates: list[Path] = []
    for p in root.glob("src/cli/**/*.cpp"):
        if any(part in SKIP_DIR_NAMES for part in p.parts):
            continue
        text = read_text_limited(p) or ""
        if any(h in text for h in spec.handlers):
            candidates.append(p)
    return sorted(candidates, key=lambda p: relpath(p, root).lower())


def exact_word_regex(token: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", re.IGNORECASE)


def first_hit(hits: Sequence[FileHit]) -> FileHit | None:
    current = [h for h in hits if not h.legacy]
    return (current or list(hits) or [None])[0]


def evidence_from_hit(spec: CommandSpec, layer: str, check: str, hit: FileHit | None, missing_status: str, missing_note: str, proof: str, ok_status: str = "OK") -> Evidence:
    if hit:
        if hit.legacy:
            return Evidence(spec.command, spec.canonical_id, layer, check, "NEEDS_REVIEW", "historical", hit.rel_path, hit.key, hit.summary, "hit is in a legacy/archive/deprecated-looking path; do not treat as current proof")
        return Evidence(spec.command, spec.canonical_id, layer, check, ok_status, proof, hit.rel_path, hit.key, hit.summary, "")
    return Evidence(spec.command, spec.canonical_id, layer, check, missing_status, "unknown", "", "", "", missing_note)


def scan_registry(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    root = result.repo_root
    registry_path = root / "src" / "cli" / "shell_commands.cpp"
    text = read_text_limited(registry_path) or ""
    add_layer_presence(result, "SOURCE", root / "src" / "cli", "source command directory", (root / "src" / "cli").exists())
    add_layer_presence(result, "SOURCE", registry_path, "shell command registry source", registry_path.exists())
    if not text:
        result.warnings.append("Could not read src/cli/shell_commands.cpp; registry checks remain unverified.")
    for spec in specs:
        hits: list[FileHit] = []
        for key in spec.registry_keys:
            rx = re.compile(r"registry\(\)\.add\(\s*\"" + re.escape(key) + r"\"\s*,[^;]*\)", re.DOTALL)
            m = rx.search(text)
            if m:
                hits.append(FileHit(registry_path, relpath(registry_path, root), key, line_summary(text, m.start()), is_probably_legacy(registry_path)))
        hit = first_hit(hits)
        status = "OK"
        note = ""
        if spec.command in {"SET INDEX", "SET ORDER"} and hit:
            # Direct SETINDEX/SETORDER registry plus SET router counts as route evidence, not proof of multiword key registration.
            note = "multiword form routes through SET router; standalone compatibility command is registered separately"
        ev = evidence_from_hit(spec, "REGISTRY", "shell registry entry", hit, "MISSING_REGISTRY", "no exact registry().add entry found for expected command key(s)", "source-confirmed", status)
        if note:
            ev.notes = note
        result.evidence.append(ev)


def scan_handlers_and_usage(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    root = result.repo_root
    for spec in specs:
        files = target_source_files(root, spec)
        if not files:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "HANDLER", "expected source file/handler", "MISSING_SOURCE_FILE", "unknown", "", "", "", f"expected source file(s) not found: {', '.join(spec.source_files)}"))
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "SOURCE_USAGE", "command-local @dottalk.usage v1 block", "UNVERIFIED", "unknown", "", "", "", "handler source file was not available"))
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "PRINT_USAGE", "command-local usage output", "UNVERIFIED", "unknown", "", "", "", "handler source file was not available"))
            continue

        # Handler definition evidence.
        handler_hits: list[FileHit] = []
        for p in files:
            text = read_text_limited(p) or ""
            for handler in spec.handlers:
                rx = re.compile(r"\bvoid\s+" + re.escape(handler) + r"\s*\(")
                m = rx.search(text)
                if m:
                    handler_hits.append(FileHit(p, relpath(p, root), handler, line_summary(text, m.start()), is_probably_legacy(p)))
                    break
        result.evidence.append(evidence_from_hit(spec, "HANDLER", "command handler definition", first_hit(handler_hits), "MISSING_HANDLER", "expected cmd_* handler definition was not found in target files", "source-confirmed"))

        # Routing/runtime: handler plus registry gives source-level runtime candidate.
        reg = matrix_evidence(result, spec.command, "REGISTRY")
        handler = first_hit(handler_hits)
        if reg and reg.status == "OK" and handler:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "RUNTIME", "registry + handler static route", "OK", "source-confirmed", handler.rel_path, handler.key, f"{handler.key} handler present and registry entry detected", "; ".join(spec.route_notes)))
        elif handler:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "RUNTIME", "handler without complete registry proof", "PARTIAL", "source-confirmed", handler.rel_path, handler.key, handler.summary, "handler exists, but registry proof was incomplete"))
        else:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "RUNTIME", "registry + handler static route", "MISSING_RUNTIME", "unknown", "", "", "", "no source-level runtime route was confirmed"))

        # Command-local @dottalk.usage block.
        usage_hits: list[FileHit] = []
        for p in files:
            text = read_text_limited(p) or ""
            for block_start in [m.start() for m in re.finditer(r"@dottalk\.usage\s+v1", text, re.IGNORECASE)]:
                window = text[block_start : min(len(text), block_start + 3500)]
                # Stop roughly at include boundary if present.
                inc = window.find("#include")
                if inc > 0:
                    window = window[:inc]
                normalized = re.sub(r"^[ \t]*// ?", "", window, flags=re.MULTILINE)
                alias_match = False
                for alias in spec.aliases:
                    if re.search(r"^\s*command:\s*" + re.escape(alias) + r"\s*$", normalized, re.IGNORECASE | re.MULTILINE):
                        alias_match = True
                    if re.search(r"^\s*usage-access:\s*" + re.escape(alias) + r"\s+USAGE\s*$", normalized, re.IGNORECASE | re.MULTILINE):
                        alias_match = True
                    if exact_word_regex(alias).search(normalized) and ("usage:" in normalized.lower() or "summary:" in normalized.lower()):
                        alias_match = True
                if alias_match:
                    usage_hits.append(FileHit(p, relpath(p, root), "@dottalk.usage v1", "command-local usage metadata block", is_probably_legacy(p)))
                    break
        result.evidence.append(evidence_from_hit(spec, "SOURCE_USAGE", "command-local @dottalk.usage v1 block", first_hit(usage_hits), "MISSING_SOURCE_USAGE", "target command source exists but no exact command-local @dottalk.usage v1 block was found", "source-declared"))

        # Command-local usage output. This accepts either print_*usage or clear inline usage output in the target file.
        print_hits: list[FileHit] = []
        for p in files:
            text = read_text_limited(p) or ""
            for m in re.finditer(r"\b(?:static\s+)?void\s+[A-Za-z0-9_]*usage[A-Za-z0-9_]*\s*\(|Usage:\\n|DotTalk\+\+ Help System", text, re.IGNORECASE):
                window = text[max(0, m.start() - 600): min(len(text), m.end() + 1600)]
                if any(exact_word_regex(alias).search(window) for alias in spec.aliases) or spec.command == "HELP" and "DotTalk++ Help System" in window:
                    print_hits.append(FileHit(p, relpath(p, root), m.group(0).replace("\n", " ")[:60], line_summary(text, m.start()), is_probably_legacy(p)))
                    break
        result.evidence.append(evidence_from_hit(spec, "PRINT_USAGE", "command-local usage output", first_hit(print_hits), "MISSING_PRINT_USAGE", "target command source exists but no command-local usage output was detected", "source-confirmed"))


def matrix_evidence(result: ScanResult, command: str, layer: str) -> Evidence | None:
    matches = [ev for ev in result.evidence if ev.command == command and ev.layer == layer]
    if not matches:
        return None
    priority = {"OK": 0, "PARTIAL": 1, "NEEDS_REVIEW": 2, "TREE_PRESENT_UNREAD": 3, "UNVERIFIED": 4}
    return sorted(matches, key=lambda ev: priority.get(ev.status, 5))[0]


def iter_pattern_files(root: Path, patterns: Sequence[str], exclude_reports: bool = True) -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if exclude_reports and relpath(path, root).lower().replace("\\", "/").startswith("docs/generated/reports/"):
                continue
            resolved = path.resolve()
            if resolved not in seen:
                files.append(path)
                seen.add(resolved)
    return sorted(files, key=lambda p: relpath(p, root).lower())


def search_files_for_aliases(root: Path, files: Sequence[Path], spec: CommandSpec) -> list[FileHit]:
    hits: list[FileHit] = []
    for path in files:
        text = read_text_limited(path)
        if not text:
            continue
        for alias in spec.aliases + (spec.canonical_id,):
            m = exact_word_regex(alias).search(text)
            if m:
                hits.append(FileHit(path, relpath(path, root), alias, line_summary(text, m.start()), is_probably_legacy(path)))
                break
    return hits


def metadata_catalog_paths(root: Path, filenames: Sequence[str]) -> list[Path]:
    bases = (root / "data" / "dbf" / "x64" / "metadata", root / "data" / "indexes" / "x64" / "metadata")
    paths: list[Path] = []
    for base in bases:
        for name in filenames:
            candidate = base / name
            if candidate.exists():
                paths.append(candidate)
    return paths


def scan_metadata(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    root = result.repo_root
    metadata_dir = root / "data" / "dbf" / "x64" / "metadata"
    index_dir = root / "data" / "indexes" / "x64" / "metadata"
    add_layer_presence(result, "METADATA", metadata_dir, "compact metadata directory", metadata_dir.exists())
    add_layer_presence(result, "METADATA_INDEX", index_dir, "metadata index directory", index_dir.exists())
    for spec in specs:
        for layer, filenames in COMPACT_METADATA_FILES.items():
            paths = metadata_catalog_paths(root, filenames)
            readable = [p for p in paths if p.suffix.lower() in {".dtx", ".meta", ".txt", ".json", ".jsonl"}]
            hit = first_hit(search_files_for_aliases(root, readable, spec))
            if hit:
                result.evidence.append(Evidence(spec.command, spec.canonical_id, layer, "metadata text sidecar/reference", "OK", "data-present", hit.rel_path, hit.key, hit.summary, "DBF row-level verification is still deferred"))
            elif paths:
                result.evidence.append(Evidence(spec.command, spec.canonical_id, layer, "metadata catalog file presence", "UNVERIFIED", "data-present", "; ".join(relpath(p, root) for p in paths[:4]), "catalog-present", "metadata catalog file(s) present", "row-level command verification deferred; catalog presence is not row proof"))
            elif result.tree_text and any(tree_mentions(result, name) for name in filenames):
                result.evidence.append(Evidence(spec.command, spec.canonical_id, layer, "metadata catalog listed in tree", "TREE_PRESENT_UNREAD", "tree-listing", "; ".join(filenames[:2]), "tree-listed", "metadata catalog appears in uploaded tree", "content was not available in the source archive, so row coverage remains unverified"))
            elif metadata_dir.exists() or index_dir.exists():
                result.evidence.append(Evidence(spec.command, spec.canonical_id, layer, "metadata catalog file presence", f"MISSING_{layer}", "unknown", "", "catalog-missing", "expected metadata catalog file was not found", "metadata directory exists but expected compact/long-form catalog was missing"))
            else:
                result.evidence.append(Evidence(spec.command, spec.canonical_id, layer, "metadata catalog file presence", "UNVERIFIED", "unknown", "", "metadata-dir-missing", "metadata directory not found in scan root", "cannot infer missing rows from source-only archive"))


def scan_data_help(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    root = result.repo_root
    help_dir = root / "data" / "help"
    add_layer_presence(result, "DATA_HELP", help_dir, "parallel data/help directory", help_dir.exists(), "parallel lane until reconciled with SYS* metadata")
    existing = [help_dir / name for name in DATA_HELP_FILES if (help_dir / name).exists()]
    readable = [p for p in existing if p.suffix.lower() in TEXT_EXTENSIONS]
    for spec in specs:
        hit = first_hit(search_files_for_aliases(root, readable, spec))
        if hit:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DATA_HELP", "data/help readable text reference", "OK", "data-present", hit.rel_path, hit.key, hit.summary, "DBF/DBT row-level verification not attempted"))
        elif existing:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DATA_HELP", "data/help file presence", "UNVERIFIED", "data-present", "; ".join(relpath(p, root) for p in existing[:4]), "data-help-present", "data/help catalog files present", "row-level command coverage not verified"))
        elif result.tree_text and any(tree_mentions(result, f"data/help/{name}") or tree_mentions(result, name) for name in DATA_HELP_FILES):
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DATA_HELP", "data/help listed in tree", "TREE_PRESENT_UNREAD", "tree-listing", "data/help", "tree-listed", "data/help files appear in uploaded tree", "content was not available in the source archive, so row coverage remains unverified"))
        elif help_dir.exists():
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DATA_HELP", "data/help file presence", "MISSING_DATA_HELP", "unknown", "", "data-help-files-missing", "data/help directory exists but expected files were absent", ""))
        else:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DATA_HELP", "data/help file presence", "UNVERIFIED", "unknown", "", "data-help-dir-missing", "data/help directory not found in scan root", "cannot distinguish absent lane from source-only archive"))


def scan_docs_diagrams_tests_runtime(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    root = result.repo_root
    docs = iter_pattern_files(root, DOC_PATTERNS)
    diagrams = iter_pattern_files(root, DIAGRAM_PATTERNS)
    tests = [p for p in iter_pattern_files(root, TEST_PATTERNS) if is_text_candidate(p)]
    runtime_files = [p for p in iter_pattern_files(root, RUNTIME_PATTERNS) if is_text_candidate(p)]
    add_layer_presence(result, "DOCS", root / "docs", "docs authority directory", (root / "docs").exists())
    add_layer_presence(result, "DIAGRAM", root / "tools" / "diagram", "diagram tool directory", (root / "tools" / "diagram").exists())
    add_layer_presence(result, "DIAGRAM", root / "data", "data diagram/search directory", (root / "data").exists())
    add_layer_presence(result, "TESTS", root / "data" / "scripts", "scripts directory", (root / "data" / "scripts").exists())
    add_layer_presence(result, "RUNTIME", root / "data" / "logs", "logs directory", (root / "data" / "logs").exists())
    for spec in specs:
        doc_hit = first_hit(search_files_for_aliases(root, docs, spec))
        diagram_hit = first_hit(search_files_for_aliases(root, diagrams, spec))
        test_hit = first_hit(search_files_for_aliases(root, tests, spec))
        runtime_hit = first_hit(search_files_for_aliases(root, runtime_files, spec))
        result.evidence.append(evidence_from_hit(spec, "DOCS", "docs authority/plain-text reference", doc_hit, "DOCS_MISSING" if docs else "UNVERIFIED", "docs files not available or no current reference detected", "doc-authority-present"))
        result.evidence.append(evidence_from_hit(spec, "DIAGRAM", "diagram/plain-text reference", diagram_hit, "DIAGRAM_MISSING" if diagrams else "UNVERIFIED", "diagram files not available or no command reference detected", "generated-present"))
        result.evidence.append(evidence_from_hit(spec, "TESTS", "test/script/log reference", test_hit, "TEST_COVERAGE_MISSING" if tests else "UNVERIFIED", "test/script files not available or no command reference detected", "script-present"))
        result.evidence.append(evidence_from_hit(spec, "RUNTIME_HELP", "runtime help/log transcript candidate", runtime_hit, "MISSING_RUNTIME_HELP" if runtime_files else "UNVERIFIED", "runtime logs/scripts not available or no HELP surface candidate detected", "session-confirmed"))


def add_design_notes(result: ScanResult, specs: Sequence[CommandSpec]) -> None:
    for spec in specs:
        if spec.command in {"SET INDEX", "SET ORDER"}:
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DESIGN_REVIEW", "canonical id model", "NEEDS_REVIEW", "source-informed", "src/cli/cmd_set.cpp", "set-router", "current source has standalone SETINDEX/SETORDER handlers plus SET INDEX/SET ORDER router forms", "do not model these only as standalone canonical IDs; preserve SET-family/subcommand relationship"))
        if spec.command == "CMDHELPCHK":
            result.evidence.append(Evidence(spec.command, spec.canonical_id, "DESIGN_REVIEW", "v1/v2 coexistence", "NEEDS_REVIEW", "source-informed", "src/cli/command_helpchk.cpp", "existing-command", "CMDHELPCHK already exists as a runtime command; v2 external scanner should not overwrite it casually", "integrate v2 as external tool first or explicit submode after review"))


def scan_repo(repo_root: Path, tree_file: Path | None = None) -> ScanResult:
    tree_text = ""
    if tree_file and tree_file.exists():
        try:
            tree_text = tree_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            tree_text = ""
    result = ScanResult(repo_root.resolve(), datetime.now(timezone.utc).replace(microsecond=0).isoformat(), tree_file.resolve() if tree_file else None, tree_text)
    specs = build_command_specs()
    scan_registry(result, specs)
    scan_handlers_and_usage(result, specs)
    scan_metadata(result, specs)
    scan_data_help(result, specs)
    scan_docs_diagrams_tests_runtime(result, specs)
    add_design_notes(result, specs)
    if tree_file and not tree_text:
        result.warnings.append(f"Tree manifest was provided but could not be read: {tree_file}")
    if not (repo_root / "data").exists() and tree_text:
        result.warnings.append("Scan root appears to be source-only; uploaded tree lists data/docs assets, but their content was not available for row/doc verification.")
    return result


def compact_symbol(ev: Evidence | None) -> str:
    if ev is None:
        return "?"
    if ev.status == "OK":
        if ev.layer == "TESTS":
            return "SCR"
        if ev.proof_level == "session-confirmed":
            return "MAN"
        return "OK"
    if ev.status == "PARTIAL":
        return "PART"
    if ev.status == "TREE_PRESENT_UNREAD":
        return "TREE"
    if ev.status == "UNVERIFIED":
        return "?"
    if ev.status.startswith("MISSING") or ev.status.endswith("MISSING") or ev.status in {"DOCS_MISSING", "DIAGRAM_MISSING", "TEST_COVERAGE_MISSING"}:
        return "MISS"
    if ev.status in {"DOCS_STALE", "DIAGRAM_STALE"}:
        return "OLD"
    if ev.status == "NEEDS_REVIEW":
        return "PART"
    return "?"


def overall_status(result: ScanResult, command: str) -> str:
    key_layers = ["REGISTRY", "HANDLER", "RUNTIME", "SOURCE_USAGE", "PRINT_USAGE", "SYSCMD", "SYSHELP", "DATA_HELP", "DOCS", "TESTS", "RUNTIME_HELP"]
    evs = [matrix_evidence(result, command, layer) for layer in key_layers]
    statuses = [ev.status for ev in evs if ev]
    if not statuses:
        return "UNVERIFIED"
    if all(s == "OK" for s in statuses):
        return "OK"
    if any(s.startswith("MISSING") or s.endswith("MISSING") or s in {"DOCS_MISSING", "TEST_COVERAGE_MISSING"} for s in statuses):
        return "PARTIAL"
    if any(s == "NEEDS_REVIEW" for s in statuses):
        return "NEEDS_REVIEW"
    if any(s == "TREE_PRESENT_UNREAD" for s in statuses):
        return "PARTIAL"
    return "PARTIAL"


def notes_for_command(result: ScanResult, command: str) -> str:
    evs = [ev for ev in result.evidence if ev.command == command]
    notes: list[str] = []
    for ev in evs:
        if ev.status in {"NEEDS_REVIEW", "MISSING_SOURCE_USAGE", "MISSING_PRINT_USAGE", "MISSING_HANDLER", "MISSING_REGISTRY"}:
            notes.append(ev.evidence_summary or ev.notes)
        if ev.status == "TREE_PRESENT_UNREAD":
            notes.append(ev.notes or ev.evidence_summary)
    if not notes and any(ev.status == "UNVERIFIED" for ev in evs):
        notes.append("one or more non-source layers remain unverified")
    return "; ".join(x for x in dict.fromkeys(notes) if x)[:320]


def gap_candidates(result: ScanResult) -> list[str]:
    candidates: list[str] = []
    for spec in build_command_specs():
        for layer in ("REGISTRY", "HANDLER", "SOURCE_USAGE", "PRINT_USAGE", "DOCS", "TESTS"):
            ev = matrix_evidence(result, spec.command, layer)
            if not ev:
                continue
            if ev.status.startswith("MISSING") or ev.status.endswith("MISSING") or ev.status in {"DOCS_MISSING", "TEST_COVERAGE_MISSING"}:
                candidates.append(f"{spec.command}: {layer} is {ev.status} - {ev.notes or ev.evidence_summary}")
        syscmd = matrix_evidence(result, spec.command, "SYSCMD")
        if syscmd and syscmd.status in {"UNVERIFIED", "TREE_PRESENT_UNREAD"}:
            candidates.append(f"{spec.command}: metadata catalog/row coverage remains {syscmd.status}; catalog presence is not row proof.")
    candidates.append("SET INDEX / SET ORDER should be modeled as SET-family routed forms plus SETINDEX/SETORDER compatibility handlers, not just as isolated standalone IDs.")
    candidates.append("CMDHELPCHK already exists in source; external v2 scanner should be introduced without casually replacing the runtime validator.")
    candidates.append("DBF/DBT/CDX/LMDB row-level parsing remains intentionally deferred until an x64base-aware reader is used.")
    return list(dict.fromkeys(candidates))


def write_csv(result: ScanResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for ev in result.layer_presence + result.evidence:
            writer.writerow({
                "command": ev.command,
                "canonical_id": ev.canonical_id,
                "layer": ev.layer,
                "check": ev.check,
                "status": ev.status,
                "proof_level": ev.proof_level,
                "evidence_path": ev.evidence_path,
                "evidence_key": ev.evidence_key,
                "evidence_summary": ev.evidence_summary,
                "notes": ev.notes,
            })


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_markdown(result: ScanResult, output_path: Path, csv_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# CMDHELPCHK v2 Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Generated: `{result.generated_at}`")
    lines.append(f"- Repo/source root scanned: `{result.repo_root}`")
    if result.tree_file:
        lines.append(f"- Tree manifest consulted: `{result.tree_file}`")
    lines.append(f"- Markdown report: `{output_path}`")
    lines.append(f"- CSV report: `{csv_path}`")
    lines.append("- Scanner mode: external static scanner; no runtime command integration")
    lines.append("- Mutation boundary: only generated report files are written")
    lines.append("- DBF/DBT/CDX/LMDB row-level parsing: **not implemented**")
    lines.append("- Precision rule: broad text mentions do not count as command-local proof")
    lines.append("")
    if result.warnings:
        lines.append("### Warnings")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Command Matrix")
    lines.append("")
    header = ["Command", "Canonical ID", *LAYER_COLUMNS, "Status", "Notes"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for spec in build_command_specs():
        cells = [spec.command, spec.canonical_id]
        for layer in LAYER_COLUMNS:
            cells.append(compact_symbol(matrix_evidence(result, spec.command, layer)))
        cells.append(overall_status(result, spec.command))
        cells.append(notes_for_command(result, spec.command))
        lines.append("| " + " | ".join(md_escape(c) for c in cells) + " |")
    lines.append("")
    lines.append("Legend: `OK` exact static evidence; `MISS` expected item missing in an available layer; `TREE` listed in uploaded tree but unread; `?` unverified; `SCR` script/test evidence; `MAN` manual/session evidence; `PART` partial/review.")
    lines.append("")

    lines.append("## Layer Presence Summary")
    lines.append("")
    lines.append("| Layer | Check | Status | Evidence path | Notes |")
    lines.append("| --- | --- | --- | --- | --- |")
    for ev in result.layer_presence:
        lines.append("| " + " | ".join(md_escape(x) for x in (ev.layer, ev.check, ev.status, ev.evidence_path, ev.notes)) + " |")
    lines.append("")

    lines.append("## Per-command Evidence")
    lines.append("")
    for spec in build_command_specs():
        lines.append(f"### {spec.command} `{spec.canonical_id}`")
        lines.append("")
        lines.append("| Layer | Check | Status | Proof | Evidence | Key | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for ev in [e for e in result.evidence if e.command == spec.command]:
            evidence = ev.evidence_path
            if ev.evidence_summary:
                evidence = f"{evidence}: {ev.evidence_summary}" if evidence else ev.evidence_summary
            lines.append("| " + " | ".join(md_escape(x) for x in (ev.layer, ev.check, ev.status, ev.proof_level, evidence, ev.evidence_key, ev.notes)) + " |")
        lines.append("")

    lines.append("## Drift / Gap Candidates")
    lines.append("")
    for item in gap_candidates(result)[:60]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Notes and Limits")
    lines.append("")
    lines.append("- This report is a visibility/audit artifact, not a HELP rewrite.")
    lines.append("- Metadata catalog presence is not proof of command-row coverage.")
    lines.append("- Runtime truth requires direct execution or trusted transcripts; source route proof is still static proof.")
    lines.append("- `TREE_PRESENT_UNREAD` means the uploaded tree listed the path, but the source archive did not include file contents.")
    lines.append("- Mentions inside legacy/archive/backup/deprecated-looking paths are not treated as current proof.")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate external CMDHELPCHK v2 static coherence reports.")
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repo/source root to scan; defaults to current working directory.")
    parser.add_argument("--tree-file", type=Path, default=None, help="Optional full dev tree listing used only for path-presence hints.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Directory for generated report files; defaults to <repo>/docs/generated/reports.")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error console output.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    repo_root = args.repo.resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        print(f"ERROR: repo root does not exist or is not a directory: {repo_root}", file=sys.stderr)
        return 2
    if args.tree_file and not args.tree_file.exists():
        print(f"ERROR: tree manifest does not exist: {args.tree_file}", file=sys.stderr)
        return 2
    out_dir = args.out_dir.resolve() if args.out_dir else repo_root / "docs" / "generated" / "reports"
    md_path = out_dir / REPORT_MD
    csv_path = out_dir / REPORT_CSV
    result = scan_repo(repo_root, args.tree_file)
    write_csv(result, csv_path)
    write_markdown(result, md_path, csv_path)
    if not args.quiet:
        print("CMDHELPCHK v2 scan complete")
        print(f"repo: {repo_root}")
        if args.tree_file:
            print(f"tree: {args.tree_file.resolve()}")
        print(f"markdown: {md_path}")
        print(f"csv: {csv_path}")
        print(f"commands: {len(build_command_specs())}")
        print(f"evidence rows: {len(result.layer_presence) + len(result.evidence)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
