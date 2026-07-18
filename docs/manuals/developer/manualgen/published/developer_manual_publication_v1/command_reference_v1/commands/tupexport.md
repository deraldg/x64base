<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# TUPEXPORT

- Catalog/topic: `DOT` / `TUPEXPORT`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Export tuple/projection output through the tuple export helper surface.

- Export tuple graph rows to a CSV file using a tuple spec, optional field list, and optional FOR predicate.

## Status

- implemented=yes; supported=yes

## Syntax

- TUPEXPORT [USAGE|&lt;args...&gt;]

## Usage

- TUPEXPORT USAGE
- TUPEXPORT CSV &lt;path&gt;
- TUPEXPORT CSV &lt;path&gt; &lt;tuple-spec&gt;
- TUPEXPORT CSV &lt;path&gt; FIELDS &lt;field-list&gt;
- TUPEXPORT CSV &lt;path&gt; * FOR &lt;expr&gt;

## Example

- TUPEXPORT CSV tmp\students.csv
- TUPEXPORT CSV tmp\students_names.csv FIELDS LNAME,FNAME
- TUPEXPORT CSV tmp\students_major.csv STUDENTS.*,MAJORS.* FOR MAJORS.NAME = "CS"

## Note

- TUPEXPORT USAGE prints usage before open-table checks or file writes.
- TUPEXPORT writes/truncates the requested CSV file.
- Tuple cursor/workspace cursor state is restored best-effort.

## Provenance

- Topic key: `DOT|TUPEXPORT`
- Included HELP rows: `15`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
