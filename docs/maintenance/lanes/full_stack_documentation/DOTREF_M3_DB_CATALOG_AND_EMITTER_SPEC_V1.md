# Dotref M3 DB catalog and emitter specification v1

Date: 2026-10-13

Status: M3E applied and verified; post-M3E router parity hardened;
development implementation complete and not published

Owner: member.derald

Steward: member.ai.codex

Lane: AIF-171 continuation, full-stack documentation and HELP

Runs: CODEX-20261013-DOTREF-M3-SPEC-001; CODEX-20261013-DOTREF-M3B-001;
DOCFLUSH-20261013-002

Evidence tier: source-evidenced specification; build- and runtime-proven M3E

Authorization: owner first authorized the specification after the 2026-10-13
prior-art review, approved the recommended structural rulings and bounded M3B,
then approved the exact M3C gate for report-only M3D. After review of M3D, the
owner said "do so" to the separately stated M3E header apply, build, runtime,
and rollback boundary. No HELP/META, manual, website, publication, commit, or
push authorization was inferred.

## 1. Boundary

This document specifies the staged implementation and records the completed
M3B-M3E boundaries. M3E changed only the generated row region in
`include/dotref.hpp`, rebuilt the two direct consumers, and produced G8-G9
proof. It did not:

- create or alter a DBF, DTX, CDX, CNX, or LMDB artifact;
- change any other `*ref` header;
- rebuild the HELP store, metadata, manuals, website, or publication;
- approve a candidate, resolve a prose conflict, or authorize promotion;
- change AIF-171's separately pending status decision.

M3B through M3E each retained their own authorization boundary. Any later
HELP/META harvest, manual, website, promotion, commit, push, or publication
step still requires its applicable gate and authorization.

## 2. Decision

Create a normalized, DBF-backed reference catalog as the reviewed intermediate
between the one metacollect harvest and the compiled `*ref` headers.

Do not make a flat, hand-edited `DOTREF.dbf` another authority. Instead:

1. metacollect harvests source once;
2. normalized `SYSREF*` candidate tables join structural facts, prose, aliases,
   arguments, subcommands, functions, and reviewed voice overrides;
3. `DOTREF.dbf` is a generated DOT-namespace inspection/projection table;
4. one emitter generates the `dotref`, `foxref`, and later `*ref` family from
   the normalized catalog, parameterized by namespace and voice;
5. the compiled header remains the runtime/bootstrap representation until a
   separately designed runtime-catalog change is approved.

This is the settled model-B direction in
`DOTREF_AUTOMATION_AND_REF_RECONCILIATION_SCOPE_V1.md`: derive the skeleton,
preserve curated voice with provenance, and keep the header for compile-time
compatibility.

## 3. Source evidence and prior art

### 3.1 Active consumer

The active implementation is `src/cli/cmdhelp.cpp`; the old
`cmd_cmdhelp.cpp` spelling survives only in `src/cli/cmdhelp.hpp`'s historical
file comment.

`cmdhelp::collect_commands()` currently merges:

    registry U foxref U dotref U edref

and reads DOT `name`, `syntax`, `summary`, and `supported` directly from the
compiled `dotref::catalog()` (`src/cli/cmdhelp.cpp:741-835`).

The current HELP builder separately mines `@dottalk.usage` contracts and ranks
`USAGE_CONTRACT` above `DOTREF` (`src/cli/cmdhelp.cpp:1558-1568` and
`src/cli/helpdata_cmdhelp_bridge.cpp:558-647`). Therefore the source contract is
already the primary prose tier, while DOTREF remains a compiled seed and
bootstrap surface.

### 3.2 Existing database shapes

The repository already has two useful downstream shapes:

- `COMMANDS.dbf`: one merged catalog row with command, implemented, supported,
  usage memo, and verbose memo (`src/cli/cmdhelp.cpp:976-1013`);
- `HELP_LINE.dbf`: normalized topic/kind/source/role/ordinal/text rows.

Neither may become the first-step authority as-is. Both are built downstream of
the current compiled header and would create a circular harvest if used to
generate that same header.

### 3.3 Existing generators and gates

- `tools/fullstack_docs/dotref_autogen.py` proposes missing native rows only.
  It does not refresh existing syntax, summary, support, or voice.
- `dottalkpp/tools/help/generate_dotref_from_metadata_v1.py` can emit a full
  candidate, but its default merge mode carries missing syntax and summary from
  the header it is intended to replace.
