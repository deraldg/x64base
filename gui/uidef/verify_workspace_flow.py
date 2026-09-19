#!/usr/bin/env python3
"""Dogfood NEW/SWITCH through the console using only disposable fixture copies.

Recreates areas 0..12 / 13..55 and the empty-workspace flow. Keeps the isolated
run directory and transcript for review. RAM capacity is covered by session_test.
"""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=root / 'build/uidef-native')
    args = parser.parse_args()
    source_binary = args.build_dir / 'src/Release/dottalkpp.exe'
    fixture = subprocess.run([str(args.build_dir / 'Release/uidef_paths_test.exe')],
                             check=True, capture_output=True, text=True, timeout=60)
    fixture_data = Path(next(line.split('=', 1)[1] for line in fixture.stdout.splitlines()
                             if line.startswith('data_root=')))
    source = fixture_data / 'dbf/lesson space/STUDENTS.dbf'
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    home = Path(tempfile.mkdtemp(prefix='workbench-flow-'))
    bin_dir, data = home / 'bin', home / 'data'
    bin_dir.mkdir()
    data.mkdir()
    binary = bin_dir / 'dottalkpp.exe'
    shutil.copy2(source_binary, binary)
    for dll in source_binary.parent.glob('*.dll'):
        shutil.copy2(dll, bin_dir / dll.name)
    (bin_dir / 'dottalkpp.ini').write_text('SET ECHO OFF\nSET PAGING OFF\nSET TALK OFF\n', encoding='ascii')
    for folder, count in [('first', 13), ('second', 43)]:
        target = data / folder
        target.mkdir()
        for i in range(count):
            shutil.copy2(source, target / f'TABLE{i:03}.dbf')
    commands = [
        f'SET PATH DBF {data / "first"}', 'WORKSPACE OPEN dbf NOINDEX',
        "? 'FLOW_INITIAL'", 'GPS',
        'WORKSPACE NEW ws2', "? 'FLOW_NEW_EMPTY'", 'GPS',
        f'SET PATH DBF {data / "second"}', 'WORKSPACE OPEN dbf NOINDEX',
        "? 'FLOW_OPEN_SECOND'", 'GPS', 'SELECT 55', 'SWITCH DEFAULT',
        "? 'FLOW_BACK_DEFAULT'", 'GPS', 'SWITCH ws2',
        "? 'FLOW_BACK_SECOND'", 'GPS', 'WORKSPACE NEW ws3',
        "? 'FLOW_THIRD_EMPTY'", 'GPS', 'SWITCH ws2', 'SWITCH ws3',
        "? 'FLOW_SWITCH_EMPTY'", 'GPS', 'SWITCH ws2',
        'WORKSPACE NEW ws2', 'SWITCH Missing',
        "? 'FLOW_REFUSALS'", 'GPS', 'SET PATH', 'WORKDESK', 'QUIT',
    ]
    script = home / 'flow.dts'
    script.write_text('\n'.join(commands) + '\n', encoding='ascii')
    result = subprocess.run([str(binary), '--script', str(script)], cwd=home,
                            capture_output=True, text=True, timeout=90)
    transcript = result.stdout + '\n' + result.stderr
    (home / 'transcript.txt').write_text(transcript, encoding='utf-8')
    print('flow_home=' + str(home), flush=True)
    print('console_sha256=' + hashlib.sha256(binary.read_bytes()).hexdigest(), flush=True)
    if result.returncode:
        raise RuntimeError(f'Console exit {result.returncode}; see isolated transcript')
    def segment(name):
        text = transcript.split(name, 1)[1]
        return text.split('FLOW_', 1)[0]

    for label, slot, owner in [('FLOW_INITIAL', 0, 'DEFAULT'),
                               ('FLOW_OPEN_SECOND', 13, 'ws2'),
                               ('FLOW_BACK_DEFAULT', 0, 'DEFAULT'),
                               ('FLOW_BACK_SECOND', 13, 'ws2'),
                               ('FLOW_REFUSALS', 13, 'ws2')]:
        text = segment(label)
        assert re.search(rf'Cursor: Area {slot} of .*Table TABLE000', text), (label, text[:900])
        assert f'owning {owner} ' in text and f'current {owner} ' in text, (label, text[:900])
    for label, slot, owner in [('FLOW_NEW_EMPTY', 13, 'ws2'),
                               ('FLOW_THIRD_EMPTY', 56, 'ws3'),
                               ('FLOW_SWITCH_EMPTY', 56, 'ws3')]:
        text = segment(label)
        assert re.search(rf'Cursor: Area {slot} of .*No table open', text), (label, text[:900])
        assert 'owning (none)' in text and f'current {owner} ' in text, (label, text[:900])
    assert '13 table(s) opened into area(s) 0..12' in transcript
    assert '43 table(s) opened into area(s) 13..55' in transcript
    assert 'WORKSPACE NEW: a workspace named ws2 already exists' in transcript
    assert 'WORKSPACE SWITCH: no such workspace: Missing' in transcript
    final = segment('FLOW_REFUSALS')
    assert re.search(r'Open\s+: 3\b', final) and re.search(r'Open areas\s+: 56\b', final)
    assert re.search(r'DBF\s+= ' + re.escape(str(data / 'second')), final)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    print('PASS console flow: global areas 0..12 and 13..55; NEW activates with no table; SWITCH selects destination first area; empty SWITCH uses area 56; duplicate NEW and unknown SWITCH preserve cursors, roots and workspace count; fixture source unchanged')


if __name__ == '__main__':
    main()
