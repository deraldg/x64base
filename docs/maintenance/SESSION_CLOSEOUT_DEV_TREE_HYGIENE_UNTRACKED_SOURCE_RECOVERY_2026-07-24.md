---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260724-001
  recorded_at_utc: 2026-07-24T22:56:28Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: dev working-tree hygiene + untracked-source recovery
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 6d374e63c
    head_commit: e738529f6
  authorization:
    requested_by: maintainer
    scope: >
      Clean up the git working tree (prune stale/unrelated files, isolate
      accidentally-deleted docs/src copies), sync working-tree modifications,
      and report + close the gap where the tracked tree referenced untracked
      source. Diagnosis and command authoring by the AI; the maintainer ran
      every git commit and push.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_DEV_TREE_HYGIENE_UNTRACKED_SOURCE_RECOVERY_2026-07-24.md
    kind: session_closeout
---

# Session Closeout — `development` working-tree hygiene + untracked-source recovery (2026-07-24)

Owning lifecycle: DotTalk++ SDLC (`project.x64base.runtime`).
Operating mode: `development` (integration branch).
Change class: repository hygiene + integrity (no engine behavior changed).
Truth state: git-verified against `HEAD`; clean-checkout buildability restored by
reference analysis, definitive clean-clone build owed (maintainer, occasional).
Promotion state: pushed to `origin/development`; **not** promoted to `C:\x64base`,
not on `main`. Consumers pull `main` via the staging gate — this session did not
touch that path.

## What the maintainer asked for

Clean up the working tree, then confirm nothing that people pull is affected, and
report the status of ERRORSTOP. Roles held per the standing constraint: the AI
diagnosed, authored the exact git command lists, and wrote docs; the **maintainer
ran every commit and push**. The AI did not commit, push, promote, or hard-delete.

## Outcome — three maintainer commits on `development`

| Commit | What | Note |
| --- | --- | --- |
| `d706baeb4` | Pruned ~336 stale/unrelated files as **pure deletions** | `palette/` (157), `designs/` (154), `memo_sidecar_v1/` (10), `.backup-rename-cli/` (8), `patches/` (3), `,gitattibutes/` (1), `tests/ccode.lnk`, `nppBackup` backup, `dottalkpp/.../cases/script.dts`, plus the 21 `docs/`+`src/` originals that were isolated (below). File-scoped per the Pre-Push Gate — no `git add -A`. |
| `fda481694` | Synced **91 modified tracked files** | Regenerated `dbf`/`cnx`/`dbt` data + index artifacts, assorted `src/{cli,tv,help}` edits, `include/*`, `labtalk` registries, docs. Owner chose "everything modified"; `git add -u` (tracked modifications only). |
| `e738529f6` | Committed **15 previously-untracked sources** the tracked tree references | Restores clean-checkout buildability (below). 2,029 insertions, all `create mode`. |

## Recovered-file isolation (the "we have them but git shows deletions" ask)

21 `docs/`+`src/` files had been deleted from the working tree. They were restored
from the last commit, then — per the maintainer's instruction that they should look
**deleted** to GitHub, not renamed — moved out of the repo entirely to the sibling
folder **`D:\code\ccode-recovered\`** (original names, original layout). Result:
git sees clean deletions, no rename pairing, nothing untracked inside the tree, and
a local safety copy is retained off to the side.

## Key finding — six latent clean-checkout build breaks on `development`

A reference check (`git grep` against `HEAD`) showed the **tracked** tree already
referenced **untracked** source that had never been committed. Because the
maintainer works in the same directory where those files exist on disk (and CMake
`file(GLOB)` compiles whatever is present), local builds were green while a clean
clone would fail. The six modules, all now committed in `e738529f6`:

- `src/cli/cmd_stop_on_error.cpp` — defines `cmd_STOP_ON_ERROR`, called by committed `shell_commands.cpp` (ERRORSTOP).
- `src/cli/dotscript_lexing.{hpp,cpp}` — `#include`d by 5 committed files (ERRORSTOP lane's lexer consolidation).
- `include/cli/vdisk_config.hpp` + `src/cli/vdisk_config.cpp` — included by committed `cmd_vdisk.cpp`.
- `include/value/value.hpp` + `src/value/value.cpp` — included by 7 committed files (core `xexpr` value type).
- `include/xbase/field_codec.hpp` + `src/xbase/field_codec.cpp` — included by 4 committed files.
- `include/xexpr/array_value.hpp` + `src/xexpr/array_value.cpp` — included by 3 committed files.
- `include/xexpr/var_store.hpp` + `src/xexpr/var_store.cpp` — included by committed `cmd_var.cpp`, `rhs_eval.cpp`.

