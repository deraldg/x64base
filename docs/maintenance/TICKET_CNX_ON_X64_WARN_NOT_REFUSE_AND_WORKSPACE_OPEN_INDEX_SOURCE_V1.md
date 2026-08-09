# Ticket: CNX on x64 -- warn, do not refuse; + WORKSPACE OPEN index-source conveniences

**Status:** ticket (review-needed, owner will recurse). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-08. **AIF: unclaimed** -- claim a fresh number with `claim-aif` on pickup (do NOT reuse
AIF-052/097). This is a scoping ticket, not a build; the owner said "create a ticket and we will
recurse back."

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

## Registration (on pickup, host-side)

`claim-aif` a fresh number, add the intake row, stamp it here. Engine-touching -> maintainer/host
build + `./datarun.ps1` proof (sandbox cannot build/run). Follows house rules: ASCII only, no
em-dashes, `&&` comment marker, scoped per-path commits.
