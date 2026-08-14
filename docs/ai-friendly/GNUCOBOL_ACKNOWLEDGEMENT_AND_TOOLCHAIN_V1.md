# GnuCOBOL acknowledgement, and the COBOL toolchain as measured

Status: review-needed. Owner: `member.derald`. Written 2026-08-14.

Closes the open gate recorded in two places:

- `docs/ai-friendly/HISTORICAL_DATABASE_MIGRATION_EMPIRICAL_PROGRESS_LANE_V1.md`
  -- "GnuCOBOL acknowledgement | open gate | Add the acknowledgement before public promotion."
- `labtalk/registries/projects.yaml` -- "GnuCOBOL acknowledgement is required before promotion."

## Acknowledgement

The COBOL hop in this project does not implement COBOL. It calls **GnuCOBOL**,
and every COBOL result this project has ever recorded as evidence was produced
by GnuCOBOL, not by anything written here. `proof.pdlc.cobol_fixed_record.hop_closed`
-- 200 records, 22,200 bytes, `RECORDS READ: 0000200`, exit 0 -- is GnuCOBOL's
output. The DBF side was ours. The COBOL side was theirs.

**GnuCOBOL** -- <https://gnucobol.sourceforge.io/> -- a GNU project, licensed
GPLv3+ (the compiler; the `libcob` runtime is LGPL). Written by **Keisuke Nishida,
Roger While, Ron Norman, Simon Sobisch, Edward Hart**, and contributors. Decades
of work on a language most of the industry stopped teaching, which is precisely
why a project about database lineage can reach for it and have it simply work.

## The toolchain, as measured 2026-08-14 on the maintainer's host

Do not trust these numbers later; they are perishable. Re-measure with
`cobc --version` and `gcc --version`.

| Component | Value |
| --- | --- |
| Compiler driver | `cobc (GnuCOBOL) 3.2.0` |
| GnuCOBOL packaged | 2023-07-28 |
| Local build date | 2025-08-03 |
| GnuCOBOL license | GPLv3+ |
| C backend used by `cobc` | MinGW GCC **15.1.0** |
| Host `gcc` | 15.2.0 (MSYS2 Rev8) |
| Invocation | `cobc -x -free` (`src/edu/edu_cobol.cpp:376`) |
| Config default | `C:\msys64\ucrt64\share\gnucobol\config\default.conf` (`edu_cobol.cpp:335`, `$COBCONFIG` overrides) |

Two things worth noticing in that table.

**GnuCOBOL is a translator, not a code generator.** `cobc` compiles COBOL to C,
then hands the C to a C compiler. So the COBOL hop's real dependency chain is
COBOL -> GnuCOBOL -> C -> GCC -> executable. Anything blamed on "COBOL" in this
project is at least as likely to be a link in that chain.

**The engine does not link GnuCOBOL.** `edu_cobol.cpp` spawns `cobc` as an
external process; no GnuCOBOL code is compiled into or linked against
`dottalkpp.exe`. The student's compiled COBOL program links `libcob` (LGPL);
this project's binaries do not. Recording the shape because it is a fact worth
having written down, not as legal advice -- confirm obligations with a lawyer
before any distribution that bundles a COBOL runtime.

## Parked: GCC has its own COBOL front end now

<https://www.phoronix.com/news/GCC-15.1-Released>
-- "GCC 15.1 Released With COBOL Compiler & Many Other Improvements", 2025-04-25.

**Why this is parked and not acted on.** GCC 15.1 shipped `gcobol`, a COBOL
front end in mainline GCC. That is a different animal from GnuCOBOL: COBOL
compiled *directly* by GCC, with no COBOL-to-C translation step and no `cobc`.

The coincidence that makes this worth a note: **the GCC underneath our GnuCOBOL
is 15.1.0** -- the exact release that gained the COBOL front end. This host is
already running a compiler that can, in principle, read COBOL without GnuCOBOL
in front of it. Whether THIS MSYS2 build was configured with the cobol language
enabled is unmeasured and should not be assumed; `gcobol --version` answers it
in one line, and a Windows/MinGW build very plausibly omits it.

What it would buy the education lane, if it ever pans out:

- No MSYS2 dependency, and no hard-coded `C:\msys64\...` path in `edu_cobol.cpp`.
  That literal is a portability defect today and would be caught by the
  local-path detectors consolidated in `tools/common/local_paths.json`.
- A COBOL hop that builds under the same GCC used for the WSL and Linux builds,
  making the hop reproducible off Windows for the first time.

Why NOT to switch, stated plainly so nobody reads this as a plan:

- `gcobol` is young. GnuCOBOL has decades of dialect coverage, and this lane
  depends on fixed-format and dialect behaviour that a new front end may not
  match. Our proof was produced by GnuCOBOL and would have to be re-earned.
- The article is 2025-04-25 and GCC is now at 16.2. This is not news; it is a
  settled option we have not evaluated. Evaluating it means running the hop
  under both and comparing byte output, which is a lane, not an afternoon.
- Switching would not remove the acknowledgement above. The evidence on record
  was produced by GnuCOBOL and stays credited to GnuCOBOL regardless.

Suggested first step whenever this is picked up: `gcobol --version` on the host,
then compile `dottalkpp/data/projects/cobol/src/first_cobol_test.cob` with both
and diff the fixed-record output byte for byte. Same discipline as the original
hop: two producers, one value, or it is not a match.
