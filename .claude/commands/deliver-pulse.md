# deliver-pulse

Deliver a validated weekly pulse note to Google Docs and Gmail (Draft).

**Usage in Claude Code:**
```
/deliver-pulse 2026-W45
```

This command is the only place that calls `manage_docs`, `manage_drive`, and
`manage_email`.  The LLM that produced the note has no tools and never reached
this step.  Only the validated note text is passed to these tools (D-013).

---

## Pre-flight checks (run before every delivery)

1. Run the Python pre-flight:

   ```bash
   uv run python -m pulse.deliver .cache/w
   ```

   - Exit 0 means the note is ready.  
   - Exit 1 means delivery must not continue — read the error and stop.

2. Read `.cache/w/delivery.json` (if it exists) to find any IDs already
   written.  Skip steps whose IDs are already present (idempotency, D-017).

3. Read `config.local.toml` for `delivery.recipient`.  The address is never
   printed or logged (D-021).  If the file is missing, stop and ask Tejas to
   create it from `config.example.toml`.

4. Read `.cache/w/pulse_note.md` and confirm it starts with `Subject:`.
   This is the note text that will go into the doc and the email body.

---

## Delivery sequence (D-015, D-016)

Perform the steps below **in order**.  After each step succeeds, immediately
write or update `.cache/w/delivery.json` via:

```bash
# After the doc step:
uv run python -c "
import json, pathlib
p = pathlib.Path('.cache/w/delivery.json')
d = json.loads(p.read_text()) if p.exists() else {}
d.update({'week': '$WEEK', 'note_sha256': '$SHA', 'doc_id': '$DOC_ID', 'doc_title': '$DOC_TITLE'})
p.write_text(json.dumps(d, indent=2))
"
```

Replace `$WEEK`, `$SHA`, `$DOC_ID`, `$DOC_TITLE` with real values.  `$SHA`
comes from `.cache/w/validation.json` → `note_sha256`.

### Step 1 — Duplicate check

Search Google Drive for a doc whose title matches:

```
Zerodha Kite Weekly Review Pulse | <WEEK>
```

Use `manage_drive` with `operation: "search"` and `query: "title='<TITLE>'"`.

- If a doc is found **and** `delivery.json` already has `doc_id`, skip to Step 3.
- If a doc is found but `delivery.json` has no `doc_id`, record its ID and skip to Step 3.
- If no doc is found, continue to Step 2.

### Step 2 — Create the Google Doc

Call `manage_docs` with:

```json
{
  "operation": "create",
  "title": "Zerodha Kite Weekly Review Pulse | <WEEK>"
}
```

Record the returned `documentId` as `doc_id`.  Write `delivery.json`.

### Step 3 — Write the note into the doc

Call `manage_docs` with:

```json
{
  "operation": "write",
  "fileId": "<doc_id>",
  "content": "<full note text from pulse_note.md>"
}
```

Then call `manage_docs` with `operation: "get"` and confirm the read-back
text contains the subject line.  This is the P3-B5 manual check.

### Step 4 — Create the Gmail draft

Skip if `delivery.json` already has `draft_id`.

Call `manage_email` with:

```json
{
  "operation": "send",
  "draft": true,
  "to": "<delivery.recipient from config.local.toml>",
  "subject": "<Subject line from pulse_note.md, without the 'Subject: ' prefix>",
  "body": "<full note text from pulse_note.md>"
}
```

Record the returned draft ID as `draft_id`.  Write `delivery.json` with
`delivered_at` set to the current UTC time.

---

## Final checks (manual, P3-B5 to P3-B8)

After delivery completes, verify:

| Check | How |
|---|---|
| P3-B5 Doc exists and matches | Read back with `manage_docs` `get`, confirm subject line is present |
| P3-B5 Draft exists | List drafts with `manage_email` `listDrafts`, confirm the new ID appears |
| P3-B6 Draft only | Search Gmail `in:sent` — count must not increase |
| P3-B6 Right recipient | Confirm the draft `to` field equals `delivery.recipient` |
| P3-B7 Idempotent | Run the command again — no second doc or draft should be created |

---

## Allowed tools

This command may call **only** the following tools:

| Tool | Allowed operations |
|---|---|
| `manage_docs` | `create`, `write`, `get` |
| `manage_drive` | `search` |
| `manage_email` | `send` (with `draft: true`), `listDrafts` |

**Blocked:** any `manage_email` operation that sends, forwards, or deletes mail.
Never call `manage_email` with `draft: false` or omit the `draft` flag.

---

## Failure handling

| Failure | Action |
|---|---|
| Pre-flight exits 1 | Stop. Fix the note or run `pulse validate` first. |
| Step 2 fails | Stop. Do not continue to Step 4 without a doc ID. |
| Step 3 read-back does not match | Stop. The doc may be blank; check and fix manually. |
| Step 4 fails after Step 2–3 succeeded | Delivery is partial. `delivery.json` has `doc_id` but no `draft_id`. Re-run the command; it will skip Step 2 and retry Step 4. |
| Any MCP error | Stop, report the error verbatim. Never retry silently. |
