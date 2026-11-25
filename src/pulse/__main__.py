"""Entrypoint when running 'python -m pulse <args>'."""

from pulse.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
