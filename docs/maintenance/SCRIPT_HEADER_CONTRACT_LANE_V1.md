# Script Header Contract — lane (`@script.usage`) v1

Status: **proposed / dev** — contract-system schema extension. Not promoted, not built.
Parent project: `project.x64base.runtime` (AIF-040).
Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-042).
Folds under: AIF-041 M4 (`dotref`/`foxref` maintainability — the "generate/reconcile from
contracts" question) and the COMMENTS pipeline doctrine
(`COMMENTS_HELP_PROOF_WORKFLOW_v1.md`, which governs `@dottalk.usage`).

## What this lane is

The `@dottalk.usage v1` contract system documents **C++ command behavior** at the source
and harvests it (COMMENTS → `SRC*` tables → CMDHELP → CMDHELPCHK → HELP/DOTREF). The gap
this lane closes: **script files** (`.dts`, `.ps1`, and later `.sh`, generators, etc.) have
no standardized, harvestable, reconcilable header contract. Some are richly commented, many
are not, and nothing checks a script's header against what the script actually is.

This lane establishes a **language-neutral, file-level script-header contract** — working
name **`@script.usage v1`** — with one harvester, one schema, and per-kind reconciliation,
so a script's own header becomes the single source of truth for what it is, how to run it,
and what it touches.

## Research preserved — design decisions (2026-07-21, maintainer + Claude/Cowork)

**Naming.** The token is **`@script.usage`**, deliberately *not* `@dotscript.usage`.
Rejected `@dotscript.usage` because it (a) names one language and (b) reads like a
*language-construct* usage doc (VAR / `$name` / subscripts), which is a different thing.
The contract here is **file-level and language-agnostic**. `@dottalk.usage` documents a
command; `@script.usage` documents a *script file*.

**Language is a field, not the token.** `@script.usage` + `runner: dts` vs
`runner: powershell`. One token, many comment syntaxes (the harvester strips the host
comment prefix — `*` / `&&` / `#` / `//` for `.dts`, `#` / `<# #>` for `.ps1` — then reads
the block, exactly as it strips `//` for C++ today). This is the "one harvester,
discriminate by a column" principle: the alternative (`@dotscript.usage` + `@pwsh.usage` +
`@bash.usage`) rebuilds N parsers and N drift surfaces — an AIF-037 (Rule of Three)
violation.

**Three contract KINDS, one pipeline.** After this lane the contract vocabulary has three
kinds, harvested by **one** COMMENTS harvester into **one** `SRC*` schema with a `KIND`
(namespace) column — never three forks:

| KIND | Where | Documents | Reconciles against |
|---|---|---|---|
| `@dottalk.usage` | C++ `cmd_*.cpp` | command behavior | command registry (existing) |
| `@x64base` (fact) | C++/headers | format/provenance facts → `SOURCE_FACT` | the actual struct/constant |
| `@script.usage` | `.dts` / `.ps1` / … | script-file manifest | the file + (for proofs) `kRegressionSpecs` |

**Grounded findings (sampled 2026-07-21):**
- `.dts` headers are **inconsistent**: the newer regression scripts carry rich structured
  headers (Purpose / Run / Pass-criterion / environment-bootstrap / mutates); older ones
  (`main/rel_join_enum_regression.dts`) have **no** structured header at all — proof the
  convention is emergent and needs ratifying, not inventing.
- `.ps1` **already has a native structured convention** — PowerShell comment-based help
  (`.SYNOPSIS` / `.DESCRIPTION` / `.PARAMETER` / `.EXAMPLE` / `.NOTES`), seen in
  `clean_dottalkpp_staging.ps1`. **The standard must align with / map onto comment-based
  help, not replace it** — extend it with the governance fields (`mutates` / `safety` /
  `lane`) via `.NOTES` or a tagged line, so PowerShell tooling (`Get-Help`) still works.

**Two payoffs that justify the lane beyond tidiness:**
1. **`.ps1` safety.** Dozens of PowerShell scripts, many destructive
   (`clean_dottalkpp_staging*.ps1`, `backup_*`, `stage_*`). A standardized `mutates:` /
   `safety:` header is a real, practical guardrail for anyone (human or AI) about to run
   one blind.
2. **Regression `.dts` drift-check for free.** A `@script.usage` block on a regression
   `.dts` reconciles against its `kRegressionSpecs` entry (name / summary /
   `in_default_suite`) — the same CMDHELPCHK idea, now for scripts. Closes the exact gap
   where a registry summary and a script's real behavior silently diverge.

