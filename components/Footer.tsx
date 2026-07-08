import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border bg-bg/40">
      <div className="mx-auto w-full max-w-6xl px-4 py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-xl">
            <div className="font-semibold">x64base</div>
            <p className="mt-2 text-sm text-muted">
              A true 64-bit evolution of the xBase lineage. Born in 1993. Reimagined for 2026.
            </p>
            <p className="mt-4 text-xs text-muted">
              x64base®, xBase_64®, DotTalk++®, TupTalk®, TableTalk®, RelTalk®, Arctic®, and
              LabTalk® are trademarks of Derald R Grimwood Jr.
            </p>
            <div className="mt-4 flex flex-wrap gap-4 text-xs">
              <a
                href="https://github.com/deraldg/x64base"
                target="_blank"
                rel="noreferrer"
                className="text-muted hover:text-fg"
              >
                GitHub: x64base
              </a>
              <Link href="/docs/dev/selfdoc-website-publication" className="text-muted hover:text-fg">
                SelfDoc → Website
              </Link>
              <Link href="/about/contributors" className="text-muted hover:text-fg">
                Contributors
              </Link>
              <Link href="/licensing/third-party-acknowledgements" className="text-muted hover:text-fg">
                Third-party credits
              </Link>
              <Link href="/downloads" className="text-muted hover:text-fg">
                Downloads
              </Link>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
            <Link href="/docs" className="text-muted hover:text-fg">
              Documentation
            </Link>
            <Link href="/products" className="text-muted hover:text-fg">
              Products
            </Link>
            <Link href="/downloads" className="text-muted hover:text-fg">
              Downloads
            </Link>
            <Link href="/licensing" className="text-muted hover:text-fg">
              Licensing
            </Link>
            <Link href="/brand" className="text-muted hover:text-fg">
              Brand
            </Link>
            <Link href="/news" className="text-muted hover:text-fg">
              News
            </Link>
            <Link href="/contact" className="text-muted hover:text-fg">
              Contact
            </Link>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-2 border-t border-border pt-6 text-xs text-muted md:flex-row md:items-center md:justify-between">
          <span>© 1993–2026 Derald R Grimwood Jr. All rights reserved.</span>
          <span className="font-mono">DBF_64 • FPT64 • Indexing • Education-first</span>
        </div>
      </div>
    </footer>
  );
}
