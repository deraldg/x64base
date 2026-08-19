---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-065
  recorded_at_utc: 2026-08-20T03:00:00Z
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
    baseline_commit: 1cdfde0e6
  authorization:
    requested_by: maintainer (member.derald), in-session -- "obviously r55.3 needs
      immediate repair", then "dbarea.cpp", then "work on the nesting probe".
  report:
    path: docs/maintenance/AIF120_TYPED_PROVIDER_V1.md
    kind: ruling
  cross_lane_finding:
    lane: AIF-116
    kind: runtime_observed
    summary: >
      xbase::locks treats a same-owner acquisition as re-entrant by returning true
      without a depth count, so the innermost unlock releases the outermost hold.
      DbArea's write path locks and unlocks per write, which destroys a record lock
      its own caller is holding. Reported as a semantics observation, not a bug
      verdict.
---

# AIF-120 -- R57: the typed provider, and a handler's record lock does not survive its own write

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R55.3 reported that the wx backend speaks console text where a typed API exists. The
owner ruled it needed immediate repair, then pointed at `dbarea.cpp`. The repair took
an hour; what `dbarea.cpp` exposed is the ruling.

## 1. R57.1 -- the typed provider, and the toolkit it does not need

`tools/uidef/uidef_xbase_locks.h` builds a `LockProvider` that calls
`xbase::locks` directly: `try_lock_table` / `try_lock_record` with the owner-aware
overloads, error strings out, and `locked_by_other()` -- a question the text path
**cannot ask at all**, because answering it means rendering a record number into a
command and R48.2 forbids that.

Ordering and all-or-nothing behaviour are identical to the text provider's, because
they are the same rulings (R48.4, R50.1).

It is a **separate header** on purpose. Including it links the engine; not including
it leaves `uidef_rt.h` dependency-free for Tk, HTML and character-cell. The
dependency becomes the target's decision rather than the generator's, which is what
R55.3 recommended.

**Correction 39, caught by the maintainer's question "is the source ready to
compile?"** -- the answer was no, and I had not checked. The header included
`uidef_rt.h` purely to name `Runtime::LockProvider`, and `uidef_rt.h` includes
`<wx/wx.h>`. So a *lock* provider required a *GUI toolkit* to compile, which meant it
could only be built on a machine with both the engine and wx -- exactly one machine,
the maintainer's WSL, and therefore untestable everywhere else. Spelling the
`std::function` type out drops the toolkit entirely. It now compiles against the real
engine headers on a VM with no GUI stack at all, and a `static_assert` proves the
spelled-out type IS `Runtime::LockProvider` rather than merely converting to it.

## 2. R57.2 -- runtime-proven: the write destroys the lock that permitted it

`src/xbase/dbarea.cpp`'s `replaceFieldStored` locks and unlocks around every write:

```cpp
if (!xbase::locks::try_lock_record(*this, rn, &lock_err)) { ... return false; }
...
xbase::locks::unlock_record(*this, rn);
```

and `create_or_validate_owned` treats a same-owner acquisition as re-entrant --
**by returning true, with no depth count**:

```cpp
// Re-entrant lock in same process/session.
if (meta.owner == me.id) { return true; }
```

Linked against the real `libxbase.a` and run:

```
granularity      : record
after handler LOCK   : record locked = yes (vm:15076:1787173931159)
write             : ok
after DbArea write   : record locked = NO ()

  the caller's lock survived its own write : NO -- DbArea's unlock removed it
```

The innermost unlock wins. A handler holding a record lock, performing the write it
took the lock for, is left holding nothing -- and nothing tells it.

**And the mirror, same probe, same run:**

```
granularity      : table
after handler LOCK   : record locked = yes (vm:15079:1787173931166)
write             : ok
after DbArea write   : table  locked = yes (vm:15079:1787173931166)

  the caller's lock survived its own write : YES
```

A table lock survives, exactly as R54's independence ruling implies: `DbArea` takes
**record** locks, and the two namespaces do not reach each other.

### The ruling

**Record granularity is unsafe for any handler that writes** -- which is most of the
handlers worth locking for. The provider keeps the option, defaults it off, and now
**says so at the call site** through the log callback rather than only in a header
comment, which is R52's own complaint about where rules live.

This is the second reason to keep `table` as the default, and it is independent of
the first. R48.3's original reason was withdrawn in R54 as resting on an unmeasured
claim about `FLOCK`. This one is measured.

## 3. What this is, and is not, for AIF-116

The engine is self-consistent. `create_or_validate_owned` says "re-entrant lock in
same process/session" and does precisely that; `DbArea` locks its own writes, which
is right. The hazard appears only when **two layers in one process manage the same
lock**, because ownership is per-process (R47.3, R54.3) and re-entrancy is not
counted.

