export type SidebarGroup = {
  label: string;
  items: { label: string; href: string }[];
};

export const docsSidebar: SidebarGroup[] = [
  {
    label: "Getting Started",
    items: [
      { label: "Overview", href: "/docs/getting-started/overview" },
      { label: "Installation", href: "/docs/getting-started/installation" },
      { label: "Quickstart", href: "/docs/getting-started/quickstart" },
      { label: "FAQ", href: "/docs/getting-started/faq" }
    ]
  },
  {
    label: "x64base Engine",
    items: [
      { label: "Architecture", href: "/docs/engine/architecture" },
      { label: "Engine Specifications", href: "/docs/engine/specifications" },
      { label: "Proven Capabilities", href: "/docs/engine/proven-capabilities" },
      { label: "ACID and the Glass-Box Engine", href: "/docs/engine/acid-and-glass-box" },
      { label: "Runtime Footprint", href: "/docs/engine/runtime-footprint" },
      { label: "xBase Ecosystem Context", href: "/docs/engine/xbase-ecosystem-context" },
      { label: "Ecosystem Feature Comparison", href: "/docs/engine/ecosystem-feature-comparison" },
      { label: "x64 Capacity Math", href: "/docs/engine/x64-capacity-math" },
      { label: "DBF Flavors and Index Defaults", href: "/docs/engine/dbf-flavors-and-indexes" },
      { label: "DBF_64 Specification", href: "/docs/engine/dbf-64-specification" },
      { label: "FPT64 Memo Format", href: "/docs/engine/fpt64-memo-format" },
      { label: "RAM DBF and VDISK", href: "/docs/engine/ram-dbf-vdisk" },
      { label: "Workspaces", href: "/docs/engine/workspaces" },
      { label: "Indexing Rules", href: "/docs/engine/indexing-rules" },
      { label: "CDX and LMDB Indexing", href: "/docs/engine/cdx-lmdb-indexing" },
      { label: "Pinocchio Benchmarks", href: "/docs/engine/pinocchio-benchmarks" },
      { label: "Regression & Proof Testing", href: "/docs/engine/regression-and-proof-testing" },
      { label: "Engine Feature Crosswalk", href: "/docs/engine/feature-crosswalk" },
      { label: "SQLsel and SQL Conformance", href: "/docs/engine/sqlsel-and-sql-conformance" },
      { label: "Error Codes", href: "/docs/engine/error-codes" },
      { label: "Messaging & Localization", href: "/docs/engine/messaging-and-localization" },
      { label: "Identity, Authentication & RBAC", href: "/docs/engine/identity-security" },
      { label: "API Reference", href: "/docs/engine/api-reference" },
      { label: "Python Integration", href: "/docs/engine/python-integration" }
    ]
  },
  {
    label: "DotTalk++",
    items: [
      { label: "Language Guide", href: "/docs/dottalk/language-guide" },
      { label: "DotScript Language Guide", href: "/docs/dottalk/dotscript-language-guide" },
      { label: "SET Family", href: "/docs/dottalk/set-family" },
      { label: "Command Families", href: "/docs/dottalk/command-families" },
      { label: "Data Mutators", href: "/docs/dottalk/data-mutators" },
      { label: "Syntax", href: "/docs/dottalk/syntax" },
      { label: "REPL", href: "/docs/dottalk/repl" },
      { label: "Command Catalog", href: "/docs/dottalk/command-catalog" },
      { label: "Command Reference", href: "/docs/dottalk/command-reference" },
      { label: "Function Catalog", href: "/docs/dottalk/function-catalog" },
      { label: "Examples", href: "/docs/dottalk/examples" },
      { label: "Curriculum", href: "/docs/dottalk/curriculum" }
    ]
  },
  {
    label: "DotTalk++ Workbench",
    items: [
      { label: "TupTalk", href: "/docs/talk-family/tuptalk" },
      { label: "TableTalk", href: "/docs/talk-family/tabletalk" },
      { label: "RelTalk", href: "/docs/talk-family/reltalk" },
      { label: "SQLsel", href: "/docs/talk-family/sqlsel" },
      { label: "Parallel GUI/TUI", href: "/docs/talk-family/parallel-gui-tui" },
      { label: "Arctic TUI", href: "/docs/talk-family/arctic" }
    ]
  },
  {
    label: "Laboratory Campus",
    items: [
      { label: "Academic Start Here", href: "/docs/labtalk/academic-start" },
      { label: "Overview", href: "/docs/labtalk/overview" },
      { label: "AI Portal — Alpha/Experimental", href: "/docs/labtalk/ai-portal" },
      { label: "AI Agent Sync -- Snapshot", href: "/docs/labtalk/agent-sync" },
      { label: "Current Tasks & Projects", href: "/docs/labtalk/current-work" },
      { label: "Cases and Storyboard", href: "/docs/labtalk/cases-storyboard" },
      { label: "Database Evolution Path", href: "/docs/labtalk/database-evolution" },
      { label: "Education Features", href: "/docs/labtalk/education-features" },
      { label: "Lesson Platform", href: "/docs/labtalk/lessons" },
      { label: "LMS Communications Lane", href: "/docs/labtalk/lms-integration-lane" },
      { label: "Student Lessons", href: "/docs/labtalk/student-lessons" },
      { label: "Guided Lesson: Records, Fields, Tables", href: "/docs/labtalk/lesson-records-fields-tables" },
      { label: "Career Lessons", href: "/docs/labtalk/career-lessons" },
      { label: "Suggest a Lesson", href: "/docs/labtalk/suggest-a-lesson" },
      { label: "Runtime Evidence Gallery", href: "/docs/labtalk/runtime-evidence" },
      { label: "SelfDoc Lane Diagrams", href: "/docs/labtalk/selfdoc-lane" },
      { label: "Non-Profit Guide", href: "/docs/labtalk/non-profit-guide" },
      { label: "Examples", href: "/docs/labtalk/examples" },
      { label: "Academic Positioning", href: "/docs/labtalk/academic-positioning" }
    ]
  },
  {
    label: "Developer Resources",
    items: [
      { label: "Current Project Truth", href: "/docs/dev/project-truth" },
      { label: "Recursive Co-development", href: "/docs/dev/recursive-co-development" },
      { label: "Current Work Lanes", href: "/docs/dev/current-lanes" },
      { label: "Roadmap", href: "/docs/dev/roadmap" },
      { label: "Developer Manual (Assembled)", href: "/docs/dev/developer-manual" },
      { label: "How the Manual Assembles Itself", href: "/docs/dev/manual-assembly" },
      { label: "Documentation Progress", href: "/docs/dev/documentation-progress" },
      { label: "Full-stack Documentation Push", href: "/docs/dev/full-stack-documentation-push" },
      { label: "Site Improvement Plan", href: "/docs/dev/site-improvement-plan" },
      { label: "Important Documents", href: "/docs/dev/important-documents" },
      { label: "Website Documentation Matrix", href: "/docs/dev/website-documentation-matrix" },
      { label: "Coined Vocabulary (Glossary)", href: "/docs/dev/coined-vocabulary" },
      { label: "Historical Source Lineage", href: "/docs/dev/historical-source-lineage" },
      { label: "Historical Family Tree", href: "/docs/dev/historical-family-tree" },
      { label: "Historical Source Files", href: "/docs/dev/historical-source-files" },
      { label: "Application UI DSL Lane", href: "/docs/dev/application-ui-dsl-lane" },
      { label: "Developer Profile", href: "/docs/dev/developer-profile" },
      { label: "Developer Handbook", href: "/docs/dev/developer-handbook" },
      { label: "SelfDoc Website Publication", href: "/docs/dev/selfdoc-website-publication" },
      { label: "Public Site Architecture", href: "/docs/dev/public-site-architecture" },
      { label: "SelfDoc Feed Pipeline", href: "/docs/dev/selfdoc-feed-pipeline" },
      { label: "HELP / Message / SelfDoc DFD", href: "/docs/dev/help-message-selfdoc-dfd" },
      { label: "Onboarding Guide", href: "/docs/dev/onboarding-guide" },
      { label: "Naming Conventions", href: "/docs/dev/naming-conventions" },
      { label: "Coding Standards", href: "/docs/dev/coding-standards" },
      { label: "Contribution Guide", href: "/docs/dev/contribution-guide" },
      // "Experimental Work" moved to the local-only Lab on 2026-08-17
      // (/lab/experimental). Leaving the entry here would have published a
      // sidebar link to a route the stripper deletes -- a 404 for every
      // visitor, which is worse than either publishing it or hiding it.
    ]
  }
];

export function flattenSidebar(groups: SidebarGroup[]) {
  return groups.flatMap((g) => g.items);
}