- `tools/fullstack_docs/refcheck_v1.py` checks identity resolution and phantoms.
- `tools/fullstack_docs/normcheck_v1.py` checks cross-authority identity and
  handler normalization.
- Neither gate proves that existing DOTREF syntax still describes the handler.

### 3.4 Dated measurement, not a permanent literal

Measured 2026-10-13 in the shared development tree at HEAD
`a48a709e968d8c208b6c19bd699028f0d25ade3e`:

- current header parser: 268 DOTREF entries;
- partial generator merge: 201 current entries metadata-backed, 67 carried,
  2 new, 270 emitted;
- partial generator pure mode: 203 emitted;
- missing-entry proposer: zero missing native command rows;
- refcheck: zero guarded phantoms;
- normalization gate: no findings;
- `SRCUSAGE.dbf`: 244 live rows;
- `SYSCMD.dbf`: 212 live rows;
- `SYSARGS.dbf`: 249 live rows.

The generator's default `SYSCMD_IMPORT_v1.csv` had 203 rows while live
`SYSCMD.dbf` had 212. This is a measured input-selection defect, not permission
to prefer the live table blindly. M3 must consume one explicit, hash-bound
harvest package and reject mixed-run inputs.

`include/dotref.hpp` was already modified by another session when this
specification began. Its working-tree SHA-256 was
`F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5`.
This hash is evidence only; it is not a promotion baseline or an ownership
claim.

## 4. Authority hierarchy

Every emitted field has exactly one normal authority. A lower source may fill a
declared gap only through an explicit disposition; it may not silently win by
being the last writer.

| Fact | Normal authority | Notes |
| --- | --- | --- |
| canonical identity, handler, visibility, active/implemented state | current metacollect `SYSCMD` candidate from the same run | registry-derived structural fact |
| subcommand identity and dispatch style | current `SYSSUBCMD` candidate from the same run | do not promote a routed subcommand to a top-level command |
| function identity | current `SYSFUNC` candidate from the same run | only when the namespace admits functions |
| argument identity and value shape | current `SYSARGS` candidate from the same run | arguments are not usage prose |
| syntax/usage, summary, examples, notes, related, risk | current `SRCUSAGE` candidate from the same run | harvested from `@dottalk.usage` by metacollect |
| aliases | registry, usage contract aliases, shortcut resolver, reviewed alias policy | retain provenance for each edge |
| namespace-specific voice | approved `REFVOICE` row | may change wording, never structural identity |
| current header wording | migration evidence only | no steady-state carry-forward authority |

### 4.1 Implemented is not supported

CMDHELP deliberately models `implemented` and `supported` separately.

- `IMPLEMENTED` comes from a reachable registry/handler identity.
- `SUPPORTED` comes from the reviewed contract status and support policy for the
  reference namespace.

The existing prototype maps `SYSCMD.ACTIVE` directly to DOTREF `supported`.
M3 must not preserve that shortcut. An active internal, compatibility-only,
experimental, or developer command can be implemented without being supported
on the public DOT surface.

### 4.2 No silent header carry

The current header is a one-time migration source for curated wording. After a
row is classified, it must resolve to one of:

- `SOURCE_CONTRACT` -- source wording is accepted;
- `APPROVED_VOICE_OVERRIDE` -- reviewed namespace wording intentionally wins;
- `DELIBERATE_EXCLUSION` -- the identity is outside this namespace;
- `BLOCKED_CONFLICT` -- candidate promotion stops.

`CARRIED_FROM_HEADER` is allowed only in a migration report. It is forbidden in
a promotable candidate.

## 5. Logical model

The model separates identity from repeated text and from alias relations. This
is required because one reference identity can have multiple syntax forms,
examples, aliases, locales, and namespace voices.

### 5.1 Stable keys

`TOPICKEY` is the readable key:

    <NAMESPACE>|<CAN_NAME>

`REF_ID` is the stable content ID derived from:

    NAMESPACE + ENT_KIND + CAN_NAME

`LINE_ID` is derived from:

    REF_ID + LOCALE_ID + VOICE + KIND + ORDINAL

The implementation must publish the exact canonicalization and hash algorithm.
Row position, DBF record number, generated numeric ID, and display order are
not stable identity.

### 5.2 `SYSREFRUN.dbf` -- harvest/run binding

One row describes one candidate assembly.

