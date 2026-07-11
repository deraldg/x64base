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
      { label: "Runtime Footprint", href: "/docs/engine/runtime-footprint" },
      { label: "xBase Ecosystem Context", href: "/docs/engine/xbase-ecosystem-context" },
      { label: "Ecosystem Feature Comparison", href: "/docs/engine/ecosystem-feature-comparison" },
      { label: "x64 Capacity Math", href: "/docs/engine/x64-capacity-math" },
      { label: "DBF Flavors and Index Defaults", href: "/docs/engine/dbf-flavors-and-indexes" },
      { label: "DBF_64 Specification", href: "/docs/engine/dbf-64-specification" },
      { label: "FPT64 Memo Format", href: "/docs/engine/fpt64-memo-format" },
      { label: "Indexing Rules", href: "/docs/engine/indexing-rules" },
      { label: "CDX and LMDB Indexing", href: "/docs/engine/cdx-lmdb-indexing" },
      { label: "Engine Feature Crosswalk", href: "/docs/engine/feature-crosswalk" },
      { label: "Error Codes", href: "/docs/engine/error-codes" },
      { label: "API Reference", href: "/docs/engine/api-reference" }
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
      { label: "Parallel GUI/TUI", href: "/docs/talk-family/parallel-gui-tui" },
      { label: "Arctic TUI", href: "/docs/talk-family/arctic" }
    ]
  },
  {
    label: "Laboratory Campus",
    items: [
      { label: "Overview", href: "/docs/labtalk/overview" },
      { label: "Cases and Storyboard", href: "/docs/labtalk/cases-storyboard" },
      { label: "Database Evolution Path", href: "/docs/labtalk/database-evolution" },
      { label: "Education Features", href: "/docs/labtalk/education-features" },
      { label: "Lesson Platform", href: "/docs/labtalk/lessons" },
      { label: "LMS Communications Lane", href: "/docs/labtalk/lms-integration-lane" },
      { label: "Student Lessons", href: "/docs/labtalk/student-lessons" },
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
      { label: "Current Work Lanes", href: "/docs/dev/current-lanes" },
      { label: "Site Improvement Plan", href: "/docs/dev/site-improvement-plan" },
      { label: "Important Documents", href: "/docs/dev/important-documents" },
      { label: "Website Documentation Matrix", href: "/docs/dev/website-documentation-matrix" },
      { label: "Historical Source Lineage", href: "/docs/dev/historical-source-lineage" },
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
      { label: "Experimental Work", href: "/docs/dev/experimental" }
    ]
  }
];

export function flattenSidebar(groups: SidebarGroup[]) {
  return groups.flatMap((g) => g.items);
}
