import type { PropsWithChildren } from "react";
import clsx from "clsx";

export function Container({ children, className }: PropsWithChildren<{ className?: string }>) {
  return <div className={clsx("mx-auto w-full max-w-6xl", className)}>{children}</div>;
}
