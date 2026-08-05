# AI Portal Tracking Dogfood -- ERD / PFD / DFD (AIF-089)

High-level diagrams of the DBF-native tracking layer and its dogfood pipeline
(built under AIF-086; command-drift lane AIF-088). Owning lane AIF-089 (diagrams /
documentation); claim host-side with `session_coordinator.py claim-aif` if tracked.

Key-FK note: cross-references are NATURAL KEYS (member `MKEY`, lane `LKEY`, run
`RKEY`), not numeric ids -- the tables are seeded from external authored data with
no engine ids, so `IMPORT` binds a key column 1:1 by name.

## 1. ERD -- entities and relationships (high level)

```mermaid
erDiagram
    SYSMEMBER ||--o{ SYSLANE    : "OWNERKEY/STEWARDKEY -> MKEY"
    SYSMEMBER ||--o{ SYSRUN     : "MEMBER/OWNER/COMMIT/AUTHOR/PLAN -> MKEY"
    SYSMEMBER ||--o{ SYSTASK    : "ASSIGNKEY -> MKEY"
    SYSLANE   ||--o{ SYSRUNLANE : "LKEY -> LANEKEY"
    SYSRUN    ||--o{ SYSRUNLANE : "RKEY -> RUNKEY"
    SYSLANE   ||--o{ SYSPROOF   : "LKEY -> LANEKEY"
    SYSLANE   ||--o{ SYSTASK    : "LKEY -> LANEKEY"

    SYSLANE {
        string LKEY PK
        string TITLE
        string OWNERKEY FK
        string STEWARDKEY FK
        int    STATUS
        int    ROWVER
    }
    SYSRUN {
        string RKEY PK
        string MEMBERKEY FK
        string ROLE
        string PROJECT
        int    STATUS
    }
    SYSRUNLANE {
        string RUNKEY FK
        string LANEKEY FK
    }
    SYSPROOF {
        string PKEY PK
        string LABEL
        string STATE
        string LANEKEY FK
    }
    SYSTASK {
        string TKEY PK
        string TITLE
        string ASSIGNKEY FK
        string LANEKEY FK
        int    STATUS
    }
    SYSMEMBER {
        string MKEY PK
        int    KIND
        int    STATUS
    }
```

`SYSLANE` is the hub: a lane has many runs (via the `SYSRUNLANE` crosswalk), many
proofs, and many tasks; every attribution resolves to `SYSMEMBER` by key. Identity,
BBS, and rulings are adjacent subsystems (own catalogs) joined by the same `MKEY`.

## 2. PFD -- process flow (the dogfood pipeline + CRUD write)

```mermaid
flowchart TD
    subgraph AUTH["Authored registries (drift-prone)"]
        Q["AI_INTERACTION_INTAKE_QUEUE_V1.md"]
        R["ai_runs.yaml"]
        P["proofs.yaml / proofs.d"]
        T["ai_portal_tasks.yaml"]
    end
    Q --> S
    R --> S
    P --> S
    T --> S
    S["seed_tracking.py<br/>extract + normalize"] --> CSV[("seed/*.csv")]
    CSV --> L["load/reload .dts<br/>CREATE X64 + IMPORT"]
    L --> ENG{{"DotTalk++ engine"}}
    ENG --> DBF[("metadata/portal/*.dbf<br/>SYSLANE RUN RUNLANE PROOF TASK")]
    DBF --> RD["crud.read / read_rows<br/>pure DBF, no engine"]
    RD --> REP["build_reports.py --source dbf"]
    REP --> HTML["AI Portal report HTML"]

    subgraph WRITE["CRUD write -- posture A (single-writer)"]
        W["crud.py create / update / delete"]
    end
    W -->|"pydottalk (needs xbase)"| ENG
    W -->|"--emit DotScript (lock-safe)"| L
    W -->|"--emit --ram (fsram dry run, zero disk)"| ENG
```

Authored state flows left-to-right into the engine, which is the single writer;
reports DERIVE from the store, so a landed lane cannot be missing from a view.
The write side has three surfaces, all validated by the same registry.

## 3. DFD -- data flow (level 1)

```mermaid
flowchart LR
    MAINT(["Maintainer / AI agents"])
    AUTHS[("Authored registries<br/>YAML + intake MD")]
    CSVS[("Seed CSVs")]
    STORE[("DBF store<br/>metadata/portal")]
    RPT["HTML reports"]

    MAINT -->|edit| AUTHS
    AUTHS -->|"P1 extract (seed_tracking.py)"| CSVS
    CSVS -->|"P2 load (engine CREATE+IMPORT)"| STORE
    STORE -->|"P3 read (crud.read)"| P4["P4 derive<br/>build_reports.py"]
    P4 --> RPT
    MAINT -->|"P5 CRUD write (crud.py)"| STORE
    RPT -->|view| MAINT

    classDef ext fill:#1d2a33,stroke:#2e4a5c,color:#dfe7ef;
    classDef store fill:#171e26,stroke:#26323f,color:#dfe7ef;
    class MAINT ext;
    class AUTHS,CSVS,STORE store;
```

Two data stores that drift (authored registries, seed CSVs) feed one store that
cannot (the engine's DBF), and every sink (reports, CRUD) reads through the engine
or its pure reader -- the derived-truth thesis drawn as a flow.
