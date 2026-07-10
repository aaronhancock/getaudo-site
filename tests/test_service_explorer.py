import unittest
from collections import Counter
from pathlib import Path

from services import service_cards


class ServiceExplorerTests(unittest.TestCase):
    def test_explorer_has_six_plain_language_examples_per_group(self) -> None:
        cards = service_cards()

        self.assertEqual(len(cards), 30)
        self.assertEqual(
            Counter(card["group"] for card in cards),
            {
                "website": 6,
                "customers": 6,
                "work": 6,
                "ai": 6,
                "decisions": 6,
            },
        )
        self.assertEqual(len({card["title"] for card in cards}), len(cards))
        self.assertEqual(len({card["url"] for card in cards}), len(cards))

        for card in cards:
            with self.subTest(title=card["title"]):
                self.assertTrue(card["title"])
                self.assertTrue(card["summary"])
                self.assertTrue(card["result"])
                self.assertTrue(card["url"].startswith("/services/"))
                self.assertTrue(
                    card["title"].startswith(
                        (
                            "My ",
                            "I ",
                            "Every ",
                            "Customers ",
                            "Customer ",
                            "Writing ",
                            "One ",
                            "We ",
                            "It ",
                        )
                    )
                )

                owner_copy = " ".join(
                    (card["title"], card["summary"], card["result"])
                ).lower()
                for industry_phrase in (
                    "workflow",
                    "crm",
                    "off-the-shelf",
                    "scope",
                    "technology basics",
                    "technology priorities",
                    "technical problems",
                    "client data",
                ):
                    self.assertNotIn(industry_phrase, owner_copy)

    def test_example_choice_keeps_the_message_field_open_ended(self) -> None:
        index_html = (Path(__file__).resolve().parents[1] / "index.html").read_text()

        self.assertNotIn(
            'prefill: "This sounds familiar: " + selectedService.title',
            index_html,
        )
        self.assertGreaterEqual(index_html.count('prefill: ""'), 2)
        self.assertIn(
            "What have you noticed? What would you like to be easier?",
            index_html,
        )


if __name__ == "__main__":
    unittest.main()
