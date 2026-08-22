---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260822-COWORK-111
  recorded_at_utc: 2026-08-22T19:05:28Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260822-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 5cc7bc3e5
  authorization:
    requested_by: maintainer (member.derald), in-session 2026-08-22 -- "go both",
      answering a proposal to fix the resolver disagreement first and re-key the
      relation store second. Authorises the resolver work (I1.3a) only; the
      re-key (I1.2) is NOT authorised by this document.
  report:
    path: docs/maintenance/AIF120_I13A_ONE_RESOLVER_RULING_V1.md
    kind: ruling
---

# AIF-120 -- I1.3a: one resolver, and an ambiguous name that says so

Status: **ruling, review-needed.** Code landed under the steward's explicit
"go both"; the author does not self-approve the design.
Owner: member.derald. Author: member.ai.claude.cowork, run `COWORK-20260822-001`.
Date: 2026-08-22. Baseline `5cc7bc3e5`. Claim: AIF-120 (held by this member).

Prerequisite for **I1.2** (re-keying the relation graph to `(handle, name)`) and
therefore for **AIF-078 stage 4**. It is not that piece and does not start it.

---

## 1. The defect, exactly

Two functions answered the question "which open work area is called X", and
they did not agree.

| resolver | lives at | rule | reach |
|---|---|---|---|
| `find_open_area_by_name_ci` | `workarea_util.cpp:29` | returns on the FIRST match -- **lowest** engine slot | 21 call sites, 15 files |
| `build_area_by_up_name` | `set_relations.cpp:778` | `out[key] = a`, unconditional assign -- **last** match, **highest** slot | 1 call site, the recursive `REL LIST` tree builder |

Neither printed which area it had chosen. So with two areas named `STUDENTS`,
the relation that bound and the tree that reported it could be describing
different tables, and the transcript would look identical either way.

**This is not a hypothetical corpus.** R112 sec 3 measured twelve basenames
present in all three flavour roots -- `students`, `teachers`, `classes`,
`enroll`, `courses`, `dept`, `majors`, `rooms`, `stud_maj`, `tassign`, `terms`,
`building`. That is the MCC demo schema. And it needs no second workspace:
`USE` guards duplicates by PATH only (`cmd_use.cpp:688`) and `USE ... ALIAS`
assigns the logical name with **no uniqueness check at all**, so

    USE dbf\x64\students
    USE dbf\x32\students IN 1        -- two areas, both named STUDENTS

is legal today, in one workspace, with the `IN` clause that landed yesterday.

## 2. What was done

**One primitive.** `find_open_areas_by_name_ci()` returns EVERY open area whose
name matches, ascending by engine slot. Singular lookup is `front()`. The map
builder indexes `front()` per key via `emplace`, not `operator[]`. The two
resolvers now **agree by construction**, not by inspection -- there is no second
matching rule left to drift.

`build_area_by_up_name` is **deleted, not replaced in kind**, and the comment
left in its place says why, so the next hand that wants a local index there
knows it is re-opening a closed defect.

**The dead second comparison is not reproduced.** The old scan compared the
target against `logicalName()` and then against `name()`. R112 sec 1 established
these are the same member (`xbase.hpp:238` and `:288`), so the second comparison
could never match when the first did not. Copying it forward would have implied
two name spaces that do not exist.

**The choice is instrumented.** When more than one area matches, the resolution
is recorded -- name, call site, every candidate `(workspace, area)`, the area
chosen, and a recurrence count -- and announced ONCE per distinct (name, site),
the same latch shape as `note_scan_truncated()` and for the same reason: a
resolver reached from inside a refresh loop must not be able to flood a
transcript.

Eleven REL call sites carry a site tag. Every other caller records as
**`unattributed`**, printed as such rather than as a blank, because an
unattributed hit is a call site nobody has labelled yet -- not an absence.

**The ledger is readable.** `WORKSPACE REGISTRY` prints

    name ambiguity : N resolution(s)
      name NAMDUP  site REL add child  chose area 1  hits 1  candidates ws1:a1 ws1:a2

and prints the count **even when it is zero**, so "no collisions" and "not
instrumented" cannot look the same (the AIF-118 shape). `WORKSPACE CLOSE ALL`
resets it, which makes one script one measurement.

## 3. Why an instrument and not just a warning -- R112 sec 6a, honoured

R112 sec 6a ruled first-wins-plus-warning admissible **only** as an instrumented
migration phase, and was explicit that a warning printed beside a wrong answer,
from a resolver called at sites that mostly print nothing, is not a fix. The
condition it set was:

> the ambiguity path **counts and records** each occurrence -- resolver call
> site, the name, and the candidate areas -- not just prints; the migration ends
> on a **measured zero**; the phase is time-boxed by that measurement, not by a
> date.

That is what shipped. The counter is the gate. Flipping to a hard refusal
remains its own commit and its own ruling, per that section.

## 4. What this does NOT do, stated rather than implied

- ~~**It does not enforce the within-workspace uniqueness invariant.**~~
  **WRONG -- see sec 5a.** The invariant is already enforced at
  `cmd_use.cpp:944-972`, and the AGAIN question I raised as owed is already
  answered there by the auto-rename. Left struck rather than deleted, because
  the correction is the finding.
- **It does not re-key the relation store.** The store is still
  `unordered_map<UPPER parent name, vector<Relation>>` with no owner field.
  That is I1.2 and it is the actual AIF-078 stage 4 blocker.
- **It does not change any field-observable behaviour.** See sec 5.
- **It does not wire the qualified-reference surface.** `WS.#n.TABLE` still
  parses and renders in `src/reference/` and reaches nothing under `src/cli`.
  R112 priced that into I1.3 and it stays unpaid.

## 5. The spec cannot fail on this defect, and says so

`NAME_AMBIG` (`dottalkpp/data/scripts/rel_name_ambiguity_regression.dts`, 4
markers) is registered but is **not a discriminator for the consolidation**. The
divergence was never field-observable: `build_area_by_up_name`'s map fed record
counts that get PRINTED and never moved a cursor. No marker in it goes red on
the old build. **The compiler is the discriminator** -- the function is gone and
cannot be called.

Stating that is the point. A spec that cannot fail on the defect it is named
after is precisely the false green this house keeps finding, and the honest move
is to write the limitation into the spec header and the registry description
rather than let a green line imply a proof it does not carry.

What the markers DO pin is the **ruled choice**:

- `N_T1` -- the lowest slot followed the parent.
- `N_T2` -- the higher slot did not. This is the direction discriminator: if
  anyone ever "fixes" ambiguity by making the last match win, both red at once.

When the policy flips to hard refusal, these two markers move. That is
deliberate: it makes the flip a red marker and its own ruling, which is what
"time-boxed by measurement" has to mean if it means anything.

## 5a. AMENDMENT, same day, after the first runtime pass -- sec 4's first bullet was wrong, and so was R112 sec 3

Written before the build, sec 4 said the within-workspace uniqueness invariant
"is not enforced" and named a ruling owed about `USE ... AGAIN` before it could
be. **The first run of `NAME_AMBIG` refused to build its own fixture and proved
otherwise:**

    USE: refused -- alias 'NAMDUP' is already held by area 1.
      Choose another, or close that area. Nothing was opened.

**The guard already exists**, at `cmd_use.cpp:944-972`, resolving the name
BEFORE the target area is touched:

- an **explicit** `ALIAS` already held is **refused**;
- a name **derived from the file stem** that is already held is **auto-renamed**
  to `<stem>2` and **announced**.

And the AGAIN question sec 4 raised as owed is already answered by that second
arm -- `USE_AGAIN` shows it live, twice, deriving `UAREGR2` and `UAREGR3`. The
comment at `:963` even names the case this lane cares about: *"the ordinary
AGAIN case, **and also two same-named files from different directories**."*

**So R112 sec 3 is stale in its sharpest claim.** It measured that
`USE ... ALIAS` assigns the logical name "with **no uniqueness check at all**"
and offered `USE dbf\x64\teachers.dbf ALIAS STUDENTS` as "a deliberate
collision, accepted". That was true at `8aca9ef1b`. It stopped being true on
2026-08-12 when USE_AGAIN's alias arm landed. **R112 sec 6a then scheduled the
within-workspace "prevent" half as work to be done, and a different lane had
already shipped it** -- a ruling planning work that was finished, which is the
mirror image of this house's usual failure and worth the same attention.

### What that does to the instrument

Two open areas in one workspace **cannot** share a logical name. So
`ambiguity_count()` is **structurally zero today** -- not untested,
*unreachable* -- until two workspaces can be open at once **and** cross-workspace
names are permitted to repeat, which R112 sec 4 says they may.

R112 sec 6a called this exact shot:

