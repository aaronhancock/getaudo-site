import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "website_readiness_audit", ROOT / "scripts" / "website_readiness_audit.py"
)
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class WebsiteReadinessAuditTests(unittest.TestCase):
    def test_parser_recognizes_accessible_names_and_page_signals(self) -> None:
        source = b"""<!doctype html><html lang='en'><head><title>Useful test page | Example</title>
        <meta name='viewport' content='width=device-width,initial-scale=1'><meta name='description' content='A useful and specific description for this complete website audit test page.'>
        <link rel='canonical' href='https://example.com/test'></head><body>
        <nav><a href='/' aria-label='Example home'><img src='/logo.png' alt='Example'></a><a href='/work'>Find your starting point</a><a href='/about'>Why Audo</a><a href='/book'>Book free discovery</a></nav>
        <main><h1>Test page</h1><form><label for='email'>Email</label><input id='email' name='email'></form></main><footer></footer></body></html>"""
        findings = []
        parser = audit.analyze_page("https://example.com/test", source, findings)
        self.assertEqual(parser.h1, ["Test page"])
        self.assertFalse([finding for finding in findings if finding.status == "fail"])

    def test_report_writes_json_markdown_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = audit.render_report("https://example.com", [], {}, Path(directory))
            self.assertEqual(report["summary"], {})
            for name in ("report.json", "report.md", "index.html"):
                self.assertTrue((Path(directory) / name).exists())


if __name__ == "__main__":
    unittest.main()
