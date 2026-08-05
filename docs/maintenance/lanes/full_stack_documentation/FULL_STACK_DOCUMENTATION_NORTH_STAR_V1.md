# Full-stack documentation: the north star

Lane: `full_stack_documentation`
Owner: `member.derald`
Read this first. The plan has the gates, the cookbook has the commands, the story
has the history. This has the point.

## Two towers, one bridge

There are two towers.

The **bottom-up tower** is the engine emitting facts. Source contracts, HELP DATA,
the reference catalogs (dotref, foxref, edref, pshell_ref, sql_ref), the metadata
tables, the registries. It *knows* things: that there are 525 HELP topics, that a
command named `NET EGRESS` exists, that today was a reconciliation. It is the
producer, and it is the system of record.

The **top-down tower** is the reader-facing presentation. The developer manual and
the website -- the hero, the nav, the maintenance-class matrix, the page bundles.
It *presents*. It is the consumer, and it is never a system of record.

Between them is a **bridge**: the feeds and generators that carry a fact from the
producing tower to the presenting one. The HELP/META harvest. The current-work
feed. The command catalog sync. The website feed packet. These are the span.

## The one rule of the bridge

**A fact is entered once, at the source, and carried across the span derived --
never re-typed on the far bank.**

That is what "integration and normalization" means here. One authority per fact.
The date is the reconciliation date, advanced once in the registry. The counts are
measured from the HELP store. The pages are produced by generators. Nothing that
can be derived is ever stored twice or typed by hand into a presenting surface.

## The failure mode, and how to recognize it

When a plank is missing -- a producer that does not exist, a fact stored instead of
derived, a generated page hand-edited from the wrong side -- the two towers do not
break. The engine stays truthful; the site stays handsome. Instead they tell the
**same lie in different fonts**: a stale date on every page, a manual missing the
commands the engine already has, a "9/9 gates" that was true last month.

If a fact is wrong in more than one place at once, you are not looking at a bug.
You are looking at a missing plank -- a fact that was copied instead of crossed.

## How the bridge gets built

Pylon by pylon, one full-stack run at a time. Each pass:

- drives the next span (this run: the harvest producer now exists; the date is
  derived end to end);
- writes down what it learned so the next crossing starts further along;
- moves one more stored fact to a measured one, one more manual step to a gate.

The flush is not a chore that finishes. It is how the bridge is built and kept
load-bearing. Run it again; drive the next pylon. That is the thesis.

## Where to go next

- Doctrine and gates: `FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md`
- Run-it-now commands: `FULL_STACK_DOCUMENTATION_FLUSH_COOKBOOK_V1.md`
- The consumer span (manual + website): `FULL_STACK_DOCUMENTATION_PHASE8_PUBLICATION_ASCENT_PLAN_V1.md`
- What a real run looked like: `runs/DOCFLUSH-20260805-001/FLUSH_V4_STORY_V1.md`
