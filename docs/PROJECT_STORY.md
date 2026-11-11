# Project story

## Problem and goal

Candidate review often hides an important distinction: the absence of documented evidence
is different from evidence of absence. TalentScout makes that distinction visible in a small,
auditable Claude workflow. It produces a review packet for fictional candidates rather than
automating an employment decision.

## Design decisions

The original proposal asked a model to give a general fit percentage and rank people.
That would make the scoring rule hard to inspect. This implementation instead fixes a
weighted rubric before processing applicants, requires exact supporting quotes, and computes
coverage points in Python. The Judge can explain the supplied order but cannot invent a new one.

A separate fairness role checks all candidates, not just the top result. It can flag concerns,
but cannot certify fairness or silently clear its own flags. Any finding blocks even the
simulated approval prompt. The reviewer sees source quotes and missing-information labels.

Offline-by-default behavior makes the portfolio reproducible without credentials or a bill.
Hash-bound fixtures prevent an unfamiliar resume from receiving a fake canned assessment.
The live provider is tested using the real SDK and a local HTTP transport, keeping billing
and model-quality claims separate from application correctness.

## Demonstrated result

The runnable CLI can replay a four-candidate review, emit structured JSON, show source
evidence, record metadata, and ask for interactive simulated approval. Tests and evaluation
artifacts document what was actually exercised. Live model performance remains unmeasured.
No user-study time saving or business impact is asserted.

## Interview narrative

**Situation:** I needed a portfolio that demonstrated Claude integration and engineering
judgment beyond a chatbot demo.

**Task:** Produce an inspectable candidate-evidence workflow with source grounding,
bounded spending, reproducible evaluation and explicit human control.

**Action:** Separate model interpretation from deterministic validation; constrain every
stage; reserve cost before generation; test failure paths with the real SDK locally; document
the remaining limits rather than claiming schemas or a second model pass solve bias.

**Result:** A documented, reproducible Python project with an offline demo, milestone history
and concrete controls that can be inspected by a reviewer. Describe only observed test results.

## Resume wording

- Built a Python/Claude evidence-review pipeline with native structured outputs, exact-source
  validation, deterministic rubric scoring and simulated human approval.
- Added per-run token-cost reservations, timeout accounting and metadata-only auditing;
  exercised SDK request contracts through a local HTTP mock without paid calls.
- Documented model limitations and delivered repeatable offline regression and optional
  baseline, name-counterfactual and prompt-injection evaluation workflows.
