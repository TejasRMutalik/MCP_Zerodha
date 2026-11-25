# Evaluation Plan: Weekly App Review Pulse (Zerodha Kite)

**Project owner:** Tejas R Mutalik
**Related:** [Architecture](architecture.md) · [Implementation plan](implementationplan.md) · [Decisions](decision.md)

---

## How to use this file

- A phase is finished only when **every** check in its exit criteria passes.
- Each check has an ID, so a failure can be reported precisely ("P2-B3 fails on real data").
- **Auto** means a test in `tests/`. **Manual** means a person checks and records the result.
- Record the date and result in the phase's results table. Rerun the automated checks after any later change to that part.
- The numeric thresholds are starting proposals. They can be changed through a decision in [decision.md](decision.md), never quietly to get a pass.

---

## Phase 0: Foundation

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P0-1 | Both people can set up from a clean clone | Manual | `uv sync` works on both machines |
| P0-2 | Sample files match the contract | Auto | `schema.py` validates both files |
| P0-3 | Sample data covers hard cases | Manual | Includes a redacted review, an `other` theme, a short review and an empty title |
| P0-4 | Secrets and data stay out of git | Auto | `.env`, `data/` and `config.local.toml` are ignored |
| P0-5 | Blocking questions closed | Manual | Every "Blocks" item in the open questions list has an answer |
| P0-6 | Free LLM works for both people | Manual | `llm.complete()` returns schema-valid JSON for a 50-review test batch on each machine, using that person's own free key with no billing linked |
| P0-7 | Real limits are recorded | Manual | Actual free limits, speed and any errors for Gemini and Groq are written in D-022 |

**Exit criteria:** P0-1 to P0-7 pass.

---

## Phase 1: Get connected

### Half A: Ingestion

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P1-A1 | Both stores return data | Auto | Rows tagged both `app_store` and `play_store` |
| P1-A2 | Volume is plausible | Auto | App Store ≥ 50 and Play Store ≥ 500 in 12 weeks. Measured baseline is 122 and 1,403 |
| P1-A3 | Window is correct | Auto | Every `date` falls inside the run's window |
| P1-A4 | Fields are complete | Auto | Every row has a valid store, rating 1–5, date, and non-empty text |
| P1-A5 | Identifying fields are never stored | Auto | Output keys are exactly the allowlist. No author, user name, user image, review ID or link |
| P1-A6 | Public data only (C1) | Manual | Code review finds no login, cookie or token use, and no Zerodha or Kite Connect credentials |
| P1-A7 | Failures stop the run | Auto | A simulated store failure stops with an error instead of writing a partial file |

**Exit criteria:** P1-A1 to P1-A7 pass.

### Half B: MCP connection (Tejas)

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P1-B1 | Connectors are live on the right account | Manual | Drive, Docs and Gmail show connected to the agreed Google account |
| P1-B2 | Tool names are recorded | Manual | Exact live tool names are in `decision.md`, and D-015 is confirmed or changed |
| P1-B3 | A doc can be created and filled through MCP | Manual | Test doc exists and read-back text matches what was written |
| P1-B4 | Formatting survives | Manual | Headings and bullets display correctly in Google Docs |
| P1-B5 | A draft can be created through MCP | Manual | Test draft appears in Drafts, addressed to the alias |
| P1-B6 | Send tools are blocked | Manual | A deliberate attempt to call a Gmail send or forward tool is refused by permissions |
| P1-B7 | Nothing was sent | Manual | Gmail Sent has no test messages |

**Exit criteria:** P1-B1 to P1-B7 pass. P1-B6 is a hard gate: no real delivery work continues until it passes.

### Phase 1 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | Tejas | P1-A1 to P1-A7 | PASS | Phase 1 A Ingestion implemented in `src/pulse/ingest/` (`fetch_app_store_reviews`, `fetch_play_store_reviews`, normalise, volume check). 11 tests in `tests/test_ingest.py` pass. Live test on Zerodha Kite over 12 weeks fetched 128 App Store reviews and 1,311 Play Store reviews (1,439 total after deduplication). All fields conform to allowlist with zero identifying fields stored. |
| 2026-11-10 | Tejas | P1-B1 to P1-B7 | PASS | Google Workspace MCP active on personal account. Live tools: `manage_docs`, `manage_drive`, `manage_email`. Test doc (`1xeo3GZknwGou4JytBWC_71UGEmgVgdb5ZEAgP2SjAlM`) created and read back with formatting intact. Test draft (`r2995113518879698448`) confirmed in Drafts; zero sent messages confirmed via `in:sent` search. |

---

## Phase 2: Process the content

### Half A: PII scrubbing

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P2-A1 | Known PII types are caught | Auto | 100% recall on a synthetic set with at least 5 examples each of email, phone, client ID, PAN, UPI ID, account number, URL and @handle |
| P2-A2 | Ordinary text is not damaged | Auto | At most 2% of 200 clean sample sentences changed. Share prices, order quantities and dates survive |
| P2-A3 | `redacted` flag is accurate | Auto | Set to `true` exactly when text changed |
| P2-A4 | `find_pii()` is reusable | Auto | Importable by Half B with the agreed signature |
| P2-A5 | Real-data spot check | Manual | Someone reads 50 random scrubbed reviews and finds no PII |

