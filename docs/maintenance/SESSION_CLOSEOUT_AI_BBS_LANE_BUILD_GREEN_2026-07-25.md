---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260725-001
  recorded_at_utc: 2026-07-25T14:05:00Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: dfa8c1366afd171d7f7d4101c6561c0ba5e27990
    head_commit: dfa8c1366afd171d7f7d4101c6561c0ba5e27990
  authorization:
    requested_by: maintainer
    scope: >
      Wire the AI-BBS / pseudo-chat agent-server lane (M1-M5) into dottalkpp, build in dev, and run
      the PDLC test gates. Records the build-green + runtime-observed milestone.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    kind: session_closeout
---

# Session Closeout -- AI-BBS Lane: Built + Test Gates Green (2026-07-25)

Owning lifecycle: DotTalk++ SDLC (`project.ai_friendly`).
Operating mode: `development` (wired directly into ccode at maintainer direction; uncommitted at time of writing).
Change class: additive -- new tables/commands/permissions + one dependency (libsodium); no existing control weakened.
Truth state: **build-verified (MSVC Release) + runtime-observed** at each gate (see Evidence).
Promotion state: committed to dev pending (working tree dirty). Mirror `C:\x64base` untouched. Not pushed to public.

## Origin

Five review-needed packages (M1-M5, `x64base-ai-bbs-*_20260724`) authored the lane. Maintainer
directed wiring them into `dottalkpp` and building/testing rather than leaving them staged. This
closeout records the went-green pass.

## Outcome -- the lane runs

- **Build:** `dottalkpp.exe` (MSVC Release) compiled with the lane in it. libsodium resolved via vcpkg
  (`unofficial-sodium::sodium`); `ws2_32` linked for the listener. One authored bug fixed at build:
  `xbase::fields::findFieldCI` -> `fields::findFieldCI` (correct namespace). One CMake ordering bug
  fixed: sodium/ws2_32 linked at top level where `find_package(unofficial-sodium)` is in scope.
- **Seed:** re-seeded (old identity DBFs backed up to `data/metadata/identity/_pre_bbs_backup_20260725/`).
  `USER PERMS` = 18 (incl. `host.network.egress`, `bbs.read`, `bbs.post`, `chat.invoke`);
  `USER LIST` includes `member.ai.grok.xai`.

## Evidence (runtime-observed, 2026-07-25)

| Gate | Observation |
|---|---|
| M3 crypto | `USER TOKEN member.ai.grok.xai` -> 43-char base64url (CSPRNG). Login with correct token = "logged in"; wrong token = "authentication failed". Argon2id via libsodium. |
| M1 board | `BBS BOARDS` created `data/metadata/bbs/{SYSBOARD,SYSTHREAD,SYSPOST}.dbf` + 3 boards. `BBS POST`/`READ` round-trip. `board.governance` rendered the `SYSGRANT` request/approve loop as posts (`[grant GRANTED]`, `[grant REQUESTED] scope=source.mutate`). |
| M2 egress | As `member.ai.grok.xai`: `NET EGRESS OPEN` -> **refused** ("not eligible: no in-scope role permission"). As owner: `NET EGRESS STATUS` -> `Block`. |
| M4 server | `BBS SERVE` -> `netstat` shows `127.0.0.1:8765` LISTENING (loopback only). `AUTH member.ai.grok.xai <token>` -> `OK`. `CHAT` -> haiku from local Ollama (v0.9.5, WSL, isolated) **while egress = Block** (loopback exempt). `BBS POST <board> <subj> :: <body>` -> `OK posted #2` (identity-bound author). |
| M6 daemon | `dottalk_bbsd.exe` linked clean after adding `src/cdx/*` (the `xindex.lib` gap); ran headless via the `DotTalkBBSD` logon scheduled task (pid distinct from any manual instance); fresh PowerShell client sessions completed AUTH/CHAT/POST across process restarts; `netstat` confirmed `127.0.0.1:8765` only. Cross-platform: SIGPIPE ignored on POSIX + `MSG_NOSIGNAL` on Linux sends. See `AI_BBS_M6_STANDALONE_DAEMON_V1.md`. |
| Lounge | `board.lounge` ("The Lounge", `bbs.post`) added to `kDefaultBoards` with an idempotent top-up in `ensure_bbs_tables()`; materializes on next `BBS BOARDS` without a re-seed. See `docs/ai-friendly/AI_BBS_LOUNGE_ROOM_V1.md`. |
| Guest | `member.guest` (External, `role.guest` = `bbs.guest` only) + `board.guestbook` (`POSTPERM=bbs.guest`). As guest: `POST board.guestbook` -> `OK posted #5`; `POST board.lounge` -> `bbs.post denied`; `READ` -> `bbs.read denied` (write-only). Server enforces per-board POSTPERM; BBS writes take table FLOCK; listener uses `SO_EXCLUSIVEADDRUSE`. Daemon runs as `DotTalkBBSD` SYSTEM/session-0 task (no console window possible). |

