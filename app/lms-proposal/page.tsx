// App Router:  app/lms-proposal/page.tsx
//
// The received Copilot deck, served as-is. This is the PITCH, preserved as prior
// art -- not a description of the tree. The paired assessment at
// /lms-architecture/ contradicts it deliberately; the two are not reconciled.
// Provenance: docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/
import Artifact from "./Artifact";

export const metadata = {
  title: "Specialty LMS Ecosystem -- Unified Platform Proposal",
  description:
    "Received external proposal (Microsoft Copilot, 2026-08-09), preserved unchanged. "
    + "Not repo authority; see the LMS Architecture assessment.",
};

export default function Page() {
  return <Artifact />;
}
