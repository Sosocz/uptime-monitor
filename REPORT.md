# SEO + CWV Report (trezapp.fr)

## Changes
- SEO on-page: canonical links, consistent lang=fr, optimized meta descriptions, and structured data (Organization + WebSite) across templates.
- Technical SEO: /robots.txt (Googlebot allowed + sitemap) and /sitemap.xml routes with cache headers.
- Performance: defer third-party analytics until idle, preload font CSS, add preconnects, and enable gzip compression.
- UX/accessibility: label-for bindings on form fields, improved contrast on key text, and explicit logo dimensions to reduce CLS.

## Why
- Faster LCP/INP by reducing render-blocking work and deferring analytics execution.
- Cleaner crawl/indexing with canonical tags, sitemap discovery, and consistent language metadata.
- Better accessibility and reduced layout shifts for Core Web Vitals and UX signals.

## How to verify
- Local pages: visit `/robots.txt` and `/sitemap.xml` for correct output.
- Lighthouse / PageSpeed: check LCP, INP, CLS, and SEO improvements.
- Search Console: validate sitemap and inspect canonical URLs.

## Before/After (estimated)
- LCP: 5.3s -> 2.5-3.0s (fonts + analytics deferral).
- INP/FID: 1.24s -> <200ms (reduced main-thread work from third parties).
- CLS: <0.1 maintained (explicit logo dimensions).

## Local commands
```bash
python -m uvicorn app.main:app --reload
```

```bash
pytest -q
```
