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
        description = f"{self.summary} Talk directly with Aaron about what is happening and what it will take to fix it."
        if len(description) <= 158:
            return description
        shorter = f"{self.summary} Request a free discovery call with Audo."
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
        "I test the form from submission to inbox, including validation, spam filters, notifications, and any CRM connection.",
        "Messages reach the right inbox, and you'll know how to check that the form is still working.",
    ),
    (
        "The website feels slow",
        "Website and app care",
        "A slow website is making visitors wait, bounce, or lose confidence.",
        "Speed problems usually come from images, scripts, hosting, caching, layout shifts, or too many small decisions that accumulated over time.",
        "I test the pages customers use, find what is slowing them down, and fix the biggest problems first.",
        "Pages load faster, especially on phones, without forcing a full rebuild.",
    ),
    (
        "WordPress warnings are piling up",
        "Website and app care",
        "WordPress updates, plugin notices, and warnings are piling up, and no one owns them.",
        "Plugin clutter creates risk because it is hard to know what can be updated, removed, replaced, or left alone without breaking the site.",
        "I review the theme, plugins, hosting, backups, update plan, and critical features before changing anything that affects production.",
        "The site has fewer unknowns, safer updates, and a simple maintenance routine instead of a dashboard full of anxiety.",
    ),
    (
        "Website leads are going missing",
        "Website and app care",
        "People submit forms, but the follow-up process is unclear or unreliable.",
        "Lead loss can happen across the form, email deliverability, CRM rules, notifications, spam filters, and manual follow-up habits.",
        "I follow a test lead from the form to the person who should respond, then fix where it gets delayed or lost.",
        "New inquiries are easier to see, assign, respond to, and trust.",
    ),
    (
        "The mobile website is confusing",
        "Website and app care",
        "Your site technically works on phones, but visitors struggle to understand or act.",
        "Mobile problems often hide in navigation, long text, tiny tap targets, slow sections, confusing forms, and calls to action that get buried.",
        "I use the site on a phone, find where people get stuck, and make the main action easier to complete.",
        "Visitors can read the page, use the menu, and finish the main action on a phone.",
    ),
    (
        "The homepage no longer matches the business",
        "Website and app care",
        "Your homepage no longer reflects what you do, who you help, or why people should trust you.",
        "An outdated homepage can make an active business look neglected or hard to understand.",
        "I rewrite the message around what customers need to know and rebuild the first screen around the most important action.",
        "The homepage explains the offer quickly and gives visitors an obvious way to respond.",
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
        "Fix booking calendar confusion",
        "Website and app care",
        "People are interested, but scheduling creates confusion, dead ends, or unnecessary back-and-forth.",
        "Booking problems can come from too many options, poor mobile UX, missing confirmations, timezone confusion, or disconnected follow-up.",
        "I review the booking flow, simplify the options, connect confirmations, and make sure the next step is obvious.",
        "Prospects can book faster, show up better prepared, and receive a cleaner first impression.",
    ),
    (
        "Fix broken checkout or payment links",
        "Website and app care",
        "Payment links, checkout steps, or purchase paths are failing at the moment trust matters most.",
        "Checkout problems can hide in expired links, redirects, embeds, scripts, payment settings, mobile layouts, or unclear confirmation steps.",
        "I test the checkout flow, isolate the failure, and make the buying process clearer and more reliable.",
        "Customers can complete payment with fewer problems and you can spot issues before they linger.",
    ),
    (
        "Fix business emails going to spam",
        "Website and app care",
        "Important business emails, form notifications, or client messages are landing in spam.",
        "Email trust problems create missed leads and awkward follow-up because people assume messages were never sent or never answered.",
        "I review the sending address, message route, SPF, DKIM, DMARC, form notifications, mailbox behavior, and message content to find the likely trust issues.",
        "Your emails have a better chance of reaching the inbox and you know what to monitor if deliverability slips again.",
    ),
    (
        "Set up simple website measurement",
        "Website and app care",
        "You want to know what is happening on the site without drowning in reports.",
        "Many small businesses either have no measurement or have disconnected tools that do not answer basic questions.",
        "I connect the basics, define the few actions worth watching, and make the data easier to interpret.",
        "You can see whether people are finding, using, and contacting you through the site.",
    ),
    (
        "Improve local service page visibility",
        "Website and app care",
        "Local customers should be able to understand where you work and what you offer.",
        "Local pages often underperform because they are thin, duplicated, unclear, or missing the details people and search engines expect.",
        "I review the page structure, service language, location signals, internal links, metadata, and helpful content gaps.",
        "Your local pages become clearer, more relevant, and better aligned with real search intent.",
    ),
    (
        "One offer needs its own page",
        "Website and app care",
        "You have a specific offer that deserves its own page instead of sending everyone to the homepage.",
        "A general site page can bury the offer when a campaign, referral, or sales conversation needs one message and one action.",
        "I build the page around the offer, who it is for, the questions buyers ask, and the action you want them to take.",
        "The page matches the offer and points interested people to one action.",
    ),
    (
        "A website move feels risky",
        "Website and app care",
        "You need to move platforms, hosts, pages, or domains without creating a mess.",
        "Migrations create risk when redirects, content, forms, tracking, email, DNS, and launch timing are treated separately.",
        "I plan the move, map dependencies, preserve the important pages, and verify the launch details.",
        "The move is calmer, cleaner, and less likely to create broken links or missed leads.",
    ),
    (
        "Key pages have accessibility barriers",
        "Website and app care",
        "Important pages or forms may be difficult for people using keyboards, screen readers, or assistive tools.",
        "Accessibility problems often hide in contrast, labels, headings, focus states, alt text, navigation, and form errors.",
        "I review the high-value pages, identify access barriers, and help prioritize fixes that make the experience more usable.",
        "More people can use the important pages, and you'll know which barriers to fix next.",
    ),
    (
        "Repair a stale blog or resources section",
        "Website and app care",
        "Your site has old articles, outdated resources, or content that no longer supports the business.",
        "Stale content can confuse visitors, weaken trust, and make it harder for search engines to understand what the site is about today.",
        "I audit the content, decide what to keep, update, redirect, consolidate, or remove, and tie the strongest pages back to service goals.",
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
        "Visitors get lost on the site",
        "Website and app care",
        "Visitors can open the site, but they cannot quickly find where to go.",
        "Menus become hard to use when pages, offers, and internal business language pile up over time.",
        "I simplify the menu, page order, labels, and buttons around the tasks visitors came to complete.",
        "People reach important pages faster instead of hunting through the site.",
    ),
    (
        "Website inquiries are stuck in inboxes or spreadsheets",
        "Website and app care",
        "Website inquiries need to land where your team can act instead of sitting in an inbox.",
        "Manual copying from forms to CRMs or spreadsheets wastes time and creates missed follow-up risk.",
        "I send the form data to the system your team already uses, with the fields and notifications they need.",
        "New inquiries are easier to track, assign, and follow up on without extra copy-paste work.",
    ),
    (
        "Give customers a cleaner way to send requests and files",
        "Website and app care",
        "Customers or clients need a cleaner place to submit requests, upload files, and see what happens next.",
        "Email-only portals create repeated clarification work because files, updates, approvals, and status details get scattered across threads.",
        "I define the portal workflow, required fields, file handling, notifications, permissions, and support plan before building the smallest working version.",
        "Customers know where to send files and requests, and your team gets everything in one place.",
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
        "Undocumented systems make every change slower and every transfer of responsibility riskier.",
        "I inventory the setup, clarify ownership, write plain notes, and identify the areas that need cleanup or support.",
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
        "I create a simple monthly rhythm for updates, review, fixes, and small improvements.",
        "Small changes get done regularly instead of waiting for the next redesign.",
    ),
    (
        "Leads need follow-up you can trust",
        "Automation",
        "New leads need timely, consistent follow-up without relying on memory.",
        "Follow-up falls apart when every inquiry requires a manual reminder, copied email, or repeated status check.",
        "I lay out each stage, write the messages, and connect the reminders or follow-up actions.",
        "Leads receive a faster response and fewer opportunities fall through the cracks.",
    ),
    (
        "Turn form submissions into tracked tasks",
        "Automation",
        "Form submissions need to become trackable work automatically.",
        "Intake loses value when every submission has to be read, copied, renamed, assigned, and remembered manually.",
        "I send each form submission to the right task list, spreadsheet, project board, or notification channel.",
        "New requests arrive as organized work instead of another loose email.",
    ),
    (
        "Send reminders before missed deadlines",
        "Automation",
        "Important deadlines rely on someone remembering to check a spreadsheet or inbox.",
        "Manual deadline tracking creates stress because problems are visible only after the date has already passed.",
        "I create reminders based on due dates, status, owner, or missing information so the right person gets an alert in time.",
        "Deadlines become easier to manage and less dependent on last-minute chasing.",
    ),
    (
        "Important numbers take too long to see",
        "Automation",
        "You need a quick view of important numbers without building reports by hand.",
        "Manual reporting wastes time and often arrives too late to guide decisions.",
        "I choose the numbers worth watching, connect the data, and build a dashboard people will use.",
        "The important numbers are available without rebuilding the report every week.",
    ),
    (
        "Proposals take too long to prepare",
        "Automation",
        "Proposals take too long because the same information is rewritten every time.",
        "Proposal work slows down when pricing, scope, client details, terms, and repeated language live in separate places.",
        "I design a repeatable input flow and generate clean proposal drafts that still leave room for human review.",
        "You produce proposals faster while keeping quality and details in your control.",
    ),
    (
        "Organize files after form submissions",
        "Automation",
        "Submitted files need to be named, stored, and connected to the right client or project.",
        "File chaos creates rework because attachments land in inboxes with inconsistent names and unclear ownership.",
        "I create a workflow that saves files into the right folders, applies clear naming, and notifies the right person.",
        "Files become easier to find and less likely to disappear in email threads.",
    ),
    (
        "Route new leads to the right person",
        "Automation",
        "New inquiries need to go to the right owner based on service, location, urgency, or account.",
        "Bad routing delays response times and creates awkward internal forwarding.",
        "I define routing rules, connect the source form or inbox, and make sure the transfer includes the details needed to respond.",
        "Leads reach the right person faster with less manual sorting.",
    ),
    (
        "Automate customer review requests",
        "Automation",
        "Happy customers should be asked for reviews at the right moment.",
        "Review requests often get skipped because they depend on someone remembering after the work is done.",
        "I create a simple trigger, message, and follow-up process that asks at a natural point in the customer journey.",
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
        "Booked calls need better confirmations, reminders, and cancellation instructions.",
        "Scheduling tools can create confusion when confirmations, prep notes, cancellations, and reminders are disconnected.",
        "I review the appointment flow and connect the messages that help people show up ready.",
        "Meetings are easier to manage and require less manual coordination.",
    ),
    (
        "CRM data is hard to trust",
        "Automation",
        "Your CRM has good information, but duplicates and messy fields make it hard to trust.",
        "A messy CRM creates problems because people stop believing the data and return to spreadsheets or memory.",
        "I review fields, duplicates, required data, lead stages, and cleanup rules before recommending a simple structure.",
        "People can find and update customer records without second-guessing the data.",
    ),
    (
        "New customer onboarding feels inconsistent",
        "Automation",
        "New customers need the same reliable path from signed agreement to the start of the work.",
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
        "I review what the spreadsheet really does and turn the important parts into a cleaner form, dashboard, or lightweight app.",
        "The work is easier to enter, harder to break, and simpler for someone else to support.",
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
        "I connect the form, database, spreadsheet, or API so the information moves in a predictable way.",
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
        "I define the simplest view people need and connect or collect the data needed to keep it current.",
        "You get one clear place to see the work without buying a huge system.",
    ),
    (
        "Turn repeated emails into templates and prompts",
        "Automation",
        "Your team writes the same explanations, replies, and follow-ups over and over.",
        "Repeated writing drains time and creates inconsistent quality across customers or projects.",
        "I identify common message types and create templates or AI-assisted prompts that still sound like you.",
        "Routine communication gets faster while still sounding personal and clear.",
    ),
    (
        "Copy-paste is slowing the work down",
        "Automation",
        "Work is slowed down by moving the same information from one system to another.",
        "A few minutes of copy-paste adds up when it happens every day and errors slip in.",
        "I map the repeated transfer, identify the safest connection point, and automate the parts that should not require judgment.",
        "The work moves with fewer manual steps and fewer avoidable mistakes.",
    ),
    (
        "Build a private internal request form",
        "Automation",
        "Your team needs a cleaner way to ask for help, changes, approvals, or resources.",
        "Ad hoc requests in chat or email are easy to lose and hard to prioritize.",
        "I create a simple internal form with the right fields, routing, notifications, and follow-up steps.",
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
        "The spreadsheet does less, breaks less often, and is easier for the team to use.",
    ),
    (
        "There are too many AI tools to choose from",
        "AI coaching and support",
        "You want to use AI, but it is hard to tell which tools are worth paying for.",
        "Choosing by popularity can leave you with an expensive tool that does not fit the job.",
        "I start with the work you want AI to do, compare the tools, and rule out anything that adds more work than it saves.",
        "You'll know which tools are worth testing and why.",
    ),
    (
        "The team needs safer rules for AI and client data",
        "AI coaching and support",
        "Your team needs AI guidance that protects customer, employee, and business information.",
        "Without agreed rules, people either avoid AI or paste sensitive information into it without understanding the risk.",
        "I help define plain-English rules, review points, approved use cases, and safer habits for everyday work.",
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
        "The team does not know where AI fits",
        "AI coaching and support",
        "Your team is curious about AI but does not know where it would save time.",
        "Generic AI training rarely sticks because it does not match the team's tools, roles, risks, or daily decisions.",
        "I teach with examples from the team's own work, including what to check and what data to keep out.",
        "People leave with concrete ways to start instead of vague excitement or fear.",
    ),
    (
        "Use AI for proposal first drafts",
        "AI coaching and support",
        "Proposal writing takes too long, but you still need accuracy and judgment.",
        "AI proposal drafts can sound generic or risky when they are not based on your real scope, customer details, and standards.",
        "I design a proposal workflow with structured inputs, reusable prompts, and human review built in.",
        "You create better first drafts faster without outsourcing the final judgment to AI.",
    ),
    (
        "Use AI to summarize meetings and calls",
        "AI coaching and support",
        "Meeting notes, follow-ups, and decisions are not getting captured consistently.",
        "AI summaries can help, but only if the workflow respects privacy, creates outputs people can trust, and lands in the right place.",
        "I help choose the capture method, output format, review step, and storage location for your meeting notes.",
        "Meetings produce clearer decisions and follow-up without adding more admin work.",
    ),
    (
        "Use AI to research before sales calls",
        "AI coaching and support",
        "You want better prep before calls without spending too much time researching manually.",
        "AI research can be shallow or inaccurate unless the sources, prompts, and review habits are designed carefully.",
        "I create a repeatable prep workflow that gathers the right background and flags what still needs human verification.",
        "You show up better prepared with less last-minute searching.",
    ),
    (
        "Support replies need to be faster without getting sloppy",
        "AI coaching and support",
        "Support responses need to be faster without becoming careless or robotic.",
        "AI can help draft replies, but weak rules can create tone problems, wrong promises, or privacy mistakes.",
        "I use real support examples to build prompts, review rules, and instructions for when a person should take over.",
        "Your team drafts replies faster without giving customers robotic or careless answers.",
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
        "You have data in spreadsheets, but turning it into answers you can act on takes too much effort.",
        "AI can help explain, clean, or analyze data, but it needs the right structure and verification habits.",
        "I help prepare the spreadsheet, define the questions, create prompts, and check the outputs for day-to-day use.",
        "Reports become easier to understand and use in decisions.",
    ),
    (
        "Procedures are hard for the team to find",
        "AI coaching and support",
        "Your team has procedures, but people still ask the same how-to questions.",
        "An AI assistant cannot answer reliably if the source material is outdated, contradictory, or incomplete.",
        "I organize the procedures, limit what the assistant can answer, and test it with questions employees really ask.",
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
        "People tried AI a few times, but it has not become a regular part of work.",
        "AI adoption fades when experiments are not tied to specific tasks, time savings, or repeatable routines.",
        "I help choose a few high-value use cases, build the prompts, document the workflow, and support the habit while it sticks.",
        "AI becomes a regular tool instead of another abandoned experiment.",
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
        "AI drafts can help, but they do not sound like your business yet.",
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
        "I identify the right tasks, build prompts, set rules, and support the person while they practice.",
        "AI becomes easier to use in the flow of that role's real work.",
    ),
    (
        "You have too many product ideas",
        "Product strategy",
        "You have too many product ideas and need to decide which one deserves attention first.",
        "It is hard to choose when every idea has a different customer benefit, cost, risk, and timeline.",
        "I help sort ideas by customer need, expected outcome, constraints, and the smallest working version.",
        "You leave with a sharper priority and less pressure to build everything at once.",
    ),
    (
        "A product idea needs a reality check",
        "Product strategy",
        "An idea sounds promising, but you need to know what could make it fail.",
        "An idea that sounds good in a brainstorm may fall apart when customers, budgets, or technical limits enter the picture.",
        "I examine the audience, problem, alternatives, adoption problems, business model, and build path.",
        "You understand the strongest case, the biggest risks, and the smartest next test.",
    ),
    (
        "Turn customer complaints into priorities",
        "Product strategy",
        "Customers are giving feedback, but it is hard to translate complaints into action.",
        "Complaints can lead to scattered fixes when no one separates symptoms from root causes.",
        "I group the feedback, identify repeated needs and pain points, and connect them to product or workflow priorities.",
        "The feedback becomes a decision tool instead of a pile of frustration.",
    ),
    (
        "Understand the customer need before building",
        "Product strategy",
        "You need to understand what customers are trying to accomplish before choosing features.",
        "Building around features too early can miss the actual need, constraints, and success criteria.",
        "I help map the customer situation, progress they want, alternatives they use, and signals that the solution is working.",
        "You get a clearer product direction before spending money on development.",
    ),
    (
        "A build-vs-buy decision is unclear",
        "Product strategy",
        "You are deciding whether to buy software, customize a tool, or build something new.",
        "Build-vs-buy decisions get expensive when hidden costs, workflow fit, data ownership, and support needs are ignored.",
        "I compare the options using the way people will use them, integrations, budget, data ownership, and maintenance.",
        "You can choose the path that solves the problem without creating unnecessary future burden.",
    ),
    (
        "A software acquisition needs product due diligence",
        "Product strategy",
        "You are buying, selling, investing in, or merging a software product and need to understand the technology risk.",
        "Product and M&A decisions get risky when product health, technical debt, roadmap reality, integrations, team dependencies, support burden, and customer migration issues are not understood.",
        "I review the product, user experience, technology, integrations, data, operations, support burden, and team dependencies to find risks and unanswered questions.",
        "You'll know what looks solid, where more investigation is needed, and which questions to ask before the deal moves ahead.",
    ),
    (
        "MVP scope is starting to sprawl",
        "Product strategy",
        "You want to launch something that works without turning it into a giant project.",
        "MVPs often become bloated because every edge case, future feature, and internal preference gets included too soon.",
        "I help define the smallest working version, what to delay, what to measure, and what must be true for launch.",
        "You'll have a smaller launch plan and a faster way to learn from customers.",
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
        "Simplify the process before you buy or build software",
        "Product strategy",
        "A workflow feels broken, but software may not be the first fix.",
        "Automating a confusing process can make the confusion faster instead of better.",
        "I map the current process, identify decisions, handoffs, waste, and unclear ownership before recommending tools.",
        "You improve the process before spending money on software.",
    ),
    (
        "The vendor or developer request is too vague",
        "Product strategy",
        "You need outside help, but the request is too vague for a reliable estimate.",
        "Vague requirements create mismatched estimates, scope creep, and handoffs where the vendor has to guess.",
        "I turn the business need into goals, user flows, constraints, requirements, open questions, and acceptance criteria.",
        "Vendors can respond more accurately and you can evaluate proposals with more confidence.",
    ),
    (
        "A vendor proposal is hard to evaluate",
        "Product strategy",
        "A software, website, or automation proposal looks expensive or unclear.",
        "Proposals can hide assumptions, leave out support, or include work that does not solve the problem.",
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
        "Your offers are strong, but the way they are packaged may be hard to understand.",
        "Pricing confusion can come from too many options, unclear outcomes, weak boundaries, or service language that reflects the business more than the buyer.",
        "I help simplify the packages, buyer logic, tradeoffs, and page language.",
        "Customers can compare options more easily and you can sell with more confidence.",
    ),
    (
        "Create a product roadmap for a small team",
        "Product strategy",
        "The team needs a roadmap that is realistic, focused, and not overloaded.",
        "Roadmaps become wish lists when priorities are not tied to customer value, team capacity, and business goals.",
        "I help shape a roadmap around outcomes, constraints, sequencing, risk, and what should wait.",
        "The team gets a clearer plan that supports decisions instead of creating pressure.",
    ),
    (
        "A project has stalled",
        "Product strategy",
        "A website, app, automation, or product effort started but lost momentum.",
        "Projects stall when ownership, scope, decisions, vendors, dependencies, or next steps become unclear.",
        "I review what exists, identify the blocker, simplify the path, and help define the next concrete move.",
        "The team knows what is blocking the project and what to do about it.",
    ),
    (
        "Turn a rough idea into a clickable prototype",
        "Product strategy",
        "You need people to understand an idea before committing to a build.",
        "Words alone can hide assumptions about flow, screens, data, and user decisions.",
        "I turn the idea into a lightweight prototype or flow that makes the concept easier to discuss and test.",
        "You can get feedback, align the right people, and reduce risk before development.",
    ),
    (
        "Prospects need quicker quote or fit answers",
        "Website and app care",
        "Customers wait too long to learn the likely cost, fit, or options.",
        "Quote requests get slow when every estimate starts with back-and-forth emails, missing details, and manual calculations.",
        "I define the questions, rules, outputs, follow-up steps, and review points, then build a sales tool that helps without overpromising.",
        "Customers get a faster answer, and your team receives the information needed for follow-up.",
    ),
    (
        "Website visitors need quick answers",
        "AI coaching and support",
        "Visitors need quick answers on your website without forcing every question into a manual email or phone call.",
        "AI support agents become risky when they are trained on weak content, answer beyond what they should know, or create promises the business cannot keep.",
        "I define the support questions, prepare the source content, set rules, build the agent flow, and create a review process for quality and escalation.",
        "Visitors get faster answers while your business keeps control of accuracy, tone, privacy, and follow-up.",
    ),
    (
        "Build a personal task and reminder system",
        "Small business setup and operations",
        "Tasks keep slipping because reminders are spread across too many apps or habits.",
        "A task system fails when it is too complex, too easy to ignore, or disconnected from real routines.",
        "I help choose a simple structure, capture method, reminder rhythm, and review habit.",
        "You get a system that supports follow-through instead of becoming another thing to manage.",
    ),
    (
        "Automate personal paperwork and forms",
        "Small business setup and operations",
        "Repeated personal paperwork takes more time than it should.",
        "Forms, applications, PDFs, and repeated information become frustrating when every request starts from scratch.",
        "I help create templates, organized source information, and AI-assisted drafts where appropriate.",
        "Recurring paperwork becomes faster, clearer, and less mentally draining.",
    ),
    (
        "Create a simple budget or planning spreadsheet",
        "Small business setup and operations",
        "You need a simple spreadsheet, not a complicated financial system.",
        "Planning gets harder when the spreadsheet is overbuilt, unclear, or disconnected from how you make decisions.",
        "I help design a simple sheet around the few categories, questions, and review habits that matter.",
        "You get a planning tool you can actually keep using.",
    ),
    (
        "The business needs a better website",
        "Website and app care",
        "Your website should explain the offer and turn visitors into inquiries.",
        "A weak or outdated site makes people work too hard to understand what you do, why they should trust you, and how to contact you.",
        "I write the message, plan the pages, build the site, connect the contact form, and make sure you can update it.",
        "You'll have a website that explains the business, is easy to update, and supports sales conversations.",
    ),
    (
        "Operations are scattered across too many places",
        "Automation",
        "Your team needs one place to manage records, requests, statuses, approvals, or daily operations.",
        "Internal work gets messy when important details live across spreadsheets, inboxes, chat threads, and memory.",
        "I lay out the records, roles, screens, and approvals, then build a small internal tool around the way your team works.",
        "The team manages the work in one system instead of chasing details across inboxes and spreadsheets.",
    ),
    (
        "Inbox and calendar are overloaded",
        "Small business setup and operations",
        "Your inbox and calendar are carrying too much of your life or work.",
        "Overload grows when messages, appointments, reminders, and decisions all compete in the same places.",
        "I help define filters, routines, reminders, labels, scheduling habits, and AI-assisted summaries where they help.",
        "Email and calendar become easier to review and less likely to hide important commitments.",
    ),
    (
        "Customer details are disconnected from the CRM",
        "Automation",
        "Your leads, customers, forms, and follow-up need to connect to the CRM instead of living in separate places.",
        "CRM value disappears when people still copy information by hand, miss required fields, or cannot trust where customer details land.",
        "I follow a lead from the form into the CRM, fix the transfer, and make sure the record includes what your team needs for follow-up.",
        "Customer details land in the CRM and are ready for follow-up without extra copy-paste.",
    ),
    (
        "Use AI for writing and research without feeling stuck",
        "Small business setup and operations",
        "You want AI help for writing, research, or decisions, but do not know how to start.",
        "AI can feel overwhelming when the first prompt is unclear and the output needs too much cleanup.",
        "I coach you through prompts, source checking, revision habits, and ways to keep your voice intact.",
        "AI becomes a helpful thinking partner instead of a confusing blank box.",
    ),
    (
        "Set up the basics for a new small business",
        "Small business setup and operations",
        "You need the basics in place: domain, email, site, forms, scheduling, payments, and simple records.",
        "Starting from scratch is hard because every tool choice affects future work and support.",
        "I help choose the simplest workable stack, connect the pieces, and document how it fits together.",
        "Your domain, email, website, scheduling, payments, and records work together without extra software.",
    ),
    (
        "Build a mobile app for a specific workflow",
        "Website and app care",
        "A customer, employee, or field task would work better in a mobile app.",
        "App projects get expensive when the users, must-have features, data, and support plan are vague.",
        "I define the users and core tasks, choose how to build it, and plan the launch and support.",
        "You'll have an app plan based on the work people need to do—not a long feature wish list.",
    ),
    (
        "You need a simple website or portfolio",
        "Small business setup and operations",
        "You need one clean place to explain who you are, what you do, and how people can contact you.",
        "Scattered profiles and links make it hard for people to understand your work, trust your experience, or contact you.",
        "I decide what the page needs to say and show, then build the simplest version that does the job.",
        "You'll have one professional page to share with clients, employers, or collaborators.",
    ),
    (
        "Prepare a solo business for its first website",
        "Small business setup and operations",
        "You need a first website, but you are not sure what it should say or include.",
        "First websites stall when offers, audience, trust points, tools, and next steps are still fuzzy.",
        "I help clarify the message, page structure, must-have tools, and simplest way to launch.",
        "You get a website plan that can be built without overcomplicating the business.",
    ),
    (
        "Client onboarding feels awkward or inconsistent",
        "Small business setup and operations",
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
    "One offer needs its own page",
    "A website move feels risky",
    "Key pages have accessibility barriers",
    "Visitors are seeing security warnings",
    "Visitors get lost on the site",
    "Website inquiries are stuck in inboxes or spreadsheets",
    "Give customers a cleaner way to send requests and files",
    "Website updates keep getting postponed",
    "Prospects need quicker quote or fit answers",
    "The business needs a better website",
    "Build a mobile app for a specific workflow",
    "Leads need follow-up you can trust",
    "Turn form submissions into tracked tasks",
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
    "There are too many AI tools to choose from",
    "The team needs safer rules for AI and client data",
    "AI prompts are inconsistent across daily work",
    "The team does not know where AI fits",
    "Support replies need to be faster without getting sloppy",
    "Procedures are hard for the team to find",
    "Website visitors need quick answers",
    "You have too many product ideas",
    "A product idea needs a reality check",
    "A build-vs-buy decision is unclear",
    "A software acquisition needs product due diligence",
    "MVP scope is starting to sprawl",
    "Simplify the process before you buy or build software",
    "The vendor or developer request is too vague",
    "A vendor proposal is hard to evaluate",
    "A project has stalled",
    "Inbox and calendar are overloaded",
    "Set up the basics for a new small business",
    "You need a simple website or portfolio",
    "Client onboarding feels awkward or inconsistent",
}


