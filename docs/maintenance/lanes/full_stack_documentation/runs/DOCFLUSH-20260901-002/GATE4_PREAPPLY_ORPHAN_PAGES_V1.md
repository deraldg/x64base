# Gate 4 pre-apply check: 47 orphan pages, pre-existing

    run       : DOCFLUSH-20260901-002 (v8)
    plan      : MANRUN-20260902T131032Z-A898C760  (PASS_PLAN_ONLY)
    measured  : 2026-09-02, BEFORE apply
    verdict   : **NOT A BLOCKER. Apply is safe.** Pre-existing condition,
                untouched by this plan and by every plan since 2026-07-18.

## What was found

    accepted command_reference_v1/commands/   211 .md files on disk
    planned replacements this run             164 pages
    NOT touched by the plan                    47 pages

The plan is `create=0, replace=168`, with **no DELETE operation**, so those 47
survive an apply unchanged.

They are not retired commands. Measured against the current 666-topic harvest,
all of these are live topics that received no page this run:

    AREA, BOTTOM, ECHO, FIND, GO, GOTO, BROWSE, BUILDVECTORS, DEFCMD, FORMULA
    (sample of the 47)

## Why it is NOT a regression, checked before concluding

The first read was "the pipeline is generating fewer pages than it should, and
applying would leave the manual half-updated." That was wrong, and the check that
settled it was the page count of every prior candidate run:

    MANRUN-20260718T034514Z   164
    MANRUN-20260718T034627Z   164
    MANRUN-20260718T034751Z   164
    MANRUN-20260718T042750Z   164
    MANRUN-20260723T041448Z   164
    MANRUN-20260728T023751Z   161
    MANRUN-20260728T024632Z   161
    MANRUN-20260728T033919Z   164
    MANRUN-20260902T125956Z   164
    MANRUN-20260902T130018Z   164   <- this run

**164 is the stable, by-design selection**, and has been since July. The command
reference deliberately covers a dispositioned subset (164 of 666 topics), not
every topic in the store. So the 47 are accumulation from a pre-July era when a
different selection was generated, and every Gate 4 apply since has left them.

The candidate index links 164 pages, so the 47 are unlinked files sitting beside
the referenced set. Nothing points at them.

## What this means for the apply

    Applying REFRESHES the 164 pages the pipeline owns.
    Applying does NOT create, worsen, or resolve the 47.
    The condition is identical before and after.

Proceeding is correct. Blocking on this would have held a good apply for a
condition it neither causes nor touches.

## The real question, for a later lane

Whether those 47 should be deleted, regenerated, or deliberately retained is a
manual-assembly decision nobody has taken. Three things are true and unreconciled:

    live pages on disk                  211
    pages the pipeline generates        164
    command_reference_pages on the site 183   (documentation-progress-v1.json)

Three numbers for one thing, in three places -- the lane's own failure signature.
The 183 was not investigated here and should not be assumed comparable; it may
count something different again, which is exactly the trap this session hit four
times. It is recorded as an open question, not a finding.

**Recommended:** a delete or retention pass belongs with the disposition-
derivation lane, where the selection that produces 164 is decided. Not this run.
