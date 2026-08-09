# Ticket: CNX on x64 -- warn, do not refuse; + WORKSPACE OPEN index-source conveniences

**Status:** BUILT + PROVEN (2026-08-09). Owner: member.derald. Steward: member.ai.claude.cowork.
**AIF-099** (claimed 2026-08-09, run COWORK-20260809-001, lane "cnx-on-x64 warn-not-refuse").
Scopes A/C/REINDEX-routing/D landed and proven by `REGRESSION RUN INDEX_X64_CNX` on the host
(all five expectations PASS, adjudicated by Claude/Cowork from the datarun transcript; REBUILD
proven to populate a CNX on an x64 table, OK=2 FAIL=0).

**Follow-up slice (2026-08-09, same lane):** Scope B was found ALREADY BUILT -- the
`WORKSPACE OPEN <target> CNX|CDX|INX|AUTO|NOINDEX` grammar, mode parse (`parse_index_mode_ci`),
explicit-mode honor (`effective_index_mode_for_area` only applies flavor policy on Auto), and
the flavor-blind attach (`attach_workspace_index`) all predate AIF-099 and carry no x64 guard.
Measure-don't-build: instead of code, a Scope B verification phase was added to
`index_x64_cnx_smoke.dts` (WORKSPACE OPEN DBF CNX attaches the copy's .cnx on x64; plain
students without a .cnx opens unindexed -- mode honored, not swapped to CDX). Cosmetic banner
fixed: `cmd_use.cpp` `valid_index_types_for` now reports "CDX, CNX" for x64 (its own comment
said "change this function only" on policy change). Host re-proof owed: rebuild + rerun
`REGRESSION RUN INDEX_X64_CNX` (now six phases).

`RECURSED IN <- session close-out (Grok Lane 1 wrap + ./datarun CNX-on-x64 check) @ the SET INDEX
refusal, 2026-08-08.` See `RECURSION_MARKERS_V1.md`. This ticket is a parked frame; the origin
frame (send Grok its corrections) is still open.

## Trigger (owner ran the test on purpose to force the failure)

On an x64 (v64/v128) table `TEST64`:

```
. cnx create           -> CNX: created ... TEST64.cnx
. cnx addtag id / name  -> OK
. reindex              -> REINDEX default -> CDX (BUILDLMDB); "BUILDLMDB: failed to build LMDB environment."
. set index to test64.cnx
  SET INDEX: True x64/v128 tables require CDX (LMDB-backed). Use .cdx for this table.   <-- REFUSED
```

The hard refusal is a **stale policy**. History (owner):
- We stopped using CNX with x64 because LMDB worked so well and was truly x64; CNX was not.
- We then **upgraded CNX to x64 standards** so internal x64base RAM tables could have in-RAM index
  support -- CNX fit the bill (realtime maintenance landed XIDX-TXN-02 M1, 2026-07-31; see the
  `CNXLIVE` regression). So CNX is now capable on x64.
- Therefore refusing CNX outright on an x64 table is wrong. **Warn, do not refuse.**

## Decision (owner)

For **non-RAM** x64 use: LMDB/CDX stays the **preferred / default** index. But when the user
**explicitly asks for `.cnx`** (the `.cnx` suffix), **allow it with a warning** rather than
refusing. RAM tables already use CNX and are unaffected. "It is simple -- just some checks we have
to go through, instead of refusing CNX we just warn."

## Scope A -- SET INDEX refusal -> warn + allow on explicit .cnx

- **File:** `src/cli/cmd_setindex.cpp` (~line 278, `err = msg(MessageId::SetIndexV64RequiresCdxText)`;
  guard comment line 79 "True x64/v128 tables require CDX").
- **Change:** when the target container is an explicit `.cnx` on an x64/v128 table, emit an
  advisory (LMDB/CDX is preferred for non-RAM x64; CNX allowed as requested) and **proceed** to
  attach the CNX order, instead of returning the refusal. Keep the refusal only for the ambiguous
  / non-explicit case if any. Preserve CDX/LMDB as the default when no suffix is given.