## Draft `@script.usage v1` field spec (ratified from existing headers)

Distilled from the good `.dts` headers already in the tree (not invented). Fields:

- `id` — script stem / logical name (harvester keys on this, **not** the filename, so
  multi-per-file works and rename churn doesn't break the catalog).
- `summary` — one line.
- `runner` — `dts` | `powershell` | `bash` | … (the language discriminator).
- `run` — exact invocation (e.g. `REGRESSION RUN DOTSCRIPT_EXPR`, or the `.ps1` command line).
- `preconditions` — open table? path slots? env? (`none` for fixture-free).
- `mutates` — `none` | `session` | `filesystem` | `data` | `journal` | … (comma-list).
- `safety` — `read-only` | `self-cleaning` | `throwaway-fixture` | `destructive`.
- `expected` / `pass-criterion` — for proof/regression scripts (the marker contract).
- `owner` / `lane` — AIF / lane id.
- `related` — other scripts, commands, or registry entries.
- `status` — `candidate` | `supported` | `deprecated`.

Version marker: the block opens `@script.usage v1`; each namespace versions independently
of `@dottalk.usage`.

## Milestones

- **M0 — inventory + spec ratification.** Inventory `.dts` and `.ps1` headers (grounded:
  some rich, some none; `.ps1` has native comment-based help). Finalize the
  `@script.usage v1` field set from what exists. Write `SCRIPT_HEADER_CONTRACT_V1.md`
  doctrine doc (the `@script.usage` analogue of `COMMENTS_HELP_PROOF_WORKFLOW_v1.md`).
- **M1 — harvester extension.** Extend the COMMENTS harvester to read `@script.usage`
  blocks across comment syntaxes (strip host prefix); add the `KIND`/`NAMESPACE` column to
  `SRC*`; key on the block `id` field (multi-per-file safe — heed the
  `cmd_var_integration_example` collision precedent). Define the `.ps1` comment-based-help
  mapping.
- **M2 — `.dts` backfill (proofs first).** Apply `@script.usage v1` to the curated /
  REGRESSION-registered `.dts` first (headers already close), then the rest. Add the
  header ↔ `kRegressionSpecs` reconciliation check.
- **M3 — `.ps1` backfill (destructive first).** Apply to `.ps1`, prioritizing destructive
  scripts (clean / stage / backup), aligning with comment-based help; surface
  `mutates` / `safety`.
- **M4 — reconciliation gate.** A CMDHELPCHK-style check that every declared
  `@script.usage` harvests **and** reconciles against its backing registry (file exists;
  regression scripts match `kRegressionSpecs`). Wire into CI / REGRESSION so the vocabulary
  is under the evidence gate, not a trust-me convention.
- **M5 (stretch) — other languages / repos.** Extend to `.sh`, the website/manual
  generators, and any other scripting surface once the `.dts`/`.ps1` pattern is proven.

## Relationship to other lanes

- **AIF-041 M4** asks whether `dotref`/`foxref` should be *generated from contracts* rather
  than hand-maintained. This lane is the same "contracts are the source of truth, reconcile
  don't hand-edit" principle applied to the script surface — they inform each other.
- **COMMENTS pipeline** owns the harvest→HELP→CMDHELPCHK machinery this lane extends.
- **REGRESSION** (`kRegressionSpecs`) is the backing registry for proof-`.dts` reconciliation.

## Non-goals / honesty

- Not a runtime feature — this is documentation/governance vocabulary, harvested and
  reconciled, not executed.
- Not a replacement for PowerShell comment-based help — it **aligns with** it.
- Not promoted until the harvester extension is built and the reconciliation gate is proven
  (runtime proves). Dev-only.

## Provenance

- Design conversation: Claude / Cowork, 2026-07-21 (this session), at maintainer direction
  ("bundle this into a lane with your research preserved").
- Sampled evidence: `dottalkpp/data/scripts/main/rel_join_enum_regression.dts` (no header),
  the 2026-07-21 regression `.dts` (rich headers), `clean_dottalkpp_staging.ps1` +
  `build.ps1` (`.ps1` header conventions).
- Parent project: `project.x64base.runtime`. Related: `@dottalk.usage` doctrine
  (`COMMENTS_HELP_PROOF_WORKFLOW_v1.md`), AIF-041 (BETA-1 stabilization, M4).
