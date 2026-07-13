# LabTalk Portal Concept v0

Status: draft concept
Scope: Local LabTalk portal / launcher / campus access point
Created: 2026-07-02

## Purpose

LabTalk needs an official entry point before it needs a large application.

The portal should give access to campus features as they are built:

- labs
- apps
- cases
- datasets
- runtime demos
- proof reports
- documentation
- external tools
- generated lessons

The first portal should be small, local, inspectable, and easy to replace.

## Portal Definition

```text
The LabTalk Portal is the local campus launcher. It reads LabTalk registries,
shows available labs/apps/cases, and launches the right tool, document, script,
runtime command, or proof report.
```

It is not the whole campus. It is the front gate.

## Recommended First Form

Use a small local menu program with a window frame.

Best first implementation:

```text
Python + Tkinter
```

Why:

- included with most Python installs
- cross-platform enough for Windows/Linux/macOS
- no web server required
- good for menus, tabs, buttons, text panes, file launchers, and simple logs
- can launch DotTalk++ scripts and external documents
- easy to replace later with a web UI or richer desktop app

The portal can start as:

```text
D:/code/ccode/labtalk/portal/labtalk_portal.py
```

## Why Not Start With a Full Web App

A web app may be useful later, but it adds routing, packaging, local server
state, browser behavior, and frontend build choices before the campus model is
stable.

LabTalk first needs:

```text
registries -> launcher -> proof readback -> lesson navigation
```

A local framed launcher is enough for that.

## Portal Modes

The portal should have clear sections:

| Section | Purpose |
|---|---|
| Campus Map | Shows the current buildings/apps/labs. |
| Labs | Lists runnable or draft labs from `registries/labs.yaml`. |
| Apps | Lists registered apps from `registries/apps.yaml`. |
| Cases | Opens case registry entries and case files. |
| Datasets | Lists datasets and known specimen files. |
| Proofs | Shows proof states and opens proof reports. |
| Runtime | Launches DotTalk++ commands, DTS scripts, or transcripts. |
| Docs | Opens LabTalk architecture, education map, and README. |

## Minimal Window Layout

```text
+------------------------------------------------------------+
| LabTalk Portal                                             |
+----------------------+-------------------------------------+
| Campus Map           |  Selected item title                |
| Labs                 |                                     |
| Apps                 |  Summary / metadata                 |
| Cases                |                                     |
| Datasets             |  Actions:                           |
| Proofs               |  [Open Doc] [Run] [Show Evidence]   |
| Runtime              |                                     |
| Docs                 |  Output / notes pane                |
+----------------------+-------------------------------------+
```

Use a normal framed desktop window at first. Do not hide behind a complicated
visual metaphor. The campus metaphor belongs in organization, not decoration.

## Launchable Item Types

The portal should eventually support these item types:

| Type | Example | First behavior |
|---|---|---|
| Markdown doc | `LABTALK_CAMPUS_ARCHITECTURE_v0.md` | Open in default editor/viewer. |
| YAML registry item | `lab.database_literacy.starter` | Show metadata in portal. |
| DotTalk++ command | `HELP`, `CASE LIST` | Launch configured runtime or show planned command. |
| DTS script | `lab_*.dts` | Run through DotTalk++ when runtime path is configured. |
| Case file | `CASE_ENG_040_METADATA_DATA_DICTIONARY.md` | Open or render summary. |
| Dataset | `STUDENTS.DBF` | Show metadata or open through DotTalk++ lab. |
| Proof report | Runtime transcript / CMDHELPCHK report | Open report, show proof state. |
| External tool | Jupyter, browser, editor, MS Project/Planner export | Launch if configured. |

## Registry Additions Needed

Add a portal registry:

```text
D:/code/ccode/labtalk/registries/portal.yaml
```

It should describe menu sections and default actions. Example:

```yaml
sections:
  - id: portal.docs
    label: Docs
    items:
      - id: doc.campus_architecture
        label: Campus Architecture
        kind: markdown
        path: D:/code/ccode/labtalk/LABTALK_CAMPUS_ARCHITECTURE_v0.md
```

The portal should read existing registries rather than hard-code everything.

## Configuration

The portal needs a local config file:

```text
D:/code/ccode/labtalk/labtalk.local.yaml
```

This should not be treated as shared doctrine. It is machine-local configuration.

Possible fields:

```yaml
paths:
  ccode_root: D:/code/ccode
  labtalk_root: D:/code/ccode/labtalk
  dottalkpp_exe: D:/code/ccode/build-msvc/.../dottalkpp.exe
  dottalkpp_data: D:/code/ccode/dottalkpp/data
tools:
  editor: code
  browser: default
  python: python
```

Do not require all paths to exist before the portal opens. Missing tools should
show a clear status.

## Portal Proof Rule

The portal should display proof state, not hide it.

Examples:

```text
Database Literacy Starter
Status: draft
Proof: runtime_lab_candidate
Next gate: Attach runtime transcript and HELP/CMDHELP readback.
```

This keeps LabTalk honest. Draft labs can be visible without being presented as
student-ready.

## First Portal Capabilities

Milestone P0:

- open framed window
- read `registries/apps.yaml`
- read `registries/labs.yaml`
- read `registries/concepts.yaml`
- read `registries/proofs.yaml`
- show sections: Docs, Apps, Labs, Proofs
- open Markdown files with default system handler
- show YAML item metadata
- show missing-runtime status without failing

Milestone P1:

- add case registry readback
- add dataset registry
- add command launch configuration
- capture command output into portal pane
- add proof report links

Milestone P2:

- run curated DotTalk++ DTS lab scripts
- save transcripts under `labtalk/proofs/`
- mark proof readback status
- generate a static campus HTML snapshot

## Implementation Boundary

Portal source belongs under:

```text
D:/code/ccode/labtalk/portal
```

LabTalk C++ runtime integration belongs under:

```text
D:/code/ccode/src/labtalk
```

The portal may call DotTalk++, but it should not require C++ changes for P0.

## Future Portal Forms

The portal can later have multiple frontends over the same registries:

| Frontend | Use |
|---|---|
| Tkinter desktop | First local launcher. |
| Static HTML | Shareable campus snapshot. |
| Local web app | Rich navigation and dashboards. |
| DotTalk++ command | Runtime-native access, e.g. `LABTALK`. |
| Jupyter notebooks | Interactive lessons. |
| GUI workbench | PLDC demonstrations and richer student labs. |

The registry model should outlive any one portal frontend.

## Recommendation

Build the first portal as a small Python/Tkinter app.

Keep it registry-driven and local:

```text
LabTalk registries -> portal window -> open/run/show evidence
```

Do not start with a large framework. The goal is immediate access to campus
features while the official LabTalk system takes shape.

