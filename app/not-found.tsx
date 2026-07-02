import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">Page not found</h1>
      <p className="text-muted">The page you requested does not exist (or hasn’t been published yet).</p>
      <Link href="/" className="inline-flex rounded-2xl border border-border bg-bg/30 px-4 py-2 text-sm font-semibold hover:bg-bg/40">
        Back to home
      </Link>
    </div>
  );
}
