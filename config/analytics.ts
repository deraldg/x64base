/**
 * GoatCounter visitor counting. ONE switch: set the code below.
 *
 * Empty string = nothing happens. No script, no pixel, no request, no counter
 * in the footer -- the site stays byte-for-byte as it was. That is deliberate:
 * the whole feature is off until the owner turns it on, so this can be
 * committed and reviewed without changing what visitors get.
 *
 * TO ENABLE
 *   1. Create a free site at https://www.goatcounter.com/ and pick a code.
 *      The code is the subdomain: code "x64base" -> x64base.goatcounter.com
 *   2. In that site's Settings, tick "Allow adding visitor counts on your
 *      website". It defaults to OFF, and without it the footer counter reads
 *      nothing -- the count endpoint refuses to answer. This is the step that
 *      is easy to miss, because everything else works without it.
 *   3. Put the code below and republish.
 *
 * WHAT THIS COSTS, stated plainly because it reverses a prior decision.
 * ReleaseStamp.tsx has said since 2026-08-13 that this site carries NO
 * analytics and NO third-party scripts of any kind. Setting a code here makes
 * that false: visitors' browsers will contact goatcounter.com. GoatCounter
 * sets no cookies, keeps no persistent identifier, and salts+rotates its
 * visitor hash every 8 hours, so it cannot build a profile or follow anyone
 * between sites -- but it is still a third party learning which page was read.
 * That comment has been corrected rather than left to rot; see ReleaseStamp.
 *
 * WHAT THE NUMBER IS WORTH. Ad-blockers block the goatcounter.com domain
 * outright, which kills the script AND the no-script pixel together. This
 * site's audience is Harbour, Xbase++ and LMDB developers -- close to the
 * highest blocker-penetration population on the internet. Treat the number as
 * a FLOOR, never a total, and never quote it as evidence of anything.
 */
export const GOATCOUNTER_CODE = "";

/**
 * No-account fallback: VisitorBadgeReloaded, an <img> badge that counts and
 * displays in one request. Set to "" to remove it entirely.
 *
 * This exists because the owner asked for a visitor counter four times and got
 * homework instead. GoatCounter above is the better instrument -- referrers,
 * per-page reads, a real dashboard -- but it needs an account, and an account
 * is not something an agent can create. This needs nothing: it works the moment
 * it ships. Verified live 2026-08-14 (rendered "visits | 1").
 *
 * Trade-offs, plainly:
 *  - It is an <img>, so it counts visitors with JavaScript disabled, and it
 *    keeps working if the JS bundle fails. That is more robust than a script.
 *  - A third party (laobi.icu) sees visitor IPs. GoatCounter salts and discards
 *    them; this service makes no such promise. It is the weaker privacy choice.
 *  - Free badge services die. jwenjian/visitor-badge, the most popular one, is
 *    already dead. If the footer count vanishes one day, this is why, and the
 *    fix is to blank this line.
 *  - It counts page loads by IP+page, not sessions. Treat it as a rough gauge.
 *
 * If both this and GOATCOUNTER_CODE are set, GoatCounter wins -- one counter in
 * the footer, not two.
 */
export const VISITOR_BADGE_PAGE_ID = "x64base.com";

/** The badge image URL, or "" when unconfigured. */
export function visitorBadgeUrl(): string {
  if (!VISITOR_BADGE_PAGE_ID) return "";
  const q = new URLSearchParams({
    page_id: VISITOR_BADGE_PAGE_ID,
    left_text: "visits",
  });
  return `https://visitor-badge.laobi.icu/badge?${q.toString()}`;
}

/** Endpoint that records a pageview. Empty when unconfigured. */
export function goatcounterEndpoint(): string {
  return GOATCOUNTER_CODE ? `https://${GOATCOUNTER_CODE}.goatcounter.com/count` : "";
}

/**
 * Site-wide total. "TOTAL" is a GoatCounter special path -- case-sensitive,
 * no leading slash -- documented at /help/visitor-counter. Returns JSON
 * { count: "1,234" }, already formatted with thousands separators.
 * Responses are cached up to four hours, so a fresh visit is not instant.
 */
export function goatcounterTotalUrl(): string {
  return GOATCOUNTER_CODE ? `https://${GOATCOUNTER_CODE}.goatcounter.com/counter/TOTAL.json` : "";
}
