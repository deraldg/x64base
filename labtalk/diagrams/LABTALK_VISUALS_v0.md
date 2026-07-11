# LabTalk Visuals v0

Status: draft visual pack
Purpose: reusable diagrams for presenting LabTalk as a Laboratory Campus

## Curated Ecosystem Relationship Map

Use this as the current source-derived boundary map for x64base engine services,
DotTalk++, DotScript, evidence, SelfDoc/MDO/manualgen, reviewed publication, and
the Laboratory Campus consumer layer.

- Source: `x64base_dottalkpp_campus_relationship_map_v1.mmd`
- Notes and source basis: `X64BASE_DOTTALKPP_CAMPUS_RELATIONSHIP_MAP_v1.md`

This v1 map supersedes the simpler boundary sketch below when authority or
development status matters. The older sketch remains useful as a compact
historical visual.

## Campus Map

Use this when explaining LabTalk at the highest level.

![LabTalk Campus Map](D:/code/ccode/labtalk/diagrams/labtalk_campus_map_v0.svg)

## Proof Path

Use this when explaining what makes LabTalk different from ordinary lesson
material.

![LabTalk Proof Path](D:/code/ccode/labtalk/diagrams/labtalk_proof_path_v0.svg)

## Mermaid: Campus Model

```mermaid
flowchart TB
    campus["LabTalk Laboratory Campus"]

    runtime["Runtime Systems Lab<br/>DotTalk++, commands, scripts, state"]
    history["Historical Data Systems Lab<br/>COBOL, CODASYL, xBase, SQL, ERP"]
    selfdoc["Self-Documenting Systems Lab<br/>comments, contracts, HELP, proof"]
    datasets["Dataset Library<br/>DBF, CSV, fixed records, SQL"]
    cases["Case Library<br/>engineering and historical stories"]
    gui["GUI and Portal Lab<br/>launchers, dashboards, workbenches"]

    campus --> runtime
    campus --> history
    campus --> selfdoc
    campus --> datasets
    campus --> cases
    campus --> gui
```

## Mermaid: LabTalk Learning Chain

```mermaid
flowchart LR
    concept["Concept"]
    app["App"]
    dataset["Dataset"]
    command["Command or Script"]
    proof["Proof"]
    casefile["Case"]
    lesson["Lesson"]

    concept --> app --> dataset --> command --> proof --> casefile --> lesson
```

## Mermaid: First Working Slice

```mermaid
sequenceDiagram
    participant P as LabTalk Portal
    participant R as Registry
    participant D as DotTalk++ Runtime
    participant E as EDREF Help
    participant T as Proof Transcript

    P->>R: read portal.yaml
    P->>R: find runtime.database_literacy_starter
    P->>D: run database_literacy_starter_v0.dts
    D->>E: HELP /ED MODEL, TABLE_RECORD_FIELD, INDEX, SCAN
    E-->>D: educational concept output
    D-->>P: stdout/stderr and return code
    P->>T: save transcript under proofs/runs
```

## Mermaid: Boundary Model

```mermaid
flowchart TB
    x64["x64base Engine<br/>storage, DBF, indexes, runtime foundation"]
    dot["DotTalk++<br/>command shell, scripts, HELP, cases"]
    lab["LabTalk<br/>campus, labs, lessons, portal, proof paths"]
    site["x64base.com<br/>public presentation"]

    x64 --> dot
    dot --> lab
    lab --> site

    lab -. references .-> x64
    lab -. runs/observes .-> dot
    site -. explains .-> lab
```
