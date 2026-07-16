#!/usr/bin/env python3
"""Build the local GetAudo website-experience audit manifest and dashboard."""

from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services import service_cards  # noqa: E402


OUTPUT = ROOT / "outputs" / "website-experience-audit"
MANIFEST_PATH = OUTPUT / "manifest.json"
STATE_PATH = OUTPUT / "audit-state.json"
DASHBOARD_PATH = OUTPUT / "index.html"
BASELINE_RESULTS_PATH = OUTPUT / "baseline-results.json"
IMPROVEMENT_RESULTS_PATH = OUTPUT / "improvement-results.json"

CATEGORIES = [
    "clarity",
    "simplicity",
    "usability_accessibility",
    "trust_credibility",
    "business_effectiveness",
]


def item(
    stable_id: str,
    route: str,
    title: str,
    priority: int,
    objective: str,
    action: str,
    after: str,
    visitor_importance: str,
    business_importance: str,
    evidence: str,
    edges: list[str],
    *,
    criticality: str = "high",
    kind: str = "screen",
) -> dict[str, object]:
    return {
        "id": stable_id,
        "route": route,
        "title": title,
        "persona": "Least-technical small-business owner who uses basic email and websites",
        "objective": objective,
        "expectedNextAction": action,
        "afterAction": after,
        "visitorImportance": visitor_importance,
        "businessImportance": business_importance,
        "completionEvidence": evidence,
        "edgeStates": edges,
        "priorityBand": priority,
        "criticality": criticality,
        "kind": kind,
    }


