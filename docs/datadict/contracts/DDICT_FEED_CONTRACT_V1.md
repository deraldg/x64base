# Native DDICT feed contract v1

Owner: member.derald. Implementation authorized 2026-10-09. Candidate-only.

## Producer and boundaries

`ddict_export <catalog-directory>` uses the shared native catalog reader and
emits deterministic UTF-8 JSON to stdout. Exit 0 means no native diagnostics,
2 means review diagnostics, and 1 means invocation/I/O failure. It never writes
DBFs, DTX, CDX or LMDB. No classic DBF parser is substituted for x64base.

`tools/datadict/catalog/ddict_feed.py build` wraps that export in a new directory.
The catalog, binary and producer hashes are checked before/after export.
Changed input aborts the run. Existing output directories and live data output
destinations are refused. Direct catalog file members, bytes, times and SHA-256
are recorded; nested historical copies are outside this snapshot's scope.

Schemas: `docs/datadict/schemas/ddict_native_v1.schema.json` and
`docs/datadict/schemas/ddict_feed_v1.schema.json`. Runtime checks additionally
validate file membership/hashes, row identities, memo states and crosswalk
equality. JSON Schema alone cannot prove source freshness or runtime behavior.

Every native diagnostic has a deterministic row in
`DDICT_DIAGNOSTIC_DISPOSITION.json`. Each row retains the original message,
classifies its failure family and repair posture, and remains `BLOCKS_READY`.
Unknown diagnostic text fails feed construction rather than falling into an
unreviewed bucket. The disposition is triage, never permission to mutate data.

Two validation postures are explicit. `FULLY_VERIFIED` binds artifacts to the
catalog members, producers and exporter binary and is mandatory for full-stack
preflight. `SNAPSHOT_ONLY` validates the complete artifact set and its internal
semantics when a clean clone has no ignored catalog directory; the Portal labels
that posture and keeps acceptance `CANDIDATE`. If a development catalog exists,
the Portal requires full proof and never falls back around stale source.

## Names, identities and evidence

Retain physical filename, independent logical table name, exact field name,
type and width. No ten-character projection or truncation is permitted.
Each row retains family, physical table and original ID. Its cross-layer key
is `DDICT:<percent-encoded-family>:<percent-encoded-table>:<percent-encoded-id>`.

Only explicit COMMAND, FUNCTION or owned SUBCOMMAND dictionary rows produce
reference-key candidates. COMMAND_SURFACE is not a command identity. Reference
normalization uppercases and collapses whitespace without removing canonical
spaces. Ambiguous multiple mappings retain both rows and force REVIEW. These
are documentary declarations, not proof that a command is executable.

Argument identities include owner kind, canonical owner, argument kind and
name. The metacollect v2 projection is `ARG:COMMAND:<owner>:<kind>:<name>`.
Live legacy IDs are not renamed. A future load must carry an old/new ID map,
owner validation, duplicate checks, physical-width checks and rollback proof.
The candidate physical contract is
`docs/datadict/schemas/sysargs_catalog_candidate_v2.dtschema`; it is not a loader
or an assertion that the live table has that schema.

Every physical memo field adds `_DD_MEMO_STATE:<field>` with NULL, RESOLVED,
INVALID or UNAVAILABLE. An empty resolved string differs from a null link.
Missing payloads and invalid space-filled M8 cells keep their diagnostics.
Do not infer memo state by searching text for brackets or error words.
Relationship endpoints retain the shared reader's OBJECT/ATTRIBUTE typing.

## Consumers

- Portal: `feed.dottalk.ddict`, trigger `ddict`, current snapshot pointer,
  reader HTML and maintained recipes. Native diagnostics remain visible.
- Manualgen: optional `DDICT_MANIFEST.json` companion in the selected harvest;
  no automatic migration of the existing 14-file HELP/META contract.
- Assembled manual: maintained recipe part plus hash-validated candidate
  dictionary appendix selected by `current_ddict_feed.json`.
- Website: dedicated internal candidate packet and proposed routes registered
  separately from existing site pages. No accepted-publication pointer moves.

A selected corrupt/stale companion fails validation. A valid snapshot with
native diagnostics or ambiguous reference keys remains REVIEW. A legacy harvest
without a companion is explicitly NOT_SELECTED, never DDICT-validated.
The current pointer binds its workspace and manifest SHA-256; consumers must
check both. Rebuilding a producer invalidates its earlier snapshot binding.

## Acceptance

Full-stack preflight now checks the selected DDICT feed. Missing/stale input
fails, and REVIEW data blocks a clean push verdict. Candidate readers remain
available so the findings can be inspected without changing the live store.

READY means the feed's checks passed; it is still CANDIDATE. Publication needs
reviewed public scope, resolved diagnostics, accepted manual parts, site baseline
checks and separate deployment evidence. Internal source paths and evidence
must not be automatically made public. All generated artifacts carry this
boundary. Source-manual integration is not runtime MAN* catalog regeneration.
