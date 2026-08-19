---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-015
  recorded_at_utc: 2026-08-19T00:51:37Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: c21413a36
  authorization:
    requested_by: maintainer (member.derald), in-session, "can you find an example on the
      internet" -> "take them all to learn from, keep the default in the repo, we decide"
      -> "yes write it up".
    scope: >
      Measures 170 third-party .SCX (3,010 object records) against R1, R2, R12, R13
      and M5. Vendors nothing: the corpus is reproducible from a clone. Corrects
      R12's M4 for the second time, this run.
  report:
    path: docs/maintenance/AIF120_CORPUS_SCAN_V1.md
    kind: measurement
---

# AIF-120 -- 170 forms, 3,010 records: what the lane got right and what it did not

Status: **measurement, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Until now every ruling in this lane rested on **three** `.SCX` files. This is the
first measurement against a corpus.

## 1. Provenance, and why nothing is vendored

| | |
| --- | --- |
| source | `https://github.com/VFPX/Samples` |
| commit | `8827135c2c60`, "Initial commit", 2019-03-05 |
| contents | 170 `.SCX`, 25 `.VCX`, 14 `.FRX`, 9 `.MNX` |
| licence | **undetermined** -- no `LICENSE` file; a README saying "Samples showing how VFP works". Microsoft-authored sample code contributed to VFPX. |

**No file from this corpus is copied into this repository.** The licence question
is the maintainer's to settle and had not been settled when this ran, so the lane
takes the measurements and leaves the bytes where they are. Every number below is
reproducible:

```sh
git clone --depth 1 https://github.com/VFPX/Samples.git
cp <ccode>/tools/vfp/read_vfp_binary.py .
python3 corpus_scan.py Samples
```

`corpus_scan.py` is the scanner that produced this document. Reader: this
project's own `tools/vfp/read_vfp_binary.py`, unmodified. **All 195 `.SCX`/`.VCX`
files read without a single failure**, which is itself a result -- the reader was
written against three specimens and generalised to a corpus it had never seen.

## 2. Two rulings confirmed at a scale the lane could not previously reach

**R13 -- `CLASS` is required on output. `CLASS` is empty in 0 of 3,010 object
records.** Not once, in 170 files, from many authors. R13 was inferred from three
specimens and one VFP error message; it now stands on three thousand records.

**M5's retraction -- the font metrics record is universal.** The trailing
`PLATFORM = COMMENT`, `UNIQUEID = RESERVED` record carrying the font table is
present in **170 of 170** files. The original M5 claimed the document carries no
font metrics. It was wrong on three specimens and it is wrong on a hundred and
seventy.

## 3. R2 becomes load-bearing rather than a footnote

**`ScaleMode` appears in the `PROPERTIES` of 19 of 3,010 records.** Six tenths of
one percent.

R2 has two halves: the document should carry its unit, and the reader must supply
a default when it does not *and record which default it applied*. The lane has
treated the first half as the ruling. **The corpus says the second half is the
ruling** -- for 99.4% of records there is no declared unit at all, so an importer
is applying a default essentially always, and R2's requirement that the applied
default be recorded is what stands between that and silent misplacement.

## 4. R12's M4 -- wrong twice, corrected here with the real structure

This measurement has now been restated three times in one session. The history
matters more than the final number:

| stated | basis | claim |
| --- | --- | --- |
| first | `ACCOUNTS.SCX` + `form1.scx` | "22 of 45 partial", aggregated across a wizard and a native form |
| second | + `STUDENTS.SCX` | "wizard 100%, native 0%" -- partiality is a wizard artifact |
| **third, here** | **170 files** | **367 of 2,684 (13.7%)**, and it tracks CONTAINERS, not producers |

Partial rate by base class, geometry-bearing records only, classes with 20 or more:

| base class | geometry records | partial |
| --- | --- | --- |
| `form` | 175 | **57%** |
| `container` | 47 | **47%** |
| `custom` | 118 | 30% |
| `commandbutton` | 538 | 25% |
| `label` | 757 | 8% |
| `combobox` | 64 | 2% |
| `textbox` | 222 | 1% |
| `checkbox` | 106 | 1% |
| `shape` (198), `dataenvironment` (127), `cursor` (79), `editbox` (42), `listbox` (34), `grid` (30), `olecontrol` (25), `optiongroup` (25), `image` (21), `pageframe` (20) | | **0%** |

