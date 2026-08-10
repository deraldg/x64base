# Co-Planning Thesis (T2) — Ledger

> **Thesis (house doctrine, Derald).** *Co-Planning:* design (**top-down**) and foundation
> (**bottom-up**) are planned and built **from both ends at once**, engineered to **meet in
> the middle** — like a bridge raised from both banks toward a surveyed meeting point.
> The **top** is the design; the **bottom** is the foundation and the pieces. The top
> declares what the foundation must carry; the foundation declares what the top can honestly
> promise; a **shared plan (the survey)** makes the two spans **converge** instead of miss.
> Neither end is finished before the other begins.

## Sibling to T1 (kept distinct on purpose)

- **T1 Co-Development** — the *parts of one artifact* develop together: code + test + docs,
  and building new work audits the surfaces it touches. ("Build the pieces together.")
- **T2 Co-Planning** — the *two directions of the whole* are planned together: top-down
  design and bottom-up foundation, surveyed to converge. ("Plan from both ends to meet.")

They reinforce but do not contain each other: you can co-develop a piece without co-planning
the whole, and you can co-plan directions without (yet) co-developing every part.

## What counts as a proof (all three)

1. **Two spans in flight** — a top-down design artifact **and** a bottom-up foundation
   effort, concurrently (not one archived, then the other).
2. **Surveyed** — a shared plan names the **meeting seam** where the spans are meant to join.
3. **Convergence** — they actually meet: the foundation delivers what the design needs at
   that seam, and/or the design is honestly constrained to what the foundation can carry.

### Strength grading
- **Strong** — both spans deliberately co-planned and met at a **named seam**.
- **Moderate** — they met, but one span predated and wasn't planned as the other's counterpart.
- **Weak** — strict sequencing dressed up as convergence.

### Falsification (kept honest)
Projects that succeed by **pure sequencing** — foundation fully first then design, or design
fully first then foundation — with no mid-planning; or spans that **miss** (design promised
what the foundation couldn't deliver; foundation built what no design needed). If success
never depends on the two ends being planned toward each other, T2 is decoration.

---

## Proof CP1 (Strong) — 2026-07-21 · AIF-043 In-Memory lane, co-planned both ends

- **Top span (design):** the lane **Charter** — vision, milestones M1–M5, durability/backend
  decisions (`PROJECT_LANE_IN_MEMORY_TABLES_V1`).
- **Bottom span (foundation):** the **M1 Assembly** — the `io()` byte-store seam, grounded
  in the *actual* DBF I/O path (`M1_ASSEMBLY_IN_MEMORY_TABLES_V1`).
- **Survey / meeting seam:** both authored in the **same session and reconciled before
  building** — the charter says "RAM-backed rows"; the assembly locates the single
  `std::fstream _fp` seam that makes it possible and routes record I/O through `io()`. The
  meeting point (`io()`) was named, then built to.
- **Convergence evidence:**
  - The bottom already reached where the top needs it — **RECNO64** (foundation, done
    earlier this session) is a **prerequisite** the in-memory design requires (RAM tables
    past 2³¹). Bottom span had arrived at the meeting line.
  - The top span reaching *down* to ground itself exposed a **crack in the bottom** — the
    `readCurrent` `_crn`-clamp bug (co-develop **P1**). Two crews checking alignment at the
    middle is exactly when you find the survey was off.
- **Grade:** Strong — deliberate, concurrent, met at the named `io()` seam; RECNO64
  corroborates the bottom span reached the line.

## Scoreboard

1 proof (CP1, Strong). Note for rigor: CP1's *deliberate* co-planning is the charter+assembly
pair; the RECNO64 convergence is partly **retrospective** (RECNO64 predated the lane, then was
recognized as its foundation) — corroboration, not the core. Cleaner future proofs want a lane
whose top and bottom are consciously surveyed to meet **from day one** — which AIF-043 M1 now is.
