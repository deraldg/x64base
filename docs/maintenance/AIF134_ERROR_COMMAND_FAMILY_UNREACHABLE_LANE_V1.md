---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-011
  recorded_at_utc: 2026-08-27T10:50:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: COWORK-20260826-002
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 372c5834f
  authorization:
    requested_by: maintainer (member.derald), in-session, "open the lane" then "then do it"
    scope: >
      Lane charter for AIF-134. Diagnosis only. No source change is authorized
      by this document; implementation requires a separate owner instruction.
  report:
    path: docs/maintenance/AIF134_ERROR_COMMAND_FAMILY_UNREACHABLE_LANE_V1.md
    kind: lane-charter
---

# AIF-134 -- the ERROR command family is registered and unreachable

    lane      : AIF-134
    claim     : coordination/aif/AIF-134.claim
    intake    : docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md
    run       : COWORK-20260826-002
    owner     : member.derald
    steward   : member.ai.claude.cowork
    sibling   : AIF-131 (same defect, fixed for BUILD in 90e5dce0b)
    status    : RUNTIME-PROVEN 2026-08-27; CORRECTED 2026-09-01 (see top:
                already reported by stack_audit_v1 DEAD_REG; FIVE keys, not three);
                awaiting owner ruling on the fix
    opened    : 2026-08-27 (host clock)
    proven    : 2026-08-27, build Aug 27 2026 09:47:07 (9e1376e1 dirty)

## CORRECTION 2026-09-01 -- THIS WAS ALREADY KNOWN, AND IT IS FIVE KEYS NOT THREE

**`tools/fullstack_docs/stack_audit_v1.py` reports this defect on every run.**

    DEAD_REG/MULTIWORD_KEY: 5 registry key(s) contain a space and can never be
    dispatched -- shell_dispatch keys on the FIRST TOKEN only. They read as
    working registrations and are dead:
        ERROR CLEAR, ERROR STATUS, ERROR TEST, SET RELATION, SET UNIQUE

This lane was opened without running that tool first. It is the "re-derived a
ruling already recorded" failure `CLAUDE.md` opens by warning about, and the
sections below were written as discovery when they were rediscovery. Recorded
here rather than quietly amended, because the discovery claim is the part that
was wrong.

**TWO SUBSTANTIVE CORRECTIONS, not just attribution:**

1. **The family is FIVE keys.** Section "The measurement" below dismissed
   `SET RELATION` and `SET UNIQUE` as OK because bare `SET` is registered. The
   authority draws the finer line and it is the right one: the KEY is dead even
   where the FUNCTION remains reachable through the `SET` router. A registration
   that never fires is a false statement about how the command is reached,
   whether or not another path happens to work. Any fix must cover all five.
2. **`BUILD INFO`, added to `include/dottalk/dotref.hpp` earlier in the same
   session as this lane, is itself flagged** by the same tool under
   `DOTREF_COV/SUBCOMMAND_ONLY`: typeable through the router, but never
   independently registered, so it has no contract, no SYSCMD row and no HELP
   topic. Documenting it was necessary and not sufficient.

**WHAT THIS LANE STILL CONTRIBUTES,** and why it is corrected rather than closed:

- The **runtime proof** (2026-08-27, one process, `Unknown command: ERROR` beside
  a green `ERROR_STATUS`) is evidence a WARN line does not carry. The second arm
  in particular -- showing the handler is healthy and only the spelling is
  unreachable -- is what separates "the ERROR family is broken" from "the
  published spelling is unreachable."
- The **AIF-131 sibling analysis** stands: `90e5dce0b` wrote the general rule
  into its own comment and did not sweep for other parentless families.
- The **ruling still needed** (router vs. delete the spaced registrations) is
  unchanged, and now applies to five keys.

## Authorization

Maintainer, in session: "open the lane", then "then do it". This charter is
**diagnosis only**. Section 7 names two candidate fixes and does not choose
between them: that is an owner ruling, not a steward's call.

## Objective

`ERROR CLEAR`, `ERROR STATUS`, `ERROR TEST` -- and, per the correction above,
`SET RELATION` and `SET UNIQUE` -- are registered as whole multi-word keys, and
the shell dispatches on the FIRST whitespace token only. No bare `ERROR` router
exists at all; `SET` has a router, but the spaced KEYS still never fire. So five
registrations can never be reached as written, while `dotref` publishes the ERROR
three as implemented and supported.

## The measurement

Dispatch reads ONE token (`src/cli/shell_api.cpp:298`):

    tok >> cmd;

So a registry key containing a space is only reachable if the bare first word is
ALSO registered and routes its own next token. Measured over all 239 registry
keys in `src/cli/shell_commands.cpp`:

    DEAD  'ERROR CLEAR'     no bare 'ERROR' -- nothing reaches the handler by this spelling
    DEAD  'ERROR STATUS'    no bare 'ERROR'
    DEAD  'ERROR TEST'      no bare 'ERROR'
    DEAD  'SET RELATION'    bare 'SET' IS registered and routes, so the FUNCTION is
                            reachable -- but this KEY never fires. First read of
                            this table called that OK. It is not: the registration
                            is a false statement about how the command is reached.
    DEAD  'SET UNIQUE'      same

    Corrected 2026-09-01 against stack_audit_v1 DEAD_REG/MULTIWORD_KEY, which
    counts all five.

