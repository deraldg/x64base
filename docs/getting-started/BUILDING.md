# Building x64base

## Portable core

Install CMake 3.21 or newer, Ninja, and a C++20 compiler, then run:

```sh
cmake --preset core
cmake --build --preset core
ctest --preset core
```

This profile intentionally excludes optional LMDB index commands, Turbo
Vision, wxWidgets, and Python bindings. The LMDB library remains a baseline
dependency for runtime message-catalog mirrors. This is the smallest supported
proof that the public source configures, compiles, and runs its core tests.

## Windows with Visual Studio 2022

```powershell
cmake --preset windows-core
cmake --build --preset windows-core --config Release
ctest --preset windows-core
```

## Linux, WSL, or macOS

```sh
cmake --preset core
cmake --build --preset core
ctest --preset core
```

## Optional dependency lanes

The repository's vcpkg manifest defines features for `index`, `tv`, `wx`, and
`python`. Set `VCPKG_ROOT`, select its CMake toolchain, and enable only the
features needed by the selected CMake options. For example:

```sh
cmake --preset index-vcpkg
cmake --build --preset index-vcpkg
ctest --preset index-vcpkg
```

Do not add personal package-manager or dependency paths to tracked CMake files.
Use environment variables or an untracked `CMakeUserPresets.json`.
