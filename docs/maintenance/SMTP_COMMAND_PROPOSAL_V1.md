---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260817-COWORK-005
  recorded_at_utc: 2026-08-18T00:40:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: a5105491f
  authorization:
    requested_by: maintainer (member.derald), in-session, "give me smtp functionality, sftp might help with prior art as a template" / "so go for it"
    scope: >
      Proposes an SMTP command that wraps the existing tools/notify/smtp_probe.py
      behind the established external-process and identity gates. Resolves the
      capability question against the permission catalog. Proposal only; no code
      written, nothing built.
  report:
    path: docs/maintenance/SMTP_COMMAND_PROPOSAL_V1.md
    kind: proposal
---

# SMTP command -- proposal

Status: proposal, review-needed. Owner: member.derald.
Author: member.ai.claude.cowork. Date: 2026-08-17.
Trigger: `src/cli/cmd_smtp.cpp` exists as a 0-byte untracked stub, created
2026-08-17 12:13 as a placeholder for this request.
Prior art: `src/cli/cmd_sftp.cpp`, `tools/notify/smtp_probe.py`.

## Most of this already exists

`tools/notify/smtp_probe.py` (2,622 B, 2026-08-12) is a working SMTP sender:

- `--probe` login only, `--send SUBJECT` with the body from stdin, `--debug`
  for the full wire trace to stderr
- `SMTP_USER` / `SMTP_PASS` required; `SMTP_HOST` default `smtp.gmail.com`,
  `SMTP_PORT` default `587`, STARTTLS via `ssl.create_default_context()`
- distinct exit codes: 0 ok, 2 no credentials, 3 auth failed, 4 other
- **credentials arrive by environment from a thin platform wrapper** -- DPAPI
  clixml on Windows, chmod-600 env file on POSIX -- and the script "never stores
  or logs the password"
- Python 3 stdlib only, per the **AIF-085** tooling rule; it explicitly replaced
  a PowerShell/.NET probe that violated that rule "and could not show the
  conversation"

So transport, TLS, credential handling, defaults and error reporting are already
decided and working. **What is missing is only the command surface.**

## Shape: wrap, do not reimplement

`SFTP` is the template and it does not implement SFTP. Its own contract says it
"stages a temporary sftp batch file and invokes the system sftp client", with
`effect: network-or-file` and the stance "Do not store passwords."

`SMTP` should wrap `tools/notify/smtp_probe.py` the same way. Implementing SMTP
in C++ would mean new protocol code, a new TLS dependency, and a second
credential path competing with a working one -- for a command whose entire job
is to hand three strings to a mail server.

This is the maintainer's own stopping rule from AIF-119 applied one level out:
if the in-process version gets complicated, shell out to the thing that already
works.

## The gates are already built

Two, both shared with existing commands:

1. **External-process policy.** `include/cli/external_process_policy.hpp`
   provides `authorize_external_process(operation, requires_network)`, used by
   `cmd_bang.cpp`, `cmd_net.cpp` and `cmd_sftp.cpp`. It requires
   `DOTTALK_ALLOW_HOST_COMMANDS=1` and `DOTTALK_ALLOW_NETWORK=1` and prints
   which one is missing.
2. **Identity capability.** `dottalk::identity::agent_permitted(<key>)`,
   AIF-045 2d-3, refusing by acting member key.

## Which capability -- resolved, and the answer is `host.shell`

The question was whether sending mail deserves its own permission. Measured
against `src/identity/identity_bootstrap.cpp`:

| id | key | risk | approval | granted to |
| --- | --- | --- | --- | --- |
| 14 | `host.shell` | Critical | yes | MAINTAINER |
| 15 | `host.network.egress` | Critical | yes | MAINTAINER, explicitly **NOT** AI_PARTNER |

`host.network.egress` is NOT a per-command "this uses the network" check. Its
only consumer is `cmd_net.cpp` (`kPerm` at :80), where `NET EGRESS OPEN/CLOSE`
toggles WSL/AFB outbound isolation at the MACHINE level. Network reachability is
therefore already governed independently of any command.

`host.shell` has exactly two check sites: `cmd_bang.cpp:109` and
`cmd_sftp.cpp:514`. Both launch processes.

**A separate `net.mail` permission would buy nothing.** Anyone holding
`host.shell` can already run `python tools/notify/smtp_probe.py --send ...`
directly through `!`. Adding an SMTP command does not widen the attack surface;
it makes an existing capability ergonomic. Inventing a permission that the shell
escape trivially bypasses is the appearance of control rather than control --
and it would need a gate proving `!` cannot reach the same script, which nothing
currently provides.

**Therefore: check `host.shell`, exactly as SFTP does.** If mail should ever be
grantable separately, the prerequisite is restricting the shell escape first;
that is a different lane and should be argued on its own terms.

## Proposed surface

```text
SMTP USAGE
SMTP PROBE                      login only; report OK / AUTH FAILED / FAILED
SMTP SEND <subject>             body from the following lines, or from a file
SMTP SEND <subject> FROM <file>
SMTP STATUS                     report configured host/port/user, never the password
```

Mirrors SFTP's verb style (`SFTP LS/GET/PUT`), keeps `USAGE` as the no-args
behaviour, and `STATUS` gives a safe way to answer "is mail configured" without
attempting a login.

Contract block to carry, following `cmd_sftp.cpp`:

```text
category: network
effect:   network
mutates:  nothing-local
risk:
  network_access: PROBE SEND
  launches_external_process: python + tools/notify/smtp_probe.py
  sends_outbound_mail: SEND
  mutates_table_data: no
  stores_credentials: no
related: SFTP, NET, PSHELL
```

## One real gap in the Python side

`smtp_probe.py` **can only send to itself** -- `msg["To"] = user`. It is a probe,
and for a probe that is correct. A usable `SMTP SEND` needs a recipient, so the
script needs a `--to` argument (defaulting to `SMTP_USER` to preserve current
behaviour). That is the only code change required outside the new command, and
it should stay stdlib-only per AIF-085.

Worth deciding at the same time: whether `SEND` refuses recipients outside an
allow-list. Sending mail is outbound and irreversible, and the console's
preview-only posture is the house instinct for exactly this class of action.

## What is NOT proposed

- No SMTP protocol implementation in C++.
- No credential storage, prompting, or reading of the DPAPI blob from the CLI.
  The platform wrapper owns that and the command must not learn it.
- No attachment support in v1. Body text only; attachments can follow if wanted.
- No new permission. See above.
- No use of `--debug` from the command: it prints the base64 AUTH exchange to
  stderr, and a CLI that can be scripted into a log file must not offer that as
  a flag.

## Verification plan

The command cannot be built or run in the Linux sandbox, so this is maintainer-
operated:

1. `SMTP USAGE` with no credentials set -- prints usage, attempts nothing.
2. `SMTP PROBE` with the gates unset -- refused by
   `authorize_external_process`, naming the missing variable.
3. `SMTP PROBE` as a member without `host.shell` -- refused by acting member key.
4. `SMTP PROBE` with gates and credentials -- `LOGIN: OK`.
5. `SMTP SEND` to self -- arrives, and the password appears in no output or log.
6. Mutation arm: wrong `SMTP_PASS` -- surfaces exit 3 as an auth failure rather
   than a generic failure, so the distinct exit codes are proven to reach the
   caller.

Arm 6 matters most. `smtp_probe.py` already distinguishes auth failure from
every other failure, and a wrapper that collapses both into "SMTP failed" would
discard a diagnosis the tool already made -- the shape recorded repeatedly in
this repository's proofs.
