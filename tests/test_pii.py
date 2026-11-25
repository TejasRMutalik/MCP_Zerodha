"""Tests for Phase 2 A: PII scrubbing.

Covers eval.md exit criteria:
P2-A1 Known PII types are caught (100% recall on synthetic set:
      at least 5 examples each of email, phone, client ID, PAN, UPI ID, account number, URL, handle)
P2-A2 Ordinary text is not damaged (at most 2% of clean sentences changed; prices, qtys, dates survive)
P2-A3 redacted flag is accurate (true exactly when text changed)
P2-A4 find_pii() is reusable (importable with agreed signature)
"""

import pytest

from pulse.pii import (
    REDACTED_LABEL,
    find_pii,
    scrub_review,
    scrub_reviews,
    scrub_text,
)


# ---------------------------------------------------------------------------
# Synthetic PII Test Set (P2-A1: >= 5 examples per type, 100% recall)
# ---------------------------------------------------------------------------

SYNTHETIC_PII_SAMPLES = [
    # 1. Emails (5+)
    ("Please reach out at support@fakebroker.com for assistance.", "email"),
    ("My email address is trader.pro99@gmail.com please reply.", "email"),
    ("Contact me via user_test+kite@yahoo.co.in thanks.", "email"),
    ("Send my statements to account123@outlook.com directly.", "email"),
    ("Billing query sent from ceo@zerodha-invest.org yesterday.", "email"),

    # 2. Indian Phone numbers (5+)
    ("Call me immediately on 9876543210 regarding my margins.", "phone"),
    ("My phone is +91 9123456789 please call back.", "phone"),
    ("Helpline contacted at +91-8888877777 during market crash.", "phone"),
    ("Try calling on 07012345678 if the main line is busy.", "phone"),
    ("Mobile number is 9988776655 fix my otp issue.", "phone"),

    # 3. Zerodha Client IDs (5+)
    ("Client id AB1234 has pending fund withdrawal issue.", "client_id"),
    ("My Kite user id is TK4021 please check margin.", "client_id"),
    ("Zerodha ID: ZM9876 trading blocked since morning.", "client_id"),
    ("Login error for user DA5512 after updating the app.", "client_id"),
    ("Cannot place orders with client id: XY7890 please unblock.", "client_id"),

    # 4. PAN Card numbers (5+)
    ("My PAN card ABCDE1234F was verified last month.", "pan"),
    ("Re-KYC asking for PAN: BKPPM4567K again and again.", "pan"),
    ("KYC rejected for PAN number AFZPR9988L without reason.", "pan"),
    ("Submitted tax details with PAN CDEPG3344M online.", "pan"),
    ("Linked Aadhaar with PAN ZXCVB5678N as requested.", "pan"),

    # 5. UPI IDs (5+)
    ("Refund my funds to trader@okhdfcbank right now.", "upi"),
    ("Payment failed on 9876543210@paytm during add funds.", "upi"),
    ("Deposited 5000 via investor@ybl but not credited.", "upi"),
    ("UPI handle is money@axisbank please verify deposit.", "upi"),
    ("Transferred through user123@icici yesterday morning.", "upi"),

    # 6. Demat / Bank Account numbers (5+)
    ("Demat account 1208160012345678 shows missing shares.", "demat_account"),
    ("Transfer money to a/c 91234567890123 immediately.", "demat_account"),
    ("Bank account no: 11223344556677 was debited twice.", "demat_account"),
    ("NSDL BO ID IN30012312345678 pledge request stuck.", "demat_account"),
    ("Account number 501002345678912 is linked to this id.", "demat_account"),

    # 7. URLs (5+)
    ("Check the outage video at https://youtu.be/fakecrash123 right now.", "url"),
    ("Download proof from http://files.example.com/logs/crash.pdf please.", "url"),
    ("Screenshots uploaded to www.dropbox.com/s/error99 today.", "url"),
    ("Read this report at https://tradingcomplaints.in/case?id=123.", "url"),
    ("Refer to guide at http://zerodha.com/help/support-article.", "url"),

    # 8. @handles (5+)
    ("Already reported this to @zerodhaonline on X.", "handle"),
    ("Tagged @nithin0dha about the constant chart freezes.", "handle"),
    ("Support agent @kamath_help promised a fix by 10 AM.", "handle"),
    ("Followed @kite_alerts but received no notification.", "handle"),
    ("Sent DM to @zerodha_support yesterday.", "handle"),
]


