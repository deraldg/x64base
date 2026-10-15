# AIF-171 guarded HELP store refresh lane v1

Date: 2026-10-13. Status: HELP refresh and canonical harvest promotion
complete; DOTREF router parity hardened with zero exceptions; manual Gate 6
candidate chain PASS and awaiting owner status decision; development
implementation complete and not published.

Owner: `member.derald`. Steward: `member.ai.codex`. Run:
`CODEX-20261013-HELP-REFRESH-001`. Parent project:
`project.x64base.runtime`. Upstream lanes: AIF-088 and AIF-170.

Authorization: owner instruction, "APPROVE the guarded gate refresh", after a
measured preflight showed a clean DDICT feed and a stale HELP store.

## Purpose and boundary

Rebuild the derived HELP store only after its compiled reference input and
source contracts agree. Preserve a complete pre-state backup, execute the
LEGACY and current builds separately, and roll back the complete store if any
post-write hard gate fails.

In scope:

- the `COPY` and `DDICT` rows in `include/dotref.hpp`;
- the engine build needed to compile those reviewed reference rows;
- all direct files in `dottalkpp/data/help` as one protected store;
- runtime transcripts, hashes, validation, and development closeout evidence;
- refresh of the internal Portal status projection after the store is proven.

Out of scope:

- edits to the concurrently owned `src/cli/cmd_copy.cpp` contract;
- DDICT catalog data, metadata imports, CDX, CNX or LMDB;
- manual acceptance, website generation, website staging or publication;
- `C:\x64base`, GitHub `main`, deployment, commit or push.

## Entry measurements

Using the repository Python 3.12 environment, full-stack preflight proved:

- website command catalog: 241 registry keys, 241 rows, 241 parsed contracts,
  zero fallback;
- website present-state: PASS against a fresh derivation, excluding build-only
  static and Pagefind counts because no website build is in scope;
- DDICT feed: READY, CANDIDATE, FULLY_VERIFIED, zero diagnostics;
- HELP ordering: FAIL because the store dated 2026-10-08 predates the
  executable dated 2026-10-12;
- contract drift: five differing command/kind pairs -- COPY EXAMPLE, NOTE and
  USAGE; DDICT NOTE and USAGE.

The guarded reference review then found `include/dotref.hpp` still described
COPY only as `COPY <source> TO <target>` and omitted DDICT's
`FAMILY LEGACY|X64` selector. Rebuilding before correcting those inputs would
make a newer but internally inconsistent store.

## Execution controls

1. Align only the two changed dotref rows with the current source contracts.
2. Require `refcheck_v1.py` and `normcheck_v1.py` to remain green.
3. Build the engine and bind the executable hash and timestamp.
4. Record hashes for every direct HELP file and copy the complete set to a
   unique dated backup; verify member names, sizes and hashes.
5. Run `CMDHELP BUILD LEGACY` and `CMDHELP BUILD . D:\code\ccode\src` as two
   separate engine invocations. Never send them as one command array.
6. Run store integrity, ordering, contract drift, harvest freshness, runtime
   HELP reflection, Portal feed and full-stack preflight checks.
7. If a required post-write check fails because of this refresh, restore the
   complete backup, verify hashes, and record the failure. Do not selectively
   mix old and new store files.

## Improvement objective

This run treats reference alignment as an executable precondition of HELP
refresh rather than a remembered checklist item. The before question was,
"Is the store newer?" The improved question is, "Did the reference input,
source contract, executable and resulting store advance in that order?"

## State

- M0 COMPLETE: Portal onboarding, AIF-171 claim, check-in and Good Neighbor
  notice.
- M1 COMPLETE: aligned only the COPY and DDICT dotref rows; reference,
  normalization and source-census gates passed.
- M2 COMPLETE: built the Release engine, bound its SHA-256, and created and
  hash-verified a complete 18-member pre-state backup.
- M3 COMPLETE: ran LEGACY and current builds as separate invocations; store
  integrity, ordering, contract drift, runtime reflection and Portal feed
  checks passed.
- M4 COMPLETE: exported a non-canonical Python measurement candidate, proved it
  14/14 fresh, and retained its v0/v1 producer mismatch as negative evidence.
- M5 COMPLETE: ran the sanctioned engine exporter, proved its v1 candidate
  14/14 fresh, generated a PASS plan with 15/15 package files, repaired the
  stale focused tests, and ran all 114 full-stack tool tests successfully.
- M6 COMPLETE: recorded the maintainer's hash-bound authorization, applied the
  seven-row canonical harvest plan, verified every target, backup and staged
  hash, and proved canonical E5 PASS 14/14 with no rollback.
- M7 CHECKPOINT: ran the explicit manualgen entry checks and five candidate
  stages. Reference, curation, disposition, command-reference and structure
  candidates pass. The command candidate is 164/164 pages; the structure
  candidate is `ALREADY_NORMALIZED_NOOP` with a zero-row status ledger. The
  exact owner status decision is pending; no approval record was inferred.
- M8 COMPLETE: closed the three M3E router advisories under the owner's
  2026-10-14 correction authorization. `DOTHELP HELP` now resolves the HELP
  catalog row, the shell VAR pre-router claims only SET/SHOW/CLEAR, and an
  explicit HELP namespace wins over the bare PREDICATES shortcut. The rebuilt
  runtime resolves 268/268 members through both `DOTHELP` and `HELP /DOT`, with
  zero router exceptions. Existing DOTHELP usage, bare HELP PREDICATES, and
  SET/SHOW/CLEAR VAR behavior remain proven.

The canonical harvest is promoted and the candidate chain is built. Full-stack
preflight step 9 still reports the expected website present-state delta because
the website authority carries the prior canonical row, line and topic counts.
Gate 4 status approval, its plan, its separately authorized apply, website
reconciliation and publication remain separate gates.
