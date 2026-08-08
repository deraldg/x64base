# Licensing Proposal 1 of 4 -- x64base engine

**Status:** DRAFT proposal, owner decision owed. Not legal advice. Date 2026-08-08.
Supersedes (for this project) the single GPLv3 blanket published 2026-08-08.

## The project

The **x64base engine**: the reusable DBF / xBase runtime, built **without** education
features (you confirmed it builds that way). The embeddable core only:

- the trinity headers (`include/xbase.hpp`, `xbase_vfp.hpp`, `xbase_64.hpp`)
- storage/table engine (DbArea, DBF read/write, memo/FPT)
- the index family (CDX / CNX / INX / LMDB backends)
- expression/eval primitives the engine needs to stand alone

**Explicitly NOT in this project:** the DotTalk++ shell and DotScript, the SelfDoc
development system, LabTalk content, and all AI work. Those are Proposals 2-4.

## Recommended license: **Apache-2.0**

Permissive. Anyone -- including a closed, commercial product -- can embed the engine.
That is the stated goal ("embeddable, or it is no fun"). Apache-2.0 over MIT because it
adds an explicit **patent grant** that protects both you and your embedders, and a clear
NOTICE/attribution mechanism.

**Alternatives considered:**
- **LGPL-3.0** -- also embeddable in closed apps, but improvements *to the engine itself*
  must be shared back. Choose this only if you want engine fixes to return to you. Slightly
  more friction for embedders.
- **MIT** -- simplest, but no patent grant. Apache-2.0 is the better default at the same
  openness.

## Why permissive here (and not the copyleft/commercial door)

The engine is the **adoption magnet**, deliberately given away. There is no income door on
the engine itself -- the value is protected downstream (DotTalk++ non-commercial, LabTalk
content, AI work private, and commercial licenses on those). This is a sound open-core
shape: free permissive core, protected everything-else.

## Open questions for you

1. **Exact source boundary.** Which files/dirs compose the "engine sans education" build
   target? A build flag exists -- name it here so the license scope maps to a real,
   buildable slice, not a vague "the engine part."
2. **Apache-2.0 vs LGPL-3.0** -- pure embed-and-go, or embed-but-fixes-return?
3. **Contributor CLA** -- needed before accepting outside engine contributions, so the
   permissive grant stays clean and you retain relicensing ability.

## If accepted

`LICENSE` (Apache-2.0 verbatim from apache.org) in the engine's scope, a short `NOTICE`,
and an entry in the repo LICENSE map (Proposal 5 territory) pointing the engine paths here.
