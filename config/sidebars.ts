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
      { label: "DBF_64 Specification", href: "/docs/engine/dbf-64-specification" },
      { label: "FPT64 Memo Format", href: "/docs/engine/fpt64-memo-format" },
      { label: "Indexing Rules", href: "/docs/engine/indexing-rules" },
      { label: "Error Codes", href: "/docs/engine/error-codes" },
      { label: "API Reference", href: "/docs/engine/api-reference" }
    ]
  },
  {
    label: "DotTalk++",
    items: [
      { label: "Language Guide", href: "/docs/dottalk/language-guide" },
      { label: "Syntax", href: "/docs/dottalk/syntax" },
      { label: "REPL", href: "/docs/dottalk/repl" },
      { label: "Examples", href: "/docs/dottalk/examples" },
      { label: "Curriculum", href: "/docs/dottalk/curriculum" }
    ]
  },
  {
    label: "Talk Family",
    items: [
      { label: "TupTalk", href: "/docs/talk-family/tuptalk" },
      { label: "TableTalk", href: "/docs/talk-family/tabletalk" },
      { label: "RelTalk", href: "/docs/talk-family/reltalk" },
      { label: "TurboTalk", href: "/docs/talk-family/turbotalk" }
    ]
  },
  {
    label: "LabTalk",
    items: [
      { label: "Overview", href: "/docs/labtalk/overview" },
      { label: "Non-Profit Guide", href: "/docs/labtalk/non-profit-guide" },
      { label: "Examples", href: "/docs/labtalk/examples" }
    ]
  },
  {
    label: "Developer Resources",
    items: [
      { label: "Current Project Truth", href: "/docs/dev/project-truth" },
      { label: "Developer Handbook", href: "/docs/dev/developer-handbook" },
      { label: "Onboarding Guide", href: "/docs/dev/onboarding-guide" },
      { label: "Coding Standards", href: "/docs/dev/coding-standards" },
      { label: "Contribution Guide", href: "/docs/dev/contribution-guide" }
    ]
  }
];

export function flattenSidebar(groups: SidebarGroup[]) {
  return groups.flatMap((g) => g.items);
}
