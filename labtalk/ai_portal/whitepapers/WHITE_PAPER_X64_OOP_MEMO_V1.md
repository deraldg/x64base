# White Paper: The x64 Object-Oriented Memo -- a 64-bit, payload-agnostic
# large-object store inside a DBF-family engine

**Status:** review-needed (authored 2026-08-11). Owner: member.derald.
Coauthor of record: member.ai.claude.cowork (Coworker, Class A).
Evidence discipline: every claim below states its tier -- runtime-proven,
source-evidenced, or chartered -- and cites its proof. Nothing here outranks
its evidence.

## Abstract

Classic xBase memo systems bolted variable-length text onto fixed-width
records with a block pointer: dBASE stored a 10-character block number into a
.dbt of 512-byte blocks; FoxPro stored a 4-byte block reference into an .fpt.
Both leaked their implementation into the record, capped their address space,
and -- in the FoxPro case -- inspected their payloads with a type word. The
x64 memo inverts all three decisions. A memo is an OBJECT addressed by a
64-bit identifier; the record field carries a canonical 16-character hex
TOKEN naming that object; and the store neither knows nor cares what the
object contains. This paper describes the design, the API and its semantics,
the failure its own oracle caught on day one, and the three instruments that
proved it at runtime -- concluding with what the design deliberately does not
claim.

## 1. Historical context: what the classic designs leaked

A DBF record is fixed-width; long text never fit. The era's answer was the
sidecar memo file, and each dialect leaked its mechanics into the table:

- **dBASE III (.dbt):** the memo field holds a 10-character DECIMAL block
  number into a chain of 512-byte blocks. Block granularity, block-chain
  fragility, and a field width chosen by the pointer's print format.
- **FoxPro (.fpt):** a 4-byte block reference and a per-object TYPE word --
  the store inspects its payloads, and the 32-bit reference bounds the file.

Both are pointer-into-implementation designs: the record knows the storage
geometry. Reorganize the sidecar and every pointer is wrong.

## 2. The x64 design: object, identifier, token

The x64 memo is an object store (evidence tier for this section:
source-evidenced -- `include/memo/memo_backend.hpp`, `src/memo/memo_ref.cpp`,
`src/memo/memostore.cpp`; the FPT64 on-disk format is specified in the public
FPT64 reference):

