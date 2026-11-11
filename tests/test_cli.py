import json
import sys

import pytest

from talentscout.agents import run_pipeline
from talentscout.main import main, review
from talentscout.utils import Audit


def test_json_stdout_is_parseable_and_metrics_use_stderr(capsys):
    assert main(["--offline", "--format", "json", "--metrics"]) == 0
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert report["approval"] == "pending"
    assert json.loads(output.err)["api_calls"] == 0


def test_hello(capsys):
    assert main(["--hello"]) == 0
    assert "Hello" in capsys.readouterr().out


def test_report_is_not_overwritten(tmp_path, capsys):
    output = tmp_path / "report.json"
    assert main(["--output", str(output)]) == 0
    original = output.read_text()
    with pytest.raises(SystemExit):
        main(["--output", str(output)])
    assert output.read_text() == original


def test_bad_input_stops_cleanly(tmp_path, capsys):
    invalid = tmp_path / "job.json"
    invalid.write_text('{"secret_resume_text":"never show me"}')
    assert main(["--job", str(invalid)]) == 2
    assert "never show me" not in capsys.readouterr().err


def test_no_live_key_required_for_default(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["--hello"]) == 0


def test_review_requires_terminal(provider, job, candidates, monkeypatch):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(ValueError, match="interactive terminal"):
        review(run_pipeline(provider, job, candidates), Audit())


@pytest.mark.parametrize(
    "answer, expected", [("yes", "approved_simulation"), ("n", "declined"), ("", "declined")]
)
def test_human_review(provider, job, candidates, monkeypatch, answer, expected):
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda _: answer)
    assert review(run_pipeline(provider, job, candidates), Audit()) == expected


def test_review_cannot_mix_with_json():
    with pytest.raises(SystemExit):
        main(["--format", "json", "--review"])


def test_audit_cannot_overwrite_inputs():
    with pytest.raises(SystemExit):
        main(["--audit-log", "data/example_resumes.csv"])
