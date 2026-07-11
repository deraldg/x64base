import type { AnchorHTMLAttributes, PropsWithChildren } from "react";

type StaticLinkProps = PropsWithChildren<
  Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> & {
    href: string;
  }
>;

export default function StaticLink({ href, children, ...props }: StaticLinkProps) {
  return (
    <a {...props} href={href}>
      {children}
    </a>
  );
}
