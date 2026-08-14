# Arctic Fox Batch (AFB) -- Launch Instructions

Local, private Ollama on WSL2 behind a Hyper-V egress block. Isolation ceiling:
**verified revocable egress isolation** (not an air-gap -- loopback + DNS still work,
the block is host-toggleable).

---

## Daily launch (isolation already configured)

Open WSL, then:
```bash
# 1. Ensure the WSL Ollama server is up and localhost-bound
systemctl is-active ollama || sudo systemctl start ollama
ss -tlnp | grep 11434                 # expect: 127.0.0.1:11434  (linux ollama pid)

# 2. Confirm isolation is ON (it persists across sessions)
curl -s --max-time 3 http://127.0.0.1:11434/api/version    # answers (loopback ok)
curl --connect-timeout 5 -s -o /dev/null https://github.com && echo OPEN || echo BLOCKED   # expect: BLOCKED

# 3. Use the coder model
ollama run qwen2.5-coder:7b                                  # interactive
ollama run qwen2.5-coder:7b "review this function: <paste>"  # one-shot
# or via API:
curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen2.5-coder:7b","prompt":"...","stream":false}'
```
Available models: `ollama list` (qwen2.5-coder:7b, llama3, mistral).

---

## After a Windows reboot / `wsl --shutdown` -- verify the guards held

```bash
# WSL: server back up and localhost-only?
systemctl is-active ollama && ss -tlnp | grep 11434
```
```powershell
# Windows (admin PS): block still set?
$w='{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'
(Get-NetFirewallHyperVVMSetting -Name $w).DefaultOutboundAction    # expect: Block
```
Persistence checklist:
- `.wslconfig` `[wsl2]` has `networkingMode=mirrored` and `firewall=true`.
- Hyper-V `DefaultOutboundAction = Block`.
- **Windows Ollama startup is DISABLED** (Settings -> Apps -> Startup). If it autostarts it grabs port 11434 on the shared loopback and the WSL server can't bind.

---

## Pull a new model (opens a brief, logged egress window)

```bash
bash /mnt/d/code/pull-with-window.sh llama3.1:8b     # default arg: qwen2.5-coder:7b
```
Fires two UAC prompts (Allow -> pull -> Block), then confirms re-isolation. Log lands in `_artifacts/pull_window_<ts>.txt`.

---

## Re-verify isolation (fresh proof artifact)

```bash
bash /mnt/d/code/verify_egress.sh
```
Checks internet blocked (multi-host, DNS-bypassed), Ollama localhost bind, and the Hyper-V setting; writes proof to `/mnt/c/Users/deral/code/_artifacts/`. Run the [B] toggle it prints to re-earn `runtime-evidenced`.

---

## Manual egress toggle (if scripting isn't handy)

```powershell
$w='{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'
Set-NetFirewallHyperVVMSetting -Name $w -DefaultOutboundAction Allow   # open (for pulls/updates)
Set-NetFirewallHyperVVMSetting -Name $w -DefaultOutboundAction Block   # closed (normal operation)
```

---

## Companion: GPTbase (hosted) -- the other half of the split

- Launch: `chatgpt.com` -> **GPTs** -> **GPTbase** (or the share link).
- Use it for design/review and web-aware research; it's change-package-bound and can't touch your repo directly.
- **Division of labor:** GPTbase = hosted, advisory, web-aware. AFB = local, private, offline. Send anything you wouldn't want leaving the machine to AFB.

---

## Registry

Registered as `app.labtalk.afb` in `labtalk/registries/apps.yaml`; audited closeout at
`docs/maintenance/SESSION_CLOSEOUT_AFB_OLLAMA_APP_REGISTRATION_2026-07-23.md`.
