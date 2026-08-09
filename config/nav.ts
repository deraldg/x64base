export type NavItem = { label: string; href: string };

export const topNav: NavItem[] = [
  { label: "About", href: "/about" },
  { label: "Products", href: "/products" },
  { label: "LabTalk", href: "/products/labtalk" },
  { label: "Documentation", href: "/docs" },
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
