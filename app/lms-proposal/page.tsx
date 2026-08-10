// App Router:  app/lms-proposal/page.tsx
//
// The received Copilot deck, served as-is. This is the PITCH, preserved as prior
// art -- not a description of the tree. The paired assessment at
// /lms-architecture/ contradicts it deliberately; the two are not reconciled.
// Provenance: docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/
import Artifact from "./Artifact";

export const metadata = {
  // Owner-titled 2026-08-10: "NON LMS" is deliberate -- fun, true, and not
  // true. True: this is not a Learning Management System (no grading; the
  // module/skill/plugin boundary rules that out). Not true: the system drifts
  // ever closer to being an LMS of another expansion -- a Learning Memory
  // System. Owner ruled unhyphenated (2026-08-10) as the more professional
  // form. Scope of the retitle is the shell we author -- this metadata, the
  // iframe title, and deck.html's own chrome + tab title. Copilot's received
  // slides (including the cover hero, which still reads "LMS") are untouched
  // per the intake preserve rule; the contradiction is the point.
  title: "Specialty NON LMS Ecosystem -- Unified Platform Proposal",
  description:
    "Received external proposal (Microsoft Copilot, 2026-08-09), preserved unchanged. "
    + "Not repo authority; see the LMS Architecture assessment. NON LMS: no grading, "
    + "no management -- though it drifts toward a Learning Memory System.",
};

export default function Page() {
  return <Artifact />;
}
