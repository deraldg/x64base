import type { PropsWithChildren } from "react";
import clsx from "clsx";

export function Prose({ children, className, html }: PropsWithChildren<{ className?: string; html?: string }>) {
  return (
    <article
      className={clsx(
        "prose prose-invert max-w-none",
        "prose-a:text-brand prose-a:no-underline hover:prose-a:underline",
        "prose-code:rounded prose-code:bg-bg/50 prose-code:px-1 prose-code:py-0.5",
        "prose-pre:border prose-pre:border-border prose-pre:bg-bg/30",
        className
      )}
      dangerouslySetInnerHTML={html ? { __html: html } : undefined}
    >
      {html ? null : children}
    </article>
  );
}
