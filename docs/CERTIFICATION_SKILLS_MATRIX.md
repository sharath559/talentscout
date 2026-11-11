# Developer competency matrix

This is an implementation map for interview review. Domain numbering and certification
requirements in the supplied brief were not independently verified; this table does not
claim official syllabus coverage, accreditation or endorsement.

| Competency | Concrete evidence | Boundary |
| --- | --- | --- |
| Claude SDK and Messages API | `ClaudeProvider.request()`, real SDK HTTP-mock tests | No paid integration run recorded |
| Token counting and model metadata | Count Tokens with response schema; model output-limit check | Metadata does not supply prices |
| Multi-role orchestration | Analyzer per resume → Judge → fairness reviewer | Bounded sequential fan-out; no autonomous tool loop |
| Context and prompts | Separate versioned system prompts and JSON user data | Separation is not injection immunity |
| Structured outputs | SDK schema transformation, strict Pydantic contracts | Schema validity is not factual validity |
| Grounding | Exact quotes, known IDs and complete criterion coverage | Relevance still requires review |
| Cost management | Decimal ledger, full output reservation, usage settlement, no retries | Per-run estimated cap; no provider spend administration |
| Model choice | Explicit model and two configurable rates | No automatic fallback or comparative model benchmark |
| Security and human control | Limited local tools, no execution/ATS, terminal review, unresolved flags block | No authentication or production approval service |
| Evaluation and observability | Fixtures, contract tests, SDK mock, optional live eval, metadata audit | Offline results do not measure fairness or live quality |
| Local data tools | Bounded CSV/job parsing and contact-pattern removal | Not model-selected tool calling or MCP |
| Reproducibility | Lockfile, scripts, passing Python 3.10/3.12/3.14 CI, milestone commits, demo artifacts | CI exercises offline contracts, not paid inference |

An honest interview answer distinguishes implemented controls, demonstrated behavior,
unmeasured quality, and proposed extensions. That distinction is a central project feature.
