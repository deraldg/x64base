"use client";

import { useMemo, useState } from "react";
import {
  CAPTURES, ERAS, TRACKS, FEATURES,
  type Capture, type FeatureId, type TrackId,
} from "@/config/retro";

/**
 * RETRO -- maintainer-only playground, headed for LabTalk as teaching material.
 *
 * Owner, 2026-08-15: "my private playground until I decide how much of it goes
 * into labtalk and dottalkpp." Confirmed 2026-08-16 as eventual teaching
 * material, which is why provenance is structural rather than optional.
 *
 * THREE LAYERS KEEP THIS OFF x64base.com, and none of them is the link:
 *   1. config/nav.ts localOnlyNav -- the menu entry renders only under local
 *      preview (NEXT_PUBLIC_SITE_VERSION unset).
 *   2. scripts/strip-local-only-output.mjs LOCAL_ONLY_DIRS -- "retro" is
 *      deleted from every build output.
 *   3. scripts/publish-github-pages.mjs -- ABORTS the publish if out/retro
 *      survived anyway.
 * Layer 2 is the one that matters: a hidden link still builds a reachable
 * route, and "nobody linked it" has never kept anything private.
 *
 * TWO READINGS, ONE DATASET
 *   By era     -- what 1985 looked like across every track at once. That is
 *                 the view five separate "history of X" pages cannot give.
 *   By feature -- the arrival of the mouse, or overlapping windows, across
 *                 every platform that got one. That is the teaching payload.
 *
 * DESIGN NOTES worth keeping
 *   - No background image. These screens were light-emitting on a dark
 *     surround; CGA, C64 and Amiga palettes only look correct against dark. A
 *     decorative background would compete with every capture and make all of
 *     them look slightly wrong. The page looks retro because the artifacts are.
 *   - Thumbnails letterbox to a fixed HEIGHT, width varies with native_res.
 *     Uniform square tiles would misrepresent every machine here.
 *   - Eras collapse; the page opens as a summary, not a wall.
 *   - Empty slots are honest. Useful at ten captures, better at five hundred,
 *     never looking broken in between.
 */

function aspect(nativeRes?: string): number {
  if (!nativeRes) return 4 / 3;
  const m = nativeRes.match(/^(\d+)\s*[xX]\s*(\d+)$/);
  if (!m) return 4 / 3;
  const w = Number(m[1]), h = Number(m[2]);
  return h > 0 ? w / h : 4 / 3;
}

const THUMB_H = 132; // fixed height; width follows the machine's real shape

function CaptureCard({ c }: { c: Capture }) {
  const w = Math.round(THUMB_H * aspect(c.native_res));
  const src = c.thumb_url || c.image_url;
  return (
    <figure className="rounded-lg border border-border bg-card p-2">
      <div
        className="flex items-center justify-center overflow-hidden rounded bg-black"
        style={{ height: THUMB_H, width: w }}
      >
        {src ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={src} alt={c.title} loading="lazy" className="h-full w-full object-contain" />
        ) : (
          <span className="px-2 text-center font-mono text-[10px] text-muted">no capture yet</span>
        )}
      </div>
      <figcaption className="mt-2 w-full" style={{ maxWidth: Math.max(w, 190) }}>
        <p className="text-sm font-semibold text-fg">{c.title}</p>
        <p className="font-mono text-[11px] text-muted">
          {c.date}
          {c.native_res ? ` | ${c.native_res}` : ""} | {c.tier}
        </p>
        {c.note ? <p className="mt-1 text-xs text-muted">{c.note}</p> : null}
        {c.features.length ? (
          <p className="mt-1 font-mono text-[10px] text-brand">{c.features.join(" . ")}</p>
        ) : null}
        {c.provenance ? (
          <p className="mt-1 text-[10px] text-muted">
            {c.provenance.credit} |{" "}
            <a href={c.provenance.source_page} className="underline hover:text-fg">
              source
            </a>{" "}
            | retrieved {c.provenance.retrieved}
          </p>
        ) : (
          <p className="mt-1 text-[10px] text-orange">provenance missing</p>
        )}
      </figcaption>
    </figure>
  );
}

