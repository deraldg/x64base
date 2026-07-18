# Runtime Evidence, Source Verification, and Canary Closure




Pippets used:
- PIP-001 Target Selection
- MDO-180 Target Selection
- MDO-181 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches runtime proof, source verification, canary lifecycle, legacy evidence cautions, report-only boundaries, and no-mutation safety.
- Do not send this directly to generic PIP-003.
- Run a slow-lane runtime/source/canary review first.

Evidence tokens under review:
- runtime
- source
- SOURCE
- SOURCE_FACT
- SelfDoc
- manualgen
- PIP
- canary
- canary ledger
- smoke test
- shakedown
- regression
- proof
- verification
- evidence
- build
- release
- HELP
- CMDHELPCHK
- metadata
- crosswalk
- report-only
- no mutation

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Runtime proof should include concrete commands, output, build context, and date where possible.
- Source verification should identify implementation ownership and should not be demoted to sidecar evidence.
- Canary rows remain visible until closed with evidence.
- Closing a canary requires current evidence, not optimism or old design intent.
- Legacy documents may be useful context but should not be treated as current fact without verification.
- Manualgen and SelfDoc remain report-only unless explicitly authorized.
- HELP, CMDHELPCHK, and metadata can guide review but cannot close runtime or source canaries by themselves.
- Evidence packages should not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.

## Purpose of this section

This section explains how the Developer Manual should use runtime evidence, source verification, and canary closure.

It follows the HELP, Metadata, CMDHELPCHK, and Manualgen Alignment section because that section established the authority doctrine. This section operationalizes that doctrine into daily engineering practice: how runtime evidence is captured, how source verification is attached, how canaries remain visible, and how canaries are closed only with evidence.

The goal is not to turn every manual claim into a test case. The goal is to prevent unsupported claims from becoming permanent prose and to make sure important uncertainties remain visible until they are resolved.

## Evidence doctrine in practice

The working doctrine remains:

- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

In practice, this means a claim may need several evidence lanes before it is safe for final manual prose.

Examples:
- A command behavior claim needs runtime evidence.
- An implementation ownership claim needs source verification.
- A HELP wording claim needs HELP evidence.
- A metadata alignment claim needs metadata evidence.
- A consistency claim may need CMDHELPCHK evidence.
- A provenance claim needs SelfDoc or manualgen run evidence.

## Runtime evidence

Runtime evidence proves observed behavior.

Useful runtime evidence includes:
- exact commands that were run;
- exact output or relevant output excerpts;
- build configuration;
- release/debug mode;
- dataset or workspace used;
- command path or script path;
- date and session context;
- pass/fail result;
- any unexpected warnings or canary behavior.

Safe wording:
- Runtime evidence proves what was observed in that run.
- Runtime evidence should be labeled with enough context to reproduce or understand it.
- Runtime evidence does not automatically define implementation ownership.
- Runtime evidence can close behavior canaries when the observed behavior is current and relevant.

Examples of runtime evidence lanes:
- smoke test;
- shakedown;
- regression run;
- build output;
- release verification;
- manual command transcript;
- script output;
- comparison before and after a repair.

## Source verification

Source verification attaches implementation and ownership evidence.

Useful source verification includes:
- source file path;
- header path;
- function or class name;
- source-comment contract;
- source-miner report;
- SOURCE_FACT row;
- SelfDoc source-comment evidence;
- handler or parser ownership note;
- subsystem boundary note.

Safe wording:
- Source defines implementation and subsystem ownership.
- Source verification should identify the relevant file or owner where possible.
- Source may verify why runtime behavior occurs.
- Source is not merely a sidecar; it is authority for implementation structure.

Source verification is especially important for claims about:
- parser dispatch;
- command handlers;
- storage ownership;
- relation traversal ownership;
- expression evaluation ownership;
- memo payload lifecycle;
- message emission;
- backend boundaries;
- generated/help/metadata alignment.

## Runtime and source together

Runtime and source answer different questions.

Runtime answers:
- What happened in this run?
- What behavior can be observed?
- Did the smoke/shakedown/regression pass?

Source answers:
- Which subsystem owns the behavior?
- Which implementation path handles it?
- Is the observed behavior intentional, scaffold leakage, compatibility behavior, or a bug?

Safe wording:
- Runtime proves behavior.
- Source defines ownership.
- A strong manual claim often needs both.
- HELP, metadata, and CMDHELPCHK can guide the search, but they do not replace runtime/source evidence.

## Canary lifecycle

A canary is a visible uncertainty, risk, or proof-sensitive behavior that must not disappear silently.

A canary can be:
- open;
- deferred;
- narrowed;
- reproduced;
- partially closed;
- closed with evidence;
- superseded by a better canary;
- converted into an issue or work item.

