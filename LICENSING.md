# x64base / DotTalk++ -- Licensing

Owner: Derald R Grimwood Jr. Status: **decided 2026-08-08 (dual-license, copyleft core)**.
Not legal advice -- the wording below is a drafted strategy; confirm the commercial-license
and CLA specifics with a lawyer before you sign anything. But this is a coherent posture you
can stand behind, and it replaces the old contradiction (MIT-tentative vs "all rights
reserved").

## The posture, in one sentence

x64base is **open source under the GNU GPL v3** for everyone, and **available under a
separate commercial license** for anyone who wants to use it in a closed or proprietary
product. You keep giving it away; only closed-source commercial users ever pay.

## Why this fits your goal

You wanted three things at once: share generously, encourage interest and preservation, and
leave an ethical door open to earn something -- without feeling mercenary. Copyleft
dual-licensing does all three:

- **Generous, and real open source.** GPLv3 is OSI-approved and copyleft. The retro / xBase
  lineage crowd and educators respect it precisely because it is genuinely open, not
  "source-available with an asterisk." Anyone can read it, run it, teach with it, fork it,
  and preserve it, forever, for free.
- **The people you most want to reach never pay.** Students, educators, hobbyists, retro-
  computing folks, researchers -- all covered by the GPL at no cost. That is what keeps it
  from feeling mercenary: the license only asks something of *commercial closed-source*
  users.
- **A real income door, in the code itself.** GPLv3 requires that anyone who distributes a
  derivative also open-source it. A company that wants to embed x64base in a *closed*
  product cannot comply with the GPL, so they come to you for a **commercial license**. That
  is the classic dual-license model (Qt, MySQL, and others have earned this way for decades).

Open license, `GPL-3.0`. Note: if you expect people to run it as a hosted *network service*
and want that to trigger the same sharing obligation, use **AGPL-3.0** instead -- one-word
swap in the LICENSE header. GPLv3 is the simpler default for a desktop/educational runtime;
AGPL closes the "SaaS loophole." Pick GPL unless you specifically want the network clause.

## What each license covers

One codebase, two ways to receive it -- do NOT try to license subsystems (DotTalk++, the
metadata surfaces, the index lanes) separately from the runtime. That was an over-complication;
it just makes the terms unenforceable and confusing. The whole engine is GPLv3; the commercial
license is an exception to the *whole* engine.

- **GPL-3.0** -- the default. Full source, full freedom, with the copyleft obligation.
- **Commercial license** -- a private agreement you grant, waiving the copyleft obligation
  for a specific closed/commercial use, in exchange for a fee you set. Because you own the
  copyright, you can offer this to anyone, anytime.

## The value layer -- income that gates nothing (farmed from the Copilot discussion)

Most of your ethical, non-mercenary income does not come from the license at all. It comes
from **understanding**, which you can sell without restricting a single line of code:

- **GitHub Sponsors / donations** -- the least-mercenary of all; nothing is gated.
- **Teaching materials** -- an "inside the engine" curriculum, a book/guide, architecture
  diagram sets, curated DBF/xBase lineage documentation.
- **Workshops, lectures, courses** -- live or recorded, for schools or companies.
- **Support / consulting / institutional contracts** -- paid help, not paid code.

The framing that keeps your dignity intact: **you are not selling the engine; you are selling
the teaching and the understanding around it.** The engine stays free.

## Educational grant

Educational and non-commercial use is already free under the GPL -- no grant needed for that.
The grant only matters for an accredited institution that wants *commercial/closed* terms:
offer them the commercial license at no charge or a nominal fee. "Controlled, but kind."

## Marks are not the license

`x64base`, `DotTalk++`, and `LabTalk` are **project marks** (names/brand), separate from the
code license. The GPL licenses the *code*, not the *name*. Anyone may fork the code; nobody
may use your marks to imply your endorsement of their fork, or ship a fork under your names.
This is a standard, open-source-compatible trademark reservation -- state it, do not enforce
it aggressively.

## What makes all of this possible: you own the copyright

You are the sole author, so you hold the copyright, so you can offer both licenses. The one
thing that would break this: accepting outside contributions without a **Contributor License
Agreement (CLA)**. If contributors ever appear, have them sign a simple CLA assigning (or
licensing) their contribution to you, or you lose the ability to relicense commercially. No
action needed today; note it for the day a second person commits.

## Implementation checklist (what to actually put in place)

1. `LICENSE` at the repo root -- the dual-license notice (drafted; see the file).
2. `COPYING` at the repo root -- the verbatim GPL-3.0 text from
   `https://www.gnu.org/licenses/gpl-3.0.txt` (do not retype it; download it).
3. `/licensing` page on the website -- the public-facing version of this posture.
4. Footer fix -- replace "All rights reserved" with the dual-license line, so it stops
   contradicting the license.
5. `project-truth` page -- replace the "root MIT license is tentative" line with this decision.
6. A per-file header note in new source files (optional but tidy): the standard GPLv3 notice
   plus "commercial licensing available -- contact the author."
