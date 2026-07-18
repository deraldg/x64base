# Full Stack Documentation Flush Record

Run ID: `DOCFLUSH-YYYYMMDD-NNN`  
Status: planned  
Owner:  
Started:  
Closed:  

## 0. Living Progress Journal

- Human log:
- Machine CSV:
- Logging mode: append-only
- Latest progress ID:
- Current gate:
- Next gate:

Append a progress entry whenever a material gate opens, passes, fails, is
reconciled, receives authorization, or changes the next action. Corrections are
new entries; do not rewrite an earlier failure out of the audit trail.

## 1. Authorization and Scope

- Requested outcome:
- Authorized report-only work:
- Authorized mutations:
- Explicitly excluded work:
- Authority root:
- Branch:
- HEAD:

## 2. Protected Systems

| System | Pre-run path | Mutation authorized? | Backup or baseline | Rollback |
| --- | --- | --- | --- | --- |
| Source and `include/*ref.hpp` |  | no |  |  |
| Comments evidence |  | no |  |  |
| Legacy HELP DBFs |  | no |  |  |
| Current HELP DATA |  | no |  |  |
| HELP indexes/LMDB |  | no |  |  |
| Live metadata |  | no |  |  |
| Accepted `MAN*` catalogs |  | no |  |  |
| Active manual/publication pointers |  | no |  |  |
| Website/public repository |  | no |  |  |

## 3. Input Manifest

| Input | Authority class | SHA-256 or version | Observed state | Notes |
| --- | --- | --- | --- | --- |
| `include/dotref.hpp` | curated compiled reference |  |  |  |
| `include/foxref.hpp` | curated compiled reference |  |  |  |
| `include/edref.hpp` | curated compiled reference |  |  |  |
| command registry | source-defined |  |  |  |
| usage contracts | source-defined |  |  |  |
| HELP DATA | generated explanation |  |  |  |
| manual canonical manifest | accepted pointer |  |  |  |
| active reader pointer | accepted pointer |  |  |  |
| current publication manifest | publication pointer |  |  |  |

## 4. Runtime Context

- Executable path:
- Executable SHA-256:
- Executable timestamp:
- Data root:
- Locale/region:
- Python path:
- Python version:
- Manualgen version:

## 5. Baseline Commands and Results

| Command | Exit/result | Evidence path | Finding |
| --- | --- | --- | --- |
| `CMDHELP` | not run |  |  |
| `CMDHELP USAGE` | not run |  |  |
| `CMDHELPCHK` | not run |  |  |
| `DOTHELP` | not run |  |  |
| `FOXHELP` | not run |  |  |
| `HELP` | not run |  |  |
| `MANUAL STATUS` | not run |  |  |
| `MANUAL COUNTS` | not run |  |  |

## 6. Drift Inventory

| ID | Layer | Identity/topic | Expected | Observed | Evidence class | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| DF-001 |  |  |  |  |  | unreviewed |

Allowed decisions:

- expected difference;
- source repair candidate;
- reference repair candidate;
- HELP rebuild candidate;
- metadata candidate;
- manual candidate;
- publication candidate;
- unresolved.

## 7. Reviewed Mutation Package

- Mutation package ID:
- Review decision:
- Approved commands:
- Approved paths:
- Pre-apply hashes/counts:
- Backup location:
- Rollback command:
- Stop conditions:

## 8. Execution Ledger

| UTC/local time | Command or action | Mode | Exit state | Files/tables changed | Evidence |
| --- | --- | --- | --- | --- | --- |
|  |  | report-only |  | none |  |

## 9. HELP Refresh Results

- Legacy build run: no
- Current build run: no
- Build order reason:
- Pre/post table counts:
- Pre/post file hashes:
- `CMDHELPCHK` result:
- `CMDHELP` targeted smoke:
- `HELP` targeted smoke:
- `DOTHELP` targeted smoke:
- `FOXHELP` targeted smoke:
- Remaining HELP drift:

## 10. Metadata and SelfDoc Results

- `metacollect` run: no
- Facts report:
- Compare report:
- Candidate CSVs:
- Live metadata changed: no
- SelfDoc records updated:
- Provenance/hash check:

## 11. Manualgen Results

| Step | Result | Run ID/output | Protected systems changed? |
| --- | --- | --- | --- |
| inventory | not run |  | no |
| validate | not run |  | no |
| export-manifest | not run |  | no |
| build-dry-run | not run |  | no |
| parity-review | not run |  | no |

- Candidate artifact:
- Candidate SHA-256:
- Current reference artifact:
- Current reference SHA-256:
- Parity summary:
- Human review decision:

## 12. Promotion and Pointer Review

| State | Before | After | Changed? | Review evidence |
| --- | --- | --- | --- | --- |
| Candidate workspace |  |  | no |  |
| Canonical manifest |  |  | no |  |
| Accepted `MAN*` catalog |  |  | no |  |
| Active primary reader |  |  | no |  |
| Current publication manifest |  |  | no |  |
| Website/public snapshot |  |  | no |  |

## 13. Closeout

- Development files changed:
- Development proof completed:
- HELP/generated data changed:
- Manual candidate created:
- Accepted publication changed:
- Promoted to `C:\x64base`:
- Commit created:
- Push completed:
- Unresolved drift:
- Next gate:
- Intentionally untouched work:

Close only the states actually completed. A green candidate or local runtime
does not imply promotion, commit, push, or public publication.
