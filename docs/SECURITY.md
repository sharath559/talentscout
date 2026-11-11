# Security and cost controls

## Boundaries and data flow

All resumes, job documents, quoted evidence and model output are untrusted. Parsers bound
file size, candidate count and field lengths. Documents are JSON-encoded as user-message
data; system instructions remain separate. These instructions reduce risk but do not establish
prompt-injection resistance. Schema checks establish shape, and exact quotes establish
provenance; neither establishes truth, relevance or fairness.

The allowlist is the set of application functions in `tools.py`. These are local preprocessing
helpers, not model-callable tools. There is no `eval`, subprocess execution, network fetch,
MCP server or model-directed filesystem access. Models cannot hire or reject anyone.

| Threat | Implemented control | Remaining exposure |
| --- | --- | --- |
| Prompt injection in a resume | Separate system/data, fixed schema, fixed ordering, fairness role | A malicious passage can still influence evidence labels or rationales |
| Fabricated qualifications | Exact source-quote checks and complete rubric validation | An authentic quote can be misleading; source claims can themselves be false |
| Demographic or prestige proxy | Names excluded from prompts; rubric constraints; fairness flags | Resume prose may reveal identity; no demographic parity proof |
| Unexpected action or tool call | Text-only response check; no execution interface | A human could overtrust misleading output |
| Secret exposure | `.env` ignored; SDK reads key; no raw API-error logging | Local environment and machine remain trusted |
| Sensitive logs | Audit contains stage and usage metadata only | Reports and terminal output intentionally contain candidate evidence |
| Terminal escape injection | Control characters stripped from rendered document text | JSON consumers must still handle untrusted strings safely |
| Overwriting documents | Reports use exclusive creation; output/audit paths checked against inputs | Operator-selected audit files are appended to; filesystem permissions remain external |

## Privacy

Offline mode makes zero API calls. In live mode Anthropic receives job text, resume text,
quotes and intermediate assessments. The display-name CSV field is omitted, and common
email/phone patterns are removed. This is not reliable anonymization: names inside prose,
locations and indirect identifiers may remain. No real-person privacy or data-retention claim
is made. Use only synthetic data unless appropriate organizational review authorizes otherwise.

Audit JSONL omits raw prompts, model outputs, names, document hashes and exception bodies.
Candidate evidence is deliberately visible in human review and exported JSON. Those exports
are the operator's responsibility; `artifacts/` is ignored. No persistent resume cache is created.

## Budget mechanics

All live requests in one provider instance share a Decimal-based budget. Count Tokens runs
before each generation, with the same system, user data and output schema. The reservation is:

```text
((ceil(counted_input × 1.10) + 1024) × input_rate
 + max_output_tokens × output_rate) / 1,000,000
```

Insufficient balance stops generation. Successful responses settle to reported input/output
usage before output validation. Timed-out or failed requests retain their reservation because
billing may be uncertain. SDK automatic retries are disabled. Prices are explicit configuration;
cached, regional or future pricing may differ. No caching, paid tools or extended thinking is used.

The cap is conservative **estimated usage per process**, not an absolute invoice guarantee.
Token estimation can differ from billing, prices can be misconfigured, and restarting resets
the ledger. An unexpectedly expensive response stops further calls but cannot undo a charge.
Configure a separate provider/workspace spending limit as needed. This project does not invoke
spend administration endpoints or claim that Count Tokens alone guarantees a $5 invoice cap.

## Human review

No finding may be approved automatically. Any `review` or `block` finding disables the local
approval prompt. Clean results remain pending until a terminal user explicitly types yes;
blank input, EOF and no decline. There is no `--yes` or piped-approval interface. This is an
interaction control, not authentication or a cryptographically signed decision record.
The approved record says `approved_simulation`; it cannot trigger a downstream action.

## Validation references

The official [structured outputs documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
describes schema transformations and limitations. The [pricing page](https://platform.claude.com/docs/en/about-claude/pricing)
is the source for configurable price assumptions. Recheck those assumptions before live use.