- **Message:** add a warn-variant message id alongside `SetIndexV64RequiresCdxText` (do not just
  silence it -- non-RAM users should see LMDB is preferred).
- **Related observed symptom (NOT necessarily in scope):** `REINDEX` on the x64 table defaulted to
  CDX/`BUILDLMDB` and reported "failed to build LMDB environment." When CNX is allowed on an
  x64 table, a `.cnx`-ordered x64 table's `REINDEX` should route to the CNX rebuild path
  (`REBUILD`), not force `BUILDLMDB`. Flagged for the recurse-back; the LMDB-env failure itself was
  observed, not diagnosed here.

## Scope C -- SET ORDER tag-container resolution (found on recurse-back, 2026-08-08)

`RECURSED IN <- owner re-test @ SET ORDER, 2026-08-08` (same parked frame). After the SET INDEX
refusal, `SET ORDER TO id` on the x64 `TEST64` failed:

```
SET ORDER: file not found: D:\...\INDEXES\x64\TEST64.cdx
```

- **File:** `src/cli/cmd_setorder.cpp` (lines 23-32): bare-tag resolution *prefers an
  already-attached compatible container*, and only falls back flavor-aware when none is attached --
  `classic -> <table>.cnx`, `true x64/v128 -> <table>.cdx`.
- **Root:** because Scope A refused the `.cnx` attach, nothing was attached, so SET ORDER fell back
  to the x64 default `TEST64.cdx` -- which does not exist -- and failed.
- **Coupling:** fixing Scope A (let the `.cnx` attach) likely makes `SET ORDER TO <tag>` succeed via
  the existing "prefer attached container" path. But the **bare-tag fallback still hard-forces
  `.cdx` for x64** (lines 24-26); make that fallback honor an existing `<table>.cnx` when present
  (advisory that CDX is preferred), instead of only ever looking for `.cdx`.
- Owner note: "set order will need to be modified."

## Scope B -- WORKSPACE OPEN index-source conveniences

Today `WORKSPACE OPEN DBF` auto-attaches the flavor-appropriate index (x64/v128 -> CDX(LMDB),
classic VFP/v32 -> CNX), suppressible with `NOINDEX`
(`src/cli/cmd_workspace.cpp` lines 28, 104, 1968, 2235; shared auto-attach doctrine in
`src/cli/cmd_use.cpp` `auto_attach_candidates_for`, ~line 395). The owner wants the index source
selectable:

- `WORKSPACE OPEN DBF`      -- current behavior (auto CDX/flavor-aware). "We used to make that an option."
- `WORKSPACE OPEN DBF CDX`  -- open all tables and attach CDX. Convenience.
- `WORKSPACE OPEN DBF CNX`  -- open all tables and attach CNX. Convenience.
- `WORKSPACE SAVE` / `WORKSPACE LOAD` already persist and restore **mixed** index graphs; the two
  `OPEN DBF <CDX|CNX>` forms are conveniences over that, not a new capability.

"Minor changes" to the WORKSPACE command parser + the auto-attach selector to honor an explicit
`CDX|CNX` token (and, per Scope A, allow CNX on x64 when explicitly asked).

## Acceptance sketch (repo idiom = datarun script + assertions)

- On an x64 table: `SET INDEX TO <t>.cnx` attaches (with an advisory), `SET ORDER TO TAG <tag>`
  orders by it, and a seek/skip round-trip is correct. No hard refusal.
- `SET ORDER TO <tag>` on an x64 table with only a `.cnx` present resolves to the `.cnx` (Scope C),
  not a missing `.cdx`.
- `WORKSPACE OPEN DBF CNX` opens the set with CNX attached; `WORKSPACE OPEN DBF CDX` with CDX;
  bare `WORKSPACE OPEN DBF` unchanged. `WORKSPACE SAVE` then `LOAD` restores the mixed graph.
- `REINDEX` on a `.cnx`-ordered x64 table routes to `REBUILD` (CNX), not `BUILDLMDB` (see Scope A
  related symptom).

## Scope D -- regression (a fix without a regression rots)

