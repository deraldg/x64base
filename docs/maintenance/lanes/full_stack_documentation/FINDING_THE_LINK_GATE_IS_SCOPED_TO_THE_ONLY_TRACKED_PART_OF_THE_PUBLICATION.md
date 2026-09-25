# Finding: the link gate is scoped to the only tracked part of the publication

    Found     : 2026-09-25, in the prepush output of commit df698774a -- the
                commit that landed the finding this one completes.
    Evidence  : measured on Windows. Directory listings, `git ls-files`, and the
                checker's own argparse default.
    Lane      : full_stack_documentation / AIF-068.
    Status    : OPEN. Does not block the Gate 4 apply; see "the apply is clean".
    Reads with : the sibling finding filed in df698774a on the published manual
                resolving on main while development tracks none of it. That one
                measured the branch state; this one is about the instrument
                built to detect that state.

## What the gate said while the defect was live

    manual-link-integrity: 164 link target(s) in the accepted README
    manual-link-integrity: PASS -- every linked page exists and is tracked

True, and it answers a smaller question than it appears to.

## The publication's tracking state on development

    subtree                                    on disk  tracked  on main
    command_reference_v1/commands/*.md            164      164      183
    command_reference_v1/README.md                  1        1        1
    developer_manual_publication_v1.md              1        1        1
    sections/sections/*.md                         28        0       24
    appendices/*                                    4        0        4
    README.md            (publication root)         1        0        1
    ..._v1_appendices.md (publication root)         1        0        1

Three files and one directory are tracked. Everything else in the published
manual is on somebody's disk only.

## The gate's universe

    tools/staging/check_manual_link_integrity.py:87
        ap.add_argument("--manual-root", default=(
            "docs/manuals/developer/manualgen/published/"
            "developer_manual_publication_v1/command_reference_v1"))

`command_reference_v1` is exactly, and only, the subtree that is fully tracked.
The gate's scope and the healthy region are coextensive.

Both of its assertions are blind in the same way:

    1  LINKED IMPLIES TRACKED reads `<manual-root>/README.md` and nothing else.
       That README carries 164 links, all tracked -> PASS. The 183 command links
       carried by the section files are in `sections/sections/`, outside the
       scope, and 19 of those resolve on no branch this gate can see.

    2  NO UNTRACKED STRAYS globs `<manual-root>/commands/*.md` only:
           on disk 164, tracked 164, strays 0
       The 28 untracked section files and 4 untracked appendices are in sibling
       directories. Zero strays is a true statement about one folder.

## Why this is the sharpest instance of the shape yet

This checker was written FOR this defect. Its own docstring:

    - "accepted" meant "present on this disk". No other clone had the pages.
    - the acceptance ledgers, hashes and backups were the ONLY record of a
      change, so an apply could not be reviewed as a diff -- and this lane's
      entire defence against a bad apply is reviewing the diff.
    ...
    2. NO UNTRACKED STRAYS. ... 47 such pages were found on 2026-09-02, dating
       from 2026-07-18 to 2026-08-25.

47 untracked pages were found under `commands/`, correctly judged serious, and a
gate was built. The gate was then scoped to the directory where the problem had
been found. The identical disease one directory over -- 28 untracked section
files and 4 untracked appendices, dating from the same 2026-07-18 publish -- has
been invisible to it ever since, and reads as PASS on every commit.

The reasoning in the docstring is sound. The scope is the defect. A check that
proves its own neighbourhood clean, in a tree where the neighbourhood was the
part somebody already fixed, is the proxy family's sixth sighting in this lane
and the first one found in a gate written to answer this exact question.

## Nothing else covers the gap either

    mandatory-tracked: 66 document(s) and 16 script(s) checked
    mandatory-tracked: PASS -- every declared file is tracked

`labtalk/ai_portal/check_mandatory_tracked.py:62` builds its set from paths the
ENTRY_DOCS cite. It is a citation-derived allow-list, so a file nothing cites
cannot be declared, and a file that is not declared cannot fail. Nothing in the
tree declares `sections/sections`. PASS is structurally guaranteed there, not
earned.

So on development: the section files are untracked, no gate asserts they should
be tracked, and the one gate whose subject is exactly "is the published manual
in the repository" is pointed one directory away.

## The apply is clean

Measured before running it, because the docstring above says the diff review is
this lane's only real defence and an untracked target destroys it:

    168 planned mutation targets, by directory:
        164  .../developer_manual_publication_v1/command_reference_v1/commands
          1  .../developer_manual_publication_v1/command_reference_v1
          2  docs/manuals/developer/manualgen/accepted_artifacts
          1  docs/manuals/developer/manualgen/accepted_manifests

    targets tracked on development : 168
    targets untracked             :   0
    targets under sections/       :   0

Every row lands in tracked, diff-reviewable files. `gate4_acceptance_apply.py`
mentions `sections/sections`, but not as a write target in this plan. The apply
proceeds.

## Remedies

    1  Widen the gate to the publication root, not `command_reference_v1`. Its
       two assertions are already the right two; they are aimed too narrowly.
       Run it over `sections/sections`, `appendices/`, and the publication root
       files and it fails today, correctly.
    2  Have it name its scope in its own output. "164 link target(s) in the
       accepted README" does not say WHICH README, or that a second set of 183
       links exists one directory over. A line naming the scope would have made
       this visible on 2026-09-02.
    3  Assert the publication is tracked as a whole, somewhere that is not a
       citation-derived allow-list. Untracked-and-unreferenced was already
       identified as the one state that is wrong whichever way you resolve it.
       28 files are in it.

## The rule this earns

A gate built in response to a defect found in one directory must be scoped to
the CLASS of the defect, not to the directory it was found in. Otherwise its
green is a report on the region that has already been repaired.
