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
| P0-4 | Secrets and data stay out of git | Auto | `.env` and `data/` are ignored |
| P0-5 | Blocking questions closed | Manual | Every "Blocks" item in the open questions list has an answer |
| P0-6 | Free LLM works on both machines | Manual | `llm.complete()` returns schema-valid JSON for a test prompt on each machine, with no paid API key set |

**Exit criteria:** P0-1 to P0-6 pass.

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
| P1-A6 | Public data only (C1) | Manual | Code review finds no login, cookie or token use |
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
| | | | | |

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
| | | | | |

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

**Exit criteria:** P3-A1 to P3-A7 pass.

### Half B: Validation gate and delivery agent (Tejas)

| ID | Check | Method | Pass condition |
|---|---|---|---|
| P3-B1 | Gate catches bad notes | Auto | One deliberately broken note per check fails: 251 words, 2 quotes, altered quote, wrong count, wrong theme order, PII inserted |
| P3-B2 | Gate passes good notes | Auto | A correct note passes |
| P3-B3 | Retries are bounded | Auto | A note that never passes stops after 2 retries with nothing delivered |
| P3-B4 | Hash lock works | Auto | Editing the note after validation makes delivery refuse |
| P3-B5 | Doc and draft are created through MCP | Manual | Both exist and match `pulse_note.md` |
| P3-B6 | Draft only (C6) | Manual | One new item in Drafts, none added to Sent, recipient equals `config.toml` |
| P3-B7 | Reruns are safe | Manual | Running delivery twice leaves one doc and one draft |
| P3-B8 | Partial failure recovers | Manual | With a draft failure simulated after the doc step, a rerun finishes without a second doc |
| P3-B9 | No direct Google integration (C5) | Auto | No `googleapis.com`, `google-auth` or `google-api-python-client` in code or dependencies |
| P3-B10 | Agent tools are minimal | Manual | Session log shows only allowlisted tool calls |
| P3-B11 | No paid dependency | Auto | Dependencies contain no paid-only service, and the pipeline runs with no paid API key in the environment |

**Exit criteria:** P3-B1 to P3-B11 pass.

### Phase 3 results

| Date | Run by | Checks | Result | Notes |
|---|---|---|---|---|
| | | | | |

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
| | | | | |

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
| | | | | |

---

## Final checklist: problem statement coverage

### Success criteria (problem statement section 10)

| Criterion | Proven by |
|---|---|
| Reviews from both stores, 8–12 week window, all fields | P1-A1, P1-A3, P1-A4 |
| 5 or fewer themes | P3-A1 |
| Exactly 3 themes, 3 quotes, 3 actions, ≤ 250 words | P3-B1, P3-B2, P2-B6 |
| No PII in any artifact | P4-4 |
| Google Doc created through MCP | P3-B5 |
| Email draft created through MCP to self or alias | P3-B5, P3-B6 |
| No direct Google API code | P3-B9 |

### Constraints (problem statement section 6)

| Constraint | Proven by |
|---|---|
| C1 Public data only | P1-A6 |
| C2 At most 5 themes | P3-A1 |
| C3 ≤ 250 words, scannable | P2-B5, P2-B6, P4-6 |
| C4 No PII in any artifact | P1-A5, P2-A1, P2-A5, P4-4 |
| C5 MCP only for Google | P3-B9, P3-B10 |
| C6 Draft to self or alias only | P1-B6, P3-B6 |
