"""Offline regression, explicitly measuring fixture plumbing rather than model quality."""

import json
from pathlib import Path

from talentscout.agents import run_pipeline


def test_curated_demo_regression(provider, job, candidates):
    expected = json.loads((Path(__file__).parents[1] / "data/expected_results.json").read_text())
    result = run_pipeline(provider, job, candidates)
    assert [item.candidate_id for item in result.judgment.ranking] == expected["ranking"]
    assert {key: str(value) for key, value in result.scores.items()} == expected["evidence_points"]
    assert provider.calls == len(candidates) + 2
    assert result.approval_allowed
    assert result.report()["approval"] == "pending"
    assert provider.metrics()["api_calls"] == 0
