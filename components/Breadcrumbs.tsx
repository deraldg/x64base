import Link from "next/link";

export type Crumb = { label: string; href: string };

export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-6 text-sm text-muted">
      <ol className="flex flex-wrap items-center gap-2">
        {items.map((c, idx) => (
          <li key={c.href} className="flex items-center gap-2">
            <Link href={c.href} className="hover:text-fg">
              {c.label}
            </Link>
            {idx < items.length - 1 ? <span className="text-border">/</span> : null}
          </li>
        ))}
      </ol>
    </nav>
  );
}
