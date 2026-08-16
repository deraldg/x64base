# Handoff -- working on the lock subsystem (xbase::locks)

**Left by** `member.ai.claude.cowork`, 2026-08-15, after AIF-116.
**For** the next agent who touches locking, or who trusts a lock.
**Companion closeout:** `docs/maintenance/SESSION_CLOSEOUT_AIF112_PHASE1_AND_LOCK_MUTUAL_EXCLUSION_2026-08-15.md`

No perishable facts below. Where a number would go stale, the measuring command
is given instead.

## Read this before you assume a lock held

Until 2026-08-15, **cross-process mutual exclusion did not hold on Windows** --
deterministically, on every write path in the engine, including the BBS daemon.
It is fixed. Any proof, log, or memory older than that date which depends on a
lock having been exclusive is worthless. Check the banner stamp on the evidence
before you trust it.

## The shape of the defect, because the shape recurs

`std::stoul` accepts the longest valid prefix and does **not** throw on trailing
junk. The owner pid was written through an un-imbued stream, a grouping locale
turned `16984` into `16,984`, the reader parsed `16`, `is_pid_alive(16)` said no,
and the stale branch handed the lock away.

The same prefix-acceptance shape appears elsewhere in this repo and in the tools
around it. When something silently accepts a partial parse, look for it.

## Where the pieces are

| Concern | Location |
|---|---|
| Owner string built | `src/xbase/xbase_locks.cpp`, `make_owner_string` |
| Sidecar written | same file, `write_lock_file` |
| Sidecar parsed | same file, `read_lock_meta` -- note `LockMeta::pid_valid` |
| Liveness | same file, `is_pid_alive` |
| Stale branches | same file -- three of them; `grep -n "is_pid_alive(" src/xbase/xbase_locks.cpp` |
| The global locale | `include/runtime/utf8_init.hpp`, reached from `src/cli/main.cpp` |
| Commands | `src/cli/cmd_lock.cpp`, `src/cli/cmd_unlock.cpp` |
| Regression | `tools/regression/lock_mutual_exclusion_regression.ps1` |

## Rules that are not obvious from the code

**1. Fail closed.** An owner whose pid cannot be parsed is presumed **alive**.
`pid_valid` carries that distinction because `pid == 0` cannot -- `is_pid_alive(0)`
is false, which would make an unreadable owner look dead. If you add a fourth
stale check, guard it the same way.

**2. Nothing releases a lock except `UNLOCK`.** Not `CLOSE`, not `CLEAR`, not
`USE`, not `DbArea::close()`, not `~DbArea()`, not process exit. Verify with
`grep -rn "unlock_table\|unlock_record\|release_held" src/ --include=*.cpp`.
`release_held` exists and is called by nothing (AIF-113).

**3. Class A versus Class B.** Class A sites acquire and release inside one
operation (RAII or paired exits) and are safe. Class B is `cmd_lock.cpp` only --
held across operations, released only by the user. Class B is the entire
exposure surface. Know which one you are writing.

**4. Anything serialised to disk must be locale-immune.** The sidecar is a
cross-process protocol file, not output. `imbue(std::locale::classic())` on any
stream that writes one. The global override in `utf8_init.hpp` covers the
process today, but it is one well-meaning edit from being reverted, and there is
no gate. See AIF-031 for the twenty sites this already happened to.

**5. The defect is Windows-only.** POSIX installs `C.UTF-8`, which carries
classic numeric facets. **A green lock suite on WSL proves nothing.** The
regression skips on non-Windows by design.

## Running the regression

```
pwsh -File tools\regression\lock_mutual_exclusion_regression.ps1
```

Five tests. T1 is the direct guard (pid round-trips ungrouped). T2 proves a dead
owner is still reclaimed -- if that fails, someone made the parser too strict and
turned a safety fix into a permanent lock. T3 and T4 prove refusal. T5 covers the
record-lock path, which checks the *table* lock and is easy to miss when patching.

Tests 3 to 5 fabricate a `.lock` sidecar rather than orchestrating two engines.
That hardcodes the sidecar **format** -- if you change the format deliberately,
these fail, and that is intended.

## Traps this session hit, so you do not

- **`LOCK` with no argument locks the current RECORD**, not the table.
  `UNLOCK` likewise. Use `LOCK TABLE` / `UNLOCK TABLE`.
- **`UNLOCK` reports success on a record that was not locked.** You cannot tell
  "released it" from "there was nothing to release".
- **A test whose fixture fails silently will report a lock defect that does not
  exist.** Verify the fixture has records, in a separate process, before judging
  a lock result. Cost this session: one false failure and a wrong diagnosis.
- **Stale sidecars from a pre-fix build are unparseable** and therefore presumed
  alive and unclearable by any command. Delete them by hand after upgrading:
  `Get-ChildItem <data> -Recurse -Filter *.lock* | Remove-Item -Force`.
- **The daemon runs straight out of the build tree** and locks its own binary.
  Stop the scheduled task before rebuilding or the link fails.
- **The daemon prints no version banner**, so you cannot tell from its log which
  build is running. Correlate its start time against the binary timestamp.

## What is still broken

- **AIF-113** -- `release_held`, `force_unlock_table`, `force_unlock_record` are
  all dead code and no `FORCE` verb is exposed. This is now a **blocking
  dependency**: leaked Class B locks are only clearable by hand.
- **AIF-117** -- `FieldRef::eval` tests non-blankness, so `COUNT FOR <logical>`
  matches every row. Do not trust a bare-field predicate; write `= T`.
- **No gate** enforces rule 4 above.
