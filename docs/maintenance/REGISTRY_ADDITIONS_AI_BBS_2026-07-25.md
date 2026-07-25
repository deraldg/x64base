# REGISTRY_ADDITIONS -- AI-BBS lane (built + runtime-observed + M6), 2026-07-25

Review-needed additions to the maintained SelfDoc/MDO registries, for merge after the
source-mutation preflight. Supersedes the M5 package's `REGISTRY_ADDITIONS.md`: the M1-M4 gates are
now **runtime-observed** (not `source_defined`), and M6 + `board.lounge` are added.

## 1. `labtalk/registries/ai_runs.yaml` -- append RUN row

```yaml
  - run_id: AIPR-20260725-001
    member: member.ai.claude.cowork
    product: Cowork
    project: project.ai_friendly
    lanes: [AIF-052, AIF-053, AIF-054]        # BBS agent-server + NET egress-security + M6/Lounge
    role: implementer
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
    git: { branch: development, baseline: dfa8c1366, head: dfa8c1366 }
    chat_handle: ""
    handle_binding: MAINTAINER_ATTESTED
    continues_run: AIPR-20260724-010
    started: 2026-07-25
    closeouts:
      - docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    status: active
```

Update `current_by_lane:`:

```yaml
  AIF-052: AIPR-20260725-001
  AIF-053: AIPR-20260725-001
  AIF-054: AIPR-20260725-001
```

## 2. `labtalk/registries/proofs.yaml` -- update/append proof rows

The M1-M4 rows advance to `runtime_observed` (observed 2026-07-25; see the closeout Evidence table).
M6 is new.

```yaml
  - id: proof.bbs.m1_board
    label: AI-BBS M1 board tables + BBS command
    state: runtime_observed
    source: docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    notes: BBS BOARDS created SYSBOARD/THREAD/POST.dbf; POST/READ round-trip; board.governance projects SYSGRANT.
  - id: proof.bbs.m2_net_egress
    label: AI-BBS M2 NET EGRESS permissioned toggle
    state: runtime_observed
    source: docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    notes: AI member refused NET EGRESS OPEN ("no in-scope role permission"); owner STATUS = Block.
  - id: proof.bbs.m3_argon2
    label: AI-BBS M3 Argon2id token crypto (libsodium)
    state: runtime_observed
    source: docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    notes: USER TOKEN -> 43-char base64url CSPRNG; correct token logs in, wrong token rejected. Gates M4.
  - id: proof.bbs.m4_serve
    label: AI-BBS M4 BBS SERVE loopback listener + Ollama bridge
    state: runtime_observed
    source: docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md
    notes: 127.0.0.1:8765 LISTENING (loopback only); AUTH OK; CHAT haiku from isolated Ollama while egress=Block; OK posted.
  - id: proof.bbs.m6_daemon
    label: AI-BBS M6 standalone dottalk_bbsd daemon
    state: runtime_observed
    source: docs/maintenance/AI_BBS_M6_STANDALONE_DAEMON_V1.md
    notes: Own binary; headless via DotTalkBBSD task (SYSTEM/session 0); AUTH/CHAT/POST across restarts; loopback-only; SO_EXCLUSIVEADDRUSE. Cross-platform SIGPIPE guard.
  - id: proof.bbs.guest
    label: AI-BBS guest leave-a-message (member.guest + board.guestbook)
    state: runtime_observed
    source: docs/ai-friendly/AI_BBS_LOUNGE_ROOM_V1.md
    notes: As member.guest -> POST board.guestbook OK posted; POST board.lounge bbs.post denied; READ bbs.read denied (write-only). Per-board POSTPERM (bbs.guest) enforced; BBS writes take table FLOCK.
```

## 3. `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` -- append rows (next ids after AIF-051)

```
| AIF-052 | AI-BBS agent-server lane (M1/M4) built + runtime-observed, Cowork 2026-07-25 | feature, server, agent_interaction, source_change, runtime_observed | `bbs/*`, `cmd_bbs.cpp`, `docs/ai-friendly/AI_BBS_LANE_V1.md`, manual command-ref (auto-harvest on `supported`) | `docs/ai-friendly/AI_BBS_LANE_V1.md`; `docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` | runtime-observed | Board + BBS SERVE (loopback, token auth, Ollama bridge). Wired into dottalkpp; gates green. Not promoted/committed. |
| AIF-053 | NET egress-security + M3 Argon2id token crypto built + runtime-observed, Cowork 2026-07-25 | security, rbac, crypto, source_change, runtime_observed | `cmd_net.cpp`, `security/token_crypto.*`, `identity_bootstrap.cpp` (perms + member.ai.grok.xai) | `docs/maintenance/SESSION_CLOSEOUT_AI_BBS_LANE_BUILD_GREEN_2026-07-25.md` | runtime-observed | host.network.egress (owner-only) refused to AI member; Argon2id/libsodium tokens round-trip. M3 gates M4. |
| AIF-054 | AI-BBS M6 standalone daemon + The Lounge room, Cowork 2026-07-25 | feature, server, daemon, cross_platform, source_change, runtime_observed | `src/tools/bbsd_main.cpp`, `bbs_server.cpp` (SIGPIPE), `bbs_store.cpp` (board.lounge + top-up), `CMakeLists.txt` (dottalk_bbsd), `D:\code\*bbsd*.ps1` | `docs/maintenance/AI_BBS_M6_STANDALONE_DAEMON_V1.md`; `docs/ai-friendly/AI_BBS_LOUNGE_ROOM_V1.md` | runtime-observed | Standalone `dottalk_bbsd`, boot-managed (DotTalkBBSD task); `board.lounge` (owner + AI partners), idempotent top-up. xindex.lib gap worked around via src/cdx; core-lib refactor owed. |
```

## 4. `@dottalk.usage` status flip (the auto-publish step)

Gates are green, so the `BBS` and `NET` command contracts may flip `status: experimental` ->
`supported`. On the next `metacollect` run this auto-harvests them into HELP/META ->
`command_reference_candidate.py` -> the `spine-command-reference` manual part. **No manifest edit.**

- `src/cli/cmd_bbs.cpp` -- `@dottalk.usage` for `BBS BOARDS|READ|POST|REPLY|CLOSE|SERVE`.
- `src/cli/cmd_net.cpp` -- `@dottalk.usage` for `NET EGRESS STATUS|OPEN|CLOSE`.

Do the flip only when committing the lane; it is the moment these commands become publicly documented.

## 5. Transcript promotion (runtime intake -> proof registry)

The M5 `event_record` recorder writes runtime transcripts to `data/metadata/bbs/proofs/*.txt`. For
each real run, copy into `labtalk/proofs/runs/` (keep the `YYYYMMDD_HHMMSS_<kind>_<slug>.txt` name)
and point the matching `proof.bbs.*` row's `source:` at the copied file. The PowerShell client
transcripts from 2026-07-25 (AUTH/CHAT/POST against `dottalk_bbsd`) are the evidence behind the
`runtime_observed` rows above.
