# Lab: ACID as an Educational Contract

Status: Design ready; runtime exercise not yet implemented  
Audience: Student, developer, maintainer

## Purpose

Learn what each ACID property promises, connect it to concrete engine
mechanisms, and distinguish transaction syntax from verified guarantees.

The lab also teaches that a glass-box interface is orthogonal to ACID. Seeing
pending state can improve understanding and diagnosis; guarantees still come
from locking, validation, commit coordination, flush ordering, and recovery.

## Safety

Run failure demonstrations only on disposable copies of sample tables. Never
inject interruption into production or sole-copy data.

## Student path

For each of Atomicity, Consistency, Isolation, and Durability:

1. State the observable guarantee in plain language.
2. Select one lane: buffered x64, direct mutation, LMDB tag, DBF+LMDB,
   memo+DBF, or legacy index.
3. Identify buffers, dirty/stale flags, writes, flush boundaries, and recovery
   mechanisms involved.
4. Predict a passing observation and a failure observation.
5. Run or inspect a repeatable test and preserve its output.
6. Assign only an allowed rating and cite the evidence.
7. Describe the smallest mechanism or test needed to improve that rating.
8. Classify the finding as an educational tradeoff, an implementation gap, or
   a tested guarantee.

## Atomicity failure demonstration design

1. Copy a sample table and associated storage.
2. Buffer an indexed-field change.
3. record the initial DBF and index state.
4. Interrupt the commit deterministically between DBF and LMDB writes.
5. Reopen all stores and compare their state.
6. Explain whether the operation was all-or-nothing.
7. Describe how a before-image journal or coordinated recovery protocol would
   change the result.

Equivalent demonstrations should be developed for invariant preservation,
concurrent-session visibility/conflicts, and reopen-after-acknowledgement.

## Expected observations

- A command named `COMMIT` does not itself establish atomicity or durability.
- A guarantee in one store does not automatically cover a multi-store update.
- A pending buffered change does not by itself make persistent stores
  inconsistent.
- A buffer viewer does not by itself weaken isolation.
- `Unverified` is the correct rating when adequate evidence is absent.
- Failed tests make limitations teachable and define concrete hardening work.

## Evidence and review

Record machine-readable outcomes in
`docs/acid/acid_test_results_<release>.json` and the interpreted assessment in
`docs/acid/acid_assessment_<release>.md`. Review scope, mechanism, evidence,
failure cases, and improvement gate before changing a rating.

## Next gate

Implement the proposed `ACID` help/status/test/report surfaces in the engine,
then replace the empty baseline result set with captured repeatable tests.
