from __future__ import annotations

import re
from dataclasses import asdict, dataclass


PUBLIC_BASE_URL = "https://getaudo.com"


@dataclass(frozen=True)
class Service:
    slug: str
    title: str
    category: str
    summary: str
    pain: str
    solution: str
    result: str

    @property
    def url(self) -> str:
        return f"/services/{self.slug}"

    @property
    def canonical_url(self) -> str:
        return f"{PUBLIC_BASE_URL}{self.url}"

    @property
    def meta_title(self) -> str:
        return f"{self.title} | Audo"

    @property
    def meta_description(self) -> str:
        description = f"{self.summary} Audo helps find the issue, fix the right thing, and make the next step clear."
        if len(description) <= 158:
            return description
        shorter = f"{self.summary} Request Free Discovery with Audo."
        if len(shorter) <= 158:
            return shorter
        return self.summary[:155].rstrip(" ,.;") + "..."


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug


SERVICE_SEEDS = [
    (
        "Contact form submissions are not arriving",
        "Website and app care",
        "Visitors try to reach you, but form submissions are not reliably arriving.",
        "A broken form quietly costs leads because the site looks available while the messages disappear, bounce, or land in the wrong inbox.",
        "I trace the form path, validation, notifications, spam settings, CRM handoff, and confirmation experience so the real failure is clear.",
        "Leads submit with confidence, messages land where they should, and you know how the form is being monitored.",
    ),
    (
        "The website feels slow",
        "Website and app care",
        "A slow website is making visitors wait, bounce, or lose confidence.",
        "Speed problems usually come from images, scripts, hosting, caching, layout shifts, or too many small decisions that accumulated over time.",
        "I review the real pages people use, identify the biggest speed drains, and prioritize fixes that improve the experience without rebuilding everything.",
        "Visitors get a faster first impression, mobile pages feel smoother, and you have a clear path for continued performance care.",
    ),
    (
        "WordPress warnings are piling up",
        "Website and app care",
        "WordPress updates, plugin notices, and warnings are piling up without a clear owner.",
        "Plugin clutter creates risk because it is hard to know what can be updated, removed, replaced, or left alone without breaking the site.",
        "I review the theme, plugins, hosting, backups, update path, and critical features before changing anything that affects production.",
        "The site has fewer unknowns, safer updates, and a practical maintenance rhythm instead of a dashboard full of anxiety.",
    ),
    (
        "Website leads are going missing",
        "Website and app care",
        "People submit forms, but the follow-up path is unclear or unreliable.",
        "Lead loss can happen across the form, email deliverability, CRM rules, notifications, spam filters, and manual follow-up habits.",
        "I map the full lead path from submit button to human response and fix the weak links that cause delay or confusion.",
        "New inquiries are easier to see, assign, respond to, and trust.",
    ),
    (
        "The mobile website is confusing",
        "Website and app care",
        "Your site technically works on phones, but visitors struggle to understand or act.",
        "Mobile friction often hides in navigation, long text, tiny tap targets, slow sections, confusing forms, and calls to action that get buried.",
        "I review the site like a real mobile visitor and simplify the path to the action that matters most.",
        "The mobile experience becomes easier to scan, easier to use, and more likely to create a real inquiry.",
    ),
    (
        "The homepage no longer matches the business",
        "Website and app care",
        "Your homepage no longer reflects what you do, who you help, or why people should trust you.",
        "Outdated homepages make good businesses look less active, less clear, or harder to choose than they really are.",
        "I clarify the message, structure the page around customer decisions, and make the first screen stronger without unnecessary redesign theater.",
        "Visitors understand the offer faster and have a clearer reason to take the next step.",
    ),
    (
        "Clarify service pages for real customers",
        "Website and app care",
        "Your service pages describe the work, but not in the way customers make decisions.",
        "Technical or internal wording can make services feel vague, interchangeable, or harder to buy.",
        "I reshape the page around the customer's pain, desired outcome, proof points, and next action.",
        "Each service page becomes easier to understand, easier to trust, and easier to act on.",
    ),
    (
        "Fix booking calendar friction",
        "Website and app care",
        "People are interested, but scheduling creates confusion, dead ends, or unnecessary back-and-forth.",
        "Booking friction can come from too many options, poor mobile UX, missing confirmations, timezone confusion, or disconnected follow-up.",
        "I review the booking path, simplify the options, connect confirmations, and make sure the next step is obvious.",
        "Prospects can book faster, show up better prepared, and receive a cleaner first impression.",
    ),
    (
        "Fix broken checkout or payment links",
        "Website and app care",
        "Payment links, checkout steps, or purchase paths are failing at the moment trust matters most.",
        "Checkout problems can hide in expired links, redirects, embeds, scripts, payment settings, mobile layouts, or unclear confirmation steps.",
        "I test the purchase path, isolate the failure, and make the buying process clearer and more reliable.",
        "Customers can complete payment with less friction and you can spot issues before they linger.",
    ),
    (
        "Fix business emails going to spam",
        "Website and app care",
        "Important business emails, form notifications, or client messages are landing in spam.",
        "Email trust problems create missed leads and awkward follow-up because people assume messages were never sent or never answered.",
        "I review the sending address, message path, SPF, DKIM, DMARC, form notifications, mailbox behavior, and message content to find the likely trust issues.",
        "Your emails have a clearer path to the inbox and you know what to monitor if deliverability slips again.",
    ),
    (
        "Set up simple website measurement",
        "Website and app care",
        "You want to know what is happening on the site without drowning in reports.",
        "Many small businesses either have no measurement or have disconnected tools that do not answer practical questions.",
        "I connect the basics, define the few actions worth watching, and make the data easier to interpret.",
        "You can see whether people are finding, using, and contacting you through the site.",
    ),
    (
        "Improve local service page visibility",
        "Website and app care",
        "Local customers should be able to understand where you work and what you offer.",
        "Local pages often underperform because they are thin, duplicated, unclear, or missing the details people and search engines expect.",
        "I review the page structure, service language, location signals, internal links, metadata, and helpful content gaps.",
        "Your local pages become clearer, more useful, and better aligned with real search intent.",
    ),
    (
        "One offer needs a focused page",
        "Website and app care",
        "You have a specific offer that needs a focused page instead of sending everyone to the homepage.",
        "A general site page can dilute the message when a campaign, referral, or sales conversation needs one clear path.",
        "I shape the page around the offer, audience, pain, proof, objections, and conversion action.",
        "Prospects land on a page that matches their intent and makes the next step easier.",
    ),
    (
        "A website move feels risky",
        "Website and app care",
        "You need to move platforms, hosts, pages, or domains without creating a mess.",
        "Migrations create risk when redirects, content, forms, tracking, email, DNS, and launch timing are treated separately.",
        "I plan the migration path, map dependencies, preserve the important pages, and verify the launch details.",
        "The move is calmer, cleaner, and less likely to create broken links or missed leads.",
    ),
    (
        "Key pages have accessibility barriers",
        "Website and app care",
        "Important pages or forms may be difficult for people using keyboards, screen readers, or assistive tools.",
        "Accessibility problems often hide in contrast, labels, headings, focus states, alt text, navigation, and form errors.",
        "I review the high-value pages, identify practical barriers, and help prioritize fixes that make the experience more usable.",
        "More visitors can use the site with confidence, and your team has a clearer accessibility improvement path.",
    ),
    (
        "Repair a stale blog or resources section",
        "Website and app care",
        "Your site has old articles, outdated resources, or content that no longer supports the business.",
        "Stale content can confuse visitors, weaken trust, and make search engines less sure what matters now.",
        "I audit the content, decide what to keep, update, redirect, consolidate, or remove, and tie useful pages back to service goals.",
        "The resources section becomes cleaner, more current, and more helpful to real buyers.",
    ),
    (
        "Visitors are seeing security warnings",
        "Website and app care",
        "Visitors are seeing browser warnings, mixed content, or security messages.",
        "Security warnings damage trust quickly and can come from certificates, redirects, old links, embedded assets, or hosting settings.",
        "I identify the source, clean up the configuration, and verify the site loads securely across important paths.",
        "Visitors no longer hit avoidable trust barriers before they can contact you.",
    ),
    (
        "Visitors cannot find the right next step",
        "Website and app care",
        "Visitors can get to the site, but they cannot quickly find the right next step.",
        "Navigation grows messy when pages, offers, audiences, and internal language accumulate without a clear decision path.",
        "I simplify the menu, page hierarchy, labels, and calls to action around what visitors are actually trying to do.",
        "People understand where to go faster, and important pages stop being buried.",
    ),
    (
        "Website inquiries are stuck in inboxes or spreadsheets",
        "Website and app care",
        "Website inquiries need to land somewhere useful instead of sitting in an inbox.",
        "Manual copying from forms to CRMs or spreadsheets wastes time and creates missed follow-up risk.",
        "I connect the form output to the right destination, add useful fields, and keep the handoff simple enough to trust.",
        "New inquiries are easier to track, assign, and follow up on without extra copy-paste work.",
    ),
    (
        "Customers need a clearer request and file handoff",
        "Website and app care",
        "Customers or clients need a cleaner place to submit requests, upload files, and see what happens next.",
        "Email-only portals create repeated clarification work because files, updates, approvals, and status details get scattered across threads.",
        "I define the portal workflow, required fields, file handling, notifications, permissions, and support path before building the smallest useful version.",
        "Customers get a clearer experience and your team receives better-organized requests with less back-and-forth.",
    ),
    (
        "Clean up a web app backlog",
        "Website and app care",
        "Your app has a long list of fixes and ideas, but it is hard to know what matters next.",
        "Backlogs become discouraging when bugs, enhancements, support requests, and strategic ideas all compete in one pile.",
        "I sort the list by impact, effort, risk, user pain, and business value, then identify the best first moves.",
        "The backlog becomes usable again and the team can make progress without guessing.",
    ),
    (
        "Document how your website works",
        "Website and app care",
        "Only one person knows how the site, tools, logins, forms, and updates actually work.",
        "Undocumented systems make every change slower and every handoff riskier.",
        "I inventory the setup, clarify ownership, write practical notes, and identify the areas that need cleanup or support.",
        "You have a clearer operating guide and fewer single points of failure.",
    ),
    (
        "Prepare a site before a campaign launch",
        "Website and app care",
        "A campaign is coming, but the website path has not been checked from visitor to follow-up.",
        "Campaign traffic exposes weak pages, broken forms, slow load times, unclear offers, and missing tracking fast.",
        "I review the campaign path, landing page, form, confirmation, tracking, and follow-up before traffic arrives.",
        "Your campaign has a cleaner place to send people and fewer avoidable leaks.",
    ),
    (
        "Turn scattered tools into one workflow dashboard",
        "Website and app care",
        "Important work is spread across tabs, spreadsheets, emails, and apps.",
        "Scattered tools make status hard to see and force people to ask for updates that should be visible.",
        "I identify the few signals that matter and create a simple dashboard or hub that brings the work into view.",
        "You spend less time hunting for status and more time acting on what matters.",
    ),
    (
        "Website updates keep getting postponed",
        "Website and app care",
        "Small website changes keep getting postponed because no one owns them.",
        "Minor edits, updates, content changes, and cleanup work can pile up until the site no longer reflects the business.",
        "I create a simple monthly rhythm for updates, review, fixes, and practical improvements.",
        "Your site keeps moving forward without needing a big project every time something changes.",
    ),
    (
        "Leads need follow-up you can trust",
        "Automation",
        "New leads need timely, consistent follow-up without relying on memory.",
        "Follow-up falls apart when every inquiry requires a manual reminder, copied email, or repeated status check.",
        "I map the lead stages, define the right messages, and connect the tools that trigger reminders or follow-up steps.",
        "Leads receive a faster response and fewer opportunities fall through the cracks.",
    ),
    (
        "Intake submissions become loose work",
        "Automation",
        "Form submissions need to become trackable work automatically.",
        "Intake loses value when every submission has to be read, copied, renamed, assigned, and remembered manually.",
        "I route form details into tasks, spreadsheets, project boards, or notifications with the right context included.",
        "New requests arrive as organized work instead of another loose email.",
    ),
    (
        "Send reminders before missed deadlines",
        "Automation",
        "Important deadlines rely on someone remembering to check a spreadsheet or inbox.",
        "Manual deadline tracking creates stress because problems are visible only after the date has already passed.",
        "I create reminders based on due dates, status, owner, or missing information so the right person sees the right next step.",
        "Deadlines become easier to manage and less dependent on last-minute chasing.",
    ),
    (
        "Important numbers take too long to see",
        "Automation",
        "You need a quick view of important numbers without building reports by hand.",
        "Manual reporting wastes time and often arrives too late to guide decisions.",
        "I identify the few metrics that matter, connect the available data, and create a dashboard people can actually use.",
        "You get a clearer operating view with less recurring spreadsheet work.",
    ),
    (
        "Proposals take too long to prepare",
        "Automation",
        "Proposals take too long because the same information is rewritten every time.",
        "Proposal work slows down when pricing, scope, client details, terms, and repeated language live in separate places.",
        "I design a repeatable input flow and generate clean proposal drafts that still leave room for human review.",
        "You produce proposals faster while keeping quality and context in your control.",
    ),
    (
        "Organize files after form submissions",
        "Automation",
        "Submitted files need to be named, stored, and connected to the right client or project.",
        "File chaos creates rework because attachments land in inboxes with inconsistent names and unclear ownership.",
        "I create a workflow that saves files into the right folders, applies useful naming, and notifies the right person.",
        "Files become easier to find and less likely to disappear in email threads.",
    ),
    (
        "Route new leads to the right person",
        "Automation",
        "New inquiries need to go to the right owner based on service, location, urgency, or account.",
        "Bad routing delays response times and creates awkward internal forwarding.",
        "I define routing rules, connect the source form or inbox, and make sure the handoff includes useful context.",
        "Leads reach the right person faster with less manual sorting.",
    ),
    (
        "Automate customer review requests",
        "Automation",
        "Happy customers should be asked for reviews at the right moment.",
        "Review requests often get skipped because they depend on someone remembering after the work is done.",
        "I create a simple trigger, message, and follow-up path that asks at a natural point in the customer journey.",
        "You earn more consistent reviews without making the process feel forced.",
    ),
    (
        "Create invoice or payment reminders",
        "Automation",
        "Payment follow-up needs to be consistent without feeling like constant manual chasing.",
        "Manual reminders are easy to postpone and can make cash flow harder to manage.",
        "I help define the reminder timing, message, and data source so payment follow-up is more predictable.",
        "You get a cleaner reminder process and fewer invoices sitting unnoticed.",
    ),
    (
        "Appointment confirmations are confusing",
        "Automation",
        "Booked calls or appointments need clearer confirmations, reminders, and next steps.",
        "Scheduling tools can create confusion when confirmations, prep notes, cancellations, and reminders are disconnected.",
        "I review the appointment flow and connect the messages that help people show up ready.",
        "Meetings are easier to manage and require less manual coordination.",
    ),
    (
        "CRM data is hard to trust",
        "Automation",
        "Your CRM has useful information, but duplicates and messy fields make it hard to trust.",
        "A messy CRM creates friction because people stop believing the data and return to spreadsheets or memory.",
        "I review fields, duplicates, required data, lead stages, and cleanup rules before recommending a practical structure.",
        "The CRM becomes easier to use, easier to report from, and less frustrating for the people who touch it.",
    ),
    (
        "New customer onboarding feels inconsistent",
        "Automation",
        "New customers need a repeatable path from signed agreement to first useful result.",
        "Onboarding gets messy when tasks, files, emails, introductions, and expectations are handled differently every time.",
        "I map the onboarding steps and create forms, checklists, notifications, or automations that support the process.",
        "Customers experience a smoother start and your team has fewer details to remember.",
    ),
    (
        "Automate employee onboarding checklists",
        "Automation",
        "New hires or contractors need the right access, documents, tasks, and context.",
        "Manual onboarding creates missed steps and inconsistent first impressions.",
        "I turn the repeatable pieces into a simple checklist or automated flow with owners and reminders.",
        "New people get what they need faster and your team can track what is still open.",
    ),
    (
        "Send status updates without manual chasing",
        "Automation",
        "Clients or teammates keep asking for updates that could be sent automatically.",
        "Status chasing drains attention because the same questions come back whenever visibility is low.",
        "I identify what status should be shared, when it should be triggered, and how to keep it accurate.",
        "People get clearer updates and you spend less time writing the same message.",
    ),
    (
        "A spreadsheet is carrying too much responsibility",
        "Automation",
        "A spreadsheet is doing important work but becoming too fragile for everyday use.",
        "Spreadsheets break down when too many people edit them, formulas are hidden, or the workflow needs structure.",
        "I review what the spreadsheet really does and turn the useful parts into a cleaner form, dashboard, or lightweight app.",
        "The process becomes easier to use, harder to break, and simpler to support.",
    ),
    (
        "Create alerts for high priority requests",
        "Automation",
        "Urgent items need to stand out before they become emergencies.",
        "Important requests can get buried when every notification looks the same.",
        "I define urgency signals and create alerts that reach the right person through the right channel.",
        "High priority work becomes visible sooner without overwhelming everyone with noise.",
    ),
    (
        "Sync data between a website and spreadsheet",
        "Automation",
        "Your website collects data that should be available in a spreadsheet or working file.",
        "Manual exports and copy-paste steps make data stale and create room for mistakes.",
        "I connect the form, database, spreadsheet, or API path so the information moves in a predictable way.",
        "The spreadsheet stays more current and the website data becomes easier to act on.",
    ),
    (
        "Automate recurring document generation",
        "Automation",
        "Reports, letters, packets, or summaries are built from the same ingredients again and again.",
        "Document work is slow when people copy from spreadsheets, emails, templates, and notes by hand.",
        "I create a structured input process and generate consistent document drafts for review.",
        "Recurring documents take less time and follow a more reliable format.",
    ),
    (
        "Create a lightweight operations dashboard",
        "Automation",
        "You need one place to see open work, blockers, owners, and next steps.",
        "Operations feel heavier when status is spread across meetings, messages, spreadsheets, and memory.",
        "I define the simplest useful view and connect or collect the data needed to keep it current.",
        "You gain a practical command center without buying a huge system.",
    ),
    (
        "Turn repeated emails into templates and prompts",
        "Automation",
        "Your team writes the same explanations, replies, and follow-ups over and over.",
        "Repeated writing drains time and creates inconsistent quality across customers or projects.",
        "I identify common message types and create templates or AI-assisted prompts that still sound like you.",
        "Routine communication gets faster while remaining personal and useful.",
    ),
    (
        "Copy-paste is slowing the work down",
        "Automation",
        "Work is slowed down by moving the same information from one system to another.",
        "Copy-paste work looks small until it becomes a daily tax on attention and accuracy.",
        "I map the repeated handoff, identify the safest connection point, and automate the parts that should not require judgment.",
        "The work moves with fewer manual steps and fewer avoidable mistakes.",
    ),
    (
        "Build a private internal request form",
        "Automation",
        "Your team needs a cleaner way to ask for help, changes, approvals, or resources.",
        "Ad hoc requests in chat or email are easy to lose and hard to prioritize.",
        "I create a simple internal form with the right fields, routing, notifications, and follow-up path.",
        "Requests arrive with better context and can be tracked without another meeting.",
    ),
    (
        "Keep follow-up from falling through the cracks",
        "Automation",
        "Important follow-up depends on memory, sticky notes, or checking too many places.",
        "When follow-up is informal, good opportunities and important commitments disappear in the noise.",
        "I create a simple system of triggers, reminders, owners, and review points around the follow-up that matters most.",
        "Follow-up becomes visible, repeatable, and easier to trust.",
    ),
    (
        "The spreadsheet process is getting fragile",
        "Automation",
        "A spreadsheet is carrying too much responsibility and is starting to slow everyone down.",
        "Messy spreadsheets create hidden rules, version confusion, broken formulas, and unclear ownership.",
        "I separate what should remain a spreadsheet from what needs a form, dashboard, automation, or lightweight tool.",
        "The process becomes simpler, more reliable, and easier for other people to use.",
    ),
    (
        "AI tool choices feel noisy",
        "AI coaching and support",
        "You want to use AI, but the tool choices are noisy and hard to compare.",
        "AI adoption gets risky when tools are chosen because they are popular instead of because they solve a real workflow problem.",
        "I help define the jobs AI should do, compare tools against those jobs, and avoid unnecessary complexity.",
        "You get a practical shortlist and a clearer reason for what to try first.",
    ),
    (
        "The team needs safer rules for AI and client data",
        "AI coaching and support",
        "Your team needs AI guidance that protects customer, employee, and business information.",
        "Without clear rules, people either avoid AI entirely or paste sensitive information into tools without thinking through risk.",
        "I help define plain-English guardrails, review points, approved use cases, and safer habits for everyday work.",
        "Your team can use AI with more confidence and less guesswork.",
    ),
    (
        "AI prompts are inconsistent across daily work",
        "AI coaching and support",
        "People are trying AI, but every result depends on inventing the prompt from scratch.",
        "AI feels inconsistent when good prompts live in one person's notes or get rewritten every time.",
        "I create reusable prompts around your actual tasks, voice, inputs, and quality standards.",
        "The team gets faster, more consistent AI outputs without needing everyone to become a prompt expert.",
    ),
    (
        "The team is unsure how to use AI in real work",
        "AI coaching and support",
        "Your team is curious about AI but unsure how it applies to real work.",
        "Generic AI training rarely sticks because it does not match the team's tools, roles, risks, or daily decisions.",
        "I teach practical use cases, safe habits, review steps, and examples tied to the work your team already does.",
        "People leave with useful ways to start instead of vague excitement or fear.",
    ),
    (
        "Use AI for proposal first drafts",
        "AI coaching and support",
        "Proposal writing takes too long, but you still need accuracy and judgment.",
        "AI proposal drafts can sound generic or risky when they are not grounded in your real scope, customer context, and standards.",
        "I design a proposal workflow with structured inputs, reusable prompts, and human review built in.",
        "You create better first drafts faster without outsourcing the final judgment to AI.",
    ),
    (
        "Use AI to summarize meetings and calls",
        "AI coaching and support",
        "Meeting notes, follow-ups, and decisions are not getting captured consistently.",
        "AI summaries can help, but only if the workflow respects privacy, creates useful outputs, and lands in the right place.",
        "I help choose the capture method, output format, review step, and storage location for your meeting notes.",
        "Meetings produce clearer decisions and follow-up without adding more admin work.",
    ),
    (
        "Use AI to research before sales calls",
        "AI coaching and support",
        "You want better prep before calls without spending too much time researching manually.",
        "AI research can be shallow or inaccurate unless the sources, prompts, and review habits are designed carefully.",
        "I create a repeatable prep workflow that gathers useful context and flags what still needs human verification.",
        "You show up better prepared with less last-minute searching.",
    ),
    (
        "Support replies need to be faster without getting sloppy",
        "AI coaching and support",
        "Support responses need to be faster without becoming careless or robotic.",
        "AI can help draft replies, but bad guardrails can create tone problems, wrong promises, or privacy mistakes.",
        "I build prompts, review rules, example replies, and escalation guidance around your real customer situations.",
        "Customers get clearer responses and your team spends less time starting from a blank screen.",
    ),
    (
        "Use AI to repurpose content",
        "AI coaching and support",
        "Good ideas are stuck in long videos, calls, articles, notes, or presentations.",
        "Content repurposing is slow when every format has to be rewritten manually.",
        "I create an AI-assisted workflow for turning source material into posts, outlines, emails, summaries, or page drafts.",
        "You get more value from content you already created while keeping final review in your hands.",
    ),
    (
        "Use AI to review long documents",
        "AI coaching and support",
        "Long documents slow down decisions because people do not know where to focus.",
        "AI can summarize documents, but it needs careful prompting so it highlights risks, obligations, gaps, and open questions.",
        "I build a review workflow that asks better questions and keeps important human review points visible.",
        "You can understand long materials faster without pretending AI replaces judgment.",
    ),
    (
        "Use AI with spreadsheets and reports",
        "AI coaching and support",
        "You have data in spreadsheets, but turning it into useful answers takes too much effort.",
        "AI can help explain, clean, or analyze data, but it needs the right structure and verification habits.",
        "I help prepare the spreadsheet, define the questions, create prompts, and check the outputs for practical use.",
        "Reports become easier to understand and use in decisions.",
    ),
    (
        "Procedures are hard for the team to find",
        "AI coaching and support",
        "Your team has procedures, but people still ask the same how-to questions.",
        "AI assistants are only useful when the source material is clear, current, and bounded by what the assistant should know.",
        "I organize the procedures, define the assistant's role, and test it against real questions before anyone relies on it.",
        "People can find answers faster while the business keeps control of the source of truth.",
    ),
    (
        "Add human review to AI workflows",
        "AI coaching and support",
        "AI saves time, but you need a clear checkpoint before anything reaches customers or decisions.",
        "Without review points, AI can quietly introduce errors, tone issues, privacy mistakes, or unsupported claims.",
        "I identify where human judgment belongs and design the workflow so review is easy instead of optional.",
        "You get AI speed with fewer quality and trust risks.",
    ),
    (
        "Turn AI experiments into real habits",
        "AI coaching and support",
        "People tried AI a few times, but it has not become a useful part of work.",
        "AI adoption fades when experiments are not tied to specific tasks, time savings, or repeatable routines.",
        "I help choose a few high-value use cases, build the prompts, document the workflow, and support the habit while it sticks.",
        "AI becomes a practical tool instead of another abandoned experiment.",
    ),
    (
        "Use AI to improve job descriptions and hiring",
        "AI coaching and support",
        "Hiring materials need to be clearer, more consistent, and easier to adapt.",
        "AI can help write hiring content, but it needs your actual role expectations, tone, and selection priorities.",
        "I create prompts and review steps for job descriptions, screening questions, outreach, and interview prep.",
        "Hiring content becomes faster to produce and easier to align with the role you actually need.",
    ),
    (
        "Use AI to plan marketing content",
        "AI coaching and support",
        "Marketing ideas are scattered and content planning feels harder than it should.",
        "AI content planning can become generic unless it is grounded in real customers, offers, objections, and proof.",
        "I help define topics, angles, prompts, review rules, and a simple publishing workflow.",
        "You get a clearer content plan and faster drafts without losing your actual voice.",
    ),
    (
        "Use AI to answer internal knowledge questions",
        "AI coaching and support",
        "People ask the same internal questions because information is hard to find.",
        "AI knowledge tools fail when the documents are messy, access is unclear, or the assistant is allowed to answer beyond its source material.",
        "I help organize source documents, define boundaries, and test answers against common internal questions.",
        "Team members can find routine answers faster while sensitive or uncertain questions still get escalated.",
    ),
    (
        "Teach AI to match your voice and standards",
        "AI coaching and support",
        "AI drafts are useful, but they do not sound like your business yet.",
        "Voice problems happen when AI does not have examples, rules, banned phrases, preferred structure, or a review process.",
        "I create a voice guide, examples, prompts, and quality checklist for the kinds of writing you use most.",
        "Drafts start closer to usable and require less rewriting.",
    ),
    (
        "Evaluate AI risk before adopting a tool",
        "AI coaching and support",
        "A new AI tool looks promising, but you are unsure about privacy, workflow fit, or real value.",
        "AI tools can add subscriptions and risk before they add measurable benefit.",
        "I review the tool against your use case, data sensitivity, team habits, integration needs, and support burden.",
        "You can decide with more confidence whether to adopt, test, wait, or choose another path.",
    ),
    (
        "Create an AI coaching plan for one role",
        "AI coaching and support",
        "One person or role could benefit from AI, but they need targeted help.",
        "Role-specific coaching works better than broad training because it focuses on the tasks, risks, and judgment calls that matter every week.",
        "I identify useful tasks, build prompts, set guardrails, and support the person while they practice.",
        "AI becomes easier to use in the flow of that role's real work.",
    ),
    (
        "Too many product ideas are competing",
        "Product strategy",
        "You have too many product ideas and need a clear first move.",
        "Good ideas compete for attention when user pain, business value, effort, risk, and timing are not compared clearly.",
        "I help sort ideas by customer job, expected outcome, constraints, and the smallest useful version.",
        "You leave with a sharper priority and less pressure to build everything at once.",
    ),
    (
        "A product idea needs a reality check",
        "Product strategy",
        "An idea sounds promising, but you need to know what could make it fail.",
        "Ideas feel safer in brainstorming than they do in front of real users, budgets, timelines, and technical constraints.",
        "I examine the audience, problem, alternatives, adoption friction, business model, and build path.",
        "You understand the strongest case, the biggest risks, and the smartest next test.",
    ),
    (
        "Turn customer complaints into priorities",
        "Product strategy",
        "Customers are giving feedback, but it is hard to translate complaints into action.",
        "Complaints can lead to scattered fixes when no one separates symptoms from root causes.",
        "I group the feedback, identify repeated jobs and friction points, and connect them to product or workflow priorities.",
        "The feedback becomes a decision tool instead of a pile of frustration.",
    ),
    (
        "Map the customer job before building",
        "Product strategy",
        "You need to understand what customers are trying to accomplish before choosing features.",
        "Building around features too early can miss the actual job, context, constraints, and success criteria.",
        "I help map the customer situation, progress they want, alternatives they use, and signals that the solution is working.",
        "You get a clearer product direction before spending money on development.",
    ),
    (
        "A build-vs-buy decision is unclear",
        "Product strategy",
        "You are deciding whether to buy software, customize a tool, or build something new.",
        "Build-vs-buy decisions get expensive when hidden costs, workflow fit, data ownership, and support needs are ignored.",
        "I compare the options against real usage, integrations, budget, flexibility, and long-term maintenance.",
        "You can choose the path that solves the problem without creating unnecessary future burden.",
    ),
    (
        "MVP scope is starting to sprawl",
        "Product strategy",
        "You want to launch something useful without turning it into a giant project.",
        "MVPs often become bloated because every edge case, future feature, and internal preference gets included too soon.",
        "I help define the smallest useful version, what to delay, what to measure, and what must be true for launch.",
        "You get a leaner build plan and a better chance of learning quickly.",
    ),
    (
        "Improve onboarding for a web app",
        "Product strategy",
        "People sign up or start using the app, but they do not reach value quickly enough.",
        "Onboarding problems hide in unclear first steps, too much setup, weak empty states, missing guidance, and confusing success moments.",
        "I review the first-use path, clarify the core job, and simplify the steps that lead to value.",
        "Users understand what to do next and are more likely to keep going.",
    ),
    (
        "The workflow is confusing before software",
        "Product strategy",
        "A workflow feels broken, but software may not be the first fix.",
        "Automating a confusing process can make the confusion faster instead of better.",
        "I map the current process, identify decisions, handoffs, waste, and unclear ownership before recommending tools.",
        "You fix the real workflow instead of buying or building around the wrong problem.",
    ),
    (
        "The vendor or developer request is too vague",
        "Product strategy",
        "You need outside help, but the request is not clear enough to price or build well.",
        "Vague requirements create mismatched estimates, scope creep, and handoffs where the vendor has to guess.",
        "I turn the business need into clear goals, user flows, constraints, must-haves, open questions, and acceptance criteria.",
        "Vendors can respond more accurately and you can evaluate proposals with more confidence.",
    ),
    (
        "A vendor proposal is hard to evaluate",
        "Product strategy",
        "A software, website, or automation proposal looks expensive or unclear.",
        "Vendor proposals can hide assumptions, missing support, vague deliverables, or work that does not solve the real problem.",
        "I review the proposal through business, product, technical, UX, maintenance, and risk lenses.",
        "You understand what you are buying, what is missing, and what questions to ask before committing.",
    ),
    (
        "Plan a dashboard people will actually use",
        "Product strategy",
        "You want a dashboard, but you do not want another screen people ignore.",
        "Dashboards fail when they show what is available instead of what helps someone make a decision.",
        "I define the audience, decisions, metrics, data sources, update rhythm, and follow-up actions before layout.",
        "The dashboard has a clearer purpose and a better chance of becoming part of real work.",
    ),
    (
        "Decide whether an idea is worth automating",
        "Product strategy",
        "You see repeated work, but you are unsure whether automation is worth it.",
        "Not every repeated task deserves automation, especially if the process, volume, risk, or data quality is unclear.",
        "I compare the time savings, error reduction, complexity, maintenance, and human judgment required.",
        "You know whether to automate now, simplify first, or leave the task manual.",
    ),
    (
        "Clarify pricing or package structure",
        "Product strategy",
        "Your offers are useful, but the way they are packaged may be hard to understand.",
        "Pricing confusion can come from too many options, unclear outcomes, weak boundaries, or service language that reflects the business more than the buyer.",
        "I help simplify the packages, buyer logic, tradeoffs, and page language.",
        "Customers can compare options more easily and you can sell with more confidence.",
    ),
    (
        "Create a product roadmap for a small team",
        "Product strategy",
        "The team needs a roadmap that is realistic, useful, and not overloaded.",
        "Roadmaps become wish lists when priorities are not tied to customer value, team capacity, and business goals.",
        "I help shape a roadmap around outcomes, constraints, sequencing, risk, and what should wait.",
        "The team gets a clearer plan that supports decisions instead of creating pressure.",
    ),
    (
        "A project has stalled",
        "Product strategy",
        "A website, app, automation, or product effort started but lost momentum.",
        "Projects stall when ownership, scope, decisions, vendors, dependencies, or next steps become unclear.",
        "I review what exists, identify the blocker, simplify the path, and help define the next useful move.",
        "The project becomes actionable again instead of sitting half-finished.",
    ),
    (
        "Turn a rough idea into a clickable prototype",
        "Product strategy",
        "You need people to understand an idea before committing to a build.",
        "Words alone can hide assumptions about flow, screens, data, and user decisions.",
        "I turn the idea into a lightweight prototype or flow that makes the concept easier to discuss and test.",
        "You can get feedback, align stakeholders, and reduce risk before development.",
    ),
    (
        "Prospects need quicker quote or fit answers",
        "Website and app care",
        "Customers need a faster way to answer a few questions and understand the likely cost, fit, or next step.",
        "Quote requests get slow when every estimate starts with back-and-forth emails, missing details, and manual calculations.",
        "I define the questions, rules, outputs, follow-up path, and review points, then build a practical tool that supports sales without overpromising.",
        "Prospects get a clearer first answer and your team receives better-qualified requests.",
    ),
    (
        "Website visitors need quick answers",
        "AI coaching and support",
        "Visitors need quick answers on your website without forcing every question into a manual email or phone call.",
        "AI support agents become risky when they are trained on weak content, answer beyond what they should know, or create promises the business cannot keep.",
        "I define the support jobs, prepare the source content, set guardrails, build the agent flow, and create a review process for quality and escalation.",
        "Visitors get faster answers while your business keeps control of accuracy, tone, privacy, and follow-up.",
    ),
    (
        "Build a personal task and reminder system",
        "Individual consulting",
        "Tasks keep slipping because reminders are spread across too many apps or habits.",
        "A task system fails when it is too complex, too easy to ignore, or disconnected from real routines.",
        "I help choose a simple structure, capture method, reminder rhythm, and review habit.",
        "You get a system that supports follow-through instead of becoming another thing to manage.",
    ),
    (
        "Automate personal paperwork and forms",
        "Individual consulting",
        "Repeated personal paperwork takes more time than it should.",
        "Forms, applications, PDFs, and repeated information become frustrating when every request starts from scratch.",
        "I help create templates, organized source information, and AI-assisted drafts where appropriate.",
        "Recurring paperwork becomes faster, clearer, and less mentally draining.",
    ),
    (
        "Create a simple budget or planning spreadsheet",
        "Individual consulting",
        "You need a practical spreadsheet, not a complicated financial system.",
        "Planning gets harder when the spreadsheet is overbuilt, unclear, or disconnected from how you make decisions.",
        "I help design a simple sheet around the few categories, questions, and review habits that matter.",
        "You get a planning tool you can actually keep using.",
    ),
    (
        "The business needs a clearer website",
        "Website and app care",
        "Your business needs a clearer, more professional website that explains the offer and turns visitors into real inquiries.",
        "A weak or outdated website makes people work too hard to understand what you do, why they should trust you, and how to take the next step.",
        "I clarify the message, plan the pages, build the site, connect the contact path, and prepare it for ongoing updates and support.",
        "You get a useful business website that is easier to understand, easier to maintain, and ready to support sales conversations.",
    ),
    (
        "Operations are scattered across too many places",
        "Automation",
        "Your team needs one practical place to manage records, requests, statuses, approvals, or daily operations.",
        "Internal work gets messy when important details live across spreadsheets, inboxes, chat threads, and memory.",
        "I define the workflow, data, roles, screens, and support needs, then build a focused internal tool that fits the way the business works.",
        "Your team can manage the work in one clearer system instead of chasing information across tools.",
    ),
    (
        "Inbox and calendar are overloaded",
        "Individual consulting",
        "Your inbox and calendar are carrying too much of your life or work.",
        "Overload grows when messages, appointments, reminders, and decisions all compete in the same places.",
        "I help define filters, routines, reminders, labels, scheduling habits, and AI-assisted summaries where useful.",
        "Email and calendar become easier to review and less likely to hide important commitments.",
    ),
    (
        "Customer details are disconnected from the CRM",
        "Automation",
        "Your leads, customers, forms, and follow-up need to connect to the CRM instead of living in separate places.",
        "CRM value disappears when people still copy information by hand, miss required fields, or cannot trust where customer details land.",
        "I map the lead and customer path, clean up the handoff, connect forms or tools, and make sure the CRM receives useful context.",
        "Customer information becomes easier to track, follow up on, and use without extra copy-paste work.",
    ),
    (
        "Use AI for writing and research without feeling stuck",
        "Individual consulting",
        "You want AI help for writing, research, or decisions, but do not know how to start.",
        "AI can feel overwhelming when the first prompt is unclear and the output needs too much cleanup.",
        "I coach you through practical prompts, source checking, revision habits, and ways to keep your voice intact.",
        "AI becomes a helpful thinking partner instead of a confusing blank box.",
    ),
    (
        "A small business tech stack is starting from zero",
        "Individual consulting",
        "You need the basics in place: domain, email, site, forms, scheduling, payments, and simple records.",
        "Starting from scratch is hard because every tool choice affects future work and support.",
        "I help choose the simplest workable stack, connect the pieces, and document how it fits together.",
        "You get a cleaner foundation without buying more software than you need.",
    ),
    (
        "A workflow may need a focused mobile app",
        "Website and app care",
        "You have a customer, employee, or field workflow that would work better as a focused mobile app.",
        "Mobile app projects get expensive when the problem, users, must-have features, data, and support plan are not clear before building.",
        "I help define the app, choose the right build path, create the essential workflows, and plan the launch and support model.",
        "You get a practical mobile app path built around real use instead of a bloated feature wish list.",
    ),
    (
        "You need one clear online home",
        "Individual consulting",
        "You need one clean place to explain who you are, what you do, and how people can contact you.",
        "Scattered profiles and links make it harder for people to understand your work, trust your experience, or take the next step.",
        "I help shape the message, page structure, contact path, and simple launch plan, then build or guide the smallest useful version.",
        "You have a professional page you can share without turning it into a giant branding project.",
    ),
    (
        "Prepare a solo business for its first website",
        "Individual consulting",
        "You need a first website, but you are not sure what it should say or include.",
        "First websites stall when offers, audience, trust points, tools, and next steps are still fuzzy.",
        "I help clarify the message, page structure, must-have tools, and simplest path to launch.",
        "You get a practical website plan that can be built without overcomplicating the business.",
    ),
    (
        "Client onboarding feels awkward or inconsistent",
        "Individual consulting",
        "You want new clients to know exactly what happens after they say yes.",
        "Onboarding feels awkward when documents, payments, forms, expectations, and first tasks are handled differently every time.",
        "I help design the onboarding steps, messages, forms, and reminders that fit your service.",
        "New clients get a smoother start and you reduce repeated admin work.",
    ),
]


