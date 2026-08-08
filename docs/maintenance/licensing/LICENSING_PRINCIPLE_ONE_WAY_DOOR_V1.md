# Licensing Principle: Openness Is a One-Way Door

**Status:** hardened principle -- the rule the license map and the four proposals sit under.
Owner: member.derald. Date 2026-08-08. Not legal advice; it is decision doctrine.

## The principle

**You can always become more open. You can never pull back a version you already released
open.** Loosening a license later is free and always available. Tightening it is impossible
for anything already released under the looser terms. License risk is therefore
*asymmetric*: over-restricting is reversible; over-opening is not.

## The corollary that matters here: "adoption now, income later" is achievable -- but not the naive way

The plan "open it now for adoption, then close it and charge later" **does not exist.** You
cannot revoke an open release from the people who already have it. Anyone who proposes that
path is wrong about how licenses work.

The real "adoption now, income later" runs on three levers, none of which costs you a single
adopter:

1. **Dual-licensing.** Release the open license (GPL) *and* offer a commercial license
   beside it. The open side drives adoption; the commercial side is the income door. Free,
   educational, hobby, and personal users never pay; only a closed/commercial embedder buys
   the exception. Adoption and income at the same time, not in sequence.
2. **Copyright ownership.** Because you wrote it, you own it, so you may sell commercial
   licenses at any time and relicense *future* versions on any terms you choose. Your
   authorship is the master key that keeps every future option open.
3. **A Contributor License Agreement (CLA).** The moment an outside contributor commits
   without a CLA, they co-own their contribution, and you lose the ability to dual-license or
   relicense. Require a CLA before accepting *any* outside contribution. This is the single
   cheapest thing that protects every other lever.

Keep those three and "income later" is fully preserved while you optimize for adoption today.

## Rules that fall out of it

- **A license binds the versions released under it, not the project forever.** Future
  versions can carry a different license (you own it); released versions cannot be changed
  retroactively.
- **Permissive is the most irreversible choice.** Apache/MIT give everything away with no
  copyleft and no dual-license leverage -- there is nothing restricted left to sell an
  exception to. Use permissive only where you intend the thing to be a genuinely free
  foundation (e.g., the embeddable engine, chosen as a deliberate platform bet).
- **Copyleft keeps the door.** GPL is fully open (adoption) yet a closed-source commercial
  user still needs a commercial license from you (income lever intact). It is the "open, but
  I kept the key" middle -- the right default when you want adoption without foreclosing
  income.
- **Protect the copyright above all.** CLA on every outside contribution, always.

## Where x64base stands right now (important, and reassuring)

The one-way door only closes for a version once someone **actually receives and relies on
it** under the open terms. x64base is **pre-adoption**: the GPLv3 blanket was just published,
`main` is not yet promoted, and no one has built on it. So you are still *setting* the door's
position, not undoing a release. Choosing the final posture now -- Apache engine (revived),
GPL+commercial app, CC-BY content, private AI, marks reserved -- is clean. The principle
governs from here **forward**: once builders arrive, what you released to them is fixed.

## The one genuinely irreversible commitment on the table

Taking the engine to **Apache** is the only decision here that cannot be walked back for the
versions you release. That is fine -- it is the intended platform bet -- but make it
deliberately, not casually. Everything else (GPL+commercial app, CC content) preserves your
levers and can be tuned later.
