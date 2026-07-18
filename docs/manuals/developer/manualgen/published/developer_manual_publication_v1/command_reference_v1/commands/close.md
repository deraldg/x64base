<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CLOSE

- Catalog/topic: `DOT` / `CLOSE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Close the current table, a selected area, or all open work areas.

- Close the current work area, honoring dirty table-buffer prompts, clearing memo/order/table slot state, and clearing affected relation state.

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
- CLOSE ALL currently clears all relations before closing the current area.
- CLOSE prompts or cancels through dirty table-buffer protection when needed.
- CLOSE runs memo sidecar lifecycle hooks before clearing area identity.
- CLOSE clears active order/index state.
- CLOSE resets table buffering state for the slot to off, clean, and fresh.
- CLOSE is a session/area mutation command; it does not directly mutate table records.
- risk:
- closes_area: yes
- clears_order_state: yes
- closes_memo_backend: yes
- resets_table_buffer_state: yes
- clears_relations_for_table: yes
- clears_all_relations: CLOSE ALL
- dirty_prompt_gate: yes
- mutates_table_data: no

## Related

- USE
- WORKSPACE
- TABLE
- COMMIT
- REL
- namespace fs = std::filesystem;
- Provided by the interactive shell.
- extern "C" xbase::XBaseEngine* shell_engine(void);
- namespace {
- static int area_index_from_ref(xbase::DbArea&amp; areaRef) {
- xbase::XBaseEngine* eng = nullptr;
- try { eng = shell_engine(); } catch (...) { eng = nullptr; }
- if (!eng) return -1;
- for (int i = 0; i &lt; xbase::MAX_AREA; ++i) {
- try {

## Provenance

- Topic key: `DOT|CLOSE`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
