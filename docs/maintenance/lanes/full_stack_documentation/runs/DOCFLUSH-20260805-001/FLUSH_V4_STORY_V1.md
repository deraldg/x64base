# The Flush: a day in the DotTalk++ documentation lane

*A narrative history of run DOCFLUSH-20260805-001 -- full-stack documentation
flush v4 -- from the first rename to the closed development-tree run, including the
detour that nearly duplicated a lane and the lessons that came out of both.*

Recorded 2026-08-05. Steward: `member.ai.claude.cowork`. Owner and final
authority: `member.derald`.

## Prologue: why "flush"

DotTalk++ is a modern C++ xBase runtime with a large surface: hundreds of
commands, a family of reference authorities (dotref, foxref, edref, pshell_ref,
sql_ref, the reserved devref, and SYSFUNC for expression functions), a HELP
data store rebuilt from source, a website that projects the command catalog, and
a manual generated from a HELP/META harvest. A "documentation flush" is the
disciplined pass that walks all of that back into agreement with the source -- and
does it by the book, with a numbered gate at every step so nothing ships on a
hunch. This was the fourth such pass. The owner named the lineage plainly: v1 by
hand, v2 and v3 pushing the assistant, v4 guiding it.

## Act 1 -- A name that was doing two jobs

The day opened on a small thing that turned out to be a big thing: the word
"Reports." Internally it meant AI-operational pages; publicly it implied reviewed
public-interest reports. The fix was a rename to **AI** across two repositories --
the engine tree and the website tree -- touching nav labels, portal links, the
public bootstrap, and the command-catalog page. A stray 404 on `/AI/console` traced
to a port-reuse bug, and a small launcher, `start-ai.ps1`, brought the site and
gateway up cleanly. Housekeeping followed: track the launcher, hand off the slice.

That naming itch -- Reports versus AI -- would resurface hours later from an
unexpected direction.

## Act 2 -- Contracts, everywhere

The heart of the flush is contract coverage. Every source file carries a
`@dottalk.file` header; every command file adds a `@dottalk.usage` block; and the
work widened to non-command files and other prefixes (`edu_`, `app_`). A new idea
crystallized here: `@dottalk.external`, an OS-boundary contract for commands that
reach outside the engine. Its first home was `EDIT`, which spawns an external
editor -- os-sensitive, not reversible, egress none. A concept doc,
`EXTERNAL_CALL_CONTRACT_V1`, gave the idea a place to live.

The doc-push pipeline took shape in parallel: harvest source comments, sync the
website command catalog, validate, commit. One stubborn holdout was `DDICT`, whose
contract used a block form the website extractor could not read. Normalizing it to
the standard `// @dottalk.usage` form dropped the catalog's unreadable-contract
fallback to zero.

## Act 3 -- Making the references agree

DotTalk++ keeps native commands in dotref and FoxPro-compat entries in foxref.
Both had drifted. The pass added an AI-systems cluster to dotref -- `BBS`, `NET`,
`CANARY` -- and then `CMDREL`, `FORMULA`, `EDIT`; it de-duplicated `NORMALIZE` and
five browser aliases out of foxref. A reference existence guard (`refcheck`) came
back clean.

Then the process itself got a lesson. A first attempt hand-rolled a
reference/authority crosswalk instead of using the lane's own prior-art tools. The
owner called it: the job is to improve the process, but you need the prior art and
have to pay attention. The redo used the real tools --
`build_reference_identity_inventory`, `build_reference_authority_crosswalk`, and the
authority contract that says disagreement produces a review row, never a silent
replacement. A new report-only recommender attached a disposition to each review
row and collapsed 95 rows to ten genuine decisions -- surfacing two real defects
(duplicate `EXAMPLE` and `SQLHELP` registrations) that were deferred, with
evidence, to a follow-up lane.

## Act 4 -- The baseline and the mojibake

Before touching the HELP build, the pass captured a pre-refresh runtime baseline
and reviewed it as Gate 2: reflection PASS, manual catalog complete, 525 topics.
The baseline earned its keep immediately. In the captured HELP text, the
`BUILDVECTORS` summary rendered a three-character garble -- a U+2014 em-dash in
`cmd_buildvectors.cpp` read as CP437. It was one instance of a class: source
comments carrying non-ASCII that the house-style gate misses because it only checks
*added* lines. The finding was recorded for a dedicated ASCII sweep rather than
chased mid-flush. (Fittingly, the review doc that recorded it first tripped the
gate by quoting the garble verbatim -- fixed by describing it in ASCII instead.)

## Act 5 -- The authorized rebuild

A HELP refresh is a mutation, so it gets a package and a gate. The package asked
the real questions: why build, which inputs changed, what files change, backup and
rollback, post-build checks. A key point was settled here by the owner: foxref
feeds the LEGACY store, so a `CMDHELP BUILD LEGACY` was required -- not merely for
provenance -- to reflect the foxref de-duplication. The authorized sequence ran
LEGACY first, then `CMDHELP BUILD . <src>`. Gate 4 validation showed exactly what
the package predicted: the primary HELP DATA was already current and rebuilt
idempotently, while the LEGACY store carried the real delta -- the browser
duplicates gone, `NORMALIZE` singular. All nine touched topics resolved. And the
`BUILDVECTORS` mojibake now sat visibly inside the HELP data, proving the deferred
finding exactly where predicted.

