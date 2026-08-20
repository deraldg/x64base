---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-050
  recorded_at_utc: 2026-08-19T14:45:00Z
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
    baseline_commit: ab7d6ec98
  authorization:
    requested_by: maintainer (member.derald), in-session, "do it" -- repairing defects
      found by the house rule "sweep for your own leftovers before you finish".
  report:
    path: docs/maintenance/AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md
    kind: ruling
---

# AIF-120 -- R42: a ruling shipped and its code did not

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Found by reading the house working-rules skill twenty-one rulings into the session
and running its section 10 sweep -- *"sweep for your own leftovers: uncommitted
files, scratch fixtures, notes owed to other lanes, and anything you cited that is
not tracked."* Nothing failed. Every gate had passed. Three defects were sitting
in committed work.

## 1. R33's fix was never in the repository

`gui/uidef/read_vfp_binary.py` is **gitignored** -- line 2 of <!-- cite-check:ignore -->
`gui/uidef/.gitignore`, a deliberate working copy of the reader that lives at
`tools/vfp/read_vfp_binary.py`.

R33's handoff staged exactly that path. `git add` on an ignored file does nothing,
the commit succeeded, every gate passed, and **the ruling shipped while the code
did not.** Measured on the tracked reader afterwards:

| marker | `tools/vfp` | `gui/uidef` |
| --- | --- | --- |
| `LANGUAGE_DRIVER` | 0 | 3 |
| `codepage_byte` | 0 | 1 |
| `_binary_value` | 0 | 2 |
| `BINARY_TYPES` | 0 | 2 |

So for two hours the lane had a ruling asserting that the reader honours 19
codepages and unpacks binary columns, and a tracked reader that did neither.

> **R42.1.** `git add` on an ignored path is a silent no-op, so a handoff that
> stages one produces a clean commit and no change. A file a ruling depends on
> must be confirmed **tracked**, not merely added.

## 2. Nine committed tools would not import on a fresh clone

Because the reader they imported was the ignored copy, sitting in their own
directory. `import_scx.py`, `import_mnx.py`, `infer_flow.py`, `manifest.py`,
`uidef_tk.py`, `uidef_tk_host.py`, `uidef_html.py`, `uidef_text.py`,
`uidef_wx.py`.

Only `contend_test.py` and `relate_test.py` survived, and by accident -- they
happened to be written with an explicit `../vfp` on the path.

**Verified by rebuilding the tree without the copy** and running each tool: all
nine now import and run, and the tracked reader reports 19 drivers.

> **R42.2.** A tool that imports from its own directory cannot be checked by
> running it in place, because the thing that would be missing is present. Rebuild
> the tree without it.

## 3. R30's document was never committed either

`AIF120_COMPOSITION_RULE_V1.md` and its two evidence files, cited by R31, R38 and
the ledger, were untracked. R30's implementation shipped **inside R31's commit**
and its document did not -- the handoff was written twice and run zero times.

That is the house's `widow` exactly: a tracked document pointing at a target that
does not exist on the surface it ships on.

## 4. What was actually wrong with my method

Three separate defects, one cause: **I verified the wrong thing.** After every
handoff I checked `git log` for the commit -- a habit added earlier today after a
handoff went unrun -- and a commit existed every time. What I never checked was
whether the *paths in it* were the paths that mattered.

The gates cannot catch this. `mandatory-tracked` checks declared files;
`prepush-gate` inspects the staged index, and an ignored path is never in it. Both
passed on every one of these commits, correctly.

> **R42.3.** A green gate is evidence about what was staged, not about what was
> intended. The check that finds this is `git ls-files --error-unmatch` on every
> path a ruling cites, and it costs one command.

## 5. Fixed

- `tools/vfp/read_vfp_binary.py` promoted 403 -> 480 lines. The uidef copy was a
  strict superset -- the only lines removed are the four latin1 decode sites -- so
  the promotion carries R33 without carrying anything else.
- Nine tools now put `tools/vfp` on `sys.path` **ahead of** their own directory, so
  a stale ignored copy cannot shadow the tracked one.
- R30's document and evidence committed.
- A Good Neighbor note for `tools/vfp/` handed to the maintainer in `RE:` form,
  because `PSEUDO_CHAT_BOARD.md` says agents do not write to it directly. I had
  written to it, then read its header, then reverted -- the file is byte-clean.

## 6. Still open

- **`gui/uidef/read_vfp_binary.py` still exists locally.** It is inert now, but a <!-- cite-check:ignore -->
  sandbox cannot delete on this mount. The maintainer can remove it.
- **Nothing checks this automatically.** R42.3 names a one-command check and
  nothing runs it. A gate that resolves every path cited in a ruling's front matter
  and body against `git ls-files` would have caught all three defects.
- **The lane has 22 rulings citing files.** They were swept once, today. Nothing
  re-sweeps them.

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Two commits. The first repairs the widow, the second the reader.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_COMPOSITION_RULE_V1.md
git add docs/maintenance/evidence/AIF120_composite.txt
git add docs/maintenance/evidence/AIF120_composite.png
git diff --cached --stat
git commit -m "AIF-120: R30 -- composition rule document and evidence; the implementation shipped early inside R31"

git add tools/vfp/read_vfp_binary.py
git add gui/uidef/import_scx.py gui/uidef/import_mnx.py gui/uidef/infer_flow.py
git add gui/uidef/manifest.py gui/uidef/uidef_tk.py gui/uidef/uidef_tk_host.py
git add gui/uidef/uidef_html.py gui/uidef/uidef_text.py gui/uidef/uidef_wx.py
git add docs/maintenance/AIF120_SHIPPED_RULING_UNSHIPPED_CODE_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R42 -- R33's fix reaches the tracked reader; nine tools stop importing a gitignored copy"
```

Then confirm the thing that was never confirmed:

```powershell
git ls-files --error-unmatch tools/vfp/read_vfp_binary.py docs/maintenance/AIF120_COMPOSITION_RULE_V1.md
```
