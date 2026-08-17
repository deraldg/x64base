# Open items -- the rung below a lane

Small, real, deferred work. Too small for an AIF lane, an SDLC gate, or a PDLC
project; too real to lose. One line each.

**Why this file exists (2026-08-17).** The coordination ladder had a documented
lightest rung -- quips (`AI_SESSION_COORDINATION_PROTOCOL_V1.md`) -- but quips
live in a gitignored inbox and do not survive a fresh clone, so parking anything
there loses it. Above that, the next rung was a claimed AIF lane, which is heavy
for "check a DNS record some day". Between the two there was nothing, so small
items went into chat and evaporated.

**Why it nags rather than merely records.** AIF-006's own warning text carries
the measurement: an obligation with no gate held at **33 percent** compliance
while gated obligations held **83-94**. A register nobody surfaces is a register
that decays. `tools/coordination/check_open_items.py` runs in the pre-push gate
and prints any row whose NEXT LOOK date has passed. It never blocks -- these are
deferred by choice, and a gate that blocks on them would teach people to delete
rows instead of doing them.

## How to use it

- **Add** a row. Take the next id. Set NEXT LOOK to when you actually want to be
  reminded, not tomorrow. A date far out is a legitimate answer.
- **Snooze** by moving NEXT LOOK. That is not cheating; it is the point. But the
  RAISED date never changes, so an item you have snoozed six times shows it.
- **Close** by deleting the row and, if it produced anything durable, saying so
  in the commit message. No closed-items graveyard here -- git already has one.
- **Promote** to an AIF lane if it grows. Claim a number, cite this id, delete
  the row.

## WHERE it gets done

The column that stops this becoming a code-only list. An item whose work happens
at a registrar or a hosting panel can NEVER be closed by a commit, and a register
that assumes otherwise silently mis-files every infrastructure item it holds.

`repo` -- a change in this tree - `site` -- the x64base-site tree -
`registrar` / `host` / `dns` -- an external control panel -
`decision` -- needs a ruling before any work starts

## Items

| id | raised | next look | where | item |
| --- | --- | --- | --- | --- |
| OI-001 | 2026-08-17 | 2026-09-15 | dns | `derald.com` serves an unrelated third party over an invalid certificate. Registry checked 2026-08-17: NOT lapsed -- registered 2004, expires 2027-06-24, GoDaddy, `NS23/NS24.DOMAINCONTROL.COM`, all four client locks set, last changed 2026-07-08 (two days before `c244300da` retired it as a support host). Check the `@` and `www` A records, whether a hosting or forwarding product is still attached, and the certificate binding. Also sweep for other places that still point at the name. |
| OI-002 | 2026-08-17 | 2026-10-01 | repo | `src/bindings/` is dead code. Nothing `add_subdirectory`s it, and `src/CMakeLists.txt` excludes it twice with "hard safety: never compile src/bindings into dottalkpp". Its comment reads `# After add_library(pydottalk MODULE ...)` -- describing a target it does not create. Pre-dates the move to `bindings/pydottalk/`; last touched 2026-04-28. It is a SECOND `pydottalk` definition and it briefly misled this session into thinking it was the live one. Delete it, or leave a one-line note saying what it was. |
| OI-005 | 2026-08-17 | 2026-09-08 | decision | **Command-shell execution from Python: how, and against which binary.** The starter README lists it as an unproven milestone, and the superseded `src/bindings/pydottalk.cpp` (OI-002) already implements `Session::run(table, commands)` and `Session::export_csv(table, fields, for_clause, out_path)` -- two capabilities the current module does not have. Three routes, and the choice decides OI-002: (a) link the shell into the `.pyd`, which drags the ~400-TU CLI back in and defeats the lean build, and gives the module its own per-process identity/catalog state that nobody logged into; (b) subprocess `dottalkpp.exe --script`, which is what `datarun.ps1` already does, keeps the process boundary, inherits the CLI's real init and permission path, and uses the documented `SET ALTERNATE` capture rule; (c) a lean data-only CLI, which is a new target and a new command subset to maintain. Prior art favours (b): `dottalkpp` and `dottalk_bbsd` already share the STORE with no IPC between them, so a third process is the established pattern rather than a new one. |
| OI-006 | 2026-08-17 | 2026-09-22 | repo | **The ROOT build has no `CMAKE_POSITION_INDEPENDENT_CODE` and would fail on Linux.** Measured 2026-08-17: the property is set NOWHERE in this repository. On ELF, every object linked into a shared module must be position-independent, and `xbase`/`memo`/`xindex` are static libs built without it. The lean pydottalk build hit this and now sets it; the root build does not, so `cmake -DBUILD_PYDOTTALK=ON` on Linux/WSL fails at LINK with `relocation R_X86_64_TPOFF32 against xbase::trigger_hooks::(anonymous)::g_suppress_depth ... recompile with -fPIC`. Windows never surfaces it because a DLL carries no such constraint. NOT urgent -- nobody builds the root on Linux today -- but it is a landmine for the first person who tries, and the diagnostic names a thread-local three libraries deep rather than the missing property. One line in the root CMakeLists, or per-target on the three libs; decide which, since setting it globally also applies to the CLI executable. |
| OI-007 | 2026-08-17 | 2026-11-03 | repo | **Re-measure `DOTTALK_INDEX_MODE` once pydottalk exposes an index API.** Today the three modes ship a byte-identical module (665336 B, sha256 `54cb15eb...`, all three) because `module.cpp` references the index zero times, so the static `libxindex.a` resolves nothing and the linker discards it, `lmdb_backend.o` included. Confirmed against the AI portal on 2026-08-17: indexing has NEVER been tested with pydottalk -- the portal names it once, as a closeout filename; the four `launcher_pydottalk` proof runs are 356-389 B with zero index hits; the only registered pydottalk proof is APPEND BLANK, which is CRUD. The binding is CRUD-only by construction. THE TRIGGER for this row is the first `setOrder`/`seek`/tag binding added to `module.cpp`: at that moment `lean-none` should start FAILING to link, the modes stop being interchangeable, and on Windows the `.pyd` may acquire a runtime dependency on `lmdb.dll` (vcpkg builds lmdb as a DLL on x64-windows) that must then ship beside it. Settle the DLL half any time with `dumpbin /dependents pydottalk.cp312-win_amd64.pyd`. Evidence: `proof.build.index_mode_changes_nothing_shipped`. |
| OI-003 | 2026-08-17 | 2026-10-01 | repo | `build.ps1` has no way to build the module alone: line 164/170 hardcode `--target dottalkpp pydottalk`, so `-WithPyDotTalk` always builds the CLI too. The lean route now exists (`build_pydottalk.ps1` -> `bindings/pydottalk` standalone), so this is no longer blocking -- but anyone reaching for `build.ps1 -WithPyDotTalk` still gets the heavy build with no switch to say otherwise. Either add `-PyOnly`, or make the wrapper the documented entry point and say so in `build.ps1`. |
