"""Strict transport contracts and application-owned scoring rules."""

from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Criterion(Contract):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,39}$")
    description: str = Field(min_length=10, max_length=500)
    weight: int = Field(ge=1, le=100)


class Job(Contract):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=10, max_length=5000)
    criteria: list[Criterion] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def valid_rubric(self):
        if sum(item.weight for item in self.criteria) != 100:
            raise ValueError("rubric weights must sum to 100")
        if len({item.id for item in self.criteria}) != len(self.criteria):
            raise ValueError("criterion IDs must be unique")
        return self


class Candidate(Contract):
    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    name: str = Field(min_length=1, max_length=100)
    resume: str = Field(min_length=20, max_length=12000)


class Status(str, Enum):
    SUPPORTED = "supported"
    PARTIAL = "partial"
    NOT_STATED = "not_stated"


class Evidence(Contract):
    criterion_id: str
    status: Status
    quotes: list[str] = Field(max_length=3)
    rationale: str = Field(min_length=10, max_length=600)

    @model_validator(mode="after")
    def require_evidence(self):
        if self.status != Status.NOT_STATED and not self.quotes:
            raise ValueError("positive credit requires source quotes")
        if self.status == Status.NOT_STATED and self.quotes:
            raise ValueError("not_stated cannot include source quotes")
        if any(len(quote.strip()) < 12 for quote in self.quotes):
            raise ValueError("source quotes must contain at least 12 characters")
        return self


class Analysis(Contract):
    candidate_id: str
    evidence: list[Evidence] = Field(min_length=1, max_length=12)


class Recommendation(Contract):
    candidate_id: str
    reason: str = Field(min_length=10, max_length=600)


class Judgment(Contract):
    ranking: list[Recommendation] = Field(min_length=1, max_length=20)


class Finding(Contract):
    candidate_id: str
    category: Literal["unsupported_inference", "proxy_risk", "prompt_injection", "other"]
    severity: Literal["review", "block"]
    detail: str = Field(min_length=10, max_length=600)


class FairnessReview(Contract):
    findings: list[Finding] = Field(max_length=50)
    summary: str = Field(min_length=10, max_length=800)
    human_review_required: Literal[True]


class Hello(Contract):
    message: str = Field(min_length=1, max_length=300)


def score(analysis: Analysis, job: Job) -> Decimal:
    """Points describe documented evidence, never probability of job performance."""
    weights = {criterion.id: criterion.weight for criterion in job.criteria}
    factors = {Status.SUPPORTED: Decimal(1), Status.PARTIAL: Decimal("0.5"),
               Status.NOT_STATED: Decimal(0)}
    return sum((Decimal(weights[item.criterion_id]) * factors[item.status]
                for item in analysis.evidence), Decimal(0))