A behavior change to index-attach policy MUST land with a curated regression, or the next refactor
silently reverts it. The repo already has the matrix cells `INDEX_X32` (CNX smoke) and `INDEX_X64`
(CDX/LMDB smoke); **CNX-on-x64 is the missing cell.**

- **New curated regression** (register in `src/cli/cmd_regression.cpp` alongside INDEX_X32/INDEX_X64;
  script under `dottalkpp/data/scripts/`), proposed name `INDEX_X64_CNX`. Self-bootstrapping and
  self-erasing throwaway x64 table in SANDBOX (follow the `students_cdx_smoke` / `students_x32_idxtest`
  pattern already in the index smokes). Explicit-run until soaked, then promote to the default suite.
- **Asserts (the three scopes):**
  - Scope A -- `SET INDEX TO <t>.cnx` on the x64 table attaches with an advisory (no hard refusal);
    a seek/skip round-trip under the CNX order is correct.
  - Scope C -- `SET ORDER TO <tag>` resolves to the `.cnx` when that is what exists (not a missing
    `.cdx`); ordered TOP/BOTTOM/SKIP are correct.
  - Scope B -- `WORKSPACE OPEN DBF CNX` opens the set CNX-attached; `WORKSPACE SAVE` then `LOAD`
    restores the mixed graph.
  - Guard the preferred default: with no explicit `.cnx`, an x64 table still auto-attaches CDX
    (the advisory path must not become the default).
- **Also update** the affected existing smokes if the policy shift changes any asserted line, and
  note it in their descriptions.
- Engine-touching -> host build + `./datarun.ps1` proof; the sandbox cannot run it (see the golden
  rule -- assert only what was actually run).

## BUILD STATUS (2026-08-09) -- Scopes A, C, D AUTHORED; Scope B deferred

`RECURSED BACK <- owner pickup ("clear the CNX block")`. Source authored by Claude (Cowork,
sandbox -- NOT compiled, NOT run; golden rule applies). Changes:

- **Scope A** (`src/cli/cmd_setindex.cpp`, `validate_explicit_ext_for_flavor`): explicit `.cnx`
  on an x64 area prints an advisory and attaches; `.inx` still refused; bare tokens still
  default to `.cdx`. The attach dispatch below the guard was verified extension-based and
  CNX-ready -- the guard was the only blocker.
- **Scope C1** (`src/cli/cmd_setorder.cpp`, `validate_explicit_container_for_flavor`): mirror
  of A for the explicit container+tag form.
- **Scope C2** (`cmd_setorder.cpp`, `default_container_for_flavor`): bare-tag fallback prefers
  an existing `.cdx`, else uses an existing `.cnx` (advisory), else preserves the original
  `.cdx` not-found message.
- **REINDEX routing** (`src/cli/cmd_reindex.cpp`, was the "related symptom"): active CNX order
  now routes bare `REINDEX` and `REINDEX ALL` to the CNX rebuild engine (`+ order_state.hpp`
  include). Flavor defaults unchanged when no CNX order is active. **REBUILD itself needed no
  change** -- verified flavor-guard-free.
- **Scope D** (`src/cli/cmd_regression.cpp` + `dottalkpp/data/scripts/index_x64_cnx_smoke.dts`):
  `INDEX_X64_CNX` registered (explicit-run until soaked). Covers A, C1, C2, the REINDEX
  routing, and the CDX-default-unchanged guard. First application of the promote-final-tests
  rule (glossary).
- **Scope B** (`WORKSPACE OPEN DBF [CDX|CNX]`) is DEFERRED to a follow-up slice -- convenience,
  not part of the block.

**Host actions owed:** `claim-aif` + stamp here; build (`cmake --build build --target dottalkpp
--config Release`); `./datarun.ps1 -CommandLines 'REGRESSION RUN INDEX_X64_CNX'`; paste output
for adjudication; then the scoped commit.

## Registration (on pickup, host-side)

`claim-aif` a fresh number, add the intake row, stamp it here. Engine-touching -> maintainer/host
build + `./datarun.ps1` proof (sandbox cannot build/run). Follows house rules: ASCII only, no
em-dashes, `&&` comment marker, scoped per-path commits.
