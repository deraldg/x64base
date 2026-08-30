# AIF-135 -- Monotonic AIF Allocator Alignment V1

Status: RULED 2026-08-30 by `member.derald` -- "max+1". Landed in the
development tree the same day; review-needed, the author does not self-approve.

Owner: `member.derald`

Steward: `member.ai.codex`

## Trigger

On 2026-08-26, `claim-aif` assigned AIF-043 to a new ERROR-family lane even
though AIF-043 is the established ramfs/VDISK identity cited by shipping command
help. `next_aif.py` independently reported AIF-134 as next and declared gaps
non-reusable.

The tools answered the same allocation question differently:

- `session_coordinator.py` preferred the lowest apparent gap;
- `next_aif.py` used the high-water mark plus one.

The narrow committed citation scan did not make lowest-gap reuse safe. Expanding
that scan across the whole repository is also unsafe: tests, bounds, and examples
deliberately contain sentinel literals such as AIF-999999.

## Rule presented to the owner

1. The canonical allocation universe is the union of live intake identifiers and
   atomic claim files.
2. A new identity is always `max(union) + 1`; historical gaps are never reused.
3. `--number` may mint only that next monotonic number.
4. Attaching a missing claim file to an identity already present in intake is a
   different operation and requires `--backfill-existing`.
5. If both authority sources are empty, allocation fails closed.
6. `O_CREAT | O_EXCL` remains the final concurrency arbiter. A racing automatic
   claimant advances upward after losing the create; it never searches backward.

## Recovery performed

- Released the erroneous AIF-043 claim owned by `COWORK-20260826-002`.
- Claimed AIF-134 for Claude's ERROR-family lane.
- Claimed AIF-135 for this allocator repair.
- Preserved AIF-043 as the ramfs/VDISK identity.

## Proof

`tools/coordination/test_session_coordinator.py` proves:

- intake containing AIF-043 and AIF-133 mints 134, then 135;
- gaps such as 89 are rejected;
- future skips such as 140 are rejected when 134 is next;
- an existing identity requires the explicit backfill switch;
- duplicate claim creation fails;
- an empty authority fails closed.

`next_aif.py` and `session_coordinator.py status` both report the same next
high-water identity from the same functions.

## Boundary

This change does not repair the ERROR command family, modify AIF-043 source or
help text, clean unrelated claims, or promote anything to `main`.

## Landed in the development tree, 2026-08-30

The design above was verified in another tree on 2026-08-26 and **never reached
`D:\code\ccode`.** That is how the same allocator minted AIF-043 a THIRD time,
for run `COWORK-20260830-001`, four days after this document said the repair was
done. A repair that lands somewhere other than where the tool runs is not a
repair -- AIF-130's lesson, on this lane's own tooling.

The owner ruled `max+1` on 2026-08-30. Rules 1 through 6 above are now
implemented in `tools/coordination/session_coordinator.py`:

- `taken()` is the intake register (rows AND citations) plus the claim files --
  the same universe `tools/coordination/next_aif.py` reads, so the allocator and
  the reporter agree by construction rather than by two scans kept in step.
- `next_aif_number()` returns `max(taken) + 1`, and returns None on an empty
  authority instead of handing out `AIF_LO`.
- `--number` mints only the next monotonic number; a forward skip is refused.
- A number already in the universe needs `--backfill-existing`.
- `status` reports `next-free AIF (max+1)` -- it used to print the lowest gap,
  which advertised a number the allocator would now refuse to mint.

**THE WIDTH AND THE RULE ARE ONE DECISION, AND THE MEASUREMENT SAYS SO.**
Section "Rule presented to the owner" rejects the repository-wide grep because
of sentinel literals. Measured here, same repository, same minute: the wide
universe holds 154 numbers with a maximum of AIF-999999, so `max+1` over it is
AIF-1000000; the narrow universe holds 146 with a maximum of AIF-149. Five of
the wide scan's hits are not numbers at all -- they resolve to `AIF-0`, which is
the matcher `AIF-0*(\d+)` quoted in prose, in the files documenting this
allocator.

**AND THE NARROWING IS SAFE ONLY BECAUSE THE RULE CHANGED.** Three numbers --
AIF-089, AIF-102, AIF-146 -- are real, spent identities with NO intake row and
NO claim file; committed prose is the only place they exist. Under lowest-gap
the wide scan was load-bearing and its silent failure on Windows is exactly what
minted AIF-043. Under `max+1` all three are below the high-water mark and
unreachable. The wide scan survives as `unrowed_citations()`, printed by
`status` under its own heading, because a spent number with no row is still a
number whose lane nobody can look up.

Tests in `tools/coordination/test_session_coordinator.py`: monotonic allocation
never fills a gap; a number cited but not rowed is still seen; an empty
authority fails closed and writes no claim file; `--number` cannot skip forward;
backfill of an existing identity must be explicit. The two pre-existing claim
tests ran against a BARE root -- a fixture that hid the very condition rule 5
must catch -- and now seed an authority.

Route documents corrected the same day, because both said the claim path shells
out to git and it no longer does: `CLAUDE.md`, `AI_README.md`. Surface and
invariants recorded in `docs/maintenance/COORDINATION_DEVELOPER_MANUAL_V1.md`.

NOT DONE HERE: the R-number allocator (`tools/coordination/next_r.py`) already
carries `max+1` and was not touched; the three unrowed identities were reported,
not rowed -- rowing another lane's number is that lane's act.
