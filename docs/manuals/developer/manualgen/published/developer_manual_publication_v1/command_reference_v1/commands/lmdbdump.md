<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDBDUMP

- Catalog/topic: `DOT` / `LMDBDUMP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Developer/diagnostic surface for dumping or inspecting LMDB-backed index/storage state.

- Open an LMDB environment read-only and dump keys and values for diagnostics, with optional named DB, grep, limit, and start-key controls.

## Status

- implemented=yes; supported=yes

## Syntax

- LMDBDUMP [USAGE|&lt;args...&gt;]

## Usage

- LMDBDUMP USAGE
- LMDBDUMP &lt;env_path&gt;
- LMDBDUMP &lt;env_path&gt; --db &lt;name&gt;
- LMDBDUMP &lt;env_path&gt; -db &lt;name&gt;
- LMDBDUMP &lt;env_path&gt; --grep &lt;ascii&gt;
- LMDBDUMP &lt;env_path&gt; -grep &lt;ascii&gt;
- LMDBDUMP &lt;env_path&gt; --trydb
- LMDBDUMP &lt;env_path&gt; --limit &lt;n&gt;
- LMDBDUMP &lt;env_path&gt; --start &lt;key&gt;
- LMDBDUMP &lt;env_path&gt; --starthex &lt;hex&gt;

## Example

- LMDBDUMP indexes\students.cdx.d
- LMDBDUMP indexes\students.cdx.d --trydb
- LMDBDUMP indexes\students.cdx.d --grep MILLER --limit 50
- LMDBDUMP indexes\students.cdx.d --db lname --start M --limit 200

## Note

- LMDBDUMP opens the supplied LMDB environment read-only.
- LMDBDUMP does not depend on the xindex backend or current work area.
- --start treats the key as ASCII unless it begins with 0x.
- --starthex accepts hex bytes.
- --trydb scans main DB keys and probes named DB candidates.
- LMDBDUMP is diagnostic and does not mutate table or index data.

## Provenance

- Topic key: `DOT|LMDBDUMP`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