> the migration phase can only observe cross-workspace ambiguity once two
> workspaces can be open at once -- before that it would record zero for the
> wrong reason, and **a zero that means "nothing was tested" is exactly the
> false green** trap-4 is about.

**The instrument built under that ruling walked into the trap the ruling
described.** Recorded rather than quietly repurposed.

The ledger is not therefore useless, but **its meaning has changed and the
claim must change with it**: it is not a migration counter for a live
first-wins policy, because there is no live within-workspace first-wins policy
to migrate. It is a **tripwire for AIF-078 stage 4** -- the line goes non-zero
the day two workspaces can hold one name, and that is the day the
cross-workspace half of R112 becomes real work. Sec 3's framing stands only for
the cross-workspace case.

### And my own spec produced a false green

`N_T1` read `.T.` in the failed run while proving nothing: only one `NAMDUP`
existed, so the resolution was unambiguous and the marker asserted a tautology.
Sec 5 argued at length that a spec which cannot fail on its subject is the
house's recurring defect; the first cut of that spec contained one. The spec is
rewritten to assert what is actually true and reachable -- the
two-directories-same-basename rename, which nothing else in the corpus covers.

### What is NOT changed by this amendment

The resolver consolidation stands and is verified: `REGRESSION ALL` green on
all 8 defaults, `USE_AGAIN` 15/15, `USE_ARGS` 7/7, on build `83f5032e`. And a
prediction I made before the run was wrong in the harmless direction: I expected
`USE_AGAIN` to emit new `NAME:` announce lines. It emitted none, and cannot --
the rename means its two instances never share a name.

## 6. Cost

One pass over the work-area array per resolution -- the same pass the old scan
made, so no regression. `build_open_area_index_ci()` is one pass for the whole
map where the old builder was also one pass. `MAX_AREA` is 512 for testing only;
callers that resolve several names in a row should build the index once rather
than scan per name, and the header says so.

## 7. Evidence tier

**Source-evidenced:** sec 1 (both resolvers read at `5cc7bc3e5`), sec 2 (the
code as landed), sec 4 (store shape, qualified-reference reach).
**Measured:** the twelve-basename overlap is R112's measurement, re-cited not
re-run. Runtime verification of `NAME_AMBIG` is OWED -- this document is written
before the steward's MSVC build; the Linux-side check is `-fsyntax-only` on the
four changed translation units, which all pass.
**Chat/AI output:** sec 3's reading of R112, sec 5's argument.

## 8. Good Neighbor note

- **What changed.**
  - `src/cli/workarea_util.hpp` / `.cpp` -- new all-matches primitive, shared
    index builder, tagged overload, ambiguity ledger. Existing signature and
    behaviour of `find_open_area_by_name_ci` unchanged.
  - `src/cli/set_relations.cpp` -- `build_area_by_up_name` deleted; 11 resolver
    calls tagged with a call site.
  - `src/cli/cmd_workspace.cpp` -- `WORKSPACE REGISTRY` prints the ledger;
    `WORKSPACE CLOSE ALL` resets it.
  - `src/cli/cmd_regression.cpp` -- array 48 -> 49, `NAME_AMBIG` registered.
  - `dottalkpp/data/scripts/rel_name_ambiguity_regression.dts` -- new.
  - This document.
- **Whose area.** `src/cli/**` is engine-adjacent and not this lane's to change
  without an explicit go. It has one: the steward's "go both", 2026-08-22.
  `dottalkpp/data/help/*` was NOT touched -- those DBFs belong to the concurrent
  document push, which is why the ledger prints through `std::cout` and the
  announce through `cli::cmdout::print_line` rather than the message catalog.
- **What authorization.** Steward, in session, 2026-08-22: "go both". Covers the
  resolver consolidation and the instrument. Does NOT cover I1.2, the
  within-workspace refusal, or the flip to hard refusal.
- **How to verify.** Build, then `REGRESSION ALL` (8 defaults must stay green),
  then `REGRESSION RUN NAME_AMBIG` -- expect `N_G0`, `N_G1`, `N_T1`, `N_T2` all
  `.T.`, a `NAME:` announce line inside the ANNOUNCE block, and a non-zero
  `name ambiguity` count with a `NAMDUP` row inside the LEDGER block. Then
  `REGRESSION RUN USE_AGAIN` and `REGRESSION RUN USE_ARGS`, both of which run
  through the changed resolver.
- **How to undo.** Revert the commit. Nothing persists: the ledger is process
  state, the spec is self-erasing, and no catalog, DBF or posture was written.
