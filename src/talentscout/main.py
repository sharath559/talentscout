"""CLI: offline by default, live only by explicit opt-in, approvals always interactive."""

import argparse
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .agents import run_pipeline
from .models import Hello
from .prompts import HELLO
from .providers import ClaudeProvider, OfflineProvider
from .tools import load_candidates, load_job, safe_terminal
from .utils import Audit, Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TalentScout: evidence-first candidate review (offline by default)."
    )
    parser.add_argument("--job", type=Path, default=Path("data/example_job.txt"))
    parser.add_argument("--resumes", type=Path, default=Path("data/example_resumes.csv"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="send input to the Anthropic API")
    mode.add_argument("--offline", action="store_true", help="replay hash-bound demo fixtures")
    parser.add_argument("--fixtures", type=Path, default=Path("data/offline_fixtures.json"))
    parser.add_argument("--hello", action="store_true", help="test provider connectivity")
    parser.add_argument("--budget", help="maximum estimated USD per live run")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--output", type=Path, help="write a JSON report (contains candidate evidence)"
    )
    parser.add_argument("--audit-log", type=Path, help="append metadata-only JSONL events")
    parser.add_argument("--metrics", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="log metadata to stderr")
    parser.add_argument("--review", action="store_true", help="interactive simulated approval")
    return parser


def review(result, audit: Audit) -> str:
    if not result.approval_allowed:
        print("Approval blocked: unresolved review findings.", file=sys.stderr)
        audit.emit("approval_blocked", findings=len(result.fairness.findings))
        return "blocked"
    if not sys.stdin.isatty():
        raise ValueError("--review requires an interactive terminal; piped approval is disabled")
    try:
        answer = input("After inspecting the evidence, approve this simulated shortlist? [y/N] ")
    except EOFError:
        answer = ""
    approved = answer.strip().lower() in {"y", "yes"}
    audit.emit("human_review", decision="approved_simulation" if approved else "declined")
    print("Shortlist approved (simulated action)." if approved else "Aborted by user.")
    return "approved_simulation" if approved else "declined"


def render_text(result) -> None:
    print("\nTALENTSCOUT / EVIDENCE BEFORE RECOMMENDATIONS")
    print(safe_terminal(result.job.title))
    print("\nEvidence points / 100 — documented coverage, not predicted performance\n")
    names = {item.id: item.name for item in result.candidates}
    for index, item in enumerate(result.judgment.ranking, start=1):
        print(
            safe_terminal(
                f"{index}. {names[item.candidate_id]} [{item.candidate_id}]"
                f"  {result.scores[item.candidate_id]:.1f}"
            )
        )
        print(safe_terminal(f"   {item.reason}"))
    for analysis in result.analyses:
        print(safe_terminal(f"\nSource evidence / {analysis.candidate_id}"))
        for evidence in analysis.evidence:
            print(safe_terminal(f"  {evidence.criterion_id}: {evidence.status.value}"))
            for quote in evidence.quotes:
                print(safe_terminal(f'    "{quote}"'))
            print(safe_terminal(f"    {evidence.rationale}"))
    print("\nFairness review / human review required")
    print(safe_terminal(result.fairness.summary))
    for finding in result.fairness.findings:
        print(safe_terminal(f"  [{finding.severity}] {finding.candidate_id}: {finding.detail}"))
    print("\nNo employment action is performed. Review the source resumes and rubric.")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.review and args.format == "json":
        parser.error("--review uses text output; use --output to save the reviewed JSON report")
    if args.audit_log and args.output and args.audit_log.resolve() == args.output.resolve():
        parser.error("audit log and report must use different paths")
    inputs = {
        path.resolve() for path in (args.job, args.resumes, args.fixtures, Path.cwd() / ".env")
    }
    if any(path and path.resolve() in inputs for path in (args.audit_log, args.output)):
        parser.error("report and audit paths must not overwrite input or configuration files")
    if args.output and args.output.exists():
        parser.error("output already exists; choose a new report path")
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    logging.getLogger("talentscout").setLevel(logging.INFO if args.verbose else logging.WARNING)
    # Explicit file only: do not search parent directories for unrelated credentials.
    load_dotenv(Path.cwd() / ".env", override=False)
    audit = Audit(args.audit_log)
    provider = None
    try:
        provider = (
            ClaudeProvider(Settings.from_env(args.budget), audit)
            if args.live
            else OfflineProvider(args.fixtures, audit)
        )
        if args.hello:
            hello = provider.request("hello", HELLO, {"action": "hello"}, Hello)
            print(
                json.dumps(hello.model_dump())
                if args.format == "json"
                else safe_terminal(hello.message)
            )
            return 0
        job, candidates = load_job(args.job), load_candidates(args.resumes)
        audit.emit(
            "run_started",
            mode="live" if args.live else "offline",
            candidates=len(candidates),
            criteria=len(job.criteria),
        )
        result = run_pipeline(provider, job, candidates)
        approval = "pending" if result.approval_allowed else "blocked"
        if args.format == "text":
            print(
                "Mode: LIVE (data sent to Anthropic)"
                if args.live
                else "Mode: OFFLINE (curated fixtures, zero API calls)"
            )
            render_text(result)
        if args.review:
            approval = review(result, audit)
        report = {**result.report(approval), "metrics": provider.metrics()}
        encoded = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
        if args.format == "json":
            print(encoded, end="")
        if args.output:
            # Exclusive creation prevents accidental replacement of input documents or reports.
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(encoded)
        audit.emit("run_completed", approval=approval)
        return 0
    except (OSError, ValueError, KeyboardInterrupt) as exc:
        # Validation errors may echo documents. Emit only their type, never their values.
        message = (
            "invalid input or model response" if isinstance(exc, ValidationError) else str(exc)
        )
        if isinstance(exc, OSError):
            message = "file operation failed; check paths, permissions and existing output files"
        if isinstance(exc, KeyboardInterrupt):
            message = "interrupted; no employment action performed"
        print(f"TalentScout stopped: {safe_terminal(message)}", file=sys.stderr)
        return 130 if isinstance(exc, KeyboardInterrupt) else 2
    finally:
        if provider and (args.metrics or args.verbose):
            print(json.dumps(provider.metrics(), sort_keys=True), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