Proof records + transcripts: to be promoted into `proofs.yaml` (`runtime_observed`) and `ai_runs.yaml`
(RUN `AIPR-20260725-001`), per `x64base-ai-bbs-M5_20260724/REGISTRY_ADDITIONS.md`.

## Files (wired into dev, uncommitted)

- New TUs: `include|src/bbs/*`, `include|src/security/token_crypto.*`, `include|src/selfdoc/event_record.*`, `src/cli/cmd_bbs.cpp`, `src/cli/cmd_net.cpp`.
- Edits: `identity_bootstrap.cpp` (perms + `member.ai.grok.xai` + Argon2id delegation), `identity_schema.hpp` (CRED->128), `identity_admin.cpp` (crypto delegation), `shell_commands.{hpp,cpp}` (register BBS/NET), CMake (`find_package(unofficial-sodium)` + link), `src/CMakeLists.txt`, `vcpkg.json` (+libsodium).
- **M6 daemon:** `src/tools/bbsd_main.cpp` (new), `bbs_server.cpp` decoupled from `cli::cmdout` + SIGPIPE/`MSG_NOSIGNAL` guards, `CMakeLists.txt` `dottalk_bbsd` target (globs `src/cdx/*` for the `xindex.lib` gap). Launchers in `D:\code`: `register-bbsd-startup.ps1`, `bbsd-startup.ps1` (ASCII-clean; scheduled task `DotTalkBBSD`).
- **Lounge:** `src/bbs/bbs_store.cpp` -- `kDefaultBoards` + top-up in `ensure_bbs_tables()`; `board.lounge` added. Docs: `docs/ai-friendly/AI_BBS_LOUNGE_ROOM_V1.md`, `docs/ai-friendly/AI_BBS_LANE_V1.md`, `docs/maintenance/AI_BBS_M6_STANDALONE_DAEMON_V1.md`.

## Next

1. Commit the lane to dev with an accurate message; promote runtime transcripts into `labtalk/proofs/runs/` + `proofs.yaml`; append the `ai_runs.yaml` RUN row.
2. Flip `BBS` / `NET` `@dottalk.usage` `status: experimental` -> `supported` (gates now green) so metacollect auto-publishes them into the command reference.
3. ~~Extract a standalone `dottalk_bbsd`~~ **DONE (M6)** -- built, boot-managed, runtime-observed; see `AI_BBS_M6_STANDALONE_DAEMON_V1.md`. Remaining sub-item: core-lib refactor so the daemon links without hand-picking `src/cdx` (the `xindex.lib` gap).
4. Registry additions authored in `REGISTRY_ADDITIONS_AI_BBS_2026-07-25.md` (proofs.yaml -> `runtime_observed`; `ai_runs.yaml` RUN `AIPR-20260725-001`; intake AIF-052/053/054). Merge after the source-mutation preflight.

## Known / deferred
- Windows-vs-WSL Ollama port contention recurred at boot (Windows Ollama autostart crept back, stealing 127.0.0.1:11434); resolved by killing it so the WSL service binds. Harden the afb-startup task or disable Windows Ollama startup permanently.
- BBS SERVE is serialized (single connection); concurrency needs a per-session refactor (pairs with M6).
