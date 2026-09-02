<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CLOSE

- Catalog/topic: `DOT` / `CLOSE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Close the current work area, honoring dirty table-buffer prompts, clearing memo/order/table slot state, and clearing affected relation state.

## Status

- implemented=yes; supported=yes

## Syntax

- CLOSE USAGE
- CLOSE
- CLOSE ALL
- CLOSE [ALL|&lt;area&gt;|&lt;alias&gt;]

## Usage

- CLOSE USAGE
- CLOSE
- CLOSE ALL

## Note

- CLOSE with no arguments closes the current work area.
- CLOSE ALL clears all relations and closes every open work area.
- CLOSE prompts or cancels through dirty table-buffer protection when needed.
- CLOSE runs memo sidecar lifecycle hooks before clearing area identity.
- CLOSE clears active order/index state.
- CLOSE resets table buffering state for the slot to off, clean, and fresh.
- CLOSE is a session/area mutation command; it does not directly mutate table records.

## Related

- USE
- WORKSPACE
- TABLE
- COMMIT
- REL

## Provenance

- Topic key: `DOT|CLOSE`
- Included HELP rows: `22`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
