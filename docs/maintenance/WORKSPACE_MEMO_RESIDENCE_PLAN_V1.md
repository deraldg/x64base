# Workspace-in-Memo Plan V1 -- saving database workspaces in memo fields

**Status:** review-needed plan (authored 2026-08-11). Owner: member.derald.
Coauthor of record: member.ai.claude.cowork (Coworker, Class A).
Parent lane: **AIF-070** (virtual workspaces / memo-resident mini-databases,
Grok intake `AIPR-20260728-GROK-002`; whitepaper on file). This plan is that
lane's FIRST RUNNABLE MILESTONE, not a new lane: before an entire database
lives in a memo (chartered, not yet run), the POSTURE of a database -- the
`.dtschema` snapshot -- lives in a memo. Smallest honest step, per house habit.

## 1. The idea in one paragraph

`WORKSPACE SAVE` already serializes a whole database posture -- areas, indexes,
tag orders, aliases, 58 declared relations -- to a small plain-text `.dtschema`
(runtime-proven: CASCADE_ENV Section 2 restores 43 areas + 58/58 relations
from one file). x64 memos are payload-agnostic and do not inspect what they
store (source-evidenced: `src/memo/memo_ref.cpp`). Put the first inside the
second: a `WORKSPACES` catalog table whose memo field carries the byte-exact
`.dtschema` text. Workspaces become DATA -- queryable, relatable, attributed
to a member, distributable over the BBS -- and the memo-resident lane gets its
first proof.

## 2. Design rules (inherited + new)

- **One format, two carriers.** The `.dtschema` text is the payload,
  byte-identical in file or memo. No second serializer, no memo-specific
  format. The FILE is the round-trip ORACLE: a memo readback must
  byte-compare against what the same SAVE writes to disk. (The dual-carrier
  verification pattern, applied to ourselves.)
- **Memos stay payload-agnostic** (AIF-070 hard constraint 1). The engine
  gains no "workspace memo type"; the catalog table is convention, not a
  memo-layer feature.
- **Classic behavior untouched** (AIF-070 hard constraint 2). File-based
  SAVE/LOAD remains the default; memo residence is additive syntax.
- **Attribution mandatory.** The catalog row records `current_member()`
  (AIF-075); an unattributed snapshot poisons a trust-based store.
- **No perishable literals in this plan.** Counts and sizes below are
  measured-at-writing or marked for M0 re-measure.

## 3. What exists (evidence-tiered)

| Piece | Tier | Evidence |
| --- | --- | --- |
| `.dtschema` serialize/restore | runtime-proven | `CASCADE_ENV` Sec 2; `workspaces/cascade_all.dtschema` |
| Loader tolerates unknown lines | runtime-proven | `* ` comment blocks + rejected-line handling, 2026-08-10 transcripts |
| Payload-agnostic 64-bit memos | source-evidenced | `src/memo/memo_ref.cpp` |
| Serializer location | source-evidenced | `cmd_workspace.cpp` `schema_save_to_file` (~L1402) -- FUSED to `ofstream`; the pivot refactor below |
| Memo-resident mini-databases | chartered | AIF-070 whitepaper; public status board entry |
| CLI memo WRITE path from command context | UNKNOWN -- M0 measures | do not assert; see M0 |

## 4. Milestones

**M0 -- Discovery (measure, do not assert).** (a) How command code writes a
multi-line string into a memo field today (REPLACE path? direct MemoRef API?
what do BBS post bodies use?); (b) EOL fidelity through the memo layer (the
oracle gate will catch, but know first); (c) practical memo size envelope vs
measured `.dtschema` sizes (cascade_all is ~small-KB; re-measure); (d) read
the AIF-070 whitepaper section on workspace payloads so this milestone lands
inside its architecture, not beside it.

