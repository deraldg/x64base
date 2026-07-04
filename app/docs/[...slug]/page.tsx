import type { Metadata } from "next";
import Link from "next/link";
import { Sidebar } from "@/components/Sidebar";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Prose } from "@/components/Prose";
import { docsSidebar, flattenSidebar } from "@/config/sidebars";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { resolveMdxPath, walkMdx } from "@/lib/content";

export async function generateStaticParams() {
  const all = walkMdx("docs");
  return all.map((r) => ({ slug: r.slug }));
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ slug: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const filePath = resolveMdxPath("docs", slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  return metadataFromFrontmatter(frontmatter, `/docs/${slug.join("/")}`);
}

export default async function DocsPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const { slug } = await params;
  const filePath = resolveMdxPath("docs", slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  const href = `/docs/${slug.join("/")}`;
  const flat = flattenSidebar(docsSidebar);
  const idx = flat.findIndex((i) => i.href === href);
  const prev = idx > 0 ? flat[idx - 1] : null;
  const next = idx >= 0 && idx < flat.length - 1 ? flat[idx + 1] : null;

  return (
    <div className="flex gap-8">
      <Sidebar groups={docsSidebar} />

      <div className="min-w-0 flex-1">
        <Breadcrumbs
          items={[
            { label: "Home", href: "/" },
            { label: "Documentation", href: "/docs" },
            { label: frontmatter.title ?? slug[slug.length - 1], href }
          ]}
        />

        <h1 className="text-3xl font-semibold tracking-tight">{frontmatter.title}</h1>
        {frontmatter.description ? <p className="mt-2 text-muted">{frontmatter.description}</p> : null}

        <div className="mt-8">
          <Prose html={content} />
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t border-border pt-6 text-sm md:flex-row md:items-center md:justify-between">
          <div>
            {prev ? (
              <Link href={prev.href} className="text-muted hover:text-fg">
                ← {prev.label}
              </Link>
            ) : null}
          </div>
          <div>
            {next ? (
              <Link href={next.href} className="text-muted hover:text-fg">
                {next.label} →
              </Link>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
