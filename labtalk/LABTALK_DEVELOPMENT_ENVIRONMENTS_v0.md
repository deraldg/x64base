# LabTalk Development Environments v0

Status: draft tracker
Created: 2026-07-05
Scope: Development and runtime requirements for LabTalk campus entities

## Purpose

This file tracks the development environments needed by campus entities such as
DotTalk++, pydottalkpp, Python-based tools, the LabTalk Portal, and x64base.

The goal is to make the runtime contract visible:

```text
entity -> language/runtime -> build or launch path -> dependencies -> proof
```

This is a tracking document, not proof by itself. Each row should eventually
point to source, build files, launch scripts, smoke runs, or proof artifacts.

## Tracking Rules

- Keep each entity separate from the environment that runs it.
- Record known paths and commands before adding new tooling.
- Mark assumptions as `needs_verification`.
- Link runtime proof when an entity is promoted from planning to active use.
- Prefer local, repeatable commands over machine-specific notes.
- Do not treat a successful install as proof that the campus entity works.

## Environment States

| State | Meaning |
|---|---|
| `known` | Requirement is established by source, config, docs, or current successful run. |
| `observed` | Requirement was seen on this machine but is not yet documented as a contract. |
| `needs_verification` | Likely requirement; confirm with build, launch, or source review. |
| `planned` | Desired environment support that is not implemented yet. |
| `retired_or_optional` | Exists historically or for convenience, but is not required for the current path. |

## Campus Entity Matrix

| Entity | Purpose | Primary runtime | Development tools | Current state | Evidence / next proof |
|---|---|---|---|---|---|
| `dottalkpp` | DotTalk++ command runtime, HELP, scripts, database commands, runtime labs. | Native Windows executable, likely C++ x64. | Visual Studio / MSVC, CMake or existing build scripts, source under `D:/code/ccode/src`. | `needs_verification` | Confirm current build command, compiler version, output path, and smoke command. |
| `x64base` | Core xBase/database engine layer used by DotTalk++ and runtime systems labs. | Native C++ library/runtime layer. | MSVC toolchain, engine source, tests or smoke scripts. | `needs_verification` | Link build target, engine smoke tests, and crosswalk proof. |
| `pydottalkpp` | Python bridge or wrapper around DotTalk++ behavior. | Python plus native runtime boundary. | Python virtual environment, packaging metadata, native DLL/EXE access path. | `planned` | Locate or create project root, package metadata, import smoke, and runtime bridge proof. |
| `python.tools` | Python scripts for reports, proof generation, validators, registry checks, and portal support. | Python 3.x on Windows. | `venv` or Conda, `pip`, standard library plus YAML/report dependencies. | `observed` | Inventory Python scripts and dependency imports; pin minimum Python version. |
| `labtalk.portal` | Local LabTalk campus launcher and navigation surface. | Python script currently launched by PowerShell. | Python 3.x, PowerShell, YAML/registry files, local filesystem access. | `known` | `launch_portal.ps1`; `portal/labtalk_portal.py`; add portal smoke transcript. |
| `labtalk.registries` | YAML campus indexes for apps, labs, concepts, proofs, and portal actions. | YAML files consumed by Python and documentation. | Text editor, YAML parser, registry validators. | `known` | `registries/*.yaml`; add schema or validation command. |
| `labtalk.docs` | Campus architecture, SDLC, education map, diagrams, lab docs, and product maps. | Markdown. | Markdown editor, optional static HTML/report generation. | `known` | Top-level `LABTALK_*_v0.md`; add generated index proof if needed. |
| `labtalk.datasets` | Sample data for database literacy and historical labs. | DBF/xBase, CSV, fixed records, SQL, or simulated fixtures. | Dataset registry, checksums, fixture reset scripts. | `planned` | Create `registries/datasets.yaml` and fixture policy before student-ready labs. |
| `manualgen.selfdoc` | Maintenance and self-documenting system reports. | Native DotTalk++ plus Python/report tooling. | Source comment scanners, HELP/CMDHELP/CMDHELPCHK, report generators. | `observed` | Link SelfDoc lab run proof and command crosswalk. |

## Baseline Workstation Requirements

These requirements describe the local Windows development machine expected to
run the current campus slice.

