# Gate 5 -- the Phase 5 candidates, BOUND by SHA-256

    Run           : DOCFLUSH-20260825-001, member.ai.claude.cowork for member.derald
    Gate          : 5. Candidate binding. **NO import, NO promotion, NO mutation.**
    Authorization : member.derald, 2026-08-26 -- "gate 5 bind"
    Status        : BOUND, review-needed.

## 1. What is bound

The candidates are gitignored by `.gitignore:342`
(`docs/maintenance/lanes/**/runs/**/*.csv`), which is what the METACOLLECT
runbook requires -- candidates stay out of history. **Binding by SHA is
therefore the ONLY thing that makes them citable**, and this document is the
tracked link. Emitted 2026-08-26.

    sha256                                                            rows  bytes  artifact
    62c12e6548f93f5365233f1349900c8bfea1214444d0aac929e0a5c5109275de   229  14031  SYSCMD_IMPORT_candidate_v1.csv
    87bd96b1e4f9e6340d89302e0c084237255a9a52562ca258772d0562655d7239    75  37576  SYSFUNC_IMPORT_candidate_v1.csv
    1a1edb0fa321fadb53b314ccaf4176f34c5fa4358eae0df7aff01bb4beafe601  1066 277250  SYSARGS_IMPORT_candidate_v1.csv
    f8fbef8a636358ca55cce1b479bddcccf1f738a5cda0a4b79f5fd59463df636e  1083 275018  metacollect_facts_v1.csv
    3490c6794f68fe672fdebdafc54ac35586f4aaa368acc981e23f363749c1d193   192  27184  metacollect_compare_v1.csv

All five live in this directory. The first three are the import candidates; the
fourth is the source-fact projection; the fifth is the source-vs-live compare.

## 2. Contract compliance, checked before binding

Against `METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md` -- itself staged in
`848273a77`'s successor after being found on disk and outside history:

    "repeated runs over unchanged source must be byte-identical"
      two emissions, all three candidates                    BYTE-IDENTICAL
    "rows sort by CAN_NAME"                                  True, 229 rows
    unique CMD_ID / unique CAN_NAME                          True / True
    "TYPE=syntax-command reserved ...; other rows command"   {command, syntax-command}
    "default VIS=public; developer rows VIS=developer"       {public, developer}
    field order CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE      exact

**Determinism is the clause that carries this binding.** It makes a re-emission
a CHECK against these hashes rather than a replacement of them.

## 3. THE PLATFORM CAVEAT, and it is load-bearing

**These candidates were emitted by a SANDBOX-BUILT metacollect, not by
`build/Release/metacollect.exe`.**

    built     g++ 11.4 (Ubuntu 22.04), -std=c++17 -O0, 12 objects + link,
              from the dt_meta TU list at CMakeLists.txt:771 -- no CMake,
              binary written to /tmp and NOT into the tree
    ran       --source-root <repo>/src --include-dev-commands
              --sysargs-include-keywords, exit 0

Determinism was proved WITHIN that toolchain. **Whether the host MSVC binary
produces byte-identical output is UNPROVEN and is the one open item on this
binding.** It is one command to settle, and it converts this binding from
sandbox-attested to host-attested:

```powershell
$mc  = 'D:\code\ccode\build\Release\metacollect.exe'
$out = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260825-001\metacollect_phase'
& $mc --source-root D:\code\ccode\src --include-dev-commands --sysargs-include-keywords `
      --syscmd-import-out  "$out\SYSCMD_host_v1.csv" `
      --sysfunc-import-out "$out\SYSFUNC_host_v1.csv" `
      --sysargs-import-out "$out\SYSARGS_host_v1.csv"
Get-FileHash "$out\SYSCMD_host_v1.csv" -Algorithm SHA256   # expect 62c12e65...
```

A difference is a FINDING, not a failure of this gate -- it would be the first
measured host/sandbox divergence in the metadata lane, and worth more than an
agreement. The v6 resume state already records one such divergence in the store
(29263 against 29265), so this is not hypothetical.

**A sandbox green is not a green on the maintainer's toolchain. Named, as
required.**

## 4. What this binding does NOT authorize

The contract is explicit and this gate does not widen it:

> Any load into `dottalkpp/data/metadata/SYSCMD.dbf`, and any associated
> CDX/LMDB work, requires a separate reviewed mutation gate with backup,
> before/after readback, rollback evidence, and explicit maintainer authority.

So: **no import, no CDX, no LMDB, no HELP mutation, no manual publication.**
Bound means citable and reproducible, nothing more.

## 5. Two measurements carried forward, unresolved

Recorded here so they are attached to the artifact they came from:

1. **SYSARGS moved 959 -> 1066, +11%**, with `--sysargs-include-keywords` on
   both runs, so the widening flag is not the difference. Unexplained.
2. **`--compare` reports 189 METADATA_ONLY**, and the number needs its
   denominator every time it is quoted: the compare's source side is
   `command_catalog.cpp`, a DIFFERENT extractor from the seed emit's registry
   scan, so it reads *"189 of 212 live SYSCMD rows have no source-catalog
   counterpart"*, not *"189 commands vanished"*. Three SOURCE_ONLY rows --
   `SET FILTER`, `SET INDEX`, `SET ORDER` -- are multiword, which is AIF-131's
   family in a third catalog.

## Good Neighbor

    What changed  : this document. No CSV was regenerated to produce it; the
                    hashes are of the artifacts already on disk. No metadata,
                    no store, no source.
    Whose area    : lane full_stack_documentation / AIF-068.
    Authorization : member.derald, 2026-08-26, "gate 5 bind".
    Verify        : sha256sum the five files in this directory against section 1.
                    Re-emit and compare -- the contract requires byte-identity.
    Undo          : delete this document; the candidates remain, unbound.
