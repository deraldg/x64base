# Selfdoc <-> AI-Portal schema sharing + normalization study (V1)

Status: review-needed. Author: member.ai.claude.cowork (lane steward, AI memory-retention lane).
Final authority: member.derald. AIF: AIF-086 (this study and its R1 extend the AIF-086 CRUD
`schema_registry` lane; filed under AIF-086, no new lane number). Baseline: `development` (measure the tip; figures below are as-read
2026-08-17). No source or schema mutated by this study -- it is analysis only.

Framing (from the maintainer): the AI-BBS and work-tracking are to become an ORTHOGONAL system.
Orthogonal is not the same as incompatible. The goal of this study is the seam where they can be
100% compatible -- shared shape, shared identity, shared lifecycle vocabulary -- without fusing
concerns or write authority.

## 1. The two schema worlds, as they actually stand

There are two parallel catalogs of catalogs, each with its own description layer.

**AI-Portal / BBS / identity** is described by `tools/dbf/schema_registry.py` (the source of truth
the CRUD and reports consume), with field lists copied verbatim from the C++ schema headers
(`identity_schema.hpp`, `bbs_schema.hpp`, `ruling_schema.hpp`, `tracking_schema.hpp`). Three groups:

- identity: SYSUSER, SYSMEMBER, SYSROLE, SYSPERM, SYSROLEPERM, SYSMEMROLE, SYSOVERRIDE, SYSASSIGN, SYSGRANT
- bbs: SYSBOARD, SYSTHREAD, SYSPOST  (all `writable=False` -- the daemon owns this store)
- portal / work-tracking: SYSRULING, SYSLANE, SYSRUN, SYSRUNLANE, SYSPROOF, SYSTASK
- plus SYSCHATLNK (`syschatlnk_v1.schema.json`), the cross-lane link (agent assignment <-> conversation)

Shared conventions across this world: a surrogate `ID N 20` primary key plus a natural key
(UKEY/MKEY/BKEY/LKEY/RKEY/...); bi-temporal stamps `VFROM/VTHRU/ROWVER` on the tables that have a
validity window; composite-key crosswalks for junctions; and -- the important one -- an explicit
`ClosePolicy` per table (`bitemporal`, `status`, `append_term`, `status_str`, `crosswalk`). The
ClosePolicy IS a normalized lifecycle vocabulary: it tells one engine how "delete/close" means for a
table that is bi-temporal versus one that carries a STATUS ladder versus an append-only ruling.

**Selfdoc** is described by `.dtschema` contracts under `dottalkpp/data/schemas/{metadata,help,messaging}/`
plus `selfdoc/metadata_system_registry_v1.json` (which registers 24 collection SYSTEMS, not tables)
and `selfdoc/reference_identity_authority_v1.json` (the identity-normalization contract). Its catalogs:
SYSCMD, SYSFUNC, SYSSUBCMD, SYSARGS, SYSMSG, SYSHELP, the four HELP_*_LOCALE companions, and the
messaging pair SYSTEM_MESSAGES / SYSTEM_MESSAGE_TEXT.

Shared conventions across the selfdoc world: a domain-string primary key (`CMD_ID C 32`, `FUNC_ID C 32`,
...); a single `VER_AT C 24` version stamp (or `CREATED_AT/UPDATED_AT` on locale rows); an `ACTIVE L`
boolean plus status strings (`IMPL_STAT`, `TRANSL_STA`, `REVIEW_STA`) for lifecycle; and free-text
stewardship/provenance (`OWNER`, `SRC_AUTH`, `SRC_FILE`, and on help rows `REVIEWED_BY`,
`SOURCE_HASH`, `GENERATED`, `CURATED`).

## 2. Reporting + CRUD: what already spans a catalog, and how

`tools/reports/build_reports.py` renders four HTML reports over the identity/bbs/portal catalogs,
driven by `portal.yaml`: BBS_BOARDS_REPORT and AI_PORTAL_REPORT (public, also reachable from the
site nav) and BBS_ACCESS_REPORT and AIF_RULINGS_REPORT (marked private, generated but never
published). `tools/dbf/crud.py` (AIF-086) is a pydottalk-backed CRUD over the same registry: reads
work on every table, writes are single-writer, portal + identity are writable, and the BBS catalog is
refused for writes because the daemon may hold that store with no lock to coordinate against. Delete
defaults to a policy-driven soft-close (rewrite STATUS / clear VTHRU), with `--purge` for the
irreversible xBase tombstone.

The load-bearing observation: both the reports and the CRUD are driven ENTIRELY by
`schema_registry.py`. A table that is in the registry gets CRUD, soft-close, and reporting for free.
A table that is not in the registry -- every selfdoc catalog today -- gets none of it. That is the
whole leverage point of this study.

