# Handoff -- the full-stack documentation life cycle, end to end

    from        : member.ai.claude.cowork
    for         : any session picking up the full-stack doc push cold
    owner       : member.derald
    doctrine    : labtalk/ai_portal/AI_TIER1_SEED_V1.md, then
                  docs/maintenance/lanes/full_stack_documentation/README.md
    command
    authority   : docs/maintenance/lanes/full_stack_documentation/
                    FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md
    posture     : the pipeline EXISTS and is mature -- 9 gates, ~50 tools, its own
                  contracts. This file is a MAP of it, not a copy of it.
    date        : 2026-08-26 (host clock)
    clock note  : the Linux sandbox clock reads 2026-08-24, the Windows host
                  reads 2026-08-26. TWO DAYS APART, measured. The host is
                  authoritative -- it is what stamps file mtimes and build
                  banners. An agent that dates an artifact from `date` in the
                  sandbox will misdate it by two days, which is how the
                  2026-08-21 handoff in this directory acquired its own date
                  note. Take dates from the host, or from a file mtime.

This is a **pointer document**. It deliberately does not restate the cookbook's
commands. Two shims that restate will diverge, and in this tree they already have
(AIF-082 6.8). The cookbook is refined every run; a copy of it here would be
authoritative-looking and wrong within two runs.

What is here is the SHAPE -- what each gate proves, what it must never do, and
the failure mode that gate exists to catch. Read this to know where you are.
Read the cookbook to know what to type.

Verify every claim below rather than trusting it. Section 6 is the only part
carrying runtime-proven evidence from the session that wrote this; everything
else is source-evidenced and could have drifted since.

---

## 0. Orientation, in order

1. `labtalk/ai_portal/AI_TIER1_SEED_V1.md` -- the five questions. If you cannot
   answer all five, keep reading it before you touch this lane.
2. `docs/maintenance/lanes/full_stack_documentation/README.md` -- the authority
   order and the pointer set.
3. `FULL_STACK_DOCUMENTATION_NORTH_STAR_V1.md` -- why the pipeline exists.
4. `FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md` -- doctrine and gate definitions.
5. `FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md` -- run-it-now commands.
6. This file, for the map and the traps.

---

## 1. The one idea the whole pipeline is built on

    Runtime proves.
    Source defines.
    HELP explains.
    Metadata organizes.
    CMDHELPCHK validates.
    SelfDoc preserves provenance.
    Manualgen assembles reviewed views.
    Publication exposes reviewed snapshots.

Read it as a chain of custody, not a list of components. Every artifact
downstream must be DERIVED from the one above it, never hand-copied alongside
it. The recurring defect in this repo is a hand-maintained copy of something
that already had an authority -- see section 6.

The corollary that decides most design questions: **if two places must agree,
one of them has to ask the other.** A generator is correct. A synced copy is a
future divergence with a date on it.

The BBOX model is the same idea in teaching form -- DATA IN, PROCESSING,
INFORMATION OUT, CONTROL -- and it is queryable from the running engine
(`BBOX MODEL`, `BBOX LANES`, `BBOX <LANE>`). Use it to orient a newcomer; it is
faster than any doc because it cannot be stale relative to the binary.

---

## 2. The life cycle: nine gates

Gates 0 through 7 run in the DEVELOPMENT tree and close there. Phase 8 is
publication and is a SEPARATE lane -- a dev-tree run that claims a public push
has overrun its own boundary.

Each gate below gives: what it proves, what it must not do, and the failure it
exists to catch.

### Gate 0 -- run envelope

    PROVES     a run exists, with id, owner, branch, scope
    NEVER      mutates anything
    CATCHES    work that cannot be audited because nobody wrote down what it was

Run directory: `docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-YYYYMMDD-NNN`.
Look at the existing run directories before choosing an id.

### Gate 0.5 -- contract coverage (the owner calls this "step 1")

    PROVES     every source file carries @dottalk.file; every command file
               carries @dottalk.usage; external-process callers carry
               @dottalk.external
    NEVER      proceeds on partial coverage
    CATCHES    THE FOUNDATIONAL FAILURE. A file without a contract is not
               "undocumented" to the generators -- it is INVISIBLE. The pass
               completes, reports success, and silently covers less than last
               time.

Targets: `source_census` 100 percent, catalog `fallback 0`.

Tools: `tools/fullstack_docs/docpush_preflight.py` (the gate),
`source_census.py` (the census), `tools/selfdoc/audit_contracts.py` (the
narrower three-question audit, including dotref registration).