Registrations, both spellings, twelve lines apart in the same file:

    shell_commands.cpp:556-558   ERROR_CLEAR / ERROR_STATUS / ERROR_TEST   reachable
    shell_commands.cpp:562-564   "ERROR CLEAR" / "ERROR STATUS" / "ERROR TEST"   dead

Both spellings route to the same three handlers, so **the capability is not
lost** -- only the spaced spelling is. That is precisely why this survived:
anyone who tried the underscore form saw it work.

The catalog publishes all six (`include/dotref.hpp:1108-1125`), and CMDHELP
renders the three spaced rows at ids 384-386 as `implemented=yes supported=yes`.
Three of those six rows describe something no user can invoke.

## Why this is the AIF-131 defect and not a new one

AIF-131 recorded the identical shape for `BUILD VECTORS` / `BUILD INFO`, and it
was fixed on 2026-08-25 in `90e5dce0b`, "BUILD is a router, not an unknown
command". That commit's own message records the runtime proof: `build vectors`
answered `Unknown command: BUILD` while `BUILDVECTORS` worked.

The fix was a bare `BUILD` router that reads its own next token
(`shell_commands.cpp:517-528`). Its inline comment states the general rule --
"SET works because SET itself is registered and reads its own next token; BUILD
had no such parent" -- and the ERROR family is the case that rule does not
cover. **The rule was written down and the sweep was not done.**

This lane is therefore a sibling, not a discovery. What is new is the sweep:
after this, the invariant "every multi-word key has a bare-first-word router" is
measured across all 239 keys rather than asserted for one family.

## Scope

- `src/cli/shell_commands.cpp` -- the ERROR registrations
- `include/dotref.hpp` -- the three spaced rows, if the ruling removes them
- HELP regeneration, if dotref changes

## Out of scope

- The underscore spellings. They work and are not in question.
- The underscore spellings and the working `SET` router path. Neither is in
  question; what is in question is the five dead KEYS.
- Any command family beyond those five. `stack_audit_v1 DEAD_REG` is the
  authority on that list and reports exactly five at this baseline; if a sixth
  appears it is a new finding against the invariant, not a reopening.

## Proof -- RUNTIME-PROVEN 2026-08-27

Run by the maintainer on the host, both arms in ONE process:

    ./datarun.ps1 -CommandLines 'ERROR STATUS','ERROR_STATUS' *> tmp\aif134_before.log

    dottalk++ v0.6 (2026-08-27, 9e1376e1 dirty)  (Aug 27 2026 09:47:07)
    ...
    . Unknown command: ERROR          <- arm 1: ERROR STATUS   (spaced)
    . Last Error:                     <- arm 2: ERROR_STATUS   (underscore)
      Severity : success
      Facility : unknown (0x0)
      Number   : 0
      HRESULT  : 0x00000000
      Message  : OK

**Arm 1 red, arm 2 green, same binary, same process.** The prediction was
written before the run and the wording came back identical to AIF-131's
`Unknown command: BUILD`.

Both arms were required and the second is the one that carries the argument: it
shows `cmd_ERROR_STATUS` is healthy and reachable, so the defect is purely the
spelling the catalog publishes. A single red arm would have been consistent with
"the ERROR family is broken", which is not what is wrong.

The transcript lives at `tmp/aif134_before.log`, which is **gitignored**
(`.gitignore:266`). That is why the decisive lines are transcribed above rather
than cited: evidence behind a gitignored path is evidence a later reader cannot
check, and the seed treats uncaptured evidence as unproven. The log is
reproducible from the one command above.

Capture note: `*>` redirection was used. NEVER capture proof with
`DOTSCRIPT ... OUT` (AIF-081: it drops everything routed through `cli::cmdout`
-- 42 lines against `SET ALTERNATE`'s 89, measured 2026-07-31).

## The ruling this lane needs

Two defensible fixes, and they differ in what they say about the product:

**(a) Add a bare `ERROR` router.** Mirrors `90e5dce0b` exactly, makes the
published catalog true, and keeps both spellings. Cost: `ERROR TEST` is
documented as `ERROR TEST [<args...>]`, so the router must forward its remaining
tokens rather than swallow them -- the `BUILD` router had no arguments to
forward and is not a complete template on that point.

**(b) Delete the three spaced registrations and their dotref rows.** Declares
the underscore spellings canonical. Smaller, and removes three dead
registrations rather than reviving them -- but it withdraws a documented surface,
which is a product decision.

Steward's note, not a recommendation: (a) is consistent with what was already
ruled for BUILD one day earlier, and consistency across a family is usually
worth more than the smaller diff. The owner may weigh the spellings differently.

## Housekeeping owed at close

- DONE 2026-08-27: runtime proof captured, both arms, and the tier upgraded from
  source-evidenced to runtime-proven. Decisive lines transcribed into the Proof
  section because the log path is gitignored.
- If the ruling changes `dotref.hpp`, a rebuild is REQUIRED before
  `cmdhelp build` will show it -- the header is compiled into the exe.
- A standing check that every multi-word registry key has a bare-first-word
  router, so the third instance of this defect is caught by a gate rather than
  by a reader.

## Provenance note

Found on 2026-08-27 while re-onboarding, not while looking for it. `TIER0_STATE`
surfaced AIF-131; verifying my own earlier `dotref` change against that lane
showed the `BUILD` router had already landed, and checking whether its rule
generalized produced this. The allocator misfire that preceded the claim
(`claim-aif` issuing AIF-043, a live lane) is recorded separately in the intake
row and is not part of this lane.
