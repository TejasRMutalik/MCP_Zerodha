"""Config and secrets loading.

Secrets come from the environment or a git-ignored .env file. They are never
printed, logged or put in exception messages.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load_env(path: Path | str | None = None) -> dict[str, str]:
    """Parse a simple KEY=VALUE file. Missing file gives an empty dict."""
    p = Path(path) if path else ROOT / ".env"
    values: dict[str, str] = {}
    if not p.exists():
        return values
    for raw in p.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_secret(name: str, env_path: Path | str | None = None) -> str | None:
    """Environment variable first, then .env. Empty values count as missing."""
    return os.environ.get(name) or load_env(env_path).get(name) or None


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(root: Path | str = ROOT) -> dict[str, Any]:
    """config.toml, overlaid with config.local.toml when it exists."""
    root = Path(root)
    cfg = tomllib.loads((root / "config.toml").read_text(encoding="utf-8"))
    local = root / "config.local.toml"
    if local.exists():
        cfg = _merge(cfg, tomllib.loads(local.read_text(encoding="utf-8")))
    return cfg
