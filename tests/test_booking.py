import tempfile
import unittest
import sqlite3
import inspect
import json
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

    def make_lead(
        self,
        *,
        name="Jamie Rivera",
        email="jamie@example.com",
        first_touch=None,
        latest_touch=None,
        request_meta=None,
    ):
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
            "first_touch": json.dumps(first_touch) if first_touch is not None else "",
            "latest_touch": json.dumps(latest_touch) if latest_touch is not None else "",
            "recaptcha_score": None,
            "recaptcha_action": None,
            "recaptcha_hostname": None,
        }
        request_id = server.store_request(payload, request_meta or {})
        token = server.issue_booking_token(request_id)
        return request_id, token

    def test_attribution_is_normalized_and_persisted_without_sensitive_url_parts(self):
        first = {
            "captured_at": "2026-07-25T15:00:00.000Z",
            "landing_url": "https://getaudo.com/services/fix-a-broken-contact-form?email=private@example.com#form",
            "referring_url": "https://www.linkedin.com/feed/?tracking=secret#item",
            "utm_source": "linkedin",
            "utm_medium": "direct_outreach",
            "utm_campaign": "lead_flow_pilot",
            "utm_content": "observed_form_issue",
            "utm_term": "must be discarded",
            "gclid": "must-be-discarded",
        }
        request_id, _ = self.make_lead(first_touch=first, latest_touch=first)

        with sqlite3.connect(server.DATABASE_PATH) as conn:
            first_raw, latest_raw = conn.execute(
                "SELECT first_touch_json, latest_touch_json FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        persisted = json.loads(first_raw)
        self.assertEqual(
            persisted["landing_url"],
            "https://getaudo.com/services/fix-a-broken-contact-form",
        )
        self.assertEqual(persisted["referring_url"], "https://www.linkedin.com/")
        self.assertEqual(persisted["utm_source"], "linkedin")
        self.assertNotIn("utm_term", persisted)
        self.assertNotIn("gclid", persisted)
        self.assertEqual(json.loads(latest_raw), persisted)

    def test_http_referrer_metadata_is_reduced_to_origin(self):
        request_id, _ = self.make_lead(
            request_meta={
                "referrer": "https://external.example/reset/private-token?secret=x#account"
            }
        )
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            referrer = conn.execute(
                "SELECT referrer FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()[0]
        self.assertEqual(referrer, "https://external.example/")

    def test_initial_request_attribution_supports_direct_no_javascript_submission(self):
        with mock.patch.object(server, "PUBLIC_BASE_URL", "https://getaudo.com"):
            attribution = server.initial_request_attribution(
                "/services/fix-a-broken-contact-form"
                "?utm_source=linkedin&utm_campaign=lead-flow&email=private@example.com",
                "https://www.linkedin.com/feed/?tracking=secret",
            )

        self.assertEqual(
            attribution["landing_url"],
            "https://getaudo.com/services/fix-a-broken-contact-form",
        )
        self.assertEqual(attribution["referring_url"], "https://www.linkedin.com/")
        self.assertEqual(attribution["utm_source"], "linkedin")
        self.assertEqual(attribution["utm_campaign"], "lead-flow")
        self.assertNotIn("email", attribution)

    def test_initial_request_attribution_ignores_internal_referrer(self):
        with mock.patch.object(server, "PUBLIC_BASE_URL", "https://getaudo.com"):
            attribution = server.initial_request_attribution(
                "/?audo_campaign=warm-intro",
                "https://getaudo.com/privacy?private=value",
            )

        self.assertEqual(attribution["audo_campaign"], "warm-intro")
        self.assertNotIn("referring_url", attribution)

    def test_malformed_or_unsafe_attribution_does_not_reject_the_lead(self):
        payload = {
            "landing_url": "javascript:alert(1)",
            "referring_url": "https://user:password@example.com/private?token=secret",
            "utm_source": "line one\nline two",
        }
        request_id, _ = self.make_lead(first_touch=payload)
        second_request, _ = self.make_lead(
            name="Morgan Lee",
            email="morgan@example.com",
        )
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            first_raw = conn.execute(
                "SELECT first_touch_json FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()[0]
            conn.execute(
                "UPDATE consultation_requests SET first_touch_json = NULL, latest_touch_json = NULL WHERE id = ?",
                (second_request,),
            )
        persisted = json.loads(first_raw)
        self.assertNotIn("landing_url", persisted)
        self.assertNotIn("referring_url", persisted)
        self.assertEqual(persisted["utm_source"], "line one line two")

        self.assertIsNone(server.normalized_attribution_json("{not-json"))
        self.assertIsNone(server.normalized_attribution_json(["not", "an", "object"]))

        forged = {
            "landing_url": "https://evil.example/copied-form",
            "referring_url": "https://partner.example/private/path?token=secret",
        }
        forged_request, _ = self.make_lead(
            name="Taylor Morgan",
            email="taylor@example.com",
            first_touch=forged,
        )
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            forged_raw = conn.execute(
                "SELECT first_touch_json FROM consultation_requests WHERE id = ?",
                (forged_request,),
            ).fetchone()[0]
        persisted_forged = json.loads(forged_raw)
        self.assertNotIn("landing_url", persisted_forged)
        self.assertEqual(persisted_forged["referring_url"], "https://partner.example/")

    def test_attribution_migration_is_additive_idempotent_and_preserves_existing_rows(self):
        request_id, _ = self.make_lead()
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            conn.execute("ALTER TABLE consultation_requests DROP COLUMN first_touch_json")
            conn.execute("ALTER TABLE consultation_requests DROP COLUMN latest_touch_json")

        server.init_db()
        server.init_db()

        with sqlite3.connect(server.DATABASE_PATH) as conn:
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(consultation_requests)")
            }
            email = conn.execute(
                "SELECT email FROM consultation_requests WHERE id = ?", (request_id,)
            ).fetchone()[0]
        self.assertIn("first_touch_json", columns)
        self.assertIn("latest_touch_json", columns)
        self.assertEqual(email, "jamie@example.com")

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

    def test_owner_email_failure_is_persisted_and_retried(self):
        request_id, _ = self.make_lead()
        with mock.patch.object(server, "GMAIL_API_SEND_ENABLED", True), mock.patch.object(
            server, "deliver_email_message", side_effect=RuntimeError("temporary Gmail outage")
        ):
            server.send_email(request_id, {"name": "Jamie Rivera", "email": "jamie@example.com"}, {})

        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT email_status, email_attempt_count, email_next_attempt_at FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            conn.execute(
                "UPDATE consultation_requests SET email_next_attempt_at = ? WHERE id = ?",
                (server.utc_now(), request_id),
            )
        self.assertEqual(row[0], "retry")
        self.assertEqual(row[1], 1)
        self.assertTrue(row[2])

        with mock.patch.object(server, "GMAIL_API_SEND_ENABLED", True), mock.patch.object(
            server, "deliver_email_message"
        ) as deliver:
            self.assertEqual(server.reconcile_email_deliveries(limit=1), 1)

        deliver.assert_called_once()
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            status, attempts = conn.execute(
                "SELECT email_status, email_attempt_count FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(status, "sent")
        self.assertEqual(attempts, 2)

    def test_owner_email_uses_a_stable_message_id_for_retries(self):
        message = server.build_email(
            42,
            {
                "name": "Jamie Rivera",
                "email": "jamie@example.com",
                "service": "Small business technology help",
                "message": "Please help.",
            },
            {},
        )
        self.assertEqual(message["Message-ID"], "<audo-consultation-42@getaudo.com>")

    def test_hubspot_sync_upserts_contact_and_creates_associated_new_inquiry(self):
        first_touch = {
            "captured_at": "2026-07-25T15:00:00.000Z",
            "landing_url": "https://getaudo.com/services/fix-a-broken-contact-form",
            "referring_url": "https://www.linkedin.com/",
            "utm_source": "linkedin",
            "utm_medium": "direct_outreach",
            "utm_campaign": "lead_flow_pilot",
            "utm_content": "observed_form_issue",
        }
        latest_touch = {
            **first_touch,
            "captured_at": "2026-07-25T15:05:00.000Z",
            "landing_url": "https://getaudo.com/",
            "audo_campaign": "warm_followup",
        }
        request_id, _ = self.make_lead(
            first_touch=first_touch,
            latest_touch=latest_touch,
        )
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
            if endpoint.endswith("/contacts/search"):
                return {"results": []}
            if endpoint.endswith("/contacts/batch/upsert"):
                return {"results": [{"id": "contact-123"}]}
            if endpoint.endswith("/deals/search"):
                return {"results": []}
            return {"id": "deal-456"}

        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=fake_request
        ):
            server.sync_hubspot(request_id, payload)

        upsert = next(
            body for endpoint, body in calls if endpoint.endswith("/contacts/batch/upsert")
        )
        deal_create = next(
            body for endpoint, body in calls if endpoint.endswith("/deals")
        )
        self.assertEqual(upsert["inputs"][0]["id"], "jamie@example.com")
        self.assertEqual(upsert["inputs"][0]["properties"]["lifecyclestage"], "lead")
        self.assertEqual(upsert["inputs"][0]["properties"]["hs_lead_status"], "NEW")
        self.assertEqual(deal_create["properties"]["dealstage"], "appointmentscheduled")
        self.assertEqual(deal_create["associations"][0]["to"]["id"], "contact-123")
        self.assertIn("Website request #", deal_create["properties"]["dealname"])
        self.assertIn("Our inventory workflow needs attention.", deal_create["properties"]["description"])
        self.assertIn("First touch referrer: https://www.linkedin.com/", deal_create["properties"]["description"])
        self.assertEqual(deal_create["properties"]["audo_first_source"], "linkedin")
        self.assertEqual(
            deal_create["properties"]["audo_first_landing_url"],
            "https://getaudo.com/services/fix-a-broken-contact-form",
        )
        self.assertEqual(deal_create["properties"]["audo_latest_campaign_code"], "warm_followup")
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_contact_id, hubspot_deal_id FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row, ("synced", "contact-123", "deal-456"))

    def test_hubspot_existing_contact_preserves_lifecycle_and_lead_status(self):
        request_id, _ = self.make_lead()
        calls = []

        def fake_request(endpoint, body):
            calls.append((endpoint, body))
            if endpoint.endswith("/contacts/search"):
                return {"results": [{"id": "existing-contact"}]}
            if endpoint.endswith("/contacts/batch/update"):
                return {"status": "COMPLETE"}
            if endpoint.endswith("/deals/search"):
                return {"results": []}
            if endpoint.endswith("/deals"):
                return {"id": "deal-456"}
            self.fail(f"Unexpected HubSpot endpoint: {endpoint}")

        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=fake_request
        ):
            server.sync_hubspot(request_id)

        update = next(
            body for endpoint, body in calls if endpoint.endswith("/contacts/batch/update")
        )
        properties = update["inputs"][0]["properties"]
        self.assertNotIn("lifecyclestage", properties)
        self.assertNotIn("hs_lead_status", properties)

    def test_confirmed_booking_advances_existing_deal_to_discovery_scheduled(self):
        request_id, _ = self.make_lead(
            first_touch={
                "landing_url": "https://getaudo.com/services/fix-a-broken-contact-form",
                "referring_url": "https://www.google.com/",
                "utm_source": "google",
                "utm_campaign": "lead_flow",
            }
        )
        start, end = server.candidate_slots()[0]
        booking, _ = server.reserve_booking(request_id, start, end)
        server.finalize_booking(
            int(booking["id"]),
            {
                "id": "calendar-event",
                "htmlLink": "https://calendar.google.com/event?eid=test",
                "hangoutLink": "https://meet.google.com/abc-defg-hij",
            },
        )
        server.save_hubspot_ids(request_id, contact_id="contact-123", deal_id="deal-456")
        calls = []

        def fake_request(endpoint, body):
            calls.append((endpoint, body))
            if endpoint.endswith("/batch/upsert"):
                return {"results": [{"id": "contact-123"}]}
            return {"status": "COMPLETE"}

        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=fake_request
        ):
            server.queue_hubspot_sync(request_id, force=True)
            claimed = server.claim_next_hubspot_sync(request_id)
            self.assertIsNotNone(claimed)
            server.sync_claimed_hubspot_request(claimed)

        update = next(body for endpoint, body in calls if endpoint.endswith("/deals/batch/update"))
        self.assertEqual(update["inputs"][0]["id"], "deal-456")
        self.assertEqual(update["inputs"][0]["properties"]["dealstage"], "qualifiedtobuy")
        self.assertEqual(update["inputs"][0]["properties"]["audo_first_source"], "google")
        self.assertIn("First touch landing:", update["inputs"][0]["properties"]["description"])
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            status = conn.execute(
                "SELECT hubspot_status FROM consultation_requests WHERE id = ?", (request_id,)
            ).fetchone()[0]
        self.assertEqual(status, "synced")

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
        self.assertEqual(row[0], "retry")
        self.assertIn("temporary outage", row[1])

    def test_hubspot_enqueue_never_calls_the_network(self):
        request_id, _ = self.make_lead()
        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request"
        ) as hubspot_request:
            server.queue_hubspot_sync(request_id)

        hubspot_request.assert_not_called()
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_attempt_count FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row, ("queued", 0))
        handler_source = inspect.getsource(server.AudoHandler.handle_consultation_post)
        self.assertIn("queue_hubspot_sync(request_id)", handler_source)
        self.assertNotIn("sync_hubspot(request_id", handler_source)

    def test_request_store_persists_the_hubspot_job_atomically(self):
        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request"
        ) as hubspot_request:
            request_id, _ = self.make_lead()

        hubspot_request.assert_not_called()
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_next_attempt_at FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row[0], "queued")
        self.assertTrue(row[1])

    def test_hubspot_retry_finds_the_created_deal_instead_of_creating_a_duplicate(self):
        request_id, _ = self.make_lead(
            first_touch={
                "landing_url": "https://getaudo.com/services/fix-a-broken-contact-form",
                "referring_url": "https://partner.example/resources",
                "utm_source": "partner",
                "utm_campaign": "lead_flow",
            }
        )
        external_deal = {"id": ""}
        create_count = 0
        stage_updates = []

        def fake_request(endpoint, body):
            nonlocal create_count
            if endpoint.endswith("/contacts/search"):
                return {"results": []}
            if endpoint.endswith("/contacts/batch/upsert"):
                return {"results": [{"id": "contact-123"}]}
            if endpoint.endswith("/contacts/batch/update"):
                return {"status": "COMPLETE"}
            if endpoint.endswith("/deals/search"):
                return {"results": [{"id": external_deal["id"]}]} if external_deal["id"] else {"results": []}
            if endpoint.endswith("/deals"):
                create_count += 1
                external_deal["id"] = "deal-created-before-timeout"
                raise RuntimeError("connection dropped after create")
            if endpoint.endswith("/deals/batch/update"):
                stage_updates.append(body)
                return {"status": "COMPLETE"}
            self.fail(f"Unexpected HubSpot endpoint: {endpoint}")

        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "hubspot_request", side_effect=fake_request
        ):
            server.sync_hubspot(request_id)
            start, end = server.candidate_slots()[0]
            booking, _ = server.reserve_booking(request_id, start, end)
            server.finalize_booking(
                int(booking["id"]),
                {
                    "id": "calendar-event",
                    "htmlLink": "https://calendar.google.com/event?eid=test",
                    "hangoutLink": "https://meet.google.com/abc-defg-hij",
                },
            )
            with sqlite3.connect(server.DATABASE_PATH) as conn:
                conn.execute(
                    "UPDATE consultation_requests SET hubspot_next_attempt_at = ? WHERE id = ?",
                    ((datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(timespec="seconds"), request_id),
                )
            server.sync_hubspot(request_id)

        self.assertEqual(create_count, 1)
        self.assertEqual(stage_updates[0]["inputs"][0]["id"], "deal-created-before-timeout")
        self.assertEqual(stage_updates[0]["inputs"][0]["properties"]["dealstage"], "qualifiedtobuy")
        self.assertEqual(stage_updates[0]["inputs"][0]["properties"]["audo_first_source"], "partner")
        self.assertEqual(
            stage_updates[0]["inputs"][0]["properties"]["audo_first_referring_url"],
            "https://partner.example/",
        )
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                """
                SELECT hubspot_status, hubspot_deal_id, hubspot_attempt_count
                FROM consultation_requests WHERE id = ?
                """,
                (request_id,),
            ).fetchone()
        self.assertEqual(row, ("synced", "deal-created-before-timeout", 2))

    def test_hubspot_reconciliation_reclaims_a_stale_sync(self):
        request_id, _ = self.make_lead()
        stale_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            conn.execute(
                """
                UPDATE consultation_requests
                SET hubspot_status = 'syncing', hubspot_attempt_count = 1,
                    hubspot_last_attempt_at = ?, hubspot_next_attempt_at = NULL
                WHERE id = ?
                """,
                (stale_at, request_id),
            )

        claimed = server.claim_next_hubspot_sync()

        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["id"], request_id)
        self.assertEqual(claimed["hubspot_attempt_count"], 2)

    def test_hubspot_reconciliation_claims_a_legacy_failed_sync(self):
        request_id, _ = self.make_lead()
        with sqlite3.connect(server.DATABASE_PATH) as conn:
            conn.execute(
                """
                UPDATE consultation_requests
                SET hubspot_status = 'failed', hubspot_attempt_count = 0,
                    hubspot_next_attempt_at = NULL
                WHERE id = ?
                """,
                (request_id,),
            )

        claimed = server.claim_next_hubspot_sync()

        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["id"], request_id)
        self.assertEqual(claimed["hubspot_attempt_count"], 1)

    def test_hubspot_retry_becomes_terminal_after_the_attempt_limit(self):
        request_id, _ = self.make_lead()
        with mock.patch.object(server, "HUBSPOT_SERVICE_KEY", "test-key"), mock.patch.object(
            server, "HUBSPOT_SYNC_MAX_ATTEMPTS", 1
        ), mock.patch.object(server, "hubspot_request", side_effect=RuntimeError("permanent outage")):
            server.sync_hubspot(request_id)

        with sqlite3.connect(server.DATABASE_PATH) as conn:
            row = conn.execute(
                "SELECT hubspot_status, hubspot_next_attempt_at FROM consultation_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
        self.assertEqual(row, ("failed", None))


if __name__ == "__main__":
    unittest.main()
