# DotTalk++ / LabTalk Case Catalog Seed v0

Generated normalization seed for docs/cases.

## Contents

- 15 runtime-readable CASE_*.md files
- CASE_FRAMEWORK.md template/boundary file
- REGISTRY_CASES_v0.csv and REGISTRY_CASES_v0.md
- MEDIA_ASSET_REGISTRY_v0.csv
- ../../LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md source-to-case state matrix
- ../../LABTALK_OVERLAY_BOUNDARY_V1.md optional overlay boundary
- ../../LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md and runtime_proofs/* proof scaffolds
- INSTALL_CASES.ps1 staging helper

## First-wave review candidates

- HIST-000 The Data Trail Overview
- HIST-020 JUMPS / 73C Army System
- HIST-030 Unisys / CODASYL at ALCOA
- HIST-040 xBase as a Major Platform
- HIST-090 DotTalk++ / LabTalk and the AI Future

These are review candidates, not publication-ready cases. They remain hidden until source, factual, media, and runtime/lab review gates are closed.

## Stubbed or candidate cases

The remaining HIST-* and ENG-* cases are present from the start so they are not forgotten, but they are not publication-ready.

## Installation target

Copy the docs/cases directory into the repository root so DotTalk++ can discover it at:

    <repo-root>/docs/cases

The current loader searches docs/cases, ../docs/cases, and ../../docs/cases.

## Boundary

LabTalk case files are an optional educational overlay. Core x64base and professional DotTalk++ runtime behavior should remain usable without case media, storyboards, or source DOCX files.