## 3. Where the two worlds overlap, and where they must not be conflated

Field-level, the selfdoc catalogs carry almost none of the identity-world normalization stack. None
use `VFROM/VTHRU/ROWVER`; none carry a sensitivity class; none carry an identity foreign key
(OWNER/SRC_AUTH/REVIEWED_BY are free-text strings, not references into SYSMEMBER). SYSCHATLNK is the
only table in either world carrying the full cross-cutting set (bi-temporal + SENSCLASS +
PROVIDER/PRODUCT/MODEL/RUNID + MEMBERID/MKEY/ASSIGNID + STATUS/ARCHIVED/PINNED).

The single genuine shared concern is PROVENANCE and STEWARDSHIP. Selfdoc says it with
`OWNER`/`SRC_AUTH`/`SRC_FILE`/`SOURCE_HASH`/`GENERATED`/`CURATED`; the portal says it with
`STEWARD`/`OWNERKEY`/`AUTHORKEY`/`RUNKEY`; SYSCHATLNK says it with `PROVIDER`/`PRODUCT`/`MODEL`/`RUNID`.
Same question -- "who or what produced this row, and from where" -- three vocabularies.

One thing must NOT be normalized by conflation: VISIBILITY is not SENSITIVITY. Selfdoc's
`VIS`/`VIS_TIER`/`PUB_SURF` is publication surface (does this belong on the public doc site). The
identity world's `SENSCLASS` is data sensitivity (does this row expose credentials or the permission
matrix). They are different axes. If AI/BBS reporting ever surfaces selfdoc content, BOTH axes must
be present and evaluated; collapsing them would either leak sensitive rows or over-hide public ones.

## 4. Opportunities to share and normalize (ranked)

R1 -- Register the selfdoc catalogs in `schema_registry.py`, with a per-table `writable` flag and a
ClosePolicy. This is a description change, not a schema migration, and it is the highest-leverage,
lowest-risk move: it immediately extends soft-close CRUD and the report engine to the selfdoc world
without touching a single DBF. Give the selfdoc catalogs `writable=False` at first (they are
candidate-writer projections owned by the metacollect pipeline; treat them like the BBS store until a
write owner is agreed), so they gain read + report + validation without opening a second writer.

R2 -- Resolve stewardship to identity. Keep the human-readable `OWNER`/`SRC_AUTH` strings, but add a
resolution/validation step that maps them to `SYSMEMBER.MKEY` the same way SYSCHATLNK uses a soft FK
(`MEMBERID` + `MKEY`). Then "who owns this command's help" is the SAME kind of fact as "who stewards
this lane" and "who authored this post" -- one member identity, referenced everywhere, orthogonal
systems still not knowing about each other's tables.

R3 -- Unify the provenance vocabulary. Reconcile PROVIDER/PRODUCT/MODEL/RUNID (AI provenance) and
SRC_AUTH/SRC_FILE/GENERATED/CURATED (source provenance) into one documented provenance shape, and let
`RUNID`/`RUNKEY` reference SYSRUN so "which run produced this row" is one join across selfdoc AND
portal. This is the concrete form of the memory lane's provenance principle: attribution is one fact
type, not per-system reinventions.

R4 -- Normalize the lifecycle vocabulary. Map selfdoc `ACTIVE`/`IMPL_STAT`/`TRANSL_STA` onto the
existing ClosePolicy taxonomy (a boolean ACTIVE is just a `status` policy with a terminal). Once
declared, one soft-close engine covers both worlds identically. The registry header already admits
"the schemas are NOT uniform" -- this is where that non-uniformity gets a shared grammar instead of
special cases.

R5 -- Adopt `ROWVER` on the selfdoc catalogs (optimistic-concurrency counter). Cheap, and it makes
the CRUD update path byte-identical to the portal path. Keep `VER_AT` as the human display stamp; add
full `VFROM/VTHRU` only where a selfdoc row genuinely has a validity window (most are regenerated
wholesale, so full bi-temporal would be overkill there).

## 5. Reverse flow: what selfdoc does better, that the portal side should adopt

Sharing is not one-directional. Three selfdoc conventions are ahead of the portal/BBS side and are
worth pulling back the other way:

- `GENERATED` / `CURATED` boolean pair -- did a machine emit this row, or did a human curate it. The
  portal and BBS tables have no such distinction, and it is exactly the "agent output vs human
  judgment" line the memory-retention lane cares about. Worth adding to SYSRUN/SYSPROOF and to
  SYSCHATLNK.
