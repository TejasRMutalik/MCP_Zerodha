"""Unified CLI for the pulse toolchain:

    pulse run [--week 2026-W47]
    pulse ingest [folder]
    pulse scrub <input>
    pulse themes <folder>
    pulse note <folder>
    pulse validate <folder>
    pulse deliver <folder>
"""

from __future__ import annotations

import argparse
import sys

from pulse.deliver.__main__ import main as deliver_main
from pulse.ingest.__main__ import main as ingest_main
from pulse.note.__main__ import main as note_main
from pulse.pii.__main__ import main as scrub_main
from pulse.run import main as run_main
from pulse.themes.__main__ import main as themes_main
from pulse.validate.__main__ import main as validate_main


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: pulse <command> [args...]")
        print("Commands: run, ingest, scrub, themes, note, validate, deliver")
        return 1

    cmd, rest = args[0], args[1:]
    commands = {
        "run": run_main,
        "ingest": ingest_main,
        "scrub": scrub_main,
        "themes": themes_main,
        "note": note_main,
        "validate": validate_main,
        "deliver": deliver_main,
    }

    if cmd not in commands:
        print(f"Unknown command: '{cmd}'")
        print(f"Available commands: {', '.join(commands.keys())}")
        return 1

    return commands[cmd](rest)


if __name__ == "__main__":
    raise SystemExit(main())
