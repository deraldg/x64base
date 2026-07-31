#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List

EXPECTED_DD064R_STATUS = "DDICT_RUNTIME_HOOK_TRIAGE_READINESS_GREEN"

def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8', errors='replace'))
    except Exception:
        return {}

def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, '') for k in fields})

def safe_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except Exception:
        return path.as_posix()

def infer_namespace(repo: Path) -> Dict[str, Any]:
    candidates = [
        repo / 'src' / 'cli' / 'cmd_catalogcanary.cpp',
        repo / 'src' / 'cli' / 'cmd_about.cpp',
        repo / 'src' / 'cli' / 'cmd_area.cpp',
        repo / 'include' / 'cli' / 'cmd_about.hpp',
    ]
    counts: Dict[str, int] = {}
    sample = ''
    rx = re.compile(r'^\s*namespace\s+([A-Za-z_][A-Za-z0-9_:]*)\s*\{')
    for path in candidates:
        if not path.exists():
            continue
        for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
            m = rx.search(line)
            if m:
                ns = m.group(1)
                if ns != 'std':
                    counts[ns] = counts.get(ns, 0) + 1
                    sample = sample or f'{safe_rel(repo, path)}:{line.strip()}'
    if counts:
        ns = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return {'namespace': ns, 'source': sample, 'inferred': 1}
    return {'namespace': 'dottalk::cli', 'source': 'default fallback', 'inferred': 0}

def infer_dbarea_namespace(repo: Path) -> Dict[str, Any]:
    candidates = [
        repo / 'include' / 'workspace' / 'workarea_manager.hpp',
        repo / 'include' / 'xindex' / 'dbarea_adapt.hpp',
        repo / 'src' / 'cli' / 'cmd_area.cpp',
    ]
    text = ''
    for path in candidates:
        if path.exists():
            text += '\n' + path.read_text(encoding='utf-8', errors='replace')
    if 'xbase::DbArea' in text:
        return {'type': 'xbase::DbArea', 'inferred': 1}
    if 'DbArea' in text:
        return {'type': 'DbArea', 'inferred': 1}
    return {'type': 'xbase::DbArea', 'inferred': 0}

def namespace_open_close(namespace: str) -> tuple[str, str]:
    parts = namespace.split('::') if namespace else []
    open_ns = '\n'.join(f'namespace {part} {{' for part in parts)
    close_ns = '\n'.join(f'}} // namespace {part}' for part in reversed(parts))
    return open_ns, close_ns

def header_text(namespace: str, dbarea_type: str) -> str:
    open_ns, close_ns = namespace_open_close(namespace)
    if dbarea_type == 'xbase::DbArea':
        db_forward = 'namespace xbase { class DbArea; }'
    elif dbarea_type == 'DbArea':
        db_forward = 'class DbArea;'
    else:
        db_forward = 'namespace xbase { class DbArea; }'
    lines = [
        '// DD-065 generated candidate',
        '// DDICT read-only command declaration',
        '// Boundary: no mutation, no HELP/META/CMDHELPCHK change, no CDX/LMDB rebuild',
        '',
        '#pragma once',
        '',
        '#include <string>',
        '',
        db_forward,
        open_ns,
        '',
        f'void cmd_DDICT({dbarea_type}& area, const std::string& raw);',
        '',
        close_ns,
        '',
    ]
    return '\n'.join(lines)