ACTIVE_SERVICE_TITLES = {
    "Contact form submissions are not arriving",
    "The website feels slow",
    "WordPress warnings are piling up",
    "Website leads are going missing",
    "The mobile website is confusing",
    "The homepage no longer matches the business",
    "One offer needs a focused page",
    "A website move feels risky",
    "Key pages have accessibility barriers",
    "Visitors are seeing security warnings",
    "Visitors cannot find the right next step",
    "Website inquiries are stuck in inboxes or spreadsheets",
    "Customers need a clearer request and file handoff",
    "Website updates keep getting postponed",
    "Prospects need quicker quote or fit answers",
    "The business needs a clearer website",
    "A workflow may need a focused mobile app",
    "Leads need follow-up you can trust",
    "Intake submissions become loose work",
    "Important numbers take too long to see",
    "Proposals take too long to prepare",
    "Appointment confirmations are confusing",
    "CRM data is hard to trust",
    "New customer onboarding feels inconsistent",
    "A spreadsheet is carrying too much responsibility",
    "Copy-paste is slowing the work down",
    "The spreadsheet process is getting fragile",
    "Operations are scattered across too many places",
    "Customer details are disconnected from the CRM",
    "AI tool choices feel noisy",
    "The team needs safer rules for AI and client data",
    "AI prompts are inconsistent across daily work",
    "The team is unsure how to use AI in real work",
    "Support replies need to be faster without getting sloppy",
    "Procedures are hard for the team to find",
    "Website visitors need quick answers",
    "Too many product ideas are competing",
    "A product idea needs a reality check",
    "A build-vs-buy decision is unclear",
    "MVP scope is starting to sprawl",
    "The workflow is confusing before software",
    "The vendor or developer request is too vague",
    "A vendor proposal is hard to evaluate",
    "A project has stalled",
    "Inbox and calendar are overloaded",
    "A small business tech stack is starting from zero",
    "You need one clear online home",
    "Client onboarding feels awkward or inconsistent",
}