Plus the two ERRORSTOP proof scripts (`errorstop/stop_on_error_regression.dts`,
`lexing/comment_handling_regression.dts`). Confirmed **not** required and left
untracked: `src/reference/{data_address,qualified_reference}.{hpp,cpp}` and
`src/cli/cmd_transaction.cpp` (no committed code references them).

## ERRORSTOP status (as reported)

Implemented in dev on 2026-07-20 (AIF-036): a session severity threshold
`OFF|WARNING|ERROR` (default OFF) aborting a running DotScript when a **new**
last-error at/above threshold is recorded (generation-counter guarded), keyed on
the messaging-recorded severity. Surfaces: `STOP_ON_ERROR` command, `SET ERRORSTOP
[TO]` alias, `DOTTALK_ERRORSTOP` env; abort hooks in both script loops. Maintainer
MSVC build was green and it was exercised interactively. **This session's
correction:** its implementation files were untracked and are now committed/pushed
(`e738529f6`) — so ERRORSTOP is no longer a half-committed tree. Remaining
(non-blocking, from the 2026-07-20 closeout): localized `MessageId`s for the
STOP_ON_ERROR status/invalid lines + an `ERROR_STATUS` threshold line, finish the
lexer unification, and tee regression transcripts into the proof corpus.

## Method / housekeeping notes

- **Stale `.git/index.lock` (recurring).** Left by timed-out git reads and,
  suspected, a git-aware shell prompt / editor watcher racing the maintainer's
  commands. The Linux mount cannot delete files inside `.git` ("Operation not
  permitted"), so removal was done Windows-side (`Remove-Item .git\index.lock
  -Force`) and the commit sequence chained (`Remove-Item; git add -u; commit;
  push`) so it completed before the lock could reappear. To avoid re-creating the
  collision, the AI stopped running index-touching git in its sandbox and used
  read-only `git grep`/`git ls-files`/`git cat-file` only.
- **Reference-check limits.** The grep catches header-include and `cmd_*` symbol
  breaks (the large majority). It cannot see a free-function link gap with no
  header signature; the definitive check remains a clean-clone configure/build,
  which the maintainer runs occasionally. Acceptable here because public consumers
  pull `main` through the `C:\x64base` staging gate, not `development`.

## Published

Pushed to `origin/development` (`6d374e63c` → `d706baeb4` → `fda481694` →
`e738529f6`) by the maintainer. Not promoted to `C:\x64base`, not on `main`. The
recovered files live outside the repo at `D:\code\ccode-recovered\`.

## Still open

- Localized `MessageId`s + `ERROR_STATUS` threshold line for STOP_ON_ERROR (messaging follow-up).
- Finish the DotScript lexer unification (line-readers / continuation logic still per-file).
- Occasional clean-clone build of `development` as the definitive buildability proof.
- Large untracked scratch population remains in the tree (notes `.txt`, `.zip`, `tmp/`, experimental `.dts`) — cosmetic, not build-affecting; a future `.gitignore` pass could quiet it.

## Provenance pointers

- ERRORSTOP lane: `docs/maintenance/DOTSCRIPT_STOP_ON_ERROR_LANE_V1.md`; closeout `docs/maintenance/SESSION_CLOSEOUT_DOTSCRIPT_ERRORSTOP_LEXING_2026-07-20.md` (AIPR-20260720-002).
- Authority chain: `AI_README.md` (public-identity block), `AI_PORTAL.md` (Authority), `PROMOTION_PROCESS.md`.
