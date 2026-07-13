# Changelog

This project follows a lightweight form of Keep a Changelog. The first public
beta release has not yet been cut.

## Unreleased

### Added

- Tentative root MIT license and public contribution/security policies.
- Cross-platform C++ build and test workflow for the public `main` branch.
- Portable core build presets and optional dependency features.
- Explicit public project status and release-readiness documentation.

### Changed

- Public `main` is defined as the canonical collaboration and release branch.
- Risky external processes use the shared security authorization policy.
- `COMMIT` no longer reports success or clears remaining retry state after a
  memo flush failure.

### Security

- Network and external-process commands are disabled unless explicitly
  authorized by environment policy.
