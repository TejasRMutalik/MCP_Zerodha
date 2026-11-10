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

### Resolved on 2026-11-06

| # | Question | Outcome |
|---|---|---|
| Q1 | Does "Zerodha" mean the Kite app? | Yes: Kite. See D-001 |
| Q3 | Which recipient for the draft? | Yourself, set in a git-ignored file. See D-021 |
| Q7 | Does the Docs MCP server have a create tool? | No: Google's reference page and a third-party review both list only `read_doc` and `update_doc`. See D-015. Rechecked against the live list in Phase 1 |
| Q4 | Can the teammate's machine run a local model? | It no longer needs to: a hosted free API is the default (D-022). Local Ollama is optional |

### Still open

These cannot be settled from here: each needs a person or an outside party.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q2 | Which Google account owns the doc and draft? Tejas offered his college account, but the teammate makes the final choice. Q11 and Q12 wait for this answer, and the recipient in `config.local.toml` must match it | Teammate | Phase 1 (B) |
| Q11 | The Drive connector in this Claude session is signed in to a different Google account from the project account, so a doc created now would land in the wrong Drive. Reconnect Drive to the project account, then connect Docs and Gmail to the same account | Tejas | Phase 1 (B) |
| Q12 | The project account is a college (Workspace) account. Its admin may block third-party connectors, or the Docs and Gmail Developer Preview servers. If blocked, ask the admin or use a personal Google account for the doc and draft | Tejas | Phase 1 (B) |
| Q9 | Create your own Gemini API key in Google AI Studio **without linking billing**, and read the actual free limits shown there. Also read Google's Gemini terms about professional or business use | Both | Phase 0 |
| Q10 | Create a Groq account and key for the backup, read its limits page, and check whether it asks for a card (the docs did not say). If it needs a card, skip Groq and use local Ollama as the backup | Both | Phase 2 |
| Q5 | Is an unofficial Play Store library acceptable to whoever assesses this milestone? Work continues on the assumption it is, with the fallback in D-006 | Tejas | Not blocking |
| Q6 | Teammate's name, for the owner fields | Tejas | No |
| Q8 | Does the teammate agree with D-019 to D-023? | Teammate | Phase 0 |

---

## Business and scope

### D-001: Product is Zerodha Kite

- **Date:** 2026-11-06 · **Status:** Accepted · **Owner:** Tejas
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
- **Checked 2026-11-06:** Vendor documentation says Google's official reviews API works only for apps you manage in Play Console, so it cannot be used for Kite. Sources disagree on whether scraping public reviews breaches Google's terms, and Google's own policy text was not found. Mitigations: only public fields are kept, no reviewer identifier is ever stored (D-008), raw data is never committed, and the run is weekly and small. **Fallback if it is ruled out:** the App Store feed alone (122 reviews in 12 weeks) plus a manually exported public dataset, with the limits that implies.
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
- **Why:** `google-play-scraper` is a Python library, and the hosted LLM APIs can be called from Python (so can a local Ollama server). Python 3.13 and uv are on Tejas's machine. The teammate's setup still needs checking.

### D-012: LLM model and output format

- **Date:** 2026-11-06 · **Status:** Superseded by D-019 and D-020 (paid API dropped) · **Owner:** Both
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
- **Cost note:** This step needs a Claude Code session on Tejas's account, so it is not free for anyone without one. Half A needs no Claude access at all.

### D-015: Create the doc through Drive, fill it through Docs

- **Date:** 2026-11-06 · **Status:** Accepted, recheck against the live tool list in Phase 1 · **Owner:** Tejas
- **Decision:** Drive `create_file` makes an empty Google Doc. Docs `update_doc` writes the note.
- **Why:** The registry lists only `read_doc` and `update_doc` for the Docs server. Drive `create_file` can create a native Google Doc, so content still goes through the Docs MCP server, matching "create or update".
- **Risk:** Section 10 says "created through the Google Docs MCP server". If the assessor reads that strictly, a Docs server with a create tool is needed.
- **Risk:** Google marks the Docs and Gmail MCP servers as Developer Preview, so their tools may change.

