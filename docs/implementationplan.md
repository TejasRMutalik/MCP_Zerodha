# Implementation Plan: Weekly App Review Pulse (Zerodha Kite)

**Project owner:** Tejas R Mutalik
**Related:** [Architecture](architecture.md) · [Evaluation](eval.md) · [Decisions](decision.md)

---

## How the work is divided

| | Half A: Data pipeline | Half B: Note and delivery |
|---|---|---|
| **Owner** | Teammate | **Tejas R Mutalik** |
| **Scope** | Reviews to themed dataset | Themed dataset to Google Doc and Gmail draft |
| **Produces** | `reviews_clean.json`, `themes.json`, `find_pii()` | Weekly note, validation gate, delivery agent |
| **Main risk** | Two messy sources, theme quality | MCP auth, draft-only safety, the 250-word limit |

Both people work at the same time in Phases 1–3. Half B builds against sample files, so neither person waits for the other. Phases 0, 4 and 5 are done together.

```
Phase 0   Foundation            ████ both
Phase 1   A: Ingestion          ████████
          B: MCP connection     ████████
Phase 2   A: PII scrubbing      ████████
          B: Note generator     ████████
Phase 3   A: Theme grouping     ████████
          B: Gate and delivery  ████████
Phase 4   Integration           ████ both
Phase 5   Weekly run, README    ████ both
```

**Moving on:** a phase is finished only when its exit criteria in [eval.md](eval.md) pass. Each person's track can move on independently, except where a dependency is listed below.

---

## Phase 0: Foundation (both)

**Goal:** agree the shared parts so both people can work independently.

| # | Task | Owner |
|---|---|---|
| 0.1 | Run `git init`, add `.gitignore` (`data/`, `.env`, `config.local.toml`), create the shared repo | Both |
| 0.2 | Create the folder layout from the architecture doc, plus `pyproject.toml` and `config.toml` | Both |
| 0.3 | Write `src/pulse/schema.py` for both shared files | Both |
| 0.4 | Hand-write `contracts/samples/` with 30 fake reviews and 5 themes. Include a redacted review, an `other` theme and short reviews | Both |
| 0.5 | Close the open questions in [decision.md](decision.md#open-questions) | Both |
| 0.6 | Each person creates their own Gemini API key in Google AI Studio (**do not link billing**) and a Groq key as backup, and stores them in `.env` | Both |
| 0.7 | Write the shared `llm` interface in `src/pulse/llm/`: Gemini and Groq providers (optional Ollama), batching of about 50 reviews, retry with failover, and a per-review result cache | Both |
| 0.8 | Run one 50-review test batch through each provider and record the real limits, speed and errors in D-022 | Both |

**Output:** a repo both people can clone, a fixed contract, sample data, a working `llm.complete()` on both machines, and no blocking open questions.

**Status on 2026-11-06 (Tejas):** 0.2, 0.3, 0.4 and 0.7 are built and tested (`uv run pytest`). 0.6 and 0.8 are done for Tejas's keys, with results in D-022. Still to do: the teammate's keys and test batch (0.6, 0.8), Q9/Q10 limits, and the teammate's review of the contract.

**Status update 2026-11-10 (Tejas):** Q2 is settled (personal Google account), Q9 and Q10 are skipped. Phase 2 Half B has started: B2.1 (ranker) and B2.2 (quote filter) are built and tested, with a local `find_pii` stub until A2.4. B1.1 is decided; connecting the connectors (Q11) and B1.2 to B1.6 are deferred until the note generator works, and must be done before any delivery code is trusted.

**Status update 2026-11-10 (Tejas, later):** B2.3 to B2.5 are built: structured note, writer with retry and quote-ID checks, renderer, and `python -m pulse.note`. A real Gemini run on the 30 sample reviews produced a valid, specific note within the word limit. B2.6 (prompt tuning on real data) and the validation gate remain.

**Status update 2026-11-07 (Ace):** 0.6 and 0.8 are done for Ace's keys. Groq works on both models (`gpt-oss-20b` in 2.2 s, `gpt-oss-120b` in 3.5 s, 50/50 correct). A first Gemini key was blocked with HTTP 403 free-tier-unavailable; a key created in a fresh AI Studio project works — three consecutive 50-review batches passed 50/50 in 3.7–4.6 s with no 429, and no rate-limit headers are returned (Q9's caps remain unreadable that way). Both providers now work on both machines. Q8 (agreement with D-019–D-023) and the numbers behind Q9/Q10 are still owed by Ace.

---

## Phase 1: Get connected

### Half A: Ingestion

| # | Task |
|---|---|
| A1.1 | App Store adapter: read RSS pages 1–10 for app `1449453802`, `in` storefront, stop once past the window |
| A1.2 | Play Store adapter: `google-play-scraper` for `com.zerodha.kite3`, newest first, `lang=en`, `country=in`, stop once past the window |
| A1.3 | Copy only rating, title, text and date. Identifying fields never leave the adapter |
| A1.4 | Normaliser: map both into the common schema, tag `store`, apply the 12-week window, remove exact duplicates |
| A1.5 | Add volume checks that stop the run if a store returns far too little |

**Output:** `pulse ingest` writes normalised rows for both stores.

### Half B: MCP connection (Tejas)

