import fs from "node:fs";
import matter from "gray-matter";
import { Card } from "@/components/Card";
import { walkMdx } from "@/lib/content";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Products",
  description:
    "The major workflows in the local DotTalk++ and x64base runtime: engine, shell, DotScript, tuple and relation views, SQLsel, and the Laboratory Campus."
};

// This list is DERIVED from content/products/*.mdx, not hand-maintained.
//
// It used to be a hardcoded array, and on 2026-08-13 the owner noticed MemoTalk
// missing from this page while its product page worked fine. Measured: THREE
// products were unreachable from here -- arctictalk, memotalk and turbotalk --
// each with an .mdx file and a live route, and none of them listed. Two had been
// invisible long enough that nobody remembered adding them.
//
// A hand-typed index of files that already exist can only ever fall behind, and
// it fails silently: the page renders perfectly, just short. Deriving it means a
// new product page CANNOT be invisible here.
//
// ORDER is still curated, because alphabetical would open the page on ArcticTalk
// rather than the engine. Anything not named in ORDER is appended alphabetically
// instead of dropped -- the omission that started this could not happen again.
const ORDER = [
  "x64base-engine",
  "dottalk",
  "dotscript",
  "memotalk",
  "tuptalk",
  "tabletalk",
  "reltalk",
  "sqlsel",
  "parallel-gui-tui",
  "arctictalk",
  "turbotalk",
  "labtalk"
];

type ProductCard = { slug: string; title: string; description: string };

function loadProducts(): ProductCard[] {
  const found: ProductCard[] = walkMdx("products").map((r) => {
    const fm = matter(fs.readFileSync(r.filePath, "utf8")).data as {
      title?: string;
      description?: string;
    };
    const slug = r.slug[0];
    return {
      slug,
      title: fm.title ?? slug,
      description: fm.description ?? ""
    };
  });

  const rank = (s: string) => {
    const i = ORDER.indexOf(s);
    return i === -1 ? ORDER.length : i;
  };
  return found.sort(
    (a, b) => rank(a.slug) - rank(b.slug) || a.slug.localeCompare(b.slug)
  );
}

const products = loadProducts();

export default function ProductsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Products</h1>
        <p className="text-muted">
          These pages name the major workflows in the local DotTalk++ / x64base runtime. Some are
          runtime-proven, some are active beta, and some are still canary or integration surfaces.
        </p>
        <p className="text-muted">
          Canonical public source:{" "}
          <a
            href="https://github.com/deraldg/x64base"
            target="_blank"
            rel="noreferrer"
            className="font-medium text-fg underline underline-offset-4"
          >
            github.com/deraldg/x64base
          </a>
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        {products.map((p) => (
          <Card key={p.slug} title={p.title} description={p.description} href={`/products/${p.slug}`} />
        ))}
      </div>
    </div>
  );
}
