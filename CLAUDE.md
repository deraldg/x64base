# DotTalk++ (ccode) -- working notes for Claude

Conventions and locations to remember when working in this repo. Keep terse; correct in place.

## Running the CLI over the work directory

Use **`./datarun.ps1`** from `D:\code\ccode`. Do NOT run the raw build exe by hand.

`datarun.ps1` (via `launch-common.ps1`) stages the **newest** built `dottalkpp.exe` into the
runtime bin and runs it over the work data:

- Runtime exe: `dottalkpp\bin\dottalkpp.exe`  (staged copy; `*.exe` is gitignored)
- Runtime data root (cwd when it runs): `dottalkpp\data`
- It also stages the full runtime DLL set beside the exe.

Interactive:  `./datarun.ps1`
Batch:        `./datarun.ps1 -CommandLines 'USER LIST','BBS BOARDS','USER SAVE'`
              (each string is one CLI line; written to a temp `.dts` and run with `--script`)

If it cannot copy the fresh build into the runtime bin (a process holds it), it now warns LOUDLY
and quantifies staleness instead of silently running the old copy.

## Build outputs (MSVC Release, default `pro-md` preset)

- `dottalkpp.exe`   -> `build\src\Release\dottalkpp.exe`   (datarun finds newest across presets)
- `dottalk_bbsd.exe` -> `build\Release\dottalk_bbsd.exe`   (standalone BBS daemon, M6)

Build both:  `cmake --build build --target dottalkpp dottalk_bbsd --config Release`
WSL builds also exist (`build-wsl`, etc.); `.exe` cross-platform via guarded code.

## BBS agent-server daemon (dottalk_bbsd)

- Runs headless via the **`DotTalkBBSD`** logon scheduled task; binds `127.0.0.1:8765` (loopback only).
- Shares the SAME data root as the CLI: `dottalkpp\data` (launched with `--data D:\code\ccode\dottalkpp\data`).
- Log: `D:\code\_bbsd_logs\bbsd.log`. Register/start scripts in `D:\code\` (`register-bbsd-startup.ps1`).
- **Rebuilding the daemon requires stopping the task first** (`Stop-ScheduledTask -TaskName 'DotTalkBBSD'`);
  a running instance locks `dottalk_bbsd.exe` (LNK1104 on build otherwise).
- Companion: `AFB-Ollama-Startup` task brings up the isolated WSL Ollama on `127.0.0.1:11434` (version
  `0.9.5` = WSL/isolated; `0.32.3` = Windows/non-isolated -- CHAT must hit the WSL one).

## Shared store + locking

- `dottalkpp` and `dottalk_bbsd` share the on-disk DBF store; there are NO pipes/IPC between them.
  In-memory identity/catalog is per-process, loaded from DBF at startup -- changes need a restart to be seen.
- The engine HAS cross-process cooperative locking (`xbase::locks`, RLOCK/FLOCK/UNLOCK via `.lock`
  sidecars, pid-stamped, stale-owner recovery). The BBS store write paths take a table FLOCK per append.

## Conventions

- DotTalk++ inline comment marker is `&&` (not `#`). Applies to single-token CLI lines; free-text
  commands (BBS POST/CHAT read to EOL) must be comment-free.
- Owner/maintainer: `member.derald`. Author docs as review-needed until committed; mirror `C:\x64base`
  and public repo are separate promotion steps.
- No em-dashes in scripts or docs (maintainer preference); use `--` / `->`.
