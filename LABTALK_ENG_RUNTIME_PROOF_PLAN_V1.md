# LabTalk Engineering Case Runtime Proof Plan v1

Status: catalog-read proof captured, behavioral fixture proof still open.

The ENG cases are runtime-lab candidates. Each now has a proof packet and catalog-read proof from `CASE SHOW <id>`. Each still needs a behavioral fixture transcript before it can move beyond `needs_runtime_proof_attachment`.

## Proof Packet Contract

Each proof packet should contain:

- command script or exact manual command sequence
- expected output summary
- captured output or transcript
- build/runtime version or commit identifier
- data fixture path
- pass/fail status
- reviewer/date

## Case Proof Targets

| Case | Proof packet | Minimum proof |
|---|---|---|
| ENG-010 | `runtime_proofs/ENG-010_RUNTIME_PROOF.md` | Show physical order versus active index/logical order using CDX or LMDB-backed navigation. |
| ENG-020 | `runtime_proofs/ENG-020_RUNTIME_PROOF.md` | Show SEEK behavior compared with SCAN/predicate traversal on the same fixture. |
| ENG-030 | `runtime_proofs/ENG-030_RUNTIME_PROOF.md` | Show buffering/dirty state and COMMIT/ROLLBACK lifecycle or document why the current runtime lacks the full behavior. |
| ENG-040 | `runtime_proofs/ENG-040_RUNTIME_PROOF.md` | Show metadata/help/catalog evidence and a validation check such as CMDHELPCHK or equivalent report. |
| ENG-050 | `runtime_proofs/ENG-050_RUNTIME_PROOF.md` | Show file/table/index/backend separation with a fixture that proves storage and navigation are distinct concerns. |

## Gate

Do not change ENG case `review_status` until its proof packet contains behavioral captured output and reviewer acceptance.
