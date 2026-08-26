# Gate 7 -- the dev-tree run closes

    Run           : DOCFLUSH-20260825-001 (flush v6), opened 2026-08-25
    By            : member.ai.claude.cowork (ALPHA), for member.derald
    Lane          : full_stack_documentation (AIF-068)
    Authorization : member.derald, 2026-08-26 -- "gate 5 bind", "gate 6 accept",
                    and the collective-manual ruling recorded in
                    `manualgen_phase/GATE6_ACCEPTANCE_V1.md` section 2
    Status        : **CLOSED** (development tree). review-needed.
    NOT claimed   : no public promotion, no push to `main`, no website publish.

## 1. The six columns Gate 7 requires

    dev-refresh   HELP store rebuilt 2026-08-26: exe 01:00:12 -> LEGACY 01:06:10
                  -> store 01:11:28. 462 commands, 2,368 arg rows, 29,268
                  HELP_LINE rows, 667 topics -- every figure read from the DBFs,
                  never from a console.
    candidate     Phase 5: three import candidates + facts + compare, five
                  SHA-256 in GATE5_BINDING_V1.md.
                  Phase 6: MANRUN-20260826T012054Z-B9F8B8BD, dry_run_sha256
                  7F6C0323..., boundary_fail_rows=0.
    promotion     NONE. No candidate was promoted, no page written, no
                  publication replaced, no metadata imported.
    staging       31 files, all of them RECORDS THAT ALREADY EXISTED ON DISK
                  AND HAD NEVER BEEN STAGED. Section 3.
    commit        every commit in this run is the maintainer's PowerShell.
                  Section 6.
    push          NONE from this run. Public promotion and website publish
                  belong to their own lanes and were not entered.

## 2. What v6 set out to do, and what it did

The charter was GIGO: *"improving the process from start to phase 6 through
normalization and refactoring will improve the web phase"*, with the website
deliberately unrun. Gate 0 through Gate 6 all ran.

**The run found more in the machinery than in the documents**, which is the
outcome the charter was hoping for:

    six proxies that cannot answer the question put to them
    three false ceilings that made runnable work read as blocked
    a 117-line manual gap, then re-diagnosed twice
    a live contract on disk and outside history
    four developer-manual variants and a pointer naming the smallest
    a `dispatch_reachable` column false on all 1,083 rows

Each is recorded in its own document in this run directory or in the AIF intake
queue. **None was prescribed a repair here** -- reporting a defect is this
lane's job; the fix belongs to the area that owns the code.

## 3. Staging: 31 records that were never in history

Gate 7's five-state pointer review (`PHASE7_READINESS_REVIEW_V1.md`) found every
authority in the manual chain UNTRACKED AND NOT IGNORED -- never staged, so no
diff, no blame, no rollback for the record that says which manual is current.