- `SOURCE_HASH` / `TXTHASH` -- a content-hash for drift / link-rot detection. This is the same
  discipline as the site's diagram-provenance byte-compare and the retro "attribution survives link
  rot" rule. A hash on SYSPROOF would let a proof detect when its cited source has changed underneath
  it.
- `SRC_FILE` -- an explicit on-disk source pointer. Cleaner than inferring source from AUTHORKEY.

## 6. The orthogonality boundary (what stays separate on purpose)

Compatibility here means shared SHAPE and shared IDENTITY, not shared WRITE AUTHORITY. The write
boundaries are real and must be preserved: the BBS store is daemon-owned (CRUD read-only), the portal
work-tracking is single-writer CRUD, and the selfdoc catalogs are pipeline-owned projections. Keeping
those three writers apart is what makes the systems orthogonal; giving them one identity space, one
provenance vocabulary, one lifecycle grammar, and one registry is what makes them 100% compatible.

SYSCHATLNK is the reference pattern for the seam: it LINKS a work assignment to a conversation without
merging the work tables into the BBS tables. (SYSCHATLNK's design originated with member.derald; it
was implemented under AIF-086. It is the maintainer's own model for the orthogonal-but-compatible
seam, which is why this study leans on it.) Replicate that -- link tables, not merged tables --
wherever selfdoc needs to relate to identity or work-tracking (for example, "this command's help was
last revised under run X" is a link row, not a new column welding selfdoc to SYSRUN).

## 7. Recommended first step and non-goals

First step: R1 alone, as a scoped, self-verifying change -- add the selfdoc catalogs to
`schema_registry.py` as `writable=False` with declared ClosePolicies, and extend
`test_schema_registry.py` (which already reparses the C++ headers) to reparse the `.dtschema`
contracts so the registry cannot drift from the schemas. That yields read + report + validation over
the selfdoc world with zero write risk, and it is a bounded, dogfoodable candidate for a Copilot
coding-agent PR or a maintainer run.

Non-goals for now: no second writer into the selfdoc store; no bi-temporal retrofit of catalogs that
are regenerated wholesale; no merging of visibility and sensitivity; no fusing of the BBS and
work-tracking tables. Those either add risk or violate the orthogonality the maintainer set.

## 8. Conformance: one security/user system

Invariant (confirmed 2026-08-17): every system references actors through ONE security/user system --
the identity catalog: `SYSUSER` (authentication credential) + `SYSMEMBER` (the principal/actor) + the
RBAC catalogs (`SYSROLE`/`SYSPERM`/`SYSROLEPERM`/`SYSMEMROLE`/`SYSOVERRIDE`/`SYSASSIGN`/`SYSGRANT`),
gated at runtime by `principal_key()` / acting member (`USER AS` / `act_as`) / `agent_permitted()`.
There is no second user, credential, or auth store -- verified: no competing table exists in the
schema or metadata trees.

Conformance today:

| System | Actor field(s) | Binding to the identity system | Conforms |
|---|---|---|---|
| identity | -- | it IS the system | n/a |
| bbs | `SYSPOST.AUTHORID`, `SYSTHREAD.OPENEDBY` (N) + `agent_permitted()` | numeric member id + permission gate | yes (AIF-075) |
| SYSCHATLNK | `MEMBERID` (N) + `MKEY` (C64) + `ASSIGNID` (N) | explicit soft FK to `SYSMEMBER` / `SYSASSIGN` | yes |
| portal / work-tracking | `OWNERKEY` / `STEWARDKEY` / `MEMBERKEY` (C64), `DECIDEDBY` (N) | same identity, bound softly by string key, not an enforced id | partial |
| selfdoc | `OWNER` / `SRC_AUTH` (C64) | free text, never resolved to `SYSMEMBER` | no (R2) |

Closing the gaps needs no new system. R2 resolves selfdoc `OWNER`/`SRC_AUTH` to `SYSMEMBER.MKEY` (the
soft-FK pattern SYSCHATLNK already uses), and the portal string keys should validate/resolve to a
member the same way. Both make the ONE identity system the enforced reference everywhere. This is the
security reading of the orthogonal-but-compatible rule: orthogonal write authority, one identity.

## 9. Provenance / verification note

Field lists in Section 1 for the identity/bbs/portal world are read directly from
`tools/dbf/schema_registry.py`. The selfdoc field triples and the registry/contract shapes are from a
read-only inventory of `dottalkpp/data/schemas/{metadata,help,messaging}/` and `selfdoc/**`; the two
load-bearing claims -- that no selfdoc catalog carries the identity-world normalization stack, and
that `reference_identity_authority_v1.json` is the existing selfdoc identity-normalization contract --
should be re-confirmed against the files before any change lands. This study proposes; it does not
mutate schema, and it makes no claim to have run the engine.
