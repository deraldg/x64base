#!/usr/bin/env python3
"""Build/launch the generated native Workbench, without staging over APPGUI.

Windows: uses the installed VS 2022 toolchain and an isolated dependency tree.
Other hosts: uses CMake's default generator and installed wxWidgets.
Package installation requires --install-deps. No branch or live database writes.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=root / 'build' / 'uidef-native')
    parser.add_argument('--deps-dir', type=Path, default=root / 'build' / 'uidef-deps')
    parser.add_argument('--install-deps', action='store_true', help='Install required vcpkg packages in --deps-dir')
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--output-name', default='arctictalk_workbench', help='Distinct filename preserves a running preview')
    parser.add_argument('--catalog', type=Path, help='Optional saved-catalog override; otherwise follow native WORKSPACES')
    args = parser.parse_args()
    configure = ['cmake', '-S', str(root), '-B', str(args.build_dir),
                 '-DDOTTALK_BUILD_UIDEF_WORKBENCH=ON', '-DDOTTALK_PRODUCT=DEVELOPMENT',
                 '-DDOTTALK_INDEX_MODE=LMDB', '-DDOTTALK_WITH_TV=OFF', '-DDOTTALK_WITH_WX=OFF',
                 '-DDOTTALK_WITH_GUI=OFF', '-DDOTTALK_BUILD_BBSD=OFF', '-DBUILD_TESTING=OFF',
                 '-DBUILD_PYDOTTALK=OFF', '-DPython3_EXECUTABLE=' + sys.executable,
                 '-DUIDEF_WORKBENCH_OUTPUT_NAME=' + args.output_name]
    if os.name == 'nt':
        configure += ['-G', 'Visual Studio 17 2022', '-A', 'x64']
        vcpkg = os.environ.get('VCPKG_ROOT')
        installed = args.deps_dir.resolve()
        if not vcpkg:
            parser.error('Set VCPKG_ROOT to the installed vcpkg tool.')
        if args.install_deps:
            subprocess.run([str(Path(vcpkg) / 'vcpkg.exe'), 'install', 'wxwidgets:x64-windows',
                            'libsodium:x64-windows', 'lmdb:x64-windows', 'nlohmann-json:x64-windows',
                            'sqlite3:x64-windows', '--classic',
                            '--x-install-root=' + str(installed)], check=True)
        if not (installed / 'x64-windows/share/wxwidgets').is_dir():
            parser.error('Run with --install-deps, or provide --deps-dir with existing wxWidgets, libsodium and LMDB.')
        # Refresh package hints when moving away from the shared root build's
        # install tree, which may legitimately remove its optional wx feature.
        configure += ['-U*wxWidgets*', '-UWX_*', '-UVCPKG_SODIUM*', '-Uunofficial*']
        configure += ['-DCMAKE_TOOLCHAIN_FILE=' + str(Path(vcpkg) / 'scripts/buildsystems/vcpkg.cmake'),
                      '-DVCPKG_MANIFEST_INSTALL=OFF', '-DVCPKG_INSTALLED_DIR=' + str(installed)]
    subprocess.run(configure, check=True)
    subprocess.run(['cmake', '--build', str(args.build_dir), '--config', 'Release', '--target',
                    'arctictalk_workbench', 'uidef_catalog_test', 'uidef_session_test', 'uidef_paths_test', 'uidef_images_test', 'uidef_table_test', 'uidef_save_test', 'uidef_memo_image_test', 'uidef_store_image_test', '--parallel', '4'], check=True)
    subprocess.run(['ctest', '--test-dir', str(args.build_dir), '-C', 'Release', '--output-on-failure'], check=True)
    binary = args.build_dir / ('Release/' + args.output_name + '.exe' if os.name == 'nt' else args.output_name)
    print('Workbench:', binary)
    if args.launch:
        subprocess.Popen([str(binary)] + (['--catalog', str(args.catalog)] if args.catalog else []))


if __name__ == '__main__':
    main()
