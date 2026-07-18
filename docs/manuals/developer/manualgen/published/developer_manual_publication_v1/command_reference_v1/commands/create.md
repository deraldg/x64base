<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# CREATE

- Catalog/topic: `DOT` / `CREATE`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Create a new table, structure, or local project artifact through the implemented DotTalk++ creation surface.

- Create a DBF table in the configured DBF path slot using the requested xBase/DBF flavor and field specification.

## Status

- implemented=yes; supported=yes

## Syntax

- CREATE [USAGE|&lt;args...&gt;]

## Usage

- CREATE USAGE
- CREATE &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE MSDOS &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE DBASE &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE FOX26 &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE FOXPRO &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE VFP &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])
- CREATE X64 &lt;name&gt; (&lt;field&gt; &lt;type&gt;[, ...])

## Example

- CREATE students (sid N(6), lname C(20), fname C(15))
- CREATE X64 teachers (teacher_id I, full_name C(80), bio M)
- CREATE VFP ledger (acct C(12), amount Y, posted D)

## Note

- CREATE with no usable table/field specification shows usage and does not create a file.
- Relative table names resolve through the configured DBF path slot.
- CREATE clears active order state and closes the current area before writing the new table.
- After a successful write, CREATE opens the created table in the current area.
- If any field is M, CREATE attempts automatic memo attach after opening the table.
- X64 CREATE applies descriptor fallback/name policy for DBF descriptor safety.
- Long, duplicate, or descriptor-unsafe X64 field names may receive fallback tokens.
- X64 logical/authoritative metadata names are preserved when they fit the current x64 metadata limits.
- CREATE is a filesystem/schema mutation command; do not classify it as a read-only report command.

## Provenance

- Topic key: `DOT|CREATE`
- Included HELP rows: `24`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
