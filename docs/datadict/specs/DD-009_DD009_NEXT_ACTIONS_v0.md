# DD-009 Next Actions v0

Recommended next package: **DD-010 HELP Artifact and CMDHELPCHK Validation Plan**.

## DD-010 scope

Report-only. No HELP rebuild. No CMDHELPCHK execution unless separately authorized.

DD-010 should design the checks that later prove whether HELP, command registry, source contracts, and dictionary links agree.

## Proposed checks

1. Command has registry row.
2. Command has `@dottalk.usage v1` source contract.
3. Command has usage-access route.
4. Command has HELP link candidate.
5. HELP DATA artifact names are known and classified.
6. CMDHELPCHK modes are cataloged as validation surfaces.
7. Educational HELP topics are separable from professional HELP profile.
8. Diagnostic/error commands link to message/error-code model.

## Not authorized by DD-009

- Do not run `CMDHELP BUILD`.
- Do not mutate HELP DATA DBFs/DBTs.
- Do not promote DD009 CSV rows into runtime metadata DBFs.
- Do not change command registration.
- Do not edit CMake/profile gating.
