# DotTalk++ SDLC Diagrams v0

Status: draft diagram pack
Created: 2026-07-04
Purpose: visual view of DotTalk++ SDLC, subsystem status, proof gates, maintenance lanes, and PLDC boundaries

## Status Legend

```mermaid
flowchart LR
    runtime["runtime-evidenced<br/>implemented/supported plus source evidence"]
    source["source-evidenced<br/>source exists, command proof incomplete"]
    help["help-catalog-evidenced<br/>HELP catalog exists, source mapping needs review"]
    planned["planned-or-in-progress<br/>do not market as complete"]
    review["review-needed<br/>no strong evidence in this pass"]

    classDef runtime fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef source fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef help fill:#e8eefc,stroke:#4b62a3,color:#1d2b57
    classDef planned fill:#f2f2f2,stroke:#777,color:#333
    classDef review fill:#f8d7da,stroke:#a94442,color:#4b1d1d

    class runtime runtime
    class source source
    class help help
    class planned planned
    class review review
```

## DotTalk++ SDLC Ownership Map

```mermaid
flowchart TB
    sdlc["DotTalk++ SDLC<br/>runtime, source, build, commands, storage, HELP, tests"]

    engine["x64base storage/data engine<br/>DBF/x64/VFP, memo, row codecs"]
    index["Indexing<br/>INX, CNX, CDX, LMDB, order, seek"]
    cli["Command runtime<br/>shell, registry, commands, scripts"]
    help["HELP / CMDHELP / CMDHELPCHK<br/>docs follow behavior"]
    maint["MAINT / maintenance SDLC<br/>SelfDoc, contracts, manualgen, datadict, messaging"]
    gui["GUI / TUI / browser fronts<br/>runtime contract plus PLDC delivery"]
    tests["Build, smoke, canaries, proof transcripts"]

    sdlc --> engine
    sdlc --> index
    sdlc --> cli
    sdlc --> help
    sdlc --> maint
    sdlc --> gui
    sdlc --> tests
```

## SDLC Flow

```mermaid
flowchart LR
    req["1. Requirements and boundary<br/>subsystem, risk, HELP impact, proof path"]
    design["2. Design<br/>modules, state, error/message contracts"]
    impl["3. Implementation<br/>correct source subsystem"]
    verify["4. Verification<br/>build, smoke, transcript, readback"]
    docs["5. Documentation and metadata<br/>HELP/CMDHELP/CMDHELPCHK alignment"]
    promote["6. Release and promotion<br/>professional_ready or lab_ready"]

    req --> design --> impl --> verify --> docs --> promote

    verify -. "fails" .-> design
    docs -. "wording outruns behavior" .-> impl
    promote -. "stale proof or drift" .-> verify
```

## Promotion Evidence Ladder

```mermaid
flowchart LR
    source["source_defined<br/>code or contract exists"]
    observed["runtime_observed<br/>behavior exercised"]
    documented["help_documented<br/>HELP/CMDHELP accurate"]
    validated["validated<br/>CMDHELPCHK/smoke/checker passed or classified"]
    pro["professional_ready<br/>safe for normal runtime use"]
    lab["lab_ready<br/>safe for LabTalk package"]

    source --> observed --> documented --> validated --> pro --> lab

    lab -. "LabTalk may package as real" .-> lt["LabTalk real"]

    classDef source fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef observed fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef ready fill:#dff5ff,stroke:#287c9b,color:#123b4a

    class source source
    class observed,documented,validated observed
    class pro,lab,lt ready
```

## Current Feature Status Map

```mermaid
flowchart TB
    features["DotTalk++ Feature Families"]

    runtime["runtime-evidenced<br/>concurrency, documentation, editing, education, GUI,<br/>index, integration, language, localization, memo,<br/>navigation, observability, query, relations, rules,<br/>schema, security, storage formats"]
    source["source-evidenced<br/>metadata / DDICT bridge"]
    planned["planned-or-in-progress<br/>future deeper proof, schema expansion, publication packaging"]
    review["review-needed<br/>scanner gaps and stale evidence"]

    features --> runtime
    features --> source
    features --> planned
    features --> review

    classDef runtime fill:#d9f7e5,stroke:#1d7f45,color:#0b3d20
    classDef source fill:#fff2cc,stroke:#9a7a00,color:#4a3600
    classDef planned fill:#f2f2f2,stroke:#777,color:#333
    classDef review fill:#f8d7da,stroke:#a94442,color:#4b1d1d

    class runtime runtime
    class source source
    class planned planned
    class review review
```

## Runtime Proof Gate