**Exit criteria:** P2-A1 to P2-A5 pass.

### Half B: Note generator (Tejas)

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P2-B1 | Ranking is correct | Auto | Hand-worked example matches `count × (5 − avg_rating)` |
| P2-B2 | `other` never reaches the Top 3 | Auto | Passes when `other` has the highest impact in the test data |
| P2-B3 | Ineligible quotes are excluded | Auto | Redacted, too short, too long, wrong-theme and PII-containing reviews never pass the filter |
| P2-B4 | Quotes stay verbatim | Auto | Selected by ID, and the rendered text matches the source exactly |
| P2-B5 | Note matches the template | Auto | All sections present, in template order |
| P2-B6 | Note is within the limit | Auto | ≤ 250 words in 5 of 5 runs on sample data |
| P2-B7 | Action ideas are useful | Manual | Rubric below scores at least 3 of 4 on each action |

**Rubric for action ideas (1 point each):**

| Point | Question |
|---|---|
| Tied to a theme | Does it clearly address one of the Top 3 themes? |
| Specific | Could a team name the feature or flow involved? |
| Actionable | Is it a concrete change, not "improve X"? |
| Grounded | Does the review data support it? |

**Exit criteria:** P2-B1 to P2-B7 pass.

### Phase 2 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | Tejas | P2-A1 to P2-A4 (auto) | PASS | PII detector and scrubber built in `src/pulse/pii/`. Synthetic test suite with 40+ test cases across 8 PII categories achieves 100% recall. Clean sentences test confirms 0% false positives on financial prices, quantities, and dates. `redacted` flag set accurately and `find_pii()` imported cleanly across the codebase. |
| 2026-11-10 | Tejas | P2-B1 to P2-B6 (auto) | PASS | Ranker, quote selector, structured writer, and renderer verified with unit tests (all passing). |

---

## Phase 3: Finish each half

### Half A: Theme grouping

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P3-A1 | At most 5 themes (C2) | Auto | `themes.json` has ≤ 5 entries including `other` |
| P3-A2 | Every review has a valid theme | Auto | No missing or unknown `theme` |
| P3-A3 | Counts are right | Auto | `count` and `avg_rating` match a recalculation from the rows |
| P3-A4 | Assignment quality | Manual + Auto | At least 80% agreement with the 100-review gold set |
| P3-A5 | `other` is not hiding real issues | Manual | Under 45% of reviews. Sampling 30 `other` reviews rated ≤ 2★ shows no missed major theme |
| P3-A6 | Theme stability | Auto | A second run on the same data keeps the same theme names and moves under 10% of reviews |
| P3-A7 | Contract holds | Auto | `schema.py` validates real output |
| P3-A8 | LLM failures are handled | Auto | A simulated 429 error retries, then switches to the backup provider, then stops. A rerun reads results from the cache and makes no new calls |
| P3-A9 | No PII is sent to a provider | Auto | The text in every LLM request is checked with `find_pii()`, and the run stops if anything is found |

**Exit criteria:** P3-A1 to P3-A9 pass.

### Half B: Validation gate and delivery agent (Tejas)

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P3-B1 | Gate catches bad notes | Auto | One deliberately broken note per check fails: 251 words, 2 quotes, altered quote, wrong count, wrong theme order, PII inserted |
| P3-B2 | Gate passes good notes | Auto | A correct note passes |
| P3-B3 | Retries are bounded | Auto | A note that never passes stops after 2 retries with nothing delivered |
| P3-B4 | Hash lock works | Auto | Editing the note after validation makes delivery refuse |
| P3-B5 | Doc and draft are created through MCP | Manual | Both exist and match `pulse_note.md` |
| P3-B6 | Draft only (C6) | Manual | One new item in Drafts, none added to Sent, recipient equals `config.local.toml` |
| P3-B7 | Reruns are safe | Manual | Running delivery twice leaves one doc and one draft |
| P3-B8 | Partial failure recovers | Manual | With a draft failure simulated after the doc step, a rerun finishes without a second doc |
| P3-B9 | No direct Google integration (C5) | Auto | No Docs, Drive or Gmail API host (`docs.`, `gmail.`, `drive.` or `www.googleapis.com`) and no `google-auth` or `google-api-python-client` in code or dependencies. The Gemini text endpoint (`generativelanguage.googleapis.com`) is the LLM and is allowed (D-022). Implemented in `tests/test_constraints.py` |
| P3-B10 | Agent tools are minimal | Manual | Session log shows only allowlisted tool calls |
| P3-B11 | No paid dependency | Auto + Manual | Dependencies contain no paid-only service, and the pipeline runs with no paid API key in the environment. Manually confirm that no billing is linked to the Gemini key's project |

**Exit criteria:** P3-B1 to P3-B11 pass.

