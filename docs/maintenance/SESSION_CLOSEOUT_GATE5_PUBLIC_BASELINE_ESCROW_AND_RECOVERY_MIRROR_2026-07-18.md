---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260718-022
  recorded_at_utc: 2026-07-18T14:36:24Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: correct the Gate 5 staging recovery model and establish the same offline recovery package at C:/code/ccode without resetting staging or authorizing Git or website work
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_GATE5_PUBLIC_BASELINE_ESCROW_AND_RECOVERY_MIRROR_2026-07-18.md
    kind: session_closeout
---

# Session Closeout — Gate 5 public-baseline escrow and recovery mirror

Date: 2026-07-18.  
Owning lifecycle: maintenance SDLC plus PLDC publication lane.  
Truth state: staging is a recoverable projection, not a second authority and
not blindly disposable.  
Promotion state: recovery ready; destructive reset remains unauthorized.

## Correction

The prior model correctly placed authority in `D:\code\ccode`, but overstated
the consequence of wiping `C:\x64base`. The public baseline contains 36 files
absent from development, including a public getting-started build guide and a
historical LMDB rebuild script. The dirty staging layer also contains 20 files
that an exact Gate 5 overlay would not automatically restore except for the
intentional `PROMOTE.manifest` replacement.

The corrected contract requires three independent restore layers: committed
public baseline, preserved dirty worktree, and authorized publication overlay.

## Final escrow

`docflush_gate5_public_baseline_escrow_20260718T144151Z/` contains:

- complete-history Git bundle for `fa7c04dcea07a2f0b5a027fba7bc953651cd83df`;
- direct tar snapshot of all 1,951 committed files / 92,540,334 bytes;
- per-file SHA-256 and development-relation ledger;
- 36-row public-baseline-only reconciliation ledger;
- complete 20-file dirty-worktree preservation package;
- corrected 316-file Gate 5 overlay plan.

Final escrow manifest SHA-256 is
`03265F97EDC6528D5A47C224AED7ABC883F6C624D6C9AF993EA3258591D5E243`.
Bundle SHA-256 is
`151FF076D5DE41AE270C1A866D1DB7BAE5C0024C923893068291C140A0B31CC3`;
tar SHA-256 is
`109B1D23782EB233F558BF353E4E98F65F6BD552887A5F55F49270E05F1754A1`.

The earlier `20260718T142803Z` and `20260718T143453Z` escrows remain retained as
superseded recovery points because they bind pre-correction/intermediate plans.
They were not deleted.

## Corrected plan and rebuild behavior

The active plan is `STAGEPLAN-20260718T144123Z`: 316 files / 1,385,570 bytes,
315 creates and one replacement, zero unrelated dirty intersections, leaks, or
findings. Plan-manifest SHA-256 is
`12EEFD28A486115C880DB302BB852615870ABC7D0D202D44C260A6819E2CB7AF`;
ledger SHA-256 is
`B43391F4D3204014E67FAC129A8419C2317E753B3D243B1CA7F52367099503EB`.

The final planner also proved all 316 source hashes still match after closeout
recording. Executable hashes live only in this non-overlaid closeout and the C
mirror pointer; the three overlay-controlled ascent/progress files no longer
hash-reference themselves.

`rebuild-staging.ps1 -Fresh -Execute` now fails closed unless supplied the
matching escrow manifest. It verifies all named hashes, current and fetched
baseline identity, dirty-layer files, and public-only ledger; restores the
dirty layer after reset; and verifies all public-only files after overlay.

## C-drive recovery mirror

`C:\code\ccode` was absent and was created as a labeled offline recovery
mirror, not as a second development repository. It contains:

- `README.md` with authority and restore order;
- `recovery\CURRENT_ESCROW.txt` with exact bindings;
- `recovery\escrows\docflush_gate5_public_baseline_escrow_20260718T144151Z\`
  with the complete final escrow;
- `recovery\tools\` with the current staging recovery tools.

All files under the copied final escrow compare byte-for-byte with development.
The copied bundle independently verifies as complete history at `fa7c04dc`.

## Verification and boundaries

- Python 3.12 staging-tool tests: 9 passed;
- PowerShell parser: pass;
- final selective-plan source hashes: 316/316 exact, zero drift;
- documentation progress parity: 37 Markdown / 37 CSV;
- AI report audit after closeout: 30/30 enforced valid, 9 grandfathered,
  zero findings;
- fail-closed missing-escrow probe: expected refusal, staging HEAD and status
  unchanged;
- `C:\x64base`: unchanged at `fa7c04dc`, original dirty layer intact;
- Git index, commit, push, website, and deployment: unchanged.

## Next gate

Obtain separate authorization for the recovery-bound reset, exact 20-file
dirty-layer restoration, proof that all 36 public-only files remain exact, and
the corrected 316-file overlay. That authorization must bind the escrow,
plan-manifest, and ledger hashes above and must not imply Git or website work.
