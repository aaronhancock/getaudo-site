from __future__ import annotations

import html
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from services import SERVICES, Service, service_cards


CATEGORY_ORDER = (
    "Website and app care",
    "Automation",
    "AI coaching and support",
    "Product strategy",
    "Small business setup and operations",
)


@dataclass(frozen=True)
class CatalogEntry:
    service: Service
    title: str
    summary: str
    result: str
    group: str
    group_label: str
    featured: bool
    detail: dict[str, object] | None

    @property
    def html_path(self) -> str:
        return self.service.url

    @property
    def markdown_path(self) -> str:
        return f"{self.service.url}.md"


def catalog_entries() -> list[CatalogEntry]:
    cards_by_source = {str(card["source_title"]): card for card in service_cards()}
    group_fallbacks = {
        "Website and app care": "website",
        "Automation": "work",
        "AI coaching and support": "ai",
        "Product strategy": "decisions",
        "Small business setup and operations": "decisions",
    }
    entries: list[CatalogEntry] = []
    for service in SERVICES:
        card = cards_by_source.get(service.title)
        entries.append(
            CatalogEntry(
                service=service,
                title=str(card["title"]) if card else service.title,
                summary=str(card["summary"]) if card else service.summary,
                result=str(card["result"]) if card else service.result,
                group=str(card["group"]) if card else group_fallbacks[service.category],
                group_label=str(card["group_label"]) if card else service.category,
                featured=card is not None,
                detail=card,
            )
        )
    return entries


def grouped_catalog(entries: list[CatalogEntry] | None = None) -> dict[str, list[CatalogEntry]]:
    grouped = {category: [] for category in CATEGORY_ORDER}
    for entry in entries or catalog_entries():
        grouped.setdefault(entry.service.category, []).append(entry)
    return {category: grouped[category] for category in CATEGORY_ORDER if grouped.get(category)}


def catalog_lastmod(base_dir: Path, override: str | None = None) -> str:
    configured = (override if override is not None else os.environ.get("SITEMAP_LASTMOD", "")).strip()
    if configured:
        try:
            return datetime.strptime(configured, "%Y-%m-%d").date().isoformat()
        except ValueError as exc:
            raise ValueError("SITEMAP_LASTMOD must use YYYY-MM-DD format.") from exc

    content_paths = (
        base_dir / "services.py",
        base_dir / "site_catalog.py",
        base_dir / "server.py",
        base_dir / "index.html",
        base_dir / "privacy.html",
        base_dir / "assets" / "site-footer.css",
    )
    timestamps = [path.stat().st_mtime for path in content_paths if path.exists()]
    timestamp = max(timestamps) if timestamps else datetime.now(timezone.utc).timestamp()
    return datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()


