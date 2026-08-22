---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-107
  recorded_at_utc: 2026-08-22T16:05:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 26e85f73c
  authorization:
    requested_by: steward (member.derald), in-session 2026-08-22 -- "a refresh
      can be issued in shell_commands.cpp after the command, also cursor
      control", corrected one message later to "excuse me, I meant the shell".
      Two follow-up rulings given on the priced options -- honour the existing
      suppression list, and leave cursor_hook in place rather than deleting it
      or wiring it.
  report:
    path: docs/maintenance/AIF120_RELATION_REFRESH_DEAD_HOOK_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R117: SET RELATION children never tracked the parent, because the hook that was supposed to move them is never called

Status: **ruling, review-needed. FIXED (2 files). REBUILD REQUIRED.**
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260818-001`.
Date: 2026-08-22. Baseline `26e85f73c`.

**Area:** engine (`src/cli/`). Changed under the steward's explicit go.

**R-number note.** The build-stamp finding (resume state sec 3) was also
carrying an R117 claim and has never been written up. This document lands, so
it takes the number; the build-stamp finding needs a new one.

---

## 1. How this surfaced, and what I got wrong first

`REGRESSION USE_AGAIN` has one red arm, `UA_T12b`
(`selfjoin_child_tracks_parent_movement`). It has been red since the arm was
written on 2026-08-12. I twice recorded it as **a semantic question owed to the
steward** -- the house record in CASCADE_ENV says *"slaving is REFRESH-driven,
not implicit per movement"*, while the xBase contract says SET RELATION is
implicit, and I filed the red as the tension between those two.

**That framing was wrong, and it sent the steward toward a decision that was
not his to make.** The house had already chosen implicit. It wrote the
mechanism, installed the callback, and deleted the fallback on the strength of
it. Nothing was ever connected to the trigger.

**The correction came from reading the dispatch rather than the doctrine.**

## 2. Measured

**(a) The cursor movers carry no refresh, deliberately.**
`shell_commands.cpp` registers `GO`, `TOP`, `BOTTOM`, `GOTO`, `SKIP`, `FIND`,
`SEEK`, `LOCATE`, `CONTINUE` bare, while ~19 other commands call
`relations_api::refresh_if_enabled()` in their registration. Its comment said
why, in its own words:

> With engine cursor hook active, avoid manual refresh on cursor-moving
> commands. Keep manual refresh for: open/close/select, relation-definition
> changes, and data mutations.

**(b) The hook is real, installed, and correct.** `shell.cpp` installs
`on_cursor_changed` as the `cursor_hook` callback. That function checks the
moved area is the current area, honours the suppression counter, and calls
`relations_api::refresh_if_enabled()` -- precisely the work `UA_T12b` needs.

**(c) `xbase::cursor_hook::notify()` has NO CALL SITES.** Defined once in
`src/xbase/cursor_hook.cpp`, declared once in `cursor_hook.hpp`, and invoked
nowhere. Verified by sweeping every subtree of `src/` except `AIPortal/`
(session archives, not built) plus `include/`: the only files that name
`cursor_hook` at all are the two that define it, `shell.cpp` (installs the
callback), **four** files holding **12** `cursor_hook::Guard suppress_cursor`
sites that suppress it (`cmd_list` 5, `cmd_seek` 3, `list_messaging` 2,
`smartlist_query` 2), `cmd_smartlist.cpp` -- which includes the header and
never uses it -- and `dbarea.cpp`, **which mentions it only to say it does not
fire**: `// - No cursor_hook notifications here.`

So: mechanism built, callback installed, suppression guards written throughout,
the manual fallback removed *because the mechanism existed* -- and the trigger
never wired. `GO 2` moves the parent and nothing tells anyone.

**(d) The suppression half of the policy already lives in the shell.**
`shell_execute_line()` (`shell_api.cpp`) -- which its own comment calls *"the
single canonical executor every front-end routes through (interactive REPL,
DO/DOTSCRIPT, init/shutdown scripts, loop bodies)"* -- already wraps
`registry().run(...)` in `RelRefreshGuard guard(shell_is_rel_refresh_suppression_command(U))`.
There is a guard in the shell whose entire job is to suppress a refresh that
never happens.

