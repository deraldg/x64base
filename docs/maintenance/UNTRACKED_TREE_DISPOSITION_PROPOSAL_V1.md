# Untracked-tree disposition proposal v1

Owner: `member.derald`
Author: `member.ai.claude.cowork`
Status: **proposal + ruling applied 2026-08-05** (report-only inventory; one
gitignore line applied per the ruling below). Companion to (and deeper than)
`REPO_HYGIENE_PLAN.md`, whose "Recommended Next Cleanup Pass" asks for exactly this
inventory. Measured: 2026-08-05, from a lock-free `git --no-optional-locks status
--porcelain --untracked-files=all` over `D:\code\ccode` @ branch `development`.

## RULING (member.derald, 2026-08-05) -- supersedes the ignore recommendation below

**Let all valid dottalkpp file types THROUGH. Exclude only `.mdb`.** The data/index
family (`.dbf .cdx .dtx .fpt .dbt .meta .dtschema .dtschemas .erz` ...) is NOT
ignored -- these may be tracked as fixtures / source tables (the
track-the-source-tables policy). Only `.mdb` is excluded, because it is regenerable
from the CDX container (SETLMDB) and can be huge. **Keep the proof always:** proof
evidence is tracked by default (nothing but `.mdb` is ignored, so no proof `.dbf`/
`.cdx` can be swallowed -- the AIF-062 scar cannot recur here).

Applied: `.gitignore` now carries `**/*.mdb` (ignore `.mdb` anywhere, matching the
prepush-gate hard block). The "Ignore set" section below is therefore **retracted**
-- do NOT add the `docs/**/*.dbf` block. The clatter is managed by NOT promoting
these to GitHub (`PROMOTE.manifest`), not by ignoring them in development.
Everything else in this doc (the authored keep-set, the scratch-to-sidecar) stands.

## The number, and why it is not one job

`7216` untracked files. That is not a backlog and not scratch; it is three
different intents wearing one `git status`. Sorting them needs the promotion
model, not a broom.

Reconciling the two things said about this tree:

- "We gitignore most of this, it is all development-to-development, we don't need
  it in GitHub." True for the **generated data/index layer**.
- The promotion model's durability rule: unpublished **authored** lanes must stay
  versioned in development, because "if development has no history, those lanes are
  gone" (`PROMOTION_MODEL_SEED_V1.md`). True for the **authored doc/source layer**.

Both hold because they are about different layers. GitHub `main` only ever
receives the `PROMOTE.manifest` subset regardless; the question here is only
"tracked in development, yes or no", which is the `.gitignore` deny-list question.

## Three intents (measured)

| Intent | What | Count (approx) | Disposition |
| --- | --- | ---: | --- |
| **Authored** | `.md .py .hpp .cpp .mmd` -- docs, tools, source | 3513 | **Keep. Commit per-lane.** Never ignore -- this is the durability-critical set. |
| **Generated** | `.dbf .cdx .dbt .dtx .fpt .inx .mdx .meta .dtschema` -- regenerable data + index artifacts | 873 | **Ignore** (deny-list), subject to Rulings 1-2 below. |
| **Scratch** | root one-offs, transcripts, dumps, dated `*.bak-*` | ~130 | **Sidecar age-out** (not `.gitignore`). 50-file list already produced; `*.bak-*` already ignored. |

The remainder (json/csv/dts/ps1 mixed into lanes) rides with its lane: a lane's
`.json`/`.csv` **outputs** are generated (ignore); its `.py`/`.ps1`/`.dts`
**tools** are authored (keep). Disposition follows the file's role, not its
extension alone.

## Keep set -- authored, commit per-lane (do NOT ignore)

These buckets are dominated by authored content and must stay versioned in
development. They are a **commit** effort (per-lane, scoped slices), not an ignore
target:

| Bucket | Authored | Note |
| --- | ---: | --- |
| `docs/manuals` | 659 | authored manual source; `manualgen/generated/` already ignored |
| `dottalkpp/docs` | 823 | docs + reusable tooling |
| `docs/datadict` (md/py) | 992 | READMEs, baselines, acceptance reports, generator tools |
| `docs/maintenance` (md) | 424 | lane docs and closeouts |
| `docs/messaging` | 340 | authored messaging docs |
| `selfdoc` / `labtalk` / `pycrud` / `bindings` / `src` | ~120 | authored source/tooling |

Committing these is out of scope for a hygiene pass and belongs to their lanes.
The point here is the negative: **a `.gitignore` sweep must not swallow them.**

## Ignore set -- RETRACTED by the ruling

Originally this section proposed a `docs/**/*.dbf`-style deny-list for the ~873
generated data/index artifacts. **The ruling retracts it.** Those file types are
let through (tracked when they are fixtures/source tables). The ONLY ignored data
type is `.mdb` (`**/*.mdb`, already applied), because it regenerates from the CDX.

Rationale the ruling settled, kept for the record:

- **Fixture policy:** `dottalkpp/data/dbf` had 42 `.dbf` tracked, 78 untracked under
  the track-the-source-tables policy. Rather than ignore the 78, they are let
  through so any source table can be tracked with a plain `git add`.
- **Proof-always (was the AIF-062 risk):** because nothing but `.mdb` is ignored, no
  proof `.dbf`/`.cdx` can be swallowed. The 16 data files under `*PROOF*` paths and
  `SYSPROOF.*` are tracked by default. No negations needed.

## Deferred -- generated `.csv` (do NOT gate yet)

Ruling (member.derald, 2026-08-05): generated `.csv` files **can** be gated
eventually, **but not now**. They stay let-through until BOTH:

1. the full-stack documentation push is finished, AND
2. we have proven they are no longer needed, OR they are officially incorporated.

Rationale: many `.csv` (harvest manifests, datadict exports, metacollect outputs)
are still live INPUTS to the manual/datadict generation. Gating them before the
generation is proven self-sufficient would starve a producer. Revisit only after
the flush closes; until then, `.csv` is tracked/through like the other valid types.
Do not add any `*.csv` ignore in the interim.

## What NOT to do

- **No blanket `*.dbf` / `*.cdx` ignore.** The ruling lets these through; ignoring
  them would collide with the fixture policy and the proof-always rule.
- **No ignoring of `.md`/`.py`.** That is the durability set.
- **No moving or deleting** authored lanes to "tidy up." Unpublished is normal
  (`PROMOTION_MODEL_SEED_V1.md`).
- **Never track `.mdb`.** Regenerate it from the CDX (SETLMDB). Gate hard-blocks it.

## Recommended safe sequence

1. **Scratch first (done/ready):** sidecar the 50 root one-offs
   (`tools/staging/triage_root_sidecar_v1.txt`); dated `*.bak-*` already ignored.
2. **Ruling 2, then the `docs/**` generated block:** clear the evidence check, add
   the deny-list above with any negations. Quiets ~360 files, zero durability or
   publish risk.
3. **Ruling 1, then the `dottalkpp/data` pass:** once you classify the 78 DBFs,
   ignore the working-data remainder. Largest single quieting, but gated on your
   fixture call.
4. **Authored lanes (separate, ongoing):** commit `docs/manuals`, `docs/messaging`,
   `docs/datadict` docs, etc. as scoped per-lane slices when each is ready. This is
   the durability work; it is not a hygiene sweep and should not be rushed into one.

Net: steps 1-3 quiet the tree without risking authored history; step 4 is the real
"version the unpublished lanes" work, done deliberately.
