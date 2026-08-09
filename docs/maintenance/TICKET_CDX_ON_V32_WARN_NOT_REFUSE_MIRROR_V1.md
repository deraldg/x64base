# Ticket: CDX-on-v32 -- warn, do not refuse (the mirror of AIF-099)

**Status:** ticket (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-09. **AIF: unclaimed** -- claim a fresh number with `claim-aif` on pickup and stamp
it here. Parent: `project.x64base.runtime`. Sibling lane: AIF-099
(`TICKET_CNX_ON_X64_WARN_NOT_REFUSE_AND_WORKSPACE_OPEN_INDEX_SOURCE_V1.md`) -- same shape,
opposite direction. Discovery record: `proof.cnx_orthogonality_recno_permutation`.

## The owner hypothesis this lane proves (or bounds)

"I always suspected the other way around would work almost out of box -- using v32 tables with
v64 LMDB indexes." Endorsed on mechanism: this is the WIDENING conversion. The LMDB/CDX backend
derives typed keys from live field values -- a v32 table's fields feed key derivation exactly as
a v64 table's do -- and small v32 recnos embed losslessly in the 64-bit keyspace. Where
CNX-on-x64 (the narrowing direction) carries real ceilings (RUN1 4-byte recnos, int32 counts,
10-char names), CDX-on-v32 has no analogous mathematical boundary. The only thing in the way is
the same stale-policy guard family AIF-099 just cleared on the other side.

## The guards to stretch (census before edit -- some may have moved)

- `src/cli/cmd_setindex.cpp` `validate_explicit_ext_for_flavor`, classic branch: accepts only
  `.inx`/`.cnx` (`SetIndexV32AcceptsInxOrCnxText`). Stretch: explicit `.cdx` on a classic table
  -> advisory + attach (CNX stays the classic preferred/default).
- `src/cli/cmd_setorder.cpp` `validate_explicit_container_for_flavor`, classic branch: refuses
  `isCdx` (`SetOrderV32UsesCnxNotCdxText`). Mirror of AIF-099 C1.
- `cmd_setorder.cpp` `default_container_for_flavor` classic branch: returns `.cnx`
  unconditionally. Mirror of C2: prefer existing `.cnx`, else use an existing `.cdx` (advisory).
- `cmd_setorder.cpp` `preferred_attached_container_for_flavor` classic branch: honors only
  `isCnx`. Mirror of Scope F: an attached CDX on a classic table wins bare-tag resolution.
- `src/cli/cmd_reindex.cpp` `default_family_for_area`: classic -> INX. Mirror routing: active
  CDX order on a classic table routes bare `REINDEX` to the CDX/BUILDLMDB family.
- `cmd_use.cpp` `valid_index_types_for`: classic reports "CNX, INX" -> "CNX, INX, CDX".
- Engine feasibility gate (measure first): confirm `BUILDLMDB` / `activate_cdx_on_area` accept a
  v32 area (key derivation, LMDB env creation). The orthogonality proof predicts yes; the
  regression proves it. If a real engine gap surfaces (not a guard), it is its own finding.

## Regression (promote-final-tests rule)

`INDEX_X32_CDX` -- mirror of `INDEX_X64_CNX`, same seven-plus-phase shape: disposable v32 copy
in SANDBOX; BUILDLMDB a CDX for it; explicit `.cdx` attach with advisory (not refusal); explicit
container+tag order; bare-tag fallback; bare REINDEX routes to CDX when CDX order active;
attached-CDX wins bare-tag (Scope F mirror); CNX-default-unchanged guard; cross-slot decoy
(configured slot outranks the hard-coded INDEXES_X64 slot -- note `dirs_for_mode` appends
`idxX64Dir` for ForceCdx, the exact mirror of the leak the owner caught). Explicit-run until
soaked.

## Rules inherited

Warn-not-refuse (owner ruling family, 2026-08-09); classic default UNCHANGED and proven so;
advisory-first raw-ASCII messages (catalog promotion is the messaging lane's call); known-bad
proofs per gate (AIF-100 M2); dogfood after proof (`proof.owner_dogfood_caught_cross_slot_leak`).

## Registration (on pickup, host-side)

`claim-aif` fresh number; intake row citing it; stamp here. Engine-touching: host build +
`./datarun.ps1` proof; sandbox authors, host proves, Claude adjudicates transcripts.