SERVICE_SLUG_OVERRIDES = {
    "Contact form submissions are not arriving": "fix-a-broken-contact-form",
    "The website feels slow": "make-a-slow-website-feel-fast",
    "WordPress warnings are piling up": "clean-up-wordpress-plugin-warnings",
    "Website leads are going missing": "stop-website-leads-from-going-missing",
    "The mobile website is confusing": "improve-a-confusing-mobile-website",
    "The homepage no longer matches the business": "refresh-an-outdated-homepage",
    "One offer needs its own page": "create-a-landing-page-for-one-offer",
    "A website move feels risky": "migrate-a-website-without-losing-momentum",
    "Key pages have accessibility barriers": "fix-accessibility-blockers-on-key-pages",
    "Visitors are seeing security warnings": "fix-ssl-and-website-security-warnings",
    "Visitors get lost on the site": "improve-website-navigation",
    "Website inquiries are stuck in inboxes or spreadsheets": "connect-website-forms-to-your-crm-or-spreadsheet",
    "Give customers a cleaner way to send requests and files": "build-a-customer-portal-for-requests-and-files",
    "Website updates keep getting postponed": "keep-monthly-website-updates-moving",
    "Prospects need quicker quote or fit answers": "build-an-online-quote-or-estimate-tool",
    "The business needs a better website": "build-a-new-website-for-your-business",
    "Build a mobile app for a specific workflow": "build-a-mobile-app-for-your-business",
    "Leads need follow-up you can trust": "automate-lead-follow-up",
    "Turn form submissions into tracked tasks": "turn-intake-forms-into-organized-tasks",
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
    "There are too many AI tools to choose from": "choose-ai-tools-for-your-business",
    "The team needs safer rules for AI and client data": "create-safe-ai-rules-for-client-data",
    "AI prompts are inconsistent across daily work": "build-a-prompt-library-for-daily-work",
    "The team does not know where AI fits": "train-your-team-to-use-ai-confidently",
    "Support replies need to be faster without getting sloppy": "use-ai-to-improve-customer-support-replies",
    "Procedures are hard for the team to find": "create-a-custom-ai-assistant-for-procedures",
    "Website visitors need quick answers": "build-an-ai-powered-website-support-agent",
    "You have too many product ideas": "decide-what-to-build-first",
    "A product idea needs a reality check": "pressure-test-a-new-product-idea",
    "A build-vs-buy decision is unclear": "choose-build-vs-buy-for-a-tool",
    "A software acquisition needs product due diligence": "product-due-diligence-before-an-acquisition",
    "MVP scope is starting to sprawl": "define-an-mvp-without-overbuilding",
    "Simplify the process before you buy or build software": "simplify-a-confusing-workflow-before-software",
    "The vendor or developer request is too vague": "create-requirements-for-a-developer-or-vendor",
    "A vendor proposal is hard to evaluate": "review-a-vendor-proposal-before-signing",
    "A project has stalled": "recover-a-project-that-stalled",
    "Inbox and calendar are overloaded": "simplify-email-and-calendar-overload",
    "Set up the basics for a new small business": "set-up-a-small-business-tech-stack-from-scratch",
    "You need a simple website or portfolio": "create-a-simple-personal-website-or-portfolio",
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
        "Open the page and use it the way a customer would.",
        "Check the form, mobile layout, speed, hosting, redirects, and follow-up emails.",
        "Separate the urgent repair from anything that can wait.",
    ],
    "Automation": [
        "Walk through the task from start to finish.",
        "Find every copy-paste step, reminder, and handoff.",
        "Keep human decisions human and automate the repeatable parts.",
    ],
    "AI coaching and support": [
        "Start with the job you want AI to help with—not the latest tool.",
        "Set rules for privacy, review, tone, and accuracy.",
        "Test the setup with the people who will use it.",
    ],
    "Product strategy": [
        "Get specific about the customer, the problem, and the decision.",
        "Compare value, cost, risk, effort, and timing.",
        "Choose something small to test before committing to a big build.",
    ],
    "Small business setup and operations": [
        "Walk through how the work gets done today.",
        "Remove tools and steps that add work without helping.",
        "Set up something simple enough to keep using.",
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
        "the page URLs, screenshots from phone and desktop, the action visitors should take, examples of confusing copy or layout, and any search or analytics details you already have",
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
        ("acquisition", "m&a", "due diligence", "diligence", "investing", "merging"),
        "the product or company being evaluated, deal stage, business goals, available product docs, technical docs, roadmap, known risks, customer migration concerns, vendor notes, and questions you need answered before moving forward",
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
    "Website and app care": "This can be a one-time repair, or I can keep an eye on updates, hosting, forms, analytics, and other ongoing work.",
    "Automation": "This can be a one-time setup. I can also stay involved when the process or the tools change.",
    "AI coaching and support": "One session may be enough for a narrow question. Teams often want more help while they test tools and build new habits.",
    "Product strategy": "Some questions take one working session. Others need help through testing, vendor conversations, or the first build.",
    "Small business setup and operations": "This can be a one-time setup, or I can help adjust it as you learn what works.",
}


