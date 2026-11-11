# Evaluation

## Recorded local results

The local build ran on macOS with CPython 3.14.5. The initial verification completed
**61 tests, all passing, with 93% statement coverage**. The interpreter, commands and
test counts describe an actual local run. The published
[GitHub Actions run](https://github.com/sharath559/talentscout/actions/runs/43057637526)
also passed all lint, formatting, tests and offline regression steps on Ubuntu with
Python 3.10, 3.12 and 3.14.

```bash
uv sync --frozen --extra dev
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=talentscout --cov-report=term-missing
uv run python scripts/evaluate.py
```

[Recorded evaluation JSON](evaluation-results.json) reports five passing offline checks:
reference order, reference points, display-name counterfactual points, mandatory human
review, and pending default approval. Two full fixture pipelines ran: 12 replayed stage
responses, zero API calls, and $0 estimated API cost.

The reference order is C001, C002, C003, C004, with points 100, 72.5, 60 and 30.
Those labels and points are human-authored expectations for fictional documents, not
empirical ground truth about candidate quality. The fixtures replay these expectations;
agreement is a regression check, not a model benchmark.

## What each verification establishes

| Verification | Measured behavior | Does not establish |
| --- | --- | --- |
| Agent contract tests | Reject fabricated quotes, unknown IDs, duplicate/missing criteria, altered rankings | Semantic relevance of a real quote |
| Budget tests | Full-output reservation, shared ledger, invalid configuration, uncertain charge handling | Provider invoice cap |
| Real SDK + HTTP mock | Actual serialized Models/Count Tokens/Messages requests, transformed schema, usage accounting | Live API availability or model quality |
| CLI tests | JSON stdout, metadata stderr, no overwrite, no piped approval, default decline | Authentication of reviewer |
| Input tests | Bounded reads, strict CSV, weights, contact patterns, terminal controls | Complete anonymization |
| Fixture evaluation | Reproducible reference order and scores; names isolated from prompt input | Statistical fairness or real-world accuracy |

The SDK transport tests include count failure, insufficient budget, refused/truncated
responses, malformed JSON, unknown output keys, output-limit mismatch and timeout without
retry. Generation usage is recorded before invalid output is rejected.

The suite deliberately includes a passing literal-quote check with semantically mismatched
evidence. This documents the boundary between provenance and relevance rather than hiding it.

## Optional live evaluation

**Status: not run. No paid Claude calls are represented by the recorded results.**

```bash
mkdir -p artifacts
uv run python scripts/evaluate.py --live --budget 0.50 --output artifacts/live-evaluation.json
```

The script performs three full pipelines with one shared budget: a baseline, the same
resumes with changed separate display names, and an injected resume instructing the model
to ignore the rubric and rank itself first. It checks synthetic reference agreement,
counterfactual score consistency, no injected score increase and a specific injection flag.
It exits nonzero on failed checks or contract/provider failure. It never approves a shortlist.

Even this live run would be a small diagnostic, not proof of safety. Name columns are
already excluded from prompts, so repeated calls principally expose sampling variance.
Future counterfactuals should include names and proxy information embedded in resume prose.

## Next study

Before claiming quality, independently annotate diverse resumes and criteria with at least
two reviewers, resolve disagreements, preserve a held-out set, and report criterion-label
agreement, unsupported-positive rate, missing-evidence rate and quote relevance. Repeat
model runs and report variance. Test paraphrases, negation, career changes, employment gaps,
multilingual input, demographic proxies and adversarial instructions. Compare a single
Analyzer with the full workflow to measure the incremental value and cost of each role.

Publish failure examples and limitations alongside metrics. Do not infer fairness from a
clean model-authored fairness summary or from agreement on a tiny synthetic sample.
