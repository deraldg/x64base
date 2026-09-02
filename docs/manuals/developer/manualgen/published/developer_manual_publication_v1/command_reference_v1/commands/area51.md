<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# AREA51

- Catalog/topic: `DOT` / `AREA51`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Report the current work-area slot and its cursor/order state WITHOUT invoking the full AREA command and WITHOUT triggering relation refresh.

## Status

- implemented=yes; supported=yes

## Syntax

- AREA51

## Usage

- AREA51

## Note

- AREA51 is a developer/debug status probe, not a member of the AREA family, and `status: developer` above says so. It read `supported` until 2026-08-30 while THIS PARAGRAPH already called it a developer probe -- the contract's own prose and its own status field disagreeing, which is the only reason the field is worth correcting: nothing downstream reads it.
- The "policy exclusions (dev/subcmd)" line in the normalization gate is computed as registered-minus-catalogued-minus-aliases and never looks at status at all, so this changes no gate and no behaviour. It changes what the file claims about itself, which is the part that was wrong.
- THE NAME IS TWO JOKES AND THE SECOND ONE IS THE OWNER'S. AREA is a core xBase concept and this house has a crowded AREA namespace -- AREA, DBAREA,
- DBAREAS, WA, WAMREPORT -- so one more was funny. It is ALSO, and primarily, the owner's nod to Area 51 of science fiction: a place you go to look at things quietly without disturbing them, which is exactly what this command does. Recorded 2026-08-30 because the sentence here previously read "it is deliberately NOT 'AREA 51'" and was misread as denying the reference. It never meant that. It means DO NOT PARSE THIS AS THE `AREA` COMMAND WITH
- ARGUMENT 51 -- the token is one word, and the command takes no arguments.
- A comment that needs its author present to be read correctly is a comment that needs rewriting.
- Unlike AREA it does NOT call relations_api::refresh_if_enabled(), which is the entire point: it observes engine state without perturbing it. Use it when a relation refresh would itself change what you are trying to look at.
- Reports "(no file open)" rather than failing when the current area is empty.
- Order/tag reporting is best-effort; a throwing order-state query is swallowed and the remaining lines still print.

## Related

- AREA
- DBAREA
- DBAREAS
- WAMREPORT
- STATUS
- GPS

## Provenance

- Topic key: `DOT|AREA51`
- Included HELP rows: `37`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
