# ACID and the Glass-Box Database

Status: Architectural analysis; not a compliance claim  
Version: 1  
Date: 2026-07-11

## Central thesis

A glass-box educational architecture does not inherently weaken ACID.
Visibility and transactional guarantees are separate dimensions. DotTalk++ can
show buffers, stale fields, locks, commit boundaries, and recovery evidence
without changing the correctness of the mechanisms underneath them.

The correct question is not whether the engine exposes its state. It is whether
each operation, storage lane, and failure boundary provides a tested guarantee.

## Three kinds of findings

An ACID review must not collapse all limitations into one category.

| Finding | Meaning | Example |
| --- | --- | --- |
| Educational tradeoff | Complexity is exposed or staged deliberately for learning. | Showing dirty and stale fields before commit. |
| Implementation gap | A required mechanism is absent or incomplete. | A persistent cross-store recovery journal is still a stub. |
| Transactional guarantee | Repeatable evidence establishes a scoped behavior. | A crash/reopen test proves an acknowledged write survives. |

An educational tradeoff is not automatically a defect. An implementation gap
must not be presented as a feature. A source mechanism is not a verified
guarantee until a repeatable test proves its behavior.

## Correcting two common inferences

### Buffered state and consistency

A tuple-buffer edit can be dirty or stale while the persistent DBF and its
indexes remain unchanged. That pending state does not by itself create a
persistent inconsistency. The consistency boundary is crossed when a direct
mutation or commit updates one participating store without updating,
invalidating, rebuilding, or recovering the others.

The current `COMMIT` contract matters here: it says partial commit is possible
and that CDX/LMDB rebuild is outside the command. Those facts identify a test
and hardening boundary; they do not justify claiming either compliance or
failure for every lane.

### Buffer inspection and isolation

Showing a user their own pending changes does not weaken isolation. Isolation
depends on session visibility, lock scope, versioning, conflict detection, and
the ordering of concurrent operations. The source contains buffering and
per-record commit-lock mechanisms, but the actual isolation model remains
unverified until concurrent reader/writer and writer/writer tests are captured.

## Property analysis

### Atomicity

Atomicity asks whether a scoped operation is all-or-nothing. Pre-commit rollback
supports the concept for pending table-buffer changes. It does not prove that a
commit spanning DBF records, memo payloads, and indexes is atomic. The current
contract explicitly allows partial commit, and persistent journal hooks are
stubs. The release rating therefore remains `Unverified`.

Required proof includes deterministic interruption at each write boundary,
reopen inspection, and recovery verification for every participating store.

### Consistency

Consistency asks whether declared invariants hold before and after a completed
operation. Visible dirty/stale metadata helps identify affected fields and
indexes. It is diagnostic evidence, not invariant proof. Tests must cover field
validation, relation constraints, index agreement, memo references, direct
mutation paths, successful commits, failed commits, and recovery.

### Isolation

Isolation asks what concurrent sessions can observe and how conflicting writes
are handled. Per-record locking during commit is a relevant mechanism, but lock
presence alone does not define an isolation level. The project needs explicit
tests for dirty reads, non-repeatable reads, lost updates, write conflicts, and
visibility before and after acknowledgement.

### Durability

Durability asks whether an acknowledged operation survives process and system
failure. LMDB-local transaction commits and memo flush methods are useful
mechanisms. They do not prove coordinated durability across DBF, memo, CDX, and
LMDB stores. Reopen tests, forced termination, flush-order inspection, and
power-loss-oriented tests are required.

## Scope before score

ACID ratings belong to an operation and storage lane, not to the product name
alone.

| Scope | Key question |
| --- | --- |
| Buffered x64 mutation | Can pending work be abandoned, committed, and recovered as specified? |
| Direct mutation | Is each immediate write complete, validated, and recoverable? |
| LMDB-local mutation | Does the LMDB transaction provide the claimed local guarantee? |
| DBF + LMDB | Is there coordinated commit or deterministic recovery across stores? |
| DBF + memo | Can payload and reference ever diverge after interruption? |
| Legacy index lane | Which guarantees are inherited, emulated, or explicitly unavailable? |

This prevents a strong local mechanism from being generalized to a multi-store
operation it does not cover.

## Educational value

ACID should be both an engineering objective and a lesson. A student should be
able to predict a guarantee, observe the participating state, inject a safe
failure into disposable data, reopen the stores, and assign a rating backed by
evidence. Failed tests are valuable when they are preserved honestly: they turn
an abstract acronym into a concrete engineering requirement.

## Current conclusion

DotTalk++ has useful mechanisms and an unusually inspectable surface for
teaching transaction behavior. The current repository does not yet contain the
complete failure, concurrency, and recovery evidence needed for a broad ACID
claim. The correct beta-0 rating remains `Unverified`, scoped by lane and
property.

The glass-box design is not the reason for that rating. It is the means by which
the project can explain, test, and eventually prove stronger guarantees.
