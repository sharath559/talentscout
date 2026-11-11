import json

import pytest
from pydantic import ValidationError

from talentscout.models import Job
from talentscout.tools import load_candidates, load_job, read_text, safe_terminal, sanitize_resume


def test_contact_removal():
    text = sanitize_resume("Contact someone@example.com or (212) 555-1212. Python APIs.")
    assert "someone@example.com" not in text
    assert "555-1212" not in text
    assert "Python APIs" in text


def test_terminal_escapes_removed():
    assert "\x1b" not in safe_terminal("name\x1b[2J\nforged line")


@pytest.mark.parametrize("mutation", ["weights", "duplicate"])
def test_rubric_integrity(job, mutation):
    value = job.model_dump()
    if mutation == "weights":
        value["criteria"][0]["weight"] = 1
    else:
        value["criteria"][1]["id"] = value["criteria"][0]["id"]
    with pytest.raises(ValidationError):
        Job.model_validate(value)


def test_json_job_round_trip(job, tmp_path):
    path = tmp_path / "job.json"
    path.write_text(json.dumps(job.model_dump()))
    assert load_job(path) == job


@pytest.mark.parametrize(
    "content",
    [
        "",
        "name,resume\nA,Text",
        "candidate_id,name,resume\na,A,short",
        "candidate_id,name,resume\na,A,Extra,columns",
    ],
)
def test_invalid_csv(content, tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(content)
    with pytest.raises(ValueError):
        load_candidates(path)


def test_bounded_file_read(tmp_path):
    path = tmp_path / "large.txt"
    path.write_bytes(b"x" * 512001)
    with pytest.raises(ValueError, match="512 KB"):
        read_text(path)
