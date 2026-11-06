# Problem Statement: Weekly App Review Pulse

**Project owner:** Tejas R Mutalik
**Milestone:** 2
**Product:** `<PRODUCT_NAME>`, the same product chosen in Milestone 1 (fill in before starting)

---

## 1. Background

Mobile products get a steady stream of user feedback through public reviews on the Apple App Store and the Google Play Store. These reviews show where users struggle (onboarding, KYC, payments, statements, withdrawals and so on), but they are:

- **Spread out** across two stores with different formats.
- **High volume and unstructured,** so nobody can read all of them each week.
- **Rarely turned into decisions,** because there is no regular, short summary that teams act on.

As a result, Product, Support and Leadership often learn about recurring pain points late, or only from anecdotes.

## 2. Problem

There is no lightweight, repeatable way to turn recent public app reviews into a short weekly summary that says **what users are saying, what hurts most, and what to do next**, and to deliver it to stakeholders where they already work (email and docs).

## 3. Goal

Build a pipeline that turns the last **8–12 weeks** of public App Store and Play Store reviews for `<PRODUCT_NAME>` into a **one-page weekly pulse**, saves it as a **Google Doc**, and creates a **Gmail draft** of the note addressed to myself or an alias. All Google integration goes through **MCP servers**, not direct API calls.

## 4. Who This Helps

| Audience | What they need | How the pulse helps |
|---|---|---|
| Product / Growth teams | Know what to fix or improve next | Ranked top themes and concrete action ideas |
| Support teams | Know what users are saying and what to acknowledge | Real (anonymised) quotes and recurring issues |
| Leadership | A quick weekly health check | One scannable page, readable in under 2 minutes |

## 5. Scope

### 5.1 In scope

1. **Review ingestion**
   - Import reviews from the **last 8–12 weeks** from both the App Store and the Play Store.
   - Fields captured per review: **rating, title, text, date** (plus store as a source tag).
   - Sources: **public review exports or publicly accessible review feeds only.**
2. **PII removal**
   - Strip or never collect usernames, emails, reviewer IDs, phone numbers, account numbers or any other identifying data.
   - Clean quotes before they are used anywhere.
3. **Theme grouping**
   - Group reviews into **no more than 5 themes** (for example: onboarding, KYC, payments, statements, withdrawals).
   - Each theme carries a volume count and average rating so themes can be ranked.
4. **Weekly note generation**: a one-page note of **250 words or fewer** containing:
   - **Top 3 themes** (with a short description and volume or sentiment signal)
   - **3 real user quotes** (verbatim, PII-free)
   - **3 action ideas** (specific and tied to the themes)
5. **Delivery through MCP**
   - **Google Docs MCP server:** create or update the weekly pulse as a Google Doc.
   - **Gmail MCP server:** create a **draft** email containing the weekly note, addressed to myself or an alias. Create it as a draft only; do not send automatically.

### 5.2 Out of scope

- Scraping content behind logins, or any non-public data source.
- Replying to reviews in the stores.
- Sending emails to external recipients automatically.
- Real-time or daily monitoring; the cadence is weekly.
- Calling Google Docs or Gmail REST APIs directly (MCP servers are used instead).

## 6. Constraints

| # | Constraint |
|---|---|
| C1 | **Public data only:** use public review exports or feeds. No scraping behind logins. |
| C2 | **At most 5 themes** across the review set. |
| C3 | **Weekly note is 250 words or fewer,** scannable (headings and bullets). |
| C4 | **No PII** (no usernames, emails or IDs) in **any** artifact: raw stores, intermediate files, the Google Doc or the email draft. |
| C5 | **Integration through MCP servers only** for Google Docs and Gmail. No hand-written REST API integration. |
| C6 | Email is a **draft** sent to self or an alias only. |

## 7. Proposed Solution Outline

```
┌──────────────────────┐   ┌──────────────┐   ┌──────────────────┐
│ App Store reviews    │──▶│              │   │                  │
│ (public export/feed) │   │  Ingest &    │──▶│  Theme grouping  │
├──────────────────────┤   │  normalise   │   │  (≤ 5 themes)    │
│ Play Store reviews   │──▶│  + strip PII │   │                  │
│ (public export/feed) │   └──────────────┘   └────────┬─────────┘
└──────────────────────┘                               │
                                                       ▼
                                          ┌─────────────────────────┐
                                          │ Weekly note generator   │
                                          │ Top 3 themes · 3 quotes │
                                          │ · 3 actions (≤250 words)│
                                          └────────────┬────────────┘
                                                       │
                              ┌────────────────────────┴───────────────┐
                              ▼                                        ▼
                  ┌───────────────────────┐              ┌───────────────────────┐
                  │ Google Docs MCP server│              │ Gmail MCP server      │
                  │ → weekly pulse doc    │              │ → draft email to self │
                  └───────────────────────┘              └───────────────────────┘
```

**Common review schema (after PII removal):**

| Field | Type | Notes |
|---|---|---|
| `store` | enum (`app_store`, `play_store`) | Source tag |
| `rating` | int (1–5) | |
| `title` | string | May be empty (often empty on Play Store) |
| `text` | string | PII-cleaned |
| `date` | ISO date | Must fall within the 8–12 week window |
| `theme` | string | Assigned during grouping |

## 8. Deliverables

1. Review dataset for the last 8–12 weeks (both stores, PII-free).
2. Theme mapping: at most 5 themes with counts and average ratings.
3. Weekly pulse note (250 words or fewer) saved as a **Google Doc** through the Google Docs MCP server.
4. **Gmail draft** containing the weekly note, addressed to self or an alias, through the Gmail MCP server.
5. A short README explaining how to re-run the pipeline each week.

## 9. Weekly Note Template

```
Subject: <PRODUCT_NAME> Weekly Review Pulse | Week of <DATE>

Window: <start> – <end> · Reviews analysed: <N> · Avg rating: <x.x>

TOP THEMES
1. <Theme>: <one-line summary> (<n> reviews, avg <x.x>★)
2. <Theme>: <one-line summary>
3. <Theme>: <one-line summary>

WHAT USERS SAY
• "<quote 1>" (<rating>★, <store>)
• "<quote 2>" (<rating>★, <store>)
• "<quote 3>" (<rating>★, <store>)

ACTION IDEAS
1. <action tied to theme 1>
2. <action tied to theme 2>
3. <action tied to theme 3>
```

## 10. Success Criteria

- [ ] Reviews from **both** stores, covering the **8–12 week** window, are imported with rating, title, text and date.
- [ ] Reviews are grouped into **5 or fewer** themes.
- [ ] The note has exactly **3 themes, 3 quotes and 3 action ideas** and is **250 words or fewer**.
- [ ] **No PII** appears in any artifact (checked before publishing).
- [ ] The Google Doc is created through the **Google Docs MCP server**.
- [ ] The email **draft** is created through the **Gmail MCP server**, addressed to self or an alias.
- [ ] No direct Google API integration code is used.

## 11. Open Items

- Confirm `<PRODUCT_NAME>` (from Milestone 1) and its App Store and Play Store identifiers.
- Choose the public review source for each store (official export, public RSS feed, or a public dataset).
- Confirm which Google Docs and Gmail MCP servers to use and connect them to the account.
- Confirm the recipient alias for the draft email.