SERVICE_SLUG_OVERRIDES = {
    "Contact form submissions are not arriving": "fix-a-broken-contact-form",
    "The website feels slow": "make-a-slow-website-feel-fast",
    "WordPress warnings are piling up": "clean-up-wordpress-plugin-warnings",
    "Website leads are going missing": "stop-website-leads-from-going-missing",
    "The mobile website is confusing": "improve-a-confusing-mobile-website",
    "The homepage no longer matches the business": "refresh-an-outdated-homepage",
    "One offer needs a focused page": "create-a-landing-page-for-one-offer",
    "A website move feels risky": "migrate-a-website-without-losing-momentum",
    "Key pages have accessibility barriers": "fix-accessibility-blockers-on-key-pages",
    "Visitors are seeing security warnings": "fix-ssl-and-website-security-warnings",
    "Visitors cannot find the right next step": "improve-website-navigation",
    "Website inquiries are stuck in inboxes or spreadsheets": "connect-website-forms-to-your-crm-or-spreadsheet",
    "Customers need a clearer request and file handoff": "build-a-customer-portal-for-requests-and-files",
    "Website updates keep getting postponed": "keep-monthly-website-updates-moving",
    "Prospects need quicker quote or fit answers": "build-an-online-quote-or-estimate-tool",
    "The business needs a clearer website": "build-a-new-website-for-your-business",
    "A workflow may need a focused mobile app": "build-a-mobile-app-for-your-business",
    "Leads need follow-up you can trust": "automate-lead-follow-up",
    "Intake submissions become loose work": "turn-intake-forms-into-organized-tasks",
    "Important numbers take too long to see": "build-a-simple-reporting-dashboard",
    "Proposals take too long to prepare": "generate-proposals-from-repeat-inputs",
    "Appointment confirmations are confusing": "connect-scheduling-and-confirmation-emails",
    "CRM data is hard to trust": "clean-up-crm-fields-and-duplicate-records",
    "New customer onboarding feels inconsistent": "build-a-new-customer-onboarding-workflow",
    "A spreadsheet is carrying too much responsibility": "convert-spreadsheet-work-into-a-simple-app",
    "Copy-paste is slowing the work down": "reduce-copy-and-paste-between-tools",
    "The spreadsheet process is getting fragile": "replace-a-messy-spreadsheet-with-a-cleaner-process",
    "Operations are scattered across too many places": "build-an-internal-admin-tool-to-manage-your-business",
    "Customer details are disconnected from the CRM": "integrate-your-business-with-a-crm",
    "AI tool choices feel noisy": "choose-ai-tools-for-your-business",
    "The team needs safer rules for AI and client data": "create-safe-ai-rules-for-client-data",
    "AI prompts are inconsistent across daily work": "build-a-prompt-library-for-daily-work",
    "The team is unsure how to use AI in real work": "train-your-team-to-use-ai-confidently",
    "Support replies need to be faster without getting sloppy": "use-ai-to-improve-customer-support-replies",
    "Procedures are hard for the team to find": "create-a-custom-ai-assistant-for-procedures",
    "Website visitors need quick answers": "build-an-ai-powered-website-support-agent",
    "Too many product ideas are competing": "decide-what-to-build-first",
    "A product idea needs a reality check": "pressure-test-a-new-product-idea",
    "A build-vs-buy decision is unclear": "choose-build-vs-buy-for-a-tool",
    "MVP scope is starting to sprawl": "define-an-mvp-without-overbuilding",
    "The workflow is confusing before software": "simplify-a-confusing-workflow-before-software",
    "The vendor or developer request is too vague": "create-requirements-for-a-developer-or-vendor",
    "A vendor proposal is hard to evaluate": "review-a-vendor-proposal-before-signing",
    "A project has stalled": "recover-a-project-that-stalled",
    "Inbox and calendar are overloaded": "simplify-email-and-calendar-overload",
    "A small business tech stack is starting from zero": "set-up-a-small-business-tech-stack-from-scratch",
    "You need one clear online home": "create-a-simple-personal-website-or-portfolio",
    "Client onboarding feels awkward or inconsistent": "create-a-simple-client-onboarding-path",
}