This is where the owner's stated workflow starts: *"source file self
documentation is our first source of truth in our fullstack push, step 1."*
Everything downstream is a projection of what this gate admits.

### Gate 1 -- inventory and classify drift

    PROVES     every command identity is reconciled across REGISTRY, CATALOG
               (SYSCMD), HELP (the *ref catalogs), and REFLECTION
    NEVER      silently replaces a stronger authority with a weaker one --
               it STOPS at review rows
    CATCHES    phantoms (a dotref entry for a command that does not exist) and
               duplicates (one command with rows in disagreeing authorities)

Do not hand-roll a crosswalk. The lane has five tools for this and they encode
prior findings.

### Gate 2 -- pre-refresh runtime baseline

    PROVES     what the system said BEFORE you changed it
    NEVER      changes anything
    CATCHES    the improvement you cannot demonstrate because you never
               recorded the starting point

Bind SHAs: script, transcript, exe. Read the transcript for mojibake -- source
em-dashes render as a CP437 garble, which is one reason the house is ASCII-only.

### Gate 3 -- reviewed HELP refresh package

    PROVES     the owner authorized a specific mutation with a named rollback
    NEVER      builds
    CATCHES    an unreviewed write to the HELP store

State why, what changed, expected file changes, backup manifest hash, rollback,
post-build checks.

### Gate 4 -- execute HELP refresh and validate

    PROVES     the generators ran and their output improved or held
    NEVER      runs with the daemon holding the store
    CATCHES    a build that silently read a stale catalog

Non-negotiable ordering, all in the cookbook:

- **Stop `DotTalkBBSD` first.** It locks the store. `Stop-ScheduledTask` alone
  is NOT sufficient -- see CLAUDE.md; you need an ELEVATED `Stop-Process`.
- **Back up `dottalkpp/data/help` before building.**
- **LEGACY first, then current.** `CMDHELP BUILD LEGACY`, then
  `CMDHELP BUILD . <ABS src>`. A `dotref.hpp` change REQUIRES the legacy pass.
- **Restart the daemon after.**

Acceptance: reflection PASS; line and topic counts at or above baseline;
targeted topics resolve; LEGACY delta visible.

Downstream derivative, same gate: regenerate the website command catalog and the
regression catalog. Both are GENERATED pages -- never hand-edit them.

### Gate 5 -- metadata candidates

    PROVES     candidate SYSCMD/SYSFUNC/SYSARGS rows exist and are hash-bound
    NEVER      imports into live metadata -- that is its own gate
    CATCHES    a metadata import nobody reviewed

`metacollect` is a separate build (`-DDOTTALK_BUILD_METACOLLECT=ON`). Candidate
CSVs stay gitignored and are bound by SHA, not committed.

### Gate 6 -- manual candidate

    PROVES     an assembled manual candidate exists with row-level lineage back
               to HELP lines
    NEVER      promotes itself to accepted
    CATCHES    a published manual whose provenance nobody can reconstruct

`tools/manualgen/manualgen.py`, a long chain of `build-*-candidate` stages, each
with its own contract doc in the lane directory. Acceptance is a separate,
authorization-bound apply step with a byte-preserved backup and a standalone
rollback command.

Attestations: `docs/manuals/developer/manualgen/accepted_artifacts/`.

### Gate 7 -- review and close the dev-tree run

    PROVES     five pointer states agree -- candidate workspace, accepted
               manifest, active reader artifact, publication manifest, website
               projection
    NEVER      claims a public push
    CATCHES    a run that thinks it published

The closeout must separate dev-refresh / candidate / promotion / staging /
commit / push. Conflating them is how a "done" gets recorded for work that
never left the tree.

### Phase 7 -> 8 entry check

Eight fail-closed conditions before ANY publication. The two most often missed:
HELP/META harvest must be re-exported AFTER the Phase 4 build, and the website
command catalog must be regenerated.

### Phase 8 -- publication ascent

Separate lanes, nine more gates. `development -> C:\x64base -> main -> site`.
Never backward, never hand-edit the same change in two trees.

---

## 3. The four rails

Running through every gate:

1. **Contracts** -- `@dottalk.file`, `@dottalk.usage`, `@dottalk.external` in
   the source. Everything is downstream of these.
2. **Catalogs** -- `dotref.hpp`/`foxref.hpp`/`edref.hpp` (compiled in), SYSCMD
   (live table, authority) with its CSV mirror (shadow, never authority).
