---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260725-BF1
  recorded_at_utc: 2026-07-26T02:33:51Z
  agent:
    provider: not_exposed
    product: not_exposed
    model: not_exposed
    access_mode: human_operated_tool
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 238c85f22
  authorization:
    requested_by: maintainer
    scope: >
      Envelope reconstructed 2026-07-28 during AI-portal audit backfill
      (AIPR-20260728-002). AI-authored, human-committed (introducing commit
      238c85f22, 2026-07-26); original session/agent identity was not recorded and is
      marked not_exposed; access_mode human_operated_tool per
      AI_REPORT_AUDIT_CONTRACT_V1.md.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_AIF050_FULLTREE_BACKFILL_2026-07-25.md
    kind: session_closeout
---

# Session Closeout -- AIF-050 M2/M3: `@dottalk.file` full-tree backfill + schema v1 revision

**Run:** AIPR-20260725-001 (continues; same session as the AI-BBS bundle).
**Lane:** AIF-050 (`docs/maintenance/AI_RUN_TRACEABILITY_LANE_V1.md`).
**Member:** member.ai.claude.cowork (implementer). **Owner / committer:** member.derald.
**Branch:** `development`. **Date:** 2026-07-25.
**Result:** GREEN -- census 1034/1034 (100.0%). One repair force-push (see Incident).

## What was asked

Take ownership of the unfinished AIF-050 contract track and make the metadata harvest richer by
actually implementing it: put a `@dottalk.file` block at the top of every `.cpp` and `.hpp`, drop
fields that duplicate what git already tracks (directory location), and add the fields that let a
file **self-identify** and **connect back to its project and the members assigned to it**.

## Survey first (the standards-seed rule, applied)

The maintainer asked whether the existing blocks were blank placeholders. They were **not**:

