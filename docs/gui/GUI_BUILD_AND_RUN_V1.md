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
can load/save first-pass `.dtschema` files; the bootstrap format persists open
areas as `table=<path>` entries. Use Workspace > Path Roots to inspect the GUI
root/data/script path decisions, and Workspace > SET DBF / SET INDEX to exercise
the reserved menu skeletons.

The two canonical runtime workspace actions are exposed directly:

- Workspace > WORKSPACE OPEN Directory... sends `workspace open <dir>` through
  the DotTalk++ command bridge. The dialog can append `CDX`, `CNX`, or `INX`
  index/key attachment, plus `FALLBACK`, `recursive`, and `TABLE`.
- Workspace > WORKSPACE LOAD Schema... sends `workspace load name.dtschemas`
  through the DotTalk++ command bridge for saved workspace graphs, including
  restored areas, relations, paths, and active tags when the file contains them.

The older bootstrap load/save menu remains separate as a GUI-core skeleton for
the current `table=<path>` prototype files.

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
$env:DOTTALKPP_GUI_CLI = "D:\code\ccode\build-wx-fixed-local\src\Release\dottalkpp.exe"
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

Configure with the existing LMDB package prefix:

```powershell
cmake -S D:\code\ccode -B D:\code\ccode\build-gui-lmdb-check -G "Visual Studio 17 2022" -A x64 -D CMAKE_PREFIX_PATH=D:\code\ccode\build-pro-md\vcpkg_installed\x64-windows -D DOTTALK_WITH_GUI=ON -D DOTTALK_WITH_WX=OFF -D DOTTALK_WITH_TV=OFF -D DOTTALK_WITH_INDEX=ON -D BUILD_TESTING=ON
```

Build and test:

```powershell
cmake --build D:\code\ccode\build-gui-lmdb-check --config Release --target dottalk_gui_core_async_smoke
ctest --test-dir D:\code\ccode\build-gui-lmdb-check -C Release -R dottalk_gui_core_async_smoke --output-on-failure
```

wx locale smoke:

```powershell
D:\code\ccode\build-wx-fixed-local\src\gui\wx\Release\dottalk_wx.exe --locale es
D:\code\ccode\build-wx-fixed-local\src\gui\wx\Release\dottalk_wx.exe --locale it
```

After launch, use the `Language` menu to switch among the seeded GUI locales
without restarting.

## C++ wxWidgets Frontend

`dottalk_wx` is opt-in:

```powershell
cmake -S D:\code\ccode -B D:\code\ccode\build-wx-check -G "Visual Studio 17 2022" -A x64 -D DOTTALK_WITH_GUI=ON -D DOTTALK_WITH_WX=ON -D DOTTALK_WITH_INDEX=ON
```

This currently requires wxWidgets to be installed for the selected toolchain.
`wxwidgets` is listed in the vcpkg manifests so future vcpkg manifest installs
can provide it.

After building, launch directly from the wx target directory. The wx target
copies the wxWidgets runtime DLLs beside `dottalk_wx.exe` on Windows:

```powershell
D:\code\ccode\build-wx-vcpkg-check\src\gui\wx\Release\dottalk_wx.exe
```

Launch with an initial table:

```powershell
D:\code\ccode\build-wx-vcpkg-check\src\gui\wx\Release\dottalk_wx.exe D:\code\ccode\build\src\Release\dbf\RM_BROWSE_V1.dbf
```

If a local build tree was produced before this copy step existed, rebuild the
`dottalk_wx` target once. As a temporary fallback, put the vcpkg triplet `bin`
directory on `PATH` before launching.

The wx skeleton currently keeps multiple opened DBFs as GUI work areas. Use the
left Areas panel to switch between open tables, and use Close Area to close the
selected area without closing the others.

For the local wx build lane, prefer the wrapper so the CLI and wx runtime DLL
paths are established consistently:

```powershell
D:\code\ccode\wx.run.ps1 --locale it D:\code\ccode\dottalkpp\data\dbf\x64\ENROLL.DBF
```

The wx Workbench mirrors the Python lane: Workspace load/save/save-as for
bootstrap `.dtschema` files, Path Roots inspection, SET DBF / SET INDEX
skeleton entries, and a Run > SCAN...ENDSCAN... dialog that displays CLI scan
output in a separate results window.

The wx Workspace menu also exposes `WORKSPACE OPEN Directory...` and
`WORKSPACE LOAD Schema...` for the canonical runtime commands.

At startup the GUI session searches for `init.ini` and `dottalkpp.ini`. At
shutdown it searches for `shutdown.ini`. Matching scripts are sent through the
same DotTalk++ CLI bridge used by the command window.
