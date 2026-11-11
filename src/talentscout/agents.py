"""Bounded multi-role workflow with deterministic validation between stages."""

from dataclasses import dataclass
from decimal import Decimal

from . import prompts
from .models import Analysis, Candidate, FairnessReview, Job, Judgment, score
from .providers import Provider


def analyze(provider: Provider, job: Job, candidate: Candidate) -> Analysis:
    payload = {"job": job.model_dump(mode="json"), "candidate_id": candidate.id,
               "resume": candidate.resume}
    result = provider.request(f"analyzer:{candidate.id}", prompts.ANALYZER, payload, Analysis)
    validate_analysis(result, job, candidate)
    return result


def validate_analysis(result: Analysis, job: Job, candidate: Candidate) -> None:
    if result.candidate_id != candidate.id:
        raise ValueError("analysis candidate ID does not match input")
    actual = [item.criterion_id for item in result.evidence]
    if len(actual) != len(set(actual)) or set(actual) != {item.id for item in job.criteria}:
        raise ValueError("analysis must cover every rubric criterion exactly once")
    for item in result.evidence:
        for quote in item.quotes:
            if quote not in candidate.resume:
                raise ValueError("analysis contains a source quote absent from the resume")


def judge_payload(job: Job, analyses: list[Analysis]) -> dict:
    points = {item.candidate_id: score(item, job) for item in analyses}
    order = sorted(points, key=lambda key: (-points[key], key))
    return {"job": job.model_dump(mode="json"),
            "analyses": [item.model_dump(mode="json") for item in analyses],
            "scores": {key: str(value) for key, value in points.items()},
            "expected_order": order}


def judge(provider: Provider, job: Job, analyses: list[Analysis]) -> Judgment:
    payload = judge_payload(job, analyses)
    result = provider.request("judge", prompts.JUDGE, payload, Judgment)
    if [entry.candidate_id for entry in result.ranking] != payload["expected_order"]:
        raise ValueError("judge changed the deterministic order, omitted or duplicated a candidate")
    return result


def fairness_payload(job: Job, candidates: list[Candidate], analyses: list[Analysis],
                     judgment: Judgment) -> dict:
    return {"job": job.model_dump(mode="json"),
            "sources": [{"candidate_id": item.id, "resume": item.resume} for item in candidates],
            "analyses": [item.model_dump(mode="json") for item in analyses],
            "judgment": judgment.model_dump(mode="json")}


def review_fairness(provider: Provider, job: Job, candidates: list[Candidate],
                    analyses: list[Analysis], judgment: Judgment) -> FairnessReview:
    result = provider.request("fairness", prompts.FAIRNESS,
                              fairness_payload(job, candidates, analyses, judgment), FairnessReview)
    ids = {item.id for item in candidates}
    if any(finding.candidate_id not in ids for finding in result.findings):
        raise ValueError("fairness finding references an unknown candidate")
    return result


@dataclass
class RunResult:
    job: Job
    candidates: list[Candidate]
    analyses: list[Analysis]
    judgment: Judgment
    fairness: FairnessReview

    @property
    def scores(self) -> dict[str, Decimal]:
        return {item.candidate_id: score(item, self.job) for item in self.analyses}

    @property
    def approval_allowed(self) -> bool:
        return not self.fairness.findings

    def report(self, approval: str = "pending") -> dict:
        names = {item.id: item.name for item in self.candidates}
        return {
            "schema_version": "1.0", "prompt_version": prompts.VERSION,
            "purpose": "synthetic candidate evidence review; no employment decision",
            "job": self.job.model_dump(mode="json"),
            "ranking": [{"candidate_id": item.candidate_id, "name": names[item.candidate_id],
                         "evidence_points": str(self.scores[item.candidate_id]),
                         "reason": item.reason} for item in self.judgment.ranking],
            "analyses": [item.model_dump(mode="json") for item in self.analyses],
            "fairness": self.fairness.model_dump(mode="json"),
            "approval": approval, "approval_allowed": self.approval_allowed,
        }


def run_pipeline(provider: Provider, job: Job, candidates: list[Candidate]) -> RunResult:
    if not candidates or len({item.id for item in candidates}) != len(candidates):
        raise ValueError("candidates must be nonempty with unique IDs")
    # Logical fan-out; sequential dispatch keeps accounting simple and bounded.
    analyses = [analyze(provider, job, candidate) for candidate in candidates]
    judgment = judge(provider, job, analyses)
    fairness = review_fairness(provider, job, candidates, analyses, judgment)
    return RunResult(job, candidates, analyses, judgment, fairness)
