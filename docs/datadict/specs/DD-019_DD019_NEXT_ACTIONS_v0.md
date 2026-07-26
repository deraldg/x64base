# DD-019 Next Actions v0

Recommended next step: DD-020 staging artifact validator skeleton.

DD-020 should validate the DD-019 stage CSV package before any local import is considered:

1. Confirm required CSV files exist.
2. Confirm required columns exist.
3. Confirm hashes are captured.
4. Confirm object/evidence/source references resolve.
5. Confirm edge endpoints resolve.
6. Confirm conflict rows are preserved.
7. Confirm promotion queue is empty unless explicitly authorized.
8. Confirm no stage file claims promoted/runtime proof without matching evidence.
9. Emit a report-only validation manifest.

Do not proceed directly to x64base DBF creation/import. A validator should come first.
