#!/usr/bin/env python3
"""Load private copies of the reported MCC/Help families; never open source tables."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, default=root / 'build/uidef-native/Release/uidef_paths_test.exe')
    args = parser.parse_args()
    data = root / 'dottalkpp/data'
    cases = [('mcc.dtschema', data / 'dbf/x32', data / 'indexes/x32', 12),
             ('help.dtschemas', data / 'help', data / 'indexes', 10)]
    # Native V2 roots are supplied explicitly. No recursive lookup, replacement
    # of source definitions, invocation of source scripts, or live-catalog writes.
    for definition, tables, indexes, expected in cases:
        schema = data / 'workspaces' / definition
        body = schema.read_text(encoding='utf-8')
        names = re.findall(r'^AREA\s+\d+\s*\|\s*dbf=([^|\r\n]+)', body, re.MULTILINE)
        assert len(names) == expected and body.startswith('DTSHEMA 2'), definition
        stems = {Path(name.strip()).stem.lower() for name in names}
        source_tables = {p.name.lower(): p for p in tables.iterdir() if p.is_file()}
        assert all(name.strip().lower() in source_tables for name in names)
        suffixes = {'.dbf', '.dbt', '.fpt', '.dtx', '.cnx', '.inx', '.idx', '.cdx', '.cdx.meta'}
        families = []
        for source_dir, target_name in [(tables, 'tables'), (indexes, 'indexes')]:
            for p in source_dir.iterdir():
                base, dot, tail = p.name.partition('.')
                if p.is_file() and dot and base.lower() in stems and ('.' + tail.lower()) in suffixes:
                    families.append((p, target_name))
        before = {p: digest(p) for p in [schema, *(p for p, _ in families)]}
        with tempfile.TemporaryDirectory(prefix='workbench-schema-proof-') as temporary:
            destination = Path(temporary)
            for name in ('tables', 'indexes'):
                (destination / name).mkdir()
            shutil.copyfile(schema, destination / definition)
            for p, target_name in families:
                shutil.copyfile(p, destination / target_name / p.name)
            result = subprocess.run([str(args.binary), '--load-definition', str(destination / definition),
                                     str(destination / 'tables'), str(destination / 'indexes')],
                                    capture_output=True, text=True, timeout=60)
            print(result.stdout, end='', flush=True)
            if result.returncode:
                raise RuntimeError(result.stderr + result.stdout)
            assert f'PASS actual schema: {definition} declared={expected} loaded={expected}' in result.stdout
        assert before == {p: digest(p) for p in before}, 'Source family changed'
        print(f'PASS unchanged source schema and {len(before) - 1} family files: {definition}', flush=True)
        for p, sha in before.items():
            print(sha, p, flush=True)


if __name__ == '__main__':
    main()
