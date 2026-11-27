# DotTalk++ on Android (Termux) -- quickstart

Status: review-needed. Milestone 1 of the native Termux port: build the real
`dottalkpp` CLI on the device and reach its prompt, with no change to database
semantics. Not yet measured on a device; see "What has been verified" below.

## What this is

A NATIVE build. Termux's own clang compiles `dottalkpp` on the phone for the
phone's userspace (normally `aarch64`). It is not an Android NDK cross-compile,
not an APK, and does not use vcpkg. Android is treated as one more Linux-like
platform:

    Windows  -> dottalkpp.exe
    Ubuntu   -> dottalkpp
    WSL      -> dottalkpp
    Android  -> dottalkpp (Termux)

## Preset

`termux-core` (in `CMakePresets.json`): LEAN / PROD, `DOTTALK_INDEX_MODE=NONE`,
no Turbo Vision, GUI, wxWidgets or Python bindings, tests ON. It sets
`DOTTALK_SYSTEM_DEPS=ON`, which resolves lmdb, libsodium and nlohmann_json from
Termux packages via pkg-config (`cmake/sysdeps/DotTalkSystemDeps.cmake`) while
leaving every vcpkg preset untouched. SQLite comes from CMake's FindSQLite3.

LMDB is still linked with index mode NONE: the runtime message catalog keeps
LMDB mirrors regardless of the index engine (`src/CMakeLists.txt`).

## Build

Keep the source tree and all live data under `$HOME`, not shared storage
(`/sdcard`): shared storage is FUSE-backed and does not give the engine's
`.lock` sidecars and rename-based writes the semantics they assume.

    pkg update && pkg upgrade
    pkg install git clang cmake ninja pkg-config python \
        liblmdb libsodium nlohmann-json sqlite

    cd ~
    git clone https://github.com/deraldg/x64base.git
    cd x64base
    git checkout development

    cmake --preset termux-core
    cmake --build --preset termux-core --target dottalkpp

A phone has few cores and little RAM compared with a desktop. If the build is
killed (Android's low-memory killer) lower parallelism:
`cmake --build --preset termux-core --target dottalkpp -j2`.

## Run

    bash ./datarun.sh

`datarun.sh` finds the newest built `dottalkpp` (it searches
`build/termux-core`), stages it into `dottalkpp/bin`, and runs it from
`dottalkpp/data`. Call it through `bash` rather than `./datarun.sh` if
`/usr/bin/env` is not remapped on your device (Termux normally remaps it via
termux-exec).

Batch form:

    bash ./datarun.sh -CommandLines 'VERSION' 'HELP'

## What has been verified

- Configure and full build of the `termux-core` preset with clang on x86_64
  Ubuntu (a stand-in: same flags and dependency path, glibc and libstdc++ rather
  than Bionic and libc++).
- The vcpkg presets do not include the system-deps path (option defaults OFF).

Not yet verified: anything on an Android device. The acceptance checklist for
the port (open/append/update DBF, FPT64 memos, locking, SQLsel, relations,
clean shutdown, regression suite) is run on the device after this milestone.
