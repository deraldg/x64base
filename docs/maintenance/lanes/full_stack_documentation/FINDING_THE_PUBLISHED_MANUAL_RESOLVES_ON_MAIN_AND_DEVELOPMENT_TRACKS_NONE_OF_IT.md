# Finding: the published manual resolves perfectly on main, and development tracks none of it

    Found     : 2026-09-25, DOCFLUSH-20260924-001 Gate 6, reading the Gate 4
                acceptance plan's own gap ledger before authorizing the apply,
                then asking the owner's question -- missing from where?
    Evidence  : measured on Windows against both branches, the publication
                staging tree and the website tree. Every count below is derived
                from git plumbing or a directory listing, none asserted.
    Lane      : full_stack_documentation / AIF-068.
    Status    : OPEN. The apply is CORRECT and proceeds. This is a branch and
                tracking defect, not a content defect, and it is bigger than the
                22 rows that surfaced it.
    Replaces  : an earlier draft of this finding titled "the manual links to 22
                command pages and none of them exist". That title was true only
                of the branch I was standing on, and its stated cause (R127's
                --expected-topic-key allow-list) named the wrong generator. Both
                errors are recorded here rather than quietly dropped.

## The question that broke the first draft

The owner asked: were they missing from github, the site, the manual? The first
draft had not asked where. It measured one tree, found 22 link destinations with
no file, and wrote a cause. Measuring the other trees inverted the finding.

## The answer, by layer

    layer                                     19 of the 22   the other 3
    ---------------------------------------   ------------   -----------
    GitHub origin/main                        PRESENT        absent
    C:\x64base publication staging            PRESENT        absent
    D:\code\ccode branch development (HEAD)   MISSING        absent
    website D:\dev\x64base-site               no per-command pages at all, by design

The 19 have been on origin/main since 2026-07-18. They are not lost. They were
never brought down into the branch that every gate in this flush measures.

## The command pages

    git ls-tree -r --name-only origin/main -- <commands>  |  grep -c .md   ->  183
    git ls-tree -r --name-only HEAD        -- <commands>  |  grep -c .md   ->  164

    in origin/main, not in HEAD (19):
        area bottom browse browser continue ersatz find go goto list locate
        schemas seek select skip smartlist top use workspace
    in HEAD, not in origin/main:  (none)

HEAD is a strict subset. The 19 are exactly the shortfall.

Publication staging agrees with main: 183 pages, the same 19 present, with real
content and not stubs -- workspace.md 3058 bytes, browser.md 2425, use.md 1812.
Staging also lacks user, buildvectors and vdisk.

## The commit, and why HEAD never saw it

    be9350531  docs: publish full-stack documentation flush
               Sat Jul 18 08:32:26 2026 -0700   Derald Grimwood
    git merge-base --is-ancestor be9350531 HEAD   ->  NO
    git rev-list --left-right --count origin/main...HEAD   ->  99  1620

Development is 1620 commits ahead and 99 behind. One of those 99 carries the
navigation core of the command reference.

## The larger defect: development tracks no section files at all

Following the same question one layer up produced the real finding.

    files tracked on origin/main : 3174
    files tracked on HEAD        : 6542
    tracked on origin/main and NOT on HEAD : 803

    by path, top of the list:
        570  dottalkpp/data
        117  docs/maintenance
         63  docs/manuals
         12  dottalkpp/docs
          7  labtalk/ai_portal

    the 63 under docs/manuals:
         24  .../published/developer_manual_publication_v1/sections/sections
         19  .../published/developer_manual_publication_v1/command_reference_v1/commands
         13  docs/manuals/dist/diagram_png
          4  .../published/developer_manual_publication_v1/appendices
          2  .../published/developer_manual_publication_v1
          1  docs/manuals/dist

The section files are the load-bearing item:

    sections/sections tracked on origin/main : 24
    sections/sections tracked on HEAD        :  0
    sections/sections present on disk        : 28
    git status --short -uall -- <sections>   :  28 rows, all "??"
    git check-ignore -v <a section>          :  no match, exit 1

Twenty-eight section files sit in the development working tree, untracked and not
ignored. `navigation_browsing_and_search.md` and
`workspaces_areas_and_session_state.md` -- the two files the gap ledger cites as
carrying 19 of the 22 links -- are among them. The gates read a publication that
the branch does not track, against a page set the branch is missing 19 of.

## The clinching measurement

Take the 24 sections that origin/main actually publishes, extract every command
link they carry, and resolve it against each branch:

    distinct command links across the 24 published sections :  183
    unresolved against origin/main's 183 pages              :    0
    unresolved against HEAD's 164 pages                     :   19

One hundred and eighty-three links, one hundred and eighty-three pages, nothing
dangling. **The published manual is internally complete and consistent on the
branch it was published to.** There is no dead-link defect in the published
manual. There is a branch that does not carry the publication and a gate that
measures it anyway.