- **Object:** an opaque byte sequence. The store records logical size and
  existence (`stat` -> `{exists, logical_bytes}`) and nothing about meaning.
  There is no type word. Payload-agnosticism is a design INVARIANT, restated
  as a hard constraint by the AIF-070 intake ("memos stay payload-agnostic --
  no special workspace-memo type that limits other payloads").
- **Identifier:** a 64-bit object id -- the address space outgrows every
  classic ceiling by construction.
- **Token:** the record field carries the id as canonical 16-character hex
  (`memo_ref.cpp`; the parser also accepts decimal and the legacy OO form
  for migration). The token names the object; it encodes nothing about
  where or how the object is stored. Reorganize the sidecar freely: names
  survive, pointers would not have.

The interface is deliberately small (`IMemoBackend`): `put_text`,
`update_text`, `get_text`, `stat`, `erase`, `flush`, plus open/close with
`CreateIfMissing`/`OpenExisting`. Two semantics deserve emphasis:

- **Append-new update.** `update_text(old_ref, bytes)` returns a NEW token;
  the old identifier is not reused (runtime-proven: `memo_smoke` asserts the
  token changes; the memo-zoo shadow model tracks token movement on every
  update across 104,044 operations). Consequence: an updated object's history
  is a chain of identifiers, which is precisely what made append-history
  workspace snapshots (SUPERSEDED rows, section 5) natural rather than
  clever.
- **Sidecar lifecycle is automatic but honest.** `cli_memo::memo_auto_on_use`
  binds a store to any open area whose schema carries memo fields --
  autocreating the sidecar by default, failing the USE in strict mode --
  and `memo_auto_on_close` releases it. The binding is per-area and works
  identically for registered work areas and standalone tables (the
  WORKSPACES catalog opens out-of-band and gets the same treatment).

One honesty note the build system itself records: `x64_memo_store.cpp`, an
experimental second OO backend, exists in the tree and is EXCLUDED from the
build while paging and inspection are layered over the working DTX path
(`src/memo/CMakeLists.txt`). The live backend is the DTX MemoStore. The
design has one production spine, not two half-spines.

## 3. The token-in-field contract, and the defect that proved the oracle

The one place the memo touches the record is the token field -- and that seam
bit its own authors on day one, which is worth recording because the failure
is the design lesson. The first WORKSPACES catalog declared its memo field
at the CLASSIC width of 10 (the dBASE block-pointer habit). The canonical
x64 token is 16 hex characters. `set` silently truncated six characters; the
same-session oracle passed (it compared against the in-memory reference);
the FRESH-session read failed with "invalid memo reference token."

Two corrections followed, both now doctrine (runtime-proven, 2026-08-11):
the field is 16 wide, and the write-side oracle reads the token back FROM
THE FIELD before byte-comparing the payload -- the field is what a future
session will read, so the field is what the oracle must trust. The classic
designs leaked geometry into the record; the one residue of that era in x64
-- a field width -- was caught by measurement within hours of first use.

## 4. Proof posture: three instruments, one day

- **memo_smoke** (standing): create, put, round-trip, stat, update-moves-
  token, flush, close, REOPEN, read both objects, erase one, verify the
  neighbor untouched. The minimal honest contract, including reopen
  durability. Runtime-proven since it landed.
- **WORKSPACE_MEMO** (registered regression, first green 2026-08-11): a
  whole database posture -- 43 work areas, 58 declared relations, 9,065
  bytes of .dtschema text -- saved INTO a memo of the self-creating
  WORKSPACES catalog and restored FROM INSIDE THE TABLE, then walked live
  by both relational walkers (positional SET RELATION and the house
  SELECT), which agree to the record. The memo as a carrier of real,
  load-bearing engine state. Runtime-proven.
- **memo_zoo** (M1 soaked 2026-08-11): the adversarial instrument. Six
  seeded driver personas -- self-mutation, cross-memo prefix overwrites,
  grow-and-shed to 64KB, duplication, merge-and-erase, zero-length and
  erase -- with payloads including embedded NUL and high bytes, byte-
  compared against a shadow model every generation, through repeated
  close/reopen cycles and post-chaos quiet sweeps. Four seeds:
  20,500 generations, 104,044 operations, ~215 reopen cycles, ZERO
  divergences. Byte fidelity, cross-memo isolation, reopen durability, and
  payload agnosticism (NULs included): runtime-proven at the store level.
  Replayable by seed; the banner prints the build stamp.

Public accounting: the dottalkpp.com status board carries "Payload-agnostic
memos" at runtime-proven citing the zoo line, and "Memo-resident
mini-databases" at chartered with its first increment noted -- promoted and
demoted by evidence, per the board's own rule.

## 5. What the design enables (each at its honest tier)

- **Workspaces as data (runtime-proven).** Because the payload is opaque and
  the token is stable, a database posture lives in a memo like any other
  object: attributed (`current_member`), timestamped, environment-stamped,
  append-historied with a SUPERSEDED flag, oracle-verified on every save.
  The store describing its own postures -- SelfDoc reaching the data layer.
- **Memo-resident mini-databases (chartered).** The AIF-070 whitepaper's
  destination: an entire small teaching database as a memo payload,
  per-student private workspaces, nested stores. The posture increment is
  proven; the full claim waits for a database, not a posture, to live in
  the memo -- and is stated at exactly that tier everywhere it appears.
- **Teaching payloads generally.** A payload-agnostic object store beside
  fixed-width records is itself curriculum: students can watch the two
  storage disciplines cooperate, byte-for-byte, in a glass-box engine.

## 6. What this paper does not claim

No multi-store transactional guarantee spans DBF, memo, and index
persistence (the ACID analysis scopes this; a single-lane WAL gain does not
extend it). Concurrency at the memo layer is chartered, not proven: the
zoo's M2 -- a second process holding the engine's cooperative FLOCK while
the animals run -- is the named proof, and until it runs the claim stays on
the bench. The store does not police content, prevent runaway callers, or
maintain genealogy; policing would violate the agnosticism this paper
celebrates, and lineage is the caller's bookkeeping (the store owes bytes,
not history). Practical payload ceilings above the zoo's 64KB envelope are
unmeasured and are not asserted here.

## 7. References

Source: `src/memo/memostore.cpp`, `src/memo/memo_ref.cpp`,
`src/memo/memo_manager.cpp`, `include/memo/memo_backend.hpp`,
`include/memo/memo_auto.hpp`, `src/memo/memo_smoke.cpp`,
`src/memo/memo_zoo.cpp`. Format: the public FPT64 reference
(x64base.com, engine docs). Proofs: `REGRESSION RUN WORKSPACE_MEMO`;
memo_zoo transcripts (seeds 20260811 / 7 / 42 / 1993, 2026-08-11).
Charters: `WORKSPACE_MEMO_RESIDENCE_PLAN_V1.md`,
`MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md`, AIF-070 intake
(`AIPR-20260728-GROK-002`). Public state: https://dottalkpp.com/status/ .
