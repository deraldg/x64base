# Laboratory Campus / LabTalk

The **Laboratory Campus** is the public education and collaboration frame for
this lane. **LabTalk** remains the project mark and local workspace name.

This workspace contains the LabTalk campus architecture, education map, and
registries. Runtime integration code belongs in `D:/code/ccode/src/labtalk`.

Repository boundary:

```text
Engine/runtime truth and Arctic GUI/TUI work stay with x64base.
LabTalk owns the portal, registries, labs, proofs, assignments, and campus overlays.
DotTalk++ remains the runtime/manual identity until a cleaner source split is justified.
```

Current starting points:

- `REPO_BOUNDARIES_LABTALK_CONSUMER_v1.md`
- `LABTALK_CAMPUS_ARCHITECTURE_v0.md`
- `LABTALK_EDUCATION_MAP_v0.md`
- `LABTALK_PORTAL_CONCEPT_v0.md`
- `LABTALK_SDLC_FRAMEWORK_v0.md`
- `LABTALK_DEVELOPER_PROFILE_v0.md`
- `LABTALK_DEVELOPMENT_ENVIRONMENTS_v0.md`
- `ai_portal/README.md`
- `ai_portal/AI_PORTAL_HARDENING_LANE_V1.md`
- `D:/code/ccode/docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md`
- `D:/code/ccode/docs/maintenance/diagrams/DOTTALKPP_SDLC_DIAGRAMS_v0.md`
- `D:/code/ccode/docs/planning/SDLC_PLDC_PLANNING_ADOPTION_v0.md`
- `registries/apps.yaml`
- `registries/ai_portal.yaml`
- `registries/labs.yaml`
- `registries/lessons.yaml`
- `registries/lms.yaml`
- `registries/concepts.yaml`
- `registries/proofs.yaml`
- `registries/portal.yaml`
- `lessons/README.md`
- `lms/README.md`
- `labs/database_literacy_starter/LAB_DATABASE_LITERACY_STARTER_v0.md`
- `diagrams/LABTALK_VISUALS_v0.md`
- `diagrams/LABTALK_SDLC_DIAGRAMS_v0.md`

Build boundary:

```text
Base DotTalk++ engine/runtime work builds in D:/code/ccode/build.
LabTalk + pydottalk companion work builds in D:/code/ccode/build-labtalk.
```

Primary LabTalk bindings build:

```powershell
.\aops\build-labtalk.ps1
```

Working rule:

```text
Laboratory Campus / LabTalk can reference DotTalk++ source, cases, datasets,
HELP, contracts, and proof artifacts, but student-facing claims should be
proof-backed or clearly labeled as simulation, design intent, or historical
review material.
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

Reserved LMS communications lane:

```powershell
python ..\src\labtalk\lms\cli.py --queue .\lms\queue\outbox status
```

The `LMS` portal section exposes the same local-only status check. Moodle is the
first provider candidate, but no LMS endpoint, token, or live delivery is
configured.
