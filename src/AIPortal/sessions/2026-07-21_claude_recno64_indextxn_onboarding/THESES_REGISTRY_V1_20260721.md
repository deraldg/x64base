# House Theses — Registry

**Candidate for promotion** to a permanent, cross-session doctrine home (e.g.
`docs/doctrine/THESES.md`). This lives in the session staging collection for now; theses
are durable house doctrine, not session-scoped — promote when ready.

## What a "thesis" means here

A **thesis** is an empirical, **falsifiable** house claim about how DotTalk++ is built or
how it behaves — not a preference or a style rule. Because it makes a prediction, it earns
its place by accumulating **proofs** and would be retired if the evidence stopped coming.

Every thesis in this registry carries:
- a one-line **statement**,
- a **falsification clause** (what would weaken/kill it — kept honest on purpose),
- a **proof-ledger** whose entries pass three tests — **coupling · yield · co-development**
  — and are graded **Strong / Moderate / Weak** (see the co-development ledger for the
  worked standard).

## Registry

| ID | Thesis | Statement (short) | Proof-ledger | Proofs |
|----|--------|-------------------|--------------|--------|
| **T1** | Co-Development | New work proves the engine; testing and documentation co-develop with the code, not after it (build the pieces together). | `CO_DEVELOPMENT_THESIS_LEDGER_V1` | 3 Strong |
| **T2** | Co-Planning | Top-down design and bottom-up foundation are planned from both ends to meet in the middle, like a bridge (plan the directions to converge). | `CO_PLANNING_THESIS_LEDGER_V1` | 1 Strong |
| T3 | _(reserved)_ | _to be recorded by Derald_ | — | — |

## T1 — Co-Development (recorded)

> New work *proves* the engine. Testing and documentation **co-develop** with the code —
> a feature build is also an audit of every surface it touches; defects below the test
> frontier are flushed out by reading/exercising those surfaces to build something new.

- **Falsification:** feature lanes whose "read the surfaces" pass yields nothing; defects
  that only ever come from dedicated QA and never from adjacent building; a ledger of only
  Weak proofs.
- **Proof-ledger:** `CO_DEVELOPMENT_THESIS_LEDGER_V1_20260721.md` — P1 (in-memory →
  `readCurrent` clamp bug), P2 (INDEX_TXN → `INDEXSEEK` freshness-mask), P3 (→ O11 cursor
  truncation). All Strong.

## T2 — Co-Planning (recorded)

> Top-down design and bottom-up foundation are planned and built **from both ends at once**,
> engineered to **meet in the middle** — a bridge from both banks to a surveyed meeting
> point. The **top** (design) declares what the **bottom** (foundation/pieces) must carry;
> the bottom declares what the top can honestly promise; the shared plan makes them converge.

- **Distinct from T1:** T1 builds the *parts* of one artifact together (code+test+docs);
  T2 plans the two *directions* of the whole to converge (design ⇄ foundation). Siblings.
- **Falsification:** success by pure sequencing (foundation-fully-first, or design-fully-
  first) with no mid-planning; or spans that miss (design promises what the foundation can't
  deliver; foundation builds what no design needs).
- **Proof-ledger:** `CO_PLANNING_THESIS_LEDGER_V1_20260721.md` — CP1: AIF-043 in-memory lane
  — charter (top) + M1 assembly (bottom) co-planned to meet at the `io()` seam. Strong.

## How to add a thesis (template)

```
## T<n> — <Name>
> <One-line statement of the claim.>
- Falsification: <what evidence would weaken or kill it>
- Proof criteria: coupling (building A required engaging B) · yield (real defect fixed /
  invariant hardened) · co-development (test + doc moved with the fix, same session)
- Proof-ledger: <THESIS_<NAME>_LEDGER_V…md>  (create alongside; grade each proof S/M/W)
```

Candidate T3+ seeds Derald may want to formalize (statements are his to write): the
**representative-by-design / Rule of Three** principle (referenced in AIF-037; Derald's
independent derivation dates to ALCOA **1990**, ~9 years before the Roberts/Fowler public
naming in *Refactoring*, 1999), the **"report-only, propose→review→promote"** authority-chain
discipline, or the **fixed-length typed-tuple as the single schema/typing carrier** invariant.
Listed only as prompts — a thesis isn't real here until it has its statement, its
falsification clause, and its first Strong proof.
