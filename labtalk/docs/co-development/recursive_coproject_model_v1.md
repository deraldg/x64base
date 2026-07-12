# The Recursive Co-development Model

Status: Architectural narrative  
Version: 1  
Date: 2026-07-11

## Definition

x64base is developed through cooperating systems rather than a one-way sequence
from code to documentation. Runtime behavior produces evidence; metadata and
SelfDoc organize it; the Laboratory Campus turns reviewed evidence into labs,
cases, diagrams, and lessons; public documentation exposes omissions and
contradictions that return to implementation work.

This is recursion in the engineering sense: the outputs of one pass become
inputs to the next pass through the same governed system.

## Three primary coproject systems

1. **x64base and DotTalk++ implementation** - the engine, command runtime,
   DotScript, contracts, HELP surfaces, and executable behavior. This repository
   is the primary technical truth.
2. **Metadata, SelfDoc, and Laboratory Campus** - collection, validation,
   provenance, proof preservation, diagrams, datasets, cases, labs, and lessons.
3. **Public documentation systems** - reviewed manuals, x64base.com, and the
   supporting DotTalk++ artifact site. Publication is a consumer and diagnostic
   surface, not an independent source of engine truth.

## Recursive loop

```text
engine behavior
    -> runtime evidence and source contracts
    -> HELP, metadata, and SelfDoc collection
    -> reviewed reports, diagrams, cases, and lessons
    -> manuals and public documentation
    -> review reveals gaps, drift, and contradictions
    -> findings return to metadata and implementation
    -> the next pass produces stronger evidence
```

The loop is controlled by provenance and review gates. Website prose cannot
silently become engine truth, and generated material cannot promote itself.

## LabTalk is broader than an executable

The Laboratory Campus, with LabTalk retained as its project and historical
name, is a hybrid collaboration layer. It contains implemented components,
developing labs, datasets, runtime demonstrations, help systems, GUI and portal
experiments, planning material, and proof artifacts. Its public repository
boundary may be incomplete without making the working local coproject empty.

## Governing doctrine

> Runtime proves, source defines, HELP explains, metadata organizes, and
> SelfDoc preserves.

The website publishes reviewed derivatives of that chain. Review then recurses
back into the system, making documentation an active engineering instrument
rather than an after-the-fact report.

## Boundaries

- Runtime and source remain authoritative for implementation claims.
- SelfDoc and metadata preserve provenance rather than manufacturing proof.
- Laboratory Campus may contain existing, developing, planned, and experimental
  work, but each item must state its status.
- Website review may identify a defect or omission; it cannot repair the source
  merely by changing public prose.
- Manual-to-website and website-to-manual movement must follow the documented
  simplex and duplex publication gates.

## Public derivative

The website page derived from this source should link onward to the SelfDoc feed
pipeline, website publication rules, Laboratory Campus overview, and important
documents index.
