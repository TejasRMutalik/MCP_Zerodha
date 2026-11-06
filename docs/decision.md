# Decision Log: Weekly App Review Pulse (Zerodha Kite)

**Project owner:** Tejas R Mutalik
**Related:** [Architecture](architecture.md) · [Implementation plan](implementationplan.md) · [Evaluation](eval.md)

---

## How to use this file

Record any technical or business decision that would be expensive to reverse, or that the other person needs to know. Never rewrite an old entry: add a new one and mark the old one **Superseded by D-xxx**.

| Status | Meaning |
|---|---|
| **Accepted** | Decided by the team |
| **Proposed** | Recommended and used in the docs, waiting for the team to confirm |
| **Superseded** | Replaced by a later decision |

Changes to the contract between Half A and Half B always need both people's agreement.

---

## Open questions

"Blocks" means work cannot be finished until it is answered.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q1 | Does "Zerodha" mean the **Kite** app? Zerodha also has other apps, such as Coin | Tejas | Phase 0 |
| Q2 | Which Google account owns the doc and draft? Connectors act as whichever account signed in, so it should be checked before Phase 1. The Drive connector is already signed in to an account | Tejas | Phase 1 (B) |
| Q3 | What recipient alias should the draft use? | Tejas | Phase 3 (B) |
| Q4 | Who provides the Anthropic API key? API use is billed separately from a Claude subscription | Both | Phase 2 |
| Q5 | Is an unofficial Play Store library acceptable to whoever assesses this milestone? See D-006 | Both | Phase 1 (A) |
| Q6 | Teammate's name, for the owner fields | Tejas | No |
| Q7 | Does Docs MCP really have no create tool? Confirm from the live tool list | Tejas | Phase 1 (B) |

---

## Business and scope

### D-001: Product is Zerodha Kite

- **Date:** 2026-11-06 · **Status:** Proposed (Q1) · **Owner:** Tejas
- **Decision:** `<PRODUCT_NAME>` is **Zerodha Kite**: App Store `1449453802`, Play Store `com.zerodha.kite3`.
- **Why:** The team chose Zerodha, and Kite is its main trading app. Both IDs were confirmed against the live store listings on 2026-11-06.

### D-002: Team split at the themed dataset

- **Date:** 2026-11-06 · **Status:** Accepted · **Owner:** Both
- **Decision:** Half A (teammate) owns ingestion, PII scrubbing and themes. Half B (Tejas) owns the note, validation and MCP delivery.
- **Why:** The only link between the halves is two files, so both can work in parallel.

### D-007: Rolling 12-week window

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Teammate
- **Decision:** Use the full 12 weeks each run, ending at the run date.
- **Why:** The App Store gives only 86 reviews in 8 weeks against 122 in 12, so the longer window keeps it visible.
- **Alternative:** 8 weeks, which is more current but thin on the App Store.

### D-009: At most 5 themes, including `other`

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Teammate
- **Decision:** 4 product themes plus `other`. `other` counts toward the limit and cannot reach the Top 3.
- **Why:** 36% of Play reviews are 3 words or fewer, and "good app" fits no theme. Counting `other` keeps C2 strictly true.
- **Alternative:** Leaving unthemed reviews out, which would make the total misleading.

### D-010: Rank themes by impact

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** `impact = count × (5 − avg_rating)`.
- **Why:** The pulse must show what hurts most, and 58% of Play reviews in the window are 5★. Ranking by volume alone could put praise first. This uses only the two numbers already in `themes.json`.
- **Alternative:** Counting only ≤ 2★ reviews, which ignores mixed 3★ feedback.

### D-011: Quote rules

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** Quotes are whole, unredacted, English reviews of 6–25 words from a Top 3 theme, with no personal names. They are chosen by ID so they cannot be reworded.
- **Why:** The problem statement requires verbatim and PII-free quotes. Three quotes must fit inside a 250-word note, which sets the upper limit.
- **Risk:** Median Play review length is 6 words, so the pool may be small for some themes. Checked in task 4.4. A likely fix is to allow an exact excerpt from a longer review.

### D-018: Word limit covers the whole note

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** The 250-word count includes the subject line, header, section titles and attributions.
- **Why:** This is the strictest reading, so the note passes under any other reading.

---

## Data sources

### D-003: Two shared JSON files as the contract

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Both
- **Decision:** `reviews_clean.json` and `themes.json`, as defined in the architecture doc. The schema adds a `redacted` flag.
- **Why:** The flag lets Half B avoid quoting text the scrubber changed, which would no longer be verbatim.

