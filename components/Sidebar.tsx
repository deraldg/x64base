"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import type { SidebarGroup } from "@/config/sidebars";

export function Sidebar({ groups }: { groups: SidebarGroup[] }) {
  const pathname = usePathname();

  return (
    <aside className="sticky top-20 hidden h-[calc(100vh-6rem)] w-64 shrink-0 overflow-y-auto pr-2 md:block">
      <div className="rounded-2xl border border-border bg-card/40 p-3">
        {groups.map((g) => (
          <div key={g.label} className="mb-4 last:mb-0">
            <div className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-muted">
              {g.label}
            </div>
            <div className="flex flex-col gap-1">
              {g.items.map((i) => {
                const active = pathname === i.href;
                return (
                  <Link
                    key={i.href}
                    href={i.href}
                    className={clsx(
                      "rounded-xl px-2 py-1.5 text-sm transition",
                      active ? "bg-bg/60 text-fg" : "text-muted hover:bg-bg/40 hover:text-fg"
                    )}
                  >
                    {i.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
