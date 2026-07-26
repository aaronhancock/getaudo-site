import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageExperienceTests(unittest.TestCase):
    def test_every_public_header_exposes_the_same_primary_destinations(self) -> None:
        shared_labels = ("Find your starting point", "Why Audo", "Book free discovery")
        sources = {
            "homepage": (ROOT / "index.html").read_text(),
            "privacy": (ROOT / "privacy.html").read_text(),
            "thank-you": (ROOT / "thank-you.html").read_text(),
            "generated pages": (ROOT / "server.py").read_text(),
        }
        for page, source in sources.items():
            with self.subTest(page=page):
                for label in shared_labels:
                    self.assertIn(label, source)

    def test_why_audo_section_uses_varied_accessible_cards(self) -> None:
        homepage = (ROOT / "index.html").read_text()

        self.assertIn("A small practice by design.", homepage)
        self.assertIn("stay with the work from start to finish", homepage)
        self.assertIn('class="why-portrait-card"', homepage)
        self.assertEqual(homepage.count('class="why-highlight-number"'), 3)
        self.assertIn("One person throughout", homepage)
        self.assertIn("Plain English", homepage)
        self.assertIn("Help that fits", homepage)

    def test_mega_footer_has_useful_navigation_and_contact_information(self) -> None:
        homepage = (ROOT / "index.html").read_text()
        footer_css = (ROOT / "assets" / "site-footer.css").read_text()

        self.assertIn('class="mega-footer"', homepage)
        self.assertIn('aria-label="Privacy and site information"', homepage)
        self.assertIn("Ways I can help", homepage)
        self.assertIn("Explore Audo", homepage)
        self.assertIn("What happens next", homepage)
        self.assertIn('href="mailto:aaron@getaudo.com"', homepage)
        self.assertIn("min-height: 44px", footer_css)
        self.assertIn(".footer-nav a {\n  min-height: 44px;", footer_css)
        self.assertIn(":focus-visible", footer_css)
        self.assertIn(".mega-footer .footer-nav {", footer_css)
        self.assertIn("display: block;", footer_css)
        self.assertIn("margin: 0;", footer_css)
        self.assertIn(".mega-footer .footer-legal {", footer_css)
        self.assertIn(".cookie-consent[hidden] {", footer_css)
        self.assertIn("display: none !important;", footer_css)

    def test_mobile_scheduler_uses_a_compact_date_select(self) -> None:
        booking_js = (ROOT / "assets" / "booking.js").read_text()
        booking_css = (ROOT / "assets" / "booking.css").read_text()

        self.assertIn("data-booking-date-select", booking_js)
        self.assertIn('label for="booking-date-select"', booking_js)
        self.assertIn("dateSelect.addEventListener", booking_js)
        self.assertIn(".booking-mobile-date-field", booking_css)
        self.assertIn(".booking-date-list {\n    display: none;", booking_css)
        self.assertIn("Your note is saved.", booking_js)
        self.assertIn('scheduler.setAttribute("aria-busy", "true")', booking_js)
        self.assertIn('<h4 tabindex="-1">', booking_js)

    def test_discovery_forms_load_privacy_minimized_attribution_before_booking(self) -> None:
        homepage = (ROOT / "index.html").read_text()
        server_source = (ROOT / "server.py").read_text()
        privacy = (ROOT / "privacy.html").read_text()
        thank_you = (ROOT / "thank-you.html").read_text()
        booking_js = (ROOT / "assets" / "booking.js").read_text()
        attribution_js = (ROOT / "assets" / "attribution.js").read_text()

        for source in (homepage, server_source):
            attribution_position = source.index("/assets/attribution.js?v=20260725-attribution1")
            booking_position = source.index("/assets/booking.js?v=20260725-attribution1")
            self.assertLess(attribution_position, booking_position)
        self.assertIn("window.AUDO_ATTRIBUTION.applyToForm(form)", booking_js)
        self.assertIn('"audo_attribution_context_v1"', attribution_js)
        self.assertIn('"utm_source"', attribution_js)
        self.assertNotIn('"gclid"', attribution_js)
        self.assertIn("privacy-minimized referring address", privacy)
        self.assertIn("If you submit the discovery form", privacy)
        self.assertIn("/assets/attribution.js?v=20260725-attribution1", privacy)
        self.assertIn("/assets/attribution.js?v=20260725-attribution1", thank_you)
        self.assertGreaterEqual(
            server_source.count("/assets/attribution.js?v=20260725-attribution1"),
            3,
        )
        self.assertIn('name="first_touch" value="__INITIAL_ATTRIBUTION__"', homepage)
        self.assertIn('name="latest_touch" value="__INITIAL_ATTRIBUTION__"', homepage)
        self.assertIn('name="first_touch" value="{initial_attribution}"', server_source)
        self.assertIn('name="latest_touch" value="{initial_attribution}"', server_source)

    def test_form_validation_identifies_and_focuses_the_field(self) -> None:
        booking_js = (ROOT / "assets" / "booking.js").read_text()
        booking_css = (ROOT / "assets" / "booking.css").read_text()

        self.assertIn("function showFieldError(fieldName, message)", booking_js)
        self.assertIn('field.setAttribute("aria-invalid", "true")', booking_js)
        self.assertIn('field.setAttribute("aria-describedby"', booking_js)
        self.assertIn("field.focus()", booking_js)
        self.assertIn("Enter an email address such as name@example.com.", booking_js)
        self.assertIn(".booking-date-list {\n  display: none;", booking_css)

    def test_unknown_routes_have_a_real_branded_404_recovery_page(self) -> None:
        server_source = (ROOT / "server.py").read_text()

        self.assertIn('self.render_not_found(send_body=send_body)', server_source)
        self.assertIn('<meta name="robots" content="noindex,follow">', server_source)
        self.assertIn("That page isn't here.", server_source)
        self.assertIn('self.send_response(HTTPStatus.NOT_FOUND)', server_source)
        self.assertNotIn('self.serve_index(send_body=send_body)\n\n    def serve_index', server_source)

    def test_scheduling_fallback_does_not_claim_a_note_on_direct_visit(self) -> None:
        thank_you = (ROOT / "thank-you.html").read_text()
        server_source = (ROOT / "server.py").read_text()

        self.assertNotIn("I have your note", thank_you)
        self.assertIn("__NOTE_FIRST_HIDDEN__", thank_you)
        self.assertIn("__BOOKING_CONTENT_HIDDEN__", thank_you)
        self.assertIn("Tell me a little first.", thank_you)
        self.assertIn('note_saved = "audo_note_saved=1"', server_source)
        self.assertIn('self.redirect("/thank-you", note_saved=True)', server_source)

    def test_consultation_forms_explain_privacy_and_follow_up(self) -> None:
        homepage = (ROOT / "index.html").read_text()
        server_source = (ROOT / "server.py").read_text()

        for source in (homepage, server_source):
            self.assertIn("How I handle your information", source)
            self.assertIn("reply within one business day", source)
            self.assertIn("/privacy#information", source)

    def test_mobile_navigation_exposes_browse_paths_with_focus_recovery(self) -> None:
        homepage = (ROOT / "index.html").read_text()

        self.assertIn('class="nav-menu-toggle"', homepage)
        self.assertIn('aria-controls="mobile-nav-menu"', homepage)
        self.assertIn('id="mobile-nav-menu" hidden', homepage)
        self.assertIn('event.key === "Escape"', homepage)
        self.assertIn('toggle.setAttribute("aria-expanded"', homepage)
        self.assertIn('<a href="#services">Find your starting point</a>', homepage)
        self.assertNotIn('<a href="#service-list">Real examples</a>', homepage)

    def test_homepage_help_choices_use_owner_language(self) -> None:
        homepage = (ROOT / "index.html").read_text()

        self.assertIn("What’s getting in your way?", homepage)
        self.assertIn("Something is broken, slow, confusing, or out of date.", homepage)
        self.assertIn("My customers and leads", homepage)
        self.assertIn("Work we do by hand", homepage)
        self.assertIn("Choose the right next step", homepage)
        self.assertIn("choosing tools, protecting information, or saving time", homepage)
        for phrase in (
            "hosting problems, analytics, integrations, accessibility",
            "customer portal, dashboard, prototype",
            "improve prompts",
            "Make a technology decision",
        ):
            self.assertNotIn(phrase, homepage)

    def test_cookie_and_sitemap_controls_meet_touch_and_focus_contracts(self) -> None:
        homepage = (ROOT / "index.html").read_text()
        privacy = (ROOT / "privacy.html").read_text()
        server_source = (ROOT / "server.py").read_text()

        for source in (homepage, privacy, server_source):
            self.assertIn("Allow analytics", source)
            self.assertIn('id="cookie-title" tabindex="-1"', source)
            self.assertIn("previousFocus", source)
        self.assertIn(".policy-summary a {\n      min-height: 44px;", privacy)
        self.assertIn(".sitemap-links a {{\n      min-height: 48px;", server_source)
        self.assertIn("header nav {{", server_source)
        self.assertIn(".category-jump-links a {{", server_source)
        self.assertIn("background: #fff;\n      color: var(--ink);", server_source)
        self.assertNotIn("\n    nav {{\n", server_source)

    def test_no_javascript_explorer_has_direct_plain_language_routes(self) -> None:
        homepage = (ROOT / "index.html").read_text()

        self.assertIn('<div class="explorer-noscript">', homepage)
        self.assertIn("Browse a few common starting points", homepage)
        self.assertIn("My website form is not working", homepage)
        self.assertIn("We copy the same information between tools", homepage)
        self.assertIn("Browse all examples", homepage)

    def test_legacy_public_routes_use_permanent_redirects(self) -> None:
        server_source = (ROOT / "server.py").read_text()

        self.assertIn('if path in {"/app", "/app/", "/app.html"}:\n            self.redirect_permanent("/")', server_source)
        self.assertIn('if path in {"/services", "/services/"}:\n            self.redirect_permanent("/#service-list")', server_source)


if __name__ == "__main__":
    unittest.main()
