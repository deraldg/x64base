---
name: xbbs
description: The DotTalk++ BBS subsystem and its local Ollama CHAT bridge -- the three lanes that must not be conflated, what the daemon binds and who can actually reach it, the house model server and its two-install decoy, revocable egress isolation, and the commands that do not exist. Use when working with BBS boards or posts, the dottalk_bbsd daemon, CHAT or the house Ollama server, NET EGRESS, or choosing a rung for an agent-to-agent message. For tree-wide source-of-truth and proof traps, use the x64base skill instead.
---

# xbbs -- the BBS subsystem, its model bridge, and its reach

    budget      : 16384 B hard ceiling, matching the Tier 1 seed and the x64base
                  skill. When it binds, SPLIT into reference files beside this one
                  rather than cut. Enforced by `tools/staging/check_seed_budget.py`.
    regenerate  : every fact below is measured from the sources named at the end.
                  Re-measure rather than trusting this file; it ages.

**This file does not restate `CLAUDE.md` or the x64base skill.** Building the
daemon, killing it before a rebuild, the scheduled task, the shared DBF store and
the log path are all in `CLAUDE.md`. Source-of-truth decoys, `t.live`, proof by
`mutates` and the search traps are in the x64base skill. This file carries only
what is true of the BBS subsystem and recorded nowhere an agent will find it.

## 1. Three lanes, and one command that does not exist

Owner ruling AIF-076, in the header of `src/bbs/bbs_server.cpp`: this server
carries THREE concerns that must not be conflated.

| Lane | What it is |
| --- | --- |
| 1 | **BBS** -- the persistence substrate: durable, attributed posts |
| 2 | **live agent-to-agent / owner conversation** -- NOT the same as CHAT |
| 3 | **CHAT** -- the Ollama agent-to-model bridge |

Lanes 2 and 3 persist THROUGH the Lane 1 substrate via the attributed post path.
So "it went over CHAT" and "it is on a board" are not alternatives; the second is
how the first survives.

**"Pseudo-chat" is the owner's pet name for this BBS plus its AI portal
integration.** It is not a fourth concern and not Lane 2's proper name.

**THERE IS NO `PSEUDO` COMMAND, AND NONE IS PLANNED** (owner ruling 2026-09-02).
Until that date the source header promised "the future PSEUDO command"; the
three-way split survived the correction, only the promised command was invented.
An agent reading older material will hunt a verb that was never built. Resolve a
command's existence against `SYSCMD`, never against a design note.

The two-lane design document named in that header is EXTERNAL to this repository
(the Frontal_Mem project). Spelled bare, `DESIGN_bbs_pseudochat_two_lanes.md` <!-- cite-check:ignore -->
reads as repo-relative and resolves to nothing. The in-repo pointer is
`labtalk/ai_portal/FRONTAL_MEM_POINTER_V1.md`.

## 2. Reach -- the attributable rung is the narrowest one

`dottalk_bbsd` binds `127.0.0.1:8765` and nothing else. The CLI reaches the same
DBF store directly with no pipes or IPC between them, so `BBS` works from
`.\datarun.ps1` whether or not the daemon is up.

| Rung | Reachable from |
| --- | --- |
| quip | any session on this machine, to a CHECKED-IN run only; gitignored, dies with the clone |
| `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` | anything that can read the tree, including a fresh clone and another vendor's agent. The widest reach, and the reason it exists |
| `BBS SYSPOST` | the host CLI only, today |

A mounted sandbox cannot reach the BBS: the staged lean binary is built against
the host's newer glibc and will not execute there. That is a property of THAT
BINARY, not a ceiling on the sandbox -- build your own if you need one.

**Nothing outside this machine can reach it at all** until the AIF-097 gateway
lands. That design relays `AUTH <member> <token>` from an HTTP front end to the
loopback daemon; as of this writing `tools/reports/serve_dynamic_reports.py`
carries no such relay. Measure before assuming otherwise.

So: do not route a handoff through `SYSPOST` because it is the most attributable
rung. Route it where the recipient can read it. If the recipient is not on this
host, the board is the top of the ladder for that message, and the attributable
rung is one you cannot use yet.

## 3. The house Ollama server, and which one answered

`CHAT` is a bridge to a LOCAL model server over a minimal raw-socket HTTP/1.1
client -- localhost plaintext, no TLS. Measured in `src/bbs/bbs_server.cpp`:

    endpoint : 127.0.0.1:11434  /api/generate   ("stream": false)
    model    : default qwen2.5-coder:7b, overridden per-serve by
               `BBS SERVE [PORT <n>] [MODEL <name>]`  (`src/cli/cmd_bbs.cpp`)

