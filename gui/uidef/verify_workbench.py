#!/usr/bin/env python3
"""Verify the native Workbench against a catalog without modifying that catalog.

--capture opens the native window briefly and saves its client view. Without it,
Windows smoke processes start hidden, except M1 and M2 focus/keyboard checks.
The result marker and process exit both
have to pass. Fresh temporary output paths prevent acceptance of stale proof.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=root / 'build/uidef-native')
    parser.add_argument('--catalog', type=Path, default=root / 'dottalkpp/data/workspaces/WORKSPACES.dbf')
    parser.add_argument('--capture', type=Path)
    parser.add_argument('--output-name', default='arctictalk_workbench')
    args = parser.parse_args()
    binary_dir = args.build_dir / 'Release' if os.name == 'nt' else args.build_dir
    suffix = '.exe' if os.name == 'nt' else ''
    workbench = binary_dir / (args.output_name + suffix)
    paths = [args.catalog, args.catalog.with_suffix('.dtx')]
    before = {str(p): digest(p) for p in paths if p.exists()}
    subprocess.run([sys.executable, '-B', str(root / 'gui/uidef/workbench_m1_test.py')], check=True, timeout=30)
    subprocess.run([str(binary_dir / ('uidef_catalog_test' + suffix))], check=True, timeout=30)
    session_proof = subprocess.run([str(binary_dir / ('uidef_session_test' + suffix))], check=True,
                                   timeout=60, capture_output=True, text=True)
    print(session_proof.stdout, end='', flush=True)
    if 'PASS workspace navigation:' not in session_proof.stdout:
        raise RuntimeError('Session test did not report its workspace-navigation proof marker')
    subprocess.run([str(binary_dir / ('uidef_save_test' + suffix))], check=True, timeout=60)
    memo_proof = subprocess.run([str(binary_dir / ('uidef_memo_image_test' + suffix))], check=True,
                                timeout=60, capture_output=True, text=True)
    print(memo_proof.stdout, end='', flush=True)
    if not memo_proof.stdout.startswith('PASS memo image:'):
        raise RuntimeError('Memo image test did not report its proof marker')
    store_proof = subprocess.run([str(binary_dir / ('uidef_store_image_test' + suffix))], check=True,
                                 timeout=60, capture_output=True, text=True)
    print(store_proof.stdout, end='', flush=True)
    if not store_proof.stdout.startswith('PASS store image:'):
        raise RuntimeError('Image storage test did not report its proof marker')
    store_sources = dict(line.split('=', 1) for line in store_proof.stdout.splitlines() if '=' in line)
    table_proof = subprocess.run([str(binary_dir / ('uidef_table_test' + suffix))], check=True, timeout=60,
                                 capture_output=True, text=True)
    print(table_proof.stdout, end='', flush=True)
    table_source = next(line.removeprefix('table_source=') for line in table_proof.stdout.splitlines()
                        if line.startswith('table_source='))
    nested_proof = subprocess.run([str(binary_dir / ('uidef_images_test' + suffix))], check=True, timeout=60,
                                  capture_output=True, text=True)
    print(nested_proof.stdout, end='', flush=True)
    if 'PASS image export:' not in nested_proof.stdout:
        raise RuntimeError('Image test did not report its export proof marker')
    nested_home = next(line.removeprefix('session_home=') for line in nested_proof.stdout.splitlines()
                       if line.startswith('session_home='))
    subprocess.run([str(binary_dir / ('uidef_images_test' + suffix)), '--catalog', str(args.catalog)], check=True, timeout=60)
    subprocess.run([str(binary_dir / ('uidef_catalog_test' + suffix)), '--catalog', str(args.catalog)],
                   check=True, timeout=30)
    paths_proof = subprocess.run([str(binary_dir / ('uidef_paths_test' + suffix))], check=True, timeout=60,
                                 capture_output=True, text=True)
    print(paths_proof.stdout, end='', flush=True)
    if not paths_proof.stdout.startswith('PASS paths:'):
        raise RuntimeError('Native path workflow proof missing')
    data_root = next(line.removeprefix('data_root=') for line in paths_proof.stdout.splitlines()
                     if line.startswith('data_root='))
    flow_catalog = next(line.removeprefix('catalog_flow=') for line in paths_proof.stdout.splitlines()
                        if line.startswith('catalog_flow='))
    if 'PASS catalog flow:' not in paths_proof.stdout:
        raise RuntimeError('Exact saved-version native proof missing')
    with tempfile.TemporaryDirectory(prefix='workbench-proof-') as temp:
        for mode in ('inspect', 'live-session', 'browse', 'edit', 'save', 'image', 'nested-image', 'memo-image', 'export-image', 'store-image', 'navigation', 'paths', 'loadview', 'openload', 'm1', 'catalog-flow', 'm3', 'close-during-read'):
            result = Path(temp) / (mode + '.txt')
            catalog = Path(nested_home) / 'workspaces/WORKSPACES.dbf' if mode in ('nested-image', 'memo-image', 'export-image') else args.catalog
            command = [str(workbench), '--catalog', str(catalog),
                       '--smoke', str(result), '--private-session']
            capture = Path(temp) / 'window.png'
            if mode == 'close-during-read':
                command.append('--close-during-read')
            if mode == 'live-session':
                command.append('--live-smoke')
            if mode == 'browse':
                command += ['--browse-smoke', '--table-source', table_source]
            if mode == 'm3':
                command += ['--m3-smoke', '--table-source', table_source]
            if mode == 'edit':
                command += ['--edit-smoke', '--table-source', table_source]
            if mode == 'save':
                command += ['--save-smoke', '--table-source', table_source]
            if mode == 'image':
                command.append('--image-smoke')
            if mode == 'nested-image':
                command.append('--nested-smoke')
            if mode == 'memo-image':
                command.append('--memo-image-smoke')
            if mode == 'export-image':
                command.append('--export-image-smoke')
            if mode == 'store-image':
                command += ['--store-image-smoke', '--table-source', store_sources['memo_source'],
                            '--image-source', store_sources['image_source']]
            if mode == 'navigation':
                command += ['--navigation-smoke', '--table-source', table_source]
            if mode == 'catalog-flow':
                command = [str(workbench), '--catalog', flow_catalog, '--private-session', '--catalog-flow-smoke',
                           '--table-source', str(Path(data_root) / 'dbf/button load/STUDENTS.dbf'), '--smoke', str(result)]
            if mode in ('paths', 'loadview', 'openload', 'm1'):
                command = [str(workbench), '--data-root', data_root,
                           '--smoke', str(result), '--' + mode + '-smoke']
            if mode != 'close-during-read' and args.capture:
                command += ['--capture', str(capture)]
            startup = None
            if os.name == 'nt' and mode not in ('m1', 'navigation', 'catalog-flow') and not (mode != 'close-during-read' and args.capture):
                startup = subprocess.STARTUPINFO()
                startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup.wShowWindow = 0
            subprocess.run(command, check=True, timeout=35, startupinfo=startup)
            report = result.read_text()
            print(report, end='', flush=True)
            if not report.startswith('PASS '):
                raise RuntimeError('Native smoke failed: ' + mode)
            if mode != 'close-during-read' and 'navigator_ok=1\n' not in report:
                raise RuntimeError('Navigator does not agree with engine snapshot: ' + mode)
            if mode == 'navigation' and ('navigation_steps=27\n' not in report or 'navigation_ok=1\n' not in report):
                raise RuntimeError('M2 tree/keyboard/context/stale-target proof did not complete')
            if mode == 'm3' and ('m3_steps=18\n' not in report or 'm3_ok=1\n' not in report):
                raise RuntimeError('M3 modal, record, memo and buffer proof did not complete')
            if mode == 'catalog-flow' and ('catalog_flow_steps=5\n' not in report or 'catalog_flow_ok=1\n' not in report):
                raise RuntimeError('Direct catalog modal and field readback proof did not complete')
            if mode != 'close-during-read' and args.capture:
                destination = args.capture if mode == 'inspect' else args.capture.with_stem(args.capture.stem + '-' +
                    {'live-session': 'live', 'browse': 'browse', 'edit': 'edit', 'save': 'save', 'image': 'image', 'nested-image': 'nested', 'memo-image': 'memo-image', 'export-image': 'export', 'store-image': 'store', 'navigation': 'navigation', 'paths': 'paths', 'loadview': 'loadview', 'openload': 'openload', 'm1': 'm1', 'catalog-flow': 'catalog-flow', 'm3': 'm3'}[mode])
                shutil.copyfile(capture, destination)
                if mode == 'm1':
                    for form in ('NEW', 'OPEN', 'LOAD', 'SAVE', 'RUN'):
                        modal = capture.with_stem(capture.stem + '-modal-' + form)
                        shutil.copyfile(modal, args.capture.with_stem(args.capture.stem + '-modal-' + form))
                    shutil.copyfile(capture.with_stem(capture.stem + '-menus'), args.capture.with_stem(args.capture.stem + '-menus'))
                if mode == 'catalog-flow':
                    for form in ('HYD', 'LOAD'):
                        shutil.copyfile(capture.with_stem(capture.stem + '-catalog-' + form),
                                        args.capture.with_stem(args.capture.stem + '-catalog-' + form))
    after = {str(p): digest(p) for p in paths if p.exists()}
    if before != after:
        raise RuntimeError('Input catalog family changed during verification')
    print('PASS input SHA-256 unchanged')
    for path, sha in after.items():
        print(sha, path)
    print('binary_sha256=' + digest(workbench))


if __name__ == '__main__':
    main()
