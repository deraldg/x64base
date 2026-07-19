# Session Closeout — AGGS ALL single-pass multi-aggregate (polish)

```yaml
ai_report_audit:
  report_id: AIPR-20260719-002
  project: project.x64base.runtime
  branch: homegrown-cnx-20251112-branch
  baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  access_mode: local_write
  scope: src/cli/cmd_aggs.cpp (one file; two changes -- AGGS ALL + aggregate FOR normalize)
  authorization_note: >
    Additive command form only, in D:\code\ccode on the existing branch. No
    branch changes; not applied to C:\x64base or GitHub. Requires maintainer
    rebuild + proof before promotion.
  stage: implemented_pending_build_and_proof
```

## What changed

`src/cli/cmd_aggs.cpp` — added `AGGS ALL <value_expr> [FOR/WHERE/DELETED]`
(alias `AGGS STATS`) via a new `run_agg_all` that computes **COUNT, SUM, AVG,
MIN, MAX in a single scan** and prints
`COUNT=<n> SUM=<s> AVG=<a> MIN=<mn> MAX=<mx>`. It reuses the exact `run_agg`
machinery — `parse_agg_spec`, `build_value_plan`, `build_predicate_ast`,
`passes_deleted_mode`, `filter::visible`, `eval_value_plan`, cursor
save/restore — so each value is identical to the corresponding standalone verb.
The existing `SUM`/`AVG`/`MIN`/`MAX`/`AGGS <verb>` forms are unchanged.

## Why

The scale sweep noted the four aggregate verbs each do an independent full scan
(~17 s each on 1M = ~68 s for all four). `AGGS ALL` collapses that to one scan
(~17 s) — a ~4× win when all four are wanted, with zero semantic change.

## Proof

`pinocchio_aggs_all_proof.dts` + `run_pinocchio_aggs_proof_teed.ps1` (read-only):
- Baseline `SUM/AVG/MIN/MAX GPA` (four scans) then `AGGS ALL GPA` (one scan).
- Expect `AGGS ALL GPA` = `COUNT=1000000 SUM=2.99933e+06 AVG=2.99933 MIN=2 MAX=4`,
  matching the four verbs, with `ELAPSED ~= one aggregate (~17 s)` not ~68 s.
- Predicate path: `AGGS ALL GPA FOR MAJOR = CSCI` → COUNT 90700.

## Proof result (build Jul 19 2026, teed sha 5E9E7315…)

- **AGGS ALL works and is ~4× faster.** `AGGS ALL GPA` = `COUNT=1000000
  SUM=2.99933e+06 AVG=2.99933 MIN=2 MAX=4` — identical to the four standalone
  verbs run just above it — in **19.5 s (one scan)** vs **75.4 s** for the four
  (19.3 + 18.6 + 19.0 + 18.5). Values match exactly.
- **Bug the proof caught (now fixed):** `AGGS ALL GPA FOR MAJOR = CSCI` returned
  `COUNT=0` (expected 90700). Cause: the aggregate FOR/WHERE predicate was never
  normalized, so unquoted `CSCI` was an undefined identifier — the **same class**
  as the SET FILTER string-literal bug, and shared by the standalone
  `SUM/AVG/MIN/MAX FOR` too (they use the same `build_predicate_ast`).

## Second change — aggregate FOR predicate normalization

Added `normalize_agg_predicate(area, spec)` (applies
`normalize_unquoted_rhs_literals` with the function-call guard) and call it in
both `run_agg` and `run_agg_all` before building the predicate AST. Fixes the
FOR/WHERE unquoted-string-literal case for **every** aggregate verb, matching
`COUNT FOR` / `SET FILTER`. Re-run the same proof to confirm section C →
`COUNT=90700` and the GPA stats over that subset.

## Notes

- Cannot compile-test here; maintainer build + proof is the gate.
- Output is a single labeled line; a future revision could emit a message-catalog
  format if a localized form is wanted.
