# Weekly App Review Pulse (Zerodha Kite)

**Project Owner:** Tejas R Mutalik · **Version:** 1.0.0 · **Milestone:** 2

An automated, privacy-first review intelligence pipeline that turns 8–12 weeks of public Apple App Store and Google Play Store reviews for **Zerodha Kite** into a scannable, one-page executive note ($\le 250$ words), publishes it as a formatted **Google Doc**, and drafts a **Gmail** message to self.

Built strictly with **free resources only** ([D-019](docs/decision.md#d-019-free-resources-only)), **zero direct Google API code** ([C5](problemstatement.md#6-constraints)), **no Zerodha / Kite Connect credentials** ([D-023](docs/decision.md#d-023-no-zerodha-or-kite-connect-api-keys)), and **Model Context Protocol (MCP)** integration for all Google Workspace operations.

---

## 🏗️ System Architecture

```
                  PUBLIC REVIEW SOURCES
                 ┌──────────────────────┐
                 │ Apple App Store RSS  │ (in storefront, pages 1–10)
                 │ Google Play Scraper  │ (com.zerodha.kite3, lang=en)
                 └──────────┬───────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ 1. Ingestion (pulse.ingest│ Allowlist fields (rating, title, text, date)
              │    & normalise.py)        │ 12-wk window, deduplication, volume checks
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │ 2. PII Scrub (pulse.scrub)│ 8 PII categories (phones, emails, PAN,
              │    find_pii() detector    │ client IDs, UPI, accounts, URLs, handles)
              └─────────────┬─────────────┘ Replaces with [redacted], sets redacted: true
                            │
                            ▼
              ┌───────────────────────────┐
              │ 3. Theme Grouping         │ Batched tool-free LLM (Gemini / Groq)
              │    (pulse.themes)         │ 4 product themes + 'other' (≤ 5 themes)
              └─────────────┬─────────────┘ Python computes counts & avg ratings
                            │
            reviews_clean.json + themes.json (Shared Contract)
                            │
                            ▼
              ┌───────────────────────────┐
              │ 4. Note Generator         │ Impact ranking: count × (5 - avg_rating)
              │    (pulse.note)           │ Verbatim quote selection by ID (no names)
              └─────────────┬─────────────┘ Renders template (≤ 250 words)
                            │
                            ▼
              ┌───────────────────────────┐
              │ 5. Validation Gate        │ 6 independent checks (length, shape,
              │    (pulse.validate)       │ ranking, numbers, verbatim, PII)
              └─────────────┬─────────────┘ SHA-256 hash locked in validation.json
                            │
                            ▼
              ┌───────────────────────────┐
              │ 6. Delivery Agent (MCP)   │ Google Workspace MCP (manage_docs,
              │    (pulse.deliver / MCP)  │ manage_drive, manage_email)
              └─────────────┬─────────────┘ Idempotent rerun via delivery.json
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    Google Drive / Docs                Gmail Drafts
   Weekly Pulse Google Doc          Draft to self (0 sent)
```

---

## 🎯 Deliverables & Constraints Coverage

### Problem Statement Deliverables (Section 8)

| # | Deliverable | Status | Location / Artifact |
|---|---|:---:|---|
| **1** | **Review dataset (8–12 wks, PII-free)** | ✅ | Ingested and scrubbed: `data/<week>/reviews_clean.json` |
| **2** | **Theme mapping with counts & ratings** | ✅ | Grouped into $\le 5$ themes: `data/<week>/themes.json` |
| **3** | **Weekly pulse note as a Google Doc** | ✅ | Created via Docs MCP: [Live Google Doc](https://docs.google.com/document/d/1xMaWCN7EV-njKqTpf-Y_Yty9yIJnP5dsSnJ82eRFpXs) |
| **4** | **Gmail draft to self or alias** | ✅ | Created via Gmail MCP: Draft ID `r-3603719627166520442` (0 sent emails) |
| **5** | **Weekly re-run guide** | ✅ | Documented below in this `README.md` |

### Core Constraints (Section 6)

| Constraint | Description | Implementation & Verification |
|---|---|---|
| **C1: Public data only** | No scraping behind logins | Public RSS feed & `google-play-scraper`; no cookies or tokens |
| **C2: At most 5 themes** | Exactly $\le 5$ themes | Schema fixed to 4 product themes + `other` |
| **C3: $\le 250$ words** | Scannable format | Note writer enforces brevity; validation gate blocks $>250$ words |
| **C4: No PII in any artifact** | Zero personal data | Allowlist in ingestion (`extra="forbid"`), regex scrubber replacing with `[redacted]`, pre-LLM scan, gate scan |
| **C5: MCP only for Google** | No direct Google API code | Verified by `tests/test_constraints.py` (0 `googleapis` imports or hosts) |
| **C6: Draft only to self** | No automated email sending | Enforced `draft: true` on `manage_email`; recipient from git-ignored `config.local.toml`; zero messages in Sent |

---

## ⚡ Quickstart

### Prerequisites

- **Python 3.11+**
- **uv** package manager (`pip install uv` or `winget install astral-sh.uv`)
- A free Google AI Studio key for Gemini (no billing linked) and/or free Groq key
- Google Workspace MCP connector configured in Antigravity or Claude Code

### 1. Installation

```bash
git clone https://github.com/TejasRMutalik/MCP_Zerodha.git
cd MCP_Zerodha
uv sync
```

### 2. Configuration & Secrets

1. Copy `.env.example` to `.env` (git-ignored) and add your free LLM keys:
   ```ini
   GEMINI_API_KEY="AIzaSy..."
   GROQ_API_KEY="gsk_..."
   ```

2. Copy `config.example.toml` to `config.local.toml` (git-ignored) and specify your personal email:
   ```toml
   [delivery]
   recipient = "your-email@gmail.com"
   ```

3. Run the automated test suite to verify your setup:
   ```bash
   uv run pytest
   # 122 passed in ~2s
   ```

---

## 📅 The Weekly Run

To execute the entire weekly review pulse, run a single command:

```bash
uv run pulse run --week 2026-W47
```

This single command automatically:
1. Fetches recent reviews from Apple App Store and Google Play Store.
2. Scrubs all PII (emails, phone numbers, client IDs, PANs, accounts, UPIs, URLs, handles).
3. Assigns reviews to themes via batched LLM classification with disk caching.
4. Generates a structured note adhering to the 250-word template with verbatim quotes.
5. Runs the independent validation gate and writes a SHA-256 hash lock to `validation.json`.

### Delivering to Google Docs & Gmail

Once the pipeline completes, deliver the validated note:

#### Option A: Direct via Antigravity MCP (Recommended)
Delivery can be triggered directly in Antigravity chat using the `google-workspace` MCP tools:
```
Deliver the pulse note for week 2026-W47
```
The agent calls `manage_drive` (duplicate search) $\rightarrow$ `manage_docs` (create & write) $\rightarrow$ `manage_email` (`draft: true`).

#### Option B: Via Claude Code Slash Command
In a Claude Code session with Google Workspace connectors active:
```
/deliver-pulse 2026-W47
```

#### Idempotency & Safety
Delivery is strictly idempotent. All generated IDs are recorded in `data/<week>/delivery.json`. If a Google Doc with the week's title already exists or the step is rerun, delivery skips creation and avoids duplicate docs or drafts.

---

## 🔧 Subcommands & Manual Stages

Each stage of the toolchain can also be executed individually:

| Command | Action | Output |
|---|---|---|
| `uv run pulse ingest data/2026-W47` | Ingest reviews from App Store & Play Store | `reviews_ingested.json` |
| `uv run pulse scrub data/2026-W47` | Scrub PII into `[redacted]` | `reviews_clean.json` |
| `uv run pulse themes data/2026-W47` | Group into 5 themes and compute metrics | `reviews_clean.json`, `themes.json` |
| `uv run pulse note data/2026-W47` | Generate weekly pulse note | `pulse_note.md` |
| `uv run pulse validate data/2026-W47` | Run validation gate & lock note SHA-256 | `validation.json` |
| `uv run pulse deliver data/2026-W47` | Pre-flight readiness check | Exits 0 if ready, 1 if blocked |

---

## 🛠️ Failure Playbook & Troubleshooting (P5-3)

| Issue | Cause | Resolution |
|---|---|---|
| **MCP auth expired** | Google OAuth refresh token expired (typically 1–2 weeks) | Run `manage_accounts` with `operation: "authenticate"` and complete Google login. |
| **Validation gate failed** | Note exceeds 250 words or quotes altered | Inspect terminal output for failing check (`length`, `shape`, `numbers`, `verbatim`, `pii`). Re-run `pulse note` to regenerate note. |
| **LLM HTTP 429 Rate Limit** | Free-tier request rate limit reached | The pipeline automatically retries with exponential backoff, then fails over to Groq. Local disk cache (`.cache/llm/`) prevents re-calling cached items. |
| **Review Volume Too Low** | Unofficial scraper returned $<500$ Play Store or $<50$ App Store reviews | Inspect network connection or run with `--no-volume-check` if testing a narrow date range. |
| **Hash Mismatch on Delivery** | Note was manually edited after validation | Delivery will refuse to run. Re-run `uv run pulse validate <folder>` to re-certify the note before delivery. |

---

## 🧪 Testing & Verification

The project includes 122 automated tests covering all functional and compliance requirements:

```bash
# Run all tests
uv run pytest

# Run architectural constraint tests (C5 compliance)
uv run pytest tests/test_constraints.py

# Run PII detection recall & false positive tests
uv run pytest tests/test_pii.py
```

---

## 📄 License & Attribution

Internal milestone project for academic evaluation. Built for Zerodha Kite review analysis. Zero trading credentials or Kite Connect APIs used.