| Requirement | State | Notes |
|---|---|---|
| Windows host | `known` | Current paths and scripts use Windows drive syntax and PowerShell. |
| PowerShell | `known` | Used by `launch_portal.ps1` and local automation. |
| Python 3.x | `observed` | Required by the LabTalk Portal and report scripts; exact minimum version still needs verification. |
| MSVC / Visual Studio Build Tools | `needs_verification` | Required for native DotTalk++ and x64base builds if building from source. |
| CMake or existing native build scripts | `needs_verification` | Confirm actual current build system before documenting as required. |
| Git | `observed` | Needed for source tracking, branch work, and proof review. |
| YAML parser for Python | `required` | PyYAML is declared in `labtalk/requirements.txt` for portal and registry loading. |

## Entity Records

### DotTalk++

Expected role:

```text
authoritative runtime for commands, HELP, CMDHELP, CMDHELPCHK, scripts, and
database behavior used by LabTalk labs.
```

Track:

| Field | Value |
|---|---|
| Source root | `D:/code/ccode/src` |
| Runtime output | `needs_verification` |
| Build command | `needs_verification` |
| Smoke command | `needs_verification` |
| Required compiler | `needs_verification` |
| LabTalk owner | Runtime Systems Lab |
| Proof target | command smoke transcript plus HELP/CMDHELP readback |

### x64base

Expected role:

```text
engine layer for xBase-style tables, records, fields, indexes, relations, and
storage behavior.
```

Track:

| Field | Value |
|---|---|
| Source root | `needs_verification` |
| Build target | `needs_verification` |
| Runtime consumers | `dottalkpp`, LabTalk runtime systems labs |
| Test or proof command | `needs_verification` |
| LabTalk owner | Runtime Systems Lab |
| Proof target | engine feature crosswalk plus smoke tests |

### pydottalkpp

Expected role:

```text
Python-accessible bridge to DotTalk++ behavior for notebooks, portal tools, test
harnesses, or lightweight teaching scripts.
```

Track:

| Field | Value |
|---|---|
| Project root | `planned` |
| Python package name | `pydottalkpp` |
| Supported Python versions | `needs_verification` |
| Native boundary | `planned` |
| Packaging | `planned` |
| First smoke | `python -c "import pydottalkpp"` once package exists |
| Proof target | import smoke plus one read-only runtime command |

### Python Tools

Expected role:

```text
registry reads, report generation, portal actions, proof capture, and validation.
```

Track:

| Field | Value |
|---|---|
| Primary entrypoint | `portal/labtalk_portal.py` |
| Launcher | `launch_portal.ps1` |
| Dependency file | `planned` |
| Virtual environment policy | `needs_verification` |
| Smoke command | `python .\portal\labtalk_portal.py --run-item runtime.selfdoc.comments_to_contracts.first_lab` |
| Proof target | portal launch transcript and proof output path |

### LabTalk Portal

Expected role:

```text
local campus launcher that exposes approved docs, labs, runtime actions, and
proof capture paths.
```

Track:

| Field | Value |
|---|---|
| Source root | `D:/code/ccode/labtalk/portal` |
| Launcher | `D:/code/ccode/labtalk/launch_portal.ps1` |
| Registry inputs | `registries/portal.yaml`, related campus registries |
| Runtime state | `dev` |
| Student readiness | not student-ready until portal proof dashboard and safety wording are complete |
| Proof target | portal action smoke transcript |

## Open Decisions

1. Decide whether LabTalk uses a single Python environment or separate
   environments for portal, reports, notebooks, and pydottalkpp.
2. Decide whether pydottalkpp is a real package, a thin subprocess wrapper, or a
   later native extension.
3. Confirm the canonical native build path for DotTalk++ and x64base.
4. Decide whether environment requirements belong only in this tracker or also
   in per-entity manifests under `registries`.
5. Add a machine-readable `tools` or `environments` registry only after the
   manual tracker stabilizes.

## Runtime Requirement Template

Use this template for every new campus entity:

```yaml
id:
name:
purpose:
owner:
source_root:
runtime:
language:
build_or_install:
launch_or_smoke:
required_tools:
required_environment:
inputs:
outputs:
mutation_policy:
proof:
truth_state:
environment_state:
last_verified:
next_gate:
```

## First Verification Backlog

1. Run or document the current DotTalk++ build command.
2. Run a DotTalk++ command smoke and capture the transcript path.
3. Confirm the x64base source root and build target.
4. Inventory Python scripts and imports under `D:/code/ccode/labtalk`.
5. Decide a Python environment policy and create a minimal requirements file if
   imports require non-standard packages.
6. Run the LabTalk Portal launcher and record the successful command and output.
7. Create a placeholder pydottalkpp project record only after its intended
   bridge style is decided.
