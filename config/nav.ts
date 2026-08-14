export type NavItem = { label: string; href: string };

/**
 * The header is split in two because twelve items did not fit and never had.
 *
 * Measured on the live site 2026-08-14, at every desktop width: the twelve
 * links needed 1145px, the logo 131px and the padding 48px, against a header
 * capped at `max-w-6xl` = 1152px. The nav overflowed its container by ~170px,
 * which pushed the DOCUMENT scrollWidth past the viewport, so every page on
 * x64base.com carried a horizontal scrollbar and clipped "Search". Because the
 * cap is fixed, a wider monitor never helped -- this was not a small-screen
 * bug, it was every screen.
 *
 * primaryNav is what a first-time visitor needs to orient: who, what, docs,
 * get it, contact, find. Measured ~940px including logo and padding, which
 * fits 1152 with room for another item later.
 *
 * moreNav is everything a returning or deep reader wants. Nothing is deleted
 * and nothing is hidden from the mobile menu, which still lists all twelve.
 *
 * If you add an item here, add it to moreNav unless you have measured that
 * primaryNav still fits. That measurement is the whole reason this file has
 * two lists.
 */
export const primaryNav: NavItem[] = [
  { label: "About", href: "/about" },
  { label: "Products", href: "/products" },
  { label: "LabTalk", href: "/products/labtalk" },
  { label: "Documentation", href: "/docs" },
  { label: "Downloads", href: "/downloads" },
  { label: "Contact", href: "/contact" },
  { label: "Search", href: "/search" }
];

export const moreNav: NavItem[] = [
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
  // The AI views (lanes/runs/proofs/tasks + the maintenance console) are served by
  // the local reports gateway (tools/reports/serve_dynamic_reports.py) at `/AI/`,
  // which also keeps `/reports/` working as a transitional alias. Link index.html
  // directly: a bare directory 404s under `next dev` (no DirectoryIndex), and the
  // static snapshot in `public/reports/` is served the same way when the gateway
  // is not in front.
  { label: "AI", href: "/AI/index.html" },
  { label: "News", href: "/news" }
];

/** Every item, in the original order. The mobile menu shows all of these. */
export const topNav: NavItem[] = [
  primaryNav[0], primaryNav[1], primaryNav[2], primaryNav[3],
  moreNav[0], moreNav[1], moreNav[2],
  primaryNav[4],
  moreNav[3], moreNav[4],
  primaryNav[5], primaryNav[6]
];