## Act 6 -- The website, honest again

The website command catalog is a derivative. Regenerating it produced a two-line
diff: the snapshot count ticked up by one and `DDICT` flipped from an unreadable
fallback to a fully curated row. The entire flush's public-catalog footprint was
that single honest change; everything else lived in the engine's HELP and reference
layers. The host interpreter briefly got in the way -- the generator needs Python
3.12 and the host defaulted lower -- so the verified output was written directly and
committed on the site repo as its own slice.

## Act 7 -- The detour: a note in a file

Then the day turned. A stray file at the repository root -- named, literally, like a
sentence: "we have a weak naming the reports.txt" -- turned out to be a note from
the owner. Its low-priority half was the Reports-versus-AI naming from the morning.
Its high-priority half asked for a cross-walk of the AI systems (AI Portal,
Pseudo-Chat, BBS, onboarding) and a prior-art scan.

The scan was done -- and done wrong. It produced a fresh crosswalk and a new lane
number without first discovering that the work already existed. The owner's git
status gave it away: an entire **AI Systems Integration SDLC** already lived under
`docs/maintenance/`, lane AIF-086, with a charter, requirements, a needs
assessment, and M0 plus M1 closeouts dated the same day as the note, stewarded by
another agent. The duplicate had looked in the AI-portal folders; the real lane
lived in maintenance.

The correction was made the way that lane's own rules demand: revert the duplicate
and the competing number, and record the mistake rather than bury it -- as defect
D12, a second occurrence of the lane's existing lesson about scans that start
before discovery is complete. The owner then assigned the steward role across, and
approved M1. Following the charter, the assistant recorded the steward change while
preserving the prior author (a correction preserves the superseded record), logged
the owner's M1 exit approval that the committed docs still showed as pending, added
one genuinely new component the earlier census predated -- the `NET EGRESS` network
capability -- and drafted the M2 component/edge model with every node pinned to a
single system of record. A run fragment and a session closeout followed; the
closeout first bounced off the report-audit gate for missing its provenance
envelope, then passed once the envelope was added. The detour was parked, cleanly,
with everything recorded.

The lesson wrote itself: prior-art discovery searches the lane's home and the claim
ledger first, not just the folders where you expect the answer.

## Act 8 -- Back to the flush: the tool that hid its instructions

Phase 5 is metadata. `metacollect` -- a standalone C++ reflection tool, no launcher,
its own build target -- re-reflected the source and emitted seed candidates: 226
SYSCMD, 74 SYSFUNC, 959 SYSARGS rows, candidate-only, imported nowhere. The owner
made a pointed request: it would have been nice not to have to search for how to run
this each time. So metacollect got documented -- an `@dottalk.external` contract on
the source (it is, after all, an external app) and a runbook capturing the build,
the flags, the outputs, and the last run's numbers. When the candidate CSVs did not
commit, it turned out to be by design: the repo does not save what it can recreate,
and run-directory CSVs are deliberately ignored. The gate record was amended to say
so.

Phase 6 is the manual. Its tool insisted on Python 3.12 -- but the owner pointed out
that the other Python work had run fine on the sandbox's 3.10. It did:
inventory, validate, export-manifest, and a build-dry-run all completed, with zero
boundary violations and the only validation failure being the interpreter
self-check itself. The manual candidate assembled -- though its harvest predated the
Phase 4 rebuild, so a re-harvest was recorded as the follow-up to include the new
commands.

## Act 9 -- Counting the gates

Near the end, the owner asked a simple question that caught a real error: how many
phases are there? The claim of "complete through every phase" was wrong. The plan
runs Phases 0 through 7 with Gates 0 through 7; a richer historical run had gone to
nine gates for full public promotion. Phase 7 was not done. So Phase 7 was done
properly: a five-state pointer review (candidate, accepted manifest, active reader,
publication manifest, website projection) that found one honest drift -- the manual
reader lagging the new commands -- and a development-run closeout that separated
dev-refresh, candidate generation, promotion, staging, commit, and push. Gate 7's
rule is precise: the development-tree run closes before any public push is claimed,
and website publication is handed to its own lane. It was, and it was.

## Epilogue: what the day taught

Four lessons outlived the run.

**Search the home first.** The most expensive mistake was re-deriving work that
already existed because the search looked in the obvious folders, not the lane's
home. Discovery is not housekeeping; it is the first gate.

**Do not save what you can recreate.** Generated CSVs, regenerable candidates,
interpreter-specific report snapshots -- the repo tracks the record that binds them
by hash, not the artifacts themselves.

**The gates are the guardrail, and they catch you too.** A non-ASCII em-dash, a
missing provenance envelope, an over-claimed "complete" -- each was caught, by a
gate or by the owner, and each correction was recorded rather than smoothed over.

**Hand public work to its own lane.** A green development run is not a publication.
The flush closed the development tree and stopped there, deliberately.

Eight gates in the plan, all accounted for; the ninth-gate public arc left to its
own lane; a detour survived and turned into a teaching case. The development-tree
run DOCFLUSH-20260805-001 is closed.
