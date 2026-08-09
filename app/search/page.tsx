import type { Metadata } from "next";
import SearchClient from "./SearchClient";

export const metadata: Metadata = {
  title: "Search",
  description: "Search the x64base documentation and public pages."
};

export default function SearchPage() {
  return (
    <div className="min-w-0 flex-1">
      <h1 className="text-3xl font-semibold tracking-tight">Search</h1>
      <p className="mt-2 text-muted">
        Search the public documentation and pages. The private working references are deliberately
        excluded from the index.
      </p>
      <div className="mt-6">
        <SearchClient />
      </div>
      <p className="mt-6 text-sm text-muted">
        Search runs entirely in your browser over a prebuilt index -- there is no server. It is
        available on the built site; under a local dev server the index is not generated.
      </p>
    </div>
  );
}