def build_sitemap_xml(base_url: str, lastmod: str, entries: list[CatalogEntry] | None = None) -> str:
    base_url = base_url.rstrip("/")
    urls = [
        (f"{base_url}/", "monthly", "1.0"),
        (f"{base_url}/privacy", "yearly", "0.5"),
        (f"{base_url}/sitemap", "monthly", "0.8"),
        *[(f"{base_url}{entry.html_path}", "monthly", "0.72") for entry in entries or catalog_entries()],
    ]
    rows = "\n".join(
        f"""  <url>
    <loc>{html.escape(url)}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""
        for url, changefreq, priority in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{rows}
</urlset>
"""


def _markdown_label(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]")


def _absolute(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _service_link(entry: CatalogEntry, base_url: str) -> str:
    description = f"{entry.summary} What gets better: {entry.result}"
    return f"- [{_markdown_label(entry.title)}]({_absolute(base_url, entry.markdown_path)}): {description}"


def build_llms_txt(base_url: str, entries: list[CatalogEntry] | None = None) -> str:
    entries = entries or catalog_entries()
    sections = [
        "# Audo",
        "",
        "> Direct, plain-English technology help for small businesses from Aaron Hancock.",
        "",
        "Audo helps non-technical small-business owners fix websites, reduce repetitive work, use AI carefully, choose software, and get practical technology projects moving. Clients work directly with Aaron from the first conversation through the work itself.",
        "",
        f"The website's complete catalog has {len(entries)} examples written around problems small-business owners recognize. The homepage explorer, sitemap, and agent-readable files all use this same catalog.",
        "",
        "## Start here",
        "",
        f"- [Audo home]({_absolute(base_url, '/')}): Overview, all service examples, Aaron's background, client work, and the discovery form.",
        f"- [Book a free discovery call]({_absolute(base_url, '/#discovery')}): Share what is happening, then choose an available 30-minute Google Meet time.",
        f"- [Human-readable sitemap]({_absolute(base_url, '/sitemap')}): Browse every public page by topic.",
        f"- [Complete service catalog in Markdown]({_absolute(base_url, '/services.md')}): Expanded descriptions, outcomes, and links for every service page.",
        f"- [Full Audo context for agents]({_absolute(base_url, '/llms-full.txt')}): Detailed company, service, booking, and page context in one file.",
        "",
        "## About Audo",
        "",
        "- Aaron Hancock is Audo's founder and senior technology partner. He has 30 years of hands-on experience building websites and software and leading product and engineering teams.",
        "- Audo is intentionally small. Clients speak with the person who diagnoses, explains, and does the work—without account managers or agency handoffs.",
        "- The audience is primarily non-technical small-business owners. Recommendations should be explained in ordinary business language, without assuming technical vocabulary.",
        "- A free discovery call is 30 minutes. The site collects a short description first, then offers live calendar availability.",
        "",
    ]
    for category, category_entries in grouped_catalog(entries).items():
        sections.extend([f"## {category}", ""])
        sections.extend(_service_link(entry, base_url) for entry in category_entries)
        sections.append("")
    sections.extend(
        [
            "## Optional",
            "",
            f"- [Privacy policy]({_absolute(base_url, '/privacy')}): What Audo collects, why it is needed, which services handle it, and what visitors can control.",
            f"- [XML sitemap]({_absolute(base_url, '/sitemap.xml')}): Canonical index of public HTML pages.",
            f"- [Service catalog data]({_absolute(base_url, '/assets/services.json')}): JSON used by the homepage explorer for all {len(entries)} service examples.",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def _entry_markdown(entry: CatalogEntry, base_url: str, heading_level: int = 3) -> str:
    heading = "#" * heading_level
    detail = entry.detail
    problem = str(detail["problem_heading"]) if detail else entry.service.pain
    goal = str(detail["goal_heading"]) if detail else entry.result
    approach = str(detail["approach_heading"]) if detail else entry.service.solution
    lines = [
        f"{heading} {entry.title}",
        "",
        entry.summary,
        "",
        f"- **What is happening:** {problem}",
        f"- **What the owner wants:** {goal}",
        f"- **How Aaron helps:** {approach}",
        f"- **What gets better:** {entry.result}",
        f"- **Web page:** [{_absolute(base_url, entry.html_path)}]({_absolute(base_url, entry.html_path)})",
        f"- **Markdown page:** [{_absolute(base_url, entry.markdown_path)}]({_absolute(base_url, entry.markdown_path)})",
    ]
    return "\n".join(lines)


def build_services_markdown(base_url: str, entries: list[CatalogEntry] | None = None) -> str:
    entries = entries or catalog_entries()
    lines = [
        "# Audo service catalog",
        "",
        "> Plain-English examples of the website, day-to-day work, AI, software, and technology decisions Aaron can help a small business handle.",
        "",
        f"This is Audo's complete catalog of {len(entries)} live service pages. It is generated from the same source as the homepage explorer and both sitemaps. Every entry below links to the normal web page and an agent-friendly Markdown version.",
        "",
        f"- [Audo home]({_absolute(base_url, '/')})",
        f"- [Book free discovery]({_absolute(base_url, '/#discovery')})",
        f"- [Short AI guide]({_absolute(base_url, '/llms.txt')})",
        f"- [Full AI guide]({_absolute(base_url, '/llms-full.txt')})",
        "",
    ]
    for category, category_entries in grouped_catalog(entries).items():
        lines.extend([f"## {category}", ""])
        for entry in category_entries:
            lines.extend([_entry_markdown(entry, base_url), ""])
    return "\n".join(lines).rstrip() + "\n"


def build_service_markdown(entry: CatalogEntry, base_url: str) -> str:
    detail = entry.detail
    problem = str(detail["problem_heading"]) if detail else entry.service.pain
    goal = str(detail["goal_heading"]) if detail else entry.result
    approach = str(detail["approach_heading"]) if detail else entry.service.solution
    steps = tuple(str(step) for step in detail["steps"]) if detail else (
        "Show Aaron what is happening now.",
        "Choose the smallest useful fix or next step.",
        "Make sure the result is clear and manageable for the business.",
    )
    lines = [
        f"# {entry.title}",
        "",
        f"> {entry.summary}",
        "",
        f"- **Category:** {entry.service.category}",
        f"- **Canonical page:** [{_absolute(base_url, entry.html_path)}]({_absolute(base_url, entry.html_path)})",
        f"- **Book free discovery:** [{_absolute(base_url, '/#discovery')}]({_absolute(base_url, '/#discovery')})",
        "",
        "## What is happening",
        "",
        problem,
        "",
        "## What the business owner wants",
        "",
        goal,
        "",
        "## How Aaron helps",
        "",
        approach,
        "",
        "## A practical way to start",
        "",
        *[f"{index}. {step}" for index, step in enumerate(steps, start=1)],
        "",
        "## What gets better",
        "",
        entry.result,
        "",
    ]
    if detail:
        questions = tuple(str(value) for value in detail["faq_questions"])
        answers = tuple(str(value) for value in detail["faq_answers"])
        lines.extend(["## Common questions", ""])
        for question, answer in zip(questions, answers):
            lines.extend([f"### {question}", "", answer, ""])
    lines.extend(
        [
            "## Related Audo resources",
            "",
            f"- [Complete service catalog]({_absolute(base_url, '/services.md')})",
            f"- [Human-readable sitemap]({_absolute(base_url, '/sitemap')})",
            f"- [Audo AI guide]({_absolute(base_url, '/llms.txt')})",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def build_llms_full_txt(base_url: str, entries: list[CatalogEntry] | None = None) -> str:
    entries = entries or catalog_entries()
    service_catalog = build_services_markdown(base_url, entries).replace(
        "# Audo service catalog", "## Complete service catalog", 1
    )
    return f"""# Audo: full context for AI agents

> Authoritative site, company, service, and booking context for getaudo.com.

## Company and audience

Audo is Aaron Hancock's independent consulting practice for small businesses. The primary audience is a non-technical business owner who knows something is frustrating, broken, slow, confusing, or taking too much time but may not know the technical name for the problem. Audo copy and recommendations use simple, direct language and connect technology work to business outcomes.

Aaron works directly with each client. He diagnoses the problem, explains the options, plans the work, and does the work. Audo can handle a one-time repair, a larger project, or ongoing support.

Aaron has 30 years of experience building websites and software and leading product and engineering teams. His background includes Cox Automotive, Dealertrack, Dealer.com, product and technology due diligence, integrations, migrations, and client work for organizations including Boston's Pizza, John Maxwell Leadership Foundation, Hattori Hanzo, and L'Oreal.

## What Audo helps with

- Websites and web apps: broken forms, slow pages, confusing mobile experiences, WordPress care, accessibility, hosting, security warnings, better customer pages, new sites, and ongoing updates.
- Customers and leads: clearer contact and booking flows, follow-up, customer records, quote tools, portals, and onboarding.
- Everyday work: repetitive data entry, forms, reminders, reports, proposals, spreadsheets, dashboards, and small internal tools.
- Practical AI help: choosing tools, setting privacy rules, training a team, improving repeated writing, finding reliable answers, and deciding where AI is or is not useful.
- Decisions and projects: choosing software, reviewing proposals, deciding what to build, clarifying requirements, recovering stalled work, and setting up a new business.

## Discovery and scheduling

The free discovery call lasts 30 minutes and uses Google Meet. A visitor first submits their name, email, optional page link, and a short description of what is happening. The next step shows live calendar availability. Bookings require at least 24 hours of notice and are offered Monday through Saturday in Central Time. Sunday is blocked. Discovery starts at [{_absolute(base_url, '/#discovery')}]({_absolute(base_url, '/#discovery')}).

## Client work shown on the site

- Boston's Pizza Restaurant & Sports Bar: accessibility work, marketing site and content management, database and server management, and ongoing support.
- Carnac AI Trading: platform development, proprietary market-analysis tools, cryptocurrency exchange connections, and an AI-assisted market analysis system.

## Important public resources

- [Audo home]({_absolute(base_url, '/')})
- [Human-readable sitemap]({_absolute(base_url, '/sitemap')})
- [XML sitemap]({_absolute(base_url, '/sitemap.xml')})
- [Privacy policy]({_absolute(base_url, '/privacy')})
- [Short AI guide]({_absolute(base_url, '/llms.txt')})
- [Complete service catalog]({_absolute(base_url, '/services.md')})

{service_catalog}
"""


def get_catalog_entry(slug: str, entries: list[CatalogEntry] | None = None) -> CatalogEntry | None:
    return next((entry for entry in entries or catalog_entries() if entry.service.slug == slug), None)
