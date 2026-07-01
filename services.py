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
        "Fix a broken contact form",
        "Website and app care",
        "Visitors try to reach you, but form submissions are not reliably arriving.",
        "A broken form quietly costs leads because the site looks available while the messages disappear, bounce, or land in the wrong inbox.",
        "I trace the form path, validation, notifications, spam settings, CRM handoff, and confirmation experience so the real failure is clear.",
        "Leads submit with confidence, messages land where they should, and you know how the form is being monitored.",
    ),
    (
        "Make a slow website feel fast",
        "Website and app care",
        "A slow website is making visitors wait, bounce, or lose confidence.",
        "Speed problems usually come from images, scripts, hosting, caching, layout shifts, or too many small decisions that accumulated over time.",
        "I review the real pages people use, identify the biggest speed drains, and prioritize fixes that improve the experience without rebuilding everything.",
        "Visitors get a faster first impression, mobile pages feel smoother, and you have a clear path for continued performance care.",
    ),
    (
        "Clean up WordPress plugin warnings",
        "Website and app care",
        "WordPress updates, plugin notices, and warnings are piling up without a clear owner.",
        "Plugin clutter creates risk because it is hard to know what can be updated, removed, replaced, or left alone without breaking the site.",
        "I review the theme, plugins, hosting, backups, update path, and critical features before changing anything that affects production.",
        "The site has fewer unknowns, safer updates, and a practical maintenance rhythm instead of a dashboard full of anxiety.",
    ),
    (
        "Stop website leads from going missing",
        "Website and app care",
        "People submit forms, but the follow-up path is unclear or unreliable.",
        "Lead loss can happen across the form, email deliverability, CRM rules, notifications, spam filters, and manual follow-up habits.",
        "I map the full lead path from submit button to human response and fix the weak links that cause delay or confusion.",
        "New inquiries are easier to see, assign, respond to, and trust.",
    ),
    (
        "Improve a confusing mobile website",
        "Website and app care",
        "Your site technically works on phones, but visitors struggle to understand or act.",
        "Mobile friction often hides in navigation, long text, tiny tap targets, slow sections, confusing forms, and calls to action that get buried.",
        "I review the site like a real mobile visitor and simplify the path to the action that matters most.",
        "The mobile experience becomes easier to scan, easier to use, and more likely to create a real inquiry.",
    ),
    (
        "Refresh an outdated homepage",
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
        "Clean up hosting, DNS, and domain confusion",
        "Website and app care",
        "Your domain, hosting, email, redirects, or DNS records feel scattered and risky.",
        "When ownership and settings are unclear, simple changes can break the site, email, analytics, or search visibility.",
        "I inventory the accounts, records, redirects, certificates, email settings, and hosting dependencies before recommending changes.",
        "You know what controls what, where risk lives, and how to make future changes with confidence.",
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
        "Create a landing page for one offer",
        "Website and app care",
        "You have a specific offer that needs a focused page instead of sending everyone to the homepage.",
        "A general site page can dilute the message when a campaign, referral, or sales conversation needs one clear path.",
        "I shape the page around the offer, audience, pain, proof, objections, and conversion action.",
        "Prospects land on a page that matches their intent and makes the next step easier.",
    ),
    (
        "Migrate a website without losing momentum",
        "Website and app care",
        "You need to move platforms, hosts, pages, or domains without creating a mess.",
        "Migrations create risk when redirects, content, forms, tracking, email, DNS, and launch timing are treated separately.",
        "I plan the migration path, map dependencies, preserve the important pages, and verify the launch details.",
        "The move is calmer, cleaner, and less likely to create broken links or missed leads.",
    ),
    (
        "Fix accessibility blockers on key pages",
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
        "Fix SSL and website security warnings",
        "Website and app care",
        "Visitors are seeing browser warnings, mixed content, or security messages.",
        "Security warnings damage trust quickly and can come from certificates, redirects, old links, embedded assets, or hosting settings.",
        "I identify the source, clean up the configuration, and verify the site loads securely across important paths.",
        "Visitors no longer hit avoidable trust barriers before they can contact you.",
    ),
    (
        "Improve website navigation",
        "Website and app care",
        "Visitors can get to the site, but they cannot quickly find the right next step.",
        "Navigation grows messy when pages, offers, audiences, and internal language accumulate without a clear decision path.",
        "I simplify the menu, page hierarchy, labels, and calls to action around what visitors are actually trying to do.",
        "People understand where to go faster, and important pages stop being buried.",
    ),
    (
        "Connect website forms to your CRM or spreadsheet",
        "Website and app care",
        "Website inquiries need to land somewhere useful instead of sitting in an inbox.",
        "Manual copying from forms to CRMs or spreadsheets wastes time and creates missed follow-up risk.",
        "I connect the form output to the right destination, add useful fields, and keep the handoff simple enough to trust.",
        "New inquiries are easier to track, assign, and follow up on without extra copy-paste work.",
    ),
    (
        "Create a client portal intake flow",
        "Website and app care",
        "Clients need a cleaner way to submit requests, files, updates, or project details.",
        "Email-only intake makes context hard to find and creates repeated clarification work.",
        "I design a simple intake flow, route submissions, organize the information, and connect it to the tools you already use.",
        "Client requests arrive with better context and less back-and-forth.",
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
        "Keep monthly website updates moving",
        "Website and app care",
        "Small website changes keep getting postponed because no one owns them.",
        "Minor edits, updates, content changes, and cleanup work can pile up until the site no longer reflects the business.",
        "I create a simple monthly rhythm for updates, review, fixes, and practical improvements.",
        "Your site keeps moving forward without needing a big project every time something changes.",
    ),
    (
        "Automate lead follow-up",
        "Automation",
        "New leads need timely, consistent follow-up without relying on memory.",
        "Follow-up falls apart when every inquiry requires a manual reminder, copied email, or repeated status check.",
        "I map the lead stages, define the right messages, and connect the tools that trigger reminders or follow-up steps.",
        "Leads receive a faster response and fewer opportunities fall through the cracks.",
    ),
    (
        "Turn intake forms into organized tasks",
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
        "Build a simple reporting dashboard",
        "Automation",
        "You need a quick view of important numbers without building reports by hand.",
        "Manual reporting wastes time and often arrives too late to guide decisions.",
        "I identify the few metrics that matter, connect the available data, and create a dashboard people can actually use.",
        "You get a clearer operating view with less recurring spreadsheet work.",
    ),
    (
        "Generate proposals from repeat inputs",
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
        "Connect scheduling and confirmation emails",
        "Automation",
        "Booked calls or appointments need clearer confirmations, reminders, and next steps.",
        "Scheduling tools can create confusion when confirmations, prep notes, cancellations, and reminders are disconnected.",
        "I review the appointment flow and connect the messages that help people show up ready.",
        "Meetings are easier to manage and require less manual coordination.",
    ),
    (
        "Clean up CRM fields and duplicate records",
        "Automation",
        "Your CRM has useful information, but duplicates and messy fields make it hard to trust.",
        "A messy CRM creates friction because people stop believing the data and return to spreadsheets or memory.",
        "I review fields, duplicates, required data, lead stages, and cleanup rules before recommending a practical structure.",
        "The CRM becomes easier to use, easier to report from, and less frustrating for the people who touch it.",
    ),
    (
        "Build a new customer onboarding workflow",
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
        "Convert spreadsheet work into a simple app",
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
        "Reduce copy and paste between tools",
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
        "Replace a messy spreadsheet with a cleaner process",
        "Automation",
        "A spreadsheet is carrying too much responsibility and is starting to slow everyone down.",
        "Messy spreadsheets create hidden rules, version confusion, broken formulas, and unclear ownership.",
        "I separate what should remain a spreadsheet from what needs a form, dashboard, automation, or lightweight tool.",
        "The process becomes simpler, more reliable, and easier for other people to use.",
    ),
    (
        "Choose AI tools for your business",
        "AI coaching and support",
        "You want to use AI, but the tool choices are noisy and hard to compare.",
        "AI adoption gets risky when tools are chosen because they are popular instead of because they solve a real workflow problem.",
        "I help define the jobs AI should do, compare tools against those jobs, and avoid unnecessary complexity.",
        "You get a practical shortlist and a clearer reason for what to try first.",
    ),
    (
        "Create safe AI rules for client data",
        "AI coaching and support",
        "Your team needs AI guidance that protects customer, employee, and business information.",
        "Without clear rules, people either avoid AI entirely or paste sensitive information into tools without thinking through risk.",
        "I help define plain-English guardrails, review points, approved use cases, and safer habits for everyday work.",
        "Your team can use AI with more confidence and less guesswork.",
    ),
    (
        "Build a prompt library for daily work",
        "AI coaching and support",
        "People are trying AI, but every result depends on inventing the prompt from scratch.",
        "AI feels inconsistent when good prompts live in one person's notes or get rewritten every time.",
        "I create reusable prompts around your actual tasks, voice, inputs, and quality standards.",
        "The team gets faster, more consistent AI outputs without needing everyone to become a prompt expert.",
    ),
    (
        "Train your team to use AI confidently",
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
        "Use AI to improve customer support replies",
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
        "Create a custom AI assistant for procedures",
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
        "Decide what to build first",
        "Product strategy",
        "You have too many product ideas and need a clear first move.",
        "Good ideas compete for attention when user pain, business value, effort, risk, and timing are not compared clearly.",
        "I help sort ideas by customer job, expected outcome, constraints, and the smallest useful version.",
        "You leave with a sharper priority and less pressure to build everything at once.",
    ),
    (
        "Pressure-test a new product idea",
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
        "Choose build vs buy for a tool",
        "Product strategy",
        "You are deciding whether to buy software, customize a tool, or build something new.",
        "Build-vs-buy decisions get expensive when hidden costs, workflow fit, data ownership, and support needs are ignored.",
        "I compare the options against real usage, integrations, budget, flexibility, and long-term maintenance.",
        "You can choose the path that solves the problem without creating unnecessary future burden.",
    ),
    (
        "Define an MVP without overbuilding",
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
        "Simplify a confusing workflow before software",
        "Product strategy",
        "A workflow feels broken, but software may not be the first fix.",
        "Automating a confusing process can make the confusion faster instead of better.",
        "I map the current process, identify decisions, handoffs, waste, and unclear ownership before recommending tools.",
        "You fix the real workflow instead of buying or building around the wrong problem.",
    ),
    (
        "Create requirements for a developer or vendor",
        "Product strategy",
        "You need outside help, but the request is not clear enough to price or build well.",
        "Vague requirements create mismatched estimates, scope creep, and handoffs where the vendor has to guess.",
        "I turn the business need into clear goals, user flows, constraints, must-haves, open questions, and acceptance criteria.",
        "Vendors can respond more accurately and you can evaluate proposals with more confidence.",
    ),
    (
        "Review a vendor proposal before signing",
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
        "Recover a project that stalled",
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
        "Get personal admin out of your head",
        "Individual consulting",
        "Important personal tasks, reminders, and decisions are scattered across memory, notes, and inboxes.",
        "Personal admin feels heavier when nothing has a trusted place to land or return at the right time.",
        "I help design a simple system for capture, reminders, documents, and review that fits how you actually live.",
        "You spend less mental energy trying to remember everything.",
    ),
    (
        "Organize household information with AI",
        "Individual consulting",
        "Household notes, instructions, preferences, and recurring tasks are hard to find when needed.",
        "Useful information loses value when it is trapped in texts, screenshots, emails, and half-finished notes.",
        "I help organize the information and create safe AI-assisted ways to search, summarize, or reuse it.",
        "You can find recurring answers faster without rebuilding the system every time.",
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
        "Use AI to plan travel or events",
        "Individual consulting",
        "Planning a trip or event involves too many tabs, details, and decisions.",
        "AI can help organize possibilities, but it needs constraints, preferences, verification, and a clear final plan.",
        "I help create an AI-assisted planning workflow for options, schedules, checklists, and decisions.",
        "You get a more organized plan with less research fatigue.",
    ),
    (
        "Build a knowledge base for recurring decisions",
        "Individual consulting",
        "You make similar decisions repeatedly and want your notes to become useful.",
        "Knowledge gets lost when it is saved without structure or never connected to the next decision.",
        "I help organize notes, examples, preferences, and decision criteria into a simple searchable system.",
        "You can reuse what you already learned instead of starting over.",
    ),
    (
        "Simplify email and calendar overload",
        "Individual consulting",
        "Your inbox and calendar are carrying too much of your life or work.",
        "Overload grows when messages, appointments, reminders, and decisions all compete in the same places.",
        "I help define filters, routines, reminders, labels, scheduling habits, and AI-assisted summaries where useful.",
        "Email and calendar become easier to review and less likely to hide important commitments.",
    ),
    (
        "Create a better way to track family projects",
        "Individual consulting",
        "Household projects, school tasks, purchases, repairs, or plans need a shared place to live.",
        "Family projects get messy when decisions happen across texts, receipts, notes, and memory.",
        "I help build a simple tracker or workflow that keeps status, owners, dates, links, and notes together.",
        "Everyone has a clearer view of what is open and what needs attention.",
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
        "Set up a small business tech stack from scratch",
        "Individual consulting",
        "You need the basics in place: domain, email, site, forms, scheduling, payments, and simple records.",
        "Starting from scratch is hard because every tool choice affects future work and support.",
        "I help choose the simplest workable stack, connect the pieces, and document how it fits together.",
        "You get a cleaner foundation without buying more software than you need.",
    ),
    (
        "Move scattered notes into one operating system",
        "Individual consulting",
        "Ideas, tasks, links, and notes live everywhere and nothing feels trustworthy.",
        "Scattered notes create friction because capture is easy but retrieval is unreliable.",
        "I help design a simple personal or business operating system for notes, tasks, projects, and recurring reviews.",
        "You can find and act on information more consistently.",
    ),
    (
        "Clean up domains, email, and online presence",
        "Individual consulting",
        "Your online basics exist, but ownership and setup are unclear.",
        "Domains, email accounts, DNS, profiles, and website settings create risk when no one knows what controls what.",
        "I inventory the setup, organize the accounts, document ownership, and identify cleanup opportunities.",
        "You know where your online presence lives and how to manage it safely.",
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
        "Create a simple client onboarding path",
        "Individual consulting",
        "You want new clients to know exactly what happens after they say yes.",
        "Onboarding feels awkward when documents, payments, forms, expectations, and first tasks are handled differently every time.",
        "I help design the onboarding steps, messages, forms, and reminders that fit your service.",
        "New clients get a smoother start and you reduce repeated admin work.",
    ),
]