| Field | Type | Meaning |
| --- | --- | --- |
| `RUN_ID` | C(48) | unique run identity |
| `REPO_SHA` | C(64) | source Git revision |
| `START_UTC` | C(32) | RFC 3339 UTC start |
| `END_UTC` | C(32) | RFC 3339 UTC completion |
| `COLLECTOR` | C(64) | collector identity/version |
| `COLL_HASH` | C(64) | collector executable or source hash |
| `POLICY_ID` | C(64) | assembly policy identity |
| `POL_HASH` | C(64) | assembly policy hash |
| `INPUT_HASH` | C(64) | canonical manifest hash over every input |
| `STATUS` | C(24) | `CANDIDATE`, `REVIEWED`, `BLOCKED`, `APPROVED` |
| `CREATED_BY` | C(64) | producing member/tool |
| `DETAIL` | M | input paths, hashes, counts, diagnostics |

### 5.3 `SYSREF.dbf` -- one reference identity

| Field | Type | Meaning |
| --- | --- | --- |
| `REF_ID` | C(64) | stable reference ID |
| `RUN_ID` | C(48) | parent candidate run |
| `NAMESPACE` | C(16) | `DOT`, `FOX`, `ED`, `DEV`, `PSHELL`, `SQL` |
| `ENT_KIND` | C(16) | `COMMAND`, `ALIAS`, `SUBCOMMAND`, `FUNCTION`, `TOPIC`, `FORM` |
| `CAN_NAME` | C(80) | canonical identity in the namespace |
| `TOPICKEY` | C(96) | namespace plus canonical identity |
| `VIS` | C(20) | public/developer/internal visibility |
| `IMPLEMENT` | L | reachable implementation exists |
| `SUPPORTED` | L | supported on this reference surface |
| `SUPPORT_ST` | C(32) | reviewed source support status |
| `MATURITY` | C(24) | maturity independent of support membership |
| `AUDIENCE` | C(24) | intended audience independent of support membership |
| `ACTIVE` | L | row participates in emission |
| `DISP_ORD` | N(10) | presentation order only |
| `SRC_AUTH` | C(32) | structural authority |
| `SRC_FILE` | C(180) | structural source evidence |
| `SRC_HASH` | C(64) | structural source hash |
| `REVIEW_ST` | C(24) | review/disposition state |
| `VER_AT` | C(32) | RFC 3339 UTC verification instant |

Required unique key: `RUN_ID + REF_ID`.

### 5.4 `SYSREFLINE.dbf` plus DTX -- repeated prose

| Field | Type | Meaning |
| --- | --- | --- |
| `LINE_ID` | C(64) | stable line identity |
| `RUN_ID` | C(48) | parent candidate run |
| `REF_ID` | C(64) | parent reference identity |
| `LOCALE_ID` | C(16) | BCP 47 content locale |
| `VOICE` | C(16) | `NATIVE`, `FOX_COMPAT`, `EDUCATION`, or governed value |
| `KIND` | C(32) | HELP `ArtifactKind` value |
| `ROLE` | C(32) | semantic role within the kind |
| `ORDINAL` | N(6) | stable ordering within the kind |
| `TEXT` | M | source or reviewed prose |
| `SRC_AUTH` | C(32) | contract/override authority |
| `SRC_FILE` | C(180) | source evidence |
| `SRC_HASH` | C(64) | exact source-fragment hash |
| `OVERRIDE` | L | approved voice override applied |
| `REVIEW_ST` | C(24) | review/disposition state |
| `ACTIVE` | L | row participates in emission |

Required unique key:
`RUN_ID + REF_ID + LOCALE_ID + VOICE + KIND + ORDINAL`.

The initial emitter consumes `SUMMARY` and `SYNTAX`. The schema retains the
closed HELP kinds already rendered upstream so later consumers do not require a
new database shape. A field is not added unless an identified consumer uses it.

### 5.5 `SYSREFALIAS.dbf` -- alias and routing edges

| Field | Type | Meaning |
| --- | --- | --- |
| `ALIAS_ID` | C(64) | stable alias edge ID |
| `RUN_ID` | C(48) | parent candidate run |
| `REF_ID` | C(64) | canonical target |
| `ALIAS` | C(80) | alternate spelling |
| `ALIAS_KND` | C(24) | registry, shortcut, compatibility, display |
| `DISP_STYL` | C(24) | direct, routed, rewritten, documentation-only |
| `TARGET_ID` | C(64) | resolved target identity when applicable |
| `SRC_AUTH` | C(32) | alias authority |
| `SRC_FILE` | C(180) | source evidence |
| `SRC_HASH` | C(64) | source hash |
| `ACTIVE` | L | active edge |

Required unique key: `RUN_ID + REF_ID + ALIAS + ALIAS_KND`.