- 12 files carried `@dottalk.file` (the AI-BBS lane's hand-classified dogfood set).
- Their `layer:` values were **manually set and accurate** (`glue`, `engine-core`, `command`,
  `header`) -- not the heuristic default.
- `src/cli/cmd_bbs.cpp` and `cmd_net.cpp` carried real `owns:` values (`DOT|BBS`, `DOT|NET`).

So the work was **not** "fill in blanks." It was a **schema revision plus a preserving upgrade**:
rewrite the 12 without losing their hand-set values, then backfill the other 1,022.

## Schema change (v1 revision)

Removed (redundant with git -- the maintainer's explicit instruction not to re-track location):

- `path:`        -- the file's own path; git tracks it, and it goes stale on any rename.
- `provenance:`  -- was `prov://<same path>`; carried no information the path did not.

Added (the AI-connectivity fields -- the point of the exercise):

- `lane:`   -- the AIF lane the file belongs to, so a file resolves to its lane doc, its run in
  `ai_runs.yaml`, and through `current_by_lane` to the **last agent who worked it**.
- `owner:`  -- the accountable member. `member.derald` on every file (owner/committer per
  governance; agents deliver, they do not commit).

Resulting block:

```cpp
// @dottalk.file v1
// subsystem: bbs                      <- derived from directory
// layer: glue                         <- preserved if hand-set, else derived
// owns: DOT|BBS                       <- command surface, blank for non-commands
// project: project.x64base.runtime
// lane: AIF-052                        <- NEW: connects to lane doc + ai_runs.yaml
// owner: member.derald                 <- NEW: accountable member
// status: supported
```

## Tool changes -- `tools/fullstack_docs/source_census.py`

- `SUBSYSTEM_LANE` map: `bbs -> AIF-052`, `security -> AIF-053`, `identity -> AIF-045`,
  `selfdoc -> AIF-050`.
- `STEM_LANE` per-file overrides for files whose lane differs from their directory
  (`cmd_bbs -> AIF-052`, `cmd_net -> AIF-053`, `bbsd_main -> AIF-054`).
- `--upgrade` mode: finds an existing block via `BLOCK_RE`, extracts `layer:` and `owns:`, re-emits
  in the current schema. Skips blocks already on the new schema (idempotent). Files with no block
  are left to `--write`.
- `derive_block()` takes `override_layer` / `override_owns` so upgrade and fresh-write share one
  code path (no second, drifting emitter).
- Bug found and fixed **during** the upgrade run: `_extract_field` used `\s*` after the colon, which
  matches newlines -- on a blank `owns:` line it swallowed the newline and captured the **next**
  `// project:` line as the value. Changed to `[ \t]*` (horizontal whitespace only). Caught by
  spot-checking output, not by the tool. **The 12 upgraded files were reverted and re-run clean.**

## Result

```
=== @dottalk.file source census (AIF-050 M2/M3) ===
total source:     1034
census (@file):   1034
commands (@usage):230
non_command:      804
uncovered:        0
coverage:         100.0%
```

- 12 blocks upgraded (hand-set `layer:` and `owns:` preserved, verified file by file).
- 1,022 blocks written fresh.
- M3's `--strict` gate is now **passable** -- promotable from advisory to a hard drift gate on
  maintainer decision.

## Incident -- directory-level `git add` swept untracked scratch (repaired same session)

**What happened.** The commit script used `git add -- src include`. That stages **everything** under
those directories, tracked or not. ~111 untracked files went in with the backfill: chat/notes `.txt`
dumps, `.zip` archives, `.dbf`/`.dbt` data, `.patch` sidecars, `.dts` smoke scripts, and the whole
`src/AIPortal/sessions/2026-07-21_.../` archive. Committed and pushed to `development` as
`6f86c8aed`.

**Repair.** `git reset --hard HEAD~1`, re-stage with `git add -u src/ include/` (**`-u` = update
tracked files only**), recommit, `git push --force origin development`. Remote now at `3706da78c`:
1035 files, no scratch. `main` was never touched.

**Collateral, found only on re-inspection.** `reset --hard` also reverted the **tracked, modified**
`source_census.py` (losing the session's tool work, restored from context) and **deleted from disk**
all 111 untracked files the bad commit had added. Both were recovered:
`git restore --source=6f86c8aed --worktree` over a NUL-delimited file list brought the 111 back.

**Lessons (candidates for the engineering-standards seed):**

1. **`git add -u <dir>` for tracked-tree sweeps, never `git add -- <dir>`.** The `-u` flag is the
   difference between "commit my edits" and "commit everything sitting here."
2. **`reset --hard` is not surgical.** It reverts tracked modifications you meant to keep and
   deletes files the discarded commit introduced. Snapshot or stash the tool changes first.
3. **A "scoped add" script must verify its own scope.** Staging a file count and a suspicious-
   extension check *before* `git commit` would have caught this pre-push. The repair script has that
   check; the original did not.
4. **If you create or expose trash in the tree, resolve it -- delete or ignore.** Maintainer's rule,
   applied below.

## Trash disposition (`.gitignore` hardening)

Rather than leave 111 loose files as a permanent trip hazard, the clear scratch categories inside
`src/` and `include/` are now ignored (dated + commented section citing this incident):

- prose/notes: `/src/**/*.txt` with `!/src/**/CMakeLists.txt` negation
- scripts/sidecars: `/src/**/*.dts`, `/src/**/*.patch`, `/src/**/*.before_image_web_defaults`
- archives/data: `/src/*.zip`, `/src/data/`, `/include/manuals/`
- parked collection areas: `/src/AIPortal/`, `/src/psych/`, `/src/labtalk/`

**Deliberately NOT ignored** (14 files, left visible as untracked -- they look like real source and
deserve a promote-or-delete decision, not silent hiding):

```
include/reference/data_address.hpp        src/reference/data_address.cpp
include/reference/qualified_reference.hpp src/reference/qualified_reference.cpp
src/cli/cmd_transaction.cpp               src/cli/schema_json_v1.schema.json
src/schemas/spec/schema_json_v1.schema.json  src/schemas/students.schema.json
src/tests/test_field_codec.cpp            src/tests/test_pdlc_foundation_smoke.cpp
src/tests/test_recno64_boundary.cpp       src/tests/test_recno64_sparse_e2e.cpp
src/tests/test_x64_record_limit.cpp       src/tests/vfp_field_interop.py
```

## Commits

| Commit | Content |
|---|---|
| `3706da78c` | AIF-050 M2/M3 full-tree backfill -- 1034 source files + `source_census.py` schema/upgrade |
| (follow-up) | `.gitignore`: scratch categories inside `src/` and `include/` |

Superseded and removed from remote history: `6f86c8aed` (the swept commit).

## Open / next

- **`layer:` heuristic review.** 1,022 blocks carry a *derived* layer (`helper` for `.cpp`, `header`
  for `.hpp`, `command` where `@dottalk.usage` is present, `test` by path/stem). Accurate at the
  coarse level; the finer distinctions the BBS files got by hand (`glue`, `engine-core`) are not
  inferred. Refine per subsystem as lanes are touched -- `--upgrade` preserves anything hand-set.
- **`lane:` is blank on most files.** Only four subsystems + three stems map today. Every future lane
  should add its `SUBSYSTEM_LANE` / `STEM_LANE` entry as part of its own closeout, so lane coverage
  grows with the work instead of needing a second sweep.
- **`owns:` blank on non-command files** by design. Fill where a non-command file plainly owns a
  surface.
- **M3 promotion decision:** flip `--strict` into the drift gates (sibling of AIF-033/035) now that
  it can pass. Maintainer call.
- **The provenance DBF** (M2's remaining piece) is still not built; the block no longer carries a
  `provenance:` pointer, so if that catalog is built it will key on `path + subsystem + lane`.

## Verification performed

- `--sample` on two files before any mutation (checked `owns:` extraction and lane mapping).
- Post-upgrade: all 12 files inspected individually for preserved `layer:`/`owns:` and absent
  `path:`/`provenance:`.
- Post-write: random sample across `src/cdx`, `src/cli`, `include/browser`, `include/xbase_64.hpp`.
- Full census re-run: 1034/1034, 100.0%.
- Grep for surviving `^// path:` / `^// provenance:` -- 8 hits, all confirmed to be **legacy
  comments in file bodies**, none inside a `@dottalk.file` block.
- Post-`.gitignore`: `git ls-files --others --exclude-standard src include` returns exactly the 14
  intentionally-visible files.
