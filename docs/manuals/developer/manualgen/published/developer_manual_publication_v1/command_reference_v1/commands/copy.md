<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# COPY

- Catalog/topic: `DOT` / `COPY`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Copy the current DBF, convert the current table to a target DBF flavor, or copy a filesystem file.

## Status

- implemented=yes; supported=yes

## Syntax

- COPY USAGE
- COPY TO &lt;DBFNAME&gt; [WITH SIDECARS] [OVERWRITE]
- COPY TO &lt;DBFNAME&gt; AS &lt;MSDOS|DBASE|FOX26|FOXPRO|VFP|X64&gt; [OVERWRITE]
- COPY TO &lt;DBFNAME&gt; AS X64 VECTOR [OVERWRITE]
- COPY FILE &lt;SRC&gt; TO &lt;DST&gt; [OVERWRITE]
- COPY &lt;source&gt; TO &lt;target&gt;

## Usage

- COPY USAGE
- COPY TO &lt;DBFNAME&gt; [WITH SIDECARS] [OVERWRITE]
- COPY TO &lt;DBFNAME&gt; AS &lt;MSDOS|DBASE|FOX26|FOXPRO|VFP|X64&gt; [OVERWRITE]
- COPY TO &lt;DBFNAME&gt; AS X64 VECTOR [OVERWRITE]
- COPY FILE &lt;SRC&gt; TO &lt;DST&gt; [OVERWRITE]

## Example

- COPY TO students_copy
- COPY TO students_x64 AS X64 VECTOR OVERWRITE
- COPY TO students_vfp AS VFP
- COPY TO students_backup WITH SIDECARS OVERWRITE
- COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE

## Note

- COPY USAGE prints usage and does not require an open table.
- COPY TO requires an open table.
- COPY FILE does not require an open table.
- WITH SIDECARS applies only to binary COPY TO.
- OVERWRITE is required when the destination already exists.

## Related

- USE
- EXPORT
- PACK

## Provenance

- Topic key: `DOT|COPY`
- Included HELP rows: `27`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
