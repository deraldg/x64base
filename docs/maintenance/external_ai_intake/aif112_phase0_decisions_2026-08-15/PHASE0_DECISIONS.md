# AIF-112 Phase-0 decisions -- LOCKED (signed 2026-08-15)

Document Control / Inventory / Check-in-Check-out PDLC. Owner member.derald; steward
member.ai.grok.xai (Outside-AI); on-disk scribe member.ai.claude.cowork.
Baseline: `development` @ `23617ec67`. Signed by maintainer + Grok, 2026-08-15.

The dogfood amendment (D1/D7) is the maintainer's, applied to the decision of record itself (not only
the spike brief): the recurring failure mode in this project is a constraint that lives somewhere it
does not get honoured, so the constraint sits in the signed decisions.

## Decisions

- **D1 -- Primary substrate.** In-tree DotTalk++ SQLite ledger, created / queried / locked ONLY
  through x64base / DotTalk++ surfaces (the SQLITE command family, work areas, tables), never a
  side-channel sqlite3 process (dogfood). Git remains the publication path. Fossil is considered,
  NOT adopted, unless the dogfooded spike proves a required property the runtime SQLite surface
  cannot express (same experiment as D7).
- **D2 -- Inventory scope.** Source + docs + samples + Workspace / Database Capsule + memo-resident
  schemas.
- **D3 -- Lock model.** Hybrid: exclusive check-out for non-mergeable items (binaries, capsules),
  advisory for pure text (Git already merges text). Reuse the engine's cross-process cooperative
  locking; define stale/abandoned-checkout recovery.
- **D4 -- Publication boundary.** Private-tree authority only; GitHub remains the clean publication
  gate (dual-tree discipline unchanged).
- **D5 -- Teaching / SelfDoc.** Full HELP + contracts (AIF-025 / AIF-037). Because the spike is
  dogfooded, the spike itself becomes representative student-facing evidence.
- **D6 -- Fence.** Confirmed: no collision with Triggers, Identity, Tuple freeze, AIF-098, or the
  remaining site-and-guard-hardening work.
- **D7 -- First spike style.** pydottalk (or the CLI / runtime API) driving a LIVE x64base instance,
  so every check-out, inventory list, and release is exercised through the product under test.
  Lightweight; stays out of C++ `src/**` until the model is proven. NO naked sqlite3 script.
- **D8 -- Relationship to AIF-055.** Explicitly coordinated: the inventory must be able to lock /
  version Workspace / Database Capsules; coordinate, do not overwrite.

Carried from the charter (to confirm in the spike, not a separate D): identity binding reuses the
existing RBAC (acting member, `bbs`-style permissions, SYSGRANT), not a parallel scheme.

## Next gate

Grok drafts the concrete Phase-1 spike package: a dogfooded pydottalk-drives-x64base spike over one
inventory class, proving the ledger / check-out model through the runtime SQLite surface (and, by
the same run, whether that surface suffices or the D1 Fossil-fallback condition is triggered).