ARCHIVED_SERVICE_REDIRECTS = {
    slugify(title): "/#service-list"
    for title, *_ in SERVICE_SEEDS
    if title not in ACTIVE_SERVICE_TITLES
}


def _build_services() -> list[Service]:
    services: list[Service] = []
    seen: set[str] = set()
    missing = ACTIVE_SERVICE_TITLES - {title for title, *_ in SERVICE_SEEDS}
    if missing:
        raise ValueError(f"Active service title not found: {sorted(missing)}")

    for title, category, summary, pain, solution, result in SERVICE_SEEDS:
        if title not in ACTIVE_SERVICE_TITLES:
            continue
        slug = SERVICE_SLUG_OVERRIDES.get(title, slugify(title))
        if slug in seen:
            raise ValueError(f"Duplicate service slug: {slug}")
        seen.add(slug)
        services.append(
            Service(
                slug=slug,
                title=title,
                category=category,
                summary=summary,
                pain=pain,
                solution=solution,
                result=result,
            )
        )
    return services


SERVICES = _build_services()
SERVICE_BY_SLUG = {service.slug: service for service in SERVICES}


CATEGORY_CHECKS = {
    "Website and app care": [
        "Review the live user path, not just the admin screen.",
        "Check forms, content, mobile behavior, speed, hosting, redirects, and follow-up.",
        "Separate quick repairs from the improvements worth supporting over time.",
    ],
    "Automation": [
        "Map the repeated task from trigger to final human decision.",
        "Find the handoffs, manual copying, missing reminders, and places where data gets stale.",
        "Automate the parts that should be consistent while keeping judgment where it belongs.",
    ],
    "AI coaching and support": [
        "Identify the real work AI should help with before choosing tools or prompts.",
        "Define privacy guardrails, review points, examples, and quality standards.",
        "Turn useful experiments into repeatable workflows people can actually use.",
    ],
    "Product strategy": [
        "Clarify the customer job, business goal, constraints, and decision that needs to be made.",
        "Sort ideas by value, risk, effort, timing, and what can be learned fastest.",
        "Create a practical next step before committing to a bigger build or vendor path.",
    ],
    "Individual consulting": [
        "Understand the recurring friction and the way you already prefer to work.",
        "Simplify the tools, routines, reminders, notes, or AI prompts around the real habit.",
        "Create a system light enough to keep using after the first setup.",
    ],
}