| # | Task |
|---|---|
| B1.1 | Confirm which Google account will own the doc and draft, then connect the Docs and Gmail connectors to it |
| B1.2 | List the live tools on Drive, Docs and Gmail, and record exact names in `decision.md` (updates D-015, D-016) |
| B1.3 | Write `.claude/settings.json`: allow only the tools in the architecture doc, deny send, forward, filter and label tools by exact name |
| B1.4 | Manual spike: create a test doc through Drive, write formatted text through Docs, read it back |
| B1.5 | Manual spike: create one test draft to the alias, confirm it sits in Drafts and nothing is in Sent |
| B1.6 | Find which format keeps headings and bullets in the doc, since this decides how the note is passed to `update_doc` |

**Output:** a working, proven path to Google with the send tools blocked. This is the riskiest part of Half B, so it comes first.

---

## Phase 2: Process the content

### Half A: PII scrubbing

| # | Task |
|---|---|
| A2.1 | Implement `find_pii(text)` returning matches by type: email, phone, Zerodha client ID, PAN, UPI ID, demat or bank account number, URL, @handle |
| A2.2 | Scrubber replaces matches with `[redacted]` and sets `redacted: true` |
| A2.3 | Build a synthetic PII test set. Never use real people's data |
| A2.4 | Publish `find_pii()` early, even if incomplete, because Half B's validator imports it |

**Output:** `pulse scrub` writes clean rows, and `find_pii()` is importable.

### Half B: Note generator (Tejas)

| # | Task |
|---|---|
| B2.1 | Ranker: compute `impact`, exclude `other`, return the top 3 |
| B2.2 | Quote filter: the eligibility rules in architecture section 5 |
| B2.3 | Define the structured output for the note: theme summaries, quote IDs, action ideas |
| B2.4 | Note writer: call the LLM with no tools, picking quotes by ID so they cannot be altered |
| B2.5 | Python renderer: fill the problem-statement template from the structured output |
| B2.6 | Tune the prompt on sample data until notes are specific, not generic |

**Output:** `pulse note` turns the two sample files into `pulse_note.md`.
**Depends on:** sample files (Phase 0). A stub `find_pii()` is fine until A2.4.

---

## Phase 3: Finish each half

### Half A: Theme grouping

| # | Task |
|---|---|
| A3.1 | Discover candidate themes from one full review set with the LLM, using the data, not a fixed list |
| A3.2 | Fix the theme list at 4 product themes plus `other` |
| A3.3 | Assign every review to one theme using structured output, with no tools |
| A3.4 | Compute `count` and `avg_rating` in Python, never from the LLM |
| A3.5 | Hand-label 100 reviews as a gold set and measure agreement |
| A3.6 | Keep theme names stable week to week so results can be compared |
| A3.7 | Run the gold set through each available provider and model, and record the pick and its score in `decision.md` |

Theme ideas to test, not findings: order execution, app outages at market open, login and 2FA, charts, funds and withdrawals, charges. The problem statement's examples, such as KYC, may not fit a trading app already past onboarding.

**Output:** real `reviews_clean.json` and `themes.json`, matching the contract.

### Half B: Validation gate and delivery agent (Tejas)

| # | Task |
|---|---|
| B3.1 | Build every validation check in architecture section 5 |
| B3.2 | Add the retry loop: up to 2 regenerations, then stop with a clear error |
| B3.3 | Write `validation.json` with the note's SHA-256, and build `pulse check-delivery-ready` |
| B3.4 | Write `.claude/commands/deliver-pulse.md` following the delivery sequence |
| B3.5 | Make delivery safe to rerun with `delivery.json` and a title search |
| B3.6 | Run the whole of Half B end to end on sample data, using a clearly marked test doc and draft |

**Output:** sample files in, Google Doc and Gmail draft out, and a rerun creates no duplicates.
**Depends on:** B1 (MCP path), A2.4 (real `find_pii()`).

---

## Phase 4: Integration (both)

**Goal:** run on real data and find what the sample data hid.

| # | Task | Owner |
|---|---|---|
| 4.1 | Connect the halves in `pulse run` | Both |
| 4.2 | First full run on real reviews | Both |
| 4.3 | Fix contract mismatches. Any contract change is logged as a decision | Both |
| 4.4 | Check enough quotes survive eligibility on real data. If not, revisit [D-011](decision.md#d-011-quote-rules) | Tejas |
| 4.5 | Check App Store complaints are not lost, as Play Store is 92% of the data | Teammate |
| 4.6 | Cross-review: each person checks the other's output for PII and quality | Both |
| 4.7 | Prompt injection test with a hostile review in the data | Both |

**Output:** one real pulse in Google Docs and a real draft, with every success criterion checked.

---

## Phase 5: Weekly run and handover (both)

| # | Task | Owner |
|---|---|---|
| 5.1 | Write `README.md`: setup, weekly commands, what to do on each failure | Both |
| 5.2 | Each person reruns the whole thing from the README alone, on a clean checkout | Both |
| 5.3 | Run a second week, or a later date range, to prove it repeats and themes stay stable | Both |
| 5.4 | Collect the deliverables and tick off problem-statement section 10 | Both |

**Output:** all 5 deliverables, and a pipeline either person can run alone.

### The weekly run (target)

```bash
uv run pulse run --week 2026-W45
```

Then, in a Claude Code session in this project:

```text
/deliver-pulse 2026-W45
```

---

## Deliverables by owner

| # | Deliverable | Owner | Phase |
|---|---|---|---|
| 1 | PII-free review dataset, both stores | A | 2–4 |
| 2 | Theme mapping with counts and average ratings | A | 3 |
| 3 | Weekly pulse note as a Google Doc | **B** | 3–4 |
| 4 | Gmail draft to self or alias | **B** | 3–4 |
| 5 | README for the weekly re-run | Both | 5 |
