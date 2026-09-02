<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLITE

- Catalog/topic: `DOT` / `SQLITE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Thin SQLite command wrapper for status, connection management, Bible seed helpers, metadata inspection, SELECT queries, and EXEC statements.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLITE
- SQLITE USAGE
- SQLITE STATUS
- SQLITE CWD
- SQLITE PWD
- SQLITE VERSION
- SQLITE OPEN &lt;file&gt;
- SQLITE OPEN :memory:
- SQLITE DB &lt;file&gt;
- SQLITE DB :memory:
- SQLITE BIBLE
- SQLITE BIBLECHECK
- SQLITE BIBLECHK
- SQLITE BOOKS
- SQLITE VERSE &lt;ref&gt;
- SQLITE SEARCH &lt;phrase&gt;
- SQLITE LIST &lt;table&gt;
- SQLITE LIST &lt;table&gt; &lt;limit&gt;
- SQLITE COLUMNS &lt;table&gt;
- SQLITE CLOSE
- SQLITE TABLES
- SQLITE SCHEMA
- SQLITE SCHEMA &lt;table-or-view&gt;
- SQLITE EXEC &lt;sql&gt;
- SQLITE SELECT &lt;sql&gt;
- SQLITE &lt;subcommand&gt; ...

## Usage

- SQLITE
- SQLITE USAGE
- SQLITE STATUS
- SQLITE CWD
- SQLITE PWD
- SQLITE VERSION
- SQLITE OPEN &lt;file&gt;
- SQLITE OPEN :memory:
- SQLITE DB &lt;file&gt;
- SQLITE DB :memory:
- SQLITE BIBLE
- SQLITE BIBLECHECK
- SQLITE BIBLECHK
- SQLITE BOOKS
- SQLITE VERSE &lt;ref&gt;
- SQLITE SEARCH &lt;phrase&gt;
- SQLITE LIST &lt;table&gt;
- SQLITE LIST &lt;table&gt; &lt;limit&gt;
- SQLITE COLUMNS &lt;table&gt;
- SQLITE CLOSE
- SQLITE TABLES
- SQLITE SCHEMA
- SQLITE SCHEMA &lt;table-or-view&gt;
- SQLITE EXEC &lt;sql&gt;
- SQLITE SELECT &lt;sql&gt;

## Note

- SQLITE with no arguments reports connection status and brief usage.
- SQLITE USAGE, HELP, and question mark print detailed usage.
- OPEN and DB connect to a SQLite database and create it if needed.
- BIBLE and BIBLECHECK open/check the canonical Bible seed database when found.
- EXEC runs non-SELECT SQL and may mutate the external SQLite database.
- SELECT prints query rows and caps output for CLI responsiveness.
- SQLITE is independent of DBF open/order state.

## Related

- SQLVER
- IMPORT
- EXPORT

## Provenance

- Topic key: `DOT|SQLITE`
- Included HELP rows: `71`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
