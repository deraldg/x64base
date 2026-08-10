import type { Metadata } from "next";
import Image from "next/image";
import Link from "@/components/StaticLink";
import { ArrowRight, Database, GitBranch, Layers3 } from "lucide-react";

export const metadata: Metadata = {
  title: "Database Schema Catalog",
  description:
    "A public catalog of Cascade ERP, MCC, HELP, metadata, governance, documentation, and teaching database schemas.",
};

const groups = [
  {
    name: "Finance",
    tables: ["GL_Accounts", "GL_Journal", "AP_Invoices", "AP_Payments", "AR_Invoices", "AR_Payments"],
  },
  {
    name: "Sales",
    tables: ["Customers", "Sales_Orders", "SO_Lines", "Price_Lists", "Shipments", "Shipment_Lines"],
  },
  {
    name: "Procurement",
    tables: ["Vendors", "Vendor_Items", "Purchase_Orders", "PO_Lines", "Receiving"],
  },
  {
    name: "Inventory",
    tables: ["Items", "Warehouses", "Stock_Levels", "Inventory_Movements"],
  },
  {
    name: "Manufacturing",
    tables: ["BOM_Headers", "BOM_Details", "Routings", "Work_Centers", "Work_Orders", "WO_Operations", "WO_Materials"],
  },
  { name: "Quality", tables: ["Quality_Tests", "Quality_Results"] },
  {
    name: "People",
    tables: ["Departments", "Employees", "Payroll_Runs", "Time_Cards"],
  },
];

const views = [
  "v_AP_Aging",
  "v_AR_Aging",
  "v_Available_Stock",
  "v_BOM_Explosion",
  "v_Open_Sales_Orders",
  "v_Reorder_Alert",
  "v_Three_Way_Match",
  "v_Trial_Balance",
  "v_Work_Order_Status",
];

const schemaFamilies = [
  {
    category: "Education and reference",
    families: [
      { name: "MCC x64", count: "13 tables", carrier: "X64 DBF", role: "Primary x64 education dataset" },
      { name: "MCC x32", count: "13 tables", carrier: "classic DBF", role: "Traditional xBase comparison dataset" },
      { name: "MCC VFP", count: "12 tables", carrier: "VFP DBF", role: "Visual FoxPro interoperability set" },
      { name: "MCC original", count: "12 tables", carrier: "reference DBF", role: "Original/reference teaching copy" },
      { name: "Bible x64", count: "13 tables", carrier: "SQLite 3", role: "Packaged scripture teaching database" },
      { name: "Pinocchio", count: "2 tables", carrier: "X64 DBF", role: "Scale and navigation benchmark fixture" },
    ],
  },
  {
    category: "Runtime and governance",
    families: [
      { name: "HELP", count: "10 live + 6 V32", carrier: "DBF + memo", role: "Commands, topics, sections, and localization" },
      { name: "Runtime metadata", count: "8 tables", carrier: "DBF", role: "Commands, functions, arguments, messages, and fields" },
      { name: "Identity / RBAC", count: "9 tables", carrier: "DBF", role: "Members, roles, permissions, grants, and assignments" },
      { name: "AI-BBS", count: "3 tables", carrier: "DBF", role: "Boards, threads, and posts" },
      { name: "AI Portal tracking", count: "5 tables", carrier: "DBF", role: "Lanes, runs, proofs, tasks, and crosswalks" },
      { name: "Data dictionary", count: "17 tables", carrier: "DBF", role: "Objects, evidence, relations, gates, and run records" },
    ],
  },
  {
    category: "Documentation and language",
    families: [
      { name: "Source comments", count: "8 tables", carrier: "DBF", role: "Files, lines, classes, usages, aliases, and memo lines" },
      { name: "Manual assembly", count: "8 tables", carrier: "DBF", role: "Runs, sections, review, publication, media, and anchors" },
      { name: "Messaging", count: "2 tables", carrier: "DBF", role: "Message identity and localized text" },
      { name: "Locale", count: "2 tables", carrier: "DBF", role: "Locales and fallback rules" },
    ],
  },
  {
    category: "Applications and fixtures",
    families: [
      { name: "PyCRUD demo", count: "4 tables", carrier: "SQLite 3", role: "Small CRUD teaching application" },
      { name: "Memo and dialect fixtures", count: "14 tables", carrier: "DBF / DBT / FPT", role: "Memo-format and dialect interoperability" },
      { name: "Sandbox and probes", count: "50 tables", carrier: "generated DBF", role: "Disposable regression and parser surfaces" },
    ],
  },
];

