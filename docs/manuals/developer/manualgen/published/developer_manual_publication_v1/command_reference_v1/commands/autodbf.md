<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# AUTODBF

- Catalog/topic: `DOT` / `AUTODBF`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Create an X64 DBF from a CSV file and import the CSV rows into the newly created table.  CSV headers may become field names; when there is no header, deterministic FIELDnnn names are generated.

## Status

- implemented=yes; supported=yes

## Syntax

- AUTODBF USAGE
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt;
- AUTODBF X64 &lt;table&gt; FROM &lt;csvfile&gt;
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; HEADER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; NOHEADER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; AUTO
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; TEXTONLY
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; INFER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; OVERWRITE
- AUTODBF [USAGE|&lt;source&gt; [TO &lt;dbf&gt;]]

## Usage

- AUTODBF USAGE
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt;
- AUTODBF X64 &lt;table&gt; FROM &lt;csvfile&gt;
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; HEADER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; NOHEADER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; AUTO
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; TEXTONLY
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; INFER
- AUTODBF &lt;table&gt; FROM &lt;csvfile&gt; OVERWRITE

## Argument

- NOHEADER
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Note

- AUTODBF defaults to X64, AUTO header detection, INFER types, comma CSV.
- CSV records are parsed as records, not physical lines: quoted fields may contain commas, doubled quotes, and embedded newlines.
- AUTO is conservative: it chooses HEADER only when the first row looks like names and later data strongly indicates typed data.  Use HEADER or NOHEADER to remove ambiguity.
- Field names are normalized to command-safe x64 logical names, uniquified, capped to the current x64 logical-name limit, and then passed through the existing x64 descriptor fallback/mangling policy.
- Long text is not auto-promoted to M yet; values must fit current fixed-field x64base limits.  This avoids silently writing memo object id 0.
- Existing target DBFs are not overwritten unless OVERWRITE is supplied.

## Related

- CREATE
- IMPORT
- IMPORTSQL
- SETPATH
- STRUCT

## Provenance

- Topic key: `DOT|AUTODBF`
- Included HELP rows: `41`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
