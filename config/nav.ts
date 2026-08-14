export type NavItem = { label: string; href: string };

export const topNav: NavItem[] = [
  { label: "About", href: "/about" },
  { label: "Products", href: "/products" },
  { label: "LabTalk", href: "/products/labtalk" },
  { label: "Documentation", href: "/docs" },
  { label: "Schemas", href: "/schemas" },
  // ECO: the ecoschema drill-down map. This artifact is GENERATED, not static
  // -- tools/fullstack_docs/ecoschema_map.py in the x64base tree emits it from
  // projects.yaml + proofs.yaml + coordination/aif/*.claim + a scan of src/.
  // DO NOT HAND-EDIT public/eco/index.html: the next generator run reverts you
  // silently and the site then disagrees with the tree until somebody notices.
  // To change it, re-run the generator and re-copy, then compare hashes --
  // two hashes, one value, or the copy is not a copy.
  //
  // It is self-contained (one <style>, one <script>, zero external refs), so
  // it needs no build step and cannot break the Next build. Linked as
  // index.html for the same reason as /AI/: a bare directory 404s under
  // `next dev`, which has no DirectoryIndex.
  //
  // Shipped deliberately as the RAW MAP (owner ruling 2026-08-13). A teaching
  // variant -- `edu_eco`, hand-authored prose classed `maintained` wrapping the
  // generated map, with the 4-of-41 registered-proof reading framed rather
  // than bare -- is kept as a possible improvement, not chartered.
  { label: "ECO", href: "/eco/index.html" },
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
