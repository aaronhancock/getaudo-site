import unittest
from collections import Counter

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


if __name__ == "__main__":
    unittest.main()
