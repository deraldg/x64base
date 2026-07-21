# AI Dev-Tools Security Doctrine V1

**Status:** active doctrine — published to the AI Portal.
**Scope:** how AI (and human) agents may use the AI-friendly developer tools in this repo,
the threat model behind them, and the controls that bound the risk.
**Freshness:** 2026-07-21.

---

## 0. Permission protocol (read this first)

DotTalk++ deliberately ships **AI-friendly dev-tools** — capabilities designed so an AI
agent can extend and exercise the engine (see §2). Because those capabilities are real,
their use carries a standing rule:

> **Any agent — AI or human — must obtain *limited*, scoped permission before using the
> AI-friendly dev-tools. This requirement is global. The project owner (Derald Grimwood)
> is the sole exemption.**

"Limited permission" means least-privilege and purpose-scoped: ask for the specific tool
and the specific task, not blanket access. Permission is granted by the owner.

This rule is currently enforced **socially and by review** — the technical gate exists but
is shipped **dormant** (§4.5), so nothing is blocked today. Publishing the tools does not
publish an open door: it publishes an invitation to *ask*.

---

## 1. Why this doctrine exists

An agent with write access to the source tree can create a new command or function file
that becomes a real, compiled, persistent engine capability. An agent that can also compile
and run closes the loop with no human in it. That is powerful and useful — and it is exactly
the surface that must be governed rather than trusted blindly. This doctrine names the
surface honestly and states the controls.

---

## 2. What the AI-friendly dev-tools are

- **Runtime DEF family** — `DEFCMD` / `UNDEFCMD` (commands) and `DEFFN` / `UNDEFFN`
  (expression functions). Mint *session-only* commands/functions at runtime with no rebuild.
  Today their bodies are **inert** (echo text / return text); they cannot execute engine or
  host operations. See `RUNTIME_DEF_FAMILY_LANE_V1.md`.
- **`EXAMPLE`** — the minimal reference built-in / token-routing testbed.
- **The write→compile→run→read-output loop** — an agent (e.g. CODEX) authoring source,
  building `dottalkpp`, piping a DotScript into it at launch, and reading the output files.
  The most capable and the most sensitive surface.

---

## 3. Threat model

1. **AI-authored source auto-arms on build.** `src/CMakeLists.txt` glob-recurses `src/**`,
   so a new `cmd_*.cpp` / `fn_*.cpp` is compiled into the next build with no explicit CMake
   edit. **Self-registering** commands/functions (static-initializer `register_extension_command`)
   activate on build with no registration edit at all. A dropped file can become a live
   capability with no distinct, reviewable "wiring" step.
2. **Loop-closing agents remove the human build gate.** The strongest technical control —
   "nothing builds or runs until a human invokes it" — is precisely what an autonomous
   write→compile→run loop automates away. Speed and risk are the same property.
3. **Future executable DEF bodies.** Today DEF bodies are inert text. If/when bodies become
   executable (DotScript / formula), a scratch def inherits whatever the interpreter can
   reach — including destructive verbs (`ZAP`/`DELETE`/`ERASE`), file writes (`WEB FETCH`),
   and attempts at host shell (`!`). This is a gated milestone, not a default.
4. **Confusion / trust attacks.** Defining misleadingly-named commands, or shadowing
   non-protected extensions. Partly mitigated (protected names can't be shadowed; can't
   clobber existing non-scratch entries), bounded by session-only scope.

---

## 4. Controls

### 4.1 Human build gate
Nothing an agent authors builds or runs until a human invokes the build — unless a
loop-closing agent is used (§4.6).

### 4.2 Git as tripwire
Every change is visible in `git status` / `git diff`. Watch specifically for new/edited
`cmd_*` / `fn_*` / `src/ext/**` / self-registering source. Nothing force-pushed. AI work
stays on the dev branch.

### 4.3 Gated promotion
Dev branch → `C:\x64base/main` promotion is a human-reviewed checkpoint (copy → rebuild →
full green → commit → push). This is where a human reads what any fast loop produced before
it ships. Keep AI work off `main`/staging until reviewed here.

### 4.4 Host-shell block (independent)
Host command execution is off by default (`DOTTALK_ALLOW_HOST_COMMANDS`). This holds against
a *compiled* binary too, so even a maliciously-authored command cannot shell out unless the
owner has enabled host commands.

### 4.5 Dormant permission gate
`include/cli/ai_devtools_policy.hpp` — `devtools_permitted()` is the single chokepoint for the
§0 protocol. **Shipped dormant (permits by default).** Owner may activate without a rebuild:
`DOTTALK_DEVTOOLS_REQUIRE_PERMISSION=1` turns enforcement on; `DOTTALK_DEVTOOLS_GRANT=1`
supplies a scoped grant. Wired into `DEFCMD`/`DEFFN`. Left dormant intentionally so publishing
the tools does not block anyone today.

### 4.6 Isolation for loop-closing agents
An agent that compiles and runs autonomously (CODEX) should point that loop at an
**isolated / scratch tree or clone**, keep `DOTTALK_ALLOW_HOST_COMMANDS` off inside it, and
never force-push. Its output reaches the authoritative tree only through §4.2 + §4.3.

---

## 5. CODEX (a loop-closing agent) — folded in, not gated

CODEX authors source, compiles `dottalkpp`, feeds DotScript via stdin at launch, and reads
output files — a smooth autonomous loop. **By owner decision it is not gated**; it remains a
trusted iteration tool. It is bounded not by a hard block but by the review controls above:
git visibility (§4.2), the promotion gate (§4.3), the independent host-shell block (§4.4), and
isolation of its build/run loop (§4.6). The DEF-family gate (§4.5) is dormant, so CODEX (like
everyone) is unblocked today; the §0 protocol remains the stated expectation.

Division of labor worth noting: an agent that *cannot* autonomously execute is the safer one
to hand authoring, careful edits, review, and governance; an agent that *can* is the fast
iteration loop, run against isolated trees with a human gate before promotion. Running both
with clear roles is a deliberate posture, not a compromise.

---

## 6. Owner exemption

The project owner (Derald Grimwood) is exempt from the §0 permission requirement. All other
agents — AI or human — are expected to ask for limited, scoped permission. The dormant gate
(§4.5) can make that expectation technically enforced whenever the owner chooses; until then
it is honor-system plus the review gates.
