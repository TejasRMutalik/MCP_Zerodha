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

### Still open

These cannot be settled from here: each needs a person or an outside party.

| # | Question | Owner | Blocks |
|---|---|---|---|
| Q2 | Which Google account owns the doc and draft? Only Tejas can sign the Docs and Gmail connectors in. Check which account the Drive connector already uses | Tejas | Phase 1 (B) |
| Q4 | Can the teammate's machine run a local model? Tejas's can (D-020). The teammate runs the hardware check in D-020 and posts the result. If it cannot, they use the free hosted option | Teammate | Phase 2 |
| Q5 | Is an unofficial Play Store library acceptable to whoever assesses this milestone? Work continues on the assumption it is, with the fallback in D-006 | Tejas | Not blocking |
| Q6 | Teammate's name, for the owner fields | Tejas | No |
| Q8 | Does the teammate agree with D-019, D-020 and D-021? | Teammate | Phase 0 |

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
- **Why:** `google-play-scraper` is a Python library, and Ollama has a Python client. Python 3.13 and uv are on Tejas's machine. The teammate's setup still needs checking.

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
- **Risk:** Free tiers can change their limits or terms. Where a free tier is used (D-020), check its current terms first, and the pipeline must stop instead of switching to a paid service (eval P3-B11).

### D-020: Swappable LLM interface, free local model by default

- **Date:** 2026-11-06 · **Status:** Proposed · **Owner:** Both
- **Decision:** All LLM calls go through one function, `llm.complete(prompt, schema)`, in `src/pulse/llm/`. The default provider is a local model served by **Ollama**. An optional free hosted tier can be added as a second provider for a machine that cannot run the local model.
- **Why:** A local model costs nothing, has no rate limits or keys, and review text stays on the machine. One interface means a provider change never touches the rest of the code, and each person can use whichever works on their hardware.
- **Model choice:** Not fixed yet. In Phase 3 (task A3.7) each available model is scored on the 100-review gold set, and the best one that runs on both machines is recorded here.
- **Checked 2026-11-06 against Ollama's docs:** a JSON schema goes in the `format` field (Python: `format=Model.model_json_schema()`), and `options` accepts `temperature` and `seed`. The docs recommend temperature 0 for more deterministic output. Whether that gives identical runs is still tested by eval P3-A6. Ollama's cloud does not support structured outputs, so only a local server is used.
- **Candidate models** (download sizes from Ollama's library): `qwen3:4b` 2.5 GB, `gemma3:4b` 3.4 GB, `llama3.2:3b` 2.0 GB, and the larger `qwen3:8b` 5.2 GB.
- **Tejas's machine:** 15.7 GB RAM, i5-12450H, RTX 3050 Laptop GPU with 4 GB video memory. The 2–3.4 GB models should fit on the GPU. The 8B model would spill onto the CPU and run slowly. Ollama is not installed yet.
- **Teammate's hardware check** (PowerShell on Windows). Post the result in the repo or chat:

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
