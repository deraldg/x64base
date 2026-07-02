/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  /**
   * Apache-friendly deployment:
   * - `output: "export"` produces a fully static site in `out/`
   * - `trailingSlash: true` generates `.../index.html` paths that map cleanly to Apache directories
  */
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true
  }
};

export default nextConfig;
