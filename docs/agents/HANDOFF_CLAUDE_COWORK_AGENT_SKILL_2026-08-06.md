# Handoff -- x64base agent skill lane (AIF-090)

    from        : member.ai.claude.cowork, 2026-08-06
    for         : whoever picks up AIF-090
    lane        : docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md
    posture     : charter opened, nothing built. The next gate is a GO/NO-GO.

This records **how to work in this lane**, not what happened. The closeout has
what happened.

---

## 1. Do not start at P1

`P0` is a go/no-go and it is first for a reason. The lane's premise is that cold
agents do not reliably reach Tier 1 on their own. That premise is **argued, not
measured**. If it turns out they do, this lane is packaging polish and should
defer behind whatever the owner names instead.

Measure before spending: bytes read before first correct action, whether
`recall.py` ran unprompted, whether a sandboxed agent took a lock-taking git.
Charter section 4, G0.

## 2. The one rule that kills this lane if you break it

The skill must contain **no doctrine of its own**. It is a generated loader and
trigger router. `AI_TIER1_SEED_V1.md:155` binds vendor shims to point rather
than restate, and this is a fourth shim after `CLAUDE.md`, `AGENTS.md` and
`.github/copilot-instructions.md` -- the most dangerous one, because it loads
with full authority and no retrieval friction.

If you find yourself writing a paragraph that explains the mutation guard, stop.
That paragraph already exists. Emit a pointer.

## 3. What is already built -- consume it, do not rebuild it

Measure these yourself rather than trusting this file; the commands are cheap.

- `labtalk/ai_portal/recall.py` -- stdlib only, runs in a bare sandbox.
  `--validate` reports the graph and passes. `recall.py <trigger>` returns a
  bounded working set and prints it as a percentage of the entry-path baseline.
- `labtalk/registries/portal_recall_graph.yaml` -- the typed graph. Triggers,
  nodes, edges. The `enforced_by` edge is what makes the decay rule computable.
- `labtalk/ai_portal/generate_tier0_state.py` -- generated state. Also wired
  into `.git/hooks/pre-commit`, which regenerates and stages `TIER0_STATE.md` on
  every commit. That is why your slices will show one extra path. It is correct;
  do not fight it.
- `tools/staging/prepush_gate.py` -- the gate host. Read how it invokes the
  portal checks before adding another.

## 4. Practical things that cost this session time

**`git status --short` is the wrong safety check on this tree.** It emits 800+
`??` lines and buries the signal. A placeholder command failed silently and went
unnoticed through two rounds because of it. Use:

```
git diff --cached --name-only
```

`AI_TIER1_SEED_V1.md:51` currently teaches the `git status --short` version.
That guidance is right in principle and does not scale to this working tree.

**PowerShell is not bash.** Multi-line commands handed to the maintainer must
use PowerShell arrays, not `\` continuations. A `\`-continued `git add` produces
`ParserError: The '<' operator is reserved for future use` or worse, silently
stages nothing.

**`check_house_style.py` blocks ADDED lines, and every line of a
previously-untracked file is added.** So an untracked document carrying
non-ASCII cannot be committed until it is normalized. `tools/staging/ascii_normalize.py`
exists now for exactly this; run `--table` to see the mapping and `--apply` to
fix. It refuses to write when it meets a codepoint it does not know.

**Test the tool before trusting it.** The normalizer above failed its own first
two fixtures: `Path.read_text(newline=...)` is 3.13+ while the host targets
3.12, and an unspaced alphabetic replacement fused two tokens. Both would have
shipped silently and both were found by throwaway fixtures, not by review.

## 5. Sandbox posture

If you are in a mounted sandbox rather than on the host: read freely, run no git
that takes `.git/index.lock`. Read-only is lock-free and allowed --
`git --no-optional-locks status`, `log`, `ls-files`, `check-ignore`, `cat-file`.
`claim-aif` shells out to `git grep`, so it stays host-side; more importantly its
`git_committed_aifs()` swallows failures and returns an empty set, so a claim
made where git cannot run will under-report what is taken and can collide.

Verify your own environment rather than citing this file: `ldd --version`,
`command -v cmake ninja`, `python3 -V`.

## 6. Open rulings that block phases

Charter section 5 carries these. They are the owner's, not yours to assume:
which repo ships the bundle, whether `.claude/skills/` projections are tracked
or regenerated per clone, and licensing for a package handed to an outside
agency.
