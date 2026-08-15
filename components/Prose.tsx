import type { PropsWithChildren } from "react";
import clsx from "clsx";

export function Prose({ children, className, html }: PropsWithChildren<{ className?: string; html?: string }>) {
  return (
    <article
      className={clsx(
        // prose-invert only under html.dark -- hardcoded invert painted
        // near-white text on the light theme (docs section, 2026-08-11).
        "prose dark:prose-invert max-w-none",
        "prose-a:text-brand prose-a:no-underline hover:prose-a:underline",
        "prose-code:break-words prose-code:whitespace-normal prose-code:rounded prose-code:bg-bg/50 prose-code:px-1 prose-code:py-0.5",
        // Code BLOCKS. prose-pre:text-fg is load-bearing, not tidying.
        //
        // Tailwind Typography's default `pre` is a dark chip on a light page:
        // it pairs a near-black background with gray-200 TEXT. The line below
        // used to override only the background (bg-bg/30, near-white in the
        // light theme) and left the text at that gray-200 default -- so light
        // mode painted rgb(229,231,235) on rgb(250,251,253). Measured 1.2:1,
        // against 4.5:1 for body text. The blocks were not faint, they were
        // GONE: owner called them "ghost scripts" and could only read them by
        // switching to dark, where the same colour measures 15.3:1.
        //
        // Inline code was never affected -- prose-code has always resolved to
        // a near-black (17.1:1), which is why `DbArea` read fine one line above
        // an invisible .dts block on the same page. That asymmetry is the tell.
        //
        // text-fg follows the theme, so both halves now move together.
        "prose-pre:border prose-pre:border-border prose-pre:bg-bg/30 prose-pre:text-fg",
        // The children of <pre> carry their own colour from the highlighter, so
        // inheritance alone does not reach them.
        "[&_pre_code]:text-fg [&_pre_code_span]:text-inherit",
        className
      )}
      dangerouslySetInnerHTML={html ? { __html: html } : undefined}
    >
      {html ? null : children}
    </article>
  );
}
