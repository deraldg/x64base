# DotTalk++ GUI Build And Run v1

Status: active developer note.

## Python GUI

The Python/Tkinter frontend is usable now and has no third-party package
requirement.

Run the visible GUI:

```powershell
python tools/gui_preview/dottalk_gui_preview.py
```

Locale smoke:

```powershell
python tools/gui_preview/dottalk_gui_preview.py --locale es
python tools/gui_preview/dottalk_gui_preview.py --locale it
```

After launch, use the `Language` menu to switch among the seeded GUI locales
without restarting.

The Python Workbench opens multiple DBFs as workspace areas. The Workspace menu
mirrors runtime-backed workspace actions through the DotTalk++ command bridge.
Use Workspace > Path Roots to inspect the GUI root/data/script path decisions,
and Workspace > SET DBF / SET INDEX to exercise the reserved menu skeletons.

The two canonical runtime workspace actions are exposed directly:

- Workspace > WORKSPACE OPEN Directory... sends `workspace open <dir>` through
  the DotTalk++ command bridge. The dialog can append `CDX`, `CNX`, or `INX`
  index/key attachment, plus `FALLBACK`, `recursive`, and `TABLE`.
- Workspace > WORKSPACE LOAD Schema... sends `workspace load name.dtschemas`
  through the DotTalk++ command bridge for saved workspace graphs, including
  restored areas, relations, paths, and active tags when the file contains them.
- Workspace > Save Workspace / Save Workspace As... sends `workspace save
  name.dtschema` through the same bridge. The Python lane no longer owns a
  private bootstrap schema format.

The command box has two lanes:

- GUI-native workbench commands: `help`, `areas`, `list`, `structure`,
  `workspace graph`, `paths`, `setpath`.
- CLI compatibility commands: prefix with `cli`, for example `cli help` or
  `cli list`.

The Run menu includes `SCAN...ENDSCAN...`. It accepts a multiline DotTalk++
scan block, sends it through the CLI bridge, and opens a separate result window
when the command completes. The seeded example uses DotTalk++ command vocabulary:
`DO X64`, `USE STUDENTS`, `SCAN`, `TUPLE`, `SKIP`, `ENDSCAN`.

`DO` / `DOTSCRIPT`, `LOOP` / `ENDLOOP`, and `VAR` / `SET VAR` are treated as
DotTalk++ CLI/script concepts. They flow through the command bridge until the
native GUI runtime command service is mature enough to own them directly.

The CLI lane runs `dottalkpp --script` in a temporary script when a CLI
executable is discoverable. To force the executable path:

```powershell
$env:DOTTALKPP_GUI_CLI = "build\src\Release\dottalkpp.exe"
```

Regenerate GUI message adapters after editing
`dottalkpp/data/messaging/gui_messages.csv`:

```powershell
python tools/gui/generate_gui_messages.py
python tools/gui/generate_gui_messages.py --check
```

Run with an initial table:

```powershell
python tools/gui_preview/dottalk_gui_preview.py build/src/Release/dbf/RM_BROWSE_V1.dbf
```

Run the headless backend smoke:

```powershell
python tools/gui_preview/test_gui_backend.py
```

The backend tries `pydottalk` first. If `pydottalk` is not importable, it uses a
read-only pure-Python DBF preview reader.

## C++ GUI Core

Configure against the canonical Windows build root:

```powershell
cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -D CMAKE_TOOLCHAIN_FILE=$env:VCPKG_ROOT\scripts\buildsystems\vcpkg.cmake -D VCPKG_TARGET_TRIPLET=x64-windows -D DOTTALK_WITH_GUI=ON -D DOTTALK_WITH_WX=OFF -D DOTTALK_WITH_TV=OFF -D DOTTALK_WITH_INDEX=ON -D BUILD_TESTING=ON
```

Build and test:

```powershell
cmake --build build --config Release --target dottalk_gui_core_async_smoke
ctest --test-dir build -C Release -R dottalk_gui_core_async_smoke --output-on-failure
```

Workbench locale smoke:

```powershell
build\src\gui\wx\Release\dottalk_wb_next.exe --locale es
build\src\gui\wx\Release\dottalk_wb_next.exe --locale it
```

After launch, use the `Language` menu to switch among the seeded GUI locales
without restarting.

## C++ wxWidgets Frontend

`dottalk_wb_next` is the active native Workbench target:

```powershell
cmake --build build --config Release --target dottalk_wb_next
```

This currently requires wxWidgets to be installed for the selected toolchain.
`wxwidgets` is listed in the vcpkg manifests so future vcpkg manifest installs
can provide it.

After building, launch directly from the wx target directory. The wx target
copies the wxWidgets runtime DLLs beside `dottalk_wb_next.exe` on Windows:

```powershell
build\src\gui\wx\Release\dottalk_wb_next.exe
```

Launch with an initial table:

```powershell
build\src\gui\wx\Release\dottalk_wb_next.exe dottalkpp\data\dbf\x64\ENROLL.DBF
```

If a local build tree was produced before this copy step existed, rebuild the
`dottalk_wb_next` target once. As a temporary fallback, put the vcpkg triplet `bin`
directory on `PATH` before launching.

The Workbench skeleton currently keeps multiple opened DBFs as GUI work areas. Use the
left Areas panel to switch between open tables, and use Close Area to close the
selected area without closing the others.

For the canonical Workbench build lane, prefer the wrapper so the CLI and wx runtime DLL
paths are established consistently:

```powershell
.\wb.run.ps1 --locale it dottalkpp\data\dbf\x64\ENROLL.DBF
```

The Workbench mirrors the Python lane: runtime-backed Workspace load/save/save-as,
Path Roots inspection, SET DBF / SET INDEX skeleton entries, and a Run >
SCAN...ENDSCAN... dialog that displays CLI scan output in a separate results
window.

The wx Workspace menu also exposes `WORKSPACE OPEN Directory...` and
`WORKSPACE LOAD Schema...` for the canonical runtime commands.

At startup the GUI session searches for `init.ini`, `dottalkpp.ini`, and
`dotscript.ini`. At shutdown it searches for `shutdown.ini`. Matching scripts
are sent through the same DotTalk++ CLI bridge used by the command window.

Lifecycle script precedence is profile-aware:

1. `DOTTALKPP_GUI_BIN` when set, for app-specific or user-specific GUI startup.
2. DotTalk++ data/root locations used by the active runtime path setup.
3. The repository/application root as a fallback.

That means a custom user start can own its banner, quote, theme, workspace, and
startup commands without changing the generic DotTalk++ bin startup files.