3. **Evidence** -- run directories, SHA-bound manifests, transcripts. Regenerable
   CSVs are gitignored and bound by hash rather than committed.
4. **Gates** -- `prepush_gate.py` at commit, `aif_collision_gate.py` for lane
   numbers, `source_policy.py` in CI, the local-path guard for public content.

---

## 4. Where the authoritative data lives

This trips every newcomer. Several obvious-looking sources are decoys; the
skill file `x64base` carries the measured table. The two that matter most here:

- Command prose is in `dottalkpp/data/help/HELP_ARTIFACTS.dbf` (~14k rows), NOT
  `SYSHELP` (8 rows, vestigial -- concluding from it is wrong by two orders of
  magnitude).
- The canonical HELP root is `dottalkpp/data/help`, NOT `dottalkpp/data/dbf/help`,
  which holds a stale snapshot. A tool given the wrong root consumes the stale
  set and reports success. `help_guard_v1.py` exists to catch exactly this.

Read DBFs with `tools/fullstack_docs/dbfread.py`: `t = dbfread.read(path)` then
`t.live`. `t.records` does not exist and `len(t)` fails.

---

## 5. Traps, in the order they will bite you

1. **A rebuild is required more often than it looks.** `dotref.hpp` is a HEADER
   COMPILED INTO THE EXE. Editing it changes nothing until `dottalkpp` is
   rebuilt. `.dts` script work needs no rebuild; catalog work always does.
2. **Check the build stamp before reading any result.** The banner prints it.
   If it did not move, you are reading the previous run again. This cost three
   full help-build cycles on 2026-08-26 before anyone looked at the timestamp.
3. **An absent check and a passing check look identical.** The AIF-118 shape,
   recurring roughly ten times in this tree. Any guard that returns the same
   answer for "fine" and "not looked at" is not a guard.
4. **A green proves nothing until an arm has been shown able to go red.**
   Mutation-test assertions before trusting a suite.
5. **The visible symptom count is not the defect count.** See 6.2 -- five of
   eleven drifted names were visible; six were masked by an unrelated accident.
   Fixing the visible five would have looked complete.
6. **Never `git add -A`.** Concurrent sessions share one tree. Stage explicit
   paths, and keep `-uall` on `git status --short` -- this repo sets
   `status.showUntrackedFiles=no`, so a bare status shows nothing for a file you
   just created.
7. **Sandbox sessions must not run mutating git, and not plain `git status`.**
   It takes `.git/index.lock`, which cannot reliably unlink across the mount.
   Read-only forms are lock-free and allowed.

---

## 6. Measured on 2026-08-26 (runtime-proven unless marked)

Findings from the session that wrote this file. These are corrections to the
pipeline itself, not to its documentation.

### 6.1 dotref.hpp reached CMDHELP only after a rebuild

`APPGUI` and `GUI` were added to `include/dotref.hpp` and CMDHELP kept emitting
the "curated DOTREF support status and help summary are pending" placeholder.
Cause: the header is compiled in. After `cmake --build build --config Release
--target dottalkpp`, both rows flipped to real text. The five recompiled
translation units were exactly the `dotref.hpp` consumers, which is the
confirmation that the change propagated rather than a coincidence.

### 6.2 cmdhelp.cpp carried a second copy of the function catalog, and it drifted

`is_expression_function_name()` in `src/cli/cmdhelp.cpp` answered from a
hand-maintained literal list of 64 names, duplicating `dottalk::expr`'s catalog.
The guard exists so expression functions are never promoted to DOT command rows
carrying a documentation debt. It was not firing.

Measured drift: **eleven** names the list had never heard of --
`FILE PADC PADL PADR PROPER STRCAT STUFF UDATE UDATETIME UNOW UTIME`.

Only FIVE were visible as bogus command rows. The other six were masked because
they also appear in `foxref`, so the FOX row claimed the key before the
placeholder branch reached them. **The masking is why the fix is delegation, not
"add the missing five."**

Fixed by delegating to `dottalk::expr::get_function_doc()`, which was already
exported and already resolves aliases. Measured before changing: zero
regressions, eleven names gained. `TRIM` was the near-miss -- it is not its own
catalog entry but an alias of `RTRIM`, so a name-only comparison called it a
loss and it is not one.

Confirmation after rebuild: command rows `465 -> 460`. Exactly five, which is
the five phantoms and nothing else. `STRCAT`, `PADC`, `PADL`, `PADR`, `PROPER`
and `STUFF` all survived because they have their own catalog rows. Had the
predicate over-fired, the drop would have exceeded five.

