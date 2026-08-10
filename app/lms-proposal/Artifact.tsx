"use client";
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Full-bleed deck route.
 *
 * The deck itself is one self-contained document served from
 *   public/lms-proposal/deck.html
 * byte-identical to the standalone viewer, so the two cannot drift.
 *
 * This component does exactly two things, and both exist because the site
 * layout would otherwise shrink the slide to a postage stamp:
 *
 *   1. Breaks out of `main`'s max-w-6xl column to the full viewport width.
 *      A slide is a fixed 16:9 canvas -- constrain its width and you constrain
 *      its height too, which is why it rendered tiny inside the column.
 *   2. Cancels `main`'s vertical padding and takes every pixel below the site
 *      header, so the deck occupies the window the way a presentation should.
 */
export default function Artifact() {
  const host = useRef<HTMLDivElement>(null);
  const [h, setH] = useState<number>();
  const [hash, setHash] = useState("");

  const fit = useCallback(() => {
    const el = host.current;
    if (!el) return;
    const top = el.getBoundingClientRect().top + window.scrollY;
    setH(Math.max(430, window.innerHeight - top));
  }, []);

  useEffect(() => {
    fit();
    window.addEventListener("resize", fit);
    const t = setTimeout(fit, 80);
    return () => { window.removeEventListener("resize", fit); clearTimeout(t); };
  }, [fit]);

  // The deck reads location.hash, but inside the iframe that is the iframe's own
  // URL, not the route's. Forward the parent hash so /lms-proposal/#05
  // opens on that slide instead of landing on the cover.
  useEffect(() => {
    const sync = () => setHash(window.location.hash || "");
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return (
    <div
      ref={host}
      style={{
        height: h ?? "100vh",
        background: "#070e17",
        overflow: "hidden",
        // escape the centered content column: pull out to the full viewport
        width: "100vw",
        marginLeft: "calc(50% - 50vw)",
        marginRight: "calc(50% - 50vw)",
        // cancel the vertical padding main applies to every route
        marginTop: "calc(-1 * var(--route-pad-top, 2.5rem))",
        marginBottom: "calc(-1 * var(--route-pad-bottom, 2.5rem))",
      }}
    >
      <iframe
        src={"/lms-proposal/deck.html" + hash}
        title="Specialty NON LMS Ecosystem Proposal"
        allow="fullscreen"
        allowFullScreen
        style={{ width: "100%", height: "100%", border: 0, display: "block" }}
      />
    </div>
  );
}
