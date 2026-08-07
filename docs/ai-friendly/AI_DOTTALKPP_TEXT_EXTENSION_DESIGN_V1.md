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
a plain, transportable text file that is **deliberately rare**, used as a curation
marker. The payoff is a clean filter:

- **`.text` = curated, transportable, belongs-in-GitHub text.** Reviewed, promotable.
- **`.txt` = the common default -- treated as potentially dirty-tree scratch.**

Today `.txt` is overloaded: it is both real documentation AND transcripts, dumps, and
one-off scratch (the untracked-tree disposition put ~130 root `.txt`/one-offs in the
"scratch, sidecar age-out" bucket). Because `.txt` means both things, the promotion
tooling cannot tell curated text from clutter by extension alone. A rarely-used
`.text` extension gives an unambiguous, greppable signal: "this text was chosen to
travel." It makes the GitHub-vs-dirty-tree filter a one-line suffix test instead of a
per-file judgment.

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
- **R3 -- convention drift.** The `.text`=curated / `.txt`=scratch split is only useful
  if recorded where sessions read it (doctrine single-source) AND, ideally, later given
  a gate. Prose alone drifts (AIF-082); P4 records it, and a future gate is a candidate.
