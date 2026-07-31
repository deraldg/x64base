# Repository Role Instructions

**Start at `labtalk/ai_portal/AI_TIER1_SEED_V1.md`** -- the canonical Tier 1
body, roughly 8 KB: repository roles, mutation guard, git rules, house
conventions, a pointer table for perishable state, a trigger index for
everything deeper, and a five-question stopping test. If you can answer those
five, stop reading and start working.

This file is a shim over that seed and must not restate it. Two shims that
restate will diverge, and have (AIF-082, 6.8a).

## Non-Negotiable Repository Roles

Reproduced verbatim, and only this, because it is the one fact whose corruption
damages every decision downstream.

| Location | Branch | Role |
| --- | --- | --- |
| `D:\code\ccode` | `development` | Sole development and authoring workspace |
| `C:\x64base` | `main` | Sterilized publication staging for GitHub `main` |

Never author original work in `C:\x64base`. **Never push or merge `development`
to `main`.** A push from `D:\code\ccode` may target only `development`, and only
when the maintainer explicitly authorizes it. Work flows one way: develop,
promote, publish. Never backward.

The durable contract is
`docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`. If an older
document calls `C:\x64base` a backup, mirror, disposable tree, or development
workspace, that description is superseded.

## Maintenance rule for this file (AIF-082, 6.11)

Always-read surfaces amplify whatever they contain, correct or stale, with no
retrieval friction to slow a bad fact down. Delivery is not accuracy. So this
file carries only **invariants** and **pointers to maintained artifacts**. No
perishable literals -- no versions, counts, lane states, or current targets. If
an agent can cheaply measure it, say "measure it" rather than asserting it.
Perishable state lives behind the pointer table in the seed.
