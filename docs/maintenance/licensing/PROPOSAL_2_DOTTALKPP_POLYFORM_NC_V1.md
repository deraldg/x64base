# Licensing Proposal 2 of 4 -- DotTalk++

**Status:** DRAFT proposal, owner decision owed. Not legal advice. Date 2026-08-08.
Supersedes (for this project) the single GPLv3 blanket published 2026-08-08.

## The project

**DotTalk++**: the application layer on top of the x64base engine, with the education
features included. Scope:

- the DotTalk++ interactive shell / REPL and command surface (`src/cli/`)
- DotScript (the scripting language), SQLSEL, the runtime command families
- the **SelfDoc development system** -- the documentation-generation pipeline
  (`tools/selfdoc/`, `tools/fullstack_docs/`, `tools/manualgen/`, the harvest/refcheck/
  normcheck machinery). *Per your correction: SelfDoc is part of DotTalk++, not the engine.*
- education/instructional features that the engine build strips out

**Not in this project:** the bare engine (Proposal 1), LabTalk content (Proposal 3), AI
work (Proposal 4).

## Recommended license: **PolyForm Noncommercial 1.0.0** (+ commercial license)

You asked for an "educational license." There is no standard OSI license by that name, and
a hand-rolled one is a trap. **PolyForm Noncommercial 1.0.0** is the clean, well-drafted
instrument that does exactly what you mean:

- source is open to read and use for **any non-commercial purpose** -- education, research,
  teaching, personal, hobby -- at no cost;
- **commercial use requires a commercial license** from you.

That is your income door for the app, the same dual-license shape as before, just
*non-commercial* rather than copyleft. It layers cleanly on an Apache-2.0 engine
(permissive-under-restrictive is allowed).

## Why not GPL here

GPL permits commercial use, so it would *not* protect the commercial door you want on the
app. Non-commercial-source-available does.

## Open questions for you

1. **SelfDoc output vs the SelfDoc tool.** The *tool* is DotTalk++ (non-commercial). The
   *documentation it generates* (manuals, the website content) is arguably content -- it may
   belong under LabTalk's CC license (Proposal 3), or be published CC-BY even if the
   generator is NC. Decide: does generated doc output inherit NC, or is it CC content?
2. **Commercial terms** -- your price/scope for a commercial DotTalk++ license (a lawyer
   should review the template before money moves).
3. **Contributor CLA** -- same as the engine; required to keep the commercial option.

## If accepted

`LICENSE` (PolyForm Noncommercial 1.0.0 verbatim from polyformproject.org) over the shell +
SelfDoc scope, a one-line "commercial license available -- contact the author" notice, and
a LICENSE-map entry pointing the DotTalk++ paths here.
