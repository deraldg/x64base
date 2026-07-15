# LabTalk x64base Presentation Plan v0

Status: draft presentation plan
Scope: How x64base presents LabTalk as a Laboratory Campus
Created: 2026-07-03

## Purpose

This plan records the public-facing presentation structure for LabTalk inside the
x64base website placeholder.

The presentation should be clear but conservative:

```text
LabTalk is a laboratory campus direction for learning computing systems through
x64base and DotTalk++.
```

It should not imply a finished packaged distribution until one exists.

## Public Positioning

LabTalk is:

- a learning-lab and campus layer for x64base / DotTalk++
- a collection of apps, labs, cases, datasets, proof artifacts, and lessons
- a way to study runtime behavior, database history, self-documentation, GUIs,
  and AI-era data literacy

LabTalk is not:

- a required dependency of the x64base engine
- a replacement for DotTalk++
- a distribution with decided licensing; current status: To be determined.

## Developer Context

LabTalk may reference Derald R. Grimwood Jr.'s professional background as
current project context, but it should do so carefully and without publishing
raw resume contact details or overstating the role.

The relevant public context is:

- U.S. Army finance and payroll experience
- mainframe payroll and COBOL/business-system experience
- xBase-era software development
- title/escrow database conversion work
- SAP R/3 ABAP/4, HR, Payroll, MM, and Finance exposure
- HR and Finance systems analysis
- community-college teaching
- current DotTalk++ / x64base C++ systems development
- current AI-assisted architecture, debugging, documentation, and review

Canonical local profile:

```text
D:/code/ccode/labtalk/LABTALK_DEVELOPER_PROFILE_v0.md
```

## Main Concept

```text
concept -> app -> dataset -> command -> proof -> case -> lesson
```

This is the core LabTalk campus pattern. Public pages should repeat this idea in
plain language.

## Campus Buildings

| Building | Public Explanation |
|---|---|
| Runtime Systems Lab | DotTalk++ commands, scripts, tables, records, indexes, relations, and state. |
| Historical Data Systems Lab | Punch cards, COBOL, CODASYL, xBase, SQL, ERP, and AI-era literacy. |
| Self-Documenting Systems Lab | Comments, contracts, HELP, CMDHELP, CMDHELPCHK, metadata, and proof. |
| Dataset Library | Small inspectable datasets for repeatable learning. |
| Case Library | Engineering and historical stories connected to live or reviewed evidence. |
| GUI and Portal Lab | Local launchers, dashboards, and front-end experiments over the same evidence. |

## x64base Placeholder Updates

Updated local x64base-IIS pages:

- `D:/dev/x64base-IIS/content/docs/labtalk/overview.mdx`
- `D:/dev/x64base-IIS/content/docs/labtalk/examples.mdx`
- `D:/dev/x64base-IIS/content/docs/labtalk/non-profit-guide.mdx`
- `D:/dev/x64base-IIS/content/products/labtalk.mdx`

These pages now present LabTalk as a Laboratory Campus instead of a thin
non-profit/free-edition placeholder.

## Page Roles

| Page | Role |
|---|---|
| Product page | Short public product positioning and status boundary. |
| Overview | Explains the Laboratory Campus model. |
| Examples | Shows first lab paths and proof-aware examples. |
| Non-Profit Guide | Explains onboarding and safe usage practices. |

## Build Proof

The x64base-IIS site build was run after the updates:

```text
npm run build
```

Result:

```text
Compiled successfully.
Generated static pages: 63/63.
```

## Next Presentation Step

Add a simple diagram or visual block to the x64base site once the design system
supports it cleanly:

```text
LabTalk Campus
  Runtime Systems Lab
  Historical Data Systems Lab
  Self-Documenting Systems Lab
  Dataset Library
  Case Library
  GUI and Portal Lab
```

The first public wording should remain careful: active laboratory direction,
not finished packaged product.
