# LabTalk SDLC Diagrams v0

Status: draft diagram pack
Created: 2026-07-04
Purpose: visual view of the Laboratory Campus SDLC by real, dev, plugged/stubbed, and planned state

## State Legend

```mermaid
flowchart LR
    real["real<br/>working behavior with evidence"]
    dev["dev<br/>working or useful, not fully promoted"]
    stub["plugged_stubbed<br/>entry point exists, behavior partial"]
    planned["planned<br/>documented intent only"]

    classDef real fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef dev fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef stub fill:#e8eefc,stroke:#4b62a3,color:#1d2b57
    classDef planned fill:#f2f2f2,stroke:#777,color:#333

    class real real
    class dev dev
    class stub stub
    class planned planned
```

## Current Campus State Map

```mermaid
flowchart TB
    campus["LabTalk Laboratory Campus"]

    runtime["DotTalk++ Runtime Systems Lab<br/>real"]
    help["HELP / CMDHELP / CMDHELPCHK Lab<br/>real"]

    selfdoc["Self-Documenting Systems Lab<br/>dev"]
    dblit["Database Literacy Starter<br/>dev"]
    cases["Case Library<br/>dev"]
    portal["LabTalk Portal<br/>dev"]

    history["Historical Data Systems Trail<br/>plugged_stubbed"]
    datasets["Dataset Library<br/>plugged_stubbed"]

    proofdash["Proof Dashboard<br/>planned"]
    staticweb["Static Campus HTML Snapshot<br/>planned"]
    nativecmd["Native LABTALK command<br/>planned"]
    notebooks["Jupyter / LMS Delivery<br/>planned"]

    campus --> runtime
    campus --> help
    campus --> selfdoc
    campus --> dblit
    campus --> cases
    campus --> portal
    campus --> history
    campus --> datasets
    campus --> proofdash
    campus --> staticweb
    campus --> nativecmd
    campus --> notebooks

    classDef real fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef dev fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef stub fill:#e8eefc,stroke:#4b62a3,color:#1d2b57
    classDef planned fill:#f2f2f2,stroke:#777,color:#333
    classDef root fill:#ffffff,stroke:#111,color:#111

    class campus root
    class runtime,help real
    class selfdoc,dblit,cases,portal dev
    class history,datasets stub
    class proofdash,staticweb,nativecmd,notebooks planned
```

## Promotion Flow

```mermaid
flowchart LR
    idea["idea / intake"]
    planned["planned"]
    stub["plugged_stubbed"]
    dev["dev"]
    real["real"]
    student["student_ready"]
    publish["publication_ready"]

    idea --> planned
    planned -->|"registry row or entry point exists"| stub
    planned -->|"runnable implementation exists"| dev
    stub -->|"useful behavior plus run evidence"| dev
    dev -->|"runtime/source/doc evidence linked"| real
    real -->|"reviewed setup, safety, expected results"| student
    student -->|"publication, source, fact, media review"| publish

    real -. "stale proof or drift" .-> dev
    dev -. "stubbed behavior found" .-> stub
    stub -. "entry point removed" .-> planned

    classDef planned fill:#f2f2f2,stroke:#777,color:#333
    classDef stub fill:#e8eefc,stroke:#4b62a3,color:#1d2b57
    classDef dev fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef real fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef ready fill:#dff5ff,stroke:#287c9b,color:#123b4a

    class planned planned
    class stub stub
    class dev dev
    class real real
    class student,publish ready
```

## SDLC, PLDC, and Ownership Split

```mermaid
flowchart TB
    dot["DotTalk++ SDLC<br/>runtime, source, commands, storage, HELP, tests"]
    maint["Maintenance SDLC<br/>SelfDoc, contracts, manualgen, datadict, messaging"]
    lab["LabTalk SDLC<br/>labs, cases, datasets, portal, proof registry"]
    pldc["PLDC<br/>product, lab, lesson, dashboard, public package delivery"]

    dot -->|"proves behavior"| lab
    maint -->|"governs evidence and reports"| lab
    dot -->|"runtime capability"| pldc
    lab -->|"learning package content"| pldc
    maint -->|"publication and validation gates"| pldc

    pldc -. "cannot bypass" .-> dot
    pldc -. "cannot bypass" .-> maint
    pldc -. "cannot bypass" .-> lab
```