An alternate spelling embedded only in a syntax string is not an alias edge.
The BUILD/BUILDVECTORS history proves why these must be modeled separately.

### 5.6 `REFVOICE.dbf` plus DTX -- reviewed human intent

This is the only independently curated input introduced by M3. It is small and
exception-oriented, not a duplicate of every source contract.

| Field | Type | Meaning |
| --- | --- | --- |
| `OVR_ID` | C(64) | stable override ID |
| `NAMESPACE` | C(16) | target namespace |
| `ENT_KIND` | C(16) | target entity kind |
| `CAN_NAME` | C(80) | target canonical identity |
| `LOCALE_ID` | C(16) | target locale |
| `VOICE` | C(16) | target voice |
| `KIND` | C(32) | field/kind being overridden |
| `ORDINAL` | N(6) | target ordinal |
| `TEXT` | M | reviewed replacement text |
| `RATIONALE` | M | why source wording is unsuitable for this namespace |
| `OWNER` | C(64) | proposal owner |
| `RULING_ID` | C(64) | owner ruling or approval evidence |
| `REVIEW_ST` | C(24) | `PROPOSED`, `APPROVED`, `REJECTED`, `SUPERSEDED` |
| `SRC_HASH` | C(64) | source text hash the override reviewed |
| `ACTIVE` | L | active override |
| `VER_AT` | C(32) | verification instant |

An override whose `SRC_HASH` no longer matches is stale and blocks promotion.
The author may propose an override but may not self-approve it.

### 5.7 `DOTREF.dbf` plus DTX -- generated projection

This table is the user's inspectable database of assembled DOT reference rows.
It is generated from the normalized tables and is never edited directly.

| Field | Type | Meaning |
| --- | --- | --- |
| `REF_ID` | C(64) | source identity |
| `RUN_ID` | C(48) | assembly run |
| `NAME` | C(80) | emitted `dotref::Item.name` |
| `SYNTAX` | M | deterministically folded syntax forms |
| `SUMMARY` | M | selected native summary |
| `SUPPORTED` | L | reviewed support state |
| `SRC_HASH` | C(64) | hash over all contributing source rows |
| `REVIEW_ST` | C(24) | final row disposition |
| `ACTIVE` | L | included in header emission |

The four C++ `Item` fields are a projection, not the normalized storage model.

### 5.8 `REFSUPPORT.dbf` -- reviewed support vocabulary

`REFSUPPORT` is the closed, owner-approved mapping from a source contract status
to `SUPPORTED`, maturity, and audience. The emitter fails closed when an active
surface resolves to a status absent from this table. Helper, shim, supplemental,
stub, deprecated, reserved, review-needed, experimental, sample, and rejected
states map false. The approved usable-surface states map true. This prevents a
new source status from silently inheriting support merely because it is active
or implemented.

## 6. Join and selection rules

1. All structural and prose inputs must name the same `RUN_ID` or be listed in
   one immutable input manifest. A mixed-run join fails.
2. Canonical identity is resolved before prose. Unresolved identities fail;
   prose never mints a command.
3. Entity kind controls its authority. A subcommand resolves through
   `SYSSUBCMD`; a function resolves through `SYSFUNC`; a namespace-owned topic
   resolves through that namespace's declared authority.
4. Each usage/syntax form is stored as its own ordered `SYSREFLINE` row. The
   projection joins forms with ` | ` only when producing the current four-field
   C++ shape.
5. Source summary is the default native summary. An approved, non-stale
   `REFVOICE` row may replace only its named namespace/locale/kind/ordinal.
6. Structural fields cannot be overridden by `REFVOICE`.
7. Aliases are relations. They are not inferred from punctuation inside syntax
   prose.
8. `SUPPORTED` follows the reviewed support policy; `IMPLEMENT` follows
   reachability. Neither is inferred from the other.
9. Every exclusion produces a disposition row. Absence is not a policy.
10. A duplicate stable key, conflicting active override, missing required
    summary/syntax, stale override, or unresolved source conflict blocks output.
11. A source block explicitly marked `supplemental`, `implementation-shim`,
    `implementation-helper`, or `backend-helper` is supporting evidence, not a
    second command-surface contract. It receives a nonblocking disposition and
    cannot displace the command contract.
12. A non-runtime declaration such as an unregistered `experimental` or `stub`
    contract receives an explicit exclusion disposition. It cannot mint a
    structural identity. A supported or otherwise unexplained contract with no
    structural identity remains blocking.