Reported as a **semantics observation, not a defect verdict** -- R52.1 is a recent
enough lesson about the difference. If it is worth closing, a depth count or a scoped
guard would do it, and both are the engine lane's call.

## 4. Correction 38 -- the probe reported a defect that was its own

The first run printed:

```
after handler LOCK   : record locked = yes ()
```

An empty owner, where the CLI had shown `Record 1: LOCKED (owner Grimwood:21080:...)`.
That looked like `is_record_locked` failing to populate `owner_out`.

It was this:

```cpp
std::printf("... %s (%s)\n",
            xbase::locks::is_record_locked(a, a.recno64(), &who) ? "yes" : "NO",
            who.c_str());
```

**Argument evaluation order is unspecified.** gcc evaluated `who.c_str()` before the
call that fills `who`. Sequencing the call onto its own line printed the owner
correctly, and `is_record_locked` is fine.

Fourth harness defect in this run, and the fourth to produce output that looked like
a finding about something else -- R44.4, R45.6, R49.4, now this. The pattern is not
carelessness in one place; it is that **a harness reporting on someone else's code is
itself untested code, and its failures wear the costume of the thing it measures.**

## 5. How it was run, since it could not be run where it was written

`libxbase.a` is built by `./wslbuild.sh` on Ubuntu 24.04. The Cowork device VM's
libstdc++ is older, so the probe compiled there and would not link
(`__isoc23_strtoull`, `_M_replace_cold`). The Cowork **container** is Ubuntu 24.04
with gcc 13 -- the same toolchain that built the archive -- so the engine headers,
the five static libraries and one fixture table (646 KB, tarred) were staged into it,
and the probe linked and ran first time.

Nothing was installed and no engine source was modified. `tmp/` is gitignored, which
is why the tarball went there.

## 5b. Why the dogfooding is the point, in the maintainer's framing

> *"keep dogfooding the engine, it is part of our proof that working top down and
> bottom up and also development of co-systems project and its documentation."*

R57.2 is the argument in one finding. The hazard is invisible from **below**: the
engine is self-consistent, `DbArea` correctly locks its own writes, and
`create_or_validate_owned` does exactly what its comment says. It is invisible from
**above**: a UI language reasoning about handlers, scopes and lock domains has no
reason to suspect that the write it performs will release the lock it took.

It only appears where the two meet -- a frontend holding a lock across a handler
while the engine locks per write. Neither layer's tests could have found it, because
neither layer is wrong.

That is what a co-system is for, and it is also why the finding had to be **run**.
Read from two files it was an inference; linked against `libxbase.a` it is a fact,
and the mirror case (table survives) came with it for free -- a result I had asserted
in R55.3 and could not have known.

The documentation matters for the same reason. R47 through R57 are the record of a
top-down lane repeatedly discovering that the bottom-up system already had the
answer -- locale, locking, identity, GUI threading -- and once, here, that it had a
question instead.

## 6. Still open

- **The typed provider has never been linked into a generated frontend.** It compiles
  and its calls are proven by the probe, but no wx app has used it end to end. That
  needs a machine with the engine and wx, which is the maintainer's WSL.
- **R55.2 is still an owner decision**, and it is the larger of the two.
- **`locked_by_other()` is untested.** It is three lines and it is untested.
- **Nesting is untested for TABLE locks taken twice** by two layers in one process.
  The same non-counting re-entrancy applies; only the record case has been run.
- **R53.4 still has no implementation.**

## 7. Good Neighbor note

- **What changed.** New: `tools/uidef/uidef_xbase_locks.h` (typed provider, no
  toolkit dependency, warns at the call site) and
  `tools/uidef/lock_nesting_probe.cpp` (the experiment, with its build line in the
  header comment).
- **Whose area.** AIF-120's own. `src/xbase/dbarea.cpp` and `xbase_locks.cpp` were
  **read and linked against, never modified**. Section 3 is an observation for
  AIF-116. The probe writes only to a copy of a fixture table.
- **What authorization.** Maintainer (member.derald), in-session: "obviously r55.3
  needs immediate repair", "dbarea.cpp", "work on the nesting probe".
- **How to verify or undo.** Verify: the build line in
  `tools/uidef/lock_nesting_probe.cpp`, run once with no argument and once with
  `table`; record must report the lock GONE and table must report it held. Undo: both
  files are new and additive; deleting them changes no shipped behaviour.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/uidef_xbase_locks.h
git add tools/uidef/lock_nesting_probe.cpp
git add docs/maintenance/AIF120_TYPED_PROVIDER_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R57 -- typed lock provider with no toolkit dependency; a handler's record lock does not survive its own write"
```
