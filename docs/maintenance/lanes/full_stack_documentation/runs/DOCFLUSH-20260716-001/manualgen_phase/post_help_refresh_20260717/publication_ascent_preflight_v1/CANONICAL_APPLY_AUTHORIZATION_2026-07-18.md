# Canonical manual apply authorization

Decision: authorized for canonical apply.  
Recorded: 2026-07-18 UTC.  
Authorized by: maintainer.  
Plan run: `MANRUN-20260718T031714Z-1A3F1333`.  
Plan manifest SHA-256: `853DBC723600AFF220A04445D0284440639F286E49372B98D71EC8DFD09717E5`.  
Mutation ledger SHA-256: `5940F79BA7F5D97F834AB7A88E402659F49B4AD9EFDCA48C27BC43BA474906F3`.  
Mutation rows authorized: 8.  
Required interpreter: Python 3.12.

## Authorized scope

The maintainer authorizes the exact eight targets and planned candidates in
`controlled_acceptance_mutation_ledger.csv` from the named plan run:

1. replace the Runtime Evidence section;
2. replace the Command Surface section;
3. create the Partial HELP appendix;
4. replace the appendix aggregate;
5. replace the active primary-reader Markdown at its existing path;
6. regenerate the accepted primary-reader evidence record;
7. regenerate the accepted canonical reference record;
8. create the append-only DOCFLUSH appendix acceptance record.

The active reader pointer path does not change.

## Required controls

- Recheck the plan/ledger hashes, all eight before states, and every planned
  candidate hash before writing.
- Preserve every existing target byte-for-byte in a timestamped backup.
- Stage and hash all after bytes before the first canonical replacement.
- Use atomic same-directory replacements where possible.
- Roll back all eight targets if any apply or after-state check fails.
- Rerun the pointer audit, Manualgen/full-stack tests, and contextual checks.

## Excluded

No MAN* catalog, HELP/META table, COMMENTS data, source-staging tree,
`C:\x64base`, website repository, commit, push, deployment, or reader-pointer
path mutation is authorized by this record.
