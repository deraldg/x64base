# NOTES -- APPEND BLANK dispatch

## The finding worth keeping

A hazard was documented, the documentation was read, and the hazard recurred
anyway. The useful question is not "who forgot to read the note" but **"what did
they read instead, and what did it tell them."**

Here the answer is exact. `cmd_append_blank.cpp` said:

```
//   APPEND BLANK is the friendly command spelling when routed by the dispatcher.
```

Conditional mood, false condition, filed in the implementation file -- the most
authoritative-looking place a reader can check. The true warning was in the
WSLADDER spec entry inside `cmd_regression.cpp`, which is a correct place to
record it and a place nobody consults before typing a command.

**A warning filed somewhere true does not outrank a falsehood filed somewhere
obvious.** Hunk 3 is not tidying; it is the hunk that stops the third recurrence.

This is the same shape as `FINDING_A_BACKFILLED_STATUS_IS_ABSENT_SPELLED_AS_SUPPORTED`
and the spec that cited the source refuting it: **a document describing an
intention in the grammatical mood of a fact.**

## Two defects, one symptom, and they do not fix each other

Easy to read this as one bug. It is two:

1. no dispatcher route for the two-word spelling (shell path);
2. a direct call at position zero (TUI path).

The route does not repair the TUI, because the TUI never reaches the dispatcher.
Had only hunk 1 landed, `APPEND BLANK` would work at the prompt and F5 would
still silently do nothing -- and it would now be harder to find, because the
obvious explanation would have been fixed.

## The latent hazard nobody asked about

`cmd_browsetui.cpp` calls `cmd_*` functions directly with hand-built streams:

```cpp
std::istringstream s("DELETE");
cmd_DELETE(area, s);
```

**The dispatcher's contract is that the stream arrives positioned past the verb.**
These call sites leave it at zero. F4 survives because `cmd_DELETE` ignores
positional arguments; F5 did not, because `cmd_APPEND` parses them. **Every such
call site is correct by luck, and stays correct only while the command it calls
keeps ignoring its arguments.** Adding an argument to any of those commands turns
a working key into a silent no-op, with no compile error and no test.

Recommended, not done here: audit every direct `cmd_*` call in the TUI (and
anywhere else building a stream by hand) and give them all the empty-stream
spelling. A `dottalk_invoke_command(area, "VERB", "args")` helper that enforces
the positioning contract in one place would be better than N correct call sites.

Out of scope: this package repairs the caller that is broken today and names the
pattern.

## Why not a test

No `src/tests` target links the CLI layer -- every one links `xbase`/`memo`, so
`shell_dispatch_line()` is not reachable from a unit test without new build
structure. The house's tool for shell behaviour is a `.dts` regression spec, and
specs live in `src/cli/cmd_regression.cpp`, a much larger surface than this
repair.

So the proof is the manual runtime sequence in TEST_PLAN.md section 2.2, with its
expectations written before the run. **That is weaker than a spec and is
described as weaker.** A spec is the right follow-up and is the honest price of
this fix: the defect's whole character is that it is invisible unless something
counts records afterwards.

## Numbers not claimed

- No AIF number. Nothing was written under `docs/ai-friendly/`.
- No R number. `next_r.py` is the steward's act. The candidate is real and
  already stated one level up: **a document that describes an intention in the
  mood of a fact will out-argue a correct warning filed elsewhere.**
- `AIPR-20260905-CLAUDE-001` is self-assigned and flagged in MANIFEST.md as a
  question, not a claim.

## Provenance of the patch

Generated with plain `diff -u` between untouched copies of the three files and
edited copies, both under `tmp/cp_work/`. **`git diff` was not used, in any
form**, per this tree's standing constraint about the mount and `.git/index.lock`.
The working tree's own `src/cli` files were never opened for writing.
