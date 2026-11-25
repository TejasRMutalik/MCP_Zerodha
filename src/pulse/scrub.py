"""CLI alias: python -m pulse.scrub forwards to pulse.pii."""

from pulse.pii.__main__ import main

if __name__ == "__main__":
    raise SystemExit(main())
