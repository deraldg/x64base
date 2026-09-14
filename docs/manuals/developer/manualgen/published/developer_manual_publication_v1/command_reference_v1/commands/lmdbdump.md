<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LMDBDUMP

- Catalog/topic: `DOT` / `LMDBDUMP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Open an LMDB environment read-only and dump keys and values for diagnostics, with optional named DB, grep, limit, and start-key controls.

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

## Related

- LMDB
- CDX
- CNX

## Provenance

- Topic key: `DOT|LMDBDUMP`
- Included HELP rows: `27`
- HELP reference run: `MANRUN-20260914T034553Z-26B1376D`
- Disposition run: `MANRUN-20260914T034657Z-783CD9C3`
- Authority: `candidate_only`; `publication_authority_claimed=0`
