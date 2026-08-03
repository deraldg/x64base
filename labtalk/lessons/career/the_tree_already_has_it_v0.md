# Search Before You Build, and Trust the Enforcer Over the Spec v0

Status: draft
Audience: developer, maintainer, ai-collaborator
Registry ID: lesson.career.the_tree_already_has_it
Concepts: concept.evidence.review, concept.selfdoc.validation
Proofs: proof.codev.system_corrects_its_extender, proof.engine.key_metadata_survives_workspace_roundtrip
Proof state: source_defined
Observed: 2026-07-29 (AIF-074, SQLSEL P0/P1 lane)

## Career Lesson

Two rules, both learned the expensive way, in one lane.

```text
1. Before designing a component, cite the search that proved it absent.
2. When authoring anything a toolchain checks, trust the ENFORCER over the SPEC.
```

They look unrelated. They are the same rule pointed in two directions: **the
tree knows more than you do, and it will tell you if you ask it before you
start rather than after.**

## Rule 1 -- Cite the search that proved it absent

A lane opened with a list of components it "needed." Nearly every one of them
already existed in the tree:

- locking
- the tuple carrier
- table buffering
- area resolution
- predicate compile and evaluate
- cursor guards
- a unique-field registry **whose own header requested the very phase the lane
  was about to design from scratch**

Construction was the right answer **zero times out of seven**. Every proposal
that survived contact with the tree turned into consumption of machinery that
was already there and already proven.

That last item deserves its own moment. `unique_registry.hpp` carried a header
comment saying "Phase 1: session-scoped ... storage/backfill policy belongs
elsewhere." The file was **asking for Phase 2 by name**. The lane proposed
building Phase 2 without reading the request. When it was finally built as
continuation rather than invention, it went green on first run: the registry
was emptied between `WORKSPACE SAVE` and `LOAD`, `LOAD` echoed
`KEY KEYREGR.KID PRIMARY` and `KEY KEYREGR.KLBL UNIQUE`, and the listing
matched pre-save exactly. Restoration was **proven, not assumed**, because the
registry was deliberately emptied first.

The rule is not "never build anything." It is that **absence is a claim, and
claims need evidence**. Writing "there is no X" costs you nothing and is
frequently false. Writing "I grepped for X across `src/` and `include/`, and
here is what I found" costs a minute and is checkable by the next person.

The claim also has to be falsifiable to be worth anything, so state its bound:
in this lane the **statement parser was the first genuine need that inward
search could not satisfy**. That single exception is what makes the other seven
meaningful. A rule that never loses is not a rule, it is a slogan.

## Rule 2 -- A hierarchy of trust

When you author something a toolchain will check -- a manifest, an envelope, a
schema, a config -- rank your sources like this:

```text
a passing in-tree example        (highest)
the ENFORCED policy registry
the specification document
memory                           (lowest)

an artifact you generated yourself but never ran through the gate
                                 (below all of the above)
```

That last line is the one people resist, and it is the one that costs the most.
Something you just produced feels verified because you were careful. Care is
not a gate. Until the check has run, the artifact is a hypothesis with good
formatting.

This ordering was learned by watching a **pre-commit gate reject the same
closeout envelope three times.** The author kept correcting it against the
published specification, which described a v2 schema **the validator does not
yet enforce**. The spec was newer. The enforcer was authoritative. Three
rejections went by before anyone stopped editing against the document and
started editing against the thing actually saying no.

Specifications describe intent. Enforcers describe reality. When they disagree,
reality wins, and the gap between them is a defect worth filing -- but you file
it *after* you satisfy the enforcer, not instead of.

## What Made This Recordable

Eleven corrections in one lane, and the split matters more than the count:

| Source | Count | Character |
|---|---|---|
| Owner redirects | 5 | Construction proposals turned into consumption of existing machinery. Catch latency fell to **zero** by the last one. |
| Toolchain, no human involved | 6 | Report-audit rejected the envelope 3x; MSVC C4244 caught a legacy 32-bit `gotoRec` in new x64 code before it shipped; the non-destructive smoke exposed a runtime usage text that had drifted from its own contract minutes after commit. |

The falling catch latency is the interesting number. The first redirect came
late and cost design work; the last was caught before it was written down. That
is what learning looks like when it is measured rather than asserted.

The evidence state here is `source_defined` rather than `runtime_observed`,
deliberately: this is a document trail, not a transcript. The trail is complete
and each instance is timestamped, quoted, and retained unedited -- but it is
not the same class of evidence as a run, and it should not claim to be.

## Practical Form

Before you build:

- Grep the tree. Then grep it for the *other* name it might have.
- Read the header comment of anything adjacent. Files ask for their own next
  phase more often than you would expect.
- In your design note, write the search you ran and what it returned. One line.

While you author:

- Find a passing in-tree example and copy its shape.
- If no example exists, satisfy the enforcer and read its source if you must.
- Run the gate before you believe your own artifact.

## Ties

- `proof.codev.system_corrects_its_extender` -- the eleven corrections.
- `proof.engine.key_metadata_survives_workspace_roundtrip` -- Phase 2 built as
  continuation, green on first run.
- `lesson.career.a_script_never_run_is_not_evidence` -- why an ungated artifact
  ranks below memory.
- `lesson.career.entities_and_the_bridge` -- why deleting "empty" things is its
  own hazard.

Owner: `member.derald`.
