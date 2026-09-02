# Command reference candidate -- review finding

    run       : DOCFLUSH-20260901-002 (v8)
    candidate : MANRUN-20260902T130018Z-1F797173
    review bk : MANRUN-20260902T130019Z-A239723B
    measured  : 2026-09-02
    posture   : REPORT-ONLY. Candidate not accepted; nothing mutated.

## The candidate is sound

    status                   PASS_CANDIDATE_ONLY
    pages                    164 / 164
    lineage rows             11121   (July candidate: 10502, +619)
    findings                 0
    local_path_hits          0
    accepted_reader_mutated  0
    website_mutated          0
    accepted reader sha      unchanged before and after

Attention-labelled pages: **2**, and both are correct.

    FOX|DO    status=partial  impl=F supp=F  INCLUDE_PARTIAL_HELP_REFERENCE
    FOX|RUN   status=partial  impl=F supp=F  INCLUDE_PARTIAL_HELP_REFERENCE

These are the FoxPro commands documented as "use DOTSCRIPT instead". Deliberately
partial, correctly flagged, no action.

The memo prose landed. `commands/area51.md` carries the full authored contract
narrative -- including the two-jokes paragraph about the command's name -- which
is content that did not exist in any harvest before the engine-backed export.
That is the payoff of the E5 work made visible on a page.

## THE FINDING: wrapped prose renders as one bullet per source line

`commands/area51.md`, Note section, verbatim:

    - AREA51 is a developer/debug status probe, not a member of the AREA family,
    - and `status: developer` above says so. It read `supported` until
    - 2026-08-30 while THIS PARAGRAPH already called it a developer probe -- the
    - contract's own prose and its own status field disagreeing, which is the

One paragraph, four bullets, sentences broken mid-clause. A reader sees a list
where the author wrote prose.

**Systematic, measured across all 164 pages:**

    pages with sentence-fragmented bullets   28 of 164
    total fragmented bullets                114

    worst: area51 18, buildlmdb 10, model 10, autodbf 7, dotscript 7,
           gps 6, cnx 5, export 5, rel 5, script 5

Detection was conservative -- a bullet counts as fragmented only if it ends in a
comma with another bullet following, or begins lower-case directly after another
bullet. Genuine lists are unaffected, so 114 is a floor, not a ceiling.

### Why it happens, and why it is not a data defect

The page generator emits one Markdown bullet per HELP_LINE row. That is CORRECT
for `Syntax` and `Usage`, which are genuinely line-oriented. It is wrong for
`NOTE`, where the store holds a wrapped paragraph as consecutive rows and the
line breaks are an artifact of the source comment's column width, not structure.

The store is right. The rendering is what needs a rule: within a NOTE block,
consecutive rows should join into a paragraph unless a row begins a new list
item or is blank.

**Not fixed here.** It is a presentation decision about how the manual reads, the
house may prefer bullets in some sections, and it changes 28 pages at once. That
is the owner's call, not the steward's -- and it is exactly the sort of thing
human review of a candidate exists to catch, which is the process working.

## Recommendation

1. **Rule on the NOTE rendering** before Gate 4 acceptance. Accepting now bakes
   114 fragmented bullets into the accepted reader, and they will be harder to
   unpick once published than to fix in the generator.
2. Everything else about this candidate is clean and ready.
3. Gate 4 (`build-gate4-acceptance-plan`) is the acceptance path for the command
   reference and is distinct from the controlled-acceptance chain, which
   replays the July prose merge and should stay unused.
