"""Compatibility launcher; prefer the installed talent_scout command."""

from talentscout.main import main

if __name__ == "__main__":
    raise SystemExit(main())
