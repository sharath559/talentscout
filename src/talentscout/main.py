"""Command-line entry point."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description="TalentScout candidate review")
    parser.add_argument("--hello", action="store_true")
    parser.parse_args()
    print("Hello from TalentScout. Human judgment stays in control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