def _build_services() -> list[Service]:
    services: list[Service] = []
    seen: set[str] = set()
    for title, category, summary, pain, solution, result in SERVICE_SEEDS:
        slug = slugify(title)
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
    topic = service.title[0].lower() + service.title[1:]
    return [
        {
            "question": f"Can Audo help me {topic} if I do not know the technical cause?",
            "answer": (
                "Yes. You do not need to diagnose the problem before reaching out. "
                f"Free Discovery starts with the plain-English situation, then I help identify what is causing the issue and what is worth doing next."
            ),
        },
        {
            "question": "What should I share before the discovery call?",
            "answer": (
                "Share the website, tool, workflow, examples, screenshots, links, or recent situations that show the friction. "
                "A short description is enough; I will review the context before responding."
            ),
        },
        {
            "question": f"Is {topic} a one-time project or ongoing support?",
            "answer": (
                "It can be either. Some situations need one focused fix, while others make more sense as monthly support so improvements, updates, and follow-up do not keep getting postponed."
            ),
        },
        {
            "question": "Why work with Audo instead of a large agency?",
            "answer": (
                "You work directly with Aaron, a senior product, software, website, automation, and AI partner. "
                "That means fewer handoffs, clearer context, and more of the budget going toward useful thinking and execution."
            ),
        },
    ]