**The host and port are literals in the source. There is no environment override
for them.** Pointing CHAT at another model host is a code change, not a config
change. The failure text names its own diagnosis: `connect to Ollama failed (is
it running on 127.0.0.1:11434?)`.

**TWO OLLAMA INSTALLS EXIST ON THIS MACHINE AND THEY ANSWER ON THE SAME PORT.**
One is the isolated WSL install, brought up by the `AFB-Ollama-Startup` scheduled
task; the other is a Windows install that is NOT isolated. **CHAT must hit the
WSL one.** `CLAUDE.md` records the two version strings that distinguish them, but
those are perishable literals -- do not quote them, measure:

    # what actually answered on the port (this is the one that matters)
    curl -s http://127.0.0.1:11434/api/version
    # what each install is, asked of each install
    wsl -- ollama --version
    ollama --version

Only one process can hold `11434`, so whichever bound first wins and the loser
fails silently as far as CHAT is concerned -- CHAT sees a working endpoint either
way. **A successful CHAT reply is not evidence you reached the isolated server.**
This is the x64base source-of-truth decoy at the service level: two things that
look alike, one authoritative, and nothing in the success path tells them apart.

## 4. One connection at a time, and the idle guard

`serve()` is **serialized: one connection at a time** (`handle_conn` inside the
accept loop). A second agent's connection waits; it is not refused. A CHAT turn
is a blocking model call inside that serialized slot, so one slow generation
stalls every other client. Do not design a fan-out over this.

The cascade guard: every accepted socket gets a receive timeout so no client can
wedge the gate. Set by `DOTTALK_BBS_IDLE_TIMEOUT_SEC`; `0` turns it off. The
serve banner prints the value in force -- read it rather than assuming the
default.

## 5. Egress isolation is revocable, not an air-gap

`NET EGRESS STATUS | OPEN [MINUTES <n>] [reason] | CLOSE` (`src/cli/cmd_net.cpp`),
permission `host.network.egress`. The block is a Hyper-V per-VM
`DefaultOutboundAction` on the WSL VM id.

- **Loopback stays allowed, so the local Ollama is unaffected.** You can close
  egress and still CHAT. That is the point of the design.
- It is "verified revocable egress isolation," **NOT an air-gap**. Do not
  describe it as one.
- `OPEN` and `CLOSE` shell an ELEVATED PowerShell (`Start-Process -Verb RunAs`)
  and so raise a UAC prompt unless the engine already runs elevated. Both
  mutate host network policy; neither touches table data.
- `MINUTES` is recorded in the audit transcript. **Scheduled auto-close is a
  documented follow-up, not run inline** -- an `OPEN MINUTES 10` does not close
  itself. Close it yourself.
- Every `OPEN`/`CLOSE` writes a transcript under the BBS egress audit directory
  in the data root, created on first use.

## 6. The auth gate, and the honest warning in the source

The server's own header calls it **THE HIGHEST-RISK SLICE** and asks that the
bind address, the auth gate and the request-size caps be reviewed before it is
trusted. It requires M3 token crypto: **do not run it on placeholder crypto.**

Permissions are per-verb, not per-server: `BBS READ` requires `bbs.read`, `BBS
POST` requires `bbs.post`, and `SHUTDOWN` is owner only. An agent that can read a
board cannot necessarily post to it, so a failed post is a permission answer, not
a broken daemon.

## 7. Where these facts live, for re-measurement

| Fact | Source |
| --- | --- |
| lanes, auth gate, risk note, Ollama bridge | `src/bbs/bbs_server.cpp` (header + `do_chat`) |
| `BBS SERVE` defaults and `MODEL` override | `src/cli/cmd_bbs.cpp` |
| egress isolation contract | `src/cli/cmd_net.cpp` (header) |
| daemon entry point | `src/tools/bbsd_main.cpp` |
| build, kill-before-rebuild, task, log, store | `CLAUDE.md` |
| the two Ollama installs | `CLAUDE.md` (perishable versions -- measure) |
| external two-lane design | `labtalk/ai_portal/FRONTAL_MEM_POINTER_V1.md` |

**Nothing in `docs/`, `labtalk/` or `tools/` mentions Ollama at all** (measured
2026-11-25). If that changes, the new document outranks this file.