13. An active `SYSCMD` identity without a direct usage block may resolve to one
    unique active `SYSSUBCMD` row by exact or compact identity. The generated
    subcommand row supplies its source-derived summary, syntax, and support
    status; ambiguous compact matches block.
14. A syntax command may inherit one unique parent contract only through an
    active `SYSARGS` keyword edge. A routed alias may inherit one unique sibling
    contract only when both handler identity and active `SYSARGS` syntax
    evidence agree. Shared handler identity alone never proves an alias.

## 7. Candidate artifacts

The first implementation writes only beneath a unique run directory:

    docs/maintenance/lanes/full_stack_documentation/runs/<RUN_ID>/dotref_m3/
      candidate/dbf/SYSREFRUN.dbf
      candidate/dbf/SYSREF.dbf
      candidate/dbf/SYSREFLINE.dbf
      candidate/dbf/SYSREFLINE.dtx
      candidate/dbf/SYSREFALIAS.dbf
      candidate/dbf/DOTREF.dbf
      candidate/dbf/DOTREF.dtx
      candidate/include/dotref_catalog.generated.inc
      reports/input_manifest.json
      reports/authority_join_report.json
      reports/current_header_migration.csv
      reports/field_diff.csv
      reports/gate_results.json

`REFVOICE.dbf` is not generated into that directory as an authority. The run
copies its hash and selected rows into the manifest while reading the reviewed
canonical override source.

No default command writes to `include/` or `dottalkpp/data/metadata/`. An
explicit `--apply` mode, if later approved, must require the reviewed manifest
hash and refuse a changed source tree.

## 8. Header shape

Keep `include/dotref.hpp` as the stable API wrapper containing:

- `dotref::Item`;
- `catalog()`, `find()`, `search()`, and alias APIs;
- inclusion of generated catalog data.

Move only the generated row initializer into a mechanically owned include such
as:

    include/generated/dotref_catalog.generated.inc

The generator must emit no wall-clock timestamp into the C++ artifact. Identical
inputs and policy produce byte-identical output.

The first pilot may emit a complete candidate `dotref.hpp` if separating the
wrapper would create unnecessary review noise. The acceptance comparison still
operates on parsed rows and fields, not line numbers or raw row counts.

## 9. Migration of the current header

The current header is valuable migration evidence because it contains reviewed
native wording and deliberate exceptions. Migration is one bounded pass:

1. parse every current row;
2. join it to normalized identity and harvested source prose;
3. compare `name`, `syntax`, `summary`, and `supported` separately;
4. classify every difference;
5. create proposed `REFVOICE` rows only for deliberate namespace wording;
6. leave stale, ambiguous, or structurally conflicting rows blocked;
7. require zero unclassified `CARRIED_FROM_HEADER` rows before promotion.

The dated baseline found 67 carried rows in the current prototype. That number
is not an acceptance floor or ceiling. The implementation remeasures and
classifies the member set from its own immutable input manifest.

## 10. Generator interface

The report-only implementation should expose an interface equivalent to:

```text
generate_ref_catalog_v1
  --root <repo>
  --run-id <id>
  --harvest-manifest <path>
  --voice-catalog <path>
  --namespace DOT
  --out <unique-run-dir>
  --report-only
```

Required behavior:

- `--report-only` is the default;
- existing output directory is refused unless an explicit resume manifest
  matches exactly;
- inputs, policies, executable/source, and outputs are SHA-256 bound;
- incomplete memo reads fail rather than becoming blank text;
- the generator reports successful rows, blocked rows, and exclusions
  separately;
- no success count includes attempted or blocked rows;
- output order is stable and declared;
- no code path reads current `dotref.hpp` after migration mode is disabled.

Do not extend `dotref_autogen.py` into a second harvester. Reuse or extract the
metacollect output reader and the existing C++ row parser/emitter where useful.

## 11. Acceptance gates

### G0 -- immutable input package

- one repository revision;
- one metacollect identity/version;
- all input paths and SHA-256 values recorded;
- memo containers included in hashes and native readback;
- no mixed-run tables.

### G1 -- schema and key integrity

- schemas match declared fields and widths;
- stable keys are unique;
- every child row resolves to a parent;
- no orphan alias, line, override, or projection row;
- locale identifiers resolve through the locale spine.

### G2 -- authority resolution

- every active row resolves through the correct authority for its entity kind;
- zero command/function/subcommand conflations;
- zero structural facts created by prose;
- every exclusion has a disposition.

`refcheck_v1.py --selftest` must first prove the guard catches a planted phantom,
then the real candidate must pass.

### G3 -- complete field refresh

