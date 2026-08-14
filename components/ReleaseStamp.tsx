"use client";

import { useEffect, useState } from "react";

/**
 * The footer's release stamp -- this site's answer to a visitor counter.
 *
 * Owner direction 2026-08-13. A visitor counter needs a server to count on, and
 * this site is static with NO analytics and NO third-party scripts of any kind.
 * Adding one would have ended that, so the counter counts something the site can
 * honestly know about itself instead: how many times it has been published.
 *
 * The number comes from /artifacts/site-release.json, which the publish script
 * writes on every deploy. That file is on this domain, so reading it sends
 * nothing anywhere and sets no cookie -- the request goes to the same server
 * that served the page.
 *
 * Fetched at run time rather than baked in at build time for an ordering reason:
 * the build happens BEFORE the publish, so at build time the current release
 * number does not exist yet. Reading it live is what keeps the displayed number
 * from always being one behind.
 *
 * Renders nothing at all if the fetch fails. A footer ornament must never be a
 * reason a page looks broken.
 */
type Release = { release_number?: number; published_at_utc?: string };

export function ReleaseStamp() {
  const [rel, setRel] = useState<Release | null>(null);

  useEffect(() => {
    let alive = true;
    fetch("/artifacts/site-release.json", { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (alive && j) setRel(j as Release);
      })
      .catch(() => {
        /* silent: no counter is better than a broken footer */
      });
    return () => {
      alive = false;
    };
  }, []);

  if (!rel?.release_number) return null;

  const day = rel.published_at_utc ? rel.published_at_utc.slice(0, 10) : null;

  return (
    <span className="font-mono" title="Publishes of this site, counted from the deploy history. No visitor tracking.">
      release {rel.release_number}
      {day ? ` · ${day}` : ""}
    </span>
  );
}
