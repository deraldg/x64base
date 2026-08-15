"use client";

import { useEffect, useState } from "react";
import { goatcounterTotalUrl, visitorBadgeUrl } from "@/config/analytics";

/**
 * Site-wide visitor count for the footer, beside the release stamp.
 *
 * Renders NOTHING unless config/analytics.ts carries a GoatCounter code, and
 * nothing if the fetch fails. Same rule as ReleaseStamp: a footer ornament is
 * never a reason a page looks broken.
 *
 * Reads /counter/TOTAL.json, whose `count` is already a formatted string with
 * thousands separators, so no client-side number formatting is needed (and no
 * locale surprises). The endpoint 404s if "Allow adding visitor counts on your
 * website" is off in the GoatCounter site settings -- that switch defaults to
 * off, and a silent absence here is what a missed tick looks like.
 *
 * Deliberately NOT wired to the release stamp: two independent numbers, two
 * independent failure modes. Fusing them would mean one broken fetch hides
 * both, and the release stamp is the one that must never disappear -- it is
 * the honest number this site can compute about itself, and it survives
 * ad-blockers because it comes from our own domain.
 */
export function VisitorCount() {
  const [count, setCount] = useState<string | null>(null);
  const url = goatcounterTotalUrl();

  useEffect(() => {
    if (!url) return;
    let alive = true;
    fetch(url, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : null))
      .then((j) => {
        if (alive && j && typeof j.count === "string") setCount(j.count);
      })
      .catch(() => {
        /* blocked, offline, or the settings tick is off. Say nothing. */
      });
    return () => {
      alive = false;
    };
  }, [url]);

  if (count) {
    return (
      <span
        className="font-mono"
        title="Visits counted by GoatCounter: no cookies, no persistent identifier, no cross-site profile. Ad-blockers block it, so this is a floor rather than a total."
      >
        {count} visits
      </span>
    );
  }

  // No GoatCounter code, or its fetch failed: fall back to the badge image.
  // An <img> needs no JS to count, so this still works where a script would
  // not -- which is why it is the fallback rather than the other way round.
  const badge = visitorBadgeUrl();
  if (!badge) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={badge}
      alt="Visits to this site"
      height={20}
      className="inline-block h-5 w-auto align-middle"
      title="Counts page loads by IP. A rough gauge, not a session count, and a third party sees the request."
    />
  );
}
