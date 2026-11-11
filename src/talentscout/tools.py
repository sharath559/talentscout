"""Local, bounded input tools; no model-controlled file access or execution."""

import csv
import hashlib
import json
import re
from pathlib import Path

from .models import Candidate, Job

MAX_FILE_BYTES = 512_000
MAX_CANDIDATES = 20


def read_text(path: Path) -> str:
    with path.open("rb") as handle:
        content = handle.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise ValueError("input file exceeds 512 KB limit")
    return content.decode("utf-8")


def load_job(path: Path) -> Job:
    """Text format: title, description, then 'criterion: id | weight | description'."""
    raw = read_text(path)
    if path.suffix == ".json":
        return Job.model_validate_json(raw)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if not lines:
        raise ValueError("job file is empty")
    description, criteria = [], []
    for line in lines[1:]:
        if line.startswith("criterion:"):
            parts = line.removeprefix("criterion:").split("|", 2)
            if len(parts) != 3:
                raise ValueError("criterion format: id | weight | description")
            key, weight, detail = (part.strip() for part in parts)
            criteria.append({"id": key, "weight": int(weight), "description": detail})
        else:
            description.append(line)
    return Job.model_validate(
        {"title": lines[0], "description": " ".join(description), "criteria": criteria}
    )


def sanitize_resume(text: str) -> str:
    """Remove common contact patterns; this is deliberately not full anonymization."""
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email removed]", text)
    text = re.sub(
        r"(?<!\w)(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}(?!\w)", "[phone removed]", text
    )
    return text.replace("\x00", "")


def load_candidates(path: Path) -> list[Candidate]:
    raw = read_text(path)
    reader = csv.DictReader(raw.splitlines(keepends=True))
    if reader.fieldnames != ["candidate_id", "name", "resume"]:
        raise ValueError("CSV header must be candidate_id,name,resume")
    candidates = []
    for row in reader:
        if len(candidates) >= MAX_CANDIDATES:
            raise ValueError("at most 20 candidates per run")
        if None in row or any(value is None for value in row.values()):
            raise ValueError("malformed CSV row")
        candidates.append(
            Candidate(
                id=row["candidate_id"], name=row["name"], resume=sanitize_resume(row["resume"])
            )
        )
    if not candidates or len({item.id for item in candidates}) != len(candidates):
        raise ValueError("provide at least one candidate, with unique IDs")
    return candidates


def fingerprint(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode()).hexdigest()


def safe_terminal(text: str) -> str:
    """Prevent untrusted document text from injecting terminal control sequences."""
    return "".join(char if char.isprintable() else " " for char in text)
