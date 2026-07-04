# LabTalk

LabTalk is a living laboratory campus for computing education.

This workspace contains the LabTalk campus architecture, education map, and
registries. Runtime integration code belongs in `D:/code/ccode/src/labtalk`.

Current starting points:

- `LABTALK_CAMPUS_ARCHITECTURE_v0.md`
- `LABTALK_EDUCATION_MAP_v0.md`
- `LABTALK_PORTAL_CONCEPT_v0.md`
- `LABTALK_SDLC_FRAMEWORK_v0.md`
- `LABTALK_DEVELOPER_PROFILE_v0.md`
- `D:/code/ccode/docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md`
- `registries/apps.yaml`
- `registries/labs.yaml`
- `registries/concepts.yaml`
- `registries/proofs.yaml`
- `registries/portal.yaml`
- `labs/database_literacy_starter/LAB_DATABASE_LITERACY_STARTER_v0.md`
- `diagrams/LABTALK_VISUALS_v0.md`

Working rule:

```text
LabTalk can reference DotTalk++ source, cases, datasets, HELP, contracts, and
proof artifacts, but student-facing claims should be proof-backed or clearly
labeled as simulation, design intent, or historical review material.
```

First runnable slice:

```powershell
.\launch_portal.ps1
```

Then select `Runtime` -> `Run Database Literacy Starter` -> `Run`.

First SelfDoc lab:

```powershell
python .\portal\labtalk_portal.py --run-item runtime.selfdoc.comments_to_contracts.first_lab
```

This captures `CMDHELP`/`CMDHELPCHK` output plus a read-only comments/contracts
crosswalk for the narrow `CMDHELP`, `CMDHELPCHK` command set.