### D-016: Draft-only is enforced by permissions

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** Allow `create_draft` and deny all Gmail send and forward tools by exact name. Take the recipient from `config.local.toml` (D-021).
- **Why:** The Gmail connector's registry listing shows 29 tools, including `forward`, `create_filter` and `delete_label`. C6 should hold even if the agent makes a mistake.
- **Checked 2026-11-06:** Google's reference page for the Gmail MCP server lists 10 tools (`create_draft`, `get_message`, `get_thread`, `label_message`, `label_thread`, `list_drafts`, `list_labels`, `search_threads`, `unlabel_message`, `unlabel_thread`) and none that sends or forwards mail. The connector registry shows 29 tools including `forward`. The two disagree, so the live list decides.
- **Known:** `create_draft` takes `to` as a plain email address (not "Name <email>"), plus `subject` and `body`, and returns only the draft ID.
- **Rule until then:** the allowlist is the real guard, with `create_draft` as the only Gmail tool permitted. The deny rules are a second layer. Task B1.2 records the live tool names here.

### D-017: Delivery is safe to rerun

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** Each run records doc and draft IDs in `delivery.json`, and the agent searches for an existing doc by title first.
- **Why:** A failure between the doc and the draft is the likeliest partial failure, and a rerun must not create duplicates.

### D-019: Free resources only

- **Date:** 2026-11-06 · **Status:** Accepted by Tejas, teammate to confirm · **Owner:** Both
- **Decision:** The project uses no paid service. Every component must run on free tools or free tiers.
- **Why:** Project constraint set by Tejas.
- **Consequence:** The paid Anthropic API in D-012 is dropped. The other parts are already free: App Store RSS (D-005), `google-play-scraper` (D-006), Python and uv (D-004), a private GitHub repo, and the Google connectors on a normal Google account.
- **Risk:** Free tiers can change their limits or terms. Where a free tier is used (D-022), check its current terms first, and the pipeline must stop instead of switching to a paid service (eval P3-B11).

### D-020: Swappable LLM interface, free local model by default