A canary should not be:
- hidden because it is inconvenient;
- closed because the expected behavior seems obvious;
- closed because old design intent says it should work;
- closed using HELP, metadata, or CMDHELPCHK alone when runtime/source proof is required.

## Opening a canary

A canary should be opened when evidence shows a behavior, mismatch, ambiguity, or risk that could affect manual accuracy or project correctness.

Good canary records include:
- short name;
- observed behavior;
- evidence source;
- date or session;
- affected subsystem;
- proof needed for closure;
- current status;
- next recommended action.

Examples:
- SET ORDER active tag reporting.
- x64 workspace ERSATZ load reporting.
- MIN/MAX command/function ambiguity.
- AGGS internal family owner exposure.
- memo backend attach on workspace open.
- generated command page duplicate or slug collision.

## Keeping canaries visible

Canaries remain visible until closed with evidence.

Visibility matters because older project documents, generated reports, and runtime sessions can overlap. A canary keeps the manual honest by saying: this claim is not ready for final prose, or this behavior needs proof-sensitive wording.

Safe wording:
- Canary rows remain visible until closed with evidence.
- Canaries can be deferred, but deferred does not mean resolved.
- Canaries can be narrowed when evidence shows only part of the risk remains.
- Canaries should be carried forward in review reports until closed, superseded, or explicitly transferred.

## Closing a canary

Closing a canary requires current evidence.

Closure evidence may include:
- runtime run showing the behavior;
- source verification showing the implementation path;
- regression test output;
- smoke test result;
- CMDHELPCHK report when the canary is about HELP/catalog consistency;
- metadata readback when the canary is about metadata coverage;
- manualgen report when the canary is about assembly output;
- explicit human decision when the canary is a policy or surface decision.

Safe wording:
- Closing a canary requires evidence.
- The closure record should name the evidence.
- The closure record should preserve enough context to audit the decision later.
- Old design intent is not closure evidence by itself.

## Legacy documents

Legacy documents are useful context.

They may contain:
- old design intent;
- old architecture notes;
- historical problems;
- early terminology;
- superseded assumptions;
- useful examples;
- project memory.

But legacy documents should not be treated as current fact without verification.

Safe wording:
- Old documents remember.
- Recent summaries steer.
- SelfDoc verifies.
- Runtime proves.
- Source defines.
- Manuals explain.

Legacy evidence should be labeled when it is used:
- historical context;
- design intent;
- superseded note;
- unverified claim;
- candidate canary;
- verified current behavior.

## Smoke tests, shakedowns, regressions, builds, and releases

Different runtime evidence lanes serve different purposes.

Smoke test:
- quick proof that a feature or path starts and behaves basically as expected.

Shakedown:
- broader exploratory runtime evidence, often with manual commands and transcript notes.

Regression:
- evidence that a previously fixed or expected behavior still works.

Build:
- evidence that code compiles and links in a given configuration.

Release:
- evidence attached to a release-ready state, usually after build and smoke checks.

Safe wording:
- Build success is not behavior proof.
- Smoke success is limited behavior proof.
- Shakedown is useful runtime evidence but should be scoped.
- Regression evidence is strong for previously known behavior.
- Release evidence should identify build configuration and major checks.

## REGRESSION and TEST as proof launchers

`REGRESSION` and `TEST` make repeatable proof entry points discoverable, but
neither command makes a run self-proving. Retain the exact command, selected
script or suite, build identity, transcript, and result counts when using either
launcher as evidence.

### REGRESSION

`REGRESSION [USAGE|LIST|SHOW <name>|RUN <name>|<name>|ALL]` selects from a
curated set of stable regression and shakedown scripts. `LIST` and `SHOW` expose
the curated entries; `RUN <name>` and the compact `<name>` form launch one
entry; `ALL` launches the defined ordered set. The command delegates execution
to `DOTSCRIPT`, so it is a catalogued launcher rather than a separate test
engine. Developer reproduction canaries that are not in the curated set remain
outside `ALL`.

### TEST

`TEST <scriptfile> [<logfile>] [VERBOSE]` runs a specified test script through
the shell test harness. The harness resolves the script path, handles supported
inline comments and continued logical commands, executes those commands, and
reports processed and error counts. A supplied logfile may be created or
truncated. The script controls the resulting side effects, so `TEST` must not be
classified as read-only merely because it is used for verification.

### Evidence boundary

Launcher availability proves only that the entry surface exists. A proof claim
still requires the retained run inputs and outcome. Cross-reference the
Scripting and Control Flow section for script semantics and Runtime Operation,
Invocation, and Automation for entry-path behavior.

## HELP, CMDHELPCHK, and metadata in evidence practice

HELP, CMDHELPCHK, and metadata are powerful review guides.

They can:
- identify expected command vocabulary;
- expose missing help or command topics;
- organize arguments, messages, variants, and functions;
- detect catalog/help drift;
- point to canaries;
- guide runtime/source verification.

