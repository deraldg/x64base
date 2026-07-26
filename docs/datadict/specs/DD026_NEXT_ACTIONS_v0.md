# DD-026 Next Actions v0

1. Install the DD-026 drop-in.
2. Run `triage_report.py --help`.
3. Run DD-026 against the clean DD-025 stable A/B classification; expected PASS with zero rows.
4. Run DD-026 against the intentional plan-to-full DD-025 classification; expected BLOCKED_REVIEW with lane/gate/root summaries.
5. Use the triage report to decide the next specialized scan/proof package.

Recommended next package after local proof: DD-027, a lane-specific rescan launcher/plan that takes DD-026 gates and proposes exactly which extractors/checks should run next.
