#!/usr/bin/env python3
"""Build an x64base engine feature crosswalk from source and harvested HELP.

Report-only generator. It does not mutate HELP, DBF metadata, command source,
or manual publication files. Outputs are generated documentation artifacts that
can be reviewed before promotion to manuals or the public website.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FeatureSpec:
    feature_id: str
    title: str
    lane: str
    keywords: tuple[str, ...]
    command_terms: tuple[str, ...]
    source_globs: tuple[str, ...]
    planned_terms: tuple[str, ...] = ()
    note: str = ""


FEATURES: tuple[FeatureSpec, ...] = (
    FeatureSpec("table-runtime", "DBF table runtime and DbArea object model", "xbase engine", ("DbArea", "dbarea", "readCurrent", "recCount", "gotoRec"), ("USE", "DBAREA", "AREA", "STRUCT", "FIELDS"), ("src/xbase/*.cpp", "include/xbase*.hpp", "src/cli/cmd_dbarea.cpp")),
    FeatureSpec("workspace-area-wrapper", "Workspaces wrapping active areas", "workspace", ("workspace", "SchemaWorkspace", "SchemaAreaState", "area state"), ("WORKSPACE", "WSREPORT", "AREA", "DBAREAS"), ("src/cli/cmd_workspace.cpp", "src/workspace/**/*.cpp", "include/workspace/**/*.hpp", "src/cli/cmd_wsreport.cpp")),
    FeatureSpec("cursor-navigation", "Cursor control and record navigation", "navigation", ("recno", "gotoRec", "skip", "top", "bottom", "bof", "eof", "cursor"), ("GO", "GOTO", "SKIP", "TOP", "BOTTOM", "FIRST", "LAST", "NEXT", "PRIOR", "RECNO", "DISPLAY", "DUMP"), ("src/cli/cmd_goto.cpp", "src/cli/cmd_skip.cpp", "src/cli/cmd_recno.cpp", "src/xbase/*cursor*.cpp", "src/cli/cursor_*.cpp")),
    FeatureSpec("record-locking", "Record locking and unlock lifecycle", "concurrency", ("lock", "unlock", "record lock", "xbase_locks", "lock_cleanup"), ("LOCK", "UNLOCK"), ("src/cli/cmd_lock.cpp", "src/cli/cmd_unlock.cpp", "src/xbase/*lock*.cpp", "include/*lock*.hpp")),
    FeatureSpec("buffered-editing", "Buffered editing, dirty state, commit and rollback", "editing", ("buffer", "dirty", "commit", "rollback", "PendingEdits", "table_buffer"), ("EDIT", "REPLACE", "COMMIT", "ROLLBACK", "CALCWRITE"), ("src/cli/*buffer*.cpp", "src/cli/table_buffer.cpp", "src/cli/cmd_commit.cpp", "src/cli/cmd_rollback.cpp", "src/tv/cmd_browsetui.cpp")),
    FeatureSpec("triggers-rules", "Triggers, rules, and validation hooks", "rules", ("trigger", "rule", "constraint", "validate", "validator"), ("TRIGGER", "RULE", "VALIDATE", "VALIDATE UNIQUE", "TUPVALIDATE"), ("src/cli/cmd_trigger.cpp", "src/cli/cmd_rule.cpp", "src/cli/cmd_validate*.cpp", "src/cli/field_constraints.cpp")),
    FeatureSpec("dbf-trinity", "DBF flavor trinity: MS-DOS/classic, VFP, and x64 DBF_64", "storage formats", ("ClassicNoMemo", "ClassicWithMemo", "Fox26Memo", "VfpBase", "VfpAutoInc", "VfpVar", "DBF_VERSION_64", "AreaKind"), ("USE", "CREATE", "AUTODBF", "STRUCT", "FIELDS", "SET INDEX", "SET ORDER"), ("include/xbase.hpp", "include/xbase_vfp.hpp", "include/xbase_64.hpp", "src/cli/cmd_setindex.cpp", "src/cli/cmd_setorder.cpp"), note="xbase.hpp is the neutral runtime contract; xbase_vfp.hpp bridges classic/MS-DOS, FoxPro, and VFP descriptors; xbase_64.hpp owns x64 extensions, vector metadata, and fallback naming."),
    FeatureSpec("vfp-field-types", "Visual FoxPro DBF field/data type compatibility", "storage formats", ("VFP", "Visual FoxPro", "Currency", "DateTime", "Double", "Integer", "field type"), ("CREATE", "AUTODBF", "FIELDS", "STRUCT"), ("include/xbase_vfp.hpp", "tests/xbase_vfp_probe.cpp", "src/cli/cli_currency.cpp", "include/cli/field_codecs.hpp", "include/cli/field_meta.hpp")),
    FeatureSpec("x64-dbf-types", "x64 DBF extensions and newer data types", "storage formats", ("DBF64", "x64", "LargeHeaderExtension", "X64Meta", "currency", "datetime", "vector"), ("CREATE", "AUTODBF", "STRUCT"), ("include/xbase_64*.hpp", "include/xbase_64_phase1_contract.txt", "tests/xbase_64_probe.cpp", "src/cli/dbf64_header_validate.cpp")),
    FeatureSpec("vectored-names", "Vectored table and field names with fallback mangling", "storage formats", ("vector", "field name", "table name", "mangle", "fallback", "string_pool"), ("CREATE", "STRUCT", "FIELDS"), ("include/xbase_64_phase1_contract.txt", "include/xbase_64*.hpp", "src/xbase/*name*.cpp")),
    FeatureSpec("memo-object-model", "Object-oriented memo storage and display", "memo", ("memo", "MemoManager", "MemoObject", "MemoRef", "FPT64", "DBT"), ("MEMO", "DISPLAY", "BROWSETUI"), ("src/memo/**/*.cpp", "include/memo/**/*.hpp", "src/cli/cmd_memo.cpp", "src/cli/memo_display.cpp")),
    FeatureSpec("index-api", "Open index API and index backends", "index", ("IndexManager", "IndexTag", "LMDB", "CDX", "CNX", "INX", "seek", "order"), ("INDEX", "REINDEX", "SET INDEX", "SET ORDER", "SEEK", "IDX", "CDX", "CNX", "LMDB", "BUILDLMDB"), ("src/xindex/**/*.cpp", "include/xindex/**/*.hpp", "src/cli/cmd_index*.cpp", "src/cli/cmd_setindex.cpp", "src/cli/cmd_setorder.cpp"), note="SET ORDER defaults v32/classic-like tables to .cnx and v64/VFP/x64 tables to .cdx; SET INDEX accepts .inx/.cnx for v32 and .cdx for v64."),
    FeatureSpec("filter-search", "Filtering, searching, predicates, and WHERE cache", "query", ("filter", "where", "predicate", "locate", "find", "seek", "wherecache"), ("SET FILTER", "LOCATE", "FIND", "SEEK", "WHERE", "WHERECACHE", "SMARTLIST"), ("src/cli/cmd_setfilter.cpp", "src/cli/filters/**/*.cpp", "src/cli/cmd_where*.cpp", "src/cli/cmd_locate.cpp", "src/cli/cmd_seek.cpp")),
    FeatureSpec("relations", "Relations and relation-aware browsing", "relations", ("relation", "Rel", "ERSATZ", "RBROWSE", "rel_enum"), ("REL", "RELATIONS", "SET RELATION", "ERSATZ", "RBROWSE"), ("src/cli/cmd_rel*.cpp", "src/cli/rel_*.cpp", "src/cli/relations_*.cpp")),
    FeatureSpec("ddl-schema", "DDL schema fetch, validation, DBF creation, seeds, and sidecars", "schema", ("DDL FETCH", "DDL VALIDATE", "DDL CREATE DBF", "EMIT SIDECARS", "SEED CSV", "schema"), ("DDL", "CREATE", "AUTODBF", "FIELDMGR"), ("src/cli/cmd_ddl.cpp", "src/cli/cmd_create.cpp", "src/cli/cmd_autodbf.cpp", "docs/schemas/**/*.json", "schemas/**/*.json"), note="DDL FETCH can perform network/file writes; DDL CREATE DBF writes filesystem DBF output and optional sidecars. SEED CSV is recognized by the contract but not fully implemented in this drop-in."),
    FeatureSpec("datadict-ddict", "Data Dictionary catalog inspection and DDICT bridge", "metadata", ("DDICT", "DATA_DICTIONARY_OBJECTS", "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "DATA_DICTIONARY_RELATION_EDGES", "DDOBJECT", "DDEDGE", "read-only"), ("DDICT",), ("src/cli/cmd_ddict.cpp", "src/datadict/**/*.cpp", "src/datadict/**/*.hpp", "tools/datadict/**/*.py", "docs/datadict/**/*.md"), note="DDICT is currently documented as read-only inspection: no DBF append/replace/delete, no CDX/LMDB rebuild, and no HELP/CMDHELPCHK/manual/catalog mutation."),
    FeatureSpec("set-family", "SET family: session, output, paths, indexes, filters, relations, locale, and buffering", "language", ("SET TABLE BUFFER", "SET CONSOLE", "SET PRINT", "SET DEVICE", "SET ALTERNATE", "SET FILTER", "SET RELATION", "SET LANGUAGE", "SET LOCALE", "SET PATH", "SET ORDER", "SET INDEX"), ("SET", "SET INDEX", "SET ORDER", "SET FILTER", "SET RELATION", "SET UNIQUE", "SET CDX", "SET CNX", "SET LMDB", "SETPATH"), ("src/cli/cmd_set.cpp", "src/cli/cmd_set*.cpp", "include/cli/settings.hpp"), note="The SET dispatcher mutates session settings and delegates specialized state to path, index/order, filter, relation, locale, and output-routing handlers."),
    FeatureSpec("dotscript-control", "DotScript command files, variables, control flow, and one-level nesting", "language", ("DotScript", "script_reader", "LOOP", "ENDLOOP", "SCAN", "ENDSCAN", "SET VAR", "line continuation", "one-level subscript", "nesting limit"), ("DOTSCRIPT", "IF", "ELSE", "ENDIF", "LOOP", "ENDLOOP", "SCAN", "ENDSCAN", "WHILE", "ENDWHILE", "UNTIL", "ENDUNTIL", "VAR", "SET VAR"), ("src/cli/cmd_dotscript.cpp", "src/cli/script_reader.cpp", "src/cli/cmd_if.cpp", "src/cli/cmd_loop.cpp", "src/cli/cmd_scan.cpp", "src/cli/cmd_while.cpp", "src/cli/cmd_until.cpp", "src/cli/cmd_var.cpp", "src/cli/dotscript_var_name.cpp"), note="Current DOTSCRIPT nesting is limited to a main script plus one subscript."),
    FeatureSpec("messaging-errors", "Messaging, error/status, and output routing", "observability", ("MessageId", "message_catalog", "cmdout", "ERROR STATUS", "output_router"), ("MSG MGR", "ERROR STATUS", "ERROR CLEAR", "ERROR TEST", "ECHO"), ("src/cli/message_catalog.cpp", "src/cli/cmd_msgmgr.cpp", "src/cli/cmd_error*.cpp", "src/cli/output_router.cpp", "src/cli/cmd_echo.cpp", "docs/messaging/**/*.md")),
    FeatureSpec("locale-language", "Location, locale, and language support", "localization", ("locale", "language", "localization", "message schema", "active locale"), ("MSG MGR", "SET"), ("docs/locale/**/*.md", "tools/locale/**/*.ps1", "src/cli/cmd_msgmgr.cpp", "include/*locale*.hpp")),
    FeatureSpec("command-timing", "Command timing and diagnostics", "observability", ("chrono", "timer", "timing", "elapsed", "duration", "profile"), ("STATUS", "BETA", "CMDHELPCHK"), ("src/cli/**/*.cpp", "include/**/*.hpp"), planned_terms=("timing", "profile")),
    FeatureSpec("gui-api", "Open GUI API, TUI, wxWidgets, and browser lanes", "gui", ("GUI", "wx", "Tk", "TUI", "browse", "screen", "foxtalk", "DottalkForm"), ("BROWSETUI", "BROWSETV", "BROWSER", "SMARTBROWSE", "SIMPLEBROWSE", "FOXTALK"), ("src/gui/**/*.cpp", "src/tv/**/*.cpp", "include/tv/**/*.hpp", "include/DottalkForm.h", "docs/gui/**/*.md")),
    FeatureSpec("external-app-network", "External app, shell, image, web, URL, SFTP, and archive boundaries", "integration", ("ShellExecute", "WinHTTP", "launches_external", "external viewer", "default URL handler", "SFTP", "ZIP", "PSHELL"), ("EDIT", "TEXT", "IMAGE", "WEB", "URL", "SFTP", "PSHELL", "BANG", "ZIP"), ("src/cli/cmd_web.cpp", "src/cli/cmd_image_display.cpp", "src/cli/cmd_sftp.cpp", "src/cli/cmd_zip.cpp", "src/cli/cmd_bang.cpp", "src/edu/edu_edit.cpp", "src/edu/edu_text.cpp"), note="These commands must document external process, network, viewer/browser launch, and filesystem-write risk separately from database mutation."),
    FeatureSpec("sql-import-export", "SQL bridge, CSV import/export, DBF copy, and tuple export", "integration", ("SQL", "sqlite", "import", "export", "CSV", "tupexport", "copy"), ("SQL", "IMPORT", "EXPORT", "IMPORTSQL", "EXPORTSQL", "TUPEXPORT", "COPY", "AUTODBF"), ("src/cli/cmd_sql*.cpp", "src/sqlite/**/*.cpp", "src/cli/cmd_import*.cpp", "src/cli/cmd_export*.cpp", "src/cli/cmd_autodbf.cpp", "src/cli/cmd_tupexport.cpp"), note="IMPORT reads CSV into an open DBF by matching headers to field names; EXPORT writes the current or named open area to CSV by default."),
    FeatureSpec("education-labs", "Education, retro, ASCII, blackbox, and student extension commands", "education", ("education", "ASCII", "Blackbox", "retro", "student extension", "self-registering extension", "SHELLO", "STUDENTHELLO"), ("ASCII", "BBOX", "BLACKBOX", "RETRO", "SHELLO", "STUDENTHELLO", "SECHO", "STUDENTECHO", "IDX", "BOOLEAN", "CASE", "CHRISTMAS", "COBOL", "CODASYL", "NORMALIZE", "SIX"), ("src/edu/**/*.cpp", "src/ext/cmd/**/*.cpp", "src/ext/fn/**/*.cpp", "src/cli/cmd_bbox.cpp", "src/cli/cmd_retro.cpp", "docs/teaching/**/*.md"), note="LabTalk should treat these as runnable education features and proof/curriculum inputs, not only as novelty commands."),
    FeatureSpec("security", "Security and policy surfaces", "security", ("security", "policy", "signature", "permission"), ("SECURITY",), ("src/cli/cmd_security.cpp", "include/xbase_security*.hpp", "src/cli/xbase_security*.hpp", "src/cli/xbase_security_tests.cpp")),
    FeatureSpec("remote-ops", "Remote and system integration surfaces", "integration", ("SFTP", "SSH", "web", "zip", "PowerShell", "system"), ("SFTP", "PSHELL", "WEB", "ZIP"), ("src/cli/cmd_sftp.cpp", "src/cli/sys_*.cpp", "src/cli/cmd_web.cpp", "src/cli/cmd_zip.cpp", "src/cli/zip_backend_*.cpp")),
    FeatureSpec("selfdoc-manualgen", "SelfDoc, HELP metadata, contracts, MAINT, Blackbox, and manualgen pipeline", "documentation", ("SelfDoc", "manualgen", "CMDHELPCHK", "HELP", "contract", "metacollect", "MDO", "@dottalk.usage", "@dottalk.contract", "comments evidence", "Blackbox", "MAINT"), ("HELP", "CMDHELP", "CMDHELPCHK", "MAINT", "BBOX", "MANUAL", "MANSTAR", "DRAWIO"), ("selfdoc/**/*.md", "selfdoc/**/*.py", "tools/manualgen/**/*.py", "tools/comments/**/*.py", "tools/contracts/**/*.py", "docs/contracts/**/*.md", "docs/maintenance/**/*.md", "dottalkpp/docs/tools/**/*.ps1", "src/cli/cmd_manual.cpp", "src/cli/cmd_manstar.cpp", "src/cli/cmdhelp.cpp", "src/cli/command_helpchk.cpp", "src/cli/cmd_maint.cpp", "src/cli/cmd_bbox.cpp"), note="Source contracts, comments evidence, HELP DATA, CMDHELPCHK, MAINT, manualgen, and website promotion are curated as a procedural lane with report-only defaults and explicit mutation gates."),
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def collect_files(root: Path, globs: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in globs:
        found.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(found))


def load_help_commands(root: Path) -> dict[str, dict[str, str]]:
    path = root / "docs/manuals/developer/manualgen/harvested/HELP_COMMANDS.csv"
    commands: dict[str, dict[str, str]] = {}
    if not path.exists():
        return commands
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.DictReader(f):
            cmd = (row.get("COMMAND") or "").strip().upper()
            if not cmd:
                continue
            commands[cmd] = {k: (v or "").strip() for k, v in row.items()}
    return commands


def command_hits(commands: dict[str, dict[str, str]], terms: tuple[str, ...]) -> list[str]:
    out: set[str] = set()
    for term in terms:
        t = term.upper()
        for cmd, row in commands.items():
            if cmd == t or cmd.startswith(t + " ") or t in cmd:
                supported = row.get("SUPPORTED", "")
                implemented = row.get("IMPLEMENT", "")
                out.add(f"{cmd} (implemented={implemented}, supported={supported})")
    return sorted(out)


def keyword_hits(root: Path, files: list[Path], terms: tuple[str, ...]) -> tuple[int, list[str]]:
    hit_count = 0
    examples: list[str] = []
    lowered = [(t, t.lower()) for t in terms]
    for path in files:
        text = read_text(path)
        low = text.lower()
        local = [term for term, term_low in lowered if term_low in low]
        if local:
            hit_count += len(local)
            if len(examples) < 8:
                examples.append(f"{rel(path, root)} [{', '.join(local[:4])}]")
    return hit_count, examples


def status_for(source_files: list[Path], source_hit_count: int, commands: list[str], planned_terms: tuple[str, ...]) -> str:
    implemented_commands = [c for c in commands if "implemented=T" in c and "supported=T" in c]
    if implemented_commands and source_files and source_hit_count:
        return "runtime-evidenced"
    if source_files and source_hit_count:
        return "source-evidenced"
    if commands:
        return "help-catalog-evidenced"
    if planned_terms:
        return "planned-or-in-progress"
    return "review-needed"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# x64base Engine Feature Crosswalk v1")
    lines.append("")
    lines.append(f"Generated: {summary['generated_utc']}")
    lines.append("")
    lines.append("Status language:")
    lines.append("")
    lines.append("- `runtime-evidenced`: implemented/supported HELP command plus source evidence.")
    lines.append("- `source-evidenced`: source evidence exists, but no matching supported HELP command was found by this scanner.")
    lines.append("- `help-catalog-evidenced`: HELP catalog evidence exists, but source mapping needs review.")
    lines.append("- `planned-or-in-progress`: found as a planning lane or broad diagnostic lane; do not market as complete.")
    lines.append("- `review-needed`: no strong evidence found by this pass.")
    lines.append("")
    lines.append("Manualgen note: this report is generated outside the protected manual publication. Promote only after review.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Features scanned: {summary['feature_count']}")
    lines.append(f"- Source files inspected through feature globs: {summary['source_file_mentions']}")
    lines.append(f"- HELP commands loaded: {summary['help_command_count']}")
    lines.append(f"- Manualgen validation status: {summary['manualgen_validation_status']}")
    lines.append(f"- Manualgen validation caveat: {summary['manualgen_validation_caveat']}")
    lines.append("")
    lines.append("## Feature Hierarchy")
    lines.append("")
    by_lane: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_lane.setdefault(row["lane"], []).append(row)
    for lane in sorted(by_lane):
        lines.append(f"### {lane.title()}")
        lines.append("")
        for row in by_lane[lane]:
            lines.append(f"#### {row['title']}")
            lines.append("")
            lines.append(f"- Status: `{row['status']}`")
            if row["commands"]:
                lines.append(f"- Commands: {row['commands']}")
            if row["evidence_files"]:
                lines.append(f"- Evidence: {row['evidence_files']}")
            if row["note"]:
                lines.append(f"- Note: {row['note']}")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out-dir", default="labtalk/reports/selfdoc")
    parser.add_argument("--manualgen-validation-status", default="FAIL")
    parser.add_argument("--manualgen-validation-caveat", default="Python 3.12 required; current run used Python 3.11.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    out_dir = root / args.out_dir
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commands = load_help_commands(root)

    rows: list[dict[str, str]] = []
    source_file_mentions = 0
    for spec in FEATURES:
        files = collect_files(root, spec.source_globs)
        source_file_mentions += len(files)
        hit_count, examples = keyword_hits(root, files, spec.keywords)
        cmds = command_hits(commands, spec.command_terms)
        rows.append(
            {
                "feature_id": spec.feature_id,
                "title": spec.title,
                "lane": spec.lane,
                "status": status_for(files, hit_count, cmds, spec.planned_terms),
                "commands": "; ".join(cmds[:16]),
                "command_count": str(len(cmds)),
                "source_file_count": str(len(files)),
                "source_keyword_hits": str(hit_count),
                "evidence_files": "; ".join(examples),
                "note": spec.note,
            }
        )

    summary = {
        "generated_utc": generated,
        "feature_count": len(rows),
        "source_file_mentions": source_file_mentions,
        "help_command_count": len(commands),
        "manualgen_validation_status": args.manualgen_validation_status,
        "manualgen_validation_caveat": args.manualgen_validation_caveat,
    }

    csv_path = out_dir / "x64base_engine_feature_crosswalk_v1.csv"
    md_path = out_dir / "x64base_engine_feature_crosswalk_v1.md"
    json_path = out_dir / "x64base_engine_feature_crosswalk_v1.manifest.json"
    manual_section = root / "docs/manuals/developer/generated/x64base_engine_feature_crosswalk_manual_section_v1.md"

    write_csv(csv_path, rows)
    write_markdown(md_path, rows, summary)
    write_markdown(manual_section, rows, summary)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    print(f"wrote {manual_section}")
    print(f"features={len(rows)} help_commands={len(commands)} source_file_mentions={source_file_mentions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
