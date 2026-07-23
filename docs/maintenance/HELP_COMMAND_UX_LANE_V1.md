# HELP Command UX — Not-Found Feedback + Did-You-Mean (Lane / Ticket V1)

Status: **intake / proposed — not started.** Parent project: `project.x64base.runtime`
(sibling of the BETA-1 stabilization lane AIF-041). Owner-filed 2026-07-22.
Change class: `C0` (ticket/design) → implementation is a later `C1`/`C2`.

## Owner report (verbatim intent)

1. **`HELP GIANT` is not "help giant."** `HELP GIANT <topic>` does not render the full /
   assembled topic the way its name promises — the behavior is inconsistent with the
   expectation of a comprehensive ("giant") help view.
2. **`HELP <anything-not-real>` returns the prompt.** Asking for a non-existent topic gives
   no feedback — it silently falls back to the top-level router (looks like it "returns the
   prompt"), so the user can't tell whether the topic is missing or they mistyped.
3. **Repeating goes in a circle.** `HELP <anything>` again just re-shows the same router —
   a loop with no progress and no signal.
4. **Wanted: did-you-mean.** On a not-found topic, HELP should **suggest similar words**
   (near-match topic/command names) instead of silently routing.

## Ground truth (verified 2026-07-22)

- `src/cli/cmd_help.cpp` (742 lines) is the `HELP` handler; `HELP GIANT <topic>` renders an
  assembled topic "through current HELP DATA" (header comment §49). `HELP` with no args prints
  the top-level router (§44).
- Topic lookup goes through `show_new_catalog_topic(term)` (cmd_help.cpp ~line 151) which
  **returns `false` when no doc is found** — there is no user-visible "topic not found"
  message and no suggestion path; control falls back to the router. This is the silent
  "returns the prompt" the report describes.
- Help content sources already present to draw candidates from: the reflected **command
  catalog** (`cli/command_catalog.hpp`), the reference catalogs `include/dotref.hpp` /
  `include/foxref.hpp` / `edref.hpp`, the **function catalog** (`cli/expr/function_catalog.hpp`),
  and the **HELP DATA** DBFs (`dottalkpp/data/help/*`). A did-you-mean matcher has a rich,
  already-indexed candidate set — no new data needed.

## Desired behavior

1. **Explicit not-found line.** `HELP <unknown>` prints a clear message, e.g.
   `No help topic 'GAINT'.` — never a silent return to the router.
2. **Did-you-mean suggestions.** Follow the not-found line with up to N near matches ranked by
   (a) exact-substring / prefix, then (b) small edit distance (Levenshtein ≤ 2–3 scaled to
   length), drawn from the command catalog + dotref/foxref/edref + function catalog + HELP
   DATA topic keys. Example:
   `No help topic 'GAINT'. Did you mean: GIANT, GRANT, PRINT?`
3. **`HELP GIANT` consistency.** Reconcile `HELP GIANT <topic>` so it renders the full
   assembled topic consistently (define what "giant" includes: syntax + examples + notes +
   warnings + related, from HELP DATA), and make `HELP GIANT <unknown>` share the same
   not-found + suggestion path.
4. **No loop.** Repeating a not-found HELP gives the same deterministic not-found + suggestions
   (informative), not a re-routed prompt.

## Milestones (proposed)

- **M0** — reproduce + catalogue the exact fall-through paths (no-arg router vs unknown topic
  vs `HELP GIANT <unknown>`); pin the candidate-source list. (this doc)
- **M1** — not-found message: any unmatched `HELP <term>` prints `No help topic '<term>'.`
  instead of silently routing. Small, low-risk.
- **M2** — did-you-mean matcher: a reusable `suggest_topics(term, limit)` over the unified
  candidate set (prefix/substring + bounded edit distance), wired into the not-found path.
  Unit-prove the matcher (like the DIR glob matcher) before engine build.
- **M3** — `HELP GIANT` consistency pass + shared not-found/suggestion path.
- **M4** — REGRESSION coverage (`HELP <unknown>` emits not-found + at least one suggestion for
  a near-miss like `GAINT`→`GIANT`); update `@dottalk.usage` notes.

## Notes

- Ties into AIF-041 M4 (`dotref`/`foxref` maintainability) and the HELP DATA family guide
  (`docs/maintenance/lanes/help/HELP_DOCUMENT_FAMILY_SYSTEM_GUIDE_v1.md`): suggestions should
  read from the same harvested sources, not a new hand list.
- Keep the matcher engine-agnostic/pure so it is unit-testable standalone.
- Dev-only, not started, not promoted.

---

## M0 — Analysis (owner: Claude/Cowork, 2026-07-22) — COMPLETE

Read `src/cli/cmd_help.cpp` (742 lines) end to end. The router `cmd_HELP` (line 554) dispatches
in this order: `GIANT`/`/GIANT` (566), `GIANT <x>`/`/GIANT <x>` (572), `BETA` (594), `PS` (603),
`SQL` (616), `PREDICATES` (628), `FUNCTIONS`/`FUNCTION <x>` (633–658), empty/`USAGE`/`?` (660),
option-flag forms `parse_opts` (665: `--build`, pred-only, `/FOX`, `/DOT`, `/ED`), then the
**general topic block** (697–739), and a final top-level hint (741).

### Root cause of "HELP <unknown> returns the prompt" (report #2/#3)

In the general topic block, after all structured lookups fail —
`show_reflected_subcommand_topic` (SET), `show_reflected_command_topic`,
`show_reflected_function_topic`, `show_new_catalog_topic`,
`show_function_topic_from_doc_catalog`, `BETA` — control reaches a **legacy fallback** guarded by
`term_effective == term_original_up` (line 722, i.e. normalization left the term unchanged — true
for ordinary typos like `GAINT`). That branch tries `show_dot_topic` → `show_ed_topic` →
`show_active_help_hint_command` → `show_fox_topic_local`, and then calls **`show_fox(area, term)`
unconditionally and `return`s (line 731–732)**. `show_fox` (line 259) is just `cmd_FOXHELP(area, term)`.

**Correction after reading `src/cli/cmd_foxhelp.cpp`:** the fall-through is *not literally
silent*. `cmd_FOXHELP` (a) does a **foxref subset match** and, if any, prints
`FoxHelpMatchesTitleText` + the matches (lines 124–132) — a crude, fox-scoped did-you-mean that
already exists; else (b) prints `FoxHelpNoTopicText` + `FoxHelpTryListHintText` (135–138). So
`HELP <typo>` yields a **terse, FOX-flavored, foxref-only** miss that points at `FOXHELP LIST` —
which reads to the user as "returned the prompt / went in a circle": help didn't own the answer,
gave no cross-namespace guidance, and the retry repeats the same fox loop. **Critically, this
FOX path `return`s at line 732 BEFORE the general `HelpNoTopicFound` message (735).** So the two
classes of unknown term diverge: a term that survives normalization unchanged → FOX fox-only
fallback; a term normalization *changed* → the general `HelpNoTopicFound` (no suggestions). That
inconsistency + the FOX-scoped delegation IS the bug. Fix direction: **HELP should own a unified,
cross-namespace not-found + suggestion terminal** rather than delegating the miss to FOXHELP's
fox-only fallback (the foxref subset-match is a useful precedent to generalize, not keep as the
only path).

### The not-found message already exists (M1 is small)

The message catalog already has per-namespace not-found IDs, all wired at call sites:
`HelpNoTopicFound` (736), `HelpNoFunctionFound` (656), `HelpNoDotTalkTopicFound` (683),
`HelpNoEducationalTopicFound` (691). So M1 needs no new message plumbing — it needs the
**common typo path to reach a not-found terminal** instead of the silent `show_fox` return.

### "HELP GIANT is not help giant" (report #1)

`HELP GIANT <topic>` (589–590) simply forwards `<topic>` to `cmd_CMDHELP` — it is effectively
`CMDHELP <topic>`, not a comprehensive assembled ("giant") view, and `GIANT <unknown>` inherits
CMDHELP's own (quiet) miss behavior. `HELP GIANT TOPICS/KIND/SOURCE` map to `CMDHELP REPORT …`
(583–585) and **`HELP GIANT TOPICS` already enumerates the current topic keys** — a ready
candidate source for suggestions.

### Candidate sources for did-you-mean (all enumerable, already indexed)

| Source | Enumerator |
| --- | --- |
| Reflected command names | command registry / `cli/command_catalog.hpp` (same set `HELP GIANT TOPICS` lists) |
| Native / legacy / edu reference | `dotref::catalog()`, `foxref::catalog()`, `edref::catalog()` — `Item.name` |
| Functions | `cli/expr/function_catalog.hpp` |
| HELP DATA topic keys | the `CMDHELP REPORT TOPICS` surface behind `HELP GIANT TOPICS` |

A `suggest_topics(term, limit)` should union these keys once, then rank by (a) prefix, (b)
substring, (c) bounded Levenshtein (≤ 2, or ≤ 3 for len ≥ 8), returning the top N distinct.

### Refined milestone plan (post-analysis)

- **M1 — unified not-found terminal.** Add `help_not_found(term)` that emits `HelpNoTopicFound`
  (+ later suggestions). Route the general-topic block through it: keep the FOX lookup but make
  it *return a found/not-found signal* (extend `show_fox`/FOXHELP to report a hit, or gate on
  `show_fox_topic_local`) rather than an unconditional pass-through, so an unknown term lands on
  `help_not_found` instead of the bare prompt. **Risk to resolve:** FOXHELP may match HELP-DATA
  topics that the in-memory `foxref::find` does not — do not lose those; the fox path must
  signal "found" truthfully before we declare not-found.
- **M2 — `suggest_topics()` matcher.** Pure, standalone-unit-testable (like the DIR glob just
  shipped). Wire into `help_not_found`. `HELP GAINT` → "No help topic 'GAINT'. Did you mean:
  GIANT, GRANT, PRINT?".
- **M3 — `HELP GIANT` consistency.** Decide the "giant" contract (full assembled topic) and give
  `GIANT <unknown>` the same not-found + suggestions terminal.
- **M4 — REGRESSION** (`HELP GAINT` emits not-found + ≥1 near suggestion) + `@dottalk.usage`
  notes.

**M0 status: complete.** Owner: Claude/Cowork. Next actionable: M1 (unified not-found terminal),
pending resolution of the FOXHELP found/not-found signal.