And which dimensions are omitted, across the 367:

| omitted | count |
| --- | --- |
| `height` **and** `width` | 207 |
| `left` **and** `top` | 100 |
| `height` alone | 48 |
| `width` alone | 12 |

**Both earlier framings are wrong.** Partiality is not a wizard artifact -- these
are overwhelmingly hand-authored forms and it occurs in 13.7% of their geometry
records. And it is not "text-bearing controls omit height": the most common
omission is `height` **and** `width` together, and the classes that omit are
containers (`form` 57%, `container` 47%) while every visual control that has an
intrinsic size -- `shape`, `image`, `grid`, `pageframe`, `editbox`, `listbox` --
omits nothing at all.

The pattern that actually fits: **a container omits the dimensions its contents
or its window manager will determine, and a sized control states them.** `form`
omits `height`/`width` because the window is sized at runtime; controls with
intrinsic geometry declare all four.

**R12.3 survives all three versions and is strengthened.** "Record that a
dimension is unspecified; never default it to a number" is exactly right whether
partiality is 100%, 0% or 13.7%. What changes is the explanation offered for
*why* it happens, and this lane has now offered three. The third is the first one
measured against enough files to be worth believing, and it should be treated as
provisional until something disproves it too.

## 5. R1 is narrower than the wizard specimens implied

**431 of 3,010 records (14.3%) carry a non-empty `CLASSLOC`.** The wizard forms
this lane started from are 20-of-24 and 20-of-26 -- near-total external
dependence. Across real forms, roughly one record in seven depends on an external
class library and the rest are self-contained.

R1's ruling is unchanged: key on `BASECLASS`, degrade gracefully. Its supporting
argument gets weaker and its cost gets lower -- an importer keyed on `CLASS`
would fail closed on 14% of records rather than on nearly all of them, which is
worse in a subtler way, since a 14% failure rate looks like a bug in a specific
form rather than a broken importer.

## 6. `RESERVED4` -- from one data point to a distribution

VFP wrote `RESERVED4 = 1` into our generated form's DataEnvironment and nothing
explained it. Across the corpus: **`2` (154 records) and `1` (16 records)**, empty
everywhere else.

**Chased, and NOT decoded.** Recorded here in full because a negative result with
its method stated is worth more than the next session repeating the search.

What is established:

1. It appears on **exactly one record per file -- the DataEnvironment, always
   record 2 -- in 170 of 170 files.** It is universal, not occasional.
2. It is **binary**: `2` (154 files) or `1` (16).
3. **It is not a count.** Uncorrelated with cursor count (0-5), DataEnvironment
   member count (0-7), and `RESERVED2` (1-8) -- all of which vary freely within
   both groups.
4. **Not a property flag.** The DataEnvironment's own property keys distribute
   almost identically across both values (`datasource` 37% vs 39%).
5. **Not a file-format version.** Every file in both groups carries the same
   `VERSION =   3.00` in its `Screen` header record.
6. **Not cleanly an era marker.** The `=1` group skews newer -- median
   `TIMESTAMP` 686,196,354 against 552,687,696 -- but the ranges overlap heavily
   (`=1` min 544,893,238 sits well inside the `=2` range), so no threshold
   separates them.

**The hypothesis that fits our own specimens perfectly and the corpus not at all.**
Our five VFP 9 files split without exception by which VFP tool produced them:

| fixture | produced by | `RESERVED4` |
| --- | --- | --- |
| `ACCOUNTS.SCX` | VFP 9 Form Wizard | `2` |
| `STUDENTS.SCX` | VFP 9 Form Wizard | `2` |
| `form1.scx` | VFP 9 designer, hand-built | `1` |
| `X64FORM_VFPSAVED.SCX` | ours, then saved by the VFP 9 designer | `1` |
| `X64FORM_SAMEDIR.SCX` | same, saved again elsewhere | `1` |

Five for five: wizard writes `2`, designer writes `1`, same VFP version. But
tested against the corpus the rule collapses -- only **2 of 152** `=2` files carry
any wizard class-library fingerprint at all. **A rule that is perfect on five
files and absent on a hundred and fifty is not a rule**, and this lane has now
been burned three times by generalising from a handful. It is recorded as a
hypothesis with its own disconfirming evidence attached, and nothing is built on
it.

