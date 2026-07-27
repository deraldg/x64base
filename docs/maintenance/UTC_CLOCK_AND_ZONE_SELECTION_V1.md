# UTC Clock and Zone Selection v1

Status: implemented, runtime-verified
Owner: member.derald   implemented_by: member.ai.claude.cowork
Date: 2026-07-26   Run: `COWORK-20260726-001`
Engine: v0.6, build Jul 26 2026 12:52:47
Recorded as: on-the-spot correction

## What changed

The engine had **no UTC clock**. Every timestamp a DotScript author could
produce was naive local wall-clock with no zone attached. That is correct and
expected for xBase `DATE()` / `TIME()` / `NOW()`, and wrong for any timestamp
written into evidence that another process, host or session will later compare.

Strictly additive. `now_local()` is unchanged and remains the default
everywhere. No existing script, proof or transcript changes behaviour.

## The surface

DotTalk++ accepts commands as functions and as scalars, so the same idea has
several spellings. They are **not** interchangeable across positions.

### Command position (prompt, `.dts` line)

```text
DATE                -> 20260726     local, unchanged
DATE UTC            -> 20260727     bare token
date "UTC"          -> 20260727     quoted
UDATE               -> 20260727     alias
UTIME               -> 014835
UNOW                -> 20260727014839

DATE --UTC          -> (blank)      not a zone token
DATE -UTC           -> (blank)      not a zone token
date("UTC")         -> Unknown command
```

The last line is the one that will confuse people. **The parenthesised form is
expression syntax.** In command position the parser wants `DATE UTC`. This is
the command/function duality working as designed, not a defect — but someone
trying the function spelling at the prompt first will conclude the feature is
broken. Document it wherever the date functions are taught.

### Expression position (`?`, `CALC`, `REPLACE ... WITH`, `IF`)

```text
DATE("UTC")         via the kDateFns table
UDATE()             via the clock-only fast path
```

### Recognised zone tokens

| token | meaning |
| --- | --- |
| *(no argument)* | local — the xBase default |
| `UTC`, `GMT`, `Z`, `ZULU` | UTC |
| `LOCAL`, `L` | local, stated explicitly |
| anything else | **empty string** |

Case-insensitive; whitespace ignored.

## Why blank, and not a fallback to local

`DATE --UTC` returns blank. That is the guard, not a bug.

Falling back to local would return a real-looking date for a request that was
never honoured — a plausible wrong answer, which is worse than no answer. The
convention matches `CTOD()`, which already returns `" "` rather than guessing.

Accepting `--UTC` / `-UTC` as synonyms is one line in `pick_zone()` if the
friendlier CLI-style spelling is ever wanted. Left out because flag syntax is
not xBase idiom, and blank-on-unknown is the more teachable rule.

## Why this was needed — two live defects, one day

Both were **wrong answers produced with confidence**, and neither was visible
to reading the code.

**`tools/coordination/session_coordinator.py` `_age_min()`** compared
`dt.datetime.utcnow().timestamp()` against `st_mtime`. `utcnow()` returns a
*naive* datetime holding UTC wall-clock; `.timestamp()` interprets a naive
value as *local*, so on a UTC-7 host every age was inflated by exactly 420
minutes. Every session reported `[STALE]` the instant it checked in, which
meant staleness detection could never fire. The tool built to prevent
concurrent-session collisions could not tell a live session from a dead one.

**`tools/fullstack_docs/manual_guard_v1.py` `parse_iso()`** stripped the `Z`
and returned a naive datetime, then compared it against a naive *local* file
mtime. Gate 4 reported:

```text
PDF_PREDATES_ASSEMBLY: staged PDF (2026-07-23T00:39) is OLDER than the
assembly it is evidence for (2026-07-23T04:14:23Z) by 3:35:15
```

**That finding was false.** The PDF's true mtime is `07:39:07Z` — 3h24m45s
*after* the assembly, the correct order. There was no provenance violation.
Acting on it meant re-rendering a PDF that was fine. A guard that invents a
violation is worse than no guard.

Same defect class, hours apart, in evidence-handling code. Both fixed.

## The rule this establishes

> Every timestamp crossing a process, host or session boundary is UTC and says
> so. Epochs internally, `...Z` on the wire. Naive local compared against UTC
> lies silently, and in a plausible direction.

Display-time regional formatting stays deferred exactly as
`LANGUAGE_REGION_DOCUMENTATION_BOUNDARY_v1` intends. This is not the region
subsystem — it is the narrow correctness rule underneath it.

## What is still local, deliberately

- `DATE()` / `TIME()` / `NOW()` / `DATETIME()` with no argument — xBase default
- `SECONDS()` — elapsed-since-midnight is a local-day concept. A UTC variant
  would mean something *different*, not something better. Arity stays `0,0`.
- The clock-only fast path in `shell_eval_utils.cpp` for the bare zero-argument
  spellings, which are local by definition.

## What is still missing

- **DBF has nowhere to store a zone.** The `D` type is 8 bytes, `YYYYMMDD`.
  Date only. Even a correctly computed UTC timestamp loses its frame on write.
  A zone-carrying datetime type is a separate, larger decision.
- **No offset arithmetic.** No `TZOFFSET()`, no conversion between frames for
  an existing value — only "what time is it, in this frame, now".
- **The locale spine has no time dimension.** It is a message-rendering
  language selector; region/culture formatting remains future work.

## Files

```text
src/cli/expr/date/date_utils.hpp    now_utc() declared
src/cli/expr/date/date_utils.cpp    now_utc() + shared format_snapshot()
src/cli/expr/fn_date.cpp            zone argument, UDATE/UTIME/UNOW/UDATETIME
src/cli/shell_eval_utils.cpp        fast path for the U* aliases
```

Both clocks render through one `format_snapshot()`, so they cannot drift in
format — only in which `std::tm` they are handed.
