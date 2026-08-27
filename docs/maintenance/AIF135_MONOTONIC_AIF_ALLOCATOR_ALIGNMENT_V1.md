# AIF-135 -- Monotonic AIF Allocator Alignment V1

Status: implemented locally; owner review before commit.

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