- **Date:** 2026-11-06 · **Status:** Partly superseded by D-022: the interface and the Ollama notes still apply, but the default provider is now a hosted API · **Owner:** Both
- **Decision:** All LLM calls go through one function, `llm.complete(prompt, schema)`, in `src/pulse/llm/`. The default provider is a local model served by **Ollama**. An optional free hosted tier can be added as a second provider for a machine that cannot run the local model.
- **Why:** A local model costs nothing, has no rate limits or keys, and review text stays on the machine. One interface means a provider change never touches the rest of the code, and each person can use whichever works on their hardware.
- **Model choice:** Not fixed yet. In Phase 3 (task A3.7) each available model is scored on the 100-review gold set, and the best one that runs on both machines is recorded here.
- **Checked 2026-11-06 against Ollama's docs:** a JSON schema goes in the `format` field (Python: `format=Model.model_json_schema()`), and `options` accepts `temperature` and `seed`. The docs recommend temperature 0 for more deterministic output. Whether that gives identical runs is still tested by eval P3-A6. Ollama's cloud does not support structured outputs, so only a local server is used.
- **Candidate models** (download sizes from Ollama's library): `qwen3:4b` 2.5 GB, `gemma3:4b` 3.4 GB, `llama3.2:3b` 2.0 GB, and the larger `qwen3:8b` 5.2 GB.
- **Tejas's machine:** 15.7 GB RAM, i5-12450H, RTX 3050 Laptop GPU with 4 GB video memory. The 2–3.4 GB models should fit on the GPU. The 8B model would spill onto the CPU and run slowly. Ollama is not installed yet.
- **Optional hardware check**, only for trying local Ollama (PowerShell on Windows):

```powershell
"{0:N1} GB RAM" -f ((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB); Get-CimInstance Win32_VideoController | Select-Object Name; nvidia-smi --query-gpu=name,memory.total --format=csv
```

  With about 8 GB RAM and no dedicated GPU, a 3–4B model still runs on the CPU, just slowly. Below that, use the hosted option.
- **Risk:** Small local models write weaker notes and label themes less accurately. The validation gate and gold set exist to catch this. If the quality is not good enough, the fallback is the free hosted tier, never a paid one.
- **Risk:** A hosted free tier receives review text. It is public and PII-scrubbed, but some free tiers may use inputs for training, so check the terms before using one. Neither tier's current limits have been verified.
- **Alternative:** Hosted free tier only, which is easier to set up but depends on limits and terms outside our control.

### D-021: Draft recipient is the owner's own address, kept out of git

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Tejas
- **Decision:** The Gmail draft is addressed to the Google account that owns it (self). The address lives in `config.local.toml`, which is git-ignored. A committed `config.example.toml` shows the format.
- **Why:** C6 allows self or an alias, and self needs no extra setup. Keeping the address out of the repo means the teammate and any future public copy never see it.
- **Alternative:** A dedicated alias, which can be swapped in later by editing one file.
- **Update 2026-11-06:** Tejas offered his college Google account, but the teammate will make the final choice (Q2). `config.local.toml` must be updated to match whichever account is chosen. Connector setup is tracked in Q11 and Q12.

### D-022: Hosted free LLM API by default: Gemini first, Groq as backup

- **Date:** 2026-11-06 · **Status:** Proposed (Tejas chose a hosted API; the provider is confirmed by the Phase 0 test) · **Owner:** Both
- **Decision:** The default provider is the **Gemini API free tier** through Google AI Studio. The backup is **Groq** with `gpt-oss-20b` or `gpt-oss-120b`. Local Ollama (D-020) stays as an optional third provider. All three sit behind `llm.complete()`, and provider and model names live in `config.toml`, never in code.
- **Why:** Tejas chose a hosted API for easier setup and better quality than a small local model. Gemini's pricing page lists several Flash and Flash-Lite models as free for input and output, and its docs describe JSON-schema output. Groq's `gpt-oss-20b` and `gpt-oss-120b` are listed as production models with strict JSON-schema output.
- **Checked 2026-11-06 from the providers' official pages** (some pages were truncated and partly summarised by the reading tool):
  - **Gemini:** the exact free limits are not on the docs page and are shown inside AI Studio. Free-tier content is used to improve Google products, and human reviewers may read it. Linking Cloud Billing turns the project into a Paid Service. The terms describe the service as for professional or business use and for people 18 or older.
  - **Groq:** the limits table I found (`gpt-oss` models: 30 requests/min, 1,000/day, 8,000 tokens/min, 200,000 tokens/day) is labelled Developer plan, so the free-plan numbers are unconfirmed. Whether a card is needed was not found. By default no customer data is retained, and no statement about training was found. Structured output cannot be combined with streaming or tool use. `qwen3.8-27b` is a preview model and may be removed.
  - **OpenRouter:** free models are limited to 20 requests/min and 50/day, and structured-output support varies per model. **Mistral:** its free tier could not be verified. Neither was chosen.
- **Rules that keep it working on free tiers:**
  1. Send reviews in batches of about 50 per request, which is roughly 30 requests a week instead of 1,500.
  2. On a 429 error, retry with a growing delay, then switch to the backup provider, then stop. Never switch to a paid service.
  3. Save every result by review ID, so a rerun makes no new calls.
  4. Keep model names in `config.toml` and avoid preview models.
  5. Never link billing to the Gemini key's project.
  6. Send only scrubbed text, so no PII ever reaches a hosted provider.
  7. Each person uses their own key, because limits apply per project or organisation.
- **Implementation:** both providers are called over plain HTTP with `httpx`, not through vendor SDKs, so no Google auth library is installed and the "no direct Google API code" check (P3-B9) stays simple. Ollama is not built.
- **Measured 2026-11-06 on Tejas's keys** (Phase 0 test, one batch of 50 invented sample reviews per call, run with `scripts/llm_batch_test.py`):
  - **Gemini `gemini-3.5-flash-lite`:** 50 of 50 labelled, all matching the sample labels, in 3.5 s. A burst of tiny requests got 15 successes in about 22 s and then HTTP 429, so about **15 requests per minute**. No rate-limit headers are sent, and the 429 carried no wait time. The **daily cap is still unknown** (Q9). Config spaces calls 5 s apart.
  - **Groq `openai/gpt-oss-20b`:** 50 of 50 labelled, all matching, in 2.1 s. The response headers show **1,000 requests per day and 8,000 tokens per minute** for this key, and one 50-review batch used about 1,700 tokens. Whether these are the free-plan limits, and whether Groq asked for a card, is still open (Q10).
  - **Caveat:** the sample reviews are invented and easy, so 50 of 50 shows that the plumbing and JSON-schema output work, not real labelling quality. Task A3.5 measures quality on real reviews, and real reviews are longer, so token counts will rise.
  - **Rough capacity:** 1,500 reviews is about 30 batches. Gemini at 5 s spacing takes about 3 minutes. Groq is limited by tokens, about 30 × 1,700 = 51,000 tokens, so roughly 7 minutes at 8,000 per minute.
- **Measured 2026-11-07 on Ace's keys (Phase 0 test, same script and samples):**
  - **Groq `openai/gpt-oss-20b`:** 50 of 50 labelled, all matching, in 2.2 s; identical result on a repeated run, and 3 runs within a few minutes produced no 429. Headers show limit 1,000 requests and 8,000 tokens/min for this key, with reset-counter windows of roughly 1.5–3 min observed. Token use per 50-review batch was about 1,700 tokens, matching Tejas's measurement.
  - **Groq `openai/gpt-oss-120b`:** 50 of 50 labelled, all matching, in 3.5 s. Both Groq models work on Ace's key.
  - **Gemini `gemini-3.5-flash-lite`: HTTP 403, blocked.** The response says the Gemini API free tier is not available on Ace's key's project and asks to set up billing. Billing is never linked (rule 5), so Gemini stays unavailable on that key until it is moved to a project that includes the free tier.
- **Update 2026-11-07 (Ace, Gemini resolved):** Ace created the key in a fresh AI Studio project and Gemini now works: three 50-review batches in a row returned 50/50 matching labels in 4.6 s, 4.3 s and 3.7 s, with no 429s. Like Tejas's key, it sends no rate-limit headers, so the per-minute and daily caps are still not readable from responses (Q9 remains open). Both default and backup providers now work on both people's keys.
- **Open:** Q9 (Gemini's daily cap, shown in AI Studio; now also Ace's 403 free-tier finding) and Q10 (Groq's card question and free-plan limits; request and token limits are now seen identically on two keys). The final model choice comes from the gold-set comparison (A3.7).
- **Risk:** Free tiers can change limits, terms or models without notice. Hosted providers see review text, though it is public and scrubbed. Whether Gemini's terms suit this project should be read once (Q9).
- **Alternative:** Local Ollama only (D-020), which has no limits or data sharing but needs capable hardware and gives weaker output.

### D-023: No Zerodha or Kite Connect API keys

- **Date:** 2026-11-06 · **Status:** Accepted · **Owner:** Tejas
- **Decision:** The project uses no Zerodha or Kite Connect credentials.
- **Why:** Kite Connect is for trading and account data and has nothing about app reviews. It needs a logged-in Zerodha account, which breaks C1 (public data only, no logins), and a key tied to a trading account could place orders. I believe it is a paid product, though I did not check the price, which would conflict with D-019.
- **Keys in this project:** only the LLM keys, each person's own, in a git-ignored `.env`. Google access goes through the MCP connectors, so there is no Google key in the code.

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
