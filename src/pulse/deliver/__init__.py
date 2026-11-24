"""Half B Phase 3: delivery agent support.

Delivery is always driven by a human running /deliver-pulse in Claude Code,
never automatically. This module provides:

  is_deliverable()   -- the hash gate (from pulse.validate)
  load_delivery()    -- read delivery.json (None if missing / corrupt)
  save_delivery()    -- write delivery.json
  note_title()       -- canonical Google Doc title for a week

The actual MCP calls (manage_docs, manage_drive, manage_email) are made
directly in the /deliver-pulse command, never from Python code, to satisfy
the no-direct-Google-API constraint (C5, P3-B9).
"""

from .runner import DeliveryRecord, load_delivery, note_title, save_delivery

__all__ = ["DeliveryRecord", "load_delivery", "note_title", "save_delivery"]