They cannot by themselves:
- prove runtime behavior;
- define implementation ownership;
- close runtime canaries;
- close source ownership canaries.

Safe wording:
- HELP explains.
- CMDHELPCHK validates.
- Metadata organizes.
- Runtime/source evidence closes runtime/source canaries.

## SelfDoc and manualgen evidence

SelfDoc preserves provenance. Manualgen assembles.

SelfDoc evidence may include:
- source-comment contract reports;
- SOURCE_FACT rows;
- source inventory;
- classifier reports;
- diagram reports;
- canary ledgers;
- provenance notes.

Manualgen evidence may include:
- pippet run records;
- target selection reports;
- draft fill reports;
- slow-lane reviews;
- PIP-003 evidence gates;
- PIP-004 reviewed candidates;
- PIP-005 human decisions;
- PIP-006 promotion patches;
- promoted draft workspaces.

Safe wording:
- SelfDoc and manualgen are evidence systems.
- They default to report-only.
- They must not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.
- Production mutation requires explicit authorization.

## Evidence crosswalks

Crosswalks connect evidence lanes without collapsing them.

Useful crosswalks include:
- runtime transcript to canary row;
- canary row to source file;
- source file to SOURCE_FACT;
- HELP topic to command identity;
- command identity to SYSCMD;
- function claim to SYSFUNC;
- diagnostic claim to SYSMSG;
- argument claim to SYSARGS;
- alias/variant claim to SYSENTVAR;
- manual section to evidence tokens;
- PIP report to promoted draft section.

Safe wording:
- Crosswalks preserve traceability.
- Crosswalks can be candidate, partial, or verified.
- Crosswalks should not pretend a weak source is strong evidence.
- Crosswalks help future metadata feeders absorb temporary evidence.

## Future META alignment

This section should eventually align with evidence metadata.

Expected future feeders and evidence lanes:
- SOURCE_FACT for source/comment provenance and implementation ownership evidence.
- SRCFILE, SRCBLOCK, SRCLINE, SRCUSAGE, SRCCLASS, SRCDISP, SRCALIAS, and MEMO_LINES for SelfDoc source-comment evidence where available.
- SYSCMD and SYSSUBCMD for command and subcommand identity tied to evidence.
- SYSFUNC for function evidence and function-command bridge canaries.
- SYSMSG for diagnostic and message canaries.
- SYSHELP for help alignment and curated help evidence.
- SYSARGS for argument-shape evidence and validation surfaces.
- SYSENTVAR for aliases, variants, and command/function entry variants.
- Manualgen PIP reports for gate evidence and assembly provenance.
- Canary ledger reports for open, deferred, reproduced, narrowed, and closed canary rows.

## No-mutation safety

Evidence packages should not mutate production artifacts during manual draft assembly.

Default boundary:
- no generated command page deletion;
- no HELP mutation;
- no META mutation;
- no CMDHELPCHK mutation;
- no catalog apply;
- no source edits;
- no runtime data mutation;
- no production SelfDoc metadata promotion;
- no final publication.

Report-only work is the default.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- runtime proof concrete commands output build context date
- source verification implementation ownership not sidecar
- canary rows visible until closed with evidence
- canary closure requires current evidence not optimism old design intent
- legacy documents context not current fact without verification
- manualgen selfdoc report-only unless authorized
- help cmdhelpchk metadata guide not close runtime source canaries
- build smoke shakedown regression labeled dated
- evidence packages no mutation
- canary deferred narrowed reproduced closed not disappear

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.


## Canary non-disappearance boundary

This exact review anchor is intentionally retained for slow-lane evidence review:

- A canary may be deferred/narrowed/reproduced/closed, but should not disappear silently.

The anchor is not final user-facing prose by itself. It preserves the boundary already described in this section: canaries remain visible until closed, superseded, transferred, or explicitly deferred with evidence.
## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- runtime proof concrete commands/output/build/date boundary is present;
- source verification/implementation ownership boundary is present;
- canary visibility and closure rules are present;
- old design intent and legacy documents are not treated as current fact without verification;
- HELP/CMDHELPCHK/metadata are review guides, not canary closure evidence by themselves;
- build, smoke, shakedown, regression, and release evidence are scoped correctly;
- SelfDoc/manualgen report-only and no-mutation boundaries are visible;
- future META/evidence feeders are preserved.

Recommended required tokens for later PIP-003:
- runtime
- source
- SOURCE
- SOURCE_FACT
- SelfDoc
- manualgen
- PIP
- canary
- canary ledger
- smoke test
- shakedown
- regression
- proof
- verification
- evidence
- build
- release
- HELP
- CMDHELPCHK
- metadata
- crosswalk
- report-only
- no mutation

## Boundary

- prose draft fill only
- slow-lane review still required
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion


