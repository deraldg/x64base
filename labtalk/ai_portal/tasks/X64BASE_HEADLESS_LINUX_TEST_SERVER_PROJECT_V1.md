# x64base Headless Linux Test Server Project v1

Status: **Planned — design and deployment validation**  
Maintainer and acceptance authority: **Derald**  
Owning project: `project.x64base.headless_test_server`  
Parent project: `project.x64base.runtime`  
Owning lifecycle: **DotTalk++ SDLC plus deployment-validation lane**  
Current SDLC lane: **design**

## Authority and Baseline

```text
Authoritative development source: D:\code\ccode
Curated publication staging:     C:\x64base
Public repository:                https://github.com/deraldg/x64base
Public branch:                    main
Public baseline for this packet:  9dc781eb39048dd4082029b76091d1b779df5685
AI Portal entry:                  https://github.com/deraldg/x64base/blob/main/AI_PORTAL.md
Target host class:                dedicated headless Linux PC
```

The public repository is the portable planning and publication baseline. It is not
newer or stronger authority than the current contents of `D:\code\ccode`.

This packet authorizes project planning and explicit deployment work requested by
Derald. It does not authorize exposing a mutation-capable service to the public
Internet, publishing credentials, weakening security policy, or treating an
unproven server as production-ready.

## Purpose

Build a controlled headless Linux reference deployment for DotTalk++ / x64base so
the project can prove its cross-platform server behavior before selecting shared
hosting, VPS, container, or long-term home-hosting infrastructure.

The server is a laboratory and deployment proof surface. It should establish what
the engine actually requires for:

- native Linux compilation and packaging;
- unattended service startup and restart;
- DBF, x64 header, CDX, memo, and LMDB operation;
- isolated user or request sessions;
- concurrent readers and controlled writers;
- crash, restart, backup, and recovery behavior;
- tuple and metadata delivery through a bounded HTTP interface;
- private remote access followed by an optional read-only public demonstration;
- AI Portal authorization and audit integration.

## Architectural Position

The system is already intended to be cross-platform. WSL is a useful build and
compatibility surface, but the target proof environment is a native Linux host.
The project must distinguish these questions:

```text
Can the source build on Linux?
Can the engine run correctly as an unattended Linux service?
Can multiple web requests be mapped to isolated x64base sessions safely?
Can a constrained public interface be exposed without granting shell authority?
```

The proposed deployment shape is:

```text
browser or trusted client
        |
      HTTPS
        |
reverse proxy (Caddy or Nginx)
        |
bounded x64base API/service
        |
independent request/session contexts
        |
DotTalk++ / x64base engine
        |
DBF + CDX + memo + LMDB test stores
```

The web layer must not expose the interactive command shell directly. Each
request must enter through a declared operation contract and receive an isolated
workspace/session context rather than sharing one mutable global `DbArea`, cursor,
order, relation, or transaction state.

## Project Principles

1. **Native proof over assumption.** Cross-platform design is not counted as Linux
   deployment proof until the current source builds and passes its relevant tests.
2. **Read-only first.** Public or semi-public access begins with status, schema,
   metadata, and bounded record reads.
3. **Session isolation.** Unrelated requests do not share mutable work areas,
   cursors, relation state, transactions, or authorization state.
4. **Engine authority remains internal.** HTTP is an adapter over the engine, not a
   second database implementation.
5. **No development-tree serving.** The server runs from a deployment package and
   dedicated data roots, never directly from `D:\code\ccode` or backup folders.
6. **Security policy remains the final clamp.** Role or project authorization does
   not override runtime path, command, privilege, secret, host-command, or unsafe
   operation restrictions.
7. **Proof is staged and reversible.** Each promotion gate can be disabled without
   damaging authoritative source or data.

## Initial Host Layout

The exact distribution and paths are implementation decisions, but the first
reference layout should preserve clear separation:

```text
/opt/x64base/                 deployed binaries and immutable support files
/etc/x64base/                 service configuration without embedded secrets
/var/lib/x64base/demo/        read-only demonstration data
/var/lib/x64base/test/        mutation, locking, and recovery test data
/var/lib/x64base/private/     non-public validation data
/var/log/x64base/             service and audit logs
```

Run the service under a dedicated unprivileged operating-system account. That
account should have no write access outside the declared test, log, and temporary
roots.

## Initial Interface Contract

The first service increment should be deliberately small:

```text
GET  /status
GET  /version
GET  /tables
GET  /tables/{table}/schema
GET  /tables/{table}/records?limit={n}&offset={n}
GET  /metadata/projects
GET  /metadata/commands
```

The initial interface is read-only. It must apply limits, deterministic ordering,
input validation, path confinement, and structured error responses.

The following surfaces are explicitly deferred until authorization, isolation,
and mutation semantics are proven:

```text
POST /script
POST /command
POST /tables/{table}/records
PATCH/DELETE record operations
index rebuild or repair operations
host-command execution
arbitrary filesystem access
```

A future script endpoint must accept only reviewed task recipes or a constrained
operation language. It must not be a remote shell disguised as an API.

## Remote-Access Stages

Use the least exposed method that can prove the current gate:

1. local console and SSH on the headless host;
2. local-area-network HTTP access;
3. private remote access through Tailscale or an equivalent authenticated overlay;
4. optional controlled HTTPS tunnel for read-only demonstration;
5. conventional public ingress only after security and recovery gates pass.

Router port forwarding is not the default first step. Public SSH exposure is not
required for the project.

## Work Lanes

### Lane 1 — Linux Build Refresh

- identify supported Linux compiler, CMake, package, and dependency versions;
- rebuild the current source under WSL as a fast compatibility check;
- build again on the native headless Linux host;
- record platform-specific source, path, library, and packaging defects;
- run existing command, expression, tuple, index, memo, relation, and LMDB smoke
  tests that are portable to the host;
- produce a repeatable build profile rather than a one-off command transcript.

### Lane 2 — Deployment Package

- define the installed binary, library, configuration, script, schema, help, and
  seed-data set;
- keep runtime data outside the installation tree;
- define version and build identity reporting;
- provide installation, upgrade, rollback, and uninstall procedures;
- prevent deployment artifacts from becoming new source authority.

### Lane 3 — Service Host

- implement a noninteractive service entry point;
- run it under `systemd` or an equivalent supervisor;
- prove clean startup, orderly shutdown, restart, and failure reporting;
- define health checks that do not mutate database state;
- keep reverse-proxy and engine-service responsibilities separate.

### Lane 4 — Request and Session Isolation

- define one request/session context per authenticated client or operation;
- prove isolation of work areas, cursors, selected orders, filters, relations,
  variables, transactions, and authorization state;
- define safe pooling only after lifecycle reset and cleanup are measurable;
- reject any design that shares one interactive shell session across unrelated
  requests.

### Lane 5 — Storage and Concurrency

Validate each storage family independently:

- DBF and x64 header open/read/write behavior;
- CDX and LMDB index open, seek, mutation, close, and reopen behavior;
- memo reference and payload-store permissions;
- multiple readers;
- reader plus writer;
- two writers targeting separate records;
- conflicting writers targeting the same record;
- process termination during mutation;
- stale lock and abandoned-session handling;
- backup and restore with explicit consistency rules.

Results must distinguish engine defects, deployment defects, and unsupported test
assumptions.

### Lane 6 — Security and Authorization

Crosswalk the server against the existing security module and the planned
`USERS -> TEAM_MEMBER -> TEAM_ASSIGNMENT -> ROLE/PERMISSION -> AUTHORIZATION`
model.

Minimum controls:

- dedicated unprivileged OS identity;
- authenticated private access before public exposure;
- no credentials in source, registry, logs, or project packets;
- path canonicalization and confinement;
- deny-by-default operation routing;
- request size, record count, runtime, and resource limits;
- explicit read versus mutation permissions;
- expiring authorization for elevated or dangerous operations;
- audit record containing actor, session, operation, scope, result, duration, and
  proof reference;
- preservation of the runtime security policy as the final operational guard.

### Lane 7 — Recovery and Operations

- service restart with tables previously open;
- host reboot and automatic service recovery;
- corrupted or missing data-root behavior;
- backup and restore proof;
- disk-full, permission-denied, and dependency-missing behavior;
- log rotation and bounded temporary storage;
- configuration rollback;
- documented emergency stop and public-ingress disable procedure.

### Lane 8 — Demonstration and Hosting Decision

- expose a read-only tuple/metadata demonstration;
- measure CPU, memory, disk, startup, and request behavior;
- record home-network availability and upload-bandwidth constraints;
- compare the proven requirements with shared hosting, VPS, container, and
  dedicated-host options;
- decide whether the headless PC remains a laboratory, becomes a private service,
  supports a public demonstration, or is replaced by a VPS deployment.

## Required Test Data Separation

