# Licensing Proposal 4 of 4 -- AI work

**Status:** DRAFT proposal, owner decision owed (one structural choice). Not legal advice.
Date 2026-08-08. Supersedes (for this project) the GPLv3 blanket published 2026-08-08.

## The project

**All AI work** -- your private IP, kept closed. Scope:

- the AI Portal (`labtalk/ai_portal/`: the Tier-1 seed, Tier-0 generator, recall graph,
  onboarding, the two-atom coordination ontology)
- the coordination system (`coordination/`, `tools/coordination/`: the atomic AIF
  allocator, presence, quips, `wake`/lineage, the pseudo-chat + agent-sync transport)
- the AI reports gateway and AI-facing tooling (`tools/reports/` AI views, the AI docs
  under `docs/ai-friendly/`)
- the AI/agent orchestration built this year

## Recommended license: **Proprietary -- All Rights Reserved**

No open grant. Copyright reserved; no permission to use, copy, modify, or redistribute.
This is the differentiated orchestration you built and want to keep.

## The one structural decision (this is the real question)

The AI work currently lives **inside the public repo**. Two ways to make it "private":

- **(a) Source-visible but proprietary** -- it stays in the public tree, marked
  all-rights-reserved. People can read it; nobody may use it. Simplest; preserves the
  transparency that some of it depends on.
- **(b) Pull into a private repo** -- truly removed from public view. Strongest protection;
  more work, and it breaks anything public that references it.

**Complication:** part of this is *deliberately public-facing* -- the partner **entry
surface** (the `agent-sync` website page, the pseudo-chat board) exists so external agents
can read and post. That has to remain *readable* even if proprietary.

**Proposed line:** the **orchestration and tooling** go proprietary (option a or b, your
call); the **partner entry surface** stays readable-but-proprietary (visible, licensed only
for the narrow purpose of interoperating with your portal, not for reuse). Draw that line
explicitly so "private" does not accidentally wall off the mailbox you built for partners.

## Open questions for you

1. **(a) visible-proprietary or (b) private-repo** for the orchestration/tooling?
2. **Where exactly is the entry-surface line** -- which files stay readable for partners?
3. **Entanglement** -- any AI code compiled into the engine/shell binaries needs a carve-out
   so it is not accidentally shipped under Apache/PolyForm.

## If accepted

A `LICENSE-PROPRIETARY.txt` + per-file headers over the AI scope, a LICENSE-map entry, and
(if option b) a migration plan to a private repo with the entry surface mirrored out.
