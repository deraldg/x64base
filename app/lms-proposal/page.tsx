// App Router:  app/lms-proposal/page.tsx
//
// The received Copilot deck, served as-is. This is the PITCH, preserved as prior
// art -- not a description of the tree. The paired assessment at
// /lms-architecture/ contradicts it deliberately; the two are not reconciled.
// Provenance: docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/
import Artifact from "./Artifact";

export const metadata = {
  // Owner-titled 2026-08-10: "NON-LMS" is deliberate -- fun, true, and not
  // true. True: this is not a Learning Management System (no grading; the
  // module/skill/plugin boundary rules that out). Not true: the system drifts
  // ever closer to being an LMS of another expansion -- a Learning Memory
  // System. The preserved deck inside still says "LMS"; the contradiction is
  // the point, and the deck stays byte-identical per the intake rule.
  title: "Specialty NON-LMS Ecosystem -- Unified Platform Proposal",
  description:
    "Received external proposal (Microsoft Copilot, 2026-08-09), preserved unchanged. "
    + "Not repo authority; see the LMS Architecture assessment. NON-LMS: no grading, "
    + "no management -- though it drifts toward a Learning Memory System.",
};

export default function Page() {
  return <Artifact />;
}
