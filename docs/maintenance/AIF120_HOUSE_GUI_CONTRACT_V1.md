---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-063
  recorded_at_utc: 2026-08-20T01:00:00Z
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
    baseline_commit: a20319abc
  authorization:
    requested_by: maintainer (member.derald), in-session -- "that is the house rule,
      always look for prior art" and "always report if a house rule or gate unjustly
      blocks progress".
  report:
    path: docs/maintenance/AIF120_HOUSE_GUI_CONTRACT_V1.md
    kind: ruling
---

# AIF-120 -- R55: the house already had a GUI threading contract, and this lane wrote its own

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

## 0. Correction 37 -- the fourth prior-art miss, and the largest

Searching for font handling under the house rule turned up no fonts and something
worse:

| file | what it is |
|---|---|
| `docs/ui/GUI_THREADING_RAII_CONTRACT_V1.md` | the house GUI threading and RAII contract |
| `include/gui/core/async_session.hpp` | *"GUI worker dispatch and lifetime boundary"* |
| `include/gui/core/gui_runtime_adapter.hpp` | *"adapters are translation seams only"* |
| `src/gui/core/gui_cli_bridge.cpp` | an existing CLI bridge |
| `docs/ui/CORE_UI_PRINCIPLES_V1.md`, `UI_LANE_TRADEOFFS_V1.md` | more of the same |

This lane's charter is *give the existing GUI a language*. It then built a dispatch
runtime (R37), a second one in C++ (R41), scopes as lifetime boundaries (R21.4,
R39-R46) and a CLI bridge for locks (R47-R49) across nineteen rulings, **without ever
opening the directory named `docs/ui/`.**

`async_session.hpp`'s contract block, which I had not read, says:

> *"AsyncSession owns the worker thread through RAII; destruction must stop the queue
> and join the worker."*
> *"queued GUI work may orchestrate shared services or CLI bridges, but must not
> invent a frontend-only DBF/index/relation behavior layer."*

That is R37 and R21.4, specified before I started.

## 1. What the derivation got right, which is worth recording

The lane derived its threading rules from VFP's behaviour and the corpus. Independent
of the house document, it landed on the same answers:

| house contract | this lane |
|---|---|
| widgets only on the GUI main thread | R11.3, asserted in the pump rather than assumed |
| worker output returns through a queue and `after()` polling | `uidef_runtime.pump()` + `root.after(30, _pump)` |
| wx: background work posts copied/shared immutable payloads | `wxWindow::CallAfter` with by-value captures (R41) |
| queued work cancelled or drained in a predictable shutdown path | scopes (R21.4), and R45's pump cancellation |
| tolerate completion order through task ids | completions keyed by name, delivered at most once (R21.4) |

Two independent derivations agreeing is genuine evidence about the rules. It is not
an excuse for the duplication.

## 2. R55.1 -- the violation that was not arguable, now fixed

> *"No detached worker thread that can outlive its session or event sink."*
> *"Worker threads joined or stopped from destructors."*

Both runtimes did exactly the named anti-pattern:

```python
threading.Thread(target=body, daemon=True).start()    # never joined
```
```cpp
std::thread([...]{ ... }).detach();                   // explicitly detached
```

A daemon thread dies wherever it stands when the interpreter exits -- possibly
mid-write. A detached `std::thread` can outlive the `Runtime` whose members its
lambda captured.

Now: Python tracks its workers and `Runtime.shutdown(timeout)` joins them, returning
any still alive (empty in test). C++ owns them in a `std::vector<std::thread>` and
`~Runtime()` calls `join_workers()`. Cancellation remains a scope concern -- this
waits, it does not abandon.

Regressions after the change: R44, R45, R46 and R49 on wx, and the two Python suites,
all reproduce their recorded results.

## 3. R55.2 -- reported, not resolved: one mutation lane vs measured domain concurrency

Invoking the maintainer's second rule -- *"always report if a house rule or gate
unjustly blocks progress"* -- because silent compliance here would discard a measured
result.

The house contract:

> **"One workspace/session has one mutation lane."** Commands affecting selection,
> current record, order, filters, relations, variables, loops, **locks**, dirty or
> session state must be serialized through the workspace executor.

R26 measured something finer. Locking the work area a handler *names* corrupts 60 of
60 trials; locking the **relation-set domain** corrupts 0 of 60 -- and leaves handlers
on *unrelated* domains free to overlap, which R38 and R41 then demonstrated on two
toolkits.

