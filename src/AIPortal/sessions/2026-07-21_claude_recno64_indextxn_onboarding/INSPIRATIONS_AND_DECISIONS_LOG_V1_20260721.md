# Inspirations & Decisions — Derald's dev gold (living log)

> The real gold we're mining: dev lessons, decisions, solutions. Quality and best
> practice as a **recursive and cyclical** theme. This log captures Derald's calls,
> principles, and design intent as they're spoken — append, date, never lose them.

**Convention:** newest at top of each section; date every entry; keep the exact
intent, not a paraphrase that softens it.

---

## Design principles / working philosophy

- **2026-07-21 — Quality is recursive and cyclical.** Best practice isn't a phase; it re-enters the work at every layer and iteration. Real dev lessons/decisions/solutions are the product, not a byproduct.
- **2026-07-21 — Be a good steward of the code.** If you see a problem while developing, flag it even if it's out of your lane. (→ `OBSERVATIONS_STEWARDSHIP` log.)
- **2026-07-21 — Constructive & safety pushback welcome; Derald is final authority.** Disagree plainly with reasoning on correctness/safety; flag taste once and move on; once decided, build it that way without relitigating.
- **From memory / project canon — Authority hierarchy:** *Conventions suggest. Registration declares. Metadata records. Runtime proves. Validators enforce.*
- **From memory — Status must be earned:** `runtime-evidenced` › `source-evidenced` › `active beta` › `canary` › `planned lane`. Milestones need falsifiable exit conditions + proof artifacts.
- **2026-07-21 — Prefer live truth over inferred truth.** e.g., gate on the live attached backend (`IndexManager::isCdx()`), not a filename-suffix guess (`orderstate::isCdx`). Runtime proves.

## Terminology / naming (locked)

- **2026-07-21 — "Native indexing" = CDX's own self-contained file format** (`cdxfile::`, twin of `cnxfile::`), independent of LMDB. **"LMDB indexing"** = the `CdxBackend` running over an LMDB env. Don't call the LMDB thing "native."
- **2026-07-21 — LMDB is the default index lane** (dev/DEVELOPMENT profile). `.cdx` file = tag-directory container; keys live in the LMDB env (`<cdx>.d`). CNX = V32 lane, CDX = V64 lane.
- **2026-07-21 — Native CNX and native CDX are twin container formats** (same header/tagdir/RUN/page primitives; differ only by magic + recno width). CNX has the working RUN1 key path; native-CDX key path is unrealized (LMDB fills it).

## Architecture decisions

- **2026-07-21 — Duplicate keys are allowed in some situations.** The composite `base‖recno8` key encoding keeps each record's index entry distinct, so incremental erase/upsert touch only the target row and never disturb sibling duplicates.
- **2026-07-21 — Full relationships & joins are supported** (SET RELATION/RELATIONS, REL JOIN/ENUM, ERSATZ). They consume the index by **materializing an ordered recno vector** (`DbTupleStream`) from the live backend — so index freshness governs join/relation correctness.
- **2026-07-21 — Vectored/long table & field names fall back to standard sizes via Derald's name-mangling algorithm.** Full name lives in x64 metadata; classic descriptor holds the mangled form. Consumers must resolve *either* the full vectored name or its mangled alias to the same field (tuple layer already does via `xfg::resolve_field_index_std`).
- **2026-07-21 — Keep the batch-rebuild capability permanently** (BUILDLMDB / REBUILD / REINDEX) for backwards-compat services and as the reconciliation/crash-recovery path. Transactional in-COMMIT maintenance is opt-in behind `SET INDEXTXN`, **default OFF** — so it can be delayed while testing and lands dark.
- **From project canon — Optional-index architecture:** `xbase` (physical engine, neutral no-op index hooks) + `xindex` (provider that installs hooks when attached). Profiles `DOTTALK_INDEX_MODE = NONE | LEGACY | LMDB`. `index_hooks` is the neutral seam; xbase never names `IndexManager`.

## Solutions / patterns worth reusing

- **2026-07-21 — Falsifiable, output-scored regression via DotScript.** No ASSERT primitive; prove with `SEEK` (consults the index) + `TUP`, and use a **unique sentinel key** as the discriminator. `COUNT FOR` scans the DBF and will pass even with a stale index — not an index-freshness proof.
- **2026-07-21 — RECNO64 widening is "stop narrowing at the CLI layer."** The engine (`recno64`/`recCount64`/`gotoRec64`) and order backend (`order_collect_recnos_asc → vector<uint64_t>`) already speak 64-bit; the bugs are int/long/uint32 carriers in the CLI/tuple/nav layer.
- **2026-07-21 — Interface changes flip atomically.** When a virtual/interface signature widens (e.g., `OrderPosition.recno`), change the interface + all implementors + all callers in one commit; never leave it half-widened.

## Working agreements

- **Outside-AI Delivery Rule:** hosted-AI changes come as reviewable change packages (patch, manifest, contracts read, behavioral effects, open questions) — `review-needed` drafts; no direct edits to `D:\code\ccode`.
- **We test source.** When a script accompanies something new, it's to exercise real compiled source — deliver compilable files, not pseudocode. Datetime-suffixed filenames.
- **Lanes** track work streams with milestone gates + proof artifacts (`XIDX-TXN-01` LMDB, `XIDX-TXN-02` CNX, tuple-vectoring RECNO64, …).

---

*Append new entries as Derald spouts them off. This file is the gold ledger.*
