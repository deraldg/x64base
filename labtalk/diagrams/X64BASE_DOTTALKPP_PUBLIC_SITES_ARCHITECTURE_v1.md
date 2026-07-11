# x64base.com and dottalkpp.com Public-Site Architecture v1

Status: curated source-derived public architecture pack

## Canonical Mermaid Sources

- `x64base_com_site_architecture_v1.mmd`
- `dottalkpp_com_site_architecture_v1.mmd`
- `x64base_dottalkpp_public_sites_connection_v1.mmd`

## Roles

`x64base.com` is the main ecosystem website. It presents the engine, formats,
product family, Laboratory Campus, project story, selected evidence, development
governance, and curated download routes.

`dottalkpp.com` is the focused manual, reference, generated-documentation, proof,
and artifact room. It supports but does not replace the main site.

The sites share an upstream evidence spine but have independent source trees,
repositories/branches, builds, route ownership, and publication histories. They
are complementary sites, not mirrors.

## Authority and Connection Rules

1. Source/runtime/HELP/metadata/contracts/proof remain upstream of both sites.
2. Reviewed manuals and manualgen outputs may feed either publication surface.
3. x64base.com links readers to deeper DotTalk++ manuals and artifacts.
4. dottalkpp.com links readers back to engine, product, campus, and project context.
5. Reviewed artifact notices and route summaries may return to x64base.com.
6. Website prose cannot flow backward into runtime or manual truth by default.
7. A reverse-flow exception requires a separately owned, non-derivable public
   artifact with recorded provenance.
8. `README.*` orientation files remain versioned provenance artifacts.

## Source Basis

- `rules/rules.txt`
- `docs/contracts/WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md`
- `D:/dev/x64base-site/README.md`
- `D:/dev/x64base-site/content/docs/dev/selfdoc-website-publication.mdx`
- `D:/dev/derald-site/README.md`
- `D:/dev/derald-site/lib/site-data.ts`
- `D:/dev/derald-site/.github/workflows/deploy-pages.yml`