Both are safe. The house rule is safe by serializing everything; R26 is safe by
serializing exactly what a relation can reach. **The house rule is stricter and
costs the concurrency R26 established.**

I am not ruling on this. Three honest options:

1. **Adopt the house rule.** One lane per document, R26 becomes an explanation of
   *why* the lane exists rather than a licence to overlap. Simplest; discards
   measured parallelism.
2. **Keep domain concurrency and amend the house contract**, on R26's evidence, to
   permit concurrent mutation across provably disjoint lock domains.
3. **Domain concurrency inside a UIDEF document, one lane at the workspace boundary.**
   Plausible, and the least examined -- it needs someone to say what a "workspace"
   is relative to a UIDEF document, which nothing currently does.

**Owner ruling wanted.** Whichever way it goes, one of two documents is currently
wrong about how a frontend may mutate.

## 4. R55.3 -- the console bridge has a sunset clause, and it has expired for wx

> *"parsing console text as the only contract for new native GUI features"* -- listed
> as an anti-pattern, with a carve-out: *"Console parsing is acceptable as a
> compatibility bridge while the shared runtime API is being extracted. It should be
> replaced by typed runtime APIs where the core already exposes stable state."*

R47.2's lock provider emits console text. For Tk and Python that is the only option.
For the **wx C++ backend it is not**: `include/xbase_locks.hpp` is a stable typed API
with owner-aware overloads, `is_record_locked(area, recno, owner_out)`,
`force_unlock_table` and `release_held` -- strictly richer than the `LOCK`/`UNLOCK`
student commands, which is what the maintainer meant by *"a simple student example"*.

So R49.1 -- *"the verbs live in the runtime on both targets"* -- is right for the text
path and is the **wrong target** for C++, which should link the API rather than speak
to it. That is a real change to what a generated frontend depends on, so it is
recorded here and not made.

## 5. The contract's acceptance checks, against what this lane has actually proven

| acceptance check | status |
|---|---|
| the app remains responsive during a command | **not tested** |
| closing the app joins/stops workers cleanly | **now** (R55.1) |
| no widget is touched from a worker thread | proven (R38, R41 -- asserted, not assumed) |
| queued work does not outlive the session | **now** (R55.1) |
| active area and record cursor remain stable after command completion | **not tested** |
| relation/index/workspace state still reflects DotTalk++ runtime output | **not tested** -- and R55.2 is exactly this question |
| tests or smoke runs cover the changed lane | yes, throughout |

Three of seven have never been run. They are a better next test list than anything
this lane would have invented, which is the argument for the house rule in one line.

## 6. Still open

- **R55.2 and R55.3 are owner decisions**, and R55.2 means one of two documents is
  wrong today.
- **`AsyncSession` is still not used.** This ruling reconciles the lane's runtime with
  the contract; it does not adopt the house implementation. Whether `uidef_rt.h`
  should *be* `AsyncSession` is a larger question than a threading fix.
- **The FONT gap is untouched.** Measured under R54: 3180 corpus objects carry a
  `PROPERTIES` memo, 1688 declare `FontName`, 561 declare `FontBold` (158 `.T.`) and
  3 declare `FontItalic` (all `.T.`) -- **161 objects state an emphasis UIDEF
  discards.** There is no font code anywhere in `include/` or `src/`, so unlike
  everything else in this ruling there is no prior art to reuse.
- **R53.4 still has no implementation.**

## 7. Good Neighbor note

- **What changed.** `gui/uidef/uidef_runtime.py`: workers tracked, `shutdown()`
  joins them. `gui/uidef/uidef_rt.h`: workers owned in a vector, `join_workers()`,
  `~Runtime()` joins.
- **Whose area.** AIF-120's own runtime. `docs/ui/`, `include/gui/`, `src/gui/` and
  `include/xbase_locks.hpp` were **read, not touched**. R55.2 and R55.3 are reports.
- **What authorization.** Maintainer (member.derald), in-session: *"always look for
  prior art"* and *"always report if a house rule or gate unjustly blocks progress"*.
- **How to verify or undo.** Verify: `python3 gui/uidef/lock_semantics_test.py` and
  `lock_provider_test.py`; on wx rebuild the R44/R45/R46/R49 harnesses -- all must
  reproduce. Undo: restoring `daemon=True` and `.detach()` restores the anti-pattern
  named in the house contract.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_runtime.py
git add gui/uidef/uidef_rt.h
git add docs/maintenance/AIF120_HOUSE_GUI_CONTRACT_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R55 -- the house had a GUI threading contract; detached workers fixed, and two conflicts reported rather than resolved"
```