```mermaid
flowchart TB
    change["DotTalk++ change"]
    build["compile/build proof"]
    smoke["targeted smoke or DTS transcript"]
    readback["fixture/readback or command output capture"]
    help["HELP/CMDHELP readback"]
    validate["CMDHELPCHK or validator"]
    report["proof report / registry link"]

    change --> build
    build --> smoke
    smoke --> readback
    readback --> help
    help --> validate
    validate --> report

    build -. "compile fail" .-> fix["fix implementation"]
    smoke -. "behavior fail" .-> fix
    validate -. "doc mismatch" .-> docfix["fix docs, contracts, or command"]
```

## Maintenance Lane Map

```mermaid
flowchart TB
    maint["Maintenance SDLC<br/>report-only by default, explicit mutation gate"]

    comments["comments<br/>source comments -> SRC* evidence"]
    help["help<br/>HELP, DOTHELP, CMDHELP, HELP DATA"]
    manualgen["manualgen<br/>manual sections -> MAN* catalog"]
    datadict["datadict<br/>DDICT, DD* tables, evidence"]
    messaging["messaging<br/>MSG*, locale, typed output"]
    cmdhelpchk["cmdhelpchk<br/>registry/help/source validation"]
    contracts["contracts<br/>intake, registry, drift, promotion"]
    bbox["blackbox<br/>teaching transformation model"]
    maintcmd["maintenance<br/>MAINT command and cookbooks"]

    maint --> comments
    maint --> help
    maint --> manualgen
    maint --> datadict
    maint --> messaging
    maint --> cmdhelpchk
    maint --> contracts
    maint --> bbox
    maint --> maintcmd

    comments --> gate["explicit mutation gate"]
    help --> gate
    manualgen --> gate
    datadict --> gate
    messaging --> gate
    contracts --> gate
```

## Runtime Risk Classes

```mermaid
flowchart TB
    risk["DotTalk++ risk classification"]

    readonly["read-only<br/>inspect, report, list, help"]
    fixture["writes fixture<br/>safe disposable data"]
    datawrite["mutates data<br/>append, replace, delete, pack, import"]
    fswrite["filesystem write<br/>export, zip, DDL create, sidecars"]
    external["external process<br/>browser, editor, shell, SFTP, web"]
    sourcewrite["source/metadata publication mutation<br/>guarded maintenance only"]

    risk --> readonly
    risk --> fixture
    risk --> datawrite
    risk --> fswrite
    risk --> external
    risk --> sourcewrite

    datawrite --> proof["before/after proof and rollback"]
    fswrite --> proof
    external --> warn["explicit user-visible risk note"]
    sourcewrite --> gate["separate authorization gate"]
```

## Profiles and Boundaries

```mermaid
flowchart LR
    engine["ENGINE<br/>core storage/data engine<br/>no LabTalk/cases/media"]
    professional["PROFESSIONAL<br/>DotTalk++ commands, HELP, metadata,<br/>scripting, reporting, validation"]
    educational["EDUCATIONAL<br/>LabTalk, cases, student examples,<br/>teaching notes, guided explanations"]
    devonly["DEV_ONLY<br/>transitional tools, aliases, experiments"]
    maintenance["MAINTENANCE<br/>reports, repair planners, validators,<br/>guarded apply packages"]

    engine --> professional --> educational
    devonly -. "not public profile" .-> professional
    maintenance -. "governs, does not replace" .-> professional
```

## DotTalk++ / LabTalk / PLDC Boundary

```mermaid
flowchart TB
    dot["DotTalk++ SDLC<br/>owns runtime behavior"]
    lab["LabTalk SDLC<br/>owns learning truth state"]
    pldc["PLDC<br/>owns delivered packages"]

    dot -->|"runtime proof"| lab
    dot -->|"runtime capability"| pldc
    lab -->|"labs, cases, proof paths"| pldc

    pldc -. "cannot promote behavior past evidence" .-> dot
    lab -. "cannot claim unproven runtime behavior" .-> dot
```

## First Operational Board

```mermaid
flowchart LR
    real["runtime-evidenced<br/>core command families, indexing, storage,<br/>HELP/CMDHELP, query, relations, GUI lanes"]
    source["source-evidenced<br/>metadata / DDICT bridge"]
    dev["dev / maintenance<br/>comments, contracts, manualgen,<br/>messaging, datadict reports"]
    planned["planned<br/>status report, release profiles,<br/>risk matrix, LabTalk reference rule"]

    real -->|"proof refresh"| dev
    source -->|"runtime smoke and readback"| real
    dev -->|"validated report and guarded gate"| real
    planned -->|"charter and registry row"| dev
```
