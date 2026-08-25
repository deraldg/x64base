# POSIX / WSL Quickstart

This quickstart is for building and running DotTalk++ from the shared source tree at:

```text
D:\code\ccode
```

Under WSL / POSIX that same tree is:

```text
/mnt/d/code/ccode
```

The WSL build lane uses the same project sources as Windows. It does not use a separate fork.

Current policy for this quickstart:

- WSL build uses the same shared source tree as Windows
- the Linux lane may build wxWidgets dependencies when the shared manifest requires them
- CLI/TUI smoke remains the first verification target even when GUI dependencies are present

## 1. Assumptions

This quickstart assumes your WSL lane already has the usual build tools in place:

- `cmake`
- `ninja`
- a working C/C++ toolchain
- an existing `vcpkg` tree, usually at `$HOME/vcpkg`

If those are already present, do not reinstall them.

The only concrete missing dependency observed in the current WSL lane was:

```bash
sudo apt update
sudo apt install -y bison
```

That was needed because the Linux `vcpkg` manifest can pull `gettext`, and that port expects `bison`.

The current wxWidgets / GTK stack also pulled a Linux-side `cairo` requirement for X11 development headers:

```bash
sudo apt update
sudo apt install -y libx11-dev libxft-dev libxext-dev
```

That requirement came from the `wxwidgets -> gtk3 -> cairo[x11]` side of the dependency graph.

For the current shared WSL lane, the practical preflight package set is:

```bash
sudo apt update
sudo apt install -y bison libx11-dev libxft-dev libxext-dev libxi-dev libxtst-dev libxrandr-dev
```

If your WSL image is brand new and truly missing the standard build tools, install them separately before using this guide.

## 2. Fresh WSL Build

The repository already provides a WSL build script:

```text
/mnt/d/code/ccode/wsl_build_dottalkpp.sh
```

Run a fresh build like this:

```bash
cd /mnt/d/code/ccode
sed -i 's/\r$//' wsl_build_dottalkpp.sh
chmod +x wsl_build_dottalkpp.sh
VCPKG_ROOT="$HOME/vcpkg" ./wsl_build_dottalkpp.sh
```

What this does:

- builds from `/mnt/d/code/ccode`
- uses a clean WSL build root at `$HOME/wsl-build/ccode/build-wsl`
- swaps in `vcpkg-wsl.json` for Linux dependency resolution
- allows the Linux dependency graph to resolve shared runtime and GUI libraries from the WSL manifest
- builds `Release`
- copies the finished binary to:

```text
/mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp
```

## 3. Manual Fresh Build Formula

If you want the explicit manual sequence instead of the helper script:

```bash
cd /mnt/d/code/ccode
cp -f vcpkg.json vcpkg.json.win
cp -f vcpkg-wsl.json vcpkg.json
rm -rf "$HOME/wsl-build/ccode/build-wsl"

cmake -S /mnt/d/code/ccode -B "$HOME/wsl-build/ccode/build-wsl" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$HOME/vcpkg/scripts/buildsystems/vcpkg.cmake" \
  -DVCPKG_TARGET_TRIPLET=x64-linux \
  -DCMAKE_BUILD_TYPE=Release \
  -DDOTTALK_WITH_TV=ON \
  -DDOTTALK_WITH_INDEX=ON \
  -DBUILD_PYDOTTALK=OFF

cmake --build "$HOME/wsl-build/ccode/build-wsl" -j

mkdir -p /mnt/d/code/ccode/dottalkpp/bin-wsl
cp -f "$HOME/wsl-build/ccode/build-wsl/src/dottalkpp" /mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp || \
cp -f "$HOME/wsl-build/ccode/build-wsl/dottalkpp" /mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp

cp -f vcpkg.json.win vcpkg.json
rm -f vcpkg.json.win
chmod +x /mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp
```

## 4. If The Build Stops In `vcpkg`

If configure stops while building Linux dependencies and the log says `gettext` could not find `bison`, install it and rerun the same build:

```bash
sudo apt update
sudo apt install -y bison
cd /mnt/d/code/ccode
VCPKG_ROOT="$HOME/vcpkg" ./wsl_build_dottalkpp.sh
```

Do not reinstall WSL, Ninja, or `vcpkg` unless they are actually missing.

If configure fails inside `cairo` with an X11 warning, install the X11 development headers shown above and rerun the same build.

If the helper script exits immediately with a missing-package message, install the packages it names and rerun it. That is now the intended fast-fail behavior.

The current wx/GTK path has already shown these Linux-side requirements:

- `bison` for the `gettext` toolchain path
- `libx11-dev`, `libxft-dev`, `libxext-dev` for `cairo[x11]`
- `libxi-dev`, `libxtst-dev` for `at-spi2-core`
- `libxrandr-dev` for `gtk3`

## 5. Run the WSL Binary

Run DotTalk++ from the runtime data root:

```bash
cd /mnt/d/code/ccode/dottalkpp/data
/mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp
```

One-line form:

```bash
cd /mnt/d/code/ccode/dottalkpp/data && /mnt/d/code/ccode/dottalkpp/bin-wsl/dottalkpp
```

## 6. Smoke Test Sequence

After launch, run this sequence:

```text
VERSION
DO X64
WORKSPACE LOAD x64.dtschemas
SELECT STUDENTS
SET INDEX TO students
SET ORDER TO fname
AREA
SMARTLIST 10
QUIT
```

Expected checkpoints:

- `VERSION` prints the Linux build banner
- `DO X64` sets DBF / INDEXES / LMDB to the `x64` lane
- `WORKSPACE LOAD x64.dtschemas` restores the school workspace
- `SELECT STUDENTS` selects the students area
- `SET INDEX TO students` attaches `students.cdx`
- `SET ORDER TO fname` should succeed if the LMDB backing store is valid
- `AREA` should show the active order and tag
- `SMARTLIST 10` should list ordered student rows

If ordering fails, capture this exact follow-up:

```text
SET INDEX TO students
SET ORDER TO fname
AREA
```

## 7. Notes

- Windows and WSL share the same source tree in `D:\code\ccode`.
- WSL builds should use the WSL-specific manifest lane from `vcpkg-wsl.json`.
- For full rebuilds on this project, it is safer to remove the WSL build directory and reconfigure than to reuse a stale cache.
- If Linux dependency resolution fails, fix the specific missing package from the log instead of re-bootstraping the whole environment.
- The current WSL manifest includes `wxwidgets`, so Linux GUI support may require a few distro packages beyond the cached `vcpkg` tree.