Use disposable or copied data only:

```text
public demonstration copy -> read-only
mutation test copy         -> replaceable
recovery test copy         -> intentionally breakable
private validation copy    -> never publicly routed
```

Authoritative development tables, maintained metadata, backups, personal files,
and publication staging must not be mounted as remotely mutable server data.

## Proof Matrix

| Gate | Required proof |
| --- | --- |
| HLS-1 Build | clean native Linux configure/build plus recorded dependencies |
| HLS-2 CLI | noninteractive script exits cleanly with deterministic output |
| HLS-3 Storage | DBF/CDX/memo/LMDB reopen and mutation smokes pass on copied data |
| HLS-4 Service | supervised startup, health check, shutdown, and restart pass |
| HLS-5 Isolation | concurrent requests show independent session and cursor state |
| HLS-6 Concurrency | reader/writer and writer/writer cases have defined outcomes |
| HLS-7 Recovery | forced termination and host restart recover without silent damage |
| HLS-8 Private remote | authenticated private access works without public ingress |
| HLS-9 Read-only public | bounded HTTPS demonstration exposes no mutation surface |
| HLS-10 Decision | measured requirements produce a documented hosting recommendation |

No later gate implies that an earlier failed gate may be ignored.

## Initial Deliverables

```text
headless-server-project/
  README.md
  BUILD_LINUX.md
  DEPLOYMENT_LAYOUT.md
  SERVICE_CONTRACT.md
  API_CONTRACT.md
  SECURITY_CROSSWALK.md
  SESSION_ISOLATION.md
  STORAGE_CONCURRENCY_TEST_PLAN.md
  RECOVERY_RUNBOOK.md
  HOSTING_DECISION_REPORT.md
  scripts/
    build-linux.*
    install-test-server.*
    run-smoke.*
  tests/
    hosting_smoke.dts
    concurrency/
    recovery/
```

These names describe the expected project packet. Their final repository
locations must be selected during local contract preflight so they align with the
current source layout rather than creating a disconnected deployment subsystem.

## Acceptance Criteria

The project is ready for a hosting decision when:

- the current x64base source has a reproducible native Linux build;
- the deployment package starts without dependence on the development tree;
- the service operates under an unprivileged account;
- read-only API operations are bounded and deterministic;
- concurrent requests do not leak cursor, work-area, relation, variable,
  transaction, or authorization state;
- DBF, CDX, memo, and LMDB behavior is recorded under reader/writer tests;
- crash and restart behavior is proven on disposable data;
- remote private access is authenticated and audited;
- any public demonstration remains read-only and can be disabled immediately;
- measured results support a documented home-hosting versus VPS decision;
- no unsupported claim of production readiness is made.

## Excluded Scope

- exposing the interactive shell directly to the Internet;
- using the authoritative development or publication-staging data roots;
- production personal-data hosting;
- embedding credentials or private network details in the public repository;
- bypassing `USERS`, team-member, role, permission, authorization, or security
  policy decisions;
- declaring shared hosting, home hosting, or VPS hosting suitable before proof;
- redesigning unrelated engine, GUI, HELP, metadata, or website subsystems.

## Risks Requiring Explicit Review

- implicit global state in CLI or engine surfaces used by concurrent requests;
- LMDB environment and process/thread assumptions;
- DBF/CDX locking behavior across processes and abnormal termination;
- memo-store partial writes and recovery;
- command surfaces that can reach host commands or arbitrary paths;
- reverse-proxy trust headers and client-identity propagation;
- home-router exposure, changing public IP addresses, ISP restrictions, power
  loss, and limited upstream bandwidth;
- divergence between WSL success and native Linux service behavior.

## First Implementation Milestone

The smallest useful first milestone is deliberately local and read-only:

1. refresh the WSL build and record drift;
2. build natively on the headless Linux host;
3. run a deterministic `hosting_smoke.dts` from a deployment directory;
4. start a supervised service exposing only `/status`, `/version`, and `/tables`;
5. call it from another device on the local network;
6. stop, restart, and reboot the host;
7. publish the proof transcript and unresolved defects to the AI Portal.

This milestone does not require public DNS, router changes, a tunnel, mutation,
or production credentials.

## Next Gate

Derald selects or prepares the headless machine and authorizes the implementation
lane against the current `D:\code\ccode` workspace. The implementing AI performs
the AI Portal startup reads and source-mutation contract preflight, then returns a
concrete file plan before modifying source, build, deployment, or maintained data.
