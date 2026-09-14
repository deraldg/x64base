<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CODASYL

- Catalog/topic: `DOT` / `CODASYL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Provide a thin CODASYL teaching veneer over already-open DotTalk++ work areas, simulating owner/member set traversal without a second storage engine.

## Status

- implemented=yes; supported=yes

## Syntax

- CODASYL [USAGE|HELP]
- CODASYL USAGE
- CODASYL HELP
- CODASYL MODE ON
- CODASYL MODE OFF
- CODASYL LOAD &lt;world&gt;
- CODASYL SETS
- CODASYL SHOW SET &lt;name&gt;
- CODASYL FIND OWNER &lt;set&gt; &lt;value&gt;
- CODASYL FIND OWNER &lt;owner_alias&gt; &lt;value&gt;
- CODASYL GET FIRST [&lt;set or member_alias&gt;]
- CODASYL GET NEXT  [&lt;set or member_alias&gt;]
- CODASYL WALK      [&lt;set or member_alias&gt;]
- CODASYL STATUS

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

## Argument

- NOTE
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- CODASYL with no arguments shows usage.
- This is a teaching adapter and does not create physical CODASYL storage.
- It uses already-open work areas and named set definitions.
- LOAD installs a predefined set map for a named lesson world.
- FIND OWNER captures the current owner and builds a member snapshot.
- GET FIRST and GET NEXT move through the simulated member ring.
- WALK prints a simulated owner/member ring and preserves the member-area cursor best-effort.
- STATUS reports CODASYL teaching state.

## Related

- WORKSPACE
- REL
- BROWSE
- USE

## Provenance

- Topic key: `DOT|CODASYL`
- Included HELP rows: `50`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