export default function SchemasPage() {
  return (
    <div className="space-y-12">
      <header className="max-w-4xl border-b border-border pb-8">
        <p className="font-mono text-xs uppercase tracking-[0.24em] text-brand">database schema catalog</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight md:text-4xl">
          The database ecology, family by family.
        </h1>
        <p className="mt-4 leading-7 text-muted">
          Cascade ERP is one governed teaching system, not the whole estate. This page also catalogs
          the MCC datasets, HELP, runtime metadata, identity and AI stores, DataDict, documentation
          catalogs, localization tables, applications, and fixtures. Counts are measured local
          snapshots; they describe schema families rather than claiming every replica is a separate
          logical database.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link href="/docs/labtalk/database-evolution" className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline">
            Database evolution lesson <ArrowRight size={14} aria-hidden="true" />
          </Link>
          <Link href="/docs/engine/architecture" className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline">
            Engine architecture <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
      </header>

      <section>
        <p className="font-mono text-xs uppercase tracking-[0.22em] text-brand">featured relational system</p>
        <h2 className="mt-2 text-3xl font-semibold tracking-tight">Cascade ERP dual-carrier schema</h2>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          ["34", "relational tables", Database],
          ["58", "foreign-key field edges", GitBranch],
          ["9", "analytical views", Layers3],
        ].map(([value, label, Icon]) => {
          const MetricIcon = Icon as typeof Database;
          return (
            <div key={String(label)} className="rounded-lg border border-border bg-card/60 p-5">
              <MetricIcon className="h-5 w-5 text-brand" aria-hidden="true" />
              <div className="mt-4 font-mono text-3xl text-fg">{String(value)}</div>
              <div className="mt-1 text-sm text-muted">{String(label)}</div>
            </div>
          );
        })}
      </section>

      <section className="space-y-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-brand">Mermaid -&gt; SVG</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">Relational schema by working module</h2>
          <p className="mt-3 max-w-4xl leading-7 text-muted">
            This readable system map names every table and shows the principal cross-module paths.
            Field-level foreign keys remain in the governed dual-schema contract; the public map
            avoids turning a 58-edge schema into an unreadable wall of lines.
          </p>
        </div>
        <a href="/images/schemas/cascade-erp-module-schema-v1.svg" className="block overflow-auto rounded-lg border border-border bg-card/35 p-3">
          <Image
            src="/images/schemas/cascade-erp-module-schema-v1.svg"
            alt="Cascade ERP tables grouped into finance, sales, procurement, inventory, manufacturing, quality, and people modules"
            width={1800}
            height={1100}
            className="min-h-[520px] w-full min-w-[900px] object-contain"
          />
        </a>
      </section>

      <section className="space-y-5">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-brand">carrier contract</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">SQLite authority and x64base mirror</h2>
          <p className="mt-3 max-w-4xl leading-7 text-muted">
            Structural parity is visible without claiming identical native capabilities. SQLite
            retains relational enforcement and view SQL. The x64base side provides inspectable DBF
            projections and snapshots, while sidecars preserve the semantics that DBF cannot enforce.
          </p>
        </div>
        <a href="/images/schemas/cascade-dual-carrier-schema-v1.svg" className="block overflow-auto rounded-lg border border-border bg-card/35 p-3">
          <Image
            src="/images/schemas/cascade-dual-carrier-schema-v1.svg"
            alt="Read-only SQLite schema inspection flowing through the dual-carrier contract into x64base DBF projections and sidecars"
            width={1600}
            height={900}
            className="min-h-[420px] w-full min-w-[760px] object-contain"
          />
        </a>
      </section>

      <section>
        <h2 className="text-3xl font-semibold tracking-tight">All 34 tables</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <div key={group.name} className="rounded-lg border border-border bg-card/50 p-5">
              <h3 className="font-semibold text-fg">{group.name}</h3>
              <ul className="mt-3 space-y-1 font-mono text-xs leading-5 text-muted">
                {group.tables.map((table) => <li key={table}>{table}</li>)}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-border bg-card/45 p-6">
        <h2 className="text-2xl font-semibold tracking-tight">Nine analytical views</h2>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {views.map((view) => (
            <div key={view} className="rounded-md border border-border bg-bg/30 px-3 py-2 font-mono text-xs text-muted">
              {view}
            </div>
          ))}
        </div>
        <p className="mt-5 text-sm leading-6 text-muted">
          In SQLite these remain executable views. In the x64base teaching mirror they are labeled
          materialized snapshots, not silently presented as live relational views.
        </p>
      </section>

      <section className="space-y-6 border-t border-border pt-10">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-brand">other database schemas</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">MCC, HELP, metadata, and the rest of the teaching system</h2>
          <p className="mt-3 max-w-4xl leading-7 text-muted">
            These are first-class schema families, not footnotes to Cascade. The map separates
            educational datasets, operational catalogs, documentation systems, and disposable
            fixtures so a learner can see both the data and its purpose.
          </p>
        </div>
        <a href="/images/schemas/database-ecology-schema-catalog-v1.svg" className="block overflow-auto rounded-lg border border-border bg-card/35 p-3">
          <Image
            src="/images/schemas/database-ecology-schema-catalog-v1.svg"
            alt="Database schema catalog showing MCC, HELP, metadata, identity, AI-BBS, AI Portal, DataDict, documentation, locale, application, and fixture families"
            width={1800}
            height={1150}
            className="min-h-[520px] w-full min-w-[900px] object-contain"
          />
        </a>
        <div className="space-y-8">
          {schemaFamilies.map((group) => (
            <div key={group.category}>
              <h3 className="font-mono text-sm uppercase tracking-[0.16em] text-orange">{group.category}</h3>
              <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {group.families.map((family) => (
                  <article key={family.name} className="rounded-lg border border-border bg-card/50 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <h4 className="font-semibold text-fg">{family.name}</h4>
                      <span className="whitespace-nowrap rounded-full border border-border px-2 py-1 font-mono text-[10px] text-brand">
                        {family.count}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-6 text-muted">{family.role}</p>
                    <p className="mt-3 font-mono text-[11px] text-muted">carrier: {family.carrier}</p>
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="rounded-lg border border-border bg-bg/30 p-5 text-sm leading-6 text-muted">
          <strong className="text-fg">Index boundary:</strong> LMDB environments, CDX, and CNX are
          derived index carriers. They are inventoried and governed, but they are not promoted here
          as independent table schemas. Backups, proof copies, and browser-profile SQLite files are
          likewise excluded from the logical schema catalog.
        </div>
      </section>
    </div>
  );
}