### D-005: App Store source is the public RSS feed

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Teammate
- **Decision:** Use the Apple customer reviews RSS feed for the `in` storefront, pages 1–10.
- **Why:** It is public and needs no login. Tested on 2026-11-06: 50 reviews per page, 10 pages at most, and it covers the 12-week window with 122 reviews.
- **Risk:** The 500-review cap is fine for Kite's current volume but would matter for a much bigger app.

### D-006: Play Store source is `google-play-scraper`

- **Date:** 2026-11-06 · **Status:** Proposed (Q5) · **Owner:** Teammate
- **Decision:** Use the open-source `google-play-scraper` library for public reviews, without login.
- **Why:** Google offers no public review feed, and the official Play Console export needs developer access to the app, which this team does not have. Tested on 2026-11-06: 1,403 reviews in 12 weeks.
- **Risk:** It is unofficial and reads public pages, so it fits C1's "no login" rule, but the problem statement says "exports or feeds". It may break if Google changes its pages, and Google's terms should be checked. This is the reason for Q5.
- **Alternative:** A public dataset, but these are unlikely to cover the most recent 12 weeks.

### D-008: Allowlist fields at the adapter

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Teammate
- **Decision:** Adapters copy only rating, title, text and date. No raw response is saved.
- **Why:** Both sources return reviewer names and IDs, and C4 forbids PII even in raw stores. Not collecting it is safer than deleting it later.

---

## Technology

### D-004: Python with uv

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Both
- **Decision:** Python 3.13, managed with `uv`.
- **Why:** `google-play-scraper` is a Python library and the Anthropic SDK is available for Python. Python 3.13 and uv are on Tejas's machine. The teammate's setup still needs checking.

### D-012: LLM model and output format

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Both
- **Decision:** Use `claude-opus-5-5` through the Anthropic Python SDK, with structured outputs. Set `effort` explicitly and handle a `refusal` stop reason.
- **Why:** Structured output means Python can check every field. Prices are $4 per million input tokens and $20 per million output tokens as of the 2026-10-06 model table.
- **Cost:** About 1,500 short reviews per run suggests under $1 a week. This is an estimate; eval P5-4 records the real figure. A cheaper model can be tried later if the gold-set score holds.
- **Note:** `temperature` is no longer accepted, so runs cannot be made identical through settings. This is why eval P3-A6 tests stability and why the validation gate exists.

### D-013: The LLM that reads reviews has no tools

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Both
- **Decision:** Theme grouping and note writing run with no tools. Only the delivery agent has MCP tools, and it sees only the validated note.
- **Why:** Anyone can write a public review, including instructions aimed at an AI. Keeping review reading apart from Gmail access removes that path instead of hoping the model ignores it.
- **Alternative:** One agent doing everything, which is simpler but gives untrusted text direct access to a mailbox.

### D-014: Delivery runs in Claude Code with connectors

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** `/deliver-pulse` is a Claude Code command using the Google connectors. It is run by hand each week.
- **Why:** It needs no OAuth code, meets C5 directly, and tool permissions can be allowed or denied by name. The cadence is weekly and the output is a draft, so a human starting it is fine.
- **Alternative:** The Claude API MCP connector, which could run unattended but means managing Google OAuth tokens. Better as a later step if the run is scheduled.

### D-015: Create the doc through Drive, fill it through Docs

- **Date:** 2026-11-06 · **Status:** Proposed (Q7) · **Owner:** Tejas
- **Decision:** Drive `create_file` makes an empty Google Doc. Docs `update_doc` writes the note.
- **Why:** The registry lists only `read_doc` and `update_doc` for the Docs server. Drive `create_file` can create a native Google Doc, so content still goes through the Docs MCP server, matching "create or update".
- **Risk:** Section 10 says "created through the Google Docs MCP server". If the assessor reads that strictly, a Docs server with a create tool is needed.

### D-016: Draft-only is enforced by permissions

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** Allow `create_draft` and deny all Gmail send and forward tools by exact name. Take the recipient from `config.toml`.
- **Why:** The Gmail server exposes more than drafting, including `forward`. C6 should hold even if the agent makes a mistake.
- **To do:** Add exact tool names here once the connector is live (task B1.2).

### D-017: Delivery is safe to rerun

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** Each run records doc and draft IDs in `delivery.json`, and the agent searches for an existing doc by title first.
- **Why:** A failure between the doc and the draft is the likeliest partial failure, and a rerun must not create duplicates.

---

## Template for new decisions

```markdown
### D-0XX: Short title

- **Date:** YYYY-MM-DD · **Status:** Proposed · **Owner:** Name
- **Decision:** What was decided.
- **Why:** The reason, with evidence where possible.
- **Alternative:** What else was considered.
- **Risk:** What could go wrong.
```
