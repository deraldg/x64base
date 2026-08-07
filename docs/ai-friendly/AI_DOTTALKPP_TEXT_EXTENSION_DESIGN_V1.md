# dottalkpp `.text` supported-extension -- charter + PDLC (v1)

Status: **design-only (review-needed).** Sandbox-authored; code/seam claims read from
source, not compiled. All build + proof steps are maintainer-operated handoffs.

Owner of record: `member.derald`
Lane owner / author: `member.ai.claude.cowork`
Coworker: open (Grok available via the external-AI intake channel if wanted).
Lane / ticket: **AIF-093** (lane `dottalkpp-text-extension`, claimed 2026-08-07 via
`tools/coordination/session_coordinator.py claim-aif`, run_id `COWORK-20260807-003`;
ledger: `coordination/aif/AIF-093.claim`).
Prior art read: `tools/staging/prepush_gate.py` (suffix classifier), `PROMOTE.manifest`
(publication allow-list), `docs/maintenance/UNTRACKED_TREE_DISPOSITION_PROPOSAL_V1.md`
(the valid-file-types ruling), `AI_PORTAL.md` (exclusion single-source-of-truth).

## 1. What `.text` is, and why

Add `.text` as a first-class, **supported** file extension across x64base/dottalkpp:
a plain, transportable text file that is **deliberately rare**, used as a positive
curation marker. This is **purely additive**:

- **`.text` = a new, opt-in marker for curated, transportable, belongs-in-GitHub text.**
- **`.txt` = UNCHANGED.** It stays a fully valid, common text extension. Nothing about
  `.txt` is excluded, gated, demoted, or renamed by this lane.

The value is the POSITIVE marker, not a demotion. Naming a file `.text` is a
deliberate, greppable signal that it was chosen to travel; the promotion tooling can
allow `.text` through as a one-line suffix test, while `.txt` keeps meaning exactly
what it always did. You reach for `.text` only when you want that "this belongs"
intent to be explicit -- which is why it is rare by design.

## 2. Seams this touches (source-verified locations)

1. **Engine / dottalkpp file-type recognition.** Register `.text` wherever the engine
   and CLI enumerate recognized text file types, so tooling treats it as first-class
   text (candidates found: `include/datatype_index.hpp`, `include/xbase_cli.hpp`,
   `include/order_path_resolver.hpp`; P1 pins the exact registry). Non-goal: no new
   binary format, no parser change -- `.text` is UTF-8/ASCII text like `.txt`.
2. **Prepush gate** (`tools/staging/prepush_gate.py`). `.text` already classifies as
   `source/docs/config` (it is neither a `HARD_BLOCK_SUFFIXES` nor a `DATA_SUFFIXES`
   member), so it passes today. P2 makes that explicit and adds the house-style/BOM
   checks that `.md` gets, so `.text` is held to the same ASCII/BOM bar.
3. **Promotion allow-list** (`PROMOTE.manifest`). Add `.text` to the curated
   documentation projection so `.text` publishes to `main`/GitHub. This is the core
   "belongs in GitHub" wiring.
4. **`.gitignore`.** Guarantee `.text` is NEVER ignored (the durability/keep side),
   mirroring the disposition ruling's "authored text is keep."
5. **Doctrine single-source** (`AI_PORTAL.md` exclusion section + the disposition
   proposal). Record the `.text`-curated / `.txt`-scratch convention so future
   sessions apply it.

## 3. Scope and non-goals

In scope: register `.text` as supported (engine recognition + gate + promote +
gitignore + doctrine). Non-goals: changing existing `.txt` behavior (it stays valid
and readable -- this is additive), inventing a binary format, or auto-migrating
existing `.txt` files (a later, separate curation pass may promote chosen `.txt` ->
`.text`).

## 4. PDLC (phased; build -> prove -> accept gate per phase)

- **P0 Charter + claim.** This doc + AIF-093 (done) + intake/registry row.
- **P1 Discovery + design.** Pin the exact engine file-type registry that must learn
  `.text`; enumerate every literal `.txt` recognition site to mirror; produce the
  one-page change list.
- **P2 Build.** Register `.text` in the engine/CLI recognizer; add it to
  `PROMOTE.manifest`; add the explicit `source/docs/config` + house-style/BOM handling
  in the prepush gate; add a `.gitignore` never-ignore guard.
- **P3 Prove (maintainer-run).** Round-trip: create a `sample.text`, confirm dottalkpp
  recognizes/opens it as text; confirm it passes the prepush gate as source/docs/config
  and is caught by the house-style ASCII check; confirm `PROMOTE.manifest` selects it;
  confirm `.gitignore` never ignores it. Recorded under `labtalk/proofs/runs/`.
- **P4 Docs + accept.** Update `AI_PORTAL.md` + the disposition ruling with the
  `.text`/`.txt` convention; publish the user-facing note (manual + website interchange
  section) at the next full-stack push, not real-time.

