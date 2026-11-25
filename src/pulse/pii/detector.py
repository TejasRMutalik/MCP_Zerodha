"""Comprehensive PII detection for app reviews (A2.1).

Covers:
- Email addresses
- Indian phone numbers (+91, 10-digit mobile starting with 6-9)
- Zerodha client IDs (e.g. AB1234, TK4021)
- Indian PAN card numbers (e.g. ABCDE1234F)
- UPI IDs (e.g. user@okhdfcbank, name@upi, 9876543210@paytm)
- Demat / Bank account numbers (9-18 digits or IN30/120 BO IDs)
- URLs (http://, https://, www.)
- Social @handles (@username)

Designed specifically to avoid false positives on:
- Share prices (e.g. 2450.50, ₹150)
- Order quantities (e.g. 100 shares, 500 qty)
- Dates (e.g. 2026-11-25, 24/11/2026)
- App versions (v3.5.1)
"""

from __future__ import annotations

import re
from typing import NamedTuple

from .models import PIIMatch


class PatternRule(NamedTuple):
    type: str
    regex: re.Pattern


# 1. URL: web addresses
_RE_URL = re.compile(
    r"\b(?:https?://[^\s/$.?#].[^\s]*|www\.[^\s/$.?#].[^\s]*)\b",
    re.IGNORECASE,
)

# 2. Email: standard email format (dot in domain)
_RE_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

# 3. UPI ID: username@bank/handle (e.g. user@okhdfcbank, 9876543210@paytm, user@upi, user@ybl)
_RE_UPI = re.compile(
    r"\b[A-Za-z0-9._%+-]{2,64}@(?!gmail|yahoo|hotmail|outlook|icloud|proton|aol)([A-Za-z]{2,30})\b",
    re.IGNORECASE,
)

# 4. PAN Card: 5 letters, 4 digits, 1 letter
_RE_PAN = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
)

# 5. Zerodha Client ID: 2 letters followed by 4 digits (e.g. AB1234), or prefixed by id/client id
_RE_CLIENT_ID = re.compile(
    r"(?:\b(?:client\s*id|user\s*id|kite\s*id|zerodha\s*id)[\s:=]+([A-Za-z0-9]{6})\b)|\b([A-Z]{2}[0-9]{4})\b",
    re.IGNORECASE,
)

# 6. Indian Phone: 10 digits starting with 6, 7, 8, or 9; optionally with +91 or 0 prefix
# Uses negative lookahead and lookbehind for digits and dots so share prices (2450.50) are never touched
_RE_PHONE = re.compile(
    r"(?<![\d\w.])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?![\d\w.])|(?<![\d\w.])0[6-9]\d{9}(?![\d\w.])",
)

# 7. Demat / Bank Account: 9 to 18 consecutive digits or CDSL/NSDL 16-character BO ID
# Specifically guarded against dates (YYYY-MM-DD) and stock quantities
_RE_ACCOUNT = re.compile(
    r"\b(?:IN(?:30)?\d{12,14}|120\d{13,14})\b|(?<![\d\w.-])\d{11,18}(?![\d\w.-])|(?:\b(?:acc(?:ount)?(?:\s*no|\s*number)?|a/c|bo\s*id)[\s:=]+([A-Za-z0-9]{8,18})\b)",
    re.IGNORECASE,
)

# 8. @handle: social handles like @zerodhaonline, @nithin0dha
_RE_HANDLE = re.compile(
    r"(?<![\w])@([A-Za-z0-9_]{3,30})\b",
)

RULES: list[PatternRule] = [
    PatternRule("url", _RE_URL),
    PatternRule("email", _RE_EMAIL),
    PatternRule("upi", _RE_UPI),
    PatternRule("pan", _RE_PAN),
    PatternRule("client_id", _RE_CLIENT_ID),
    PatternRule("phone", _RE_PHONE),
    PatternRule("demat_account", _RE_ACCOUNT),
    PatternRule("handle", _RE_HANDLE),
]


def find_pii(text: str) -> list[PIIMatch]:
    """Scan text and return all non-overlapping PIIMatch objects in text order."""
    if not text:
        return []

    raw_matches: list[PIIMatch] = []

    for rule in RULES:
        for m in rule.regex.finditer(text):
            # For patterns with capture groups (e.g. client ID prefix), pick the non-empty group if applicable
            start, end = m.start(), m.end()
            match_text = m.group(0)

            # Special refine for client_id regex group 1 or 2
            if rule.type == "client_id":
                if m.group(1):
                    start = m.start(1)
                    end = m.end(1)
                    match_text = m.group(1)
                elif m.group(2):
                    start = m.start(2)
                    end = m.end(2)
                    match_text = m.group(2)

            # Special refine for account regex group 1
            elif rule.type == "demat_account" and m.lastindex and m.group(m.lastindex):
                start = m.start(m.lastindex)
                end = m.end(m.lastindex)
                match_text = m.group(m.lastindex)

            raw_matches.append(PIIMatch(rule.type, match_text, start, end))

    # Sort matches by start position, then by longest match first
    raw_matches.sort(key=lambda x: (x.start, -(x.end - x.start)))

    # Resolve overlapping spans (greedy left-to-right)
    filtered: list[PIIMatch] = []
    last_end = -1
    for m in raw_matches:
        if m.start >= last_end:
            filtered.append(m)
            last_end = m.end

    return filtered