CATEGORY_AGENCY_CONTEXT = {
    "Website and app care": "Website and app issues often cross content, hosting, UX, forms, email, search, and operations. Audo brings senior product, engineering, and agency delivery experience without making you repeat the story to multiple people.",
    "Automation": "Automation work needs someone who understands the actual workflow, not just the tool connection. Audo brings senior product and engineering judgment to shape, build, explain, and support the process directly.",
    "AI coaching and support": "AI work needs judgment, privacy awareness, examples, training, and follow-through. Audo brings broad technology and product experience while keeping the coaching close to the real work people do every day.",
    "Product strategy": "Product work gets better when strategy and execution stay connected. Audo brings product and engineering leadership experience, so the recommendation is based on what it would take to actually build or support it.",
    "Small business setup and operations": "Small-business systems depend on the details: people, habits, tools, customers, and timing. Audo brings senior technology experience without turning the work into a large process.",
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


EXPLORER_GROUP_LABELS = {
    "website": "My website",
    "customers": "My customers",
    "work": "How we work",
    "ai": "Using AI",
    "decisions": "I need help deciding",
}


EXPLORER_SERVICES = [
    (
        "Contact form submissions are not arriving",
        "website",
        "My website form isn't sending me messages",
        "People fill out my contact form, but I don't receive their message.",
        "I receive every message in the right place and know the form is working.",
    ),
    (
        "The website feels slow",
        "website",
        "My website takes too long to load",
        "Customers wait for pages to open, especially on their phones.",
        "My pages open faster and customers can get where they need to go.",
    ),
    (
        "WordPress warnings are piling up",
        "website",
        "My WordPress site keeps showing warnings",
        "I see update and plugin notices, but I'm worried that changing something will break the site.",
        "The warnings are handled safely and I know what needs regular attention.",
    ),
    (
        "The mobile website is confusing",
        "website",
        "My website is hard to use on a phone",
        "Customers have trouble using the menu, reading pages, or filling out forms on their phones.",
        "Customers can use the site and take the next step easily from a phone.",
    ),
    (
        "The homepage no longer matches the business",
        "website",
        "My website no longer describes my business",
        "What I offer has changed, but the homepage still tells the old story.",
        "The homepage clearly explains what I do now and how customers can get started.",
    ),
    (
        "The business needs a better website",
        "website",
        "My business has outgrown its website",
        "The site feels outdated and no longer gives customers confidence in the business.",
        "I have a professional site that explains the business and supports sales.",
    ),
    (
        "Leads need follow-up you can trust",
        "customers",
        "I need a better way to follow up with new leads",
        "Follow-up depends on someone seeing an email and remembering what to do next.",
        "New leads get a timely response and fewer opportunities are forgotten.",
    ),
    (
        "Appointment confirmations are confusing",
        "customers",
        "My appointment messages confuse customers",
        "Customers are not sure when to arrive, where to go, or how to reschedule.",
        "Customers get clear appointment details and I spend less time answering the same questions.",
    ),
    (
        "New customer onboarding feels inconsistent",
        "customers",
        "Every new customer gets a different start",
        "Forms, emails, payments, and first steps are handled differently each time.",
        "Every customer gets the same clear welcome and knows what happens next.",
    ),
    (
        "Prospects need quicker quote or fit answers",
        "customers",
        "Customers wait too long for a quote or answer",
        "People have to call or wait for me to learn the price, availability, or whether I can help.",
        "Customers get a useful answer sooner and I spend less time on repeated questions.",
    ),
    (
        "Give customers a cleaner way to send requests and files",
        "customers",
        "Customer requests and files are scattered everywhere",
        "Questions, documents, approvals, and updates arrive by email, text, and other places.",
        "Customers have one clear place to send what I need and check what happens next.",
    ),
    (
        "Customer details are disconnected from the CRM",
        "customers",
        "I can't see the whole customer story in one place",
        "Customer details are split between forms, email, spreadsheets, and different apps.",
        "I can see the information I need without hunting through several places.",
    ),
    (
        "Turn form submissions into tracked tasks",
        "work",
        "I have to turn every form into a task by hand",
        "Someone reads every form, copies the details, assigns the work, and remembers the next step.",
        "Each request becomes clear, assigned work without all the copying and reminders.",
    ),
    (
        "Important numbers take too long to see",
        "work",
        "It takes too long to see how the business is doing",
        "I have to rebuild the same report before I can understand what is happening.",
        "I can see the few numbers that matter without rebuilding a report every week.",
    ),
    (
        "Proposals take too long to prepare",
        "work",
        "I rewrite the same proposal every time",
        "Services, prices, terms, and customer details are copied into each new proposal.",
        "I can prepare a good proposal faster and still review it before it goes out.",
    ),
    (
        "CRM data is hard to trust",
        "work",
        "I can't trust my customer list",
        "Names are duplicated, details are missing, and no one knows which information is current.",
        "My customer list is cleaner, easier to use, and more reliable.",
    ),
    (
        "A spreadsheet is carrying too much responsibility",
        "work",
        "One spreadsheet is running too much of the business",
        "The file is important, but it is fragile, slow, and difficult for everyone to use.",
        "The work is easier to manage and no longer depends on one complicated spreadsheet.",
    ),
    (
        "Copy-paste is slowing the work down",
        "work",
        "We copy the same information from one app to another",
        "Names, dates, files, and updates are entered more than once in different places.",
        "Information moves where it needs to go with less typing and fewer mistakes.",
    ),
    (
        "There are too many AI tools to choose from",
        "ai",
        "I don't know which AI tools are worth using",
        "Every tool promises something different, and I don't want to waste money or time.",
        "I know which tools are worth trying and what I would actually use them for.",
    ),
    (
        "The team needs safer rules for AI and client data",
        "ai",
        "My team needs simple rules for using AI safely",
        "People are experimenting, but no one knows what customer or business information is safe to share.",
        "My team has clear rules and knows when a person needs to check the answer.",
    ),
    (
        "The team does not know where AI fits",
        "ai",
        "I don't know where AI would actually help my business",
        "AI sounds useful, but I can't connect it to the work my team does every day.",
        "I have a short list of practical uses that could genuinely save time.",
    ),
    (
        "Support replies need to be faster without getting sloppy",
        "ai",
        "Writing customer replies takes too long",
        "My team answers similar questions again and again, but every response still needs to sound human.",
        "We can write replies faster while keeping them accurate and personal.",
    ),
    (
        "Procedures are hard for the team to find",
        "ai",
        "My team can't find the instructions they need",
        "Instructions exist, but they are spread across documents, folders, and old conversations.",
        "People can find a clear answer without asking someone to search for it.",
    ),
    (
        "Website visitors need quick answers",
        "ai",
        "Customers keep asking the same questions",
        "Simple questions become phone calls or emails because the answers are hard to find on the website.",
        "Customers get quick answers and know when they need to contact a person.",
    ),
    (
        "Set up the basics for a new small business",
        "decisions",
        "My new business needs help with technology",
        "I need help setting up email, a website, booking, payments, and a simple way to keep records.",
        "The basics are set up, work together, and are easy for me to manage.",
    ),
    (
        "A build-vs-buy decision is unclear",
        "decisions",
        "I don't know whether to buy software or have something built",
        "The tools I found don't quite fit, but I don't know if building my own would be worth it.",
        "I understand the choices, likely costs, and simplest next step.",
    ),
    (
        "Simplify the process before you buy or build software",
        "decisions",
        "I think the way we work is the real problem",
        "Adding another app may not help if the current steps are confusing or unnecessary.",
        "The work is simpler before I spend money on new software.",
    ),
    (
        "A vendor proposal is hard to evaluate",
        "decisions",
        "I don't know if this proposal is a good deal",
        "A company gave me a price and plan, but I can't tell what is included or whether it will solve the problem.",
        "I know what the proposal includes, what is missing, and what to ask before I agree.",
    ),
    (
        "A project has stalled",
        "decisions",
        "My website or software project has stalled",
        "The work started, but decisions, problems, or unclear responsibilities have stopped progress.",
        "I know what is blocking the work and what needs to happen next.",
    ),
    (
        "You have too many product ideas",
        "decisions",
        "I have too many technology problems to tackle",
        "Several things need attention, and I don't know what to fix first.",
        "I have a clear, practical order for what to handle now and what can wait.",
    ),
]


def _explorer_detail(
    problem_heading: str,
    goal_heading: str,
    approach_heading: str,
    form_heading: str,
    form_prompt: str,
    faq_heading: str,
    steps: tuple[str, str, str],
    faq_questions: tuple[str, str, str],
) -> dict[str, object]:
    return {
        "problem_heading": problem_heading,
        "goal_heading": goal_heading,
        "approach_heading": approach_heading,
        "form_heading": form_heading,
        "form_prompt": form_prompt,
        "faq_heading": faq_heading,
        "steps": steps,
        "faq_questions": faq_questions,
    }


EXPLORER_DETAIL_COPY = {
    "Contact form submissions are not arriving": _explorer_detail(
        "The form looks fine, but the messages disappear.",
        "Every inquiry reaches you.",
        "Trace the message from the page to your inbox.",
        "Show me where the messages should go.",
        "Send the form page and tell me which inbox should receive each message.",
        "Questions about missing form messages.",
        ("Submit a real test message.", "Check notifications, spam filters, and routing.", "Confirm the fix from the customer's side."),
        ("Why can a form say it worked when no message arrives?", "Can you fix this without rebuilding my website?", "How will I know the form keeps working?"),
    ),
    "The website feels slow": _explorer_detail(
        "Customers are waiting on the page.",
        "Pages open quickly on phones and computers.",
        "Find the few things causing most of the delay.",
        "Show me which pages feel slow.",
        "Send the slowest page and tell me where customers usually notice the delay.",
        "Questions about a slow website.",
        ("Time the pages customers use most.", "Fix the largest speed problems first.", "Recheck the site on phones and slower connections."),
        ("What usually makes a small-business website slow?", "Will the site need to be rebuilt to make it faster?", "How much faster can the important pages become?"),
    ),
    "WordPress warnings are piling up": _explorer_detail(
        "The warnings keep growing because no one knows what is safe.",
        "A clean dashboard and a safe update routine.",
        "Check backups and dependencies before changing anything.",
        "Show me the WordPress warnings you see.",
        "Tell me which notices worry you and when the site was last safely updated.",
        "Questions about WordPress warnings and updates.",
        ("Review the theme, plugins, and backups.", "Separate safe updates from risky changes.", "Leave a simple routine for future maintenance."),
        ("Which WordPress warnings actually need attention?", "Could an update break the live website?", "Can you leave WordPress easier for me to maintain?"),
    ),
    "The mobile website is confusing": _explorer_detail(
        "The website works, but not comfortably on a phone.",
        "Customers can read, tap, and finish the next step.",
        "Use the site like a customer and fix the frustrating parts.",
        "Show me where phone users get stuck.",
        "Send the page and describe what a customer should be able to do from a phone.",
        "Questions about improving the mobile website.",
        ("Try the main customer task on a phone.", "Fix navigation, forms, and hard-to-tap controls.", "Test the finished path on common screen sizes."),
        ("Why does the site look fine on a computer but fail on phones?", "Which mobile problems should be fixed first?", "Can the mobile experience improve without replacing the whole site?"),
    ),
    "The homepage no longer matches the business": _explorer_detail(
        "Your homepage is telling an older version of the business.",
        "Visitors understand what you do now.",
        "Rebuild the message around the questions customers ask first.",
        "Tell me what changed in the business.",
        "Share the current homepage and what you want customers to understand now.",
        "Questions about updating an outdated homepage.",
        ("Identify what the homepage says today.", "Clarify the current offer and best next action.", "Reshape the page around the new message."),
        ("How do I know which homepage message is confusing people?", "Will this require rewriting the entire website?", "What should visitors understand before they scroll?"),
    ),
    "The business needs a better website": _explorer_detail(
        "The current site no longer earns confidence.",
        "A professional site for the business you have now.",
        "Keep what works and replace what is holding the site back.",
        "Tell me what the current website is missing.",
        "Share the site and the impression you want it to give a new customer.",
        "Questions about replacing an outdated website.",
        ("Review the pages customers rely on.", "Decide what can stay and what needs replacing.", "Build the smallest site that supports the business well."),
        ("How can I tell whether the site needs a refresh or a rebuild?", "What should a better small-business website include?", "Can the new site be easier for me to update?"),
    ),
    "Leads need follow-up you can trust": _explorer_detail(
        "Good leads depend on someone remembering to follow up.",
        "Every new lead gets a timely next step.",
        "Connect each inquiry to a dependable follow-up routine.",
        "Show me what happens after a new lead arrives.",
        "Tell me where leads come from and who should respond to them.",
        "Questions about dependable lead follow-up.",
        ("Follow one lead from arrival to response.", "Set the owner, timing, and message for each next step.", "Make missed follow-up visible before the lead goes cold."),
        ("Where do small businesses usually lose new leads?", "Can follow-up improve without adding a complicated sales system?", "How will my team know who needs a response?"),
    ),
    "Appointment confirmations are confusing": _explorer_detail(
        "Customers are unsure what happens after they book.",
        "Clear confirmations with the right details.",
        "Simplify every message from confirmation through reminder.",
        "Show me the messages customers receive.",
        "Send a confirmation or reminder that has caused confusion.",
        "Questions about clearer appointment messages.",
        ("Book a test appointment as a customer.", "Fix missing times, locations, and rescheduling instructions.", "Confirm that reminders arrive when they are useful."),
        ("What information belongs in an appointment confirmation?", "Can confirmations and reminders come from the same booking flow?", "How can customers reschedule without calling us?"),
    ),
    "New customer onboarding feels inconsistent": _explorer_detail(
        "Each customer gets a different welcome.",
        "A clear, repeatable start for every customer.",
        "Put forms, payment, files, and next steps in a sensible order.",
        "Walk me through a new customer's first week.",
        "Tell me what every customer needs to receive, send, sign, or pay for.",
        "Questions about consistent customer onboarding.",
        ("List every step after a customer says yes.", "Put the steps in the right order with clear owners.", "Create one welcome path the team can repeat."),
        ("What should happen immediately after a customer signs up?", "How much of onboarding should be automatic?", "Can customers see what they still need to complete?"),
    ),
    "Prospects need quicker quote or fit answers": _explorer_detail(
        "Potential customers wait too long for basic answers.",
        "A faster path to price, availability, and fit.",
        "Turn repeated quote questions into a guided response.",
        "Show me how you answer quote requests today.",
        "Tell me what you must know before giving someone a useful answer.",
        "Questions about faster quotes and fit answers.",
        ("Collect the few details that change the answer.", "Create a clear price, range, or next-step response.", "Route unusual requests to a person quickly."),
        ("Can customers get an answer without seeing a fixed price?", "What information should a quote form ask for?", "How do we keep quick answers accurate?"),
    ),
    "Give customers a cleaner way to send requests and files": _explorer_detail(
        "Files and requests are hiding in too many places.",
        "One clear place for customers to send what you need.",
        "Create a simple request path that keeps updates together.",
        "Show me how requests and files arrive now.",
        "Tell me what customers send, how often, and who needs to act on it.",
        "Questions about customer requests and file sharing.",
        ("Gather the common request and file types.", "Create one clear submission path with the right fields.", "Notify the right person and keep the request easy to find."),
        ("Should customers use a portal instead of email?", "How can customers send files safely?", "Will customers be able to tell what happens next?"),
    ),
    "Customer details are disconnected from the CRM": _explorer_detail(
        "No single place shows what happened with a customer.",
        "The full customer story is easy to find.",
        "Connect the details your team already collects.",
        "Show me where customer information lives.",
        "Tell me which details your team has to search for most often.",
        "Questions about bringing customer details together.",
        ("Map where each important customer detail starts.", "Choose one dependable place for the current record.", "Connect forms and updates without creating duplicates."),
        ("Do we need to replace our current customer system?", "Which customer details should be kept in one place?", "How do we prevent duplicates after everything is connected?"),
    ),
    "Turn form submissions into tracked tasks": _explorer_detail(
        "Every request creates another round of copying and reminders.",
        "New requests become assigned work automatically.",
        "Connect the form to the way your team handles work.",
        "Show me what happens after someone submits the form.",
        "Send the form and describe the task that should be created from it.",
        "Questions about turning forms into assigned work.",
        ("Match form answers to the task details your team needs.", "Assign each request using simple business rules.", "Confirm the task and notification arrive together."),
        ("Can a form create work in the tool we already use?", "How will the right person be assigned?", "What happens when a submission is incomplete?"),
    ),
    "Important numbers take too long to see": _explorer_detail(
        "You rebuild the report before you can read the business.",
        "The important numbers are ready when you need them.",
        "Choose the few numbers that matter and gather them automatically.",
        "Show me the report you keep rebuilding.",
        "Tell me which numbers drive a decision and where they come from.",
        "Questions about simpler business reporting.",
        ("Agree on the small set of useful numbers.", "Connect each number to a dependable source.", "Present the result in a view you will actually check."),
        ("Which numbers belong on a small-business dashboard?", "Can the report update without manual spreadsheets?", "How will we know if a number is wrong?"),
    ),
    "Proposals take too long to prepare": _explorer_detail(
        "Each proposal starts from the same blank page.",
        "A polished proposal without repetitive rewriting.",
        "Turn standard services, pricing, and terms into reusable parts.",
        "Show me how you build a proposal now.",
        "Send a recent proposal and point out what changes from customer to customer.",
        "Questions about preparing proposals faster.",
        ("Separate standard content from customer-specific details.", "Create reusable choices for services, pricing, and terms.", "Keep a final human review before anything is sent."),
        ("Can proposals stay personal if parts are reused?", "Where should pricing and terms come from?", "Will I still approve every proposal before it goes out?"),
    ),
    "CRM data is hard to trust": _explorer_detail(
        "Duplicate and missing details make the customer list unreliable.",
        "One clean list your team can trust.",
        "Agree on the right fields, remove duplicates, and set simple rules.",
        "Show me where the customer list breaks down.",
        "Tell me which missing or duplicated details cause the most trouble.",
        "Questions about cleaning up customer records.",
        ("Find duplicate, incomplete, and conflicting records.", "Decide which fields the business truly needs.", "Add simple rules that keep new records cleaner."),
        ("How do you decide which duplicate customer record is correct?", "Can we clean the list without losing history?", "How do we stop the same problems from returning?"),
    ),
    "A spreadsheet is carrying too much responsibility": _explorer_detail(
        "One fragile file is carrying critical work.",
        "A simpler system that does not depend on one spreadsheet.",
        "Keep the useful logic and replace the parts that cause mistakes.",
        "Show me the spreadsheet everyone depends on.",
        "Tell me what the file controls and what goes wrong most often.",
        "Questions about replacing a business-critical spreadsheet.",
        ("Understand the decisions and calculations inside the file.", "Separate useful rules from fragile manual steps.", "Move the work into a simple shared tool."),
        ("Does every spreadsheet need to become custom software?", "Can the existing data be carried into the new setup?", "Will the replacement be easier for the team to use?"),
    ),
    "Copy-paste is slowing the work down": _explorer_detail(
        "The same details are typed again and again.",
        "Information moves between your apps with less effort.",
        "Connect only the repeatable handoffs worth automating.",
        "Show me what your team keeps copying.",
        "Tell me where the information starts and where it has to end up.",
        "Questions about reducing copy-and-paste work.",
        ("Watch one complete copy-and-paste task.", "Match the fields between the two places.", "Add checks so missing information does not disappear."),
        ("Which copy-and-paste tasks are worth automating?", "Can the apps we already use share information?", "What happens when the information does not match?"),
    ),
    "There are too many AI tools to choose from": _explorer_detail(
        "Every AI tool sounds useful until you have to choose one.",
        "A short list of tools tied to real work.",
        "Start with the jobs you want help with, then test small options.",
        "Tell me what you hope AI will help you do.",
        "List the work you want to make faster before we compare any tools.",
        "Questions about choosing useful AI tools.",
        ("Name the specific work that takes too much time.", "Compare a few tools using the same real task.", "Keep only the option that earns its cost and effort."),
        ("How can I compare AI tools that promise the same thing?", "Should we pay for a tool before the team tests it?", "How will we know whether an AI tool is actually saving time?"),
    ),
    "The team needs safer rules for AI and client data": _explorer_detail(
        "People are using AI without shared boundaries.",
        "Clear rules that protect customer and business information.",
        "Decide what is safe, what needs review, and what stays off limits.",
        "Tell me how your team is using AI today.",
        "Share the tools people use and the kinds of information they work with.",
        "Questions about safer AI use at work.",
        ("List the AI uses already happening on the team.", "Classify information that can and cannot be shared.", "Write simple review rules people can follow."),
        ("What information should never be pasted into an AI tool?", "Do different AI tools need different rules?", "How do we make the rules useful instead of intimidating?"),
    ),
    "The team does not know where AI fits": _explorer_detail(
        "AI sounds promising, but it is not connected to daily work.",
        "A few practical uses that genuinely save time.",
        "Look for repeated writing, searching, sorting, and summarizing.",
        "Show me the work your team repeats.",
        "Describe the tasks people postpone, repeat, or spend too long finishing.",
        "Questions about finding practical uses for AI.",
        ("List the repetitive work people do each week.", "Test AI on one low-risk task with a clear answer.", "Keep the uses that help and drop the ones that do not."),
        ("Which small-business tasks are good first uses for AI?", "What work should AI not handle?", "How much time should a useful AI test actually save?"),
    ),
    "Support replies need to be faster without getting sloppy": _explorer_detail(
        "Helpful replies take too long to write.",
        "Faster answers that still sound like your business.",
        "Use approved information to draft replies for a person to review.",
        "Show me the questions your team answers repeatedly.",
        "Share a few real questions and examples of replies that sound right.",
        "Questions about using AI for customer replies.",
        ("Collect the questions customers ask most often.", "Give AI approved facts, policies, and tone examples.", "Require a person to review every reply before sending."),
        ("Will AI replies sound generic or impersonal?", "How do we keep an AI-written answer accurate?", "Can the team stay in control of every message?"),
    ),
    "Procedures are hard for the team to find": _explorer_detail(
        "The answer exists, but your team cannot find it.",
        "Instructions are easy to search and use.",
        "Bring scattered guidance into one dependable source.",
        "Show me where your instructions are stored.",
        "Tell me what people search for most and where the answers live now.",
        "Questions about making procedures easier to find.",
        ("Gather the documents and conversations people rely on.", "Remove outdated or conflicting instructions.", "Create one search experience with clear source links."),
        ("Do all of our procedures need to be rewritten first?", "How will the assistant know which instruction is current?", "Can people verify where an answer came from?"),
    ),
    "Website visitors need quick answers": _explorer_detail(
        "Simple website questions keep becoming calls and emails.",
        "Customers get quick answers and know when to contact a person.",
        "Start with common questions and build a safe response path.",
        "Show me the questions customers ask most.",
        "Share the repeated questions and the answers you want customers to receive.",
        "Questions about answering visitors with AI.",
        ("Choose the questions suitable for an instant answer.", "Use only approved website and business information.", "Send uncertain or sensitive questions to a person."),
        ("Which website questions should an AI assistant answer?", "How do we prevent the assistant from making up an answer?", "When should the conversation be handed to a person?"),
    ),
    "Set up the basics for a new small business": _explorer_detail(
        "Every early technology choice affects the next one.",
        "The essentials work together and stay manageable.",
        "Choose only what the business needs now, then connect it cleanly.",
        "Tell me what your new business needs to do.",
        "What are you opening, selling, or scheduling—and what is already set up?",
        "Questions about setting up your business technology.",
        ("List the jobs the business must handle.", "Choose the simplest tools for those jobs.", "Connect the setup and document how to use it."),
        ("What technology should I set up before I open?", "Do I need separate tools for email, booking, and payments?", "Can the setup grow without starting over?"),
    ),
    "A build-vs-buy decision is unclear": _explorer_detail(
        "No ready-made tool fits perfectly.",
        "A clear decision based on cost, fit, and control.",
        "Compare the real compromises before spending money.",
        "Tell me what the software needs to do.",
        "Share the tools you have considered and the gaps that still matter.",
        "Questions about buying software or building it.",
        ("Define the few requirements that cannot be compromised.", "Compare total cost, flexibility, and ongoing ownership.", "Test the least expensive reasonable option first."),
        ("How close does ready-made software need to be?", "What costs are easy to miss in a custom build?", "Can we test the decision before making a large commitment?"),
    ),
    "Simplify the process before you buy or build software": _explorer_detail(
        "New software will not fix unnecessary steps.",
        "A simpler process before you buy anything.",
        "Map what happens today and remove the confusion first.",
        "Walk me through the work that feels broken.",
        "Describe one real job from start to finish, including every handoff and delay.",
        "Questions about fixing the process before the software.",
        ("Follow one job through the current process.", "Remove steps that add effort without adding value.", "Decide whether any software is still needed."),
        ("How can we tell whether the process or the software is the problem?", "Will simplifying the process disrupt current work?", "What if the best answer is not buying another tool?"),
    ),
    "A vendor proposal is hard to evaluate": _explorer_detail(
        "The proposal is hard to judge in the vendor's language.",
        "You know what is included, missing, and risky.",
        "Translate the proposal into plain decisions and questions.",
        "Show me the proposal before you sign it.",
        "Send the proposal and tell me what the vendor says it will solve.",
        "Questions about reviewing a technology proposal.",
        ("Match each promised feature to a real business need.", "Identify missing costs, assumptions, and responsibilities.", "Prepare the questions to ask before agreeing."),
        ("Which parts of a technology proposal deserve the closest review?", "How can I compare two proposals with different scopes?", "Can you join a vendor conversation if questions remain?"),
    ),
    "A project has stalled": _explorer_detail(
        "Progress stopped because the next move is unclear.",
        "A practical path that gets the project moving again.",
        "Find the blocker, assign the decision, and restart smaller.",
        "Tell me where the project stopped.",
        "Share what was completed, what is blocked, and who is involved now.",
        "Questions about recovering a stalled project.",
        ("Review the work, decisions, and promises already made.", "Name the blocker and the person who can resolve it.", "Restart with one small, verifiable milestone."),
        ("Can a stalled project be rescued without starting over?", "What if the original developer or vendor is unavailable?", "How do we prevent the project from stalling again?"),
    ),
    "You have too many product ideas": _explorer_detail(
        "Everything feels important, so nothing moves.",
        "A clear order for what to fix now and later.",
        "Rank each problem by impact, urgency, effort, and risk.",
        "Show me the list that keeps growing.",
        "Share the fixes and ideas competing for attention right now.",
        "Questions about choosing technology priorities.",
        ("Group related problems and remove duplicates.", "Rank the work by business value and urgency.", "Choose one first move with a clear finish line."),
        ("How do we compare an urgent fix with a promising new idea?", "Should easy wins come before higher-impact work?", "How often should the priority list be revisited?"),
    ),
}


def service_cards() -> list[dict[str, object]]:
    services_by_title = {service.title: service for service in SERVICES}
    cards: list[dict[str, object]] = []
    for source_title, group, title, summary, result in EXPLORER_SERVICES:
        service = services_by_title.get(source_title)
        if not service:
            raise ValueError(f"Explorer service title not found: {source_title}")
        detail = EXPLORER_DETAIL_COPY.get(source_title)
        if not detail:
            raise ValueError(f"Explorer detail copy not found: {source_title}")
        cards.append(
            {
                "title": title,
                "source_title": service.title,
                "category": service.category,
                "group": group,
                "group_label": EXPLORER_GROUP_LABELS[group],
                "summary": summary,
                "pain": service.pain,
                "result": result,
                "url": service.url,
                **detail,
            }
        )
    return cards


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
    return [
        {
            "question": "Can you help if I don't know what's causing it?",
            "answer": "Yes. Tell me what you can see, when it started, and anything that changed. I can investigate from there.",
        },
        {
            "question": "What should I send before we talk?",
            "answer": "Send whatever you already have. A link, screenshot, example, or error message is usually enough to get started.",
        },
        {
            "question": "Is this a one-time fix, or can you keep helping?",
            "answer": CATEGORY_ONGOING_CONTEXT[service.category],
        },
        {
            "question": "Will I work with you directly?",
            "answer": "Yes. I handle the call, the recommendation, and the work. If I ever need to bring in someone else, I'll tell you first.",
        },
    ]
