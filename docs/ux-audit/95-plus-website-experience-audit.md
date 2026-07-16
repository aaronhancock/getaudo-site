# 95+ Website Experience Audit

## Purpose

The 95+ Website Experience Audit is a reusable, evidence-based process for reviewing and improving a public website. It adapts the rigor of Audo's admin UX audit without depending on Audo admin routes, fixtures, workflows, roles, or components.

It is designed to answer five questions for every meaningful visitor experience:

1. Can the intended visitor understand it?
2. Can the visitor confidently decide what to do next?
3. Can the visitor complete the task without friction or prior technical knowledge?
4. Does the experience earn trust and support the website's business objective?
5. Does it work reliably on desktop, mobile, keyboard, and assistive technology?

This is not a checklist-only or automated score. Codex performs the substantive analysis using screenshots, rendered behavior, content, DOM evidence, accessibility results, performance evidence, and complete task execution. Automated checks provide evidence and hard gates; they do not replace judgment.

## Scope model

The audit inventory is built from visitor-visible **experiences**, not only URLs. An atomic audit item is one page, state, step, or interaction with one immediate visitor objective.

Inventory sources include:

- Public routes and templates.
- Header, navigation, footer, and site-wide components.
- Page sections that carry a distinct message, decision, or action.
- Forms, schedulers, purchases, downloads, and other conversion paths.
- Menus, dialogs, accordions, tabs, carousels, videos, and embeds.
- Loading, empty, validation, error, success, cancellation, and recovery states.
- Desktop and mobile variants.
- Keyboard, focus, and screen-reader states.
- Titles, descriptions, canonicals, social metadata, structured data, redirects, 404s, and indexing behavior.
- Performance-sensitive fonts, images, scripts, and third-party resources.
- Every new public experience created during improvement work.

The manifest must state for each item:

- Stable ID and route.
- Visitor persona and immediate objective.
- The one expected next action.
- What happens after that action.
- Why the task matters to the visitor.
- Why it matters to the business.
- Completion evidence and expected destination.
- Applicable edge and recovery states.
- Launch priority and business criticality.

## Viewports

Each item is reviewed independently at:

- Desktop: `1280 × 900`.
- Mobile: `390 × 844`.
- Narrow mobile hard-gate smoke check: `360 × 800`.

Additional breakpoints may be tested when the layout changes materially.

## Scoring contract

Each desktop and mobile item receives five independent 1–100 scores. Scores are never averaged to hide a failing category.

### 1. Clarity

- Purpose and audience are immediately understandable: 15 points.
- Problem, offer, or information is explained plainly: 20 points.
- Next action is unmistakable: 20 points.
- Result of the action is explained: 15 points.
- Why it matters is clear: 10 points.
- Completion and next destination are clear: 10 points.
- No technical or insider knowledge is required: 10 points.

### 2. Simplicity

- One primary message, decision, or action at a time: 25 points.
- Only information needed now receives emphasis: 20 points.
- Safe or recommended choice is supplied when useful: 15 points.
- Advanced and future information uses progressive disclosure: 15 points.
- Minimal memory, typing, and prior knowledge are required: 10 points.
- No duplicate, competing, or contradictory guidance: 15 points.

### 3. Usability and accessibility

- Visual hierarchy and primary action: 15 points.
- Navigation, orientation, and progress: 15 points.
- Responsive layout, readable type, and no cutoff or overflow: 20 points.
- Feedback, validation, error recovery, and preserved context: 15 points.
- Keyboard order, focus, semantics, and screen-reader behavior: 20 points.
- Touch targets, interaction reliability, and back-navigation behavior: 15 points.

### 4. Trust and credibility

- Claims are truthful, specific, and appropriately supported: 20 points.
- Identity, ownership, qualifications, and responsibility are clear: 15 points.
- Privacy, consent, contact expectations, and relevant limitations are clear: 15 points.
- Visual and editorial presentation feels professional and complete: 15 points.
- Pricing, commitments, or next-step expectations are transparent when relevant: 15 points.
- No manipulation, fake urgency, invented proof, or internal language: 20 points.

### 5. Business effectiveness

This category is adapted to the site's objective: lead generation, sale, booking, support, education, donation, visit, signup, or another declared outcome.

- Visitor value is concrete and compelling: 20 points.
- The action matches the visitor's likely intent and readiness: 15 points.
- Objections and uncertainty are answered without overload: 15 points.
- The complete path has minimal friction: 20 points.
- The promised outcome matches the actual destination and result: 20 points.
- Measurement is ethical, truthful, and aligned with the declared objective: 10 points.

## Evidence and deductions

Every deduction records:

- Category and criterion.
- Points deducted.
- Exact visible or behavioral reason.
- Screenshot, DOM, interaction, accessibility, metadata, link, or performance evidence.
- Exact improvement required to recover the points.

Fixed deduction anchors:

- 2 points: minor friction.
- 5 points: noticeable hesitation or presentation problem.
- 10 points: likely confusion, lost trust, or abandonment.
- 20 or more points: blocked task, broken interaction, misleading claim, or dependence on unexplained knowledge.

## Passing rule

An item passes only when:

- All five desktop scores are at least 95.
- All five mobile scores are at least 95.
- No hard-gate failure remains.
- The limiting persona can complete the intended task using only visible instructions.
- The item has fresh rendered evidence after its latest material change.
- An independent Codex review confirms the score rather than copying the prior assessment.

Code inspection alone cannot produce a passing result.

## Hard gates

Hard-gate failures include:

