import { Card } from "@/components/Card";

const products = [
  { slug: "x64base-engine", title: "x64base Engine", description: "DBF runtime, x64-family tables, indexes, memos, work areas." },
  { slug: "dottalk", title: "DotTalk++", description: "Canonical command shell, scripting surface, and teaching runtime." },
  { slug: "tuptalk", title: "TupTalk", description: "Tuple-facing record views, projections, export, validation, and relation-aware row output." },
  { slug: "tabletalk", title: "TableTalk", description: "Table, field, work-area, order, cursor, and browser inspection workflows." },
  { slug: "reltalk", title: "RelTalk", description: "Relation graphs, asymmetric links, workspace persistence, and ERSATZ traversal." },
  { slug: "arctictalk", title: "ArcticTalk", description: "Public front-end umbrella for GUI, TUI, shell-bridge, and repeatable maintenance lanes." },
  { slug: "labtalk", title: "LabTalk", description: "Laboratory campus for DotTalk++, x64base, lessons, and proof-aware learning." }
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