For every current and candidate DOT identity compare the member set and each
claim independently:

- identity;
- aliases and routing style;
- syntax forms;
- summary;
- supported;
- implemented;
- namespace voice.

A zero missing-name result does not satisfy this gate.

### G4 -- no silent legacy carry

- zero promotable `CARRIED_FROM_HEADER` rows;
- every header-only fact is accepted as a reviewed override, excluded, or
  blocked;
- stale override source hashes fail.

### G5 -- native/compatibility voice preservation

Select commands represented in both DOT and FOX. Prove that shared structural
facts remain shared while approved native and compatibility wording remains
distinct. A generator that flattens both voices fails.

### G6 -- determinism and no-op

- two clean runs from identical inputs produce byte-identical DBF logical rows,
  DTX memo text, manifests, and generated header data;
- deterministic comparison ignores physical memo allocation details only after
  native logical-content readback matches;
- re-running against an already current target produces no content mutation.

### G7 -- round trip

- parse generated header rows back into the normalized four-field DOTREF view;
- compare keys and every field to `DOTREF.dbf`;
- no truncation, escape loss, newline loss, or encoding drift;
- long and multi-line summaries are planted positive fixtures.

### G8 -- compile and runtime parity

After separate apply authorization:

- isolated metacollect build passes;
- engine rebuild passes;
- DOTHELP/browser resolver/CMDHELP consume the generated catalog;
- topic member sets are compared, not only counts;
- syntax, summary, support, and alias differences equal the approved field diff;
- `CMDHELPCHK`, `refcheck_v1.py`, and `normcheck_v1.py` pass;
- a planted stale-syntax fixture fails before the real candidate passes.

### G9 -- promotion and rollback

- candidate review records the exact manifest hash;
- promotion refuses a different source revision or input hash;
- backup and rollback paths are explicit and read back;
- live `dotref.hpp`, HELP, metadata, manuals, and website remain untouched until
  their individually authorized stage;
- the development closeout stops before website staging or publication.

## 12. Implementation packages

### M3A -- specification

This document. Owner review decides the schema and rules; authors do not
self-approve.

### M3B -- report-only catalog assembler

Implement schema creation, same-run joins, manifests, and reports. Produce no
live DBF or header mutation.

### M3C -- migration classifier

Import the current parsed header as evidence, classify every field difference,
and prepare proposed `REFVOICE` rows. No override becomes approved implicitly.

### M3D -- DOT pilot emitter

Emit candidate normalized tables, `DOTREF.dbf`, and generated C++ data for the
DOT namespace. Run G0-G7 without applying.

### M3E -- reviewed apply and runtime proof

Only after explicit authorization, promote the approved DOT candidate, rebuild,
and run G8-G9.

### M3F -- family emitter

Parameterize the proven emitter for FOX and the remaining namespaces. Preserve
each namespace's declared authority and voice; do not assume command semantics
for ED, PSHELL, SQL, or reserved DEV rows.

## 13. Recorded M3B decisions

Owner authorization recorded the following rulings before implementation:

1. Use generic normalized `SYSREF*` tables and a generated `DOTREF` projection.
2. `REFVOICE` is the only new independently curated authority.
3. Retain the compiled header as the runtime/bootstrap surface.
4. Keep `IMPLEMENTED` and `SUPPORTED` as independent claims.
5. Enforce same-run hash binding and zero silent header carry as hard gates.
6. Use review-friendly `REFVOICE_v1.csv` as the canonical text projection;
   later authorized stages may compile reviewed rows to DBF/DTX.

M3B implements these decisions in:

- `dottalkpp/data/schemas/metadata/sysref_catalog.dtschema`;
- `dottalkpp/data/scripts/metadata/REFVOICE_v1.csv`;
- `tools/fullstack_docs/build_sysref_harvest_manifest_v1.py`;
- `tools/fullstack_docs/generate_sysref_candidate_v1.py`;
- `tools/fullstack_docs/tests/test_build_sysref_harvest_manifest_v1.py`;
- `tools/fullstack_docs/tests/test_generate_sysref_candidate_v1.py`.

The manifest builder binds explicit source files and collector members without
guessing a latest artifact. The assembler requires that dedicated immutable
authority manifest, validates the
declared SHA-256 of every input, refuses mixed harvest runs and paths outside
the repository, writes only CSV/JSON review artifacts below a new output
directory, and reports blocked identities separately from assembled rows. It
has no apply mode and never reads `include/dotref.hpp`.

## 14. Verification and housekeeping

Verified 2026-10-13 for M3A and M3B:

- document is ASCII-only and contains no replacement characters;
- every repository path cited as current source/prior art exists;
- `include/dotref.hpp`, `SYSCMD.dbf`, `SYSARGS.dbf`, and `SRCUSAGE.dbf`
  retained their pre-specification SHA-256 values;
- no DBF, DTX, CDX, CNX, LMDB, header, HELP, live metadata, manual, website,
  staging, commit, or remote state was changed by M3B;
- nineteen focused unit tests prove deterministic report output, independent
  implementation/support claims, hash refusal, mixed-run refusal, stale
  override blocking, approved override provenance, explicit missing-contract
  disposition, helper-contract classification, unresolved experimental
  exclusion, real duplicate refusal, SYSSUBCMD compact resolution, syntax-arm
  resolution, guarded routed-alias resolution, explicit manifest binding,
  path-containment enforcement, and existing-output refusal;
- M3B creates only the specification, schema contract, empty reviewed-override
  template, report-only assembler, and focused tests listed above.

Pre-existing shared-tree state left untouched includes the modified
`include/dotref.hpp` and an ignored generated SRCUSAGE data artifact.
Their presence is evidence about the shared workspace, not ownership by this
run. No handoff is added because this document itself is the bounded design and
contains the next implementation packages.

### M3C implementation checkpoint -- DOCFLUSH-20261013-002

M3C is now implemented as two report-only passes:

- `classify_dotref_migration_v1.py` compares the parsed compiled header with
  the M3B command projection field by field;
- `build_dotref_migration_closure_v1.py` resolves the complete current DOT
  member set through source authority and emits proposed, inactive migration
  voice rows.

Measured on the hash-bound 2026-10-13 run, the closure resolves all 268 current
members: 231 canonical commands, 23 display aliases, 12 subcommands, and two
implemented extension functions. Zero member is carried merely because it was
present in the header, and zero member is unresolved. The 536 syntax/summary
voice rows remain `PROPOSED` and inactive; this checkpoint does not approve
them. The current `supported` differences also remain a separate reviewed
policy decision, so M3D/M3E promotion is not implied.

Twenty-six focused M3B/M3C/manifest tests pass together. `refcheck_v1.py`
passes its planted-phantom self-test and the live reference set, while
`normcheck_v1.py` reports no fail or warn findings. No live header, DBF/DTX,
HELP/META, manual, website, staging tree, Git index, commit, or remote state was
mutated by M3C.

### M3D report-only checkpoint -- DOCFLUSH-20261013-002

The owner approved the exact M3C review gate at SHA-256
`DEEC42244DC5FC2A193F8E53F5348750DBAB86234458F5DC4A06C26FC2C9035B`
for report-only M3D emission. The separate approval record preserves that
authorization without changing the reviewed gate bytes.

M3D now emits seven isolated candidate tables: SYSREFRUN, SYSREF, SYSREFLINE,
SYSREFALIAS, REFVOICE, REFSUPPORT, and DOTREF. The candidate contains 268
reference identities, 23 explicit alias edges, 536 owner-approved initial
voice rows, 2,658 normalized prose rows, and 23 closed support-policy rows.
The generated C++ projection contains 268 rows.

Two independent emissions and native DotTalk++ CREATE X64/IMPORT loads passed
G0-G7. Twelve logical artifacts and twelve physical DBF/DTX files are
byte-identical between the runs. Native readback compared all 268 DOTREF rows,
including both memo fields, with the generated CSV projection. Native memo
verification passed five memo-bearing tables per run with zero bad IDs,
missing objects, or orphan objects. The 22 differences from the current header
are all reviewed `SUPPORTED` results; identity, order, syntax, and summary have
zero drift.

Verification authority:

- `dotref_m3/m3d_pilot_v1/verification_v1/m3d_verification_summary.json`
  SHA-256 `69F5E037C28418AF21CFF6E0DE1525BB8F1D7EA07175F766AB0AD4400B7F7034`;
- candidate DOTREF DBF SHA-256
  `75D824FF5A7E7B0ECD5E0EFED5AB51F1811A2710C1E548C0249D5838055FA6C3`;
- candidate DOTREF DTX SHA-256
  `2EDC3B4AAEC467DD42EB80063E2FC24F985140970D733FA86179850357905745`;
- generated row include SHA-256
  `2184A0085DA4D617863EC01373E16191B3D7FE86E466D4BDC756A077CAE2DCD3`.

