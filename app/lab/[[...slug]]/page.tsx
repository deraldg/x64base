import type { Metadata } from "next";
import Link from "@/components/StaticLink";
import { Prose } from "@/components/Prose";
import { compileMdxFromFile } from "@/lib/mdx";
import { metadataFromFrontmatter } from "@/lib/seo";
import { resolveMdxPath, walkMdx } from "@/lib/content";

/**
 * THE LAB -- local-only working surface. Created 2026-08-17.
 *
 * WHY IT EXISTS
 *   Some pages are real work but not a public claim yet: prototypes, research
 *   directions, inventories of things that exist in source but are not proven.
 *   Before this route the only choices were "publish it" or "delete it", so
 *   unfinished material sat on the public site carrying more authority than the
 *   work behind it. The first tenant is the Dewey / hierarchy experiment
 *   inventory, moved out of /docs/dev/experimental.
 *
 *   It is deliberately NOT /reports (that lane is the AI portal and console) and
 *   NOT /retro (that lane is emulator and OS-capture material whose
 *   redistribution rights are unsettled). Different reasons for being private.
 *
 * HOW IT STAYS PRIVATE -- three independent layers, same as /retro and /reports:
 *   1. config/nav.ts localOnlyNav -- the link renders only when
 *      NEXT_PUBLIC_SITE_VERSION is unset, i.e. local preview. WEAKEST layer: a
 *      hidden link still builds a reachable route, so it must never be alone.
 *   2. scripts/strip-local-only-output.mjs LOCAL_ONLY_DIRS -- "lab" is listed,
 *      so the built directory is deleted from every output root before publish.
 *   3. scripts/publish-github-pages.mjs -- ABORTS the publish outright if
 *      out/lab survived anyway.
 *
 *   Any one layer failing leaves the other two. That is the point, and it is why
 *   adding a page here is safe by default rather than safe if you remember.
 *
 * TO PROMOTE A PAGE OUT OF THE LAB
 *   Move the .mdx back under content/docs/, add its sidebar entry in
 *   config/sidebars.ts, and check nothing still links to /lab. Promotion is a
 *   deliberate edit in two files, which is the intended friction.
 */

export async function generateStaticParams() {
  return [
    { slug: [] as string[] },
    ...walkMdx("lab").map((r) => ({ slug: r.slug }))
  ];
}

export async function generateMetadata({
  params
}: {
  params: Promise<{ slug?: string[] }>;
}): Promise<Metadata> {
  const { slug } = await params;
  if (!slug?.length) {
    // The index is not a content file; it is the listing below.
    return { title: "The Lab", robots: { index: false, follow: false } };
  }
  const filePath = resolveMdxPath("lab", slug);
  const { frontmatter } = await compileMdxFromFile(filePath);
  const meta = metadataFromFrontmatter(frontmatter, `/lab/${slug.join("/")}`);
  // Belt and braces: this should never be fetched by a crawler because it is
  // never published, but if it ever is, say so in the page itself too.
  return { ...meta, robots: { index: false, follow: false } };
}

function Banner() {
  return (
    <div className="mb-8 rounded-lg border border-border bg-card/60 px-4 py-3 text-sm">
      <span className="font-mono text-xs uppercase tracking-wider text-brand">
        Local only
      </span>
      <p className="mt-1 text-muted">
        This page is part of the Lab and is never published. It holds work that is
        real but not yet a public claim. Promoting it is a deliberate move back
        into <code>content/docs/</code>.
      </p>
    </div>
  );
}

export default async function LabPage({
  params
}: {
  params: Promise<{ slug?: string[] }>;
}) {
  const { slug } = await params;

  if (!slug?.length) {
    const pages = walkMdx("lab");
    return (
      <div className="min-w-0">
        <h1 className="text-3xl font-semibold tracking-tight">The Lab</h1>
        <p className="mt-2 text-muted">
          Local-only working surface. Nothing here is published.
        </p>
        <Banner />
        <ul className="space-y-2">
          {pages.map((p) => (
            <li key={p.slug.join("/")}>
              <Link
                href={`/lab/${p.slug.join("/")}`}
                className="text-brand hover:text-fg"
              >
                {p.slug.join(" / ")}
              </Link>
            </li>
          ))}
        </ul>
        {pages.length === 0 ? (
          <p className="text-muted">No lab pages yet.</p>
        ) : null}
      </div>
    );
  }

  const filePath = resolveMdxPath("lab", slug);
  const { frontmatter, content } = await compileMdxFromFile(filePath);

  return (
    <div className="min-w-0">
      <Link href="/lab" className="text-sm text-muted hover:text-fg">
        &larr; The Lab
      </Link>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight">
        {frontmatter.title}
      </h1>
      {frontmatter.description ? (
        <p className="mt-2 text-muted">{frontmatter.description}</p>
      ) : null}
      <div className="mt-6">
        <Banner />
      </div>
      <Prose html={content} />
    </div>
  );
}
