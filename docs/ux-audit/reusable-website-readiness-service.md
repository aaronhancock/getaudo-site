# Reusable Website Readiness Audit

This package turns the Audo 95+ experience audit into a repeatable client service. It combines human UX review with deterministic checks for technical SEO, AI/agent discovery, crawlability, structured data, shared navigation, and accessibility signals.

## Deliverables

Each run produces:

- `report.json` for integrations and historical comparison.
- `report.md` for a written client handoff.
- `index.html` for a filterable, shareable local report.
- A complete page inventory derived from the canonical XML sitemap.
- Page-level evidence and recommendations for every warning or failure.
- A limitations section that separates automated evidence from manual review and legal claims.

## Run it for any website

```bash
python3 scripts/website_readiness_audit.py \
  --url https://example.com \
  --output outputs/example-website-audit
```

To audit a local mirror while validating production canonicals:

```bash
python3 scripts/website_readiness_audit.py \
  --url http://127.0.0.1:8765 \
  --canonical-host getaudo.com \
  --include-path /thank-you \
  --output outputs/public-website-readiness-audit
```

## Automated scope

### Technical SEO and crawlability

- HTTP status and HTML content type for every sitemap URL.
- `robots.txt` availability and absolute sitemap declaration.
- XML validity, canonical-only URLs, duplicates, and route coverage.
- Unique title, meta description, canonical, language, viewport, and H1.
- Canonical path alignment.
- JSON-LD syntax and reported schema types.
- Index/noindex signals.

### AI and agent discovery

- `/llms.txt` and `/llms-full.txt` availability.
- Basic llms.txt Markdown structure: H1, summary blockquote, and absolute source links.
- Linked agent-friendly catalogs and page-specific Markdown sources.
- Guardrails against unsupported pricing, guarantees, testimonials, or capabilities.
- Consistency between the HTML catalog, XML sitemap, human sitemap, JSON catalog, and AI-readable catalogs.

`llms.txt` is an emerging proposal, not a search-engine guarantee. It complements crawlable HTML, canonicals, sitemaps, and structured data; it does not replace them.

### Accessibility signals

- Document language, viewport, one H1, heading evidence, and landmarks.
- Unique IDs.
- Image `alt` attributes.
- Programmatic labels for form controls.
- Accessible text for links and buttons.
- Shared navigation availability.

The release audit must add rendered keyboard, focus, 200%/400% zoom, reflow, contrast, reduced-motion, screen-reader, mobile target-size, error recovery, and complete conversion-path checks. Automated output is not WCAG conformance or legal certification.

### Experience and business review

Run the technical package inside the broader [95+ Website Experience Audit](95-plus-website-experience-audit.md). That process adds persona-based clarity, simplicity, trust, business effectiveness, responsive screenshots, and end-to-end task completion.

## Client service workflow

1. **Discovery:** identify the canonical origin, public routes, business goal, limiting persona, conversion journeys, analytics, forms, and third parties.
2. **Baseline:** run the reusable scanner, capture desktop/mobile evidence, complete keyboard and conversion journeys, and freeze the initial report.
3. **Prioritized findings:** separate hard gates, revenue or trust risks, accessibility barriers, discoverability problems, and polish.
4. **Remediation:** repair the worst item first, rerun affected checks, and retain before/after evidence.
5. **Final report:** deliver executive summary, scorecard, page inventory, findings, fixes completed, remaining manual or external work, and maintenance plan.
6. **Release check:** audit the exact revision to be deployed and perform read-only production smoke checks afterward.

## Report positioning

The service may be described as a comprehensive website experience, discoverability, and accessibility-readiness audit. Do not market it as an ADA certification, WCAG certification, guaranteed ranking improvement, guaranteed AI citation, or legal opinion.

## Standards and maintenance

The rubric should be reviewed at least quarterly against current primary guidance:

- W3C WCAG 2.2 and supporting techniques.
- Google Search Central crawling, canonical, sitemap, and structured-data documentation.
- The current llms.txt proposal and actual behavior of major AI crawlers.
- Browser and assistive-technology behavior used by the audited audience.
