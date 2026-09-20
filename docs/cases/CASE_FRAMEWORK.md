# CASE_FRAMEWORK

This file is intentionally named CASE_FRAMEWORK.md so the current case catalog loader skips it.

## Purpose

The normalized CASE_*.md files are runtime-readable derivatives of source/evidence material. They are not the source of truth by themselves.

## Current loader contract

The uploaded case_catalog.cpp loader expects files under docs/cases whose filenames start with CASE_ and end in .md. It reads simple front matter fields id, title, type, era, level, lab, and domains. It extracts these body sections:

- SUMMARY
- PROBLEM
- WORKFLOW
- MODEL
- TAKEAWAY

## Boundary

- Source DOCX files and images remain evidence assets.
- CASE_*.md files are normalized catalog entries.
- runtime_visibility: hidden_until_reviewed means registered but not student/runtime-published.
- manual_visibility: outline_only means table-of-contents presence only.
- Engineering cases need an attached runtime proof packet before promotion.
- LabTalk/cases/media are optional overlay artifacts, not required x64base engine dependencies.

## Promotion rule

A case should not become publication-ready until source review, factual review, media review, and runtime/lab review have passed.