**Also tested and rejected: the database-container hypothesis.** A VFP
DataEnvironment can source from free tables or from a `.DBC`, which is exactly the
kind of distinction a per-DataEnvironment marker would plausibly record. Measured:
`=2` splits 44 DBC-backed / 10 free / 100 with no cursors at all; `=1` splits
1 / 5 / 10. Both values occur on both kinds. Not it.

**The maintainer's reframing, untested and the most promising direction left.**
member.derald, in session: *"I have a weird file or two I have to keep in the
workspace dir to handle things like value ranges for fields, maybe its like that."*

That reframes the search. Every hypothesis above treats `RESERVED4` as describing
something INTRINSIC to the DataEnvironment -- its size, its members, its data
source, its era, its producer -- and all of them fail. A marker that flags or
points at state held OUTSIDE the file would be invisible to every one of those
correlations, which is precisely the shape of the evidence: universal, binary,
and uncorrelated with everything measurable inside the document.

It is recorded untested because testing it needs artifacts this corpus does not
carry -- the workspace-side files a DataEnvironment might reference. Whoever picks
this up should start there rather than re-running the correlations above, which
are all recorded as negative.

**One thing about `RESERVED4` IS settled, and it matters for R13.** Our writer
left it **empty**, and VFP 9 opened, ran and round-tripped the file anyway. So
`RESERVED4` is a field the reference implementation **writes but does not
require** -- a third category beside R13's required-on-output and optional-on-input.
Gate 10's contract needs all three: *required to produce*, *optional to produce*,
and *emitted by the reference but safely omitted*. Only the last is invisible
unless you write the format and get away with leaving something out.

## 7. What this corpus makes available that the lane still lacks

- **169 of 170 forms carry real `METHODS` code** -- R4's open item, which the lane
  has been waiting on since the first specimen. `Samples/Solution/Forms/Graphics/graph.scx`
  is the standout: 36 records, 3,900 bytes of methods, real drawing calls
  (`THISFORMSET.frmGraph.line(...)`, `forecolor = rgb(0,0,0)`), and a `formset`.
- **14 `.FRX`** -- the report format, never opened before this lane. Measured
  separately in section 8.
- **Base-class vocabulary 26 -> 36.** New: `formset`, `page`, `optionbutton`,
  `separator` (78 records), `control`, `collection`, `relation`, `cursoradapter`,
  `projecthook`, `reportlistener`.

## 8. `.FRX` -- the third designer format, and R10 gets wider

`Samples/Solution/Reports/invoice.frx`: version `0x30`, 58 records, `rlen` 229,
width arithmetic checks, **75 columns** against `.SCX`'s 23 and `.MNX`'s 25.

| concept | `.SCX` | `.MNX` | `.FRX` |
| --- | --- | --- | --- |
| position | `Top`/`Left` in a `PROPERTIES` memo | **none at all** | `VPOS`/`HPOS` as columns |
| font | a font table in the trailing `RESERVED` record | n/a | `FONTFACE`/`FONTSTYLE`/`FONTSIZE` as columns |
| colour | a `PROPERTIES` value | n/a | `PENRED`/`PENGREEN`/`PENBLUE`, `FILLRED`/`FILLGREEN`/`FILLBLUE` as integers |
| parenting | `PARENT`, flat or dotted | `LEVELNAME` + `ITEMNUM` | `OBJTYPE` bands |

R10 says "every designer format parents differently; only the DBF layer is
shared." Measured on a third format, that is **more** true than when it was
written: the formats differ not only in parenting but in where they put geometry,
how they encode fonts, and how they represent colour. 54 of 58 `.FRX` records
carry geometry, in a vocabulary no other format uses.

For gate 10 this is the strongest available argument that the design table must
define its own encoding for each concept and treat every designer format as a
mapping, never as a shape to inherit.

## 9. Handoff -- PowerShell, run in `D:\code\ccode`

```powershell
git add docs/maintenance/AIF120_CORPUS_SCAN_V1.md
git add docs/maintenance/AIF120_COORDINATE_RULING_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git status --short -uall
git commit -m "AIF-120: corpus scan over 170 third-party forms -- R13 and M5 confirmed at scale, M4 corrected a second time, .FRX measured"
```
