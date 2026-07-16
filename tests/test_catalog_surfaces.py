import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from services import ARCHIVED_SERVICE_REDIRECTS, SERVICE_COMMONNESS_ORDER, SERVICES, service_cards
from site_catalog import (
    build_llms_full_txt,
    build_llms_txt,
    build_robots_txt,
    build_service_markdown,
    build_services_markdown,
    build_sitemap_xml,
    catalog_entries,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://getaudo.com"


class CatalogSurfaceTests(unittest.TestCase):
    def test_public_catalog_uses_the_reviewed_most_common_first_order(self) -> None:
        self.assertEqual(tuple(service.title for service in SERVICES), SERVICE_COMMONNESS_ORDER)

    def test_every_public_catalog_surface_uses_the_live_services(self) -> None:
        entries = catalog_entries()

        self.assertEqual(len(entries), len(SERVICES))
        self.assertEqual(len(entries), 30)
        self.assertEqual(sum(entry.featured for entry in entries), len(service_cards()))
        self.assertEqual(
            {entry.service.title for entry in entries},
            {str(card["source_title"]) for card in service_cards()},
        )
        self.assertIn("create-requirements-for-a-developer-or-vendor", ARCHIVED_SERVICE_REDIRECTS)
        self.assertEqual(len({entry.html_path for entry in entries}), len(entries))
        self.assertEqual(len({entry.markdown_path for entry in entries}), len(entries))

        xml_text = build_sitemap_xml(BASE_URL, "2026-07-10", entries)
        root = ET.fromstring(xml_text)
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap_urls = {node.text for node in root.findall("s:url/s:loc", namespace)}
        expected_urls = {
            f"{BASE_URL}/",
            f"{BASE_URL}/privacy",
            f"{BASE_URL}/sitemap",
            *{f"{BASE_URL}{entry.html_path}" for entry in entries},
        }
        self.assertEqual(sitemap_urls, expected_urls)
        self.assertNotIn("changefreq", xml_text)
        self.assertNotIn("priority", xml_text)

    def test_llms_files_are_linked_markdown_and_include_the_full_catalog(self) -> None:
        entries = catalog_entries()
        short_guide = build_llms_txt(BASE_URL, entries)
        service_catalog = build_services_markdown(BASE_URL, entries)
        full_guide = build_llms_full_txt(BASE_URL, entries)

        self.assertTrue(short_guide.startswith("# Audo\n\n> "))
        self.assertIn("complete catalog has 30 examples", short_guide)
        self.assertNotIn("49", short_guide)
        self.assertIn("[Complete service catalog in Markdown]", short_guide)
        self.assertNotIn("auto-rotating", short_guide)
        self.assertIn("# Audo service catalog", service_catalog)
        self.assertIn("# Audo: full context for AI agents", full_guide)
        self.assertIn("## Using AI at work", short_guide)
        self.assertIn("## Choosing what to do next", service_catalog)
        self.assertNotIn("## AI coaching and support", short_guide)
        self.assertNotIn("## Product strategy", service_catalog)

        for entry in entries:
            with self.subTest(service=entry.service.slug):
                markdown_url = f"{BASE_URL}{entry.markdown_path}"
                self.assertIn(markdown_url, short_guide)
                self.assertIn(markdown_url, service_catalog)
                self.assertIn(entry.result, service_catalog)

        featured_entry = next(entry for entry in entries if entry.featured)
        detail_page = build_service_markdown(featured_entry, BASE_URL)
        self.assertIn("## Common questions", detail_page)
        self.assertIn(str(featured_entry.detail["problem_heading"]), detail_page)

    def test_generated_routes_replace_drift_prone_static_files(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text()
        server_source = (ROOT / "server.py").read_text()

        self.assertFalse((ROOT / "llms.txt").exists())
        self.assertFalse((ROOT / "sitemap.xml").exists())
        self.assertNotIn("COPY llms.txt", dockerfile)
        self.assertNotIn("COPY sitemap.xml", dockerfile)
        self.assertIn("COPY site_catalog.py /app/site_catalog.py", dockerfile)
        self.assertIn('if path == "/llm.txt":', server_source)
        self.assertIn('self.redirect_permanent("/llms.txt")', server_source)
        self.assertIn('if path == "/services.md":', server_source)

    def test_privacy_hero_has_short_balanced_plain_language_copy(self) -> None:
        privacy = (ROOT / "privacy.html").read_text()

        self.assertIn("How Audo handles the information you share.", privacy)
        self.assertIn("text-wrap: balance", privacy)
        self.assertIn('rel="alternate" href="/llms.txt"', privacy)
        self.assertNotIn("Here's what happens to the information you share.", privacy)

    def test_public_site_uses_aaron_without_a_last_name(self) -> None:
        public_sources = (
            ROOT / "index.html",
            ROOT / "privacy.html",
            ROOT / "thank-you.html",
            ROOT / "server.py",
            ROOT / "site_catalog.py",
        )

        for source in public_sources:
            with self.subTest(source=source.name):
                self.assertNotIn("hancock", source.read_text().lower())

        entries = catalog_entries()
        self.assertNotIn("hancock", build_llms_txt(BASE_URL, entries).lower())
        self.assertNotIn("hancock", build_llms_full_txt(BASE_URL, entries).lower())
        self.assertFalse(any("hancock" in path.name.lower() for path in ROOT.rglob("*") if ".git" not in path.parts))

    def test_unreleased_audo_agent_is_absent_from_every_public_surface(self) -> None:
        entries = catalog_entries()
        forbidden_product_names = (
            "audo agent",
            "audo-agent",
            "audo ai agent",
        )
        public_surfaces = {
            "homepage": (ROOT / "index.html").read_text(),
            "privacy": (ROOT / "privacy.html").read_text(),
            "thank-you": (ROOT / "thank-you.html").read_text(),
            "human sitemap template": (ROOT / "server.py").read_text(),
            "llms summary": build_llms_txt(BASE_URL, entries),
            "llms full guide": build_llms_full_txt(BASE_URL, entries),
            "services markdown": build_services_markdown(BASE_URL, entries),
            "xml sitemap": build_sitemap_xml(BASE_URL, "2026-07-16", entries),
        }
        public_surfaces.update(
            {
                f"service page {entry.service.slug}": build_service_markdown(entry, BASE_URL)
                for entry in entries
            }
        )

        for surface, content in public_surfaces.items():
            with self.subTest(surface=surface):
                normalized = content.lower()
                for product_name in forbidden_product_names:
                    self.assertNotIn(product_name, normalized)

    def test_server_exposes_crawl_and_agent_discovery_files(self) -> None:
        server_source = (ROOT / "server.py").read_text()
        self.assertIn('if path == "/robots.txt":', server_source)
        self.assertIn("build_robots_txt(PUBLIC_BASE_URL)", server_source)
        self.assertIn('if path == "/llms.txt":', server_source)
        self.assertIn('if path == "/llms-full.txt":', server_source)
        robots = build_robots_txt(BASE_URL)
        self.assertIn("Disallow: /api/", robots)
        self.assertIn(f"Sitemap: {BASE_URL}/sitemap.xml", robots)
        self.assertIn(f"# AI-readable site guide: {BASE_URL}/llms.txt", robots)

    def test_machine_readable_context_matches_the_public_small_business_positioning(self) -> None:
        entries = catalog_entries()
        machine_context = "\n".join(
            (
                build_llms_txt(BASE_URL, entries),
                build_llms_full_txt(BASE_URL, entries),
                (ROOT / "index.html").read_text(),
            )
        ).lower()

        for internal_or_automotive_term in (
            "cox automotive",
            "dealertrack",
            "dealer.com",
            "dealership platforms",
            "automotive retail technology",
            "m&a technology review",
        ):
            self.assertNotIn(internal_or_automotive_term, machine_context)

        self.assertIn("small business", machine_context)
        self.assertIn("30 years", machine_context)


if __name__ == "__main__":
    unittest.main()
