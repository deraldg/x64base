# SOAK EVIDENCE -- the runs a promotion actually stands on

Promotion doctrine says a spec enters the default suite on **two green runs on a
build nobody changed anything on**. Until 2026-09-08 nothing checked that. It was
enforced by whoever was promoting remembering to look, and on that day it came
within one edit of not being enforced at all: two green VARCHARRESET runs were
taken either side of a one-line string change, and only a deliberate third run on
an unchanged build made the soak real. Nobody would have known.

`tools/staging/check_soak_evidence.py` now reads this file whenever a spec's
`in_default_suite` flag flips false -> true in `src/cli/cmd_regression.cpp`, and
HARD-BLOCKS the commit unless this file carries **two or more rows for that spec
whose BANNER strings are byte-identical** and whose verdicts read PASS.

## WHAT THE BANNER IS, AND WHY IT IS THE RIGHT THING TO QUOTE

The engine prints it at startup, and every capture already contains it:

    dottalk++ v0.6 (2026-09-08, 8885ab99 dirty)  (Sep 08 2026 15:23:52)

It carries the version, the **commit hash**, the **dirty flag** and the **build
timestamp**, and it is written by the binary under test rather than by a tool
making claims about itself. Two runs whose banners are byte-identical were run
against the same build of the same tree. Two runs whose banners differ were not,
whatever anyone believes about the change between them.

## WHAT THIS CANNOT DO, STATED SO NOBODY READS MORE INTO A GREEN GATE

**It cannot prove a run happened.** Captures live in gitignored `tmp/`, so the
gate never sees them; these rows are transcribed by a person. What it *does* is
force the provenance to be written down and then check it for consistency --
which converts "I remembered to compare the build stamps" into a comparison the
gate performs and cannot forget. Transcribing a banner you did not observe is
falsifying evidence, not defeating a check.

**Copy the banner out of the capture file. Do not type it from memory.** The
rows below were taken with `grep` from `tmp/varreset2.txt` and
`tmp/varreset3.txt` rather than reconstructed.

## ROWS

| SPEC | BANNER | VERDICT | RECORDED |
|---|---|---|---|
| VARCHARRESET | dottalk++ v0.6 (2026-09-08, 8885ab99 dirty)  (Sep 08 2026 15:23:52) | PASS 15/15 | 2026-09-08 |
| VARCHARRESET | dottalk++ v0.6 (2026-09-08, 8885ab99 dirty)  (Sep 08 2026 15:23:52) | PASS 15/15 | 2026-09-08 |

VARCHARRESET's rows are recorded **after** its promotion (50b85c3b4), which this
gate did not exist to guard. They are the genuine banners of the second and third
soak runs, read out of the capture files, and they are here so the first spec the
gate protects is not also the first spec with no history in it. A third run --
`Sep 08 2026 15:13:56`, also PASS -- is deliberately NOT listed: it was the first
green, on a different build, and listing it would imply the soak rested on three
matching runs when it rested on two.
