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
        for field in (
            "problem_heading",
            "goal_heading",
            "approach_heading",
            "form_heading",
            "faq_heading",
        ):
            self.assertEqual(len({card[field] for card in cards}), len(cards))

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

                self.assertEqual(len(card["steps"]), 3)
                self.assertEqual(len(card["faq_questions"]), 3)
                self.assertEqual(len(card["faq_answers"]), 3)

                page_copy = " ".join(
                    [
                        card["title"],
                        card["summary"],
                        card["result"],
                        card["problem_heading"],
                        card["goal_heading"],
                        card["approach_heading"],
                        card["form_heading"],
                        card["form_prompt"],
                        card["faq_heading"],
                        *card["steps"],
                        *card["faq_questions"],
                        *card["faq_answers"],
                    ]
                ).lower()
                for clinical_phrase in (
                    "approved facts",
                    "blocker",
                    "classify",
                    "compromised",
                    "conflicting records",
                    "current record",
                    "dashboard",
                    "dependencies",
                    "dependable",
                    "guided response",
                    "handoffs",
                    "impact, urgency",
                    "low-risk",
                    "practical uses",
                    "requirements",
                    "reusable",
                    "routing",
                    "scope",
                    "source links",
                    "submission path",
                    "suitable",
                    "technology basics",
                    "technology priorities",
                    "verifiable milestone",
                ):
                    self.assertNotIn(clinical_phrase, page_copy)

                for heading in (
                    card["problem_heading"],
                    card["goal_heading"],
                    card["approach_heading"],
                ):
                    self.assertLessEqual(len(heading.split()), 18)

                for step in card["steps"]:
                    self.assertLessEqual(len(step.split()), 15)

        self.assertEqual(
            len({step for card in cards for step in card["steps"]}),
            len(cards) * 3,
        )
        self.assertEqual(
            len(
                {
                    question
                    for card in cards
                    for question in card["faq_questions"]
                }
            ),
            len(cards) * 3,
        )

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

    def test_detail_page_faqs_are_expanded_by_default(self) -> None:
        server_source = (Path(__file__).resolve().parents[1] / "server.py").read_text()

        self.assertIn('f"""<details open>', server_source)
        self.assertIn('seed_message = display_title.rstrip(".!?") + "."', server_source)
        self.assertIn('required>{h(seed_message)}', server_source)
        self.assertNotIn("This is a real, fixable problem.", server_source)
        self.assertNotIn("A few questions you may have.", server_source)

    def test_explorer_actions_and_tabs_explain_and_support_their_behavior(self) -> None:
        index_html = (Path(__file__).resolve().parents[1] / "index.html").read_text()

        self.assertIn("Tell Aaron about this", index_html)
        self.assertIn("Read how I can help", index_html)
        self.assertIn('event.key === "ArrowRight"', index_html)
        self.assertIn('event.key === "Home"', index_html)
        self.assertIn("button.tabIndex = selected ? 0 : -1", index_html)
        self.assertIn(".problem-choice-summary {\n        display: none;", index_html)


if __name__ == "__main__":
    unittest.main()