export default function RetroPage() {
  const [openEra, setOpenEra] = useState<string | null>(ERAS[1]?.id ?? null);
  const [feature, setFeature] = useState<FeatureId | null>(null);

  const shown = useMemo(
    () => (feature ? CAPTURES.filter((c) => c.features.includes(feature)) : CAPTURES),
    [feature]
  );

  const byEraTrack = (era: string, track: TrackId) =>
    shown.filter((c) => c.era === era && c.track === track).sort((a, b) => a.year - b.year);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-10">
      <div className="mb-6 rounded-xl border border-orange/60 bg-card p-3">
        <p className="font-mono text-xs text-orange">LOCAL ONLY -- NOT PUBLISHED</p>
        <p className="mt-1 text-sm text-muted">
          Stripped from every build output; the publish aborts if it survives.
        </p>
      </div>

      <h1 className="text-3xl font-bold tracking-tight">RETRO</h1>
      <p className="mt-3 max-w-3xl text-muted">
        One timeline, several tracks. Read it by <strong>era</strong> to see what a
        year looked like everywhere at once, or filter by <strong>feature</strong> to
        watch one idea arrive across every platform that got it.
      </p>
      <p className="mt-2 max-w-3xl text-sm text-muted">
        The database lineage is deliberately absent: it lives in{" "}
        <code>docs/cases/CASE_HIST_*</code> with its own generator, and one home per
        artifact is the rule.
      </p>

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <span className="font-mono text-xs text-muted">feature:</span>
        <button
          type="button"
          onClick={() => setFeature(null)}
          className={`rounded-lg border px-2 py-1 text-xs transition ${
            feature === null ? "border-brand bg-card text-fg" : "border-border text-muted hover:text-fg"
          }`}
        >
          all
        </button>
        {FEATURES.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => setFeature(f.id === feature ? null : f.id)}
            className={`rounded-lg border px-2 py-1 text-xs transition ${
              feature === f.id ? "border-brand bg-card text-fg" : "border-border text-muted hover:text-fg"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {CAPTURES.length === 0 ? (
        <p className="mt-6 rounded-lg border border-border bg-card p-3 text-sm text-muted">
          No captures yet. Add them to <code>CAPTURES</code> in{" "}
          <code>config/retro.ts</code> -- the template is in the comment above it.
          Suggested first pass: 1985-89.
        </p>
      ) : null}

      <div className="mt-8 space-y-3">
        {ERAS.map((era) => {
          const open = openEra === era.id;
          const count = shown.filter((c) => c.era === era.id).length;
          return (
            <section key={era.id} className="rounded-xl border border-border bg-card">
              <button
                type="button"
                onClick={() => setOpenEra(open ? null : era.id)}
                className="flex w-full items-center justify-between gap-4 px-4 py-3 text-left"
              >
                <span>
                  <span className="font-mono text-sm text-brand">{era.label}</span>
                  <span className="ml-3 text-sm text-muted">{era.blurb}</span>
                </span>
                <span className="font-mono text-xs text-muted">
                  {count} {open ? "-" : "+"}
                </span>
              </button>

              {open ? (
                <div className="border-t border-border px-4 py-4">
                  {TRACKS.map((t) => {
                    const items = byEraTrack(era.id, t.id);
                    return (
                      <div key={t.id} className="mb-5 last:mb-0">
                        <h3 className="mb-2 font-mono text-xs uppercase tracking-wide text-muted">
                          {t.label}
                        </h3>
                        {items.length ? (
                          <div className="flex flex-wrap gap-3">
                            {items.map((c) => (
                              <CaptureCard key={c.id} c={c} />
                            ))}
                          </div>
                        ) : (
                          <div className="rounded-lg border border-dashed border-border px-3 py-4 text-xs text-muted">
                            empty slot -- nothing recorded for this track in this era
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </section>
          );
        })}
      </div>

      {/* The public home for this material. RETRO here is the staging bench --
          collect freely, promote deliberately. The index at derald.com is the
          curated face, and keeping the link here means the two never drift into
          being two separate collections that disagree. */}
      <div className="mt-10 border-t border-border pt-6">
        <p className="text-sm text-muted">
          Public retro index:{" "}
          <a
            href="https://www.derald.com/retro"
            className="font-mono text-brand underline hover:text-fg"
            rel="noopener"
          >
            www.derald.com/retro
          </a>
        </p>
        <p className="mt-1 text-xs text-muted">
          This page is the private bench. That one is the curated index.
        </p>
      </div>
    </main>
  );
}