GERUND_PREFIXES = (
    ("Pressure-test", "pressure-testing"),
    ("Set up", "setting up"),
    ("Clean up", "cleaning up"),
    ("Simplify", "simplifying"),
    ("Stop", "stopping"),
    ("Make", "making"),
    ("Fix", "fixing"),
    ("Improve", "improving"),
    ("Refresh", "refreshing"),
    ("Clarify", "clarifying"),
    ("Create", "creating"),
    ("Migrate", "migrating"),
    ("Repair", "repairing"),
    ("Document", "documenting"),
    ("Prepare", "preparing"),
    ("Turn", "turning"),
    ("Keep", "keeping"),
    ("Automate", "automating"),
    ("Send", "sending"),
    ("Build", "building"),
    ("Generate", "generating"),
    ("Organize", "organizing"),
    ("Route", "routing"),
    ("Connect", "connecting"),
    ("Integrate", "integrating"),
    ("Convert", "converting"),
    ("Reduce", "reducing"),
    ("Replace", "replacing"),
    ("Choose", "choosing"),
    ("Train", "training"),
    ("Use", "using"),
    ("Add", "adding"),
    ("Evaluate", "evaluating"),
    ("Teach", "teaching"),
    ("Decide", "deciding"),
    ("Define", "defining"),
    ("Review", "reviewing"),
    ("Plan", "planning"),
    ("Recover", "recovering"),
    ("Get", "getting"),
    ("Move", "moving"),
    ("Map", "mapping"),
)


