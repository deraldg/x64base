# Website SelfDoc Publication Contract v1

Status: design-intended active contract.

## Purpose

This contract defines how DotTalk++ / x64base runtime work feeds the website.

The website is not an independent marketing fiction layer. It is a downstream
publication surface that should be able to trace important technical and
educational claims back to SelfDoc, contracts, manuals, metadata, and reviewed
runtime documents.

## Core Rule

`D:\code\ccode` is the implementation truth.

`D:\dev\x64base-site` is the public publication surface.

The site may reorganize, summarize, and present material for readers, but it
must not invent technical truth that the runtime/source tree cannot support.

## Authority Order

Use the existing project authority order:

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manualgen assembles teachable manuals.
Website publishes reviewed public-facing derivatives.
```

The website is downstream of the runtime and SelfDoc family, not upstream of it.

## Full-Stack Rule

x64base / DotTalk++ is a full-stack teaching system from beginning to end:

- engine and file/runtime behavior,
- command shell and DotScript,
- HELP, metadata, contracts, and manuals,
- diagrams and curated documentation,
- GUI/TUI/workbench surfaces,
- website publication and educational presentation.

The website should therefore be treated as part of the explainable system, not
as a disconnected brochure.

## Shared Document Rule

Shared documents should be divided into these classes:

| Class | Primary home | Website role |
| --- | --- | --- |
| Runtime/engineering truth | `D:\code\ccode\docs`, source, contracts, HELP lanes | summarized or mirrored |
| Publication-ready developer manuals | `D:\code\ccode\docs\manuals` and manualgen outputs | curated excerpts or full public pages |
| SelfDoc diagrams and metadata publication assets | `D:\code\ccode\dottalkpp\docs\generated` and related outputs | rendered/linked public artifacts |
| Site-only navigation and framing copy | `D:\dev\x64base-site\content` | presentation-only, must not contradict truth |

If the same technical claim exists in both trees, the runtime/source tree wins.

## GitHub/Public Surface Rule

The public website should link readers to current public work on GitHub where
appropriate.

Current public publication target:

- `https://github.com/deraldg/x64base`

The website may also describe local implementation truth in `D:\code\ccode`,
but it must not imply that unpublished local work is already public.

## SelfDoc Publication Rule

SelfDoc should feed the website through reviewed artifacts such as:

- contracts,
- developer handbook pages,
- project truth/status pages,
- manual excerpts,
- metadata-derived diagrams,
- command/help summaries,
- educational case/lab narratives.

Direct raw dumps are not the goal. The goal is reviewed, provenance-aware
publication.

## Educational Goal

The project should explicitly support learning front-end work through the
x64base / DotTalk++ / LabTalk system.

That educational goal includes:

- learning how runtime truth feeds UI truth,
- learning how CLI, TUI, GUI, and website layers align,
- learning how documentation and metadata feed public presentation,
- learning how a database system can explain itself from source to website.

LabTalk is the natural education-facing frame for this goal.

## Website Naming Rule

For the front-end family:

- `ArcticTalk` is the public umbrella brand,
- `Foxtalk` and fox-derived lanes remain valid lineage/subsystem names,
- classic FoxPro-style syntax may be preserved for historical reasons,
- the site should not revive `TurboTalk` as the forward-facing product name.

## Review Triggers

Review this contract when:

- site copy contradicts runtime truth,
- a new manual/publication lane is added,
- SelfDoc starts producing new public artifacts,
- GUI/TUI branding changes,
- GitHub publication structure changes,
- education/lab positioning changes.