def test_p2_a1_synthetic_pii_100_percent_recall():
    """P2-A1: 100% recall across all known PII categories."""
    for text, expected_type in SYNTHETIC_PII_SAMPLES:
        matches = find_pii(text)
        assert len(matches) >= 1, f"Failed to detect {expected_type} in: '{text}'"
        match_types = [m.type for m in matches]
        assert expected_type in match_types, f"Expected '{expected_type}' in {match_types} for '{text}'"


# ---------------------------------------------------------------------------
# P2-A2: Ordinary text is not damaged (Prices, Qtys, Dates survive)
# ---------------------------------------------------------------------------

CLEAN_SAMPLE_SENTENCES = [
    "Bought 100 shares of Reliance at 2450.50 today.",
    "Nifty fell by 250 points, options premium jumped to 145.20.",
    "Order placed for 500 qty at market price 120.",
    "Sold 50 shares at 1250 on 2026-11-25.",
    "App updated to version 3.5.1 on 24/11/2026.",
    "Added 10,000 rupees to funds via netbanking smoothly.",
    "Charts on 15m and 5m timeframe load very fast.",
    "Loss of 1,500 on intraday trade due to stop loss trigger.",
    "Target 2600 hit on Infosys with 25 shares.",
    "Dividend of 15.50 per share credited to account.",
    "Market opened at 24,150.30 and closed at 24,300.",
    "Holding 10 shares of Tata Motors since 2024.",
    "Zerodha Kite is the best trading application in India.",
    "GTT order triggered at 9:15 AM without any latency.",
    "Brokerage is 20 rupees per executed order.",
    "Candlestick chart indicators like MACD and RSI are very clean.",
    "Order executed in 50 milliseconds.",
    "Portfolio return is up by 14.5% this financial year.",
    "Smooth UI and dark mode is pleasing to eyes.",
    "Face ID login takes less than 1 second.",
]


def test_p2_a2_clean_sentences_not_damaged():
    """P2-A2: Clean financial & trading phrases do not trigger false positive PII."""
    changed_count = 0
    for sentence in CLEAN_SAMPLE_SENTENCES:
        matches = find_pii(sentence)
        if matches:
            changed_count += 1

    false_positive_rate = changed_count / len(CLEAN_SAMPLE_SENTENCES)
    assert false_positive_rate <= 0.02, f"False positive rate {false_positive_rate:.1%} exceeds 2% threshold"


# ---------------------------------------------------------------------------
# P2-A3: Redaction Flag & Replacement Accuracy
# ---------------------------------------------------------------------------

def test_p2_a3_scrub_text_replaces_with_redacted_label():
    text = "Contact 9876543210 or user@example.com for PAN ABCDE1234F"
    scrubbed, was_redacted, matches = scrub_text(text)

    assert was_redacted is True
    assert len(matches) == 3
    assert REDACTED_LABEL in scrubbed
    assert "9876543210" not in scrubbed
    assert "user@example.com" not in scrubbed
    assert "ABCDE1234F" not in scrubbed


def test_p2_a3_clean_text_keeps_redacted_false():
    text = "Awesome trading interface and great charts."
    scrubbed, was_redacted, matches = scrub_text(text)

    assert was_redacted is False
    assert len(matches) == 0
    assert scrubbed == text


def test_p2_a3_scrub_review_sets_flag_accurately():
    review_with_pii = {
        "store": "play_store",
        "rating": 1,
        "title": "Broken app",
        "text": "My phone 9876543210 is not receiving OTP",
        "date": "2026-11-20",
        "redacted": False,
    }
    clean_review = {
        "store": "app_store",
        "rating": 5,
        "title": "Smooth",
        "text": "Smooth order execution and fast biometric login",
        "date": "2026-11-21",
        "redacted": False,
    }

    res = scrub_reviews([review_with_pii, clean_review])
    assert res[0]["redacted"] is True
    assert REDACTED_LABEL in res[0]["text"]

    assert res[1]["redacted"] is False
    assert REDACTED_LABEL not in res[1]["text"]


# ---------------------------------------------------------------------------
# P2-A4: find_pii() Signature & Reusability
# ---------------------------------------------------------------------------

def test_p2_a4_find_pii_reusable_signature():
    """P2-A4: find_pii(text) returns truthy list on PII and falsy list on clean text."""
    dirty_result = find_pii("Call 9876543210")
    assert bool(dirty_result) is True
    assert len(dirty_result) == 1

    clean_result = find_pii("Nothing to redact here")
    assert bool(clean_result) is False
    assert len(clean_result) == 0
