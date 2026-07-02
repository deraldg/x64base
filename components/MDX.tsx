import Link from "next/link";
import type { ComponentProps } from "react";

function Anchor(props: ComponentProps<"a">) {
  const href = props.href ?? "";
  if (href.startsWith("/")) {
    return <Link href={href}>{props.children}</Link>;
  }
  return <a {...props} target={props.target ?? "_blank"} rel={props.rel ?? "noreferrer"} />;
}

export const mdxComponents = {
  a: Anchor,
  code: (props: ComponentProps<"code">) => <code className="font-mono text-sm" {...props} />,
  pre: (props: ComponentProps<"pre">) => <pre className="font-mono text-sm" {...props} />
} as const;