SERVICE_SHARE_HINTS = (
    (
        ("customer portal", "requests and files", "upload files"),
        "the request types, files customers need to upload, status updates they need to see, required fields, permissions, notification rules, and examples of the back-and-forth you want to reduce",
    ),
    (
        ("quote", "estimate", "cost"),
        "the questions customers should answer, the factors that affect pricing or fit, sample estimates, rules or ranges, required follow-up details, and where the request should go after submission",
    ),
    (
        ("website support agent", "support agent", "chatbot"),
        "the questions visitors ask most, support docs or page content, topics the agent should avoid, escalation rules, contact handoff needs, tone examples, and any privacy limits",
    ),
    (
        ("internal admin tool", "manage your business", "records", "approvals"),
        "the records or requests to manage, current spreadsheets or tools, user roles, statuses, approvals, reports, permissions, and examples of the daily work the tool should replace",
    ),
    (
        ("crm integration", "integrate your business with a crm", "customer information"),
        "the CRM you use or are considering, form sources, lead stages, required fields, current copy-paste steps, follow-up rules, and examples of customer records that should be created or updated",
    ),
    (
        ("mobile app", "field workflow"),
        "the users, devices, must-have workflows, data that needs to be captured or shown, login needs, offline requirements if any, examples of similar apps, and what would make the app worth using",
    ),
    (
        ("new website", "professional website", "website for your business"),
        "your current website if you have one, examples of sites you like, the services or offers to explain, trust points, photos or brand assets, must-have pages, and the action visitors should take",
    ),
    (
        ("personal website", "portfolio"),
        "examples of sites you like, the audience you want to reach, services or work you want to highlight, bio or resume notes, photos or links, and the contact action visitors should take",
    ),
    (
        ("contact form", "form submissions", "website forms", "forms"),
        "the affected page URL, form fields, expected inbox or CRM destination, test submissions, confirmation emails, spam settings, and examples of messages that did or did not arrive",
    ),
    (
        ("business emails", "going to spam", "spam", "deliverability", "spf", "dkim", "dmarc"),
        "examples of messages that landed in spam, the sending email address, form or mailbox involved, email provider, any bounce messages, and screenshots of current SPF, DKIM, or DMARC records if you have them",
    ),
    (
        ("ssl", "security warnings", "mixed content", "browser warnings"),
        "the affected page URLs, screenshots of the browser warning, recent hosting or plugin changes, certificate details if available, and examples of links or assets that trigger the warning",
    ),
    (
        ("slow", "fast", "speed", "performance"),
        "the slow page URLs, device or browser examples, recent site changes, PageSpeed or Lighthouse reports if you have them, and the parts of the experience that feel worst",
    ),
    (
        ("wordpress", "plugin", "theme"),
        "the WordPress warnings, plugin or theme names, screenshots of update notices, hosting details, backup status, and the site features you cannot afford to break",
    ),
    (
        ("lead", "crm", "follow-up", "follow up"),
        "where the lead starts, where it should land, the CRM or spreadsheet involved, notification examples, missed follow-up examples, and the timing you expect",
    ),
    (
        ("mobile", "navigation", "homepage", "service page", "landing page", "local", "blog", "resources"),
        "the page URLs, screenshots from phone and desktop, the action visitors should take, examples of confusing copy or layout, and any search or analytics context you already have",
    ),
    (
        ("email and calendar", "inbox", "email overload"),
        "the inbox and calendar tools involved, examples of messages or appointments that get missed, current filters or labels, reminder habits, and the commitments that need to stay visible",
    ),
    (
        ("booking", "calendar", "scheduling", "appointment"),
        "the booking link, calendar tool, confirmation and reminder messages, timezone or cancellation examples, and the step where people get confused",
    ),
    (
        ("checkout", "payment", "invoice"),
        "the checkout or payment link, provider name, failed step, screenshots of errors, confirmation messages, and examples of successful and failed attempts",
    ),
    (
        ("accessibility", "ada", "screen reader", "keyboard"),
        "the key page URLs, forms or actions that matter most, any audit results, screenshots, keyboard or screen reader issues if known, and the audience that needs access",
    ),
    (
        ("migration", "migrate", "redirect"),
        "the current platform, target platform, domain details, important page list, redirect needs, forms, tracking, email dependencies, and launch timing",
    ),
    (
        ("dashboard", "report", "measurement", "analytics", "metrics", "data"),
        "the current data sources, sample spreadsheet or report, decisions the numbers should support, who needs the view, and how often it should update",
    ),
    (
        ("intake", "portal", "request form", "submitted files", "files"),
        "the current intake path, sample submissions, file examples, required fields, routing rules, and what usually causes back-and-forth",
    ),
    (
        ("backlog", "roadmap", "stalled", "project"),
        "the current list of requests or ideas, known blockers, users affected, business priority, deadlines, and any vendor or internal history",
    ),
    (
        ("deadline", "reminder", "status", "alert", "priority"),
        "the trigger, due dates, owners, notification channels, examples of missed items, and what should happen when something is urgent",
    ),
    (
        ("vendor proposal", "proposal before signing"),
        "the proposal or statement of work, estimate, timeline, assumptions, deliverables, support terms, open questions, and the business outcome the vendor is supposed to support",
    ),
    (
        ("proposal", "document", "paperwork", "template", "draft"),
        "example documents, repeated fields, templates, source data, approval steps, and what a good final draft should include",
    ),
    (
        ("onboarding", "new customer", "new hire", "employee"),
        "the current steps, forms, access needs, documents, owners, handoff points, and places where people usually wait or ask questions",
    ),
    (
        ("spreadsheet", "spreadsheets"),
        "the workbook, sample rows, formulas or tabs that matter, who edits it, what breaks, and what output or decision it needs to support",
    ),
    (
        ("ai", "prompt", "voice", "content", "writing", "research", "meeting", "call", "knowledge"),
        "the AI tools you have tried, sample inputs and outputs, examples of good and bad results, privacy concerns, source material, and the role or team that will use it",
    ),
    (
        ("product", "mvp", "idea", "build", "buy", "customer", "prototype", "vendor", "requirements", "pricing", "package"),
        "the idea or decision, target customer, current alternatives, notes or proposals, constraints, budget or timing, and what would make the next move worthwhile",
    ),
    (
        ("personal", "household", "family", "task", "email", "budget", "travel", "notes", "solo", "client onboarding"),
        "the apps, notes, calendars, files, examples, routines, preferences, privacy constraints, and recurring decisions involved",
    ),
)


