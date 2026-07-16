#!/usr/bin/env python3
"""Reusable public-site audit for SEO, AI discovery, accessibility, and consistency.

The audit is intentionally dependency-free so it can run against any public or
local website. Automated results are evidence, not an accessibility or legal
certification; the generated report includes the manual checks still required.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


USER_AGENT = "AudoWebsiteReadinessAudit/1.0 (+https://getaudo.com/)"
PUBLIC_FILES = ("/robots.txt", "/sitemap.xml", "/llms.txt", "/llms-full.txt")


@dataclass
class Finding:
    status: str
    category: str
    check: str
    route: str
    message: str
    evidence: str = ""
    recommendation: str = ""


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.robots = ""
        self.lang = ""
        self.viewport = ""
        self.h1: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self.links: list[tuple[str, str]] = []
        self.images: list[tuple[str, str | None]] = []
        self.inputs: list[dict[str, str]] = []
        self.labels_for: set[str] = set()
        self.buttons: list[str] = []
        self.ids: list[str] = []
        self.json_ld: list[str] = []
        self.nav_texts: list[list[str]] = []
        self.landmarks = Counter()
        self._capture: str | None = None
        self._text: list[str] = []
        self._link_href = ""
        self._nav_depth = 0
        self._nav_links: list[str] = []

    @staticmethod
    def attrs_dict(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = self.attrs_dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        if tag == "html":
            self.lang = data.get("lang", "")
        if tag in {"header", "nav", "main", "footer", "aside"}:
            self.landmarks[tag] += 1
        if tag == "nav":
            self._nav_depth += 1
            if self._nav_depth == 1:
                self._nav_links = []
        if tag == "title":
            self._capture, self._text = "title", []
        elif tag in {f"h{i}" for i in range(1, 7)}:
            self._capture, self._text = tag, []
        elif tag == "button":
            self._capture, self._text = "button", [data.get("aria-label", "")]
        elif tag == "script" and data.get("type") == "application/ld+json":
            self._capture, self._text = "jsonld", []
        elif tag == "meta":
            name = data.get("name", "").lower()
            if name == "description": self.description = data.get("content", "").strip()
            if name == "robots": self.robots = data.get("content", "").strip()
            if name == "viewport": self.viewport = data.get("content", "").strip()
        elif tag == "link" and "canonical" in data.get("rel", "").lower().split():
            self.canonical = data.get("href", "").strip()
        elif tag == "a":
            self._capture, self._text = "a", [data.get("aria-label", "")]
            self._link_href = data.get("href", "")
        elif tag == "img":
            self.images.append((data.get("src", ""), data.get("alt") if "alt" in data else None))
        elif tag in {"input", "select", "textarea"}:
            data["tag"] = tag
            self.inputs.append(data)
        elif tag == "label" and data.get("for"):
            self.labels_for.add(data["for"])

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        text = re.sub(r"\s+", " ", "".join(self._text)).strip()
        if self._capture == "title" and tag == "title":
            self.title = text
            self._capture = None
        elif self._capture in {f"h{i}" for i in range(1, 7)} and tag == self._capture:
            level = int(tag[1])
            self.headings.append((level, text))
            if level == 1: self.h1.append(text)
            self._capture = None
        elif self._capture == "button" and tag == "button":
            self.buttons.append(text)
            self._capture = None
        elif self._capture == "jsonld" and tag == "script":
            self.json_ld.append("".join(self._text).strip())
            self._capture = None
        elif self._capture == "a" and tag == "a":
            self.links.append((self._link_href, text))
            if self._nav_depth: self._nav_links.append(text)
            self._capture = None
        if tag == "nav" and self._nav_depth:
            if self._nav_depth == 1:
                self.nav_texts.append([value for value in self._nav_links if value])
            self._nav_depth -= 1


def fetch(url: str, timeout: int = 15) -> tuple[int, dict[str, str], bytes, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read(), response.geturl()
    except HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read(), exc.geturl()
    except URLError as exc:
        return 0, {}, b"", str(exc.reason)


def map_public_url(url: str, audit_origin: str, canonical_host: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname == canonical_host:
        origin = urlparse(audit_origin)
        return urlunparse((origin.scheme, origin.netloc, parsed.path or "/", "", parsed.query, ""))
    return url


def add(findings: list[Finding], status: str, category: str, check: str, route: str, message: str,
        evidence: str = "", recommendation: str = "") -> None:
    findings.append(Finding(status, category, check, route, message, evidence, recommendation))


def analyze_page(public_url: str, body: bytes, findings: list[Finding]) -> PageParser:
    route = urlparse(public_url).path or "/"
    parser = PageParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    required = {
        "title": bool(parser.title), "description": bool(parser.description),
        "canonical": bool(parser.canonical), "language": bool(parser.lang),
        "viewport": "width=device-width" in parser.viewport,
    }
    for check, passed in required.items():
        add(findings, "pass" if passed else "fail", "SEO" if check in {"title", "description", "canonical"} else "Accessibility",
            check, route, f"{check.capitalize()} is present." if passed else f"{check.capitalize()} is missing.",
            recommendation="Add a unique, accurate value in the document head." if not passed else "")
    add(findings, "pass" if len(parser.h1) == 1 else "fail", "SEO", "single-h1", route,
        f"Found {len(parser.h1)} H1 element(s).", evidence=" | ".join(parser.h1),
        recommendation="Use one descriptive H1 for the page's primary topic.")
    title_ok = 15 <= len(parser.title) <= 65
    desc_ok = 70 <= len(parser.description) <= 170
    add(findings, "pass" if title_ok else "warn", "SEO", "title-length", route,
        f"Title length is {len(parser.title)} characters.", parser.title,
        "Keep the title concise and descriptive; roughly 15–65 characters is an audit heuristic, not a ranking rule.")
    add(findings, "pass" if desc_ok else "warn", "SEO", "description-length", route,
        f"Description length is {len(parser.description)} characters.", parser.description,
        "Write a useful page-specific summary; roughly 70–170 characters is an audit heuristic, not a ranking rule.")
    canonical_ok = urlparse(parser.canonical).path.rstrip("/") == route.rstrip("/") if parser.canonical else False
    add(findings, "pass" if canonical_ok else "fail", "SEO", "canonical-alignment", route,
        "Canonical path matches the page." if canonical_ok else "Canonical path does not match the page.", parser.canonical,
        "Use one absolute, self-referential canonical and list that same URL in the XML sitemap.")
    duplicate_ids = [value for value, count in Counter(parser.ids).items() if count > 1]
    add(findings, "pass" if not duplicate_ids else "fail", "Accessibility", "unique-ids", route,
        "IDs are unique." if not duplicate_ids else f"Duplicate IDs: {', '.join(duplicate_ids)}.")
    missing_alt = [src for src, alt in parser.images if alt is None]
    add(findings, "pass" if not missing_alt else "fail", "Accessibility", "image-alt", route,
        "Every image has an alt attribute." if not missing_alt else f"{len(missing_alt)} image(s) lack alt attributes.",
        " | ".join(missing_alt[:5]), "Give meaningful images concise alternatives and decorative images alt=\"\".")
    unlabeled = []
    for field in parser.inputs:
        if field.get("type", "").lower() in {"hidden", "submit", "button"}: continue
        field_id = field.get("id", "")
        if not (field.get("aria-label") or field.get("aria-labelledby") or (field_id and field_id in parser.labels_for)):
            unlabeled.append(field.get("name") or field_id or field["tag"])
    add(findings, "pass" if not unlabeled else "fail", "Accessibility", "form-labels", route,
        "Form controls have accessible labels." if not unlabeled else f"Unlabeled controls: {', '.join(unlabeled)}.")
    empty_actions = [href for href, text in parser.links if not text and not href.startswith("#")]
    empty_buttons = [text for text in parser.buttons if not text]
    add(findings, "pass" if not empty_actions and not empty_buttons else "fail", "Accessibility", "control-names", route,
        "Links and buttons have accessible text." if not empty_actions and not empty_buttons else "Some links or buttons have no text.")
    landmark_ok = parser.landmarks["main"] == 1 and parser.landmarks["nav"] >= 1
    add(findings, "pass" if landmark_ok else "warn", "Accessibility", "landmarks", route,
        f"Landmarks: main={parser.landmarks['main']}, nav={parser.landmarks['nav']}, footer={parser.landmarks['footer']}.",
        recommendation="Use one main landmark plus named navigation and footer landmarks.")
    structured_ok = True
    types: list[str] = []
    for block in parser.json_ld:
        try:
            value = json.loads(block)
            if isinstance(value, dict):
                graph = value.get("@graph", [value])
                for node in graph if isinstance(graph, list) else [value]:
                    if isinstance(node, dict) and node.get("@type"): types.append(str(node["@type"]))
        except json.JSONDecodeError:
            structured_ok = False
    noindex = "noindex" in parser.robots.lower()
    jsonld_pass = structured_ok and (bool(parser.json_ld) or noindex)
    jsonld_message = (
        "Structured data is optional on this intentionally noindex supporting page."
        if noindex and not parser.json_ld
        else f"Valid JSON-LD types: {', '.join(types) or 'none'}."
        if structured_ok
        else "JSON-LD is malformed."
    )
    add(findings, "pass" if jsonld_pass else "warn", "AI and structured data", "json-ld", route,
        jsonld_message, recommendation="Add only accurate JSON-LD that matches visible page content.")
    return parser


def render_report(base_url: str, findings: list[Finding], pages: dict[str, PageParser], output: Path) -> dict[str, object]:
    counts = Counter(f.status for f in findings)
    categories: dict[str, dict[str, int]] = {}
    for category in sorted({f.category for f in findings}):
        group = [f for f in findings if f.category == category]
        categories[category] = dict(Counter(f.status for f in group))
    report = {
        "site": base_url, "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": dict(counts), "categories": categories,
        "pages": sorted(pages), "findings": [asdict(f) for f in findings],
        "limitations": [
            "Automated checks cannot establish WCAG conformance or legal compliance.",
            "Manual keyboard, screen-reader, zoom, contrast, motion, cognitive clarity, and complete conversion-path testing remain required.",
            "Search engines and AI systems do not guarantee indexing, ranking, citations, or rich results.",
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Website readiness audit: {base_url}", "", f"Generated: {report['generatedAt']}", "",
             f"- Pages analyzed: {len(pages)}", f"- Passed checks: {counts['pass']}",
             f"- Warnings: {counts['warn']}", f"- Failures: {counts['fail']}", "",
             "## Important limitation", "", *[f"- {item}" for item in report["limitations"]], ""]
    for category in sorted(categories):
        lines.extend([f"## {category}", ""])
        for finding in [f for f in findings if f.category == category and f.status != "pass"]:
            lines.extend([f"### {finding.status.upper()}: {finding.check} — {finding.route}", "", finding.message])
            if finding.evidence: lines.extend(["", f"Evidence: `{finding.evidence}`"])
            if finding.recommendation: lines.extend(["", f"Recommendation: {finding.recommendation}"])
            lines.append("")
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    rows = "".join(
        f"<tr class='{f.status}'><td>{html.escape(f.status.upper())}</td><td>{html.escape(f.category)}</td>"
        f"<td>{html.escape(f.route)}</td><td>{html.escape(f.check)}</td><td>{html.escape(f.message)}</td>"
        f"<td>{html.escape(f.recommendation)}</td></tr>" for f in findings
    )
    page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Website readiness audit — {html.escape(base_url)}</title><style>
body{{margin:0;padding:32px;color:#18221d;background:#fbfbf7;font:16px/1.5 system-ui,sans-serif}}main{{max-width:1400px;margin:auto}}h1{{font-size:clamp(32px,5vw,64px)}}
.summary{{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}}.summary span{{padding:12px 16px;border-radius:10px;background:white;border:1px solid #d9dfdb;font-weight:750}}
table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:12px;text-align:left;vertical-align:top;border:1px solid #d9dfdb}}th{{background:#eaf0ed}}tr.fail td:first-child{{color:#9e281f;font-weight:800}}tr.warn td:first-child{{color:#865d0d;font-weight:800}}tr.pass td:first-child{{color:#1f624d;font-weight:800}}
</style></head><body><main><h1>Website readiness audit</h1><p>{html.escape(base_url)}</p><div class='summary'><span>{len(pages)} pages</span><span>{counts['pass']} pass</span><span>{counts['warn']} warnings</span><span>{counts['fail']} failures</span></div>
<p><strong>Scope:</strong> technical SEO, AI discovery, structured data, crawl surfaces, static accessibility signals, and shared navigation. This is not legal or WCAG certification.</p>
<table><thead><tr><th>Status</th><th>Area</th><th>Route</th><th>Check</th><th>Finding</th><th>Recommendation</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>"""
    (output / "index.html").write_text(page, encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit any public website and generate JSON, Markdown, and HTML reports.")
    ap.add_argument("--url", required=True, help="Website origin to fetch, for example https://example.com")
    ap.add_argument("--canonical-host", help="Expected canonical hostname; useful when auditing a local mirror")
    ap.add_argument("--output", default="outputs/public-website-readiness-audit")
    ap.add_argument("--max-pages", type=int, default=200)
    ap.add_argument("--include-path", action="append", default=[], help="Additional public path to audit, such as /thank-you")
    args = ap.parse_args()
    audit_origin = args.url.rstrip("/")
    canonical_host = args.canonical_host or urlparse(audit_origin).hostname or ""
    findings: list[Finding] = []
    pages: dict[str, PageParser] = {}
    sitemap_public_urls: list[str] = []

    for path in PUBLIC_FILES:
        status, headers, body, _ = fetch(audit_origin + path)
        add(findings, "pass" if status == 200 else "fail", "Crawl and AI discovery", path.lstrip("/") or path, path,
            f"HTTP {status}; content type {headers.get('content-type', 'unknown')}.",
            recommendation=f"Serve {path} directly with a 200 response." if status != 200 else "")
        if path == "/robots.txt" and status == 200:
            text = body.decode("utf-8", errors="replace")
            ok = bool(re.search(r"(?im)^\s*Sitemap:\s*https?://", text))
            add(findings, "pass" if ok else "fail", "Crawl and AI discovery", "robots-sitemap", path,
                "robots.txt names an absolute XML sitemap." if ok else "robots.txt does not name an absolute XML sitemap.")
        if path == "/sitemap.xml" and status == 200:
            try:
                root = ET.fromstring(body)
                ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                sitemap_public_urls = [n.text or "" for n in root.findall("s:url/s:loc", ns)]
                unique = len(sitemap_public_urls) == len(set(sitemap_public_urls))
                add(findings, "pass" if sitemap_public_urls and unique else "fail", "SEO", "xml-sitemap", path,
                    f"Found {len(sitemap_public_urls)} unique canonical URL(s)." if unique else "Sitemap is empty or contains duplicates.")
            except ET.ParseError as exc:
                add(findings, "fail", "SEO", "xml-sitemap", path, f"Malformed XML: {exc}.")
        if path in {"/llms.txt", "/llms-full.txt"} and status == 200:
            text = body.decode("utf-8", errors="replace")
            llms_ok = text.startswith("# ") and "\n> " in text and "https://" in text
            add(findings, "pass" if llms_ok else "warn", "AI and structured data", "llms-format", path,
                "File has a Markdown H1, summary, and absolute source links." if llms_ok else "File lacks the expected Markdown structure or source links.")

    seeds = list(sitemap_public_urls or [f"https://{canonical_host}/"])
    for path in args.include_path:
        public = f"https://{canonical_host}{'/' if not path.startswith('/') else ''}{path}"
        if public not in seeds: seeds.append(public)
    for public_url in seeds[: args.max_pages]:
        fetch_url = map_public_url(public_url, audit_origin, canonical_host)
        status, headers, body, _ = fetch(fetch_url)
        route = urlparse(public_url).path or "/"
        add(findings, "pass" if status == 200 else "fail", "Reliability", "page-status", route, f"HTTP {status}.")
        if status != 200 or "html" not in headers.get("content-type", ""): continue
        pages[route] = analyze_page(public_url, body, findings)

    required_nav = {"Find your starting point", "Why Audo", "Book free discovery"}
    for route, parser in pages.items():
        primary = set(parser.nav_texts[0]) if parser.nav_texts else set()
        missing = sorted(required_nav - primary)
        add(findings, "pass" if not missing else "fail", "Consistency", "primary-navigation", route,
            "Primary navigation contains the shared destinations." if not missing else f"Missing shared navigation: {', '.join(missing)}.",
            recommendation="Use the same visible primary destinations across public pages.")

    audit_host = urlparse(audit_origin).hostname or ""
    report_site = f"https://{canonical_host}" if canonical_host and canonical_host != audit_host else audit_origin
    report = render_report(report_site, findings, pages, Path(args.output))
    print(json.dumps({"output": str(Path(args.output).resolve()), "pages": len(pages), **report["summary"]}))
    return 1 if report["summary"].get("fail", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
