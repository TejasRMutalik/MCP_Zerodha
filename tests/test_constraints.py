"""Automated checks for project constraints (eval P3-B9 and P3-B11, C5 and D-019)."""

import re
from pathlib import Path

import pytest

from pulse.config import load_config
from pulse.llm.factory import _CLASSES

ROOT = Path(__file__).resolve().parents[1]

# Google Docs, Drive and Gmail must go through MCP. The Gemini text endpoint
# (generativelanguage.googleapis.com) is the LLM, not Docs or Gmail, and is allowed.
FORBIDDEN_IN_CODE = [
    "docs.googleapis.com",
    "gmail.googleapis.com",
    "www.googleapis.com",
    "drive.googleapis.com",
    "googleapiclient",
    "google.oauth2",
    "google_auth",
    "google-auth",
]
FORBIDDEN_DEPENDENCIES = ["google-api-python-client", "google-auth", "google-auth-oauthlib", "gspread"]


def python_files():
    for folder in ("src", "scripts", "tests"):
        for path in (ROOT / folder).rglob("*.py"):
            if path.name != "test_constraints.py":
                yield path


@pytest.mark.parametrize("needle", FORBIDDEN_IN_CODE)
def test_no_direct_google_docs_or_gmail_code(needle):
    hits = [str(p.relative_to(ROOT)) for p in python_files() if needle in p.read_text(encoding="utf-8")]
    assert hits == [], f"{needle} found in {hits}"


def test_no_google_client_libraries_in_dependencies():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    for name in FORBIDDEN_DEPENDENCIES:
        assert not re.search(rf'["\']{re.escape(name)}\b', pyproject), name


def test_only_free_providers_are_configured():
    configured = set(load_config()["llm"]["providers"])
    assert configured <= set(_CLASSES) == {"gemini", "groq"}


def test_no_zerodha_credentials_are_used():
    for path in python_files():
        text = path.read_text(encoding="utf-8").lower()
        assert "kiteconnect" not in text and "kite_api" not in text, path