### 6.3 The catalog indexes by name, not by syntax prose

`BUILD INFO` and `BUILD VECTORS` are real registered commands. `dotref.hpp`
already named all three spellings -- but in the SYNTAX field, and CMDHELP builds
its lookup from the NAME field alone. Documented and undocumented were
indistinguishable from the generator's side. Fixed with explicit rows, following
the `APPGUI`/`GUI` precedent.

**Generalize this.** Information present in a field nobody indexes is absent.
Three of this session's four findings were that shape.

### 6.4 audit_contracts.py has a blind spot, and it is the AIF-118 shape

`tools/selfdoc/audit_contracts.py` keys on `cmd_*`/`app_*` FILENAMES and reads
`dotref.hpp`. A command reaching the catalog through the RUNTIME REGISTRY is
outside its vision entirely -- it reports clean because it never looked. None of
6.1 through 6.3 were findable by it.

CMDHELP's own placeholder text is the better worklist: it enumerates exactly
what is missing, from the runtime's own view. Recommended follow-up is to have
the audit read the registry, or diff against the placeholder set, so its silence
means something.

### 6.5 The audit's exemption widened, and the number improved without work

**Owner ruling wanted. Nothing reverted -- this is a report, not a fix.**

`c492d957d "Harden fullstack contract preflight"` (a concurrent session, in this
shared tree) added an exemption to `tools/selfdoc/audit_contracts.py`:

    file_block = comment_block(text, FILE_TAG)
    layer = LAYER_FIELD.search(file_block)
    if layer and layer.group(1).strip().lower() == "helper":
        helpers.append(rel)
        continue

It runs BEFORE the `@dottalk.usage` test, so a command file declaring
`layer: helper` in its `@dottalk.file` block is never checked for a usage
contract at all.

Measured effect: files reported as missing usage went **7 -> 1**. No
documentation was written. Six files were exempted, one (`cmd_palette_stub.cpp`,
`layer: command`) still reports.

Why this is worth a ruling rather than a shrug:

1. **`layer:` is an architectural field, not a documentation-obligation
   declaration.** The pre-existing exemption was `status: implementation-helper`
   INSIDE the usage block -- a field whose only purpose is to say "I
   deliberately export no command." You had to author a contract to claim it.
   The new one repurposes a field that was already there for another reason.
2. **The new exemption is free and self-certifying.** Any file can leave the
   audit's view by editing one word. The old one cost you a usage block.
3. **The metric improved because the measurement changed, not the tree.** That
   is the exact pattern this same tool's docstring warns about, in the paragraph
   about refusing a number that improves when nothing should have improved. The
   tool now does the thing its own comments warn against.
4. **Blast radius today is small, but it scales with the wrong number.** 330
   files repo-wide declare `layer: helper`; only 7 are `cmd_*`/`app_*` command
   files right now. The rule grows with the 330.

The defensible reading is that a helper genuinely exports no command and
exempting it is correct. If the owner takes that reading, the fix is small:
require BOTH `layer: helper` and an explicit opt-out in the file, so the
exemption stays deliberate and stays visible.

Either way, Gate 0.5's "100 percent coverage" now means something different than
it did before c492d957d, and the cookbook's target line does not say so.

---

## 7. Open, and owed

- The audit blind spot in 6.4 -- not yet recorded as an open item.
- **Seven** command files carry no `@dottalk.usage`. Measured by direct read,
  2026-08-26:

      src/cli/app_army.cpp                    layer: helper
      src/cli/app_erp.cpp                     layer: helper
      src/cli/app_paxon.cpp                   layer: helper
      src/cli/cmd_order.cpp                   layer: helper
      src/cli/cmd_palette_stub.cpp            layer: command
      src/palette/cmd_fox_palette_entry.cpp   layer: helper
      src/palette/cmd_palette_shim.cpp        layer: helper

  **`audit_contracts.py` currently reports ONE of these, not seven.** See 6.5 --
  the discrepancy is a live judgment call for the owner, not a defect to fix
  behind anyone's back.

  Corrected in place twice, which is the useful part of this bullet: an earlier
  count of EIGHT also listed `cmd_browsetui.cpp`, which does carry a usage
  block. Both errors came from citing a previous run instead of re-measuring.
  Re-measure this list rather than quoting it.
- `TRANSACTION` (status experimental) is unregistered. Policy call, not a defect.
- `cmd_workspace.cpp`'s `@dottalk.usage` block still omits `NEW`, `SWITCH`,
  `REGISTRY`, `CLOSE ALL` and `SET RECURSION`. Until refreshed,
  `dottalkpp/data/scripts/workspace_multi_demo.dts` stands in as that usage
  documentation and says so in its header.
