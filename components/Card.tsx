import type { PropsWithChildren } from "react";
import Link from "next/link";
import clsx from "clsx";

export function Card({
  title,
  description,
  href,
  children,
  className
}: PropsWithChildren<{
  title: string;
  description?: string;
  href?: string;
  className?: string;
}>) {
  const inner = (
    <div
      className={clsx(
        "rounded-2xl border border-border bg-card/70 p-5 shadow-soft backdrop-blur",
        "transition hover:border-brand/60 hover:bg-card/85",
        className
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold tracking-tight text-fg">{title}</h3>
          {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
        </div>
        {href ? (
          <span className="shrink-0 rounded-full border border-border bg-bg/40 px-2 py-1 text-xs text-muted">
            Open
          </span>
        ) : null}
      </div>
      {children ? <div className="mt-4">{children}</div> : null}
    </div>
  );

  return href ? (
    <Link href={href} className="block focus:outline-none focus:ring-2 focus:ring-brand/50 rounded-2xl">
      {inner}
    </Link>
  ) : (
    inner
  );
}
