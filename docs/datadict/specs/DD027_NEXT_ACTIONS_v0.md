# DD-027 Next Actions v0

After installing DD-027:

1. Run `baseline_accept.py --help`.
2. Accept the current green stable baseline using:
   - scan: `docs/datadict/reports/DDRUN-stable-B-v0`
   - diff: `docs/datadict/reports/DDRUN-stable-A-to-B-diff-v0`
   - triage: `docs/datadict/review_queue/DD026-stable-A-to-B-v0`
3. Store output under `docs/datadict/baselines/DDBASE-stable-v0`.
4. Use `dd027_next_comparison_target.json` as the base reference for the next redocumentation run.

Do not import catalog DBFs or promote dictionary facts as part of DD-027.
