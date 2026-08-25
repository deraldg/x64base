# Gate 0 -- run envelope, full-stack documentation flush v5

    Run           : DOCFLUSH-20260812-001
    Lane          : full_stack_documentation
    Recorded      : 2026-08-12
    Owner         : member.derald
    Steward       : member.ai.claude.cowork
    Entry branch  : development
    Entry HEAD    : 46bd9233fc4ddfa644f3cfcec8fafc8179bc662e
    Predecessor   : DOCFLUSH-20260805-001 (v4), closed at Gate 7
    Status        : OPEN at Gate 0. No mutation performed by this record.

Lineage, in the owner's words (recorded in v4's story): **v1 by hand, v2 and v3
pushing the assistant, v4 guiding it.** The methodology is to walk the process
end to end each pass, streamlining and automating more of it each time, until it
is mostly a batch or chain run. v5 continues that arc.

---

## 1. Why v5 exists, stated honestly

v5 was NOT planned. The owner was deliberately delaying it and intended only a
convenience refresh of the help files. Three things on 2026-08-12 made a full run
necessary instead:

1. **`include/dotref.hpp` changed.** It had not moved since 2026-08-05 and
   therefore predated the entire memo-resident workspace lane -- HELP was
   describing a `WORKSPACE` that had stopped existing. Three entries were
   rewritten (WORKSPACE, ERASE, REGRESSION). A dotref change is exactly the case
   v4's own retired-footguns list wrote a recipe for.

2. **That recipe was then half-skipped.** v4 recorded: *"A dotref.hpp change
   requires `CMDHELP BUILD LEGACY` then `CMDHELP BUILD . <ABS src>` (foxref feeds
   LEGACY). Back up `dottalkpp/data/help` first; the daemon locks the store."*
   Only the second command was run. No LEGACY pass, no backup. This is the most
   likely reason the rewritten dotref prose did not appear in the store while the
   short syntax strings did.

3. **The HELP store was rebuilt outside a run envelope.** `cmdhelp build .
   d:\code\ccode\src` executed with no Gate 0, no Phase 2 baseline to compare
   against, and no Gate 4 validation record. Per the cookbook a HELP refresh is
   Phase 3 (reviewed package) then Phase 4 (execute + validate). The store has
   therefore moved with no gate record of where it moved from or to. **That is
   the condition v5 must first repair, before it can proceed normally.**

Consequence for this run: the Phase 2 baseline is NOT a pre-refresh baseline in
the usual sense. It captures a store that has ALREADY been rebuilt ad hoc. That
must be stated in the Gate 2 record rather than papered over, and it is the
reason v5's baseline cannot be diffed against v4's Gate 4 numbers as like for
like.

---

## 2. Scope

IN scope for v5:

- Re-establish a gated baseline over the ad-hoc-rebuilt store (Phase 2 / Gate 2).
- Reference authorities: `dotref.hpp` (changed), `foxref.hpp` (candidate: see
  section 4), SYSFUNC (**blocked**, see section 3).
- Correct HELP rebuild sequence, this time by the recipe: LEGACY first, backup
  first, daemon stopped.
- Phase 5/6 re-harvest that v4 explicitly owed: the manualgen harvest predates
  v4's Phase-4 rebuild, so the manual candidate lacks BBS/NET/CANARY/CMDREL/
  FORMULA/EDIT -- and the store has moved again since.

**THE WEBSITE CLOSEOUT GATE, added to this envelope 2026-08-12 after reading
the site's own rules.** `D:\dev\x64base-site\README.md` routes all website work
-- human or AI -- through `content/docs/dev/website-documentation-matrix.mdx`
FIRST, and that matrix states its own gate:

> on every full-stack push, once the website is approved, this matrix must be
> updated and re-audited to match the signed-off site (advance `Last audited`,
> reclassify any changed pages, record new diagrams and feeds). **The run does
> not close until the matrix is current** -- a stale matrix blocks.

This run had not recorded that obligation. It is in scope now, and it is a
CLOSING condition rather than a phase: v5 cannot close on a stale matrix.

What v5 already knows it must reconcile there, because today's engine work
falsified it:

- **`/docs/engine/proven-capabilities`** (`maintained`) -- its workspace entry
  ends "plus the still-chartered writeback cycle". WRITEBACK landed 2026-08-12,
  proven on both toolchains.
- **`/schemas`** closing section (`maintained`) -- same lane, same claim.
- **`/docs/engine/ecosystem-feature-comparison`** (`maintained`) -- carries the
  workspace rows including the honest NO on simultaneous residency (still true)
  and the writeback row (no longer true).
- **`/news/announcements/`** -- a dated announcement is drafted
  (`the-return-leg.mdx`). News posts are event records, so the 2026-08-11
  article is NOT edited; the correction rides in a new dated post that names
  the earlier non-claim it closes.

