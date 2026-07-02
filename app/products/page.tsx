import { Card } from "@/components/Card";

const products = [
  { slug: "x64base-engine", title: "x64base Engine", description: "DBF runtime, x64-family tables, indexes, memos, work areas." },
  { slug: "dottalk", title: "DotTalk++", description: "Canonical command shell, scripting surface, and teaching runtime." },
  { slug: "tuptalk", title: "TupTalk", description: "Tuple-facing inspection and relation-aware output workflows." },
  { slug: "tabletalk", title: "TableTalk", description: "Table, schema, work-area, and browser inspection concepts." },
  { slug: "reltalk", title: "RelTalk", description: "Relation graphs, asymmetric joins, workspace state, and ERSATZ." },
  { slug: "turbotalk", title: "TurboTalk", description: "Repeatable maintenance, smoke, indexing, and validation workflows." },
  { slug: "labtalk", title: "LabTalk", description: "Educational lab framing for DotTalk++ / x64base." }
];

export default function ProductsPage() {
  return (
    <div className="space-y-8">
      <header className="max-w-2xl space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">Products</h1>
        <p className="text-muted">
          These pages name the major workflows in the local DotTalk++ / x64base runtime. Some are
          runtime-proven, some are active beta, and some are still canary or integration surfaces.
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
