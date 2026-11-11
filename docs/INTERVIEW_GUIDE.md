# Interview guide

**Three-minute walkthrough**

Run `uv run talent_scout --offline --metrics`. Explain the fixed rubric and exact quotes.
Show one `not_stated` assessment and describe the question it raises for a person. Show
`validate_analysis()` and the Judge order check. Run `uv run pytest`. Finish with the
explicit difference between fixture regression and measured live model performance.

**Why several roles?** Independent per-resume analyses keep the task bounded. Judge adds
readable reasons; fairness review checks the combined result. These are separate calls with
different contracts, not independent sources of truth. Remove a role if a measured ablation
shows it adds cost without improving review quality.

**Can the model hallucinate?** Yes. Exact quotes stop invented strings from passing, and
unknown IDs/criteria are rejected. But a real quote can be irrelevant, negated or misleading.
The tests explicitly demonstrate that provenance checks do not establish semantic correctness.

**Does the fairness pass remove bias?** No. It flags concerns for review. Any finding blocks
simulated approval. It can miss issues and share errors with the Analyzer. A larger independent
evaluation would be needed before making a fairness claim.

**What protects against injection?** Documents are data in a separate message, output keys
are allowlisted, points and order are application-owned, and there are no action tools.
This limits authority; it does not guarantee the model won't mislabel evidence.

**Why not simply ask for a fit score?** A fixed rubric makes points reproducible from labels,
exposes exactly where evidence is missing, and prevents silent changes to weights. It still
does not make the rubric itself unbiased or the model's interpretation objectively correct.

**Is $5 guaranteed?** It is a conservative estimated cap per run. Each call reserves counted
input with a margin plus the full output maximum. Actual usage settles afterward. Incorrect
prices, count variance, restarts and timeouts prevent an absolute billing guarantee. A separate
provider-side spending control remains external to this app.

**Does data leave the machine?** Offline mode: no. Live mode: job/resume text and intermediate
evidence go to Anthropic. Separate display names are withheld, but free text is not fully
anonymized. Metadata logs omit document text; exported reports intentionally contain evidence.

**Are tests proving Claude works?** No. Unit tests and HTTP mocks verify code and transport
contracts. Offline regression verifies curated fixtures. The optional live eval measures a
small synthetic baseline, name-counterfactual consistency and injection behavior; it has not
been run in the recorded build.

**What would you improve next?** Independent annotations and broader eval first. Then assess
whether Judge and fairness roles improve results enough to justify cost. Persistent budget
accounting, access control and reviewed integrations would precede any consequential use.
