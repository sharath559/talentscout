from pathlib import Path

import pytest

from talentscout.providers import OfflineProvider
from talentscout.tools import load_candidates, load_job

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def job():
    return load_job(ROOT / "data/example_job.txt")


@pytest.fixture
def candidates():
    return load_candidates(ROOT / "data/example_resumes.csv")


@pytest.fixture
def provider():
    return OfflineProvider(ROOT / "data/offline_fixtures.json")