An attempted re-emission into the existing `run_a` directory was refused with
exit 2 and left its candidate hash unchanged. M3D has no apply mode. The live
header, HELP/META stores, manuals, website, publication staging, Git index,
commits, and remotes remain outside this package. At that checkpoint M3E still
required separate exact authorization; the next checkpoint records it.

### M3E apply and runtime checkpoint -- DOCFLUSH-20261013-002

The owner authorized M3E after the boundary was stated explicitly. The durable
authorization record has SHA-256
`AFA2FA0A7713EEB7184180A0422098F4ECE233B91B68C9903543D947EC075164`.
The guarded apply tool rechecked the approved gate, verification summary,
generated include, live pre-header, repository revision, branch, 268-member
order, and exactly 22 approved support-only changes before writing.

The live `include/dotref.hpp` row region was promoted atomically from SHA-256
`F1C30234AF8765BF5732BEF926928F9AF583B22AC9AC7F14DBA3DDD895AD33E5`
to
`0FAB5B3AAED1B6C0AA0AAE81C1F0C6406CFFD597A2DF6555824DD9DBB9D91243`.
The byte-preserved backup read back at the pre-header hash. Prefix and suffix
bytes outside the generated row region were preserved, including concurrent
COPY/DDICT work.

G8 and G9 pass. Release builds produced `metacollect.exe` at SHA-256
`3092230A5F13D301970C03583AE5F3E7BA415B75EC3269C84A6437BAD7BB1F6B`
and `dottalkpp.exe` at SHA-256
`5C0E119D5A2BE2EFC3C5B0E92EE702FB1D336CD2E2CA2D7044F637BC11CD4B01`.
The rebuilt runtime listed all 268 DOTHELP members in exact order, reflected
representative AUTODBF, COPY, and DDICT rows, and passed CMDHELPCHK REF. Thirty-
six focused tests, refcheck self-test/live, and normcheck pass. The isolated
rollback drill restored the exact pre-header hash while leaving the live header
at the promoted hash.

Three router behaviors are recorded as advisories, not concealed as missing
catalog members:

- `DOTHELP HELP` selects DOTHELP usage; `HELP /DOT HELP` resolves the member;
- `DOTHELP VAR` is intercepted by the broad second-token VAR router;
  `HELP /DOT VAR` resolves the member;
- `HELP /DOT PREDICATES` is diverted by `predOnly` precedence, while the full
  DOTHELP list still contains the member.

The verification summary has SHA-256
`4A821FB53E3DD7429C8847440C5EB29323E7A6150B6E593B91FFDF2A25A9FAAE`
and status `M3E_G8_G9_PASS`. The promotion manifest has SHA-256
`3A065D2FAE4AE2B892E2BB651535FD8F6DFF75D896CF067ACC1E8AC6019554B7`.
M3E did not mutate HELP/META, manuals, website, publication staging, the Git
index, commits, or remotes. Those remain later, separately governed steps.

### Post-M3E router-parity hardening -- CODEX-20261014-DOTHELP-ROUTER-001

The owner authorized correction of the three advisories above. They remain in
the M3E checkpoint as the accurate discovery record; this checkpoint closes
them rather than rewriting that evidence.

- `DOTHELP HELP` no longer treats HELP as a usage synonym. `USAGE` and `?`
  retain the usage path, while HELP resolves the catalog member.
- The shell VAR pre-router now requires a SET, SHOW, or CLEAR command head
  before it claims a VAR/VAR! second token. It no longer intercepts arbitrary
  commands such as `DOTHELP VAR`.
- The implicit bare PREDICATES shortcut now fires only when no explicit HELP
  namespace is present. `HELP PREDICATES` retains the tutorial, while
  `HELP /DOT PREDICATES` resolves the DOTREF member.

The Release runtime at SHA-256
`BF70D96B640D3FFF2106096151A990CF5F3F8B91C7314BAB39D9D756FE82B8D4`
resolves all 268 approved members, in order, through both `DOTHELP <member>`
and `HELP /DOT <member>`. The verifier is independently bound to approved
candidate SHA-256
`70E3AE34B43105E3EB0818731107E9DCEC5E7189B4CB9B9240C3C3BA5F38AF73`;
its changed-candidate negative control passes. The focused C++ parser test,
refcheck self-test/live, normcheck, and compatibility probe all pass. The
verification summary SHA-256 is
`AED1F6CCA5F5A0CDDB1AAE5E5634013A209D5E27B1FF245E57CAB1CB469F97B2`.

No DOTREF data row, HELP/META store, manual, website, publication staging,
Git index, commit, push, or remote was changed by this correction.