def source_text(namespace: str, dbarea_type: str) -> str:
    open_ns, close_ns = namespace_open_close(namespace)
    lines = [
        '// DD-065 generated candidate',
        '// DDICT read-only command implementation slice',
        '// This first slice provides HELP/usage and safe acknowledgement for accepted subcommands',
        '// It intentionally does not mutate DBF rows, create/rebuild CDX or LMDB, or touch HELP/META/CMDHELPCHK',
        '',
        '#include "cli/cmd_ddict.hpp"',
        '',
        '#include <algorithm>',
        '#include <cctype>',
        '#include <iostream>',
        '#include <sstream>',
        '#include <string>',
        '',
        open_ns,
        '',
        'namespace {',
        '',
        'std::string trim_copy(std::string s) {',
        '    auto not_space = [](unsigned char ch) { return !std::isspace(ch); };',
        '    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));',
        '    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());',
        '    return s;',
        '}',
        '',
        'std::string upper_copy(std::string s) {',
        '    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char ch) {',
        '        return static_cast<char>(std::toupper(ch));',
        '    });',
        '    return s;',
        '}',
        '',
        'std::string first_token(const std::string& s) {',
        '    std::istringstream iss(s);',
        '    std::string tok;',
        '    iss >> tok;',
        '    return tok;',
        '}',
        '',
        'void print_ddict_usage() {',
        '    std::cout',
        '        << "Usage:\\n"',
        '        << "  DDICT HELP\\n"',
        '        << "  DDICT STATUS\\n"',
        '        << "  DDICT TABLES\\n"',
        '        << "  DDICT OBJECTS [TYPE <type>] [PROFILE <profile>]\\n"',
        '        << "  DDICT FIELDS <table>\\n"',
        '        << "  DDICT TAGS <table>\\n"',
        '        << "  DDICT REL <object-id-or-name> [IN|OUT|BOTH]\\n"',
        '        << "  DDICT EVIDENCE <object-id-or-name>\\n"',
        '        << "Notes:\\n"',
        '        << "  DDICT is read-only over the active Data Dictionary catalog.\\n"',
        '        << "  DDICT must not append, replace, delete, pack, zap, create, import, rebuild CDX, rebuild LMDB, or mutate HELP/META/CMDHELPCHK.\\n";',
        '}',
        '',
        'void print_pending(const std::string& sub) {',
        '    std::cout',
        '        << "DDICT " << sub << " is accepted by contract but runtime read implementation is pending the next guarded slice.\\n"',
        '        << "Use DDICT HELP for the accepted command family.\\n";',
        '}',
        '',
        '} // anonymous namespace',
        '',
        f'void cmd_DDICT({dbarea_type}& area, const std::string& raw) {{',
        '    (void)area;',
        '',
        '    const std::string arg = trim_copy(raw);',
        '    const std::string sub = upper_copy(first_token(arg));',
        '',
        '    if (sub.empty() || sub == "HELP" || sub == "?" || sub == "USAGE") {',
        '        print_ddict_usage();',
        '        return;',
        '    }',
        '',
        '    if (sub == "STATUS" || sub == "TABLES" || sub == "OBJECTS" ||',
        '        sub == "FIELDS" || sub == "TAGS" || sub == "REL" ||',
        '        sub == "EVIDENCE") {',
        '        print_pending(sub);',
        '        return;',
        '    }',
        '',
        '    std::cout << "DDICT: unknown subcommand \"" << sub << "\".\\n";',
        '    print_ddict_usage();',
        '}',
        '',
        close_ns,
        '',
    ]
    return '\n'.join(lines)

def smoke_script_text() -> str:
    return '\n'.join([
        '* DD-065 DDICT usage smoke',
        '* Requires runtime registration before this script can pass',
        'ddict help',
        'ddict status',
        'ddict tables',
        'ddict fields ddobject',
        'ddict tags ddattr',
        'ddict rel ddobject both',
        'ddict evidence ddrun',
        'ddict fields nosuchtable',
        '',
    ])

def runlog_text(run_id: str, status: str, header_dest: Path, source_dest: Path, smoke_dest: Path, registered: int) -> str:
    lines = [
        '# DD-065 Guarded DDICT Runtime Source Package Record',
        '',
        f'Run id: `{run_id}`',
        f'Created UTC: `{utc_now()}`',
        f'Status: **{status}**',
        '',
        '## Installed artifacts',
        '',
        '```text',
        f'Header: {header_dest}',
        f'Source: {source_dest}',
        f'Smoke: {smoke_dest}',
        f'Runtime registration: {registered}',
        '```',
        '',
        '## Boundary',
        '',
        'DD-065 v0 installs the initial source candidate only when explicitly requested',
        '',
        'It does not mutate the active Data Dictionary catalog, append/replace/delete/pack/zap DBFs, create/rebuild CDX or LMDB, mutate HELP/META/CMDHELPCHK, or repair catalog content',
        '',
        'Runtime command registration remains a separate guarded step unless a later DD package explicitly patches the dispatcher',
        '',
    ]
    return '\n'.join(lines)

