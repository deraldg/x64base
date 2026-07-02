# DotTalk++ Python GUI Frontend

This folder contains the first Python desktop GUI lane for DotTalk++.
It started as a visible preview harness, but it is now treated as a valid
first-class frontend path alongside the compiled C++ wxWidgets frontend.

Frontend lanes:

- `dottalk_gui_core`: GUI-neutral C++ runtime/session/event layer.
- `dottalk_wx`: compiled wxWidgets desktop frontend.
- `tools/gui_preview/dottalk_gui_preview.py`: Python/Tkinter desktop frontend.

Backend order:

1. Use `pydottalk` if it is importable from `PYDOTTALK_BIN` or known build dirs.
2. Fall back to a pure-Python read-only DBF preview reader.

Run:

```powershell
python tools/gui_preview/dottalk_gui_preview.py
```

The app opens a desktop window, reads sample records on a worker thread, and
displays a grid/log/status layout matching the wx skeleton.

Threading policy mirrors the C++ GUI core:

- tasks emit queued/running/completed/failed progress,
- runtime work runs on a worker thread,
- Tkinter widgets are updated only by the UI thread draining queued events.

Headless backend smoke:

```powershell
python tools/gui_preview/test_gui_backend.py
```