**M1 -- The pivot refactor (small, testable, engine-neutral).** Split
`schema_save_to_file` into `schema_save_to_string()` + a thin file writer;
same for the loader (`schema_load_from_string()`). Behavior change: none.
Proof: existing WORKSPACE SAVE/LOAD transcripts unchanged; CASCADE_ENV stays
10/10. This refactor is worth doing even if the lane stalls -- it is what
makes ANY second carrier possible.

**M2 -- Catalog + write path.** `WORKSPACES` catalog table (x64 flavor;
canonical posture: PK tag on WS_NAME): `WS_NAME C`, `SAVED_AT` timestamp,
`AUTHOR C` (current_member), `NOTES C`, `SHA256 C` (payload hash, lineage),
`SNAPSHOT M`. New syntax (owner decision D1 below) writes
`schema_save_to_string()` into the memo, upserting by name, FLOCK per append
as the BBS store does. **Oracle gate:** immediately read the memo back and
byte-compare against the string; also compare against a file SAVE of the same
state. Mismatch = hard fail, loudly.

**M3 -- Read path + the proof.** Load syntax feeds the memo text to
`schema_load_from_string()`. THE demonstration, per the testing-sequence
doctrine (SET RELATION first): save the Cascade posture to memo, WORKSPACE
CLOSE, load FROM MEMO, then rerun the CASCADE_ENV Section 2 traversal --
parent BOTTOM + REL REFRESH drives the child to record 11, and the SQLSEL
walker agrees. Both walkers over a graph restored from inside a table.
Promote per promote-final-tests: either CASCADE_ENV gains a Section 3 or a
new `WORKSPACE_MEMO` regression with G-guards + oracle byte-compare marker.

**M4 -- Provenance surfaces.** `WORKSPACE LIST` (or DIR) over the catalog;
author/date/hash visible; glossary entry; site status-board row moves the
memo-resident entry's story forward: "first increment runtime-proven --
posture-in-memo; full mini-database still chartered" (tier honesty: the BIG
claim stays chartered until a database, not a posture, lives in the memo).

**M5 -- Horizon (explicitly NOT this plan).** The whitepaper's full vision:
student mini-databases in memos, per-member private workspaces, nested
stores. Each needs its own milestone and proof; nothing here claims them.

## 5. Owner decisions requested

- **D1 -- Syntax.** `WORKSPACE SAVE <name> MEMO` / `WORKSPACE LOAD <name>
  MEMO` (trailing carrier keyword, house-SELECT precedent of optional
  keywords) vs `WORKSPACE PUBLISH/FETCH <name>`. Recommend the former:
  same verbs, additive carrier.
- **D2 -- Catalog home.** `dottalkpp/data/DBF/x64/WORKSPACES.dbf` (engine
  data root) vs per-system bundles carrying their own catalog. Recommend
  data root now; bundles later if systems want private catalogs.
- **D3 -- Lane accounting.** Run as AIF-070 M-milestones (recommended; the
  charter asked for exactly this) vs a fresh AIF claimed via
  `session_coordinator.py claim-aif`.
- **D4 -- Upsert vs append-history.** Overwrite by name, or keep every save
  as a row (history in-store) with LATEST flagged. Recommend append-history
  with a `SUPERSEDED` flag -- it is the no-perishable-literals rule applied
  to snapshots, and it costs one field.

## 6. Risks, honestly

EOL/encoding fidelity through the memo layer (oracle gate catches; M0
measures); serializer refactor touching a proven path (mitigated: transcripts
+ CASCADE_ENV must stay green before any new syntax lands); scope creep
toward M5 (mitigated: Section 5 exists so nobody -- including the coauthor --
reads this plan as the mini-database claim).

## 7. Why this is the right next brick

It converts the status board's oldest "chartered" entry into a runtime-proven
first increment using only proven parts; it makes workspaces first-class
attributed data (the store describing its own postures -- SelfDoc doctrine
reaching the data layer); and every milestone is one sitting long with its
proof named in advance.
