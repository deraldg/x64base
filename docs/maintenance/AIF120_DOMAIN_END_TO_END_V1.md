---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-067
  recorded_at_utc: 2026-08-20T04:20:00Z
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
    baseline_commit: a07c97b17
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- "keep dogfooding
      the engine"; R58 section 5 named these two cases.
  report:
    path: docs/maintenance/AIF120_DOMAIN_END_TO_END_V1.md
    kind: ruling
---

# AIF-120 -- R59: R26's closure reaches the engine, and a write keeps the lock that allowed it

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R58 closed with two gaps: *"One area, not a domain"* and *"No write, and no
contention."* This closes the first and half the second.

## 1. The document's `Relation` becomes one lock domain in generated code

`SOURCE` declares two aliases and one edge:

```
Alias = students / Table = d_STUDENTS.dbf
Alias = enroll   / Table = d_ENROLL.dbf
Relation = students -> enroll ON sid
```

and `uidef_wx.py --dispatch` emits:

```cpp
static const std::vector<std::vector<std::string>> DOMAINS = {{"enroll", "students"}};
```

One domain, not two. R36 reads the edge out of `SOURCE`, R26's transitive closure
collapses the aliases, and the generator carries it into the compiled frontend
without the target being told anything.

## 2. R59.1 -- naming one area acquires the whole closure, against the real engine

```
before any handler: students=free    enroll=free
  during ReadBoth : students=LOCKED  enroll=LOCKED
  completion      : completed result=200/686
after everything  : students=free    enroll=free
```

The handler is fired with `alias = "students"`. **Both areas are locked** while it
runs, and the locks are real -- `xbase::locks::is_table_locked` on two live
`DbArea`s, not a model. `200/686` are the true record counts of both tables.

R26 measured this in a model in July and argued it ever since: locking the area a
handler *names* corrupts 60 of 60 trials because a relation moves the child's pointer
without passing through its interface. **This is that rule executing against the
engine it was written about**, through a frontend generated from a document.

## 3. R59.2 -- the second handler writes to an area it never named

The second handler is fired on `enroll`, and writes to `students`:

```
--- second handler, on the OTHER alias of the same domain ---
  WriteOne write  : ok
  after the write : students=LOCKED  enroll=LOCKED
  completion      : completed result=wrote
```

Two results in one line.

**The reach is real.** A handler that names `enroll` can write `students`, because
the relation joins them -- which is exactly the hazard R26 exists to cover and the
reason the lock is the closure rather than the named area. Had the domain been the
named alias alone, this write would have been unprotected.

**The table lock survives its own write.** R57.2 proved the record case is destroyed
by `DbArea`'s own `unlock_record`, and predicted the table case survives because the
namespaces are independent (R54). Proven here through a generated frontend rather
than a probe: both locks still held after `replaceFieldStored` returns.

## 4. Evidence tier

**runtime-proven**, against `libxbase.a` built from the current tree, with wx 3.2.4,
under `xvfb`. The generated file compiles clean under `-Wall -Wextra` (R58.2).

## 5. Still open

- **No contention.** Both handlers ran to completion before the next fired. Two
  frontends contending for one domain -- where R47's refusal semantics would actually
  fire -- has been proven against the CLI (R50) and never against a typed frontend.
- **Rollback, through the engine.** R52 proved all-or-nothing rollback against the
  CLI and R49 against a recording sink. The typed provider's rollback path has not
  executed: it needs an acquisition that fails partway, which needs a second process.
- **Record granularity is still the unsafe one.** R57.2 stands and nothing here
  changes it; this ruling only exercises table granularity.
- **The Tk backend still has no engine path at all.** It cannot link, so R55.3 leaves
  it on the CLI bridge, and no Tk frontend has ever spoken to a live dottalkpp.
- **R55.2 remains the owner's**, and it is now the last thing in the lock work that
  is not either proven or explicitly parked.

## 6. Good Neighbor note

- **What changed.** New file only: `gui/uidef/wx_domain_registry.cpp`, with its
  build line in the header comment. **No shipped code changed in this ruling** -- it
  is a measurement of what R36, R26, R57 and R58 already built.
- **Whose area.** AIF-120's own. The engine was linked against and read, never
  modified. Both tables are copies; the write touches only the copy.
- **What authorization.** Maintainer (member.derald), standing in-session: "keep
  dogfooding the engine".
- **How to verify or undo.** Verify: the build line in
  `gui/uidef/wx_domain_registry.cpp`; expect `students=LOCKED enroll=LOCKED` during
  both handlers and `free free` after. Undo: the file is a test; deleting it changes
  no behaviour.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add gui/uidef/wx_domain_registry.cpp
git add docs/maintenance/AIF120_DOMAIN_END_TO_END_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R59 -- R26's relation closure acquired through the engine from a generated frontend; a write keeps the table lock that allowed it"
```
