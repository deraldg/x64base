# DEV-19 External References

```yaml
page_id: DEV-19
title: External References
status: DRAFT
last_verified: 2026-08-20
evidence_classes: [SOURCE, PLANNED]
```

## Purpose

A register of the OUTSIDE sources this project reads when it needs to know what a
legacy format or a legacy behaviour was. It exists because those sources were
already being cited one at a time, inside whichever document happened to need
them, where nobody else could find them again.

This page links and characterises. **It does not copy.** Every source below is
someone else's work, published under their terms, and the useful thing to record
here is what it is good for and where it stops -- not its text.

## The governing rule, and it is not new

Stated first in `docs/ai-friendly/AI_ENGINE_VFP_M1_NULLFLAGS_DECODE_DESIGN_V1.md`
and adopted here unchanged:

> Any conflict between external authorities is resolved by the real-fixture
> proof.

An external source is evidence about a FORMAT. It is never evidence about this
engine. Where a document says one thing and a measured fixture says another, the
fixture wins and the discrepancy gets written down.

The companion rule, standing in AIF-120 and general enough to belong here:

> **VFP is the source of the DOCUMENT FORMATS only.** Runtime semantics come from
> x64base, measured.

## Register

### The Hacker's Guide to Visual FoxPro ("hackfox")

Whil Hentzen, Tamar E. Granor, Ted Roche, Doug Hennig et al.
Published online at `https://hackfox.github.io/`.

The single most useful outside description of the VFP file formats and of what
the product actually did, as distinct from what its own help said. Organised by
section and chapter, addressable per page.

**Pages this project has relied on so far:**

| Page | What it covers | Where it was used |
|---|---|---|
| `section1/s1c2.html` -- "DBF, FPT, CDX, DBC -- Hike!" | The container formats: table, memo, compound index, database container | `AI_ENGINE_VFP_M1_NULLFLAGS_DECODE_DESIGN_V1.md`, alongside two independent implementations, for the `_NullFlags` varlength decode |
| `section6/s6c2.html` -- "What's in the Downloads?" | The book's own download bundle: demo code, utility classes, the HTML Help build of the book | Filed 2026-08-20 at the steward's request. See the note below |

**A note on `section6/s6c2.html`, because filing it without one would mislead
whoever opens it next:** this page is bibliography, not format documentation. It
describes what ships in the book's `downloads.zip` -- drag-and-drop demos, array
utilities, a Connection Manager class -- and it notes that the VFP 7 print edition
dropped roughly a thousand pages of Reference section, which survives only in the
HTML Help build (`hackfox.chm`). Its practical value to us is that pointer: **the
Reference material this project keeps wanting is in the CHM, not in the printed
book.** It is a map to the source, not the source.

The page also states that the authors' copyright notices must be retained when
their example code is used. Nothing in this repository uses their code, and this
register is not an invitation to start.

### Implementation cross-checks

Independent readers of the same formats, useful precisely because they were
written by people who had to make the bytes work rather than describe them:

| Source | What it settles |
|---|---|
| `go-foxpro-dbf` (Sebastiaan Klippert), issue #9 "Support VFP Varchar field" | The `_NullFlags` varlength-bit plus last-byte length behaviour |
| tDBF (Delphi/BCB), open-discussion thread "_NullFlags Field on Visual FoxPro" | The same field, arrived at independently |

## How to add to this page

One row, one URL, one sentence on what the page is *good for*, and one on where
it stops. If a source was used to settle something, name the document it settled
it in -- a reference nobody can trace back to a decision is a bookmark, not
evidence.

If a source turns out to be wrong against a fixture, **do not delete the row.**
Record the disagreement and which fixture won. A source that was wrong once is
still worth knowing about, and the next reader deserves to inherit the correction
rather than repeat the experiment.
