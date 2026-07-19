warning: in the working copy of '.gitignore', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'AI_PORTAL.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'AI_README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/agents/CURRENT_TARGET.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/ai-friendly/AI_FRIENDLY_WORKFLOW_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/contracts/CONTRACT_REGISTRY_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/EDITION_PUBLICATION_PLAN_A_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/PINOCCHIO_STRESS_TEST_PLAN_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/maintenance/lanes/full_stack_documentation/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'labtalk/ai_portal/PROMOTION_MODEL_SEED_V1.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'labtalk/ai_portal/README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tools/staging/rebuild-staging.ps1', LF will be replaced by CRLF the next time Git touches it
[1mdiff --git a/.gitignore b/.gitignore[m
[1mindex 84f81cdc..e0cec8e4 100644[m
[1m--- a/.gitignore[m
[1m+++ b/.gitignore[m
[36m@@ -39,6 +39,7 @@[m [mDartConfiguration.tcl[m
 [m
 # Local environments[m
 .venv/[m
[32m+[m[32m.venv312/[m
 .vscode/[m
 [m
 # Local runtime state[m
[1mdiff --git a/AI_PORTAL.md b/AI_PORTAL.md[m
[1mindex 0feda4eb..19f3df93 100644[m
[1m--- a/AI_PORTAL.md[m
[1m+++ b/AI_PORTAL.md[m
[36m@@ -149,6 +149,36 @@[m [mReport each state separately:[m
 [m
 Never claim a later state merely because an earlier one succeeded.[m
 [m
[32m+[m[32m### Document As You Work (AIF-024)[m
[32m+[m
[32m+[m[32mCloseout is a **rollup, not a reconstruction**. Document each material step as it[m
[32m+[m[32mhappens, while the facts are still in hand — do not defer all recording to the[m
[32m+[m[32mend and re-derive it from memory or the chat.[m
[32m+[m
[32m+[m[32mA step is material (and gets recorded when it lands, not later) when it:[m
[32m+[m
[32m+[m[32m- changes source, data, or an AI-facing doc;[m
[32m+[m[32m- produces a build or proof result, a hash, or a measured number;[m
[32m+[m[32m- makes a decision that constrains later work, or discovers a finding.[m
[32m+[m
[32m+[m[32mRecord it in the appropriate durable place as you go: the running Session[m
[32m+[m[32mCloseout / progress log, an intake or contract row, a proof transcript with its[m
[32m+[m[32mhash. The chat is never the record. If a step's evidence (a hash, a timing, a[m
[32m+[m[32mbefore/after count) is not captured at the moment it is produced, it is treated[m
[32m+[m[32mas **not proven** — a later recollection does not substitute.[m
[32m+[m
[32m+[m[32mRationale, recorded so it is not relitigated: reconstructing a session's trail at[m
[32m+[m[32mthe end loses the evidence that was cheapest to capture in the moment (exact[m
[32m+[m[32mhashes, timings, the reason a path was rejected) and invites overclaiming. The[m
[32m+[m[32m2026-07-16 corrective audit (AIF-021) is the worked example — a session that[m
[32m+[m[32mdeferred its records understated its own diff, skipped the Session Log row, and[m
[32m+[m[32mcalled surfaces ready before proof. Documenting continuously makes AIF-006[m
[32m+[m[32mcloseout a summary of an already-written trail instead of a scramble.[m
[32m+[m
[32m+[m[32mThis does not add a new artifact. It uses the same durable places AIF-006 and the[m
[32m+[m[32msession-closeout convention already name; it only fixes **when** they are written[m
[32m+[m[32m— continuously, not at the end.[m
[32m+[m
 ### Closeout Updates Startup (AIF-006)[m
 [m
 If a session changed **lane state** — a new or superseded contract, a promoted[m
[1mdiff --git a/docs/agents/CURRENT_TARGET.md b/docs/agents/CURRENT_TARGET.md[m
[1mindex ec628c3e..7cc1ca67 100644[m
[1m--- a/docs/agents/CURRENT_TARGET.md[m
[1m+++ b/docs/agents/CURRENT_TARGET.md[m
[36m@@ -1,38 +1,75 @@[m
 # Current Target[m
 [m
 Status: active.[m
[31m-Updated: 2026-07-15.[m
[32m+[m[32mUpdated: 2026-07-19.[m
 Supersedes: the completed staging-restoration/publication target recorded below.[m
 [m
[32m+[m[32m## Development Focus Update — 2026-07-19[m
[32m+[m
[32m+[m[32mThe maintainer-gated promotion objective below (reconcile public corrections into[m
[32m+[m[32mdevelopment, then push reviewed staging) is unchanged and still open — no branch,[m
[32m+[m[32mcommit, or push has been made, and `C:\x64base`/GitHub are untouched.[m
[32m+[m
[32m+[m[32mActive development since 2026-07-16 has been in the Pinocchio scale/durability[m
[32m+[m[32mlane (AIF-017 / AIF-023), all in `D:\code\ccode` on the existing branch and all[m
[32m+[m[32mdev-only (not promoted):[m
[32m+[m
[32m+[m[32m- **Scale-verb hardening (Phase 1.3).** The scale sweep's remaining O(n) verbs[m
[32m+[m[32m  are fixed and hash-bound proven: `SEEK` keyed range-seek (57s → ms), `DELETE`/[m
[32m+[m[32m  `RECALL` bulk write-transaction batching under an active order (65.4s → 37.8s),[m
[32m+[m[32m  `AGGS ALL` single-pass multi-aggregate (~4×), plus the earlier nav `TOP`/`SKIP`[m
[32m+[m[32m  LMDB-cursor fix. Companion `SET FILTER`/aggregate `FOR` string-literal fix.[m
[32m+[m[32m- **Table-buffer durability WAL (AIF-023).** `COMMIT`/`ROLLBACK` are now[m
[32m+[m[32m  crash-recoverable via a durable `.tbj` redo log (three teed-transcript phases:[m
[32m+[m[32m  durable writer, recovery-on-open, buffered `DELETE`). Enabled only under[m
[32m+[m[32m  `TABLE BUFFER PERSISTENT`; default RamOnly behavior unchanged; the[m
[32m+[m[32m  multiple-retained-edits-per-field capability is preserved (added[m
[32m+[m[32m  `TABLE BUFFER HISTORY ON|OFF`). Scoped durability gain, not a full-ACID claim;[m
[32m+[m[32m  DBF-`fsync` and CDX/LMDB reconciliation remain open hardening.[m
[32m+[m
[32m+[m[32mCloseouts and Session Log rows are recorded in[m
[32m+[m[32m`docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`; the durability lane is intake row[m
[32m+[m[32mAIF-023. None of this changes the authority chain or the promotion gate below;[m
[32m+[m[32mit is queued behind the same maintainer-reviewed staging commit/push.[m
[32m+[m
 ## Current Objective — Reconcile Public Corrections Into Development[m
 [m
 Public AI Portal consistency work was completed through:[m
 [m
 - `100169433b583e5f51eafdeea130607d71942376` — public-state reconciliation;[m
[31m-- `a0cf52654c4f8e834e969e3c2524fd397d627a95` — canonical AI startup path.[m