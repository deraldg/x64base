import type { AnchorHTMLAttributes, PropsWithChildren } from "react";

type StaticLinkProps = PropsWithChildren<
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
    href: string;
  }
>;

const siteVersion = process.env.NEXT_PUBLIC_SITE_VERSION ?? "local-preview";

function versionedHref(href: string) {
  if (!href.startsWith("/") || href.startsWith("//")) return href;

  const hashIndex = href.indexOf("#");
  const base = hashIndex >= 0 ? href.slice(0, hashIndex) : href;
  const hash = hashIndex >= 0 ? href.slice(hashIndex) : "";

  // Split any existing query off the path so we can normalize the path itself.
  const qIndex = base.indexOf("?");
  let pathPart = qIndex >= 0 ? base.slice(0, qIndex) : base;
  const existingQuery = qIndex >= 0 ? base.slice(qIndex) : "";

  // The site is built with `trailingSlash: true` (next.config): every directory
  // route is exported as `<path>/index.html`. A bare `/products` (no slash) cannot
  // resolve to that index without DirectoryIndex, so it 404s in local preview and on
  // a plain static host. Give extension-less directory routes a trailing slash so the
  // link matches the export. Leave explicit files (e.g. `/AI/index.html`) untouched.
  const lastSeg = pathPart.slice(pathPart.lastIndexOf("/") + 1);
  if (pathPart !== "/" && !pathPart.endsWith("/") && !lastSeg.includes(".")) {
    pathPart = `${pathPart}/`;
  }

  const rebuilt = `${pathPart}${existingQuery}`;
  const separator = rebuilt.includes("?") ? "&" : "?";

  return `${rebuilt}${separator}v=${encodeURIComponent(siteVersion)}${hash}`;
}

export default function StaticLink({ href, children, ...props }: StaticLinkProps) {
  return (
    <a {...props} href={versionedHref(href)}>
      {children}
    </a>
  );
}
