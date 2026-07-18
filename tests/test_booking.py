import tempfile
import unittest
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import server


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = server.DATABASE_PATH
        server.DATABASE_PATH = Path(self.temp_dir.name) / "consultations.sqlite3"
        server.init_db()

    def tearDown(self):
        server.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    def make_lead(self, *, name="Jamie Rivera", email="jamie@example.com"):
        payload = {
            "name": name,
            "company_name": "Rivera Hardware",
            "website": "https://example.com",
            "promo_code": "LOCAL",
            "email": email,
            "phone": "555-0100",
            "service": "Small business technology help",
            "timeline": "Schedule after request",
            "preferred_times": "",
            "message": "Our inventory workflow needs attention.",
            "source": "test",
            "interest_context": "test lead",
            "recaptcha_score": None,
            "recaptcha_action": None,
            "recaptcha_hostname": None,
        }
        request_id = server.store_request(payload, {})
        token = server.issue_booking_token(request_id)
        return request_id, token

    def test_candidate_slots_follow_hours_notice_cadence_and_sunday_block(self):
        now = datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)
        slots = server.candidate_slots(now)

        self.assertTrue(slots)
        self.assertGreaterEqual(slots[0][0], now + timedelta(hours=24))
        for start, end in slots:
            local_start = start.astimezone(server.BOOKING_ZONE)
            local_end = end.astimezone(server.BOOKING_ZONE)
            self.assertNotEqual(local_start.weekday(), 6)
            self.assertGreaterEqual(local_start.hour, 8)
            self.assertLessEqual(local_end.hour, 21)
            self.assertEqual((end - start).total_seconds(), 30 * 60)

        same_day = [start for start, _ in slots if start.astimezone(server.BOOKING_ZONE).date() == slots[0][0].astimezone(server.BOOKING_ZONE).date()]
        if len(same_day) > 1:
            self.assertEqual((same_day[1] - same_day[0]).total_seconds(), 45 * 60)

    def test_booking_token_authorizes_only_the_matching_lead(self):
        request_id, token = self.make_lead()

        lead = server.get_consultation_for_booking(request_id, token)
        self.assertEqual(lead["name"], "Jamie Rivera")
        with self.assertRaises(ValueError):
            server.get_consultation_for_booking(request_id, "wrong-token")

    def test_availability_filters_calendar_conflicts(self):
        now = datetime(2026, 7, 9, 12, 0, tzinfo=timezone.utc)
        first_start, first_end = server.candidate_slots(now)[0]
        with mock.patch.object(server, "google_busy_periods", return_value=[(first_start, first_end)]):
            days = server.build_availability(now)

        returned_starts = {
            slot["start"]
            for day in days
            for slot in day["slots"]
        }
        self.assertNotIn(first_start.isoformat().replace("+00:00", "Z"), returned_starts)
        self.assertTrue(returned_starts)

    def test_database_reservation_blocks_a_duplicate_slot(self):
        first_request, _ = self.make_lead()
        second_request, _ = self.make_lead(name="Morgan Lee", email="morgan@example.com")
        start, end = server.candidate_slots()[0]

        booking, created = server.reserve_booking(first_request, start, end)
        self.assertTrue(created)
        self.assertEqual(booking["status"], "pending")
        with self.assertRaises(server.BookingUnavailable):
            server.reserve_booking(second_request, start, end)

    def test_calendar_invite_contains_submitted_lead_information(self):
        request_id, token = self.make_lead()
        lead = server.get_consultation_for_booking(request_id, token)
        start, end = server.candidate_slots()[0]
        captured = {}

        def fake_request(method, endpoint, **kwargs):
            captured.update(kwargs["payload"])
            return {
                "id": "event-id",
                "htmlLink": "https://calendar.google.com/event?eid=test",
                "hangoutLink": "https://meet.google.com/abc-defg-hij",
            }

        with mock.patch.object(server, "google_calendar_request", side_effect=fake_request):
            server.create_calendar_event(lead, start, end, "audo-event-id")

        description = captured["description"]
        self.assertIn("Jamie Rivera", description)
        self.assertIn("jamie@example.com", description)
        self.assertIn("555-0100", description)
        self.assertIn("Rivera Hardware", description)
        self.assertIn("https://example.com", description)
        self.assertIn("Our inventory workflow needs attention.", description)
        self.assertEqual(captured["attendees"][0]["email"], "jamie@example.com")
        self.assertEqual(captured["attendees"][1]["email"], "matthewaaron@gmail.com")
        self.assertEqual(captured["conferenceData"]["createRequest"]["conferenceSolutionKey"]["type"], "hangoutsMeet")

    def test_audit_fixture_never_contacts_calendar_or_sends_email(self):
        request_id, token = self.make_lead()
        lead = server.get_consultation_for_booking(request_id, token)
        start, end = server.candidate_slots()[0]

        with mock.patch.object(server, "AUDIT_FIXTURES_ENABLED", True), mock.patch.object(
            server, "google_calendar_request"
        ) as calendar_request, mock.patch.object(server.smtplib, "SMTP") as smtp:
            self.assertTrue(server.calendar_configured())
            self.assertEqual(server.google_busy_periods(start, end), [])
            event = server.create_calendar_event(lead, start, end, "fixture-event")
            server.send_email(request_id, {"email": "jamie@example.com"}, {})

        calendar_request.assert_not_called()
        smtp.assert_not_called()
        self.assertEqual(event["hangoutLink"], "https://meet.google.com/fixture-audo-call")

    def test_hubspot_sync_upserts_contact_and_creates_associated_new_inquiry(self):
        request_id, _ = self.make_lead()
        payload = {
            "name": "Jamie Rivera",
            "company_name": "Rivera Hardware",
            "website": "https://example.com",
            "email": "jamie@example.com",
            "phone": "555-0100",
            "service": "Small business technology help",
            "message": "Our inventory workflow needs attention.",
            "interest_context": "Daily work",
        }
        calls = []

        def fake_request(endpoint, body):
            calls.append((endpoint, body))
            if endpoint.endswith("/batch/upsert"):
                return {"results": [{"id": "contact-123"}]}
            return {"id": "deal-456"}

        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=fake_request
        ):
            server.sync_hubspot(request_id, payload)

        self.assertEqual(calls[0][1]["inputs"][0]["id"], "jamie@example.com")
        self.assertEqual(calls[1][1]["properties"]["dealstage"], "appointmentscheduled")
        self.assertEqual(calls[1][1]["associations"][0]["to"]["id"], "contact-123")
        self.assertIn("Our inventory workflow needs attention.", calls[1][1]["properties"]["description"])
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_contact_id, hubspot_deal_id FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row, ("synced", "contact-123", "deal-456"))

    def test_hubspot_failure_does_not_raise_or_lose_the_saved_request(self):
        request_id, _ = self.make_lead()
        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=RuntimeError("temporary outage")
        ):
            server.sync_hubspot(request_id, {"name": "Jamie Rivera", "email": "jamie@example.com"})

        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_error FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row[0], "failed")
        self.assertIn("temporary outage", row[1])


if __name__ == "__main__":
    unittest.main()
