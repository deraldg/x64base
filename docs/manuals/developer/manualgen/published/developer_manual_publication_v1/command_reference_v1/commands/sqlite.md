<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLITE

- Catalog/topic: `DOT` / `SQLITE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

SQLite integration.<br><br>        Examples:<br>            SQLITE DB data\sql_regression.sqlite<br>            SQLITE EXEC CREATE TABLE t(x INT)<br>            SQLITE EXEC INSERT INTO t(x) VALUES (1)<br>            SQ

- Thin SQLite command wrapper for status, connection management, Bible seed helpers, metadata inspection, SELECT queries, and EXEC statements.
- SQLite integration.
- Examples:
- SQLITE DB data\sql_regression.sqlite
- SQLITE EXEC CREATE TABLE t(x INT)
- SQLITE EXEC INSERT INTO t(x) VALUES (1)
- SQLITE SELECT * FROM t
- Notes:
- Used for regression testing and DBF↔SQL bridging experiments.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLITE &lt;subcommand&gt; ...

## Usage

- SQLITE
- SQLITE USAGE
- SQLITE STATUS
- SQLITE CWD
- SQLITE PWD
- SQLITE VERSION
- SQLITE OPEN &lt;file&gt;

## Note

- SQLITE with no arguments reports connection status and brief usage.
- SQLITE USAGE, HELP, and question mark print detailed usage.
- OPEN and DB connect to a SQLite database and create it if needed.
- BIBLE and BIBLECHECK open/check the canonical Bible seed database when found.
- EXEC runs non-SELECT SQL and may mutate the external SQLite database.
- SELECT prints query rows and caps output for CLI responsiveness.
- SQLITE is independent of DBF open/order state.

## Provenance

- Topic key: `DOT|SQLITE`
- Included HELP rows: `25`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
