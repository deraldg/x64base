# AIF-136 M4 Cognitive Demotion Proof V1

Evidence state: runtime-proven locally on 2026-08-27

Owner ruling: `AIF136-M3-PILOT-001`, approved at
`2026-08-27T00:10:00Z`

## Scope

This proof covers cognitive loading and retrieval metadata for the three exact
owner-approved historical Portal bodies. It does not prove, attempt, or
authorize physical storage movement or reclamation.

## Proven behavior

1. The current M1 inventory matches each manifest memory ID, path, byte size,
   and live SHA-256.
2. The M2/M4 classification projection marks exactly the three manifest IDs as
   `C3` and `owner_confirmed`.
3. Ordinary `onboard` recall does not name or load any selected full body.
4. `portal_history` recall resolves the bounded history summary.
5. The summary resolves every selected exact source path and SHA-256.
6. Every source body remains at its original Git-tracked path.

## Repeatable commands

```powershell
cd D:\code\ccode
.\.venv312\Scripts\python.exe labtalk\ai_portal\validate_memory_pilot_manifest.py
.\.venv312\Scripts\python.exe labtalk\ai_portal\build_portal_history_summary.py --check
.\.venv312\Scripts\python.exe labtalk\ai_portal\verify_memory_pilot_recall.py
.\.venv312\Scripts\python.exe labtalk\ai_portal\build_memory_storage_classification.py --check
.\.venv312\Scripts\python.exe labtalk\ai_portal\recall.py --validate
```

Expected controlled result: all commands pass; the manifest reports three
exact approved items and no physical action; the recall proof reports three
cold bodies excluded from onboarding and resolved through the history summary.

## Rollback

Remove the three exact owner-confirmed classification overrides and the
`trigger.portal_history` summary projection. The bodies never moved, so no data
restore is required.

## Boundary forward

M4 completion does not authorize M5. Any reconstructible-data reclaim pilot
requires a new explicit owner authorization over an exact manifest after a
successful reconstruction proof.
