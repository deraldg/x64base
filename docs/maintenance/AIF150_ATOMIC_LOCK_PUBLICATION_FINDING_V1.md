# AIF-150 -- atomic lock publication was fixed before it was directly raced

Status: review-needed, runtime-proven on Windows, not pushed

Owner: `member.derald`

Author: `member.ai.codex.local`

Related lane: AIF-074 SQLsel P4.2/P4.3

## Finding

SQLsel's two-table read fence exposed a pre-existing defect in the shared xBase
lock primitive. The former `exists()` followed by truncating file creation was
a time-of-check/time-of-use race: two processes could both observe no sidecar,
both report acquisition, and the later writer could replace the live owner's
identity. Commit `240240faf` replaced that sequence with atomic
`CREATE_NEW`/`O_EXCL` publication.

The five-arm native protocol test added with that fix checked real table and
record sidecars, fail-closed owner parsing, the table/record handshake, and
same-owner re-entry. It did not release two real processes against the same
absent sidecar. The source mechanism was corrected, but the defining race had
no direct regression.

## Repair to the proof

`src/tests/test_lock_protocol.cpp` now has a sixth arm. For sixteen rounds it:

1. starts two child processes with different owner identities;
2. waits until both children announce readiness;
3. releases both through one filesystem start gate;
4. requires exactly one successful `try_lock_table()` result;
5. reads the live sidecar from a third process context and requires the stored
   owner to equal the winner; and
6. holds the winner until inspection, releases it, waits for both children,
   and requires the sidecar to self-erase.

This is a protocol regression, not a SQLsel-only test. SQLsel is how the defect
was found; every table lock, record lock, and FLOCK consumer depends on the
same publication primitive.

## Evidence

Runtime, Windows MSVC Release build, 2026-09-03:

```text
lock_protocol: PASS -- table/record handshake and atomic publication 6/6
```

Mutation test: the Windows publication branch was temporarily changed to the
old check-then-create shape, with a 25 ms post-check delay and overwrite-capable
creation. The new arm failed in every round with both children reporting `WIN`;
some rounds also observed a missing or overwritten owner. Exit status was 1.
The mutation was removed, the atomic source restored, and the target rebuilt.

## Limits

- The synchronized race was run on Windows. The child-process harness includes
  a POSIX `fork`/`exec` path, but that path has not yet been built or run here.
- Filesystem sidecars remain a cooperative protocol, not an OS byte-range lock
  and not MVCC.
- This record does not widen SQLsel's transaction claim. A JOIN gets a
  statement read fence across two tables; it does not gain cross-table write
  atomicity.

## Review disposition

Ships local and review-needed. The author does not self-approve. No push or
publication is authorized by this record.