## Case Study Lifecycle

```mermaid
flowchart LR
    memory["source_memory"]
    source["source_document_seen"]
    draft["normalized_case_draft"]
    readable["runtime_readable"]
    labcase["lab_candidate"]
    reviewed["reviewed_case"]
    student["student_case"]
    publication["publication_case"]

    memory --> source
    source --> draft
    draft --> readable
    readable --> labcase
    labcase --> reviewed
    reviewed --> student
    student --> publication

    draft -. "loader/readback only;<br/>not proof of history" .-> readable
    labcase -. "needs learning objective,<br/>dataset/tool path, proof plan" .-> reviewed
```

## Case Study Clusters

```mermaid
flowchart TB
    cases["LabTalk Case Studies"]

    overview["Data Trail Overview<br/>HIST-000, HIST-090"]
    army["Army Finance / JUMPS<br/>HIST-020"]
    cobol["COBOL / Connected Computers<br/>HIST-010"]
    codasyl["CODASYL / Alcoa<br/>HIST-030"]
    xbase["xBase / Earthkids / Paxon<br/>HIST-040, HIST-050, HIST-060"]
    erp["ERP / Hynix / SAP<br/>HIST-070, HIST-080"]
    eng["Engineering Runtime Cases<br/>ENG-010 through ENG-050"]

    cases --> overview
    cases --> army
    cases --> cobol
    cases --> codasyl
    cases --> xbase
    cases --> erp
    cases --> eng

    overview -->|"campus purpose"| lab["Lab package"]
    army -->|"payroll, records, audit trails"| lab
    cobol -->|"fixed records, batch"| lab
    codasyl -->|"network DB, industrial data"| lab
    xbase -->|"DBF, migration, small business"| lab
    erp -->|"ERP, SQL, integration"| lab
    eng -->|"runtime behavior proof"| lab
```

## Tool Lifecycle

```mermaid
flowchart TB
    tool["Laboratory Campus Tool"]

    portal["Portal launcher<br/>dev"]
    scanner["Report scanner<br/>real/dev by proof"]
    runner["Proof runner<br/>dev until transcript exists"]
    mutator["Fixture mutator<br/>planned/dev with disposable fixtures"]
    runtimecmd["Runtime command<br/>owned by DotTalk++ SDLC"]
    gui["GUI/workbench<br/>PLDC plus owning SDLC"]
    publisher["Publication generator<br/>PLDC plus maintenance SDLC"]

    tool --> portal
    tool --> scanner
    tool --> runner
    tool --> mutator
    tool --> runtimecmd
    tool --> gui
    tool --> publisher

    runner --> proof["proof artifact"]
    scanner --> report["report with authority limit"]
    mutator --> fixture["rollback and fixture boundary"]
    runtimecmd --> dot["DotTalk++ SDLC gate"]
    publisher --> review["publication review gate"]

    classDef dev fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef planned fill:#f2f2f2,stroke:#777,color:#333
    classDef gate fill:#fbe5d6,stroke:#a64b00,color:#4a2200

    class portal,scanner,runner,gui dev
    class mutator planned
    class proof,report,fixture,dot,review gate
```

## First Operational Board

```mermaid
flowchart LR
    real["real<br/>DotTalk++ runtime lab<br/>HELP/CMDHELP/CMDHELPCHK"]
    dev["dev<br/>SelfDoc first lab<br/>Database literacy starter<br/>Case library<br/>Portal"]
    stub["plugged_stubbed<br/>Historical trail<br/>Dataset library"]
    planned["planned<br/>Proof dashboard<br/>Static campus HTML<br/>Native LABTALK command<br/>Jupyter/LMS"]

    real -->|"proof refresh"| dev
    dev -->|"review and proof closure"| real
    stub -->|"first useful behavior"| dev
    planned -->|"registry or entry point"| stub
```

