import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HomepageExperienceTests(unittest.TestCase):
    def test_why_audo_section_uses_varied_accessible_cards(self) -> None:
        homepage = (ROOT / "index.html").read_text()

        self.assertIn("Senior experience.", homepage)
        self.assertIn("One person to call.", homepage)
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
        self.assertIn('href="mailto:getaudo@gmail.com"', homepage)
        self.assertIn("min-height: 44px", footer_css)
        self.assertIn(":focus-visible", footer_css)
        self.assertIn(".mega-footer .footer-nav {", footer_css)
        self.assertIn("display: block;", footer_css)
        self.assertIn("margin: 0;", footer_css)

    def test_mobile_scheduler_uses_a_compact_date_select(self) -> None:
        booking_js = (ROOT / "assets" / "booking.js").read_text()
        booking_css = (ROOT / "assets" / "booking.css").read_text()

        self.assertIn("data-booking-date-select", booking_js)
        self.assertIn('label for="booking-date-select"', booking_js)
        self.assertIn("dateSelect.addEventListener", booking_js)
        self.assertIn(".booking-mobile-date-field", booking_css)
        self.assertIn(".booking-date-list {\n    display: none;", booking_css)


if __name__ == "__main__":
    unittest.main()
