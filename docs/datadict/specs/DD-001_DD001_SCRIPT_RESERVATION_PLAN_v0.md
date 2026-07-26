# DD-001 Script Reservation Plan v0

Scripts are part of the DotTalk++ lifecycle and should be cataloged as first-class artifacts. They should not be hidden as loose files, and they should not be confused with engine dependencies.

## Script classes to reserve

```text
DotScript runtime/setup scripts
  metadata lane setup, workspace load, smoke checks, path setup

Build/config scripts
  CMake, presets, vcpkg manifests, build wrappers

Python probes/bindings
  pydottalk tests, lifecycle probes, diagnostics

Maintenance scripts
  MDO/manualgen packages, savepoint appenders, publication validators

Runtime launchers
  dev/test launchers, smoke launchers, profile launchers

Optional overlay loaders
  LabTalk/case/student/media setup scripts
```

## Rule

A script can be cataloged without being part of x64base core. `DD_SCRIPT.required_for_profile` and `DD_SCRIPT_BOUNDARY` keep that distinction explicit.

## Current corrected zip observation

The corrected C++ zip contains Python binding/probe scripts and build config files. It does not contain the larger PowerShell/MDO/DotScript estate seen or discussed elsewhere, so DD-003 should accept additional script roots when run locally.
