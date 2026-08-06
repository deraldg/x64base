# AI BBS M4.2 -- reviewable patch spec (v1)

Status: **patch spec, NOT applied to source.** Edit 5 (seed rows) is mechanical and
ready to apply; Edit 7 (harness) is a **reference skeleton to review, wire, and
prove**. Gated on M4.1 being landed and proven first. Owner: `member.derald`.
Design: `AI_BBS_M4_2_OLLAMA_AGENT_HARNESS_DESIGN_V1.md`. Runsheet:
`AI_BBS_M4X_BUILD_RUNSHEET_V1.md`. Complete the mutation preflight; scoped commit.

---

## Edit 5 -- `src/identity/identity_bootstrap.cpp` seed rows -- APPLY AS-IS

Add the Ollama service user (next free user id **9**) and member (next free member
id **7**), mirroring the existing AI partners exactly. No new permission: role
`AI_PARTNER` already grants `bbs.read/post` + `chat.invoke` and denies
`source.mutate` + `host.network.egress`.

User -- add after `U_GUEST` (S105):
BEFORE:
```
    const UserId U_GUEST     = U(8, "user.guest",            "guest",  "Guest",           "", AuthKind::Token);
```
AFTER:
```
    const UserId U_GUEST     = U(8, "user.guest",            "guest",  "Guest",           "", AuthKind::Token);
    const UserId U_AI_OLLAMA = U(9, "user.ai.ollama.local",  "ollama", "Ollama (local)",  "", AuthKind::Token);
```
Member -- add after the guest member (S120):
BEFORE:
```
    (void)                        M(6, "member.guest",            MemberKind::External, U_GUEST,  GUEST);        // AIF-055 leave-a-message
```
AFTER:
```
    (void)                        M(6, "member.guest",            MemberKind::External, U_GUEST,  GUEST);        // AIF-055 leave-a-message
    (void)                        M(7, "member.ai.ollama.local",  MemberKind::AI,    U_AI_OLLAMA, AI_PARTNER);   // M4.2 Ollama-as-agent
```
Proof: seed reload -> `USER LIST` shows `member.ai.ollama.local` (kind AI, role
`ai_partner`). No permission row is added -- verify `agent_permitted` denies
`source.mutate` for it.

---

## Edit 6 -- credential -- RUNTIME, not code

The owner mints its token once (same path as the other AI members):
```
USER TOKEN member.ai.ollama.local
```
The token is owner-issued at runtime and **never committed**. The harness receives
it via environment (`DOTTALK_OLLAMA_TOKEN`), never as a literal.

---

## Edit 7 -- harness -- REFERENCE SKELETON (review, wire, prove)

Ruling A (harness home) is open; this is the **script-client** option, which needs
zero server change -- it speaks the existing AUTH/READ/CHAT/POST line protocol.
Ruling B trigger is the recommended **owner-poked single turn**: one read ->
model -> post per invocation, no standing loop. Save as e.g.
`tools/bbs/ollama_agent_harness.py` (path per Ruling A).

Protocol framing (from `bbs_server.cpp`): requests are `\r\n`-terminated lines;
each response is data lines ended by a lone `.` line.

```python
#!/usr/bin/env python3
"""M4.2 Ollama-agent harness (reference skeleton). One owner-poked turn:
AUTH as member.ai.ollama.local -> BBS READ <board> -> CHAT -> BBS POST.
Token from env DOTTALK_OLLAMA_TOKEN (never hardcoded). Loopback only."""
import os, socket, sys

HOST, PORT = "127.0.0.1", 8765
MEMBER = "member.ai.ollama.local"

def _recv_until_dot(f):
    lines = []
    for line in f:
        line = line.rstrip("\r\n")
        if line == ".":
            break
        lines.append(line)
    return lines

def turn(board, subject):
    token = os.environ.get("DOTTALK_OLLAMA_TOKEN")
    if not token:
        sys.exit("set DOTTALK_OLLAMA_TOKEN (owner: USER TOKEN member.ai.ollama.local)")
    with socket.create_connection((HOST, PORT)) as s:
        f = s.makefile("r", encoding="utf-8", newline="")
        def send(msg): s.sendall((msg + "\r\n").encode("utf-8"))
        # 1) AUTH
        send(f"AUTH {MEMBER} {token}")
        auth = _recv_until_dot(f)
        if not auth or not auth[0].startswith("OK"):
            sys.exit(f"auth failed: {auth}")
        # 2) READ the board for context (bbs.read)
        send(f"BBS READ {board}")
        context = _recv_until_dot(f)[1:]   # drop the leading OK
        # 3) CHAT: invoke the model under this member's own chat.invoke
        prompt = "You are the local project assistant. Given this board:\n" + \
                 "\n".join(context) + "\nWrite one concise, useful reply."
        send("CHAT " + prompt.replace("\n", " "))
        reply = _recv_until_dot(f)
        if reply and reply[0].startswith("OK"):
            reply = reply[1:]
        body = " ".join(reply).strip() or "(no model output)"
        # 4) POST as ourselves (bbs.post) -- attribution is member.ai.ollama.local
        send(f"BBS POST {board} {subject} :: {body}")
        posted = _recv_until_dot(f)
        send("QUIT")
        print("posted:", posted[0] if posted else "(no ack)")

if __name__ == "__main__":
    b = sys.argv[1] if len(sys.argv) > 1 else "board.afb.chat"
    subj = sys.argv[2] if len(sys.argv) > 2 else "ollama turn"
    turn(b, subj)
```

Review/prove points (do not assume):
- **Agency:** the resulting post's author is `member.ai.ollama.local`, not the
  owner, not author-zero.
- **Bound:** the harness never sends a command needing `source.mutate` or
  `host.network.egress`; if it tries, `agent_permitted` denies it.
- **Egress isolation:** run one turn with `NET EGRESS CLOSE` (DefaultOutboundAction
  Block); the turn completes (loopback to Ollama exempt), `NET EGRESS STATUS` reads
  Block.
- **Concurrency:** run alongside a human agent (needs M4.1); two distinct authors,
  no identity bleed.
- **CHAT prompt** newlines are flattened because `CHAT` reads to end-of-line; keep
  the prompt single-line or extend the protocol later.

---

## Apply / prove order (M4.2, after M4.1 is proven)

1. Edit 5 -> build -> seed reload -> `USER LIST` shows `member.ai.ollama.local`.
2. Edit 6 -> owner `USER TOKEN member.ai.ollama.local`.
3. Edit 7 -> wire per Ruling A/B -> run the four proofs above.
4. Scoped commit (seed row separate from harness). Harness token stays out of tree.
