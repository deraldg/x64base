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

/**
 * Do-not-count list.
 *
 * A static site cannot filter by IP -- there is no server of ours in the path,
 * and the address is attached by the visitor's own browser when it fetches the
 * badge. So the filter lives EARLIER than the IP: a flag in the visitor's own
 * localStorage that decides whether the request is made at all. Nothing is sent
 * anywhere to be filtered; the request simply never happens.
 *
 * That is strictly better than a server-side disallow list. A disallow list
 * still receives your address and then promises not to use it. This never
 * hands it over.
 *
 * Two modes, because "don't count me" and "don't tell them I was here" are
 * different wishes:
 *
 *   "quiet"  -- fetch with query_only=true. You SEE the true count, and it does
 *               not go up. The service still sees the request (and therefore
 *               the address), it just does not record a visit.
 *   "silent" -- no request at all. Nothing leaves the browser, no address is
 *               seen, and the badge does not render for you.
 *
 * To switch yourself off, run this once in the browser console on x64base.com:
 *
 *     localStorage.setItem('x64base:nocount', 'quiet')   // see it, don't add
 *     localStorage.setItem('x64base:nocount', 'silent')  // send nothing
 *     localStorage.removeItem('x64base:nocount')         // count me again
 *
 * It is per-browser and per-device, so set it on each machine you browse from.
 * Anyone else you want excluded -- a co-maintainer, a CI checker -- runs the
 * same line. That is the whole disallow list: it is distributed, and each entry
 * is held by the person it excludes, which is the only place it can be honest.
 */
export const NOCOUNT_KEY = "x64base:nocount";
export type NoCountMode = "quiet" | "silent" | null;

export function noCountMode(): NoCountMode {
  if (typeof window === "undefined") return null;
  try {
    const v = window.localStorage.getItem(NOCOUNT_KEY);
    return v === "quiet" || v === "silent" ? v : null;
  } catch {
    return null; // private mode, storage disabled: behave as a normal visitor
  }
}

/**
 * The badge image URL, or "" when unconfigured or suppressed.
 * `query_only` is the service's own documented parameter for reading the count
 * without incrementing it.
 */
export function visitorBadgeUrl(mode: NoCountMode = null): string {
  if (!VISITOR_BADGE_PAGE_ID) return "";
  if (mode === "silent") return "";
  const q = new URLSearchParams({
    page_id: VISITOR_BADGE_PAGE_ID,
    left_text: "visits",
  });
  if (mode === "quiet") q.set("query_only", "true");
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
