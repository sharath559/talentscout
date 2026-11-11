"""Rebuild curated offline transport fixtures. This does not call or evaluate Claude."""

import json
from pathlib import Path

from talentscout.agents import fairness_payload, judge_payload
from talentscout.models import Analysis, Judgment
from talentscout.tools import fingerprint, load_candidates, load_job

ROOT = Path(__file__).resolve().parents[1]


def main():
    job = load_job(ROOT / "data/example_job.txt")
    candidates = load_candidates(ROOT / "data/example_resumes.csv")
    # (status, exact source quote, evidence explanation), in rubric order.
    rows = [
        [
            (
                "supported",
                "Built Python APIs for an internal billing service.",
                "Direct evidence of Python backend API implementation.",
            ),
            (
                "supported",
                "Designed PostgreSQL schemas and migrations.",
                "Direct evidence of PostgreSQL database design and migration work.",
            ),
            (
                "supported",
                "Wrote pytest integration tests for payment workflows.",
                "Explicit automated backend integration testing.",
            ),
            (
                "supported",
                "Operated production services and handled on-call incidents.",
                "Explicit production operations and incident response work.",
            ),
        ],
        [
            (
                "supported",
                "Built Python APIs for a document management service.",
                "Direct evidence of Python backend API implementation.",
            ),
            (
                "supported",
                "Designed PostgreSQL schemas and migrations.",
                "Explicit PostgreSQL design and migration work.",
            ),
            (
                "partial",
                "Wrote unit tests for utility functions during a training project.",
                "Some automated testing is documented; backend test scope is unclear.",
            ),
            (
                "not_stated",
                None,
                "Production operation ownership is not stated; ask the candidate.",
            ),
        ],
        [
            (
                "supported",
                "Built Python APIs for a community project.",
                "Explicit Python API work; project context does not reduce credit.",
            ),
            ("not_stated", None, "SQLite is documented, but PostgreSQL experience is not stated."),
            (
                "supported",
                "Wrote pytest integration tests for API endpoints.",
                "Explicit automated backend testing of API endpoints.",
            ),
            (
                "not_stated",
                None,
                "Production operation ownership is not stated; ask the candidate.",
            ),
        ],
        [
            (
                "partial",
                "Completed a Python tutorial with basic exercises.",
                "Python exposure is documented, but backend API implementation is not stated.",
            ),
            ("not_stated", None, "PostgreSQL experience is not stated; ask the candidate."),
            (
                "partial",
                "Wrote automated browser tests for the frontend.",
                "Automated tests are documented; backend testing is not stated.",
            ),
            (
                "not_stated",
                None,
                "Production operation ownership is not stated; ask the candidate.",
            ),
        ],
    ]
    fixtures = {}
    analyses = []
    for candidate, row in zip(candidates, rows, strict=True):
        output = {
            "candidate_id": candidate.id,
            "evidence": [
                {
                    "criterion_id": criterion.id,
                    "status": status,
                    "quotes": [quote] if quote else [],
                    "rationale": reason,
                }
                for criterion, (status, quote, reason) in zip(job.criteria, row, strict=True)
            ],
        }
        analyses.append(Analysis.model_validate_json(json.dumps(output)))
        payload = {
            "job": job.model_dump(mode="json"),
            "candidate_id": candidate.id,
            "resume": candidate.resume,
        }
        fixtures[f"analyzer:{candidate.id}"] = {
            "input_sha256": fingerprint(payload),
            "output": output,
        }
    reasons = [
        "Evidence covers all four criteria. A human should verify depth and context.",
        "Python and PostgreSQL are documented; test scope is partial and operations is not stated.",
        "Python APIs and backend tests are documented; PostgreSQL and operations are not stated.",
        "Some Python and automated testing exposure is documented; "
        "backend depth needs clarification.",
    ]
    judgment = Judgment.model_validate(
        {
            "ranking": [
                {"candidate_id": candidate.id, "reason": reason}
                for candidate, reason in zip(candidates, reasons, strict=True)
            ]
        }
    )
    fixtures["judge"] = {
        "input_sha256": fingerprint(judge_payload(job, analyses)),
        "output": judgment.model_dump(mode="json"),
    }
    fixtures["fairness"] = {
        "input_sha256": fingerprint(fairness_payload(job, candidates, analyses, judgment)),
        "output": {
            "findings": [],
            "human_review_required": True,
            "summary": "No specific concern flagged in this curated demo. This is not a "
            "fairness certification; a person must review all evidence and missing context.",
        },
    }
    fixtures["hello"] = {
        "input_sha256": fingerprint({"action": "hello"}),
        "output": {"message": "Hello from TalentScout. Evidence first, human review always."},
    }
    (ROOT / "data/offline_fixtures.json").write_text(json.dumps(fixtures, indent=2) + "\n")


if __name__ == "__main__":
    main()
