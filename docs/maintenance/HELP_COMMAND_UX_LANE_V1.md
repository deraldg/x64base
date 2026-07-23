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