**Under the owner's collective ruling this stopped being a decision.** Staging
what exists is RECORDING, not CHOOSING, so it no longer waits on which manual
becomes canonical.

    3   accepted_artifacts/     ACTIVE_PRIMARY_READER_ARTIFACT.txt and the two
                                artifact records it stands beside
    15  accepted_manifests/     ACTIVE_MANUALGEN_MANIFEST.txt, the canonical
                                manifest, and twelve MDO acceptance records
                                (MDO-207 through MDO-220)
    10  publication_ascent_preflight_v1/   the 2026-07-18 authorization packet,
                                including CANONICAL_APPLY_AUTHORIZATION -- the
                                maintainer's own signed authority for the
                                canonical apply, with its plan-manifest and
                                mutation-ledger SHAs
    3   published/*.md          three developer-manual combined artifacts

**THE GATE CHOSE THE SCOPE, NOT ME**, and that is the part worth keeping.
`check_cited_paths.py` was run after each addition and walked the authority
chain in three bounded steps: an acceptance record widowed its authorization;
the authorization packet widowed the manuals it cites; staging those closed it.

    cited-paths: 22 document(s), 7 path(s) cited, 7 tracked -- OK

A sweep would have taken 670 untracked files under `manualgen/`. The chain took
31, and every one is reachable from a citation.

**DEFERRED ON PURPOSE:** the fourth developer-manual variant,
`..._man_cli_reference_v1/` (185,993 B, 29 H1 sections -- the largest, and the
one that appears to have resolved the MDO-261/270 insertion markers into real
sections). Nothing staged cites it, so no gate requires it, and it belongs to
the hardening pass that resolves the collective. Also unstaged and unswept: the
remaining ~640 untracked files under `manualgen/` (review packets, work orders,
candidate manifests, assembly sources). Named so the omission is a decision.

## 4. Gate 7 -> 8 entry rows, as they stand

Phase 8 is OUT OF SCOPE for v6. Recorded because the rows are cheap and the
state is useful to whoever opens it.

    E1  dev-tree run closed at Gate 7      **PASS -- this document**
    E2  HELP current + CMDHELPCHK PASS     UNRUN (needs the engine, host)
    E3  contracts 100%, catalog fallback 0 contracts 100.0% uncovered=0 PASS;
                                           catalog UNRUN (site repo, out of scope)
    E4  refcheck_v1 + normcheck_v1         **PASS**, both run 2026-08-26
    E5  harvest re-exported after build    PARTIAL -- candidate workspace matches
                                           the live store on all six HELP tables;
                                           canonical `harvested/` still the stale
                                           12:18 export. One command.
    E6  command-catalog.mdx regenerated    OUT OF SCOPE
    E7  store backup + rollback named      **PASS** -- help.bak-20260825-180609
    E8  owner authorization per mutation   N/A -- nothing mutating was proposed

**E5 is the one to fix first** when v7 opens; the cookbook flags it as the row
that usually fails, and it is now the only PARTIAL.

## 5. What v6 leaves for v7, ranked

1. **A content-level assertion in the preflight.** 6' is a membership check and
   says so; the id-stripped content diff is what saw the substantive half of
   this run and is still a hand-run workaround.
2. **The rehearsal harness.** Build every program outside the tree, run the
   push, emit predictions, diff against the owner's run.
   `AI_PUSH_AUTOMATION_WHAT_THE_SANDBOX_CHANGES_V1.md` section 2.
3. **A stated-impossibility check** -- flag any routing document asserting
   "cannot build / cannot run" with no adjacent measurement date. Would have
   fired on all four of this run's ceilings.
4. **Harden the manual**, per the owner's ruling: resolve the developer-manual
   variants, and decide what student and user manuals (one markdown file each)
   should be. The website LINKS to the manual rather than projecting it, so this
   can be done without the website moving in step.
5. **Five open rulings** -- the multiword registrations, `dispatch_reachable`,
   the CRLF/LF hash, the DOT-only page filter, the `!= (3, 12)` version guard.
6. **`validate_metadata_system_registry.py` FAILs on 10 of 24 systems and
   nothing runs it.** Not a v6 finding by scope, found in passing, and the
   loudest unwatched check in the tree.

## 6. Sandbox conduct, measured this run and worth carrying

    read-only git      fine, with --no-optional-locks
    git add            WORKS, and leaves a lock it CANNOT UNLINK -- so a second
                       add in the same session fails until the lock is moved
                       aside. One add with all paths, or clear between adds.
    git commit         NOT from a sandbox: the pre-commit hook runs
                       repository_role_guard then prepush_gate, minutes against
                       a per-call ceiling of seconds
    orphaned locks     `mv` aside; a sandbox cannot delete
    build and run      YES, all of it -- and that correction is now on the
                       route an arriving agent walks, not only in the documents
                       this run happened to trip over

**And one method note against my own work in this section.** The `git add` that
staged the fourth manual returned exit 0 and did not stage it; the failure was a
warning, not an error, and an earlier add in the same loop had its stderr
filtered by my own pipeline. **I read silence as success.** That is *an empty
result is not a measurement* -- already on record in this lane, in a document I
had read the same night.

## Good Neighbor

    What changed  : this document, plus 31 files STAGED (not modified). No
                    manual was edited, no pointer moved, no workspace assembled,
                    no candidate promoted, no metadata imported.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : member.derald, 2026-08-26 -- "gate 5 bind", "gate 6 accept",
                    the collective-manual ruling, and "yes" to staging the
                    authorities and drafting this closeout.
    Verify        : check_cited_paths.py -- expect 7 cited, 7 tracked, OK.
                    git log --stat for the commit carrying this document lists
                    all 31 additions.
                    E4: refcheck_v1.py and normcheck_v1.py, both PASS.
    Undo          : `git rm --cached` the 31 restores them to untracked; delete
                    this document to reopen the run. Nothing else to reverse --
                    v6 promoted nothing.

---

## 7. The house-style block, and why the fixer is the WRONG tool here

The first attempt at this commit was BLOCKED, correctly, by `check_house_style.py`:

    BLOCKED -- non-ASCII in added documentation lines

Four files, one `U+FEFF` byte-order mark each, no other offence:

    accepted_manifests/MDO-219_ACCEPTED_MEDIA_ANCHOR_MANIFEST_v1.md:1
    accepted_manifests/MDO-220_ACCEPTED_MEDIA_SECTION_INSERTION_v1.md:1
    published/..._media_section_v1/..._media_section_v1.md:5
    published/..._manual_mutation_cycle_v1/..._media_section_v1.md:5

**The gate is not wrong and neither is its reasoning.** Its own message names
the cause exactly: *"staging a previously UNTRACKED file makes every one of its
lines an added line, so the whole file must be clean, not just your edit."*
Importing history into history subjects it to today's house style. That is a
real consequence of Gate 7's staging and it was not anticipated.

**`ascii_normalize.py --apply` MUST NOT be run on these four.** Measured, not
argued:

    current_combined_sha256, recorded in GATE6_ACCEPTANCE_V1.md and in the
    dry-run manifest, for ..._media_section_v1.md:
      5ADFCDED44B4C7F4B0938EAC526FA466A5C4BB48FD59BFC85DA582E91E7F2C53
    the file on disk hashes to exactly that.        <- identity confirmed
    with the BOM stripped it hashes to
      89B6F551D1B8658670846083847B05AAD0AA091A7F2F535A2BB4220949638382

**Normalising that file would falsify a hash the maintainer accepted two commits
ago.** The other three are the same instinct one step milder: MDO-219 and
MDO-220 are ACCEPTANCE RECORDS, and editing the bytes of a record of what was
accepted, to satisfy a style rule written afterwards, destroys the only property
that makes it a record.

**So the exception the gate itself offers is the correct route**, and it is the
case that message was written for: *"or `git commit --no-verify` if you are
deliberately importing text."* This is deliberately importing text.

**WHAT `--no-verify` COSTS, stated rather than glossed.** It skips EVERY hook,
not just house-style: `repository_role_guard.py` and `prepush_gate.py` do not
run. The compensating evidence is that they DID run, on the blocked attempt, and
every one of them passed in that same output:

    repository-role-guard  PASS, development worktree on development
    AIF-collision gate     PASS, 128 rows / 128 distinct
    check-version-coherence OK, one authority
    mandatory-tracked      PASS, 63 documents and 10 scripts
    cited-paths            OK, 15 cited / 15 tracked
    check-seed-budget      PASS, 7,326 B of 8,192 B
    R-number gate          PASS
    check-aif-claimed      nothing in scope
    house-style            BLOCKED  <- the only failure, and it is these 4 BOMs

**The bypass is therefore narrow and evidenced, not blind.** If any other gate
had failed in that run this commit would not be proposed.

**Recorded for whoever hardens the manual:** these four BOMs are now IN history
and will be flagged on every future change to those files. The right time to
strip them is when the collective is resolved and the affected hashes are
re-bound in the same act -- not before, and never as a lone cleanup. That is a
hardening task, and it is the second one this closeout has handed forward.
