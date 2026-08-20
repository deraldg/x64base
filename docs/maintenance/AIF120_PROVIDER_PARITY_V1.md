---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-057
  recorded_at_utc: 2026-08-19T20:30:00Z
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
    baseline_commit: d36fa002c
  authorization:
    requested_by: maintainer (member.derald), in-session "next" -- taking R48
      section 7's untested C++ seam.
  report:
    path: docs/maintenance/AIF120_PROVIDER_PARITY_V1.md
    kind: ruling
---

# AIF-120 -- R49: a rule the runtime cannot enforce on one target is a rule that target does not have

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R48 section 7: *"The C++ provider has no test. `uidef_rt.h` takes a `LockProvider`
callable and nothing exercises one; the seam is proven on the Python side only. The
C++ seam is seven lines and untested is untested."*

Testing it found something worse than an untested seam.

## 1. The two runtimes did not enforce the same rule

R48.2 ruled that **the runtime never renders a number into a command**, because a
recno written through a default-constructed `ostringstream` under a grouping locale
becomes `LOCK 16,984` and reads back as `16` (AIF-116).

In Python that holds by construction: `LockProvider` writes the commands.

In C++ it did not hold at all. The seam was

```cpp
using LockProvider = std::function<bool(bool acquire,
                                        const std::vector<std::string>& aliases)>;
```

-- a list of aliases handed to the target, which then said whatever it liked. A
target formatting `"LOCK " << recno` through an un-imbued stream reintroduces
AIF-116 in full, and the runtime that made the rule has no say.

**A rule the runtime cannot enforce on one of its two targets is a rule that target
does not have.** The asymmetry was invisible because the seam compiled, and because
nothing had ever passed a provider through it.

## 2. Ruling R49.1: the verbs live in the runtime, on both targets

`uidef::lock_provider(run, record_granularity)` builds the provider in `uidef_rt.h`.
A target supplies only `run(text) -> bool`:

```cpp
rt.set_lock_provider(uidef::lock_provider(
    [](const std::string& cmd){ return engine.execute(cmd); }));
```

Sorted on acquire, reversed on release, all-or-nothing with rollback -- the same
ordering as the Python provider, because it is the same ruling.

## 3. Runtime-proven, under AIF-116's own runtime condition

The harness sets a grouping locale **globally**, exactly as the engine picked one up,
and proves it is live before testing anything:

```
  grouping locale is active : an un-imbued stream writes 16,984
  table  acquire : SELECT enroll ; LOCK TABLE ; SELECT students ; LOCK TABLE
  table  release : SELECT students ; UNLOCK ; SELECT enroll ; UNLOCK
  record acquire : SELECT enroll ; LOCK ; SELECT students ; LOCK
  record release : SELECT students ; UNLOCK ; SELECT enroll ; UNLOCK
  rollback       : returned false, rolled back 1 lock(s)
                   (SELECT enroll ; LOCK TABLE ; SELECT students ; LOCK TABLE ; SELECT enroll ; UNLOCK)
  runtime-rendered numbers in any command : none
  engine refuses : handler ran=false  completion state=refused

  verbs and order (both granularities) : True
  all-or-nothing rollback              : True
  no runtime-rendered numbers          : True
  engine refusal refuses the handler   : True
```

Byte-identical to the Python provider's command text, from the same domain, on a
target with a different language and different threading primitives. The fourth case
is the one the C++ suite lacked: it reaches through the provider into dispatch and
shows a refused acquisition refusing the handler rather than running it anyway.

Regressions after the header change: R44's scope test, R45's nested test, R46's page
teardown and R47's lock semantics all reproduce their recorded results.

## 4. Correction 32: the harness produced nothing, and nothing looked like nothing

The first build hung with no output at all, through `xvfb-run`, with a 124 exit.

`uidef_after_init` is called from inside `OnInit`, **before the main loop exists**, so
`wxTheApp->ExitMainLoop()` there is a no-op: the app then starts its loop and runs
forever. Every `printf` was still sitting in a block-buffered stdout, which is
discarded when the process is killed. The harness had in fact done all its work
correctly and printed all of it.

This is the third harness-timing defect in this run, and the three form a set:

| | what the harness did | what the output looked like |
|---|---|---|
| R44.4 | slept on the UI thread inside `CallAfter` | both panels failed -- identical to the defect under test |
| R45.6 | `tail -10` cut the first result line | one case produced no output -- identical to a crash |
| R49.4 | called `ExitMainLoop` before the loop existed | the whole harness produced no output |

Each time the harness's own timing produced output indistinguishable from a real
result. R49.4 is the benign member of the set -- *nothing* is obviously wrong,
whereas R44.4's plausible-but-wrong table is the dangerous kind. **The general rule
this lane keeps rediscovering: in an event-driven harness, decide what the output
should look like before running it, because afterwards every shape has an
explanation.**

## 5. Observed: the AB-BA refusal count is not stable

R47's C++ AB-BA run logged one `refused Inner domain busy` and one `ui Inner`. The
same binary now logs two refusals. Both are correct: whether the second thread's
inner acquisition lands while the first still holds its domain depends on the
interleaving.

Only the invariants are stable -- **no thread blocked, both handlers complete** --
and those are what the tests assert. A test asserting `refusals == 1` would be flaky,
and R47's evidence block should be read as one observed interleaving rather than the
behaviour. `lock_semantics_test.py` asserts the invariants; `case_contention` may
assert an exact refusal count only because its 50ms stagger makes the order
deterministic.

## 6. Still open

- **Nothing has run against the binary.** Unchanged from R47.5 and R48.7, and it is
  still the largest gap. Both providers are now proven to *say* the right thing; the
  engine has never *heard* it.
- **Per-handler granularity and `SET REPROCESS` have no fields.** Owner's, unchanged.
- **`lock_provider` sorts by alias string.** Two frontends under different collation
  could in principle order a domain differently. It does not matter while
  `try_lock_table` never waits -- there is no circular wait to order against -- but
  the rationale is a comment, not a test, and if the engine ever gains a blocking
  acquire it becomes load-bearing.
- **No test sets a grouping locale in a Python frontend.** The C++ side is now
  covered; Python's number formatting is not locale-sensitive by default, which is
  an argument, not a run.

## 7. Good Neighbor note

- **What changed.** `gui/uidef/uidef_rt.h` gains `uidef::lock_provider`, a factory
  that builds the `LockProvider` inside the runtime. New:
  `gui/uidef/wx_provider_registry.cpp`.
- **Whose area.** AIF-120's own. Nothing in `src/` or `include/` was touched;
  `xbase::locks` is AIF-116's.
- **What authorization.** Maintainer (member.derald), in-session "next".
- **How to verify or undo.** Verify: build `scopes.cpp` (generated with
  `--dispatch`) against `gui/uidef/wx_provider_registry.cpp` and run under
  `xvfb-run`; all four cases must print True and the header line must show the
  grouping locale writing `16,984`. Undo: deleting `uidef::lock_provider` restores
  the alias-list seam, and with it a target's freedom to write its own commands.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/uidef_rt.h
git add gui/uidef/wx_provider_registry.cpp
git add docs/maintenance/AIF120_PROVIDER_PARITY_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R49 -- the lock verbs move into the runtime on both targets; the C++ seam let a target reintroduce AIF-116"
```
