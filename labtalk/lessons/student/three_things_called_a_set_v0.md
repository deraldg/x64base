# Three Things Called a Set v0

Status: idea
Audience: student, self-learner, instructor
Registry ID: lesson.student.three_things_called_a_set

## Purpose

Teach students to read past vocabulary. One system, one word, three different
meanings -- and the skill being built is noticing that a familiar word has been
reused rather than assuming it means what it meant last time.

x64base uses "set" for three unrelated things:

| Spelling | What it actually is | Where |
|---|---|---|
| `SET ORDER`, `SET RELATION`, `SET FILTER` | a VERB. Configure session state. | the `SET` command family |
| CODASYL `SET` | an OWNER-to-MEMBER RELATIONSHIP between two record types | `CODASYL` command, `src/cli/cmd_codasyl.cpp` |
| workspace GROUP | a flat COLLECTION: named, membership-based, may overlap | the workspace manager |

The first is obvious once seen. The interesting pair is the second and third,
because they look alike and are not.

## The trap

A CODASYL set and a workspace group both present as "a named thing you can
traverse". A student who has met one will map the other onto it and be wrong in
a way that produces working code and false understanding.

**CODASYL set: membership is a RELATIONSHIP.** A `SET` names an owner record
type and a member record type. A member belongs to a set *occurrence* by virtue
of a key matching an owner. Traversal is owner-to-members. It is much closer to
`SET RELATION` than to a container. In x64base this is deliberately a teaching
veneer: no physical owner/member pointers, no on-disk CODASYL storage, rings
simulated by GET FIRST / GET NEXT over a snapshot.

**Workspace group: membership is BELONGING.** A group names a collection of
workspaces. A workspace is in the group or it is not; nothing relates it to
another workspace. A workspace may be in several groups at once, which no
CODASYL member can be with respect to one set type.

The one-sentence discriminator, worth memorising:

> A CODASYL set relates records to each other. A workspace group collects
> workspaces. One is an edge; the other is a bag.

## Campus Path

```text
lesson.student.database_history_trail   (COBOL / CODASYL / xBase / SQL trail)
  -> lesson.student.three_things_called_a_set
    -> the workspace manager (groups) as the modern instance
```

## Student Path

1. Run `CODASYL` with no arguments and read its usage. Note that it says
   "teaching adapter" and lists what it deliberately does NOT do.
2. Find an owner and a member in a loaded world. Traverse owner-to-members.
   Ask: what makes a record a member? (A key match, not a declaration.)
3. Ask the falsifying question: **can one member record belong to two different
   set occurrences of the same set type at once?** Work out why not.
4. Now look at workspace groups. Put one workspace in two groups.
5. Ask the same falsifying question and get the opposite answer. That difference
   IS the lesson.
6. Finally, run any `SET ORDER` / `SET FILTER` command and observe that the
   third meaning shares nothing with the first two but the letters.

## Expected Observations

- Vocabulary collision is normal in real systems and is not a defect. It happens
  because different eras solved different problems and reached for the same
  short word.
- The way to tell them apart is not the name; it is the QUESTION each answers.
  "What is this record related to?" versus "what collection is this in?"
- A word being familiar is not evidence that the concept is. This generalises
  well beyond databases and is the transferable skill here.
- Overlap is the sharp test: things that can belong to two collections at once
  are not participating in a relationship, they are being collected.

## Instructor Notes

The historical framing is genuinely useful and should not be presented as
merely a curiosity: CODASYL (1969) already had named collections with
membership and traversal. Students should leave understanding that "named
collection you can walk" is not a modern invention, while ALSO being able to
say precisely how the 1969 version differs from the 2026 one.

Resist the tempting simplification "workspace groups are just CODASYL sets".
It is memorable, and it is wrong, and the lesson exists because it is wrong.

## Proof Links

- `src/cli/cmd_codasyl.cpp` -- the CODASYL teaching adapter, `status: supported`,
  `category: education`. Its own header states the non-goals.
- `docs/maintenance/WORKSPACE_RUNTIME_RECONCILIATION_AIF070_AIF078_V1.md` --
  the group model, and the record of why "group" was chosen over "set"
  (the word was already taken twice).
- `lesson.student.database_history_trail` -- the surrounding history trail.

## Next Gate

**This lesson is an IDEA, not a draft, and the reason is honest: half of it is
not runnable yet.** The CODASYL half works today. The workspace-group half
describes a manager that does not exist (AIF-078, design stage). Steps 4 and 5
of the Student Path cannot be performed.

Promote to `draft` when workspace groups exist and a student can actually put
one workspace in two groups and observe the difference. Until then this is a
lesson plan, not a lesson, and marking it otherwise would be the exact defect
class the campus records elsewhere -- a documented capability that has not been
honoured.