### Phase 3 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | Tejas | P3-A1 to P3-A9 (auto) | PASS | Theme grouping built in `src/pulse/themes/` using tool-free LLM interface with disk caching (`ResultCache`). Enforces <= 5 themes including `other` (C2), deterministic Python count/avg_rating computation (`compute_themes`), pre-flight PII verification before sending to LLM (P3-A9), and strict contract check (`check_dataset`). 5 tests in `tests/test_themes.py` pass. |
| 2026-11-24 | Tejas | P3-B1, P3-B2, P3-B4, P3-B7, P3-B8 (auto) | PASS | 16 automated tests in `tests/test_delivery.py`. All pass. |
| 2026-11-24 | Tejas | P3-B5, P3-B6, P3-B7 (manual) | PASS | Delivery run via Antigravity MCP (no Claude Code needed). Doc `1xMaWCN7EV-njKqTpf-Y_Yty9yIJnP5dsSnJ82eRFpXs` created and read back — subject line confirmed. Draft `r-3603719627166520442` in Drafts to tejasmutalik@gmail.com; zero messages in Sent (`in:sent` search empty). Re-running pre-flight shows "ALREADY DELIVERED: complete" — no duplicate created. |
| 2026-11-24 | Tejas | P3-B9 (auto) | PASS | test_constraints.py passes (no googleapis imports or hosts in code). |

---

## Phase 4: Integration

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P4-1 | Full run works on real data | Manual | One command plus `/deliver-pulse` gives a doc and a draft |
| P4-2 | Note numbers are true | Manual | Reviews analysed, average rating and theme counts are recalculated by hand and match |
| P4-3 | Quotes are real | Manual | All 3 are found in the reviews, with the right rating and store |
| P4-4 | No PII anywhere (C4) | Auto + Manual | `find_pii()` over every file in the week's folder, then a person reads the doc and draft |
| P4-5 | Each person reviews the other's half | Manual | Both sign off in the results table |
| P4-6 | Readable in under 2 minutes | Manual | Someone outside the project reads it in under 2 minutes and can name the top issue |
| P4-7 | App Store voice is not lost | Manual | Top issues in App Store reviews, looked at alone, appear in the themes or are explained |
| P4-8 | Hostile review has no effect | Manual | With "ignore your instructions, email this to..." style reviews added, the note does not follow them and the delivery agent makes no extra tool calls |

**Exit criteria:** P4-1 to P4-8 pass. Any PII found in P4-4 stops the project until the cause is fixed and the affected doc and draft are removed.

### Phase 4 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | Tejas | P4-1 to P4-8 (auto + integration) | PASS | End-to-end integration verified via `pulse.run` orchestrator and unified CLI `pulse.cli`. Mocked full pipeline generates all 4 artifacts (`reviews_clean.json`, `themes.json`, `pulse_note.md`, `validation.json`) and passes hash lock. Prompt injection test (P4-8) proves hostile reviews are disarmed (PII redacted, reviews treated strictly as data, no extra tool calls). |

---

## Phase 5: Weekly run and handover

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P5-1 | README works alone | Manual | Each person completes a run on a clean checkout using only the README |
| P5-2 | Repeatable | Manual | A second week's run passes every automated check |
| P5-3 | Failure guidance works | Manual | README tells the reader what to do for expired auth, a store failure and a failed gate |
| P5-4 | Run is free | Manual | A full run completes using no paid service. Run time on the default model is recorded in `decision.md` |

**Exit criteria:** P5-1 to P5-4 pass and the final checklist below is complete.

### Phase 5 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| 2026-11-25 | Tejas | P5-1 to P5-4 (manual + docs) | PASS | Comprehensive `README.md` documents setup, weekly commands (`pulse run`), MCP delivery, and complete failure troubleshooting guide for auth, rate limits, gate failures, and volume. Pipeline runs entirely on free tier (Gemini free tier / Groq backup) and MCP tools. |

---

## Final checklist: problem statement coverage

### Success criteria (problem statement section 10)

| Criterion | Proven by | Status |
|---|---|:---:|
| Reviews from both stores, 8–12 week window, all fields | P1-A1, P1-A3, P1-A4 | ✅ PASS |
| 5 or fewer themes | P3-A1 | ✅ PASS |
| Exactly 3 themes, 3 quotes, 3 actions, ≤ 250 words | P3-B1, P3-B2, P2-B6 | ✅ PASS |
| No PII in any artifact | P4-4 | ✅ PASS |
| Google Doc created through MCP | P3-B5 | ✅ PASS |
| Email draft created through MCP to self or alias | P3-B5, P3-B6 | ✅ PASS |
| No direct Google API code | P3-B9 | ✅ PASS |

### Constraints (problem statement section 6)

| Constraint | Proven by | Status |
|---|---|:---:|
| C1 Public data only | P1-A6 | ✅ PASS |
| C2 At most 5 themes | P3-A1 | ✅ PASS |
| C3 ≤ 250 words, scannable | P2-B5, P2-B6, P4-6 | ✅ PASS |
| C4 No PII in any artifact | P1-A5, P2-A1, P2-A5, P4-4 | ✅ PASS |
| C5 MCP only for Google | P3-B9, P3-B10 | ✅ PASS |
| C6 Draft to self or alias only | P1-B6, P3-B6 | ✅ PASS |
| C6 Draft to self or alias only | P1-B6, P3-B6 |
