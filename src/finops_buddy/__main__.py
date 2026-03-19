"""Allow running as python -m finops_buddy."""

from finops_buddy.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
