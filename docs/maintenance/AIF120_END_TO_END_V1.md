---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-066
  recorded_at_utc: 2026-08-20T03:45:00Z
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
    baseline_commit: 8de8b0737
  authorization:
    requested_by: maintainer (member.derald), in-session -- "keep dogfooding the
      engine, it is part of our proof that working top down and bottom up and also
      development of co-systems project and its documentation".
  report:
    path: docs/maintenance/AIF120_END_TO_END_V1.md
    kind: ruling
---

# AIF-120 -- R58: a generated frontend drives the real engine, and the chain is closed

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R57 section 6 opened with: *"The typed provider has never been linked into a
generated frontend."* It has now.

## 1. The whole chain, in one process

```
UIDEF table  ->  uidef_wx.py --dispatch  ->  generated wx C++
             ->  uidef::Runtime            (R37/R41 dispatch, R47 refusal)
             ->  uidef::xbase_lock_provider (R57.1, typed)
             ->  xbase::locks + xbase::DbArea   (the engine)
```

```
open students        : ok
provider             : typed (xbase::locks), table granularity
   handler saw recCount64=200, table locked=yes (vm:18217:1787174311351)
   completion: completed result=200
after the handler    : table locked = no -- released ()

  end to end: generated wx -> runtime -> typed provider -> engine : OK
```

Every stage is real. The document is a UIDEF table; the C++ is generated from it and
not hand-written; the runtime is the one R37 and R41 built; the lock is taken by
`xbase::locks` and **held by the engine while the handler runs** -- the handler asks
and is told the owner. `recCount64() = 200` is the real record count of the real
`STUDENTS.dbf`, matching what the CLI reported in R50.

**This is the first time the lane's chain has touched the engine.** Every prior proof
stopped at a recording sink, a model, or the CLI's text surface.

## 2. R58.1 -- R53.4 implemented, not merely ruled

R53.4 said a conforming frontend opens every `SOURCE` alias into its own work area
before firing any handler, and R57 listed it as having no implementation. The
registry does exactly that, and the shape enforces it: the provider is installed
against a **resolver**, and a resolver can only answer for areas that are already
open. An unopened alias returns `nullptr`, which the provider reports as

> *"alias is not open -- R53.4 requires the frontend to open every SOURCE alias
> before firing a handler"*

and refuses the acquisition. The rule is now a code path rather than a sentence.

## 3. R58.2 -- the generator was emitting a warning into every frontend

Building with `-Wall -Wextra` produced:

```
warning: capture of variable 'g_scope' with non-automatic storage duration
   w_B1->Bind(wxEVT_BUTTON, [g_scope](wxCommandEvent&){ ... });
```

`g_scope` is a global. Capturing a global by value is redundant, and gcc says so --
**an error under `-Werror`**, which any serious build uses. R44 introduced this by
having `scope_for()` return the literal `g_scope` for form-level scopes and then
splicing whatever it returned into the capture list.

Container scopes are locals and must still be captured; only the global must not.
The generator now emits `[]` for the form scope and `[sc_P1]` for a panel's, and the
generated file is **warning-clean under `-Wall -Wextra`**.

Worth noting how it surfaced: fourteen wx builds across R40 through R57 never showed
it, because none of them passed `-Wall`. **A warning nobody enables is a warning
nobody has.**

Regressions after the change: R44's scope test and R45's nested teardown reproduce.

## 4. What this proves for the co-system argument

The maintainer's framing (R57.5b) is that dogfooding is evidence for building
top-down and bottom-up together. R58 is the other half of R57's evidence, and the
two say different things:

- **R57** found a defect that neither layer could see alone -- the engine unlocking
  a lock its caller held.
- **R58** found that when both layers are honest, they compose without a shim. The
  provider is 60 lines. There is no translation layer, no adapter, no emulation of
  engine behaviour in the frontend. The document names an alias, the engine opens it,
  the runtime locks the domain, the handler reads.

The second is the weaker-looking result and the more important one. A top-down design
that has to *simulate* the system beneath it has not met it -- which is precisely
what R47 corrected, when the lane's runtime was locking with `threading.RLock`
beside an engine that had locks.

## 5. Still open

- **One area, not a domain.** `SOURCE` here declares a single alias. The all-or-
  nothing acquisition across a relation set, and its rollback, are proven against the
  CLI (R52) and against a recording sink (R49) but not yet against the engine through
  a generated frontend.
- **No write, and no contention.** The handler reads. The interesting cases -- two
  frontends contending, and a handler writing under the lock it holds -- are exactly
  R57.2's territory and are not exercised here.
- **The Tk backend has no equivalent.** It cannot link the engine, so its provider
  must stay the CLI text path (R55.3). Nothing has run a Tk frontend against a live
  dottalkpp process.
- **`locked_by_other()` is still untested.** Named in R57.6 and still three untested
  lines.
- **R55.2 remains the owner's**, and is now the only thing blocking a settled answer
  on how a frontend may mutate.

## 6. Good Neighbor note

- **What changed.** `gui/uidef/uidef_wx.py`: form-level scopes are no longer
  captured (they are globals). New: `gui/uidef/wx_e2e_registry.cpp`, the end-to-end
  target, with its build line in the header comment.
- **Whose area.** AIF-120's own. The engine was **linked against and read, never
  modified**; the target opens a copy of a fixture table and writes nothing.
- **What authorization.** Maintainer (member.derald), in-session: "keep dogfooding
  the engine".
- **How to verify or undo.** Verify: the build line in
  `gui/uidef/wx_e2e_registry.cpp`; expect `recCount64=200`, `table locked=yes`
  during the handler and `no -- released` after. Undo: the generator change is one
  conditional; restoring it reintroduces the `-Wall` warning in every generated
  frontend that has a form-level button.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_wx.py
git add gui/uidef/wx_e2e_registry.cpp
git add docs/maintenance/AIF120_END_TO_END_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R58 -- a generated wx frontend drives the real engine end to end; R53.4 implemented and a -Wall warning removed from every generated file"
```
