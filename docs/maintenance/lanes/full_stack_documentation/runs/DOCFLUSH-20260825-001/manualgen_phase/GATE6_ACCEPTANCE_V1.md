# Gate 6 -- the Phase 6 manual candidate, ACCEPTED as a candidate

    Run           : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Gate          : 6. Manual candidate acceptance. **NO publication replacement.**
    Authorization : member.derald, 2026-08-26 -- "gate 6 accept"
    Also ruled    : the manuals are treated COLLECTIVELY for now (section 2)
    Status        : ACCEPTED (candidate), review-needed.

## 1. What is accepted, bound by hash

    run id                MANRUN-20260826T012054Z-B9F8B8BD
    created_utc           2026-08-26T01:20:57Z
    manualgen_version     1.2.0-docflush
    dry_run_sha256        7F6C03239F0E1DF55B95EDAC52196569D2EE2958D9D9036B83A6C025F8410928
    current_combined      5ADFCDED44B4C7F4B0938EAC526FA466A5C4BB48FD59BFC85DA582E91E7F2C53
    sections / media / appendices     25 / 19 / 13
    harvest               14/14 files, candidate workspace, manifest sha256
                          91b3f4a242fe274851f1b64e490fc396fbf90be792c47151cceb001440e3b688

    boundary_fail_rows    0        <- THE ACCEPTANCE CONDITION, and it is met
    validation_fail_rows  1        <- PYTHON_312 on the sandbox's 3.10, named
                                      by re-running validate_inventory directly;
                                      24 of 25 PASS, every harvest check green
    postbaseline selector selected 1 key, DOT|BUILD, PASS_CANDIDATE_ONLY,
                          wrote nothing

All nine boundaries PASS: no publication rebuilt, no published workspace
mutated, no media touched, no x64base tables created, no C++ written, no
HELP/META/CMDHELPCHK mutation.

**The harvest is the substantive change this candidate carries.** The canonical
`harvested/` was the stale 12:18 export (460 commands / 665 topics / 29,262
lines) against a live store of 462 / 667 / 29,268. A build against it would not
have known `DOT|BUILD`, `FOX|FILE`, or the corrected `BUILD VECTORS` /
`BUILD INFO` status. The re-export to a candidate workspace matches the live
store on all six HELP tables.

## 2. THE OWNER'S RULING, recorded because it changes what this gate means

Asked which workspace is the manual, the owner corrected the question:

> "my workspace is the manual? the website should just link to the manual /
> there is more than one manual / we have not matured the manual in long time
> so treat it collectively for now and we will harden it"

Three things follow, and the readiness review was wrong on the first:

**a. A workspace is not a manual.** `PHASE7_READINESS_REVIEW_V1.md` section 6
made "rule which workspace is the manual" the first blocker. That framed an
assembly directory as the artifact. A workspace is where an assembly happens;
the manual is what a reader reads.

**b. There is more than one manual, and the review only looked at one.** On
disk:

    docs/manuals/developer/    4,208 markdown files
    docs/manuals/student/          1
    docs/manuals/user/             1

The four "manuals" the review compared were four **developer**-manual assembly
variants. Student and user are single stubs. *"We have not matured the manual in
a long time"* is measurable, and that is the measurement.

**c. Collective for now; hardened later.** So Gate 6 accepts the candidate
WITHOUT resolving which developer-manual workspace becomes canonical. That
resolution is deferred by ruling, not overlooked -- and this document is where a
later hardening pass should start.

**d. The website LINKS to the manual; it does not project it.** This retires
"website projection" as a fifth state to reconcile in the pointer review. A link
needs one stable address, which is a far smaller obligation than a projection
kept in sync -- and it means the manual's shape can be hardened without the
website moving in step.

## 3. What acceptance does NOT authorize

    no publication replacement       the dry run wrote nothing and this
                                     changes nothing about that
    no promotion to main             dev-tree only
    no website publish               out of scope for v6 by owner ruling, and
                                     now a LINK rather than a projection (2d)
    no page generation               the R127 generator ran --dry-run only;
                                     writing pages is a separate act
    no canonical-workspace ruling    deferred by 2c

## 4. Carried, and now attached to an accepted candidate

1. **The canonical `harvested/` is still stale.** Accepted against a CANDIDATE
   harvest. Re-exporting the canonical one is E5 of the Phase 7 -> 8 entry check
   and is one command.
2. **`dry_run_hash_matches_current_combined` can never be 1** -- published
   manual is CRLF, the assembler writes LF. Strip `\r` and the delta is 123
   lines in two hunks.
3. **The 117-line tail**, re-diagnosed in the readiness review: the MDO-261 and
   MDO-270 blocks are absent from a rebuild of `media_section_v1`, but
   `..._man_cli_reference_v1` carries 29 H1 sections and no MDO markers, which
   is what it looks like when insertion markers have been resolved into real
   sections by a later workspace. **Not a content-loss risk. A which-one-is-it
   risk**, and 2c defers it deliberately.
4. **`FOX|FILE` cannot be paged.** `supported()` filters `CATALOG == "DOT"`, and
   FOX|FILE has no DOT sibling for composition to attach to. The runnable ask is
   small: make the filter REPORT what it drops.

## Good Neighbor

    What changed  : this document. Nothing was re-run to produce it; the hashes
                    are from the dry-run manifest already on disk. No workspace,
                    no publication, no media, no store.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : member.derald, 2026-08-26, "gate 6 accept", plus the
                    collective-manual ruling quoted in section 2.
    Verify        : the run's build_dry_run_manifest.json carries every figure in
                    section 1; the nine boundary rows are in its `boundary` array.
                    Section 2b: ls docs/manuals/*/ and count .md per manual.
    Undo          : delete this document; the candidate remains, unaccepted.
