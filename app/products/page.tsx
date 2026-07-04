import { Card } from "@/components/Card";

const products = [
  { slug: "x64base-engine", title: "x64base Engine", description: "DBF runtime, x64-family tables, indexes, memos, work areas." },
  { slug: "dottalk", title: "DotTalk++", description: "Canonical command shell, scripting surface, and teaching runtime." },
  { slug: "dotscript", title: "DotScript", description: "Script language for repeatable command files, loops, variables, comments, and automation." },
  { slug: "tuptalk", title: "TupTalk", description: "Tuple-facing record views, projections, export, validation, and relation-aware row output." },
  { slug: "tabletalk", title: "TableTalk", description: "Table buffering, dirty/stale state, commit/rollback, and buffered mutation workflows." },
  { slug: "reltalk", title: "RelTalk", description: "Relation graphs, asymmetric links, workspace persistence, and ERSATZ traversal." },
  { slug: "parallel-gui-tui", title: "Parallel GUI/TUI", description: "DotTalk++ Workbench lane for keeping graphical and terminal surfaces aligned over the same engine services." },
  { slug: "labtalk", title: "Laboratory Campus", description: "Alpha collaboration campus for planning, in-development labs, and existing x64base/DotTalk++ learning evidence." }
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