CATEGORY_ONGOING_CONTEXT = {
    "Website and app care": "If the issue is isolated, it may be a focused repair. If it touches updates, hosting, forms, search visibility, analytics, or regular content changes, ongoing support usually keeps it from drifting again.",
    "Automation": "If the workflow is stable, it may be a one-time setup. If the process changes, tools evolve, or people need help trusting the automation, ongoing support keeps the workflow useful.",
    "AI coaching and support": "If the need is narrow, a focused coaching or setup session may be enough. If people are learning new habits, testing tools, or creating guardrails, ongoing support helps the practice stick.",
    "Product strategy": "Some product questions need one clear decision session. Others benefit from ongoing support while the idea moves through testing, scope, vendor conversations, or early build work.",
    "Individual consulting": "Some personal systems need one setup. Others work better with light ongoing support while the routine becomes natural and the tools get adjusted around real life.",
}


CATEGORY_AGENCY_CONTEXT = {
    "Website and app care": "Website and app issues often cross content, hosting, UX, forms, email, search, and operations. Audo brings senior product, engineering, and agency delivery experience without splitting that context across account layers.",
    "Automation": "Automation work needs someone who understands the actual workflow, not just the tool connection. Audo brings senior product and engineering judgment to shape, build, explain, and support the process directly.",
    "AI coaching and support": "AI work needs practical judgment, privacy awareness, examples, training, and follow-through. Audo brings broad technology and product experience while keeping the coaching close to the real work people do every day.",
    "Product strategy": "Product work gets better when strategy and execution stay connected. Audo brings product and engineering leadership experience, so the recommendation stays grounded in what it would take to actually build or support it.",
    "Individual consulting": "Individual and small-business systems are personal and context-heavy. Audo brings senior technology experience in a direct, practical, lightweight model instead of turning the work into a large process.",
}