## 3. What changed

**One call, in the canonical executor.** `src/cli/shell_api.cpp`, immediately
after the guard scope closes and inside the `SET TIMER` window so the cost is
reported honestly:

    if (!shell_is_rel_refresh_suppression_command(U))
        relations_api::refresh_if_enabled();

This covers every command that moves the cursor, present and future, on every
front-end, with no per-command opinion in the registry. It was chosen over
nine per-command wrappers on the steward's instruction ("I meant the shell").

**The suppression list is honoured, on the steward's ruling.**
`refresh_from_parent_name` matches **by scan, not index seek**
(`set_relations.cpp:346`), so an unconditional refresh would put a full child
scan on the back of `COUNT` / `LIST` / `SUM` over a large table -- the exact
cost that list was built to avoid. Reusing the same predicate as
`RelRefreshGuard` means the suppress-during and skip-after halves cannot drift
apart.

**Six comment blocks in `shell_commands.cpp` repointed.** They instructed
future authors to *"rely on engine cursor hook (no manual refresh here)"*.
Left as-is they would have been actively wrong the moment this landed --
the same failure mode as a stale `@dottalk.usage` block, one layer down: **the
comment is the contract.** The block on `AREA`/`RECNO` is corrected on a point
of fact as well: it hedged *"if RECNO sets position"*, and `cmd_recno.cpp:122`
does call `gotoRec64`.

## 4. Reported, NOT fixed

- **`cursor_hook` is now provably dead code** -- `notify()`, the callback, the
  installer, and the 12 `Guard suppress_cursor` sites. **Left in place on the
  steward's ruling**, so this commit is one added call and nothing else, and a
  bisect can separate the behaviour fix from any deletion. Removing it, or
  wiring `notify()` at the `DbArea` cursor movers so the GUI and tuple
  front-ends get it too, is a separate ruling.
- **18 explicit refresh calls in `shell_commands.cpp` are now redundant.**
  Every explicit-call command except `DELETE` is *not* on the suppression list,
  so the shell already refreshed after it -- those sites now refresh twice.
  Retained deliberately (same reason as above). **`DELETE` is the only one that
  must survive any cleanup**: it IS on the suppression list, so the shell skips
  it and its own call is the only refresh it gets. Measured, not assumed.
- **This is an AIF-079 instance, not a fresh class.** IDXSTALE's own
  description records `wasStale()` having *"seven overrides and ZERO call
  sites (AIF-079 instance 1)"*. A fully-built mechanism that nothing invokes
  is a shape this house has already numbered once. **A census of the others is
  owed** -- this is the second instance found by accident rather than by
  looking.

## 5. Good Neighbor note

**What changed.** `src/cli/shell_api.cpp` gains one conditional call to
`relations_api::refresh_if_enabled()` plus the `set_relations.hpp` include.
`src/cli/shell_commands.cpp` gains no code changes at all -- six comment blocks
only. No command registration was touched; no engine file was touched.

**Whose area.** `src/cli/**` is engine, not this lane's own code.

**What authorization.** The steward's in-session instruction to put the refresh
in the shell, plus his rulings on the two priced options.

**How to verify.** Rebuild, then:

    REGRESSION USE_AGAIN

`UA_T12b` is the arm under test and should go **from red to green**; every
other arm must stay green. Then `REGRESSION ALL` plus the explicit-run specs --
nothing else should move.

**One caveat on that verification, stated rather than implied.** `UA_T12b`
asserts the CHILD landed on Bob; it does not assert the PARENT moved. `GO 2`
prints nothing and the only status line for area 9 is emitted by the `SELECT 9`
that precedes it, so a green here is consistent with -- though it does not
prove -- the parent having moved. This exact trap already fired once in this
arm; the script's own correction note records that an earlier `GO 3` was a
no-op and that `UA_T12` measured less than its name claimed. A one-line
assertion of the parent's identity between `GO 2` and `SELECT BOSS` would close
it, and that is not weakening the marker.

**How to undo.** Revert the two files. The change is additive: removing the
conditional call restores the previous behaviour exactly, and no other site
depends on it.
