# Licensing Proposal 3 of 4 -- LabTalk / Laboratory Campus

**Status:** DRAFT proposal, **TENTATIVE** -- owner to pick the CC flavor. Not legal advice.
Date 2026-08-08. Supersedes (for this project) the GPLv3 blanket published 2026-08-08.

## The project

**LabTalk / the Laboratory Campus**: the education layer -- curriculum, labs, lab
specimens, teaching guides, the campus/course material. This is primarily **content, not
software**, which is why it wants a *content* license, not a code license. GPL/Apache/
PolyForm are all software licenses and are the wrong family for teaching material.

**Boundary note:** any *code* that lives under LabTalk (tooling, generators) follows the
software licensing (engine or DotTalk++ as appropriate). Only the *content* -- prose,
curriculum, lab exercises, diagrams, specimen data -- is licensed here.

## Recommended: **Creative Commons** -- three real options (kicking them around)

- **CC-BY-4.0** -- maximal openness; anyone may use, adapt, and even *commercialize* with
  attribution. No income door. Best if you want the widest possible educational reach and
  don't intend to sell the content.
- **CC-BY-NC-4.0 (recommended)** -- free to learn, share, and adapt for **non-commercial**
  use with attribution; commercial use needs your permission. This matches DotTalk++'s
  non-commercial posture, so your whole education side tells **one coherent story: free to
  learn, licensed to commercialize.** It preserves your "sell the understanding" income.
- **CC-BY-NC-SA-4.0** -- same as NC, plus **share-alike**: derivatives must stay under the
  same license. Adds protection against someone enclosing your curriculum, at the cost of
  some remix friction.

**My pick: CC-BY-NC-4.0**, with CC-BY-NC-SA-4.0 as the choice if you specifically want
derivatives to remain open.

## Open questions for you (why this stays tentative)

1. **Pick the CC flavor** -- BY, BY-NC, or BY-NC-SA.
2. **Content boundary** -- exactly which paths are LabTalk content vs LabTalk code vs
   DotTalk++ SelfDoc output. This overlaps Proposal 2's open question about generated docs.
3. **Specimen / fixture data** -- lab data sets: content (CC) or fixtures shipped with the
   engine/app? Decide where sample DBF data falls.

## If accepted

The chosen CC license (verbatim from creativecommons.org) over the LabTalk content scope,
plus a LICENSE-map entry. Until you pick a flavor, this project is marked **tentative** and
carries no license file yet -- the one place it is correct to leave a "to be determined."