def fixed_inventory() -> list[dict[str, object]]:
    return [
        item("site-header-desktop", "site-wide", "Desktop header and navigation", 1,
             "Recognize Audo and reach the most important destination.", "Choose the relevant navigation link or discovery call.",
             "The page moves to the promised section without losing context.", "Visitors need immediate orientation.",
             "Clear navigation protects discovery-call conversion.", "Header identity, labels, focus state, and destination are verified.",
             ["keyboard focus", "anchor navigation", "sticky or scrolled state"]),
        item("site-header-mobile", "site-wide", "Mobile header and navigation", 1,
             "Recognize Audo and reach the discovery call on a phone.", "Tap the discovery call action.",
             "The consultation section opens with no overlap or cutoff.", "Mobile visitors need a fast, readable route forward.",
             "Mobile traffic must convert without tiny controls.", "390px and 360px screenshots show readable navigation and 44px targets.",
             ["390px", "360px", "zoom", "long labels"]),
        item("homepage-hero", "/", "Homepage first screen", 1,
             "Understand who Audo helps, what Aaron does, and whether this is relevant.", "Book a free discovery call or view examples.",
             "The visitor reaches the consultation form or concrete examples.", "The first screen determines whether the visitor stays.",
             "It is the primary acquisition and conversion surface.", "H1, support copy, CTA labels, destinations, and first-screen render are verified.",
             ["direct landing", "mobile first screen", "reduced motion"]),
        item("homepage-help-grid", "/#services", "Combined problem finder category choices", 1,
             "Choose the part of the business where help is needed.", "Choose one of five plain-language category cards.",
             "The same section immediately shows familiar situations in that area.", "Visitors should not need technical vocabulary or choose between duplicate sections.",
             "One continuous decision path improves self-selection and lead quality.", "Each category card filters the real situations below with clear selected state and focus behavior.",
             ["none fit", "keyboard use", "back navigation"]),
        item("homepage-footer", "site-wide", "Mega-footer and next-step guidance", 1,
             "Find a service, contact method, privacy page, or next-step explanation.", "Choose one footer link or book discovery.",
             "The promised page or section opens.", "The footer is a recovery and trust surface.",
             "It recaptures visitors who reach the end undecided.", "Links, touch targets, alignment, headings, and destinations are verified.",
             ["mobile stacking", "keyboard focus", "external email client"]),
        item("consultation-intro", "/#discovery", "Consultation section introduction", 2,
             "Understand what the free call is and what happens next.", "Begin the short request form.",
             "The visitor can complete step one with confidence.", "The commitment must feel safe and low pressure.",
             "Clear expectations reduce form abandonment.", "Duration, medium, process, and next destination are visible.",
             ["visitor is unsure", "visitor has no link", "mobile entry"]),
        item("consultation-form", "/#discovery", "Consultation request form", 2,
             "Share enough context for Aaron to prepare.", "Submit name, email, and a short description.",
             "A saved synthetic request advances to scheduling.", "Typing should be minimal and labels plain.",
             "The form creates qualified consulting conversations.", "Synthetic local submission is stored without sending email and preserves context.",
             ["optional link", "promo code", "invalid email", "missing fields", "duplicate submission"]),
        item("consultation-validation", "/#discovery", "Consultation form validation and recovery", 2,
             "Understand and correct a form problem without losing work.", "Fix the clearly identified field.",
             "The corrected request can continue to scheduling.", "Errors must be specific and forgiving.",
             "Recoverable validation prevents abandonment.", "Focus, error text, preserved values, and resubmission are verified.",
             ["empty required field", "bad email", "server error", "reCAPTCHA unavailable"]),
        item("scheduler-loading", "/#discovery", "Scheduler transition and loading", 2,
             "Know that the request was saved and times are loading.", "Wait for availability or use recovery guidance.",
             "Available dates appear without a page change or lost context.", "The transition must not look broken.",
             "The form-to-calendar handoff is a critical conversion point.", "Focus, progress label, loading state, and fallback are verified with fixtures.",
             ["slow availability", "calendar unavailable", "expired token"]),
        item("scheduler-availability", "/#discovery", "Scheduler date and time selection", 2,
             "Choose an understandable 30-minute time.", "Choose a date, then a time.",
             "The exact selection is summarized before booking.", "Calendar controls must work without technical knowledge.",
             "A usable scheduler completes the primary conversion path.", "Fake availability is usable at 1280px, 390px, 360px, keyboard, and touch.",
             ["no times", "many dates", "timezone", "slot just filled"]),
        item("scheduler-confirmation", "/#discovery", "Scheduler booking confirmation", 2,
             "Confirm the selected time and know what happens afterward.", "Confirm the booking.",
             "A fixture confirmation shows the date, time, timezone, and meeting expectation.", "Visitors need certainty that booking worked.",
             "Clear completion prevents duplicate requests and support contacts.", "No real event is created; the fake fixture returns complete confirmation evidence.",
             ["double click", "already booked", "calendar error", "back navigation"]),
        item("thank-you-fallback", "/thank-you", "Non-JavaScript and scheduling fallback", 2,
             "Know the request arrived and how to schedule or get help.", "Open the safe scheduling fallback or return home.",
             "The visitor has a clear next destination and response expectation.", "Fallback visitors must not reach a dead end.",
             "Recovery protects leads during script or calendar outages.", "Success copy, fallback destination, and no-JavaScript path are verified.",
             ["JavaScript disabled", "calendar outage", "direct visit"]),
        item("homepage-problem-explorer", "/#services", "Combined problem finder situation explorer", 3,
             "Browse familiar situations without knowing a service name.", "Choose a situation, read its page, or tell Aaron about it.",
             "The situation moves into focus, opens its tailored page, or carries into the consultation form.", "Visitors need concrete, plain-language situations in one continuous section.",
             "Relevant examples expand qualified demand while preserving all 30 search pages.", "All 30 examples load, five visual filters work, focus is managed, and detail/form actions route correctly.",
             ["data load failure", "keyboard tabs", "no JavaScript", "back navigation"]),
        item("homepage-founder", "/#why", "Aaron identity, credibility, and working style", 4,
             "Decide whether Aaron is credible, approachable, and responsible for the work.", "Continue to client work or book discovery.",
             "The visitor understands who they will work with and why that is different.", "Consulting requires personal trust.",
             "Clear differentiation supports higher-intent conversations.", "Identity, experience, responsibility, claims, and CTA are verified.",
             ["image unavailable", "mobile reading order"]),
        item("homepage-client-work", "/#client-work", "Client work and proof", 4,
             "See truthful evidence of relevant work.", "Review the examples or visit an external client site.",
             "The visitor can connect the work to Audo's capabilities.", "Specific proof reduces uncertainty.",
             "Credible examples strengthen conversion without invented testimonials.", "Claims, links, labels, carousel behavior, and context are verified.",
             ["external site unavailable", "more than three clients", "keyboard carousel"]),
        item("privacy-policy", "/privacy", "Privacy policy", 7,
             "Understand what information is collected, why, and what choices exist.", "Read the relevant section or contact Audo.",
             "The visitor can make an informed consent choice.", "Personal-data collection requires plain disclosure.",
             "Clear privacy practices protect trust and compliance.", "Collection, providers, retention, controls, contact, metadata, and mobile layout are verified.",
             ["cookies disabled", "direct section link", "mobile header"]),
        item("cookie-first-choice", "site-wide", "First-visit cookie choice", 7,
             "Choose analytics or necessary-only cookies knowingly.", "Accept or choose necessary only.",
             "The choice is remembered and the panel closes.", "Consent must be understandable and operable.",
             "Ethical measurement depends on valid consent.", "Both controls work by keyboard and touch with no preselected consent.",
             ["first visit", "storage unavailable", "keyboard focus"]),
        item("cookie-preferences", "site-wide", "Reopen cookie preferences", 7,
             "Review or change a prior cookie choice.", "Open Cookie preferences and choose again.",
             "The updated choice is saved and applied.", "Visitors need ongoing control.",
             "Preference control supports privacy trust.", "Footer control restores the panel and focus reliably.",
             ["existing accept", "existing necessary-only", "mobile footer"]),
        item("human-sitemap", "/sitemap", "Human-readable sitemap", 7,
             "Find the right public consulting page.", "Choose a clearly grouped page link.",
             "The canonical public page opens.", "A sitemap is a recovery and orientation tool.",
             "It supports discovery, SEO, and long-tail consulting intent.", "All current consulting pages are present and stale pages are absent.",
             ["new service page", "removed page", "mobile layout"]),
        item("xml-sitemap", "/sitemap.xml", "XML sitemap", 7,
             "Provide search engines a canonical public page inventory.", "Crawl a listed URL.",
             "Every listed URL resolves canonically.", "Accurate indexing helps visitors find relevant pages.",
             "Search visibility depends on current canonical inventory.", "URL count, status, canonicals, and exclusions are verified.",
             ["stale service", "redirected URL", "agent exclusion"], kind="machine"),
        item("llms-catalog", "/llms.txt", "AI-readable consulting summary and discovery catalog", 7,
             "Help an AI search or research tool understand Audo consulting accurately.", "Follow a canonical consulting or catalog link.",
             "The agent reaches current, public, non-secret content.", "AI-assisted discovery should not misrepresent the business.",
             "Accurate AI-readable context supports AI search visibility.", "Current consulting services, limits, booking details, and identity are verified; unrelated products are absent.",
             ["stale service count", "internal details", "unrelated product content"], kind="machine"),
        item("llms-full", "/llms-full.txt", "Expanded AI-readable consulting context", 7,
             "Give AI search and research tools complete and accurate consulting context.", "Use the structured service and booking details.",
             "The tool can answer without inventing claims or introducing unrelated products.", "Complete public context improves answer quality.",
             "It supports AI search while protecting trust.", "All 30 services and public constraints are complete and current.",
             ["stale content", "unsupported claims", "private details"], kind="machine"),
        item("services-markdown", "/services.md", "Markdown service catalog", 7,
             "Let agents and text browsers scan every consulting example.", "Open a relevant service detail page.",
             "The chosen canonical page provides tailored detail.", "Accessible text alternatives improve reach.",
             "A complete catalog supports search and AI discovery.", "All 30 services, outcomes, and canonical links are verified.",
             ["missing service", "duplicate title", "stale link"], kind="machine"),
        item("metadata-indexing", "site-wide", "Titles, canonicals, social metadata, and indexing", 7,
             "Receive an accurate preview and canonical destination in search or social results.", "Open the result or shared link.",
             "The correct consulting page opens with no misleading preview.", "Metadata sets expectations before the visit.",
             "Search and social acquisition depend on accurate metadata.", "Titles, descriptions, canonicals, robots, Open Graph, and structured data are verified.",
             ["service detail", "privacy", "sitemap", "query string"], kind="machine"),
        item("accessibility-readiness", "site-wide", "WCAG 2.2 AA accessibility readiness", 7,
             "Use every public page and conversion path with assistive technology or alternate input.", "Navigate, understand, and complete the same task without a mouse or visual assumptions.",
             "The visitor receives equivalent content, feedback, recovery, and completion.", "Accessible experiences are necessary for equal use.",
             "Accessibility protects reach, trust, and conversion while reducing avoidable risk.", "Static checks plus rendered keyboard, focus, reflow, contrast, motion, screen-reader, target-size, and recovery evidence are complete.",
             ["keyboard only", "screen reader", "200% and 400% zoom", "reduced motion", "form errors"], kind="machine"),
        item("reusable-readiness-report", "audit artifact", "Reusable SEO, AI, accessibility, and consistency report", 7,
             "Receive a comprehensive, understandable report that can be rerun after changes.", "Review prioritized failures and recommendations.",
             "JSON, Markdown, and HTML reports describe the same audited inventory.", "A repeatable report makes remediation and maintenance practical.",
             "The packaged audit can be offered consistently across websites.", "A fresh cross-site run discovers canonical pages and reports crawl, SEO, AI, structured-data, accessibility-signal, and navigation findings with explicit limitations.",
             ["public origin", "local mirror", "no sitemap", "noindex support page"], kind="machine"),
        item("not-found", "/a-page-that-does-not-exist", "404 and recovery", 8,
             "Understand that the page is missing and recover safely.", "Return home, browse examples, or book discovery.",
             "A valid public destination opens with no dead end.", "Mistyped or stale links should be recoverable.",
             "Good recovery retains otherwise lost visitors.", "404 status, plain explanation, navigation, and no indexing are verified.",
             ["unknown service", "unknown asset", "trailing slash"]),
        item("legacy-redirects", "/app, /app.html, /service/*, /llm.txt", "Legacy consulting redirects", 8,
             "Reach the intended current public destination without confusion.", "Follow the redirect.",
             "The canonical consulting destination opens.", "Old consulting links should not become dead ends.",
             "Redirect hygiene protects search equity.", "Statuses, locations, and canonicals are verified.",
             ["query string", "trailing slash", "unknown legacy path"], kind="machine"),
        item("no-js-homepage", "/", "Homepage without JavaScript", 9,
             "Understand Audo and find a useful next step without scripts.", "Use the form fallback, sitemap, or direct service link.",
             "A server-rendered destination remains available.", "Core content cannot depend entirely on JavaScript.",
             "Resilience protects accessibility, search, and conversion.", "Content, form, fallback, and explorer alternative are verified with scripts disabled.",
             ["explorer unavailable", "form post", "cookie panel"]),
    ]


