export type NavItem = { label: string; href: string };

export const topNav: NavItem[] = [
  { label: "About", href: "/about" },
  { label: "Products", href: "/products" },
  { label: "LabTalk", href: "/products/labtalk" },
  { label: "Documentation", href: "/docs" },
  { label: "Schemas", href: "/schemas" },
  // Two LMS decks, kept deliberately separate and NOT reconciled (AIF-102).
  //
  //   /lms-proposal/     the received Microsoft Copilot pitch, preserved unchanged
  //                      as prior art. Authored with no repository access; it names
  //                      an "xBridge Protocol" that exists nowhere in the tree.
  //   /lms-architecture/ the local assessment of that pitch, measured against the
  //                      tree, carrying the LabTalk campus registry counts.
  //
  // Both are `static` in the website documentation matrix, and both are report-only:
  // no AIF closeout promotes either to repo authority. Provenance for the pair:
  // docs/maintenance/external_ai_intake/specialty_lms_ecosystem_2026-08-09/
  // Trailing slashes match the rest of the site and avoid a redirect hop.
  { label: "LMS", href: "/lms-proposal/" },
  { label: "Downloads", href: "/downloads" },
  // The AI views (lanes/runs/proofs/tasks + the maintenance console) are served by
  // the local reports gateway (tools/reports/serve_dynamic_reports.py) at `/AI/`,
  // which also keeps `/reports/` working as a transitional alias. Link index.html
  // directly: a bare directory 404s under `next dev` (no DirectoryIndex), and the
  // static snapshot in `public/reports/` is served the same way when the gateway
  // is not in front.
  { label: "AI", href: "/AI/index.html" },
  { label: "News", href: "/news" },
  { label: "Contact", href: "/contact" },
  { label: "Search", href: "/search" }
];
