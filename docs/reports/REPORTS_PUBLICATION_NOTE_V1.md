# Reports -- publication and exposure note V1

**Question asked (2026-07-25):** could these reports be viewable by others on the x64base.com
website, or vice versa -- public or private?

**Short answer:** two of the three are publishable after a review pass. **One must not be published
at all.** And the "vice versa" direction -- this machine reading the website -- is currently
**blocked by design** and should stay that way.

Sensitivity is recorded per item in `labtalk/registries/portal.yaml` (`portal.reports`).

---

## 1. Direction A -- publishing reports OUT to x64base.com

### `BBS_ACCESS_REPORT.html` -- **PRIVATE. Do not publish.**

This is an **authentication-surface map**. It contains no secrets, and that is exactly why it is
easy to publish by mistake. What it gives an outsider:

- **Valid member keys** -- `member.derald`, `member.ai.grok.xai`, `member.guest`, and the rest.
  These are not decorative; they are the literal first argument to `AUTH <member.key> <token>`.
  Publishing them hands over the username half of every credential pair.
- **Which identities hold a credential** -- the report marks "token set" vs "no token", i.e. exactly
  which accounts are live and worth attacking.
- **The full permission matrix** -- which role holds `git.push`, `source.mutate`,
  `host.network.egress`. That tells an attacker precisely which identity is worth compromising and
  what it would buy them.
- **The protocol and port** -- `127.0.0.1:8765`, the command grammar, the idle timeout.

None of that is dangerous *today*, because the listener is loopback-only and the token is a real
Argon2id secret. The exposure is **conditional**: it becomes valuable the moment the server is ever
reachable, even briefly, even by accident. Publishing it means that future misconfiguration comes
with a pre-written reconnaissance document.

The house rule already covers this -- **the token is the trust boundary** -- but defence in depth
means not publishing the map of the boundary either.

### `BBS_BOARDS_REPORT.html` -- internal; publishable only after content review

The structure (rooms, permissions, counts) is harmless and frankly a good demonstration. The
**post bodies** are the problem: this renders every post verbatim, and the worklog board is
specifically where agents drop **internal state** -- what is unfinished, what is risky, what the next
agent should pick up. Handoff post #6 currently names open work and risk in plain language.

Boards are not classified, but they were not written for an audience either. If this is published,
publish it **per board** (`board.notice` and `board.lounge` are natural candidates) rather than
wholesale, and read the bodies first.

### `AI_PORTAL_REPORT.html` -- internal; **the good publication candidate**

This is the one worth showing people. It contains no credentials and no auth surface. What it does
contain is the methodology: lanes with honest evidence classes, runs that record the
**author / planner / owner / committer split that git cannot express**, and a proof ledger that
distinguishes "we wrote it down" from "we watched it work."

Review before publishing anyway:

- Closeout filenames and lane notes occasionally name internal paths (`D:\code\ccode`, `C:\x64base`)
  and infrastructure details. Cosmetic, but they read as leakage.
- `MAINTAINER_ATTESTED` handle bindings are fine to show; they are a design statement, not a secret.
- Some proof notes quote command lines. Check none quotes a real token.

---

## 2. Direction B -- this machine reading x64base.com ("vice versa")

**Currently blocked, deliberately.** Network egress is the permission `host.network.egress`, and it
is **owner-only**: no agent role holds it, and the runtime STATUS reports `Block`. This was
runtime-proven in the AI-BBS lane (`proof.bbs.m2_net_egress`): an AI member was refused
`NET EGRESS OPEN` with "no in-scope role permission."

That is a **feature, not a gap**. It is what makes the local Ollama bridge safe: the model answers
`CHAT` while having no path off the box. Opening egress so the machine can read its own website
would dissolve that guarantee for a trivial convenience. If content ever needs to flow website ->
repo, do it as a **file the maintainer brings in**, not as a live fetch.

---

## 3. If publication is wanted, the shape it should take

Do **not** publish `docs/reports/` as a directory. That is the same directory-level mistake as
`git add -- src include`: it publishes whatever happens to be in the folder, including the next
report someone adds without thinking about sensitivity.

Recommended instead:

1. **Explicit allow-list** -- a publish step naming individual files, defaulting to deny. The
   `sensitivity:` field in `portal.yaml` is the machine-readable form of that list.
2. **A public build mode** -- `build_reports.py --public` that emits only publishable reports and
   omits sensitive fields (member keys reduced to kind + role; the connection recipe dropped). Better
   than a manual redaction pass, because it cannot be forgotten.
3. **Publication is `role.pub_op` + owner** -- `website.publish` is already a distinct permission.
   Any publish path must run through it, not around it.
4. **Regenerate at publish time, never copy.** These are generated artifacts; a stale published copy
   showing old permissions is worse than none.

## 4. Recommendation

| Report | Public? | Condition |
|---|---|---|
| `AI_PORTAL_REPORT.html` | **Yes, after review** | Scrub internal absolute paths; verify no token in proof notes. |
| `BBS_BOARDS_REPORT.html` | **Selective** | Publish chosen boards only; read post bodies first. Exclude `board.worklog`. |
| `BBS_ACCESS_REPORT.html` | **No** | Auth-surface map. Internal only, permanently. |
| Website -> repo (egress) | **No** | Keep `host.network.egress` owner-only and blocked. Bring files in by hand. |

The honest summary: the portal report is a **showcase** and would do the project credit. The access
report is **operational security documentation** that happens to be pretty. Same generator, same
styling, opposite handling -- which is precisely why the sensitivity marking lives in the registry
next to each item, rather than in someone's memory.

---

Lane: AIF-060 (reports). Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
Evidence class: `source-defined` (analysis + registry marking; no publish path built).