Direction Gates apply and were read: implementation -> website is the simplex
default; **website -> manual is blocked**. Nothing on the site may be promoted
back into the manual or source-side truth.

A defect found while drafting, recorded here because it is the matrix's business
and not the engine's: `lib/seo.ts` reads `fm.description`, falling back to a
generic string, and the news index renders `frontmatter.description`. Two of
fifteen announcements use `summary:` instead -- including the 2026-08-11
"A table whose rows are databases" -- so that article currently publishes with
the generic meta description and a BLANK blurb in its own index listing. One
word per file. Owner's call whether it rides this run.

OUT of scope, inherited from v4's disposition:

- Phase 8 publication ascent (its own lane).
- AIF-067 dotref-automation M2/M3 (deferred). Noted because M2 -- "flag dotref
  summaries that drifted from the contract" -- is precisely the check that would
  have caught this run's over-long dotref entries automatically.

---

## 3. GATE 0 PRECONDITION -- metacollect is broken, and it blocks an authority

`SYSFUNC_IMPORT_v1.csv` is stale by exactly one function, `FILE`. It cannot be
regenerated by hand ("metacollect regeneration rather than hand-forged"), and
metacollect no longer builds:

    commit 5a4f9b3ec made src/cli/expr/fn_string.cpp depend on
    paths::get_slot / paths::resolve_in_slot. dt_meta compiles fn_string.cpp
    but links neither resolver, so the metacollect target fails to link.
    DOTTALK_BUILD_METACOLLECT defaults OFF, which is why every build and every
    gate passed while the target was unbuildable.

This is a defect introduced by this session's own engine work, and it is a Gate 0
precondition rather than a later phase item because SYSFUNC is one of the
authorities the run reconciles against (77 functions), and `FN_COVERAGE` has
warned `FILE` on every commit since.

Fix is verified in a scratch tree -- add `src/common/path_resolver.cpp` and
`src/common/path_state.cpp` to the `dt_meta` target; it then links and builds
clean. NOT APPLIED, pending an owner ruling: `dt_meta` carries a stated safety
boundary ("no HELP DATA rebuild, no CMDHELPCHK mutation, no DBF writes") and
`path_state` brings process-wide mutable path-slot state into a library built to
be minimal. Whether that crosses the boundary is the owner's call, not the
steward's.

**Gate 0 does not pass until this is ruled on.** The run may proceed to Phase 1
inventory meanwhile; it may not reach a Gate 4 HELP rebuild claiming SYSFUNC
agreement.

### RESOLVED 2026-08-25. The text above is left standing because it was true when written.

**All three legs are satisfied, and two of them were satisfied before this
amendment and nothing said so.** Full record:
`gate0/GATE0_PRECONDITION_CLOSEOUT_V1.md`.

1. **The link fix landed 2026-08-14 in `d99f4ed9c`** -- `path_resolver.cpp` and
   `path_state.cpp` added to the `dt_meta` target. "NOT APPLIED, pending an
   owner ruling" was accurate on 2026-08-12 and stale from 2026-08-14. **It went
   eleven days unamended, and on 2026-08-25 it caused this steward to start
   re-raising a closed blocker.** That is the cost of a run record that is only
   ever appended to at the front.

2. **SYSFUNC no longer disagrees with the engine.**
   `tools/fullstack_docs/normcheck_v1.py`, 2026-08-25:
   `IMPLEMENTED(fn specs) 75 == CATALOG(SYSFUNC) 75`, `FN_IDENTITY 0`,
   `FN_COVERAGE 0`. The `FILE` warning is gone. **The count of 77 above is also
   stale; the catalogue holds 75.**

3. **metacollect builds and links -- verified BY BUILDING**, which the
   `CMakeLists.txt` comment asked for and nobody had done: `d99f4ed9c` carries a
   one-line message with no body or transcript, and `DOTTALK_BUILD_METACOLLECT`
   is still `OFF` by default at `CMakeLists.txt:114` -- the same default that
   hid the original breakage. Eleven `dt_meta` sources plus
   `src/tools/metacollect_main.cpp`, isolated, g++ 13.3.0 `-std=c++17`:
   12/12 translation units compiled, linked to a 1,603,904-byte binary with
   **zero undefined references**, and `./metacollect --help` returns the tool's
   own argument diagnostic -- it starts and parses, it did not merely link.
   **Caveat: Linux/g++ only. MSVC untested**, and the blocker this closes was
   itself a toolchain-visibility problem.

**The owner ruling this precondition asked for** -- whether `path_state`'s
process-wide mutable slot state crosses `dt_meta`'s stated "no DBF writes"
boundary -- **is answered in the code that landed**, and the reasoning is
recorded in the CMakeLists comment: a local stub would have compiled and then
resolved paths DIFFERENTLY from the engine, which is worse than a link error,
because a link error stops.

**GATE 0'S METACOLLECT PRECONDITION PASSES.** A Gate 4 HELP rebuild may now
claim SYSFUNC agreement, and section 1b is the measurement that backs the claim.

