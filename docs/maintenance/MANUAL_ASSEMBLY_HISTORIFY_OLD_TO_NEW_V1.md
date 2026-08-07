# Historify -- from "force the pieces together" to a manifest-driven assembler

A development lesson, with evidence. MANUAL-ASSEMBLY lane (AIF-035), 2026-07-20.
Companions: `MANUAL_ASSEMBLY_LANE_V1.md`, `MANUAL_ASSEMBLY_M2_PART_CONTRACTS_V1.md`.

This document records, deliberately, how the developer manual went from being
*forced together* to being *assembled*. It is kept as evidence because the
project makes a self-documentation claim, and the honest way to hold that claim
is to show the moment the claim became true.

## The old way -- build the pieces and force them together

The first manual was real, and it worked, but it was made the way early software
is always made: build each piece, then force the pieces into one artifact by
hand. Concretely, producing `developer_manual_publication_v1.md` meant running on
the order of twenty individually-invoked, human-gated manualgen commands --
`inventory`, `validate`, `build-dry-run`, `build-reference-candidate`,
`build-curation-candidate`, `build-disposition-candidate`,
`build-selective-merge-candidate`, `build-controlled-acceptance-plan`,
`apply-controlled-acceptance`, the gate4/gate5 steps, and more -- each writing into
its own run directory, each needing a person to carry the result to the next
step.

It produced a good manual. But the *process* had the signature problems of
force-fitting:

- **No single assembler.** There was assembly *vocabulary* (`build-dry-run` even
  says "assemble a dry-run manual") but no one command that turned a declared
  whole into the manual. The whole lived in a person's head and a README's list
  of twenty commands.
- **The seams showed as gaps.** Nothing generated a table of contents, an index,
  or a glossary. The 183 command pages were *linked*, not bound. Front and back
  matter -- the very things that make a document a manual rather than a pile of
  chapters -- simply did not exist.
- **It drifted, and drift was found by hand.** When source changed, someone had
  to notice the manual was stale and re-hunt the affected prose. The work this
  week that preceded this lane was exactly that: a reactive, page-by-page sweep.

None of this was wrong for where the project was. It is simply the first stage of
every build: make it exist by force of will.

## The turning point -- declare the artifact, don't hand-fit it

The shift was not a bigger script. It was a change of stance: **stop assembling
the manual by hand and start declaring what the manual is**, then let a machine
assemble it. Four questions, separated cleanly:

1. **What** is the manual made of? -> a bill of materials.
2. **How** may each part be produced and touched? -> per-part contracts.
3. **Assemble** it -> one manifest-driven runner.
4. **Keep it honest** -> a drift gate.

## The new way -- manifest, assembler, gate

The manual is now declared in `tools/manualgen/manual_assembly_manifest.yaml`
(schema `dottalk.manual.assembly_manifest.v1`): **22 parts** in reading order,
each carrying its class, direction, source-of-record, a stable `MAN-*` anchor, a
region mode that bounds what the assembler may touch, and a generator binding.
The vocabulary is shared verbatim with the website content manifest, so the
manual and the site sit on one simplex/duplex spine.

`tools/manualgen/assemble_manual.py` reads that manifest and emits the manual in
one pass -- a loop over parts, dispatching on region mode, reusing manualgen for
the parts it already builds and running eight new generators for the rest
(title, provenance, TOC, function reference, error catalog, diagrams, glossary,
index, colophon). It writes to `generated/`, never `published/`; acceptance stays
gated.

`tools/manualgen/check_manual_drift.py` re-assembles from current source and fails
the build if a *generated* region no longer matches -- the same discipline the
catalog and diagram checks already apply, now covering the manual.

## Evidence

| | Old way | New way |
| --- | --- | --- |
| Assembly | ~20 hand-carried CLI steps | one `assemble_manual.py` run |
| The whole | implicit (a README list) | declared (22-part manifest) |
| TOC / index / glossary | none | generated |
| Command pages | 183 linked | 183 bound |
| Front/back matter | absent | title, provenance, colophon generated |
| Staleness | found by hand | drift gate fails the build |
| Self-record | none | colophon records its own build |

First assembled build (source commit `8ee746de`): **22/22 parts, 13,782 lines,
anchors balanced 18/18**; 63 functions harvested from `function_catalog.cpp`, 183
command pages bound, 12 diagrams bound from the attachment matrix, TOC + index +
glossary generated. Drift gate proven end to end: clean **PASS** (22 parts) -> a
corrupted generated region flips it to **FAIL** and names the part -> restore
returns to **PASS**. Exports produced (Markdown, PDF, HTML) and staged to the
website at a stable "latest" permalink.

## The lesson (the part that generalises)

Force-fitting is *imperative*: the artifact is whatever fell out of the steps you
happened to run, and its integrity lives in the operator's memory. Assembly is
*declarative*: the artifact is what the manifest says it is, the machine
guarantees the parts are present and current, and integrity is a build gate
instead of a person's vigilance.

The tell that a subsystem is ready for this shift is the same tell we had here --
you can *name the pieces* but you *force them together*. When that is true, the
move is not to automate the forcing; it is to declare the whole and generate to
it. The forcing then disappears, and what is left is a thing that can prove
itself. The manual's colophon is the proof made literal: the last page records
exactly how the first twenty-one parts were assembled.

## Where this plugs in

- SDLC: this is the manual-side twin of the website assembly stream (AIF-033) and
  the diagram generation lane (AIF-032); all three are governed by the doc/SDLC
  model pinned in AIF-034.
- AI-Portal: the lane, its milestones, and this lesson are the process record;
  the assembler and gate are the mechanism. Together they let the self-doc claim
  be demonstrated on demand rather than asserted.
