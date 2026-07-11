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
  const separator = base.includes("?") ? "&" : "?";

  return `${base}${separator}v=${encodeURIComponent(siteVersion)}${hash}`;
}

export default function StaticLink({ href, children, ...props }: StaticLinkProps) {
  return (
    <a {...props} href={versionedHref(href)}>
      {children}
    </a>
  );
}