def lower_first(value: str) -> str:
    if not value:
        return value
    if len(value) > 1 and value[0].isupper() and value[1].isupper():
        return value
    return value[0].lower() + value[1:]


def strip_period(value: str) -> str:
    return value.strip().rstrip(".")


def gerund_topic(title: str) -> str:
    for prefix, replacement in GERUND_PREFIXES:
        if title.lower().startswith(prefix.lower()):
            suffix = title[len(prefix) :]
            return replacement + suffix
    return lower_first(title)


def problem_topic(title: str) -> str:
    return lower_first(strip_period(title))


def solution_action(service: Service) -> str:
    action = strip_period(service.solution)
    if action.startswith("I help "):
        action = action[len("I help ") :]
    elif action.startswith("I "):
        action = action[len("I ") :]
    return lower_first(action)


def share_hints(service: Service) -> str:
    haystack = " | ".join(
        [service.title, service.category, service.summary, service.pain, service.solution, service.result]
    ).lower()
    for keywords, hints in SERVICE_SHARE_HINTS:
        if any(keyword_matches(haystack, keyword) for keyword in keywords):
            return hints
    return "the links, tools, screenshots, examples, recent changes, current workarounds, and the outcome you want"


def keyword_matches(haystack: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in haystack
    return re.search(rf"\b{re.escape(keyword)}\b", haystack) is not None


def get_service(slug: str) -> Service | None:
    return SERVICE_BY_SLUG.get(slug)


def service_cards() -> list[dict[str, str]]:
    return [
        {
            "title": service.title,
            "category": service.category,
            "summary": service.summary,
            "url": service.url,
        }
        for service in SERVICES
    ]


def service_dict(service: Service) -> dict[str, object]:
    data = asdict(service)
    data["url"] = service.url
    data["canonical_url"] = service.canonical_url
    data["meta_title"] = service.meta_title
    data["meta_description"] = service.meta_description
    data["checks"] = CATEGORY_CHECKS[service.category]
    data["faqs"] = service_faqs(service)
    return data


def service_faqs(service: Service) -> list[dict[str, str]]:
    topic = problem_topic(service.title)
    summary = lower_first(strip_period(service.summary))
    pain = lower_first(strip_period(service.pain))
    result = lower_first(strip_period(service.result))
    action = solution_action(service)
    hints = share_hints(service)
    return [
        {
            "question": f"Can Audo help when {topic} and I do not know the technical cause?",
            "answer": (
                f"Yes. You can start with the symptoms: {pain}. "
                f"I will help connect what you are seeing to the likely causes and the next step worth taking."
            ),
        },
        {
            "question": f"What should I share before discovery when {topic}?",
            "answer": (
                f"Share anything that shows {summary}. Useful starting points include {hints}. "
                f"That context gives me enough to {action}."
            ),
        },
        {
            "question": "Is solving this a one-time project or ongoing support?",
            "answer": (
                f"It can be either. The goal is that {result}. "
                f"{CATEGORY_ONGOING_CONTEXT[service.category]}"
            ),
        },
        {
            "question": "Why work with Audo on this problem instead of a large agency?",
            "answer": (
                f"{CATEGORY_AGENCY_CONTEXT[service.category]} "
                "You work directly with Aaron, so there are fewer handoffs, clearer context, and more of the budget goes toward useful thinking and execution."
            ),
        },
    ]
