<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CODASYL

- Catalog/topic: `DOT` / `CODASYL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Display CODASYL/network-database educational/demo material for historical database context.

- Provide a thin CODASYL teaching veneer over already-open DotTalk++ work areas, simulating owner/member set traversal without a second storage engine.

## Status

- implemented=yes; supported=yes

## Syntax

- CODASYL USAGE
- CODASYL HELP
- CODASYL MODE ON
- CODASYL MODE OFF
- CODASYL LOAD &lt;world&gt;
- CODASYL SETS
- CODASYL SHOW SET &lt;name&gt;
- CODASYL FIND OWNER &lt;set&gt; &lt;value&gt;
- CODASYL FIND OWNER &lt;owner_alias&gt; &lt;value&gt;
- CODASYL GET FIRST
- CODASYL GET FIRST &lt;set&gt;
- CODASYL GET FIRST &lt;member_alias&gt;
- CODASYL GET NEXT
- CODASYL GET NEXT &lt;set&gt;
- CODASYL GET NEXT &lt;member_alias&gt;
- CODASYL WALK
- CODASYL WALK &lt;set&gt;
- CODASYL WALK &lt;member_alias&gt;
- CODASYL [USAGE|HELP]

## Usage

- CODASYL USAGE
- CODASYL HELP
- CODASYL MODE ON
- CODASYL MODE OFF
- CODASYL LOAD &lt;world&gt;
- CODASYL SETS
- CODASYL SHOW SET &lt;name&gt;
- CODASYL FIND OWNER &lt;set&gt; &lt;value&gt;
- CODASYL FIND OWNER &lt;owner_alias&gt; &lt;value&gt;
- CODASYL GET FIRST
- CODASYL GET FIRST &lt;set&gt;
- CODASYL GET FIRST &lt;member_alias&gt;
- CODASYL GET NEXT
- CODASYL GET NEXT &lt;set&gt;
- CODASYL GET NEXT &lt;member_alias&gt;
- CODASYL WALK
- CODASYL WALK &lt;set&gt;
- CODASYL WALK &lt;member_alias&gt;
- CODASYL STATUS

## Note

- CODASYL with no arguments shows usage.
- This is a teaching adapter and does not create physical CODASYL storage.
- It uses already-open work areas and named set definitions.
- LOAD installs a predefined set map for a named lesson world.
- FIND OWNER captures the current owner and builds a member snapshot.
- GET FIRST and GET NEXT move through the simulated member ring.
- WALK prints a simulated owner/member ring and preserves the member-area cursor best-effort.
- STATUS reports CODASYL teaching state.

## Provenance

- Topic key: `DOT|CODASYL`
- Included HELP rows: `49`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
