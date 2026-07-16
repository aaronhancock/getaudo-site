import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from services import ARCHIVED_SERVICE_REDIRECTS, SERVICES, service_cards
from site_catalog import (
    build_llms_full_txt,
    build_llms_txt,
    build_service_markdown,
    build_services_markdown,
    build_sitemap_xml,
    catalog_entries,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://getaudo.com"


class CatalogSurfaceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