def main() -> int:
    ap = argparse.ArgumentParser(description='DD-065 guarded DDICT runtime source package')
    ap.add_argument('--repo-root', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--run-id', default='DD065-guarded-ddict-runtime-source-package-v0')
    ap.add_argument('--dd064r-dir', default='docs/datadict/reports/DD064R-ddict-runtime-hook-triage-readiness-final-v0')
    ap.add_argument('--header-destination', default='include/cli/cmd_ddict.hpp')
    ap.add_argument('--source-destination', default='src/cli/cmd_ddict.cpp')
    ap.add_argument('--smoke-destination', default='dottalkpp/data/tests/dd065_ddict_usage_smoke.dts')
    ap.add_argument('--apply-source-files', action='store_true')
    ap.add_argument('--replace-existing', action='store_true')
    ap.add_argument('--install-smoke-test', action='store_true')
    ap.add_argument('--write-record', action='store_true')
    ap.add_argument('--record-path', default='docs/datadict/runlog/DD-065_GUARDED_DDICT_RUNTIME_SOURCE_PACKAGE_RECORD.md')
    ap.add_argument('--profile', action='append', default=[])
    ap.add_argument('--fail-on-review', action='store_true')
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out_dir).resolve()
    dd064r_dir = (repo / args.dd064r_dir).resolve()
    header_dest = (repo / args.header_destination).resolve()
    source_dest = (repo / args.source_destination).resolve()
    smoke_dest = (repo / args.smoke_destination).resolve()
    record_path = (repo / args.record_path).resolve()
    out.mkdir(parents=True, exist_ok=True)

    dd064r_manifest = read_json(dd064r_dir / 'dd064r_ddict_runtime_hook_triage_readiness_manifest.json')
    dd064r_ready = dd064r_manifest.get('status') == EXPECTED_DD064R_STATUS

    ns = infer_namespace(repo)
    dbt = infer_dbarea_namespace(repo)

    h_text = header_text(ns['namespace'], dbt['type'])
    cpp_text = source_text(ns['namespace'], dbt['type'])
    dts_text = smoke_script_text()

    generated_dir = out / 'generated_source'
    generated_dir.mkdir(parents=True, exist_ok=True)
    generated_header = generated_dir / 'cmd_ddict.hpp'
    generated_source = generated_dir / 'cmd_ddict.cpp'
    generated_smoke = generated_dir / 'dd065_ddict_usage_smoke.dts'
    generated_header.write_text(h_text, encoding='utf-8')
    generated_source.write_text(cpp_text, encoding='utf-8')
    generated_smoke.write_text(dts_text, encoding='utf-8')

    failures = 0
    review_rows: List[Dict[str, Any]] = []
    if not dd064r_ready:
        failures += 1
        review_rows.append({'issue': 'DD064R_NOT_READY', 'detail': dd064r_manifest.get('status', '')})

    source_installed = 0
    header_installed = 0
    smoke_installed = 0

    if args.apply_source_files and failures == 0:
        for dest, text, label in [(header_dest, h_text, 'HEADER'), (source_dest, cpp_text, 'SOURCE')]:
            if dest.exists() and not args.replace_existing:
                failures += 1
                review_rows.append({'issue': f'{label}_DESTINATION_EXISTS', 'detail': str(dest)})
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text, encoding='utf-8')
                if label == 'HEADER':
                    header_installed = 1
                else:
                    source_installed = 1

    if args.install_smoke_test and failures == 0:
        if smoke_dest.exists() and not args.replace_existing:
            failures += 1
            review_rows.append({'issue': 'SMOKE_DESTINATION_EXISTS', 'detail': str(smoke_dest)})
        else:
            smoke_dest.parent.mkdir(parents=True, exist_ok=True)
            smoke_dest.write_text(dts_text, encoding='utf-8')
            smoke_installed = 1

    record_written = 0
    if args.write_record:
        record_path.parent.mkdir(parents=True, exist_ok=True)
        record_written = 1

    if args.apply_source_files and source_installed and header_installed:
        status = 'DDICT_RUNTIME_SOURCE_FILES_INSTALLED_REGISTRATION_PENDING' if failures == 0 else 'DDICT_RUNTIME_SOURCE_PACKAGE_REVIEW'
    elif args.install_smoke_test and smoke_installed:
        status = 'DDICT_RUNTIME_SMOKE_TEST_INSTALLED_REGISTRATION_PENDING' if failures == 0 else 'DDICT_RUNTIME_SOURCE_PACKAGE_REVIEW'
    else:
        status = 'DDICT_RUNTIME_SOURCE_PACKAGE_READY' if failures == 0 else 'DDICT_RUNTIME_SOURCE_PACKAGE_REVIEW'

    if args.write_record:
        record_path.write_text(runlog_text(args.run_id, status, header_dest, source_dest, smoke_dest, 0), encoding='utf-8')

    source_ledger = [
        {'artifact': 'header', 'generated_path': str(generated_header), 'destination': str(header_dest), 'installed': header_installed, 'exists_after': int(header_dest.exists()), 'action': 'INSTALLED' if header_installed else 'GENERATED_REPORT_ARTIFACT_ONLY'},
        {'artifact': 'source', 'generated_path': str(generated_source), 'destination': str(source_dest), 'installed': source_installed, 'exists_after': int(source_dest.exists()), 'action': 'INSTALLED' if source_installed else 'GENERATED_REPORT_ARTIFACT_ONLY'},
        {'artifact': 'smoke_test', 'generated_path': str(generated_smoke), 'destination': str(smoke_dest), 'installed': smoke_installed, 'exists_after': int(smoke_dest.exists()), 'action': 'INSTALLED' if smoke_installed else 'GENERATED_REPORT_ARTIFACT_ONLY'},
    ]

    next_patch_rows = [
        {'next_step': 'DD-066_REGISTRATION_DISCOVERY', 'purpose': 'Find exact dispatcher and build registration points locally', 'allowed_now': 0, 'reason': 'DD-065 v0 avoids blind dispatcher patching'},
        {'next_step': 'DD-066_CMAKE_OR_BUILD_INTEGRATION', 'purpose': 'Add cmd_ddict.cpp to build only after exact build file is found', 'allowed_now': 0, 'reason': 'Build integration varies by local project layout'},
        {'next_step': 'DD-066_RUNTIME_SMOKE', 'purpose': 'Run DDICT HELP after registration', 'allowed_now': 0, 'reason': 'Requires dispatcher registration first'},
    ]

    gate_rows = [
        {'gate': 'dd064r_readiness_green', 'expected': EXPECTED_DD064R_STATUS, 'observed': dd064r_manifest.get('status', ''), 'pass': int(dd064r_ready)},
        {'gate': 'source_artifacts_generated', 'expected': 1, 'observed': int(generated_header.exists() and generated_source.exists()), 'pass': int(generated_header.exists() and generated_source.exists())},
        {'gate': 'source_files_installed_when_requested', 'expected': int(args.apply_source_files), 'observed': int(source_installed and header_installed), 'pass': int((not args.apply_source_files) or (source_installed and header_installed))},
        {'gate': 'smoke_installed_when_requested', 'expected': int(args.install_smoke_test), 'observed': smoke_installed, 'pass': int((not args.install_smoke_test) or smoke_installed)},
        {'gate': 'record_written_when_requested', 'expected': int(args.write_record), 'observed': record_written, 'pass': int((not args.write_record) or record_written)},
        {'gate': 'runtime_registration_deferred', 'expected': 0, 'observed': 0, 'pass': 1},
    ]

    boundary_rows = [
        {'boundary': 'guarded_source_package', 'observed': 1, 'required': 1, 'pass': 1},
        {'boundary': 'cxx_source_files_created', 'observed': int(source_installed and header_installed), 'required': int(args.apply_source_files), 'pass': int((not args.apply_source_files) or (source_installed and header_installed))},
        {'boundary': 'runtime_command_registration', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'active_catalog_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'dbf_append_replace_delete_pack_zap', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'cdx_lmdb_create_rebuild', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'help_meta_cmdhelpchk_mutation', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'catalog_regeneration', 'observed': 0, 'required': 0, 'pass': 1},
        {'boundary': 'manual_row_repair', 'observed': 0, 'required': 0, 'pass': 1},
    ]

    write_csv(out / 'dd065_source_install_ledger.csv', source_ledger, ['artifact', 'generated_path', 'destination', 'installed', 'exists_after', 'action'])
    write_csv(out / 'dd065_next_patch_plan.csv', next_patch_rows, ['next_step', 'purpose', 'allowed_now', 'reason'])
    write_csv(out / 'dd065_gate_ledger.csv', gate_rows, ['gate', 'expected', 'observed', 'pass'])
    write_csv(out / 'dd065_review_rows.csv', review_rows, ['issue', 'detail'])
    write_csv(out / 'dd065_no_mutation_boundary_ledger.csv', boundary_rows, ['boundary', 'observed', 'required', 'pass'])

    report_lines = [
        '# DD-065 Guarded DDICT Runtime Source Package',
        '',
        f'Run id: `{args.run_id}`',
        f'Status: **{status}**',
        f'Created UTC: `{utc_now()}`',
        '',
        '## Purpose',
        '',
        'DD-065 creates the first guarded DDICT runtime source package',
        '',
        '## Prerequisite',
        '',
        f'- DD-064R status: `{dd064r_manifest.get("status", "")}`',
        '',
        '## Inference',
        '',
        f'- Namespace: `{ns["namespace"]}`',
        f'- Namespace source: `{ns["source"]}`',
        f'- DbArea type: `{dbt["type"]}`',
        '',
        '## Generated artifacts',
        '',
        f'- Header report artifact: `{generated_header}`',
        f'- Source report artifact: `{generated_source}`',
        f'- Smoke report artifact: `{generated_smoke}`',
        '',
        '## Installed artifacts',
        '',
        f'- Header installed: **{header_installed}**',
        f'- Source installed: **{source_installed}**',
        f'- Smoke installed: **{smoke_installed}**',
        '- Runtime registration: **0**',
        '',
        '## Boundary',
        '',
        'DD-065 v0 does not patch the dispatcher or build system',
        'Runtime command registration remains pending for DD-066 or later after exact local hook discovery',
        '',
    ]
    (out / 'DD065_GUARDED_DDICT_RUNTIME_SOURCE_PACKAGE_REPORT.md').write_text('\n'.join(report_lines), encoding='utf-8')

    manifest = {
        'contract': 'dd065_guarded_ddict_runtime_source_package_v0',
        'run_id': args.run_id,
        'created_utc': utc_now(),
        'status': status,
        'repo_root': str(repo),
        'profiles': args.profile,
        'dd064r_status': dd064r_manifest.get('status', ''),
        'namespace': ns['namespace'],
        'namespace_inferred': ns['inferred'],
        'dbarea_type': dbt['type'],
        'dbarea_type_inferred': dbt['inferred'],
        'apply_source_files': int(args.apply_source_files),
        'replace_existing': int(args.replace_existing),
        'install_smoke_test': int(args.install_smoke_test),
        'header_installed': header_installed,
        'source_installed': source_installed,
        'smoke_installed': smoke_installed,
        'record_written': record_written,
        'record_path': str(record_path) if record_written else '',
        'runtime_command_registration': 0,
        'active_catalog_mutation': 0,
        'dbf_append_replace_delete_pack_zap': 0,
        'cdx_lmdb_create_rebuild': 0,
        'help_meta_cmdhelpchk_mutation': 0,
        'failures': failures,
        'next_recommended_action': 'DD-066 registration/build integration discovery and guarded dispatcher patch',
    }
    write_json(out / 'dd065_guarded_ddict_runtime_source_package_manifest.json', manifest)

    print(f"DD-065 guarded DDICT runtime source package manifest: {out / 'dd065_guarded_ddict_runtime_source_package_manifest.json'}")
    print(f"status: {status}; header_installed: {header_installed}; source_installed: {source_installed}; smoke_installed: {smoke_installed}; registration: 0; failures: {failures}")
    return 2 if (args.fail_on_review and failures) else 0

if __name__ == '__main__':
    raise SystemExit(main())
