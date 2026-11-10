# Weekly App Review Pulse (Zerodha Kite)

**Project owner:** Tejas R Mutalik · **Version:** 0.1.0 · **Status file for:** 2026-11-07

Turns the last 12 weeks of public Zerodha Kite reviews (App Store RSS + Play
Store scraper) into a one-page weekly note, saves it as a Google Doc, and
creates a Gmail draft. Free resources only — no paid service anywhere, and no
Zerodha API keys ([D-019](docs/decision.md#d-019-free-resources-only),
[D-023](docs/decision.md#d-023-no-zerodha-or-kite-connect-api-keys)).

Related docs: [Problem statement](problemstatement.md) ·
[Architecture](docs/architecture.md) ·
[Implementation plan](docs/implementationplan.md) ·
[Evaluation](docs/eval.md) · [Decisions](docs/decision.md)

---

## Current status: Phase 0 complete, Half B build started

| Area | Status | Notes |
|---|---|---|
| Phase 0 · Foundation | ✅ Mostly done | Scaffold, data contract, samples and LLM interface built and tested |
| Phase 0 · Keys 0.6, 0.8 | ✅ Done | Both providers work on Tejas's and Ace's keys (Groq 2.2–3.5 s, Gemini 3.7–4.6 s per 50-review batch, 50/50 correct); recorded in D-022 |
| Phase 0 · Q9/Q10 limits | ⏭️ Skipped | Not blocking; see D-022 |
| Phase 1 · B: MCP connection | ✅ Done | Google Workspace MCP active on personal account (`tejasmutalik@gmail.com`). Live tools: `manage_docs`, `manage_drive`, `manage_email`. Spikes verified (doc created/read back, draft created in Drafts, zero sent mail). P1-B1 to P1-B7 pass. |
| Phase 1 · A: Ingestion | ⬜ Not started | Teammate's half |
| Phase 2 · B: Note generator | ✅ Done | Ranker, quote filter, note format, writer, renderer and validation gate built with SHA-256 hash lock (PRs #6, #8, #10). All 81 tests pass. |
| Phase 2 · A, Phase 3–5 | ⬜ Not started | — |

**Snapshot (2026-11-10):**

- 81/81 tests pass (`uv run pytest`).
- Q2, Q9, Q10, Q11, Q12 are closed. Open: Q8 (Ace, issue #4), Q5, Q6.

**Earlier snapshot (2026-11-07):**

- 46/46 tests pass (`uv run pytest`).
- Git tree is clean; 6 commits on the default branch.
- Last commit: `82e1370` — "Record Google account decision and connector setup risks".
- 2026-11-07: Ace's 0.6/0.8 batch test done — Gemini (after a key in a fresh AI Studio project) and Groq both pass on Ace's keys: 50/50 labels, 2.2–4.6 s per 50-review batch, no 429s. Gemini sends no rate-limit headers on either key. Recorded in D-022.

## What is built so far

| Component | Path | State |
|---|---|---|
| Shared data contract | `src/pulse/schema.py` | Built — defines `reviews_clean.json` and `themes.json` |
| Config loading | `src/pulse/config.py` | Built — `config.toml`, `config.local.toml`, `.env` |
| Swappable LLM interface | `src/pulse/llm/` | Built — Gemini default, Groq backup; batching, retry/failover, per-review cache. Ollama optional, not built |
| Sample contract data | `contracts/samples/` | Built — 30 fake reviews, 5 themes |
| Note generator | `src/pulse/note/` | Built — ranker, quote filter, structured note, LLM writer (no tools, quotes by ID), renderer, `python -m pulse.note` (B2.1 to B2.5) |
| Tests | `tests/` | Built — 81 tests (schema, LLM, constraints, ranker, quotes, note writer, validation gate) |
| Validation gate | `src/pulse/validate/` | Built — 6 checks on the finished note, SHA-256 hash lock, `python -m pulse.validate` |
| Ingest, PII, themes, CLI | `src/pulse/…` | **Not built** — planned per implementation plan |
| MCP delivery (`.claude/`) | — | **Not built** — Phase 1 B, after the connectors are attached to the personal account |

## Where this repo is going

The real-data measurement (2026-11-06) confirmed the shape of the work:
Play Store is ~92% of reviews, median review length is 6 words, and the
"other" theme exists because many reviews carry no topic. Next steps are
Phase 1: the App/Play adapters and normaliser (Half A) and the full MCP
connector path with a send-tool denylist (Half B, riskiest item).

## Running locally

```bash
uv sync              # install dependencies (Python >= 3.11)
uv run pytest        # 46 tests, all passing
cp config.example.toml config.local.toml   # add your delivery recipient
```

`.env` holds the LLM API keys (Gemini, Groq). `data/`, `.env` and
`config.local.toml` are git-ignored. A weekly re-run guide is planned for
Phase 5.