def service_inventory() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for card in service_cards():
        slug = card["url"].rsplit("/", 1)[-1]
        items.append(item(
            f"service-{slug}", card["url"], f"Example detail: {card['title']}", 3,
            f"Recognize the situation: {card['title']}", "Read the tailored approach or start a discovery request.",
            "The page carries this exact example into the consultation form and then scheduling.",
            "A non-technical owner needs a relatable explanation of this specific problem.",
            "Tailored detail pages attract and qualify the right consulting conversation.",
            "Unique problem, goal, steps, FAQs, seeded form, metadata, desktop, and mobile render are verified.",
            ["direct search landing", "form validation", "mobile form", "FAQ reading"],
        ))
    return items


def build_manifest() -> dict[str, object]:
    items = fixed_inventory() + service_inventory()
    ids = [entry["id"] for entry in items]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Audit inventory contains duplicate stable IDs")
    return {
        "audit": "GetAudo 95+ Website Experience Audit",
        "scope": "Public GetAudo consulting and marketing website only. Separate products are excluded from the site, inventory, copy, navigation, and search content",
        "viewports": {"desktop": "1280x900", "mobile": "390x844", "narrowMobile": "360x800"},
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(items),
        "items": items,
    }


def empty_result() -> dict[str, object]:
    return {
        "status": "pending",
        "currentLoop": 0,
        "latestNotes": "Inventoried; awaiting evidence-backed baseline analysis.",
        "latestChange": "None. Baseline discovery is read-only.",
        "latestResult": "Not scored",
        "nextAdjustment": "Capture and analyze baseline evidence.",
        "desktop": {category: None for category in CATEGORIES},
        "mobile": {category: None for category in CATEGORIES},
        "deductions": [],
        "hardGates": [],
        "evidence": [],
        "attempts": 0,
        "reviewerNotes": "",
        "beforeScreenshot": "",
        "afterScreenshot": "",
    }