- Uncommitted at time of writing: the 6.2/6.3 source fix, the regenerated help
  data (only trustworthy paired with that source), and the `gui/uidef` contract
  backfill.
- `dottalkpp/data/indexes/x32/STUDENTS.cnx` grew 9664 -> 14656 bytes during a
  help build. Unexplained. Account for it before it ships.
- **RESOLVED, and it was the reverse of the guess.** This bullet originally
  flagged the build stamp reading `Aug 22 2026` on a compile that felt like
  2026-08-24, and suspected a slow host clock. Measured: the HOST is 2026-08-26
  and the LINUX SANDBOX is 2026-08-24. The sandbox is two days BEHIND, not the
  host. Nothing is wrong with the build stamp; the agent reading it was using
  the wrong clock. See the clock note in this file's header, and take dates from
  the host or a file mtime. The stamp gap between `14:26:43` and `14:41:46`
  remains the reliable did-it-rebuild signal regardless of date.

---

## 8. The five-minute version

    1.  Contracts in the source, or nothing downstream can see the file.
    2.  Reconcile identities across registry / catalog / HELP / reflection.
    3.  Record what the runtime says BEFORE.
    4.  Get authorization, back up the HELP store, stop the daemon.
    5.  REBUILD if a catalog header changed. Then LEGACY, then current.
    6.  Record what the runtime says AFTER. Counts must hold or rise.
    7.  Regenerate the derived website pages. Never hand-edit them.
    8.  Metadata and manual candidates are candidates. Acceptance is its own gate.
    9.  Close in the dev tree. Publication is somebody else's lane.

Check the build stamp at every step that claims a result.

---

## GOOD NEIGHBOR

    WHAT CHANGED   : new file, docs/agents/HANDOFF_CLAUDE_COWORK_FULLSTACK_DOC_LIFECYCLE_2026-08-26.md.
                     Also modified, uncommitted:
                       src/cli/cmdhelp.cpp      -- is_expression_function_name now
                                                   delegates to get_function_doc
                       include/dotref.hpp       -- added BUILD VECTORS, BUILD INFO
                       src/cli/cmd_workspace.cpp -- @dottalk.usage block gains
                                                   NEW/UNDER/SWITCH/REGISTRY/
                                                   CLOSE ALL + notes; the printed
                                                   workspace_print_usage() text
                                                   corrected where it called NEW
                                                   runtime-only (false since
                                                   D10.1, 2026-08-23) and where
                                                   the notes said bare CLOSE
                                                   closes all areas (false since
                                                   AIF-078 stage 3).
    WHOSE AREA     : full_stack_documentation lane, owner member.derald.
                     cmdhelp.cpp is HELP-lane code. cmd_workspace.cpp is
                     AIF-078 / AIF-070 territory -- co-session COWORK-20260818-001
                     has been active there.
    TO CO-SESSION  : whoever committed c492d957d -- I did NOT revert your
                     layer:helper exemption. It is reported for owner ruling in
                     section 6.5 of the new handoff, with the measurement (7 -> 1
                     reported, zero documentation written). If the widening was
                     owner-directed, say so and 6.5 becomes a note instead of a
                     question.
    AUTHORIZATION  : maintainer request in session, "give me a complete handoff on
                     the fullstack doc life cycle with steps". The cmdhelp.cpp and
                     dotref.hpp edits were made under the maintainer's stated step-1
                     instruction earlier in the same session and are RUNTIME-PROVEN
                     (465 -> 460 command rows, build Aug 22 2026 14:41:46).
                     NOT authorized and NOT done: any commit, any push, any
                     publication step, any touch of C:\x64base.
    VERIFY OR UNDO : verify  ->  ./datarun.ps1 -CommandLines 'cmdhelp build legacy','cmdhelp build . d:\code\ccode\src'
                                 expect 460 command rows; no UDATE/UTIME/UNOW/
                                 UDATETIME/FILE rows in the DOT command list;
                                 BUILD INFO and BUILD VECTORS at supported=yes
                     undo    ->  git checkout -- src/cli/cmdhelp.cpp include/dotref.hpp
                                 then rebuild, then re-run the help build
                     this doc ->  git rm docs/agents/HANDOFF_CLAUDE_COWORK_FULLSTACK_DOC_LIFECYCLE_2026-08-26.md
