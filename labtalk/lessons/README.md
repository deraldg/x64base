# LabTalk Lessons

This directory is the local lesson shelf for the Laboratory Campus.

Lesson records are registered in:

```text
registries/lessons.yaml
```

The lesson platform separates two lanes:

- `student/` - lessons intended to become learner-facing campus material.
- `career/` - lessons learned while building LabTalk, DotTalk++, x64base, and related systems.

## Lesson Rule

A LabTalk lesson should stay connected to the campus proof chain:

```text
concept -> app -> dataset -> command -> proof -> case -> lesson
```

Draft lessons may be visible, but they must keep their proof state and next gate
clear. Do not promote a lesson to `student_ready` until setup, safety,
expected observations, review notes, and proof links are complete.

## Lesson Shape

Use this shape unless a lesson has a stronger local template:

```text
Title
Status
Audience
Purpose
Source story
Concepts
Apps used
Dataset used
Commands used
Student path
Expected observations
Questions
Proof/evidence links
Instructor notes
Career lesson, if applicable
Next gate
```