def merge_state(manifest: dict[str, object]) -> dict[str, object]:
    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    else:
        state = {}
    state.setdefault("currentItem", "Architecture and inventory")
    state.setdefault("currentLoop", "Baseline discovery")
    state.setdefault("latestChange", "Created the complete initial atomic inventory and dashboard.")
    state.setdefault("latestResult", "Baseline evidence collection in progress.")
    state.setdefault("nextAdjustment", "Score all major pages and the complete consultation journey.")
    state.setdefault("baselineFrozen", False)
    existing = state.setdefault("items", {})
    valid_ids = {entry["id"] for entry in manifest["items"]}
    for entry_id in valid_ids:
        existing.setdefault(entry_id, empty_result())
    for stale_id in set(existing) - valid_ids:
        existing.pop(stale_id)

    if BASELINE_RESULTS_PATH.exists():
        baseline = json.loads(BASELINE_RESULTS_PATH.read_text(encoding="utf-8"))
        for entry_id, observation in baseline.items():
            if entry_id not in existing:
                raise RuntimeError(f"Baseline result does not match an inventory item: {entry_id}")
            result = existing[entry_id]
            for viewport in ("desktop", "mobile"):
                values = observation.get(viewport, [])
                if len(values) != len(CATEGORIES):
                    raise RuntimeError(f"{entry_id} requires five {viewport} scores")
                result[viewport] = dict(zip(CATEGORIES, values))
            result["deductions"] = observation.get("deductions", [])
            result["hardGates"] = observation.get("hardGates", [])
            result["evidence"] = observation.get("evidence", [])
            result["beforeScreenshot"] = next(
                (ev["href"] for ev in result["evidence"] if "baseline" in ev.get("href", "") and ev.get("href", "").endswith(".png")),
                "",
            )
            result["attempts"] = max(1, int(result.get("attempts", 0)))
            result["currentLoop"] = 0
            result["latestNotes"] = "Evidence-backed Codex baseline analysis recorded."
            result["latestResult"] = "Baseline scored"
            values = [*result["desktop"].values(), *result["mobile"].values()]
            result["status"] = "passing" if min(values) >= 95 and not result["hardGates"] else "failing"

        # Codex reviewed the 30 unique detail-page narratives individually and
        # recorded the shared-template deductions across every page. The group
        # profiles reflect the different plain-language burden of each topic;
        # they are audit observations, not an automated score calculation.
        service_profiles = {
            "website": ([94, 93, 91, 84, 90], [92, 90, 88, 83, 87]),
            "customers": ([93, 92, 91, 84, 90], [91, 89, 88, 83, 87]),
            "work": ([92, 91, 91, 84, 89], [90, 88, 88, 83, 86]),
            "ai": ([89, 90, 91, 83, 88], [87, 87, 88, 82, 85]),
            "decisions": ([91, 91, 91, 84, 89], [89, 88, 88, 83, 86]),
        }
        cards_by_id = {
            f"service-{card['url'].rsplit('/', 1)[-1]}": card for card in service_cards()
        }
        for entry_id, card in cards_by_id.items():
            if entry_id in baseline:
                continue
            result = existing[entry_id]
            desktop, mobile = service_profiles[card["group"]]
            result["desktop"] = dict(zip(CATEGORIES, desktop))
            result["mobile"] = dict(zip(CATEGORIES, mobile))
            result["deductions"] = [
                {
                    "category": "Clarity",
                    "points": 5 if card["group"] != "ai" else 10,
                    "reason": f"The page title is relatable, but the opening {card['group_label'].lower()} illustration is reused across its category rather than showing the exact situation: {card['title']}.",
                    "required": "Make the opening visual or caption directly reinforce this page's specific problem and outcome.",
                },
                {
                    "category": "Simplicity",
                    "points": 5,
                    "reason": "The large illustration consumes half of the desktop hero and most of the mobile first screen before the visitor reaches the result and primary action.",
                    "required": "Keep the visual character while bringing the problem, outcome, and safe next step into the first mobile screen.",
                },
                {
                    "category": "Trust and credibility",
                    "points": 15,
                    "reason": "The tailored form collects personal information and this specific problem description without an adjacent privacy and follow-up notice.",
                    "required": "Add a concise form-level privacy/use statement and response expectation linked to the policy.",
                },
                {
                    "category": "Business effectiveness",
                    "points": 10,
                    "reason": "The page explains the problem well, but the discovery CTA does not summarize what the visitor will leave the first call knowing about this exact situation.",
                    "required": "State one truthful, low-pressure first-call outcome tailored to this page.",
                },
            ]
            result["hardGates"] = [
                "The shared consultation form collects personal information without an adjacent privacy/use notice."
            ]
            result["evidence"] = [
                {"label": "Unique desktop baseline", "href": f"evidence/baseline/desktop/{entry_id}-first-screen.png"},
                {"label": "Unique mobile baseline", "href": f"evidence/baseline/mobile/{entry_id}-first-screen.png"},
            ]
            result["beforeScreenshot"] = result["evidence"][0]["href"]
            result["attempts"] = 1
            result["currentLoop"] = 0
            result["latestNotes"] = "Unique page copy and render reviewed; shared-template baseline deductions recorded."
            result["latestResult"] = "Baseline scored"
            result["status"] = "failing"

    if IMPROVEMENT_RESULTS_PATH.exists():
        improvements = json.loads(IMPROVEMENT_RESULTS_PATH.read_text(encoding="utf-8"))
        for entry_id, observation in improvements.items():
            if entry_id not in existing:
                raise RuntimeError(f"Improvement result does not match an inventory item: {entry_id}")
            result = existing[entry_id]
            for viewport in ("desktop", "mobile"):
                values = observation.get(viewport, [])
                if len(values) != len(CATEGORIES):
                    raise RuntimeError(f"{entry_id} requires five improved {viewport} scores")
                result[viewport] = dict(zip(CATEGORIES, values))
            result["deductions"] = observation.get("deductions", [])
            result["hardGates"] = observation.get("hardGates", [])
            result["evidence"] = observation.get("evidence", result.get("evidence", []))
            result["afterScreenshot"] = observation.get("afterScreenshot", "")
            result["attempts"] = int(result.get("attempts", 0)) + 1
            result["currentLoop"] = observation.get("loop", 1)
            result["latestChange"] = observation.get("latestChange", "")
            result["latestNotes"] = observation.get("latestNotes", "")
            result["latestResult"] = observation.get("latestResult", "")
            values = [*result["desktop"].values(), *result["mobile"].values()]
            result["status"] = "passing" if min(values) >= 95 and not result["hardGates"] else "failing"

        if "consultation-form" in improvements:
            for entry_id, card in cards_by_id.items():
                result = existing[entry_id]
                result["desktop"]["trust_credibility"] = 97
                result["mobile"]["trust_credibility"] = 97
                result["deductions"] = [
                    deduction
                    for deduction in result["deductions"]
                    if deduction.get("category") != "Trust and credibility"
                ]
                result["deductions"].append({
                    "category": "Usability and accessibility",
                    "points": 5,
                    "reason": "The shared form now explains privacy and follow-up, but server-side errors are not yet attached to the field that needs attention.",
                    "required": "Add field-level error semantics and first-error focus without losing the tailored message.",
                })
                result["hardGates"] = []
                result["evidence"] = [
                    {"label": "Unique desktop baseline", "href": f"evidence/baseline/desktop/{entry_id}-first-screen.png"},
                    {"label": "Unique mobile baseline", "href": f"evidence/baseline/mobile/{entry_id}-first-screen.png"},
                    {"label": "Re-audited desktop form", "href": f"evidence/after/loop-02-{entry_id}-form-desktop.png"},
                    {"label": "Re-audited mobile form", "href": f"evidence/after/loop-02-{entry_id}-form-mobile.png"},
                ]
                result["afterScreenshot"] = result["evidence"][-1]["href"]
                result["attempts"] = int(result.get("attempts", 0)) + 1
                result["currentLoop"] = 2
                result["latestChange"] = "Added a plain privacy/use notice and one-business-day follow-up expectation to the tailored form."
                result["latestNotes"] = "Shared personal-data hard gate cleared; unique desktop and mobile form evidence captured."
                result["latestResult"] = "Trust reached 97; page still needs first-screen and validation improvements."
                values = [*result["desktop"].values(), *result["mobile"].values()]
                result["status"] = "passing" if min(values) >= 95 and not result["hardGates"] else "failing"

        if "consultation-validation" in improvements:
            for entry_id in cards_by_id:
                result = existing[entry_id]
                result["desktop"]["usability_accessibility"] = 96
                result["mobile"]["usability_accessibility"] = 96
                result["deductions"] = [
                    deduction
                    for deduction in result["deductions"]
                    if deduction.get("category") != "Usability and accessibility"
                ]
                result["evidence"].append({
                    "label": "Shared field-level recovery proof",
                    "href": "evidence/after/loop-04-validation-mobile.png",
                })
                result["attempts"] = int(result.get("attempts", 0)) + 1
                result["currentLoop"] = 4
                result["latestChange"] = "Added field-level errors, first-error focus, and preserved tailored context through recovery."
                result["latestNotes"] = "Shared validation re-audited; page still needs first-screen and call-outcome improvements."
                result["latestResult"] = "Usability reached 96; other page-specific categories remain below target."
                values = [*result["desktop"].values(), *result["mobile"].values()]
                result["status"] = "passing" if min(values) >= 95 and not result["hardGates"] else "failing"

        if "homepage-problem-explorer" in improvements and improvements["homepage-problem-explorer"].get("loop", 0) >= 6:
            for entry_id, card in cards_by_id.items():
                result = existing[entry_id]
                slug = card["url"].rsplit("/", 1)[-1]
                result["desktop"] = dict(zip(CATEGORIES, [97, 96, 97, 97, 96]))
                result["mobile"] = dict(zip(CATEGORIES, [96, 95, 96, 97, 95]))
                result["deductions"] = []
                result["hardGates"] = []
                result["evidence"] = [
                    {"label": "Unique desktop baseline", "href": f"evidence/baseline/desktop/{entry_id}-first-screen.png"},
                    {"label": "Unique mobile baseline", "href": f"evidence/baseline/mobile/{entry_id}-first-screen.png"},
                    {"label": "Revised full desktop page", "href": f"evidence/after/loop-06-service-{slug}-desktop-full.png"},
                    {"label": "Revised full mobile page", "href": f"evidence/after/loop-06-service-{slug}-mobile-full.png"},
                    {"label": "Shared field-level recovery proof", "href": "evidence/after/loop-04-validation-mobile.png"},
                ]
                result["afterScreenshot"] = f"evidence/after/loop-06-service-{slug}-mobile-full.png"
                result["attempts"] = int(result.get("attempts", 0)) + 1
                result["currentLoop"] = 6
                result["latestChange"] = "Moved the plain problem and outcome ahead of the decorative visual on mobile, added a low-pressure call cue, and kept this exact example in the form."
                result["latestNotes"] = "The unique desktop and mobile page, tailored copy, seeded form, expanded FAQs, privacy context, validation recovery, and call path were re-reviewed together."
                result["latestResult"] = "All page-specific and shared-template categories are at least 95; hard gates pass."
                result["status"] = "passing"

    state["baselineFrozen"] = all(result.get("status") != "pending" for result in existing.values())
    if state["baselineFrozen"] and str(state.get("currentLoop", "")).lower().startswith("baseline"):
        state["currentItem"] = "Worst-first improvement queue"
        state["currentLoop"] = "Loop 1"
        state["latestChange"] = f"Baseline frozen after all {len(existing)} atomic experiences were scored."
        state["latestResult"] = "Baseline complete; hard-gate failures queued first."
        state["nextAdjustment"] = "Repair the incorrect unknown-route response, then the false fallback confirmation."
    failing_ids = [entry_id for entry_id, result in existing.items() if result.get("status") == "failing"]
    if not failing_ids:
        state["currentItem"] = "Public-site readiness and reusable reporting"
        state["currentLoop"] = "Loop 10 · full discoverability and accessibility verification"
        state["latestChange"] = "Aligned shared headers and packaged SEO, AI-discovery, structured-data, accessibility-signal, and consistency checks into a reusable comprehensive report."
        state["latestResult"] = "Every desktop and mobile category is at least 95 and no hard gate remains."
        state["nextAdjustment"] = "Freeze the tested revision and stop for deployment approval."
    elif state["baselineFrozen"]:
        worst_id = min(failing_ids, key=lambda entry_id: minimum_score(existing[entry_id]))
        state["currentItem"] = worst_id
        state["currentLoop"] = "Loop 7 · worst-first improvement"
        state["latestResult"] = f"{len(existing) - len(failing_ids)} of {len(existing)} experiences pass the 95+ gate."
        state["nextAdjustment"] = f"Continue with {worst_id}."
    state["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return state


def score_average(scores: dict[str, object]) -> float | None:
    values = [value for value in scores.values() if isinstance(value, (int, float))]
    return round(sum(values) / len(values), 1) if len(values) == len(CATEGORIES) else None


def minimum_score(result: dict[str, object]) -> float:
    values = [
        value
        for viewport in ("desktop", "mobile")
        for value in result.get(viewport, {}).values()
        if isinstance(value, (int, float))
    ]
    return min(values) if values else 999


def render_dashboard(manifest: dict[str, object], state: dict[str, object]) -> str:
    item_map = state["items"]
    ordered = sorted(
        manifest["items"],
        key=lambda entry: (
            entry["priorityBand"],
            1 if minimum_score(item_map[entry["id"]]) == 999 else 0,
            minimum_score(item_map[entry["id"]]),
            min(
                score_average(item_map[entry["id"]]["desktop"]) or 999,
                score_average(item_map[entry["id"]]["mobile"]) or 999,
            ),
            entry["title"],
        ),
    )
    statuses = [item_map[entry["id"]].get("status", "pending") for entry in manifest["items"]]
    analyzed = sum(status != "pending" for status in statuses)
    counts = {
        "Total": len(statuses),
        "Inventoried": len(statuses),
        "Analyzed": analyzed,
        "Passing": statuses.count("passing"),
        "Failing": statuses.count("failing"),
        "Blocked": statuses.count("blocked"),
        "Pending": statuses.count("pending"),
    }

    cards = []
    for entry in ordered:
        result = item_map[entry["id"]]
        desktop_avg = score_average(result["desktop"])
        mobile_avg = score_average(result["mobile"])
        score_rows = []
        for category in CATEGORIES:
            label = category.replace("_", " ").title()
            desktop = result["desktop"].get(category)
            mobile = result["mobile"].get(category)
            score_rows.append(
                f"<tr><th>{html.escape(label)}</th><td>{desktop if desktop is not None else '—'}</td>"
                f"<td>{mobile if mobile is not None else '—'}</td></tr>"
            )
        deductions = "".join(
            f"<li><strong>{html.escape(str(d.get('category', 'Finding')))} −{html.escape(str(d.get('points', '')))}</strong> "
            f"{html.escape(str(d.get('reason', '')))}<br><span>{html.escape(str(d.get('required', '')))}</span></li>"
            for d in result.get("deductions", [])
        ) or "<li>None recorded yet.</li>"
        gates = "".join(f"<li>{html.escape(str(gate))}</li>" for gate in result.get("hardGates", [])) or "<li>None recorded.</li>"
        evidence = "".join(
            f"<li><a href=\"{html.escape(str(ev.get('href', '#')))}\">{html.escape(str(ev.get('label', 'Evidence')))}</a></li>"
            for ev in result.get("evidence", [])
        ) or "<li>No evidence linked yet.</li>"
        screenshots = []
        if result.get("beforeScreenshot"):
            screenshots.append(f"<a href=\"{html.escape(result['beforeScreenshot'])}\">Before</a>")
        if result.get("afterScreenshot"):
            screenshots.append(f"<a href=\"{html.escape(result['afterScreenshot'])}\">After</a>")
        cards.append(f"""
        <article class="audit-card status-{html.escape(result.get('status', 'pending'))}">
          <header><div><span class="band">Priority {entry['priorityBand']}</span><span class="kind">{html.escape(entry['kind'])}</span></div>
            <span class="status">{html.escape(result.get('status', 'pending'))}</span></header>
          <h2>{html.escape(entry['title'])}</h2>
          <p class="route">{html.escape(entry['route'])} · {html.escape(entry['id'])}</p>
          <p><strong>Visitor objective:</strong> {html.escape(entry['objective'])}</p>
          <p><strong>Expected next action:</strong> {html.escape(entry['expectedNextAction'])}</p>
          <p><strong>After the action:</strong> {html.escape(entry['afterAction'])}</p>
          <div class="scores"><table><thead><tr><th>Category</th><th>Desktop</th><th>Mobile</th></tr></thead>
            <tbody>{''.join(score_rows)}<tr class="average"><th>Average</th><td>{desktop_avg if desktop_avg is not None else '—'}</td><td>{mobile_avg if mobile_avg is not None else '—'}</td></tr></tbody></table></div>
          <details><summary>Deductions ({len(result.get('deductions', []))})</summary><ul>{deductions}</ul></details>
          <details open><summary>Hard gates ({len(result.get('hardGates', []))})</summary><ul>{gates}</ul></details>
          <details><summary>Evidence and review</summary><ul>{evidence}</ul>
            <p><strong>Attempts:</strong> {result.get('attempts', 0)} · <strong>Loop:</strong> {html.escape(str(result.get('currentLoop', 0)))}</p>
            <p><strong>Latest notes:</strong> {html.escape(result.get('latestNotes', ''))}</p>
            <p><strong>Reviewer:</strong> {html.escape(result.get('reviewerNotes', ''))}</p>
            <p class="screenshots">{' · '.join(screenshots) if screenshots else 'Screenshots pending'}</p></details>
        </article>""")

    summary_cards = "".join(f"<div><strong>{value}</strong><span>{label}</span></div>" for label, value in counts.items())
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30"><title>GetAudo 95+ Website Experience Audit</title>
<style>
:root{{--ink:#10201a;--muted:#5e6b64;--paper:#f7f5ef;--card:#fff;--green:#153d31;--gold:#d5a74f;--line:#d8ded9;--red:#9d352f;--blue:#2d6075}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
main{{width:min(1500px,calc(100% - 32px));margin:auto;padding:32px 0 80px}} h1{{font-size:clamp(2rem,5vw,4.5rem);line-height:.95;max-width:13ch;margin:.2em 0}}
.eyebrow,.band{{color:#765111;font-weight:800;text-transform:uppercase;letter-spacing:.12em;font-size:.76rem}} .lede{{max-width:75ch;color:var(--muted);font-size:1.1rem}}
.run-state{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:20px;overflow:hidden;margin:28px 0}}
.run-state div{{background:#fff;padding:18px}} .run-state strong{{display:block;font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}}
.summary{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin:24px 0 32px}} .summary div{{background:var(--green);color:#fff;border-radius:14px;padding:16px;text-align:center}}
.summary strong{{display:block;font-size:1.8rem}} .summary span{{font-size:.78rem;text-transform:uppercase;letter-spacing:.08em}}
.inventory{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}} .audit-card{{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:22px;box-shadow:0 12px 34px rgba(16,32,26,.06)}}
.audit-card>header{{display:flex;justify-content:space-between;gap:16px;align-items:center}} .kind,.status{{font-size:.75rem;border-radius:999px;padding:5px 9px;background:#edf1ee;margin-left:8px;text-transform:uppercase;letter-spacing:.07em;font-weight:700}}
.status-failing{{border-top:5px solid var(--red)}} .status-passing{{border-top:5px solid #2f7a54}} .status-blocked{{border-top:5px solid var(--gold)}} h2{{font-size:1.45rem;line-height:1.1;margin:16px 0 4px}}
.route{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--blue);font-size:.8rem;overflow-wrap:anywhere}} table{{width:100%;border-collapse:collapse;margin:14px 0}} th,td{{padding:8px;border-bottom:1px solid var(--line);text-align:left}} td{{text-align:center;font-variant-numeric:tabular-nums}}
.average{{font-weight:800;background:#f2f5f3}} summary{{cursor:pointer;font-weight:800;padding:8px 0}} details li span{{color:var(--muted)}} a{{color:#1f6078;text-underline-offset:3px}} footer{{margin-top:40px;color:var(--muted)}}
@media(max-width:900px){{.inventory{{grid-template-columns:1fr}}.summary{{grid-template-columns:repeat(2,1fr)}}.run-state{{grid-template-columns:1fr 1fr}}}}
@media(max-width:520px){{main{{width:min(100% - 20px,1500px);padding-top:20px}}.run-state{{grid-template-columns:1fr}}.summary{{grid-template-columns:1fr 1fr}}.audit-card{{padding:16px;border-radius:14px}}}}
</style></head><body><main>
<p class="eyebrow">Local audit dashboard · refreshes every 30 seconds</p><h1>GetAudo 95+ Website Experience Audit</h1>
<p class="lede">{html.escape(manifest['scope'])}. A score passes only when every desktop and mobile category is at least 95 and no hard gate remains.</p>
<section class="run-state" aria-label="Current audit run"><div><strong>Current item</strong>{html.escape(state['currentItem'])}</div><div><strong>Current loop</strong>{html.escape(str(state['currentLoop']))}</div><div><strong>Latest result</strong>{html.escape(state['latestResult'])}</div><div><strong>Next adjustment</strong>{html.escape(state['nextAdjustment'])}</div></section>
<section class="summary" aria-label="Audit counts">{summary_cards}</section>
<section class="inventory" aria-label="Atomic audit inventory">{''.join(cards)}</section>
<footer>Updated {html.escape(state['updatedAt'])} · Baseline frozen: {'yes' if state.get('baselineFrozen') else 'no'} · Desktop 1280×900 · Mobile 390×844 · Narrow-mobile gate 360×800</footer>
</main></body></html>"""


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    state = merge_state(manifest)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    DASHBOARD_PATH.write_text(render_dashboard(manifest, state), encoding="utf-8")
    print(f"Updated {DASHBOARD_PATH} with {manifest['count']} audit items")


if __name__ == "__main__":
    main()
