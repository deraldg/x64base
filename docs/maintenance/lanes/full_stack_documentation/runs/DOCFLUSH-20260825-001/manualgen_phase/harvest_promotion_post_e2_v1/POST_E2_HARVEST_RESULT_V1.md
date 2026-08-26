# Post-E2 Canonical Harvest Result V1

Status: PASS

Run: `DOCFLUSH-20260825-001-E5-POST-E2-001`

- Candidate export: 14 tables, 63,217 rows.
- Semantic candidate freshness: PASS 14/14.
- Authorized replacements: six.
- Verified byte-identical no-ops: nine.
- Canonical files mutated: six.
- Canonical semantic readback: PASS 14/14, zero manifest findings.
- Rollback performed: no.
- Backup retention: local ignored, with before and staged-after hashes.

Manualgen proof used `.venv312` and explicit workspaces:

- inventory: 14/14 harvest files;
- validation FAIL rows: 0;
- validation REVIEW rows: 0;
- boundary FAIL rows: 0.

An earlier system-Python/implicit-workspace invocation produced one environment
FAIL and two selection REVIEW rows. It did not mutate protected systems and is
not used as acceptance evidence.

E5 is closed. E6 is the next open entry: regenerate and validate the website
command catalog against the current registry and HELP surfaces.
