# Unfiled -- salvaged content with accidental filenames

**Created:** 2026-08-15 by `member.ai.claude.cowork`, owner-directed housekeeping.
**Nothing was deleted.** Eight files were renamed and moved here from
`docs/maintenance/`. Content is byte-identical; only the names changed.

## Why these existed

Each file's name was its own first line with path separators stripped -- the
signature of a paste landing in a "new file" prompt, or a shell redirect that
took the command as the filename. They were untracked, sitting in a tracked
documentation directory, and unfindable by name.

None of them was junk. Two are working recipes, one is a house rule, three are
notes with open questions, one is a pointer, one is terminal ephemera.

## Contents and disposition

| File | Was | Disposition |
|---|---|---|
| `RULE_housekeeping_completes_the_task.txt` | `A task isn't done until the houseke.txt` | **Needs filing as doctrine.** See below. |
| `RECIPE_manualgen_build_reference_candidate.txt` | `& $py12 .toolsmanualgen...` | Working `manualgen build-reference-candidate` invocation. `build-reference-candidate` appears in no `.md` under `docs/` or `tools/` -- this is the only written copy. Candidate for the full-stack flush cookbook. |
| `RECIPE_sysfunc_five_functions_runsheet.txt` | `Before I hand you commands, let me.txt` | Ordered runsheet to take PROPER/PADL/PADR/PADC/STUFF green and re-harvest SYSFUNC to clear `normcheck FN_COVERAGE`. Verify whether it was executed; if so it is history, if not it is an open task. |
| `NOTE_lmdb_index_tag_updating_open_question.txt` | `lmdb works end to end, behind the s.txt` | Design observation ending "thoughts???" -- an unanswered question about index tag updating to disk given mutation points already exist in replace/calcwrite/delete/commit/recall. |
| `NOTE_expectation_vs_availability_gap_spanning.txt` | `expectation vs availability  and ga.txt` | Teaching-point sketch on gap spanning; ends "speculate, report?" -- also unanswered. |
| `NOTE_onboarding_prompt_fragment.txt` | `I forgot you are a new chat. Find t.txt` | Onboarding prompt fragment (AI memory retention, educational/experimental framing). Superseded by the portal onboarding docs; keep or discard. |
| `POINTER_gptbase_custom_gpt_url.txt` | `httpschatgpt.comgg-6a62abde...txt` | The GPTbase custom-GPT URL, listed twice. GPTbase is `member.ai.chatgpt`, a registered advisor -- if this URL is not in `labtalk/registries/apps.yaml`, it should be. |
| `EPHEMERA_ollama_status_check_paste.txt` | `derald@Grimwoodmntc...$.txt` | Terminal paste: ollama active, `127.0.0.1:11434`, `qwen2.5-coder:7b` present. Point-in-time diagnostic, 2026-07-25. No lasting value. |

## The rule that did not get filed

> A task isn't done until the housekeeping is finished.

**Where it belongs:** `labtalk/ai_portal/AI_TIER1_SEED_V1.md`, section 5
("Document as you work") or 6 ("The one habit that matters"). It is an
invariant, not perishable state, so it passes the seed's content test.

**Why it was not filed here:** the seed's own maintenance contract says
"Adding requires demoting, and demoting means moving," and
`check-seed-budget` currently reports **7959 B of 8192 B, 233 B headroom**.
Promoting this rule means deciding what leaves the seed. That is an owner
decision against a gated file, not a scribe edit. Contract:
`TIER1_MAINTENANCE_CONTRACT_V1.md`.

**Worth knowing before you decide:** the rule may already be filed in
operational form. The seed's trigger table reads:

> close out work | update what you made stale; **leave a handoff, not only a
> closeout**

That is the same instruction as a procedure. What the aphorism adds is a
*definition of done* rather than a step in a checklist -- which is arguably
worth its own line, and arguably already covered. Owner's call.

**Three options:**

1. Promote to the seed, demoting something else per the contract.
2. Leave it operational -- treat "update what you made stale" as sufficient and
   discard the aphorism.
3. File it in a non-gated doctrine doc where phrasing can live without competing
   for seed bytes.

## Cleanup

This directory is a triage staging area, not a destination. When each item is
filed, executed, answered, or discarded, remove it. When the directory is empty,
remove the directory. Deleting files is the maintainer's to do; the scribe moved
and renamed only.