## 5. Test plan

- Positive: `sample.text` recognized by the engine text path; passes prepush as
  source/docs/config; ASCII/BOM checked; `PROMOTE.manifest` includes it.
- Negative: a non-ASCII line in a `.text` file trips house-style (same bar as `.md`);
  a `.text` file is never matched by any `.gitignore` rule.
- Convention: a `.txt` scratch file in a scratch dir remains gate-able/scratch while a
  sibling `.text` promotes -- the filter distinguishes them by suffix alone.

## 6. Coordination

- Claim done (AIF-093). Host-side: add the intake-queue row; register in
  `labtalk/registries/` if tracked as a project; commit `coordination/aif/AIF-093.claim`
  with the docs. Builds + proofs are maintainer-operated.

## 7. Risks

- **R1 -- silent gitignore capture.** If any existing ignore rule matches `*text*`,
  `.text` could be swallowed. P2 adds an explicit `!*.text` (or equivalent) guard and a
  proof that check-ignore reports it as never-ignored.
- **R2 -- engine recognition scope creep.** Keep `.text` a pure text alias; do not wire
  it into script execution or data import unless a later milestone asks. Additive only.
- **R3 -- convention drift.** The `.text` = "chosen to travel" convention is only useful
  if recorded where sessions read it (doctrine single-source). Prose alone drifts
  (AIF-082); P4 records it, and a future promote-gate that treats `.text` as
  always-allow is a candidate. `.txt` needs no rule change -- it is untouched.

## 8. P1 discovery result -- dottalkpp runtime scan (2026-08-07)

Scanned `D:\code\ccode\dottalkpp` for text files. Measured: **93 `.txt`, 0 `.text`.**
The "home"/curated text separates cleanly from scratch by location + name, which
confirms the marker is worth having (and that authoring future curated text as `.text`
is low-friction):

- **Home / curated (natural `.text`, ~25):** help packs (`help/INDEXING_HELP_PACK.txt`,
  `SET_ORDER_HELP.txt`, `dbarea.txt`, `predicate_help.txt`); READMEs
  (`docs/*README.txt`, `data/dbf/{og,x32}/README.txt`, `data/help/DATA_INDEX_README.txt`,
  `data/scripts/README.txt`); schema docs (`data/dbf/*_schema.txt`); localized
  message-seed text (`data/scripts/messaging_priority_a_seed_v1/*.txt`, en/de/es/fr/it);
  project manifests (`data/projects/*/manifest.txt`).
- **Scratch (correctly stays `.txt`, no change):** proof transcripts
  (`data/metadata/bbs/proofs/*.txt`), superseded/correction/proposal dumps
  (`*.SUPERSEDED_*.txt`, `*.CORRECTION_*.txt`, `*.proposal.txt`), output/url dumps,
  and the pre-excluded generated/tmp/bak/logs.
- **Mis-suffixed oddities (separate cleanup, not this lane):**
  `LIST_CURSOR_SHAKEDOWN.DTS.txt`, `mcc_x64.dtschema.txt`.

Reminder (owner, 2026-08-07): this lane does NOT rename or gate any `.txt`. The list
above only shows that a curated set EXISTS and is greppable; adopting `.text` is opt-in
going forward, and any rename of an existing curated file is a separate owner call.

## 9. P2 plan -- the additive wiring (concrete change-list)

1. **`PROMOTE.manifest`:** add an allow pattern `**/*.text` (with a comment) so any
   `.text` file publishes to the public repo. This is the core "special" wiring -- the
   one-line filter. Does not touch any `.txt` pattern.
2. **Tooling recognition:** add `"*.text"` alongside `"*.txt"` wherever supported text
   types are enumerated for promotion/fixtures (e.g. `tools/staging/promote_data_fixtures.ps1`
   schema filter). Additive.
3. **Prepush gate:** `.text` already classifies as `source/docs/config` (not
   `HARD_BLOCK`, not `DATA_SUFFIXES`), so it passes today. Optional refinement: include
   `.text` in the house-style ASCII coverage so it is held to the same bar as `.md`.
   No BOM check needed (BOM is C/C++ only).
4. **`.gitignore`:** verified no generic `*text*` rule exists (only specific paths like
   `/dottalkpp/data/logfile.txt`), so `.text` is safe from capture (R1 low). Optional
   durability guard: an explicit `!**/*.text` never-ignore line.
5. **Engine recognition:** confirm whether any CLI verb needs to OPEN `.text` as text
   (P1 open item); if not, `.text` is a pure marker + text alias and needs no C++
   change. Keep additive (R2).
6. **Doctrine:** record the `.text` = "chosen to travel" convention in `AI_PORTAL.md`
   and the disposition ruling; publish the user-facing note at the next full-stack push.