- Broken, inert, misleading, or incorrectly routed actions.
- A form, booking, checkout, signup, or contact flow that cannot be completed or recovered.
- False, unsupported, unverifiable, or misleading claims.
- Missing consent or privacy information for personal-data collection.
- Horizontal overflow, overlap, cutoff, unreadable text, or hidden critical controls.
- Critical mobile controls smaller than 44 pixels.
- Serious or critical accessibility findings.
- Keyboard traps, lost focus, incorrect focus restoration, or inaccessible navigation.
- Dead ends, context loss, false success, or unclear completion.
- Missing or misleading titles, canonicals, redirects, indexing directives, or primary metadata.
- Severe performance behavior that materially prevents use.
- A primary action whose destination does not deliver what was promised.
- Real customer, billing, publishing, email, booking, or destructive mutations during audit fixtures.

## Mandatory discoverability and accessibility-readiness module

Every future 95+ audit must also run the reusable website-readiness package described in `reusable-website-readiness-service.md`. This is a release gate, not an optional appendix.

Required evidence includes:

- Canonical, robots, XML sitemap, redirect, indexing, metadata, and structured-data alignment.
- Human sitemap and all agent-readable catalogs generated from the same live route inventory.
- `/llms.txt`, `/llms-full.txt`, page-specific Markdown where offered, and source-of-truth guardrails for agents.
- Page-level language, headings, landmarks, image alternatives, control names, form labels, and unique IDs.
- Rendered keyboard, focus, zoom/reflow, contrast, reduced-motion, target-size, screen-reader, and form-recovery checks.
- Explicit disclosure that automated accessibility evidence is not legal advice or a WCAG/ADA certification.
- No claims that SEO markup guarantees rankings, rich results, indexing, AI citations, or recommendations.

## Audit dashboard

Each website receives its own local dashboard, separate from product/admin audits. Recommended path:

`outputs/website-experience-audit/index.html`

The dashboard must:

- Refresh every 30 seconds without requiring an application server.
- Show total, inventoried, analyzed, passing, failing, blocked, and pending items.
- Show current item, current loop, latest change, latest result, and next adjustment.
- Show every desktop/mobile category score and each viewport average.
- Sort scored items by launch-priority band, then lowest individual score, then lowest average.
- Put unscored items below scored items within the same priority band.
- Show deductions, hard gates, evidence, attempts, and reviewer notes.
- Link unique before and after screenshots for every finalized item.
- Never overwrite a before image with an after image.
- Automatically surface newly discovered or newly created experiences.
- Distinguish product failures from unavailable fixtures or external blockers.
- Embed only seeded, synthetic, public, or redacted data.

## Operation phases

### Phase 1: Discovery and architecture

1. Find the actual repository, runtime, CMS, deployment method, data stores, forms, integrations, and public routes.
2. Establish production as read-only during discovery.
3. Build a deterministic local environment using safe fixtures.
4. Create the atomic manifest and a completeness check.
5. Create the dashboard with all known items initially unscored.

### Phase 2: Baseline

1. Analyze all major pages and complete visitor workflows before fixing small elements.
2. Capture desktop and mobile screenshots.
3. Exercise complete tasks and recovery paths.
4. Run DOM, link, metadata, accessibility, keyboard, focus, responsive, and performance checks.
5. Perform Codex analysis and record evidence-backed scores.
6. Freeze the baseline and create the worst-first queue.

### Phase 3: Improvement loops

Only one audit item is active at a time, although a shared component change may affect several items.

1. Reproduce the exact local state.
2. Review it through the limiting persona.
3. Record deductions and identify the smallest coherent improvement.
4. Implement locally.
5. Run focused functional, responsive, accessibility, content, metadata, performance, and persistence checks.
6. Capture fresh evidence with unique filenames.
7. Independently rescore the item.
8. Update the dashboard immediately.
9. Repeat until all scores are 95+ and hard gates pass.
10. Re-audit every other item affected by shared changes.
11. Recalculate the queue and continue without waiting between items.

### Phase 4: Release checkpoint

Before deployment:

- Every launch-critical item passes.
- Complete conversion journeys pass end to end with safe fixtures.
- No known broken action remains.
- Accessibility, responsive, link, metadata, SEO, and performance release gates pass.
- Before/after evidence exists for every changed passing item.
- The exact tested revision is committed and pushed.
- A rollback path and production smoke plan are documented.

Deploy only the exact tested revision. Production verification is read-only and must confirm the primary journeys, health, revision, and absence of regressions to adjacent products or routes.

## Prioritization

Priority bands should be customized to the website, but the default order is:

1. Site-wide navigation and the homepage.
2. Primary business/conversion journey.
3. Core offer or information pages.
4. Trust, proof, identity, and objections.
5. Forms, scheduling, checkout, signup, and confirmation.
6. Mobile navigation and mobile conversion.
7. Supporting content.
8. Legal, privacy, accessibility, errors, and recovery.
9. Secondary components and edge cases.

Within each band, work from the lowest individual score upward. Hard-gate failures always precede score-only improvements.

## Guardrails

- Do not weaken authentication, privacy, consent, or security to make a score rise.
- Do not invent testimonials, results, customer counts, awards, credentials, partnerships, urgency, or statistics.
- Do not expose internal architecture, margins, provider secrets, operational notes, or implementation jargon.
- Do not perform customer-facing mutations during tests.
- Do not mark unavailable evidence as passing.
- Do not inflate scores to finish faster.
- Do not deploy between local loops.
- Do not treat a passing average as sufficient when any individual category is below 95.