## And the 3 that really do not exist

The four sections on disk that main does not publish are:

    ai_portal_and_pseudo_chat.md                            links: (none)
    identity_authentication_rbac_and_security.md            links: user.md
    runtime_configuration_definitions_and_help_controls.md  links: buildvectors.md
    vdisk_ram_dbf_and_transient_storage.md                  links: vdisk.md

Exact correspondence, and it decomposes the 22 cleanly:

    19  links from PUBLISHED sections to pages that exist on main and in
        staging, and are untracked on development       -> branch defect
     3  links from UNPUBLISHED sections to pages that exist nowhere, on any
        branch, in staging, or on the site              -> real content debt

USER, BUILDVECTORS and VDISK are the only genuinely missing pages, and each is
the natural companion of a section that has never been published. That is three
pages of work, not twenty-two.

## What is still wrong on main

    reader command links on origin/main : 164
    reader command links on HEAD        : 164
    the two lists                       : identical
    does either reader link use.md      : no

Both readers link the same 164. On main, where use.md exists, the reader still
does not link it. So on main those 19 pages are orphans: present on disk, linked
by the sections, unreachable from the reader.

That is the mechanism the first draft should have named:

    tools/manualgen/manualgen_lib/command_reference_candidate.py:427
        links = _extract_command_links(reader_path.read_text(encoding="utf-8-sig"))
    tools/manualgen/manualgen_lib/command_reference_candidate.py:525
        expected_pages = len(links)
        if expected_pages != 164:
            findings.append(f"EXPECTED_164_LINKS:{expected_pages}")

The candidate page set is the set of command links already present in the
accepted reader, and 164 is hardcoded. A command the reader never links can
never get a page, no matter how completely the harvest and the disposition
cover it. That is why the sections know about 183 and the reader knows about 164,
and it is why the number 164 survived a branch that is 19 pages short.

The earlier draft blamed R127's `--expected-topic-key` allow-list. That belongs
to a different generator, `build_postbaseline_supported_command_pages.py`. It was
not the cause of anything measured here.

## The harvest and the contracts are not at fault

Checked, because the obvious suspicion was that the navigation verbs were never
collected:

    HELP_HELP_TOPIC.csv                          contains DOT|USE, DOT|SELECT,
                                                 DOT|LIST, DOT|WORKSPACE and the rest
    manual_section_factory_approved_topics.csv   all 21 are INCLUDE_BASE_CANDIDATE
                                                 / SUPPORTED_BASE_SHELF
                                                 / 01_developer_command_reference
    help volume                                  WORKSPACE 638 lines, USE 166,
                                                 USER 163, LIST 127

The harvest has them. The disposition approves them. The 479 approved topics are
simply not the page-selection input, despite looking like they would be.

## The website is not a layer here

`content/docs/dottalk/command-reference.mdx` states in its own prose that it
leads with a snapshot "without duplicating generated command pages into the
website repository". Measured: 0 references to `command_reference_v1/commands`
across all 13 site `.mdx` files. The website never carries per-command pages, so
it cannot be missing them.

## Why this does not block the apply

All 22 gap rows carry `introduced_by_gate4 = 0` and disposition
`PREEXISTING_STANDALONE_SOURCE_GAP_HELD_FOR_RECONCILIATION`. Gate 4 neither
creates nor repairs them. The apply is correct on either branch.

## The proxy family, fifth sighting

The lane has now named this shape five times: a check that cannot answer the
question put to it, and reads as coverage because it is green. Here the ledger
column is `present_in_accepted_reader_destination_set`, which is a true and
useless fact -- it asks whether the reader links the destination, when the
question was whether the destination exists, and on which branch. A column
named `destination_file_exists_on_this_branch` would have caught all of this in
July.

## Remedies

    1  Track the section files on development, or state in writing that
       sections/sections is generated output that is deliberately untracked and
       make the gates say so. Twenty-eight untracked files that the gates read
       is the defect underneath the 22.
    2  Reconcile the 99 commits development is behind origin/main, or record the
       publish-to-main step as a one-way door and stop measuring development
       against publications it does not carry. 803 files is too many to be an
       accident.
    3  Add `destination_file_exists` and the branch name to the standalone
       section link gap ledger. The existing column cannot answer the question.
    4  Write USER, BUILDVECTORS and VDISK command pages, and publish the four
       sections that carry them. This is the only content work in the 22.
    5  Make the reader's link set derive from the approved topic set rather than
       from its own prior links, or record at
       command_reference_candidate.py:427 that the page set is deliberately a
       fixpoint of the accepted reader and that 164 is therefore a floor, not a
       measurement.

## What I got wrong, recorded on purpose

    1  Measured one branch and wrote "none of them exist". 19 of 22 existed in
       two places.
    2  Named R127's allow-list as the cause. Wrong generator.
    3  Did not ask "missing from where" until the owner asked it.

The first two were caught only because of the third.
