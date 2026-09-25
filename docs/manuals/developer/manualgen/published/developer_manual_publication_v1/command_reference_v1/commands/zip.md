<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# ZIP

- Catalog/topic: `DOT` / `ZIP`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

List, create, or extract ZIP archives through the configured ZIP backend.

## Status

- implemented=yes; supported=yes

## Syntax

- ZIP [USAGE|&lt;args...&gt;]
- ZIP USAGE
- ZIP LIST &lt;archive.zip&gt;
- ZIP CREATE &lt;archive.zip&gt; &lt;path&gt;
- ZIP EXTRACT &lt;archive.zip&gt; [target_dir]
- ZIP LIST backups.zip
- ZIP CREATE source_bundle.zip src
- ZIP EXTRACT source_bundle.zip tmp\source_bundle

## Usage

- ZIP USAGE
- ZIP LIST &lt;archive.zip&gt;
- ZIP CREATE &lt;archive.zip&gt; &lt;path&gt;
- ZIP EXTRACT &lt;archive.zip&gt; [target_dir]

## Example

- ZIP LIST backups.zip
- ZIP CREATE source_bundle.zip src
- ZIP EXTRACT source_bundle.zip tmp\source_bundle

## Note

- ZIP USAGE prints usage and does not touch archive files.
- ZIP LIST reads an archive and prints entries.
- ZIP CREATE writes an archive, adding .zip when needed.
- ZIP EXTRACT writes files under the target directory or current directory.

## Related

- COPY
- EXPORT

## Provenance

- Topic key: `DOT|ZIP`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
