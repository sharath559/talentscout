# Limitations

This is a synthetic-data engineering portfolio, not a validated employment assessment.
It can organize evidence against explicit criteria and enforce review boundaries. It cannot
determine a person's potential, verify their claims, predict performance, or establish fairness.

1. **Missing text is not missing ability.** A terse resume may earn fewer coverage points.
   `not_stated` should drive a follow-up question. Rankings must not become rejection rules.
2. **Provenance is narrower than correctness.** An exact PostgreSQL quote could be assigned
   to a Python criterion and still pass the literal quote check. A regression test explicitly
   demonstrates this boundary. Humans must verify semantic relevance and negation.
3. **Interpretation remains probabilistic.** Supported versus partial labels and rationales
   may change between calls. A deterministic score formula does not make the labels objective.
4. **Fairness reviewers can miss bias.** The same model plays all roles, so errors may be
   correlated. An empty finding list means no issue detected, not absence of discrimination.
5. **Prompt injection remains possible.** JSON schemas do not neutralize malicious data.
   The app limits downstream authority but cannot guarantee unbiased evidence interpretation.
6. **Names are only partly isolated.** The separate name column never reaches Claude;
   names and demographics in free text can still do so. Contact removal is limited.
7. **Offline success is fixture success.** Canned outputs are hand-authored, hash-bound and
   deterministic. Replaying them establishes wiring, not model quality or robustness.
8. **The reference set is tiny.** Four English resumes for one role cannot establish
   real-world accuracy, subgroup performance or quality for unconventional careers.
9. **Costs are estimates and reset per run.** Rates are not discovered automatically.
   Timeouts may be billed. No application can reverse provider charges after a response.
10. **Approval is a demonstration.** A terminal prompt is not identity verification, legal
    review, consent, appeal, access control, or protection against automation bias.

No live API run or live evaluation is asserted. No fairness percentages, hiring outcomes,
official certification coverage, production readiness, or recruiter time savings are claimed.
Local tests are described in EVALUATION.md. Tournament selection, MCP, prompt caching,
PDF extraction, concurrent dispatch, persistent billing, and ATS integration are not implemented.

Before considering any real hiring use, replace the fixture study with authorized data,
independent annotations, representative outcome studies, counterfactual tests, and the
organization's own human review, privacy, governance and legal processes. That is future work.