Two facts found while closing it, both recorded in the closeout and neither
blocking Gate 0:

- `dottalkpp/data/metadata/` holds the eight SYS* authorities this run
  reconciles against -- 16 top-level files, 580,299 bytes -- and **0 are tracked
  and 0 are gitignored.** A fresh clone has no SYSCMD and no SYSFUNC.
- `normcheck_v1.py` returned the same answer for an ABSENT SYSFUNC as for one in
  perfect agreement, on a **fail**-severity lane. Filed to AIF-118; patched and
  proven to fail on 2026-08-25.

---

## 4. Open questions carried into Phase 1

**Q1 -- harvest scope: 205 mined vs 229 present.** The ad-hoc build reported
"Usage contracts mined directly: 3459 row(s) from 205 file(s)". Measured now:

    contract-bearing .cpp             229
    contract-bearing .cpp + .hpp      233
    contract-bearing .cpp in src/cli  203

205 is close to the `src/cli` count (203), not the tree count (229). If the
harvest is `src/cli`-shaped, then `src/edu/*` (16 contract files), plus contracts
under `src/help`, `src/identity`, `src/xbase` and `src/security`, are not being
mined at all. That would be a silent coverage gap in the authority the whole
flush reconciles against.

Not asserted as a defect -- the 2-file difference between 203 and 205 is
unexplained either way, and the miner may take an explicit root list. Phase 1
must determine which, because "contracts exist" and "contracts are harvested" are
different claims and only the second one reaches HELP.

Confirmed while forming the question: `edu_` and `app_` handlers ARE native
commands belonging in dotref (`dotref_autogen.py` routing: `cmd_` / `edu_` /
`app_` -> NATIVE). `lab_` does not exist as a prefix -- zero files. `edref` is a
separate catalog owning its own namespace (29 entries; refcheck treats its 21
namespace entries as not-failures).

**Q2 -- foxref and `FILE()`.** `FILE()` was added to the engine on 2026-08-12 and
is a genuine VFP function name, but ours is deliberately broader than VFP's (any
filesystem entry counts, directories included, because an absence proof must not
be passed by a leftover empty directory). `foxref.hpp` has no `FILE` entry.
Decision needed: add one recording the divergence, or leave foxref silent.
`FILE()` correctly does NOT belong in dotref -- `dotref_autogen.py` states that
expression functions are not in the command registry and SYSFUNC owns them.

**Q3 -- `risk:` blocks are not harvested.** Measured: VDISK's own long-standing
`loses_ephemeral_data` key appears 0 times in built HELP DATA, as do all other
risk keys. A `risk:` block added to `WORKSPACE` on 2026-08-12 is therefore for
source readers only. Whether risk should reach HELP is a lane question, not a
defect; it is recorded so nobody writes more of them expecting them to surface.

---

## 5. Entry-state facts (re-measure at Gate 2; do not trust this list)

    entry HEAD                      46bd9233fc4ddfa644f3cfcec8fafc8179bc662e
    branch                          development
    dotref entries                  258
    contract-bearing .cpp           229
    non-ASCII inside contract blocks 0   <- see section 6
    HELP store                      REBUILT AD HOC 2026-08-12, no gate record

---

## 6. Closed before this run opened: AIF-088's deferred ASCII sweep

The portal task (`ai_portal_tasks.yaml`, recorded 2026-08-05 from v4's Phase 2
baseline) chartered: *"Dedicated ASCII sweep of source comments/@dottalk
contracts (em-dash -> --, arrows -> ->), so HELP DATA and the website catalog
stay ASCII... The house-style gate only checks added lines, so this backlog needs
a one-time sweep and an optional whole-file gate on @dottalk contract blocks."*

The sweep half is DONE, committed as `4c584ba8f`: 215 em-dash replacements across
141 files, including `cmd_buildvectors.cpp:21` -- the exact line v4 named as the
proven mojibake case.

**Verification, which also sharpens the scope for the gate half:** there are now
**0 non-ASCII characters inside any `@dottalk.usage` block, tree-wide**. The
harvester reads the contract block, not every comment, and the discriminator is
measurable: `U+2500` box-drawing appears 3556 times inside comments across
contract-bearing files and **0 times in built HELP DATA**. So the enforceable
rule is narrower and cleaner than "no non-ASCII in comments" -- it is **no
non-ASCII inside a contract block**, which a gate can check precisely without
touching the 3556 decorative separators or the 312 accented characters the
localized surfaces need (measured: 0 of those accents are in comments; they are
all runtime strings).

STILL OPEN from that task: the whole-file gate on contract blocks. It is the
durable half, and `check_house_style.py` still checks `.md` only.

Steward's note, recorded because it cost time: this session re-derived the
gate-gap finding and presented it as new, a week after it had been written down
in the portal with the same analysis and the same prescription. The evidence was
where the owner said it was.
