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
 * AMENDED 2026-08-14. The sentence above stopped being unconditionally true.
 * The owner asked for an actual visitor counter after emailing Xbase++, Harbour
 * and LMDB, which is a fair thing to want to measure, so GoatCounter was wired
 * in behind config/analytics.ts. It is OFF until a code is set there, so the
 * paragraph above still describes the shipped default -- but it is now a
 * setting, not a property of the site, and pretending otherwise would make this
 * comment the sort of stale claim this project keeps correcting.
 *
 * The two numbers stay SEPARATE on purpose. This one is computed from our own
 * deploy history, served from our own domain, and no blocker can touch it. The
 * visitor count comes from a third party that a large share of this site's
 * audience blocks. They sit side by side in the footer and they are not the
 * same kind of fact: one is exact, the other is a floor.
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
 *
 * The 0 case is deliberate and is NOT the same as the failure case. public/
 * carries a committed seed with release_number 0, so `next dev` shows
 * "release dev" rather than the nothing it used to show. Before that seed
 * existed, local rendered blank while production rendered a number, and the
 * component reported neither -- the two surfaces disagreed silently. Worse, a
 * missing artifact IN PRODUCTION would have looked exactly like localhost:
 * no error, no gap, just absence. The publish script now verifies the live
 * file after pushing, because that blindness cannot be fixed from in here.
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

  // A number we could not read at all -> render nothing, as before.
  // A number we read as 0 -> the dev seed; say so out loud.
  if (rel === null || typeof rel.release_number !== "number") return null;

  const isDev = rel.release_number === 0;
  const day = rel.published_at_utc ? rel.published_at_utc.slice(0, 10) : null;

  return (
    <span className="font-mono" title="Publishes of this site, counted from the deploy history. Not a visitor count -- this site has no analytics and no third-party scripts.">
      release {isDev ? "dev" : rel.release_number}
      {day ? ` · ${day}` : ""}
    </span>
  );
}
