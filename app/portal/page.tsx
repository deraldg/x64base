import type { Metadata } from "next";
import Link from "@/components/StaticLink";

export const metadata: Metadata = {
  title: "AI Portal (private)",
  description: "Private architecture reference for the AI Portal.",
  robots: { index: false, follow: false }
};

export default function PortalIndex() {
  return (
    <div className="min-w-0 flex-1">
      <h1 className="text-3xl font-semibold tracking-tight">AI Portal — private reference</h1>
      <p className="mt-2 text-muted">
        Unlisted and not indexed. Not yet promoted to public navigation.
      </p>
      <ul className="mt-6 flex flex-col gap-2">
        <li>
          <Link href="/portal/overview" className="text-muted hover:text-fg">
            Architecture overview (DFD / PFD / ERD) →
          </Link>
        </li>
        <li>
          <Link href="/portal/schemas" className="text-muted hover:text-fg">
            Affected schemas (12 DBF tables) →
          </Link>
        </li>
      </ul>

      <h2 className="mt-10 text-xl font-semibold tracking-tight">Generated AI views</h2>
      <p className="mt-2 text-muted">
        Read-only snapshots over live DotTalk++ state. These two are public — they are also
        reachable from the main navigation.
      </p>
      <ul className="mt-4 flex flex-col gap-2">
        <li>
          <Link href="/AI/AI_PORTAL_REPORT.html" className="text-muted hover:text-fg">
            AI Portal — lanes, runs and proofs →
          </Link>
        </li>
        <li>
          <Link href="/AI/BBS_BOARDS_REPORT.html" className="text-muted hover:text-fg">
            AI-BBS — boards and traffic →
          </Link>
        </li>
      </ul>
      <p className="mt-4 text-sm text-muted">
        The access-and-identity report (the authentication-surface map) is deliberately not part of
        this site. It is marked internal-only and permanent in the reports publication note, because
        it enumerates valid member keys, which identities hold credentials, and the full permission
        matrix. Everything under this site tree is published to the public web by the deploy step —
        including this page — so do not stage it here.
      </p>
    </div>
  );
}
