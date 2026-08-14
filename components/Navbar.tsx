"use client";

import Link from "@/components/StaticLink";
import { usePathname } from "next/navigation";
import { useMemo, useState } from "react";
import clsx from "clsx";
import { Menu, X, ChevronDown } from "lucide-react";
import { topNav, primaryNav, moreNav } from "@/config/nav";

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);

  const mark = (i: { label: string; href: string }) => ({
    ...i,
    active: pathname === i.href || (i.href !== "/" && pathname.startsWith(i.href + "/"))
  });

  const items = useMemo(() => topNav.map(mark), [pathname]);
  const primary = useMemo(() => primaryNav.map(mark), [pathname]);
  const more = useMemo(() => moreNav.map(mark), [pathname]);
  const moreHasActive = more.some((i) => i.active);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg/60 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-card/70">
            <span className="font-mono text-xs text-brand">64</span>
          </span>
          <span className="font-semibold tracking-tight">x64base</span>
        </Link>

        {/* min-w-0 is not decoration. Without it a flex child refuses to shrink
            below its content, which is how twelve links pushed the document
            scrollWidth past the viewport and gave every page a horizontal
            scrollbar. It is the backstop if primaryNav ever outgrows the bar
            again: the nav clips instead of the whole page scrolling sideways. */}
        <nav className="hidden min-w-0 items-center gap-1 md:flex">
          {primary.map((i) => (
            <Link
              key={i.href}
              href={i.href}
              className={clsx(
                "shrink-0 rounded-xl px-3 py-2 text-sm transition",
                i.active ? "bg-card/70 text-fg" : "text-muted hover:bg-card/60 hover:text-fg"
              )}
            >
              {i.label}
            </Link>
          ))}

          <div
            className="relative shrink-0"
            onMouseEnter={() => setMoreOpen(true)}
            onMouseLeave={() => setMoreOpen(false)}
          >
            <button
              type="button"
              onClick={() => setMoreOpen((v) => !v)}
              aria-expanded={moreOpen}
              aria-haspopup="true"
              className={clsx(
                "inline-flex items-center gap-1 rounded-xl px-3 py-2 text-sm transition",
                moreHasActive ? "bg-card/70 text-fg" : "text-muted hover:bg-card/60 hover:text-fg"
              )}
            >
              More
              <ChevronDown size={14} className={clsx("transition", moreOpen && "rotate-180")} />
            </button>
            {moreOpen ? (
              <div className="absolute right-0 top-full z-50 min-w-44 rounded-xl border border-border bg-card p-1 shadow-lg">
                {more.map((i) => (
                  <Link
                    key={i.href}
                    href={i.href}
                    onClick={() => setMoreOpen(false)}
                    className={clsx(
                      "block rounded-lg px-3 py-2 text-sm transition",
                      i.active ? "bg-bg text-fg" : "text-muted hover:bg-bg hover:text-fg"
                    )}
                  >
                    {i.label}
                  </Link>
                ))}
              </div>
            ) : null}
          </div>
        </nav>

        {/* No ThemeToggle here, deliberately (owner report 2026-08-13, round
            four). It rendered THREE times -- desktop nav, mobile bar, and the
            banner strip added by 8a3f98ff5 -- and each instance held its own
            useState `mode`. Clicking one wrote localStorage and flipped the
            class, but the other two never re-read, so their labels went stale
            and the next click computed `next` from a wrong base and jumped
            somewhere incoherent. Rounds one through three all treated this as
            a visibility problem and only ever ADDED a rendering site, which is
            what finally broke the behaviour. One control, one state: the
            banner strip in layout.tsx. */}
        <div className="flex items-center gap-2 md:hidden">
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-xl border border-border bg-card/60 p-2 text-muted hover:text-fg"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? "Close menu" : "Open menu"}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {open ? (
        <div className="border-t border-border bg-bg/70 backdrop-blur md:hidden">
          <div className="mx-auto flex w-full max-w-6xl flex-col gap-1 px-4 py-3">
            {items.map((i) => (
              <Link
                key={i.href}
                href={i.href}
                onClick={() => setOpen(false)}
                className={clsx(
                  "rounded-xl px-3 py-2 text-sm transition",
                  i.active ? "bg-card/70 text-fg" : "text-muted hover:bg-card/60 hover:text-fg"
                )}
              >
                {i.label}
              </Link>
            ))}
          </div>
        </div>
      ) : null}
    </header>
  );
}
