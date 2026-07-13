import Link from "@/components/StaticLink";

export function Footer() {
  return (
    <footer className="border-t border-border bg-bg/40">
      <div className="mx-auto w-full max-w-6xl px-4 py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-xl">
            <div className="font-semibold">x64base</div>
            <p className="mt-2 text-sm text-muted">
              A modern 64-bit research evolution of the xBase lineage. Born in 1993. Reimagined for 2026.
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
              <Link href="/docs/dev/third-party-acknowledgements" className="text-muted hover:text-fg">
                Third-party credits
              </Link>
              <Link href="/downloads" className="text-muted hover:text-fg">
                Downloads
              </Link>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <Link href="/docs" className="text-muted hover:text-fg">
              Documentation
            </Link>
            <Link href="/products" className="text-muted hover:text-fg">
              Products
            </Link>
            <Link href="/downloads" className="text-muted hover:text-fg">
              Downloads
            </Link>
            <Link href="/news" className="text-muted hover:text-fg">
              News
            </Link>
            <Link href="/contact" className="text-muted hover:text-fg">
              Contact
            </Link>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-3 border-t border-border pt-6 text-xs text-muted md:flex-row md:items-center md:justify-between">
          <span>© 1993–2026 Derald R Grimwood Jr. All rights reserved.</span>
          <div className="flex flex-wrap gap-4">
            <Link href="/licensing" className="hover:text-fg">Project notice</Link>
            <Link href="/brand" className="hover:text-fg">Identity notes</Link>
            <span className="font-mono">DBF_64 • FPT64 • Indexing • Education-first</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
